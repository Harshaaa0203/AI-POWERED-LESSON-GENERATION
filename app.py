"""
AI-POWERED LESSON CREATION TOOL
Streamlit Frontend Application
Full-featured dashboard, research display, dual QC evaluation, instructor editing, and multi-format exports.
"""

import os
import io
import json
import zipfile
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from database.db_manager import DatabaseManager
from services.ai_service import AIService
from services.lesson_service import LessonService
from services.qc_service import QCService
from agents.recommendation_agent import RecommendationAgent
from exports.pdf_exporter import PDFExporter
from exports.markdown_exporter import MarkdownExporter
from utils.helpers import get_score_color, get_severity_color, format_duration
from utils.error_handler import format_error_for_ui, LessonCreatorError

# =====================================================================
# PAGE CONFIGURATION & STYLES
# =====================================================================
st.set_page_config(
    page_title="AI Lesson Creation Tool",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =====================================================================
# SESSION STATE & SERVICE INITIALIZATION
# =====================================================================
if "gemini_key" not in st.session_state:
    st.session_state["gemini_key"] = os.getenv("GEMINI_API_KEY", "")

if "youtube_key" not in st.session_state:
    st.session_state["youtube_key"] = os.getenv("YOUTUBE_API_KEY", "")

if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if "active_lesson_id" not in st.session_state:
    st.session_state["active_lesson_id"] = None

if "edit_buffer" not in st.session_state:
    st.session_state["edit_buffer"] = {}

if "delete_confirm_id" not in st.session_state:
    st.session_state["delete_confirm_id"] = None

@st.cache_resource
def get_db():
    return DatabaseManager()

db = get_db()

# Recreate AIService based on session key
ai_service = AIService(
    api_key=st.session_state["gemini_key"],
    model=st.session_state["selected_model"]
)
lesson_service = LessonService(ai_service=ai_service, db_manager=db)
qc_service = QCService(ai_service=ai_service, db_manager=db)
rec_agent = RecommendationAgent(ai_service=ai_service)
pdf_exporter = PDFExporter()
md_exporter = MarkdownExporter()

# =====================================================================
# SIDEBAR NAVIGATION & SETTINGS
# =====================================================================
with st.sidebar:
    st.markdown("### 🎓 AI Lesson Creator")
    st.caption("Pedagogical AI & Dual-Layer QC System")
    st.divider()

    nav_options = [
        "1. 📊 Dashboard",
        "2. ➕ Create New Lesson",
        "3. 🔍 Research Results",
        "4. 📖 Generated Lesson",
        "5. 🛡️ Factual Accuracy QC",
        "6. 🎯 Instructional Quality QC",
        "7. ✏️ Review and Edit",
        "8. 👁️ Preview Lesson",
        "9. 📤 Export Lesson",
        "10. 💾 Saved Lessons"
    ]

    selected_nav = st.radio("Navigation", nav_options, index=0)

    st.divider()
    st.markdown("#### ⚙️ AI Engine & Settings")

    provider_info = ai_service.get_provider_info()
    if provider_info["status"] == "live":
        st.success(f"🟢 **{provider_info['provider']}**\n\nModel: `{provider_info['model']}`")
    else:
        st.info(f"🔵 **Offline Pedagogical Engine**\n\nActive for zero-latency testing & demo.")

    with st.expander("🔑 Configure API Keys", expanded=False):
        input_key = st.text_input(
            "Gemini API Key",
            value=st.session_state["gemini_key"],
            type="password",
            help="Free key from https://aistudio.google.com/app/apikey"
        )
        if input_key != st.session_state["gemini_key"]:
            st.session_state["gemini_key"] = input_key
            st.rerun()

        model_choice = st.selectbox(
            "Gemini Model",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0
        )
        if model_choice != st.session_state["selected_model"]:
            st.session_state["selected_model"] = model_choice
            st.rerun()

        yt_key = st.text_input(
            "YouTube API Key (Optional)",
            value=st.session_state["youtube_key"],
            type="password",
            help="Optional. If omitted, web video extraction is used automatically."
        )
        if yt_key != st.session_state["youtube_key"]:
            st.session_state["youtube_key"] = yt_key

    # Current Active Lesson display & selector in sidebar
    st.divider()
    st.markdown("#### 📚 Active Lesson")
    all_saved = db.list_lessons(limit=100)
    if all_saved:
        id_options = [l["id"] for l in all_saved]
        titles_map = {l["id"]: f"{l['title']}" for l in all_saved}
        
        # Ensure active_lesson_id defaults to the first available lesson
        if not st.session_state.get("active_lesson_id") or st.session_state["active_lesson_id"] not in id_options:
            st.session_state["active_lesson_id"] = id_options[0]

        curr_sel_idx = id_options.index(st.session_state["active_lesson_id"])
        selected_sb_id = st.selectbox(
            "Select Loaded Lesson",
            options=id_options,
            format_func=lambda x: titles_map.get(x, x),
            index=curr_sel_idx,
            key="sb_lesson_picker"
        )
        if selected_sb_id != st.session_state["active_lesson_id"]:
            st.session_state["active_lesson_id"] = selected_sb_id
            st.session_state["edit_buffer"] = {}
            st.rerun()

        active_meta = db.get_lesson(st.session_state["active_lesson_id"])
        if active_meta:
            st_val = active_meta.get("status", "processing")
            s_class = f"status-{st_val.replace('_', '-')}"
            st.markdown(f"Status: <span class='status-badge {s_class}'>{st_val.upper()}</span>", unsafe_allow_html=True)
    else:
        st.session_state["active_lesson_id"] = None
        st.caption("No lessons saved in database yet.")

# Helper to fetch active lesson (auto-loads first available lesson)
def get_active_lesson():
    if not st.session_state.get("active_lesson_id"):
        available = db.list_lessons(limit=1)
        if available:
            st.session_state["active_lesson_id"] = available[0]["id"]
            return available[0]
        return None
    lesson = db.get_lesson(st.session_state["active_lesson_id"])
    if not lesson:
        available = db.list_lessons(limit=1)
        if available:
            st.session_state["active_lesson_id"] = available[0]["id"]
            return available[0]
        return None
    return lesson

def render_top_lesson_switcher():
    """Renders a top toolbar allowing immediate lesson switching across all views."""
    all_lessons = db.list_lessons(limit=100)
    if not all_lessons:
        return
    c_sel, c_stat = st.columns([3, 1])
    id_map = {l["id"]: f"{l['title']}  [{l['status'].upper()}]" for l in all_lessons}
    ids = list(id_map.keys())
    curr_id = st.session_state.get("active_lesson_id")
    idx = ids.index(curr_id) if curr_id in ids else 0
    with c_sel:
        chosen = st.selectbox(
            "📚 Active Lesson Topic (Switch between saved lessons):",
            options=ids,
            format_func=lambda x: id_map.get(x, x),
            index=idx,
            key=f"switcher_{selected_nav[:2].strip()}"
        )
        if chosen != st.session_state.get("active_lesson_id"):
            st.session_state["active_lesson_id"] = chosen
            st.session_state["edit_buffer"] = {}
            st.rerun()
    with c_stat:
        l_meta = db.get_lesson(st.session_state["active_lesson_id"])
        if l_meta:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.caption(f"ID: `{l_meta['id'][:8]}` | {l_meta['created_at'][:10]}")
    st.divider()

# =====================================================================
# VIEW 1: DASHBOARD
# =====================================================================
if "1. 📊 Dashboard" in selected_nav:
    st.markdown("""
        <div class="main-header-card">
            <h1 class="main-header-title">🎓 AI-Powered Educational Lesson Creation Tool</h1>
            <p class="main-header-subtitle">Automated multi-source research, 45-minute lesson generation, and dual-agent quality control verification</p>
        </div>
    """, unsafe_allow_html=True)

    stats = db.get_dashboard_stats()

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{stats['total_lessons']}</div>
                <div class="kpi-label">Total Lessons</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value" style="color: #16a34a;">{stats['completed_lessons']}</div>
                <div class="kpi-label">Completed</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value" style="color: #d97706;">{stats['needs_review_lessons']}</div>
                <div class="kpi-label">Needs Review</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        f_color = get_score_color(stats['avg_factual_score'])
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value" style="color: {f_color};">{stats['avg_factual_score']}</div>
                <div class="kpi-label">Avg Factual QC</div>
            </div>
        """, unsafe_allow_html=True)
    with c5:
        i_color = get_score_color(stats['avg_instructional_score'])
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value" style="color: {i_color};">{stats['avg_instructional_score']}</div>
                <div class="kpi-label">Avg Pedagogical QC</div>
            </div>
        """, unsafe_allow_html=True)

    # Visual Analytics: 45-Minute Lesson Pacing Architecture
    with st.expander("⏱️ Framework Pacing Architecture (45-Minute Lesson Allocation)", expanded=False):
        import pandas as pd
        pacing_df = pd.DataFrame([
            {"Section": "1. Introduction", "Minutes": 3, "Focus": "Hook, Context & Preview"},
            {"Section": "2. Prerequisites & Concepts", "Minutes": 5, "Focus": "Definitions & Foundational Terms"},
            {"Section": "3. Detailed Explanations", "Minutes": 15, "Focus": "Deep Conceptual Breakdown"},
            {"Section": "4. Real-World Examples", "Minutes": 7, "Focus": "Applied Production Scenarios"},
            {"Section": "5. Practical Activity", "Minutes": 7, "Focus": "Hands-on Exercise"},
            {"Section": "6. Knowledge Check", "Minutes": 5, "Focus": "Diagnostic Questions & Review"},
            {"Section": "7. Lesson Summary", "Minutes": 3, "Focus": "Synthesis & Core Takeaways"}
        ])
        st.bar_chart(pacing_df.set_index("Section")["Minutes"], color="#3b82f6")
        st.caption("Total Duration: Exactly 45 Minutes (Strictly Enforced by QC Agent 2).")

        # QC Scores Comparison Across Lessons
        recent_list = stats.get("recent_lessons", [])
        if recent_list:
            scores_data = []
            for r_item in recent_list:
                f_s = (r_item.get("factual_qc_report") or {}).get("overall_score")
                i_s = (r_item.get("instructional_qc_report") or {}).get("overall_score")
                if f_s is not None and i_s is not None:
                    scores_data.append({
                        "Lesson": r_item["title"][:20],
                        "Factual Accuracy QC": float(f_s),
                        "Instructional Quality QC": float(i_s)
                    })
            if scores_data:
                st.write("**Audit Scores Comparison (Factual vs Instructional):**")
                sc_df = pd.DataFrame(scores_data).set_index("Lesson")
                st.bar_chart(sc_df)

    st.markdown("<br/>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        st.subheader("📋 Recently Created Lessons")
        recent = stats.get("recent_lessons", [])
        if not recent:
            st.info("No lessons created yet. Start by clicking **Create New Lesson** in the sidebar!")
        else:
            for item in recent:
                lid = item["id"]
                title = item["title"]
                obj = item["learning_objective"]
                status = item["status"]
                created = item["created_at"].split("T")[0]
                status_class = f"status-{status.replace('_', '-')}"

                with st.container():
                    st.markdown(f"""
                        <div class="content-box">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-weight: 700; font-size: 1.1rem; color: #1e3a8a;">{title}</span>
                                <span class="status-badge {status_class}">{status.upper()}</span>
                            </div>
                            <p style="color: #475569; font-size: 0.9rem; margin-top: 0.4rem; margin-bottom: 0.5rem;">{obj[:140]}...</p>
                            <span style="font-size: 0.8rem; color: #94a3b8;">Created: {created} &nbsp;|&nbsp; ID: {lid[:8]}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    btn_c1, btn_c2, _ = st.columns([1, 1, 3])
                    with btn_c1:
                        if st.button("Load Lesson", key=f"dash_load_{lid}"):
                            st.session_state["active_lesson_id"] = lid
                            st.session_state["edit_buffer"] = {}
                            st.success(f"Loaded '{title}' into active workspace!")
                            st.rerun()
                    with btn_c2:
                        if st.button("View Export", key=f"dash_exp_{lid}"):
                            st.session_state["active_lesson_id"] = lid
                            st.session_state["edit_buffer"] = {}
                            st.rerun()

    with col_right:
        st.subheader("⚡ Quick Launch Test Cases")
        st.markdown("""
        Test the application with the pre-configured assignment benchmarks:
        """)

        with st.container():
            st.markdown("""
            **TEST CASE 1 (Mandatory Assignment Benchmark):**
            - **Title:** `HTTP Requests and Responses`
            - **Objective:** *Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.*
            """)
            if st.button("🚀 Load Test Case 1 Preset", use_container_width=True):
                st.session_state["preset_title"] = "HTTP Requests and Responses"
                st.session_state["preset_objective"] = "Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
                st.info("Preset loaded! Switch to 'Create New Lesson' to run.")

        st.markdown("<br/>", unsafe_allow_html=True)
        with st.container():
            st.markdown("""
            **TEST CASE 2 (Educational Algorithm Benchmark):**
            - **Title:** `Binary Search Algorithm`
            - **Objective:** *Explain the divide-and-conquer principle of binary search and analyze its logarithmic O(log n) time complexity.*
            """)
            if st.button("🚀 Load Test Case 2 Preset", use_container_width=True):
                st.session_state["preset_title"] = "Binary Search Algorithm"
                st.session_state["preset_objective"] = "Explain the divide-and-conquer principle of binary search and analyze its logarithmic O(log n) time complexity."
                st.info("Preset loaded! Switch to 'Create New Lesson' to run.")

# =====================================================================
# VIEW 2: CREATE NEW LESSON
# =====================================================================
elif "2. ➕ Create New Lesson" in selected_nav:
    st.subheader("➕ Create New Educational Lesson")
    st.markdown("Enter the lesson title and learning objective. The pipeline will automatically conduct multi-source research, generate a structured 45-minute lesson, and audit it through two independent QC agents.")

    default_title = st.session_state.get("preset_title", "")
    default_obj = st.session_state.get("preset_objective", "")

    with st.form("create_lesson_form"):
        title_input = st.text_input(
            "Lesson Title *",
            value=default_title,
            placeholder="e.g. HTTP Requests and Responses",
            help="Enter a clear, descriptive educational topic."
        )

        objective_input = st.text_area(
            "Learning Objective *",
            value=default_obj,
            placeholder="e.g. Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.",
            height=110,
            help="State what the learner will be able to explain, demonstrate, or perform upon completion."
        )

        col_f1, col_f2 = st.columns([1, 4])
        with col_f1:
            submitted = st.form_submit_button("🚀 Start Creation", use_container_width=True, type="primary")

    if submitted:
        if not title_input.strip() or not objective_input.strip():
            st.error("Please provide both a Lesson Title and a Learning Objective.")
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(val: float, message: str):
                progress_bar.progress(val)
                status_text.markdown(f"**Step Progress:** {message}")

            try:
                with st.spinner("Processing lesson pipeline..."):
                    lesson_record = lesson_service.create_lesson_pipeline(
                        title=title_input,
                        learning_objective=objective_input,
                        progress_callback=update_progress
                    )
                st.session_state["active_lesson_id"] = lesson_record["id"]
                st.session_state["edit_buffer"] = {}
                progress_bar.progress(1.0)
                status_text.success("🎉 Lesson successfully generated, researched, and dual-QC verified!")
                st.balloons()
            except Exception as e:
                status_text.error(format_error_for_ui(e))

# =====================================================================
# VIEW 3: RESEARCH RESULTS
# =====================================================================
elif "3. 🔍 Research Results" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        st.subheader(f"🔍 Research Dossier: {lesson['title']}")
        st.caption(f"Objective: {lesson['learning_objective']}")

        research = lesson.get("research_sources") or {}
        web_sources = research.get("web_sources", [])
        book_sources = lesson.get("book_sources") or research.get("book_sources", [])
        youtube_sources = lesson.get("youtube_resources") or research.get("youtube_resources", [])

        tab_web, tab_books, tab_youtube, tab_claims = st.tabs([
            f"🌐 Web Sources ({len(web_sources)})",
            f"📚 Book References ({len(book_sources)})",
            f"📺 YouTube Videos ({len(youtube_sources)})",
            "🛡️ Verified Factual Anchors"
        ])

        with tab_web:
            st.markdown("#### Educational Websites & Official Documentation")
            if not web_sources:
                st.info("No web sources recorded. You can retry research from the controls below.")
            else:
                for idx, ws in enumerate(web_sources, 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="content-box">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: 600; font-size: 1rem; color: #1e3a8a;">{idx}. {ws.get('title')}</span>
                                <span class="status-badge" style="background:#e0f2fe; color:#0369a1;">{ws.get('credibility', 'Medium')} Credibility</span>
                            </div>
                            <p style="color: #475569; font-size: 0.88rem; margin: 0.4rem 0;">{ws.get('snippet')}</p>
                            <span style="font-size: 0.8rem; color: #64748b;">Source URL: <a href="{ws.get('url')}" target="_blank">{ws.get('url')}</a> &nbsp;|&nbsp; Category: {ws.get('category')}</span>
                        </div>
                        """, unsafe_allow_html=True)

        with tab_books:
            st.markdown("#### Verified Bibliographic Sources (Open Library & Google Books)")
            if not book_sources:
                st.info("No specific book records returned. Bibliographic catalog search will update on rerun.")
            else:
                for idx, bk in enumerate(book_sources, 1):
                    authors = ", ".join(bk.get("authors", ["Unknown"]))
                    st.markdown(f"""
                    <div class="content-box">
                        <span style="font-weight: 600; font-size: 1rem; color: #1e3a8a;">📖 {idx}. {bk.get('title')}</span><br/>
                        <span style="color: #334155; font-size: 0.9rem;">Authors: <b>{authors}</b> &nbsp;|&nbsp; Year: <b>{bk.get('publication_year', 'N/A')}</b> &nbsp;|&nbsp; Publisher: <b>{bk.get('publisher', 'N/A')}</b></span><br/>
                        <span style="color: #64748b; font-size: 0.8rem;">Catalog Reference: <a href="{bk.get('url')}" target="_blank">{bk.get('url')}</a></span>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_youtube:
            st.markdown("#### Educational Video Resources")
            if not youtube_sources:
                st.info("No YouTube videos retrieved.")
            else:
                cols = st.columns(2)
                for idx, yt in enumerate(youtube_sources):
                    with cols[idx % 2]:
                        st.markdown(f"""
                        <div class="content-box">
                            <span style="font-weight: 600; color: #b91c1c;">▶️ {yt.get('title')}</span><br/>
                            <span style="color: #475569; font-size: 0.85rem;">Channel: <b>{yt.get('channel')}</b></span><br/>
                            <p style="color: #64748b; font-size: 0.82rem; margin: 0.4rem 0;">{yt.get('description', '')[:120]}...</p>
                            <a href="{yt.get('url')}" target="_blank" style="font-size: 0.85rem; font-weight: 600; color: #2563eb;">Watch Video on YouTube →</a>
                        </div>
                        """, unsafe_allow_html=True)
                        if yt.get('url'):
                            with st.expander("▶️ Watch Video Inline"):
                                st.video(yt.get('url'))

        with tab_claims:
            st.markdown("#### Key Grounded Factual Claims")
            claims = research.get("key_factual_claims", [])
            if not claims:
                st.info("No discrete factual claims synthesized.")
            else:
                for cl in claims:
                    st.markdown(f"""
                    <div class="content-box" style="border-left: 4px solid #10b981;">
                        <span style="font-weight: 600; color: #065f46;">Verified Fact:</span> {cl.get('claim')}<br/>
                        <span style="font-size: 0.8rem; color: #64748b;">Source Citation: <i>{cl.get('source')}</i> (<a href="{cl.get('url')}" target="_blank">{cl.get('url')}</a>)</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()
        if st.button("🔄 Re-run Research Stage Only", key="btn_retry_research"):
            with st.spinner("Re-running multi-source research..."):
                updated = lesson_service.retry_stage(lesson["id"], "research")
                st.success("Research sources refreshed!")
                st.rerun()

# =====================================================================
# VIEW 4: GENERATED LESSON
# =====================================================================
elif "4. 📖 Generated Lesson" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        active_content = lesson.get("edited_lesson") or lesson.get("generated_lesson")
        if not active_content:
            st.warning("Lesson content has not been generated yet.")
        else:
            is_edited = bool(lesson.get("edited_lesson"))
            st.subheader(f"📖 {active_content.get('lesson_title', lesson['title'])}")
            if is_edited:
                st.caption("ℹ️ Showing latest **Instructor-Edited / Revised Version**.")
            else:
                st.caption("ℹ️ Showing **Original AI-Generated Version**.")

            # Top Badge Bar
            dur = active_content.get("estimated_total_minutes", 45)
            lvl = active_content.get("difficulty_level", "Intermediate")
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <span class="duration-pill">⏱️ Total Duration: {dur} Minutes</span>
                <span class="duration-pill">📊 Level: {lvl}</span>
                <span class="duration-pill">👥 Dual-Mode: Self-Learning & Classroom</span>
            </div>
            """, unsafe_allow_html=True)

            # 14-Section Accordion
            with st.expander("1. Introduction (3 Minutes)", expanded=True):
                st.markdown(active_content.get("introduction", ""))

            with st.expander("2. Prerequisites & Key Concepts (5 Minutes)", expanded=True):
                st.markdown("**Prerequisites:**")
                for p in active_content.get("prerequisites", []):
                    st.markdown(f"- {p}")
                st.markdown("**Key Concepts:**")
                for kc in active_content.get("key_concepts", []):
                    st.markdown(f"- **{kc.get('concept')}**: {kc.get('definition')}")

            with st.expander("3. Detailed Explanations (15 Minutes)", expanded=True):
                st.markdown(active_content.get("detailed_explanations", ""))

            with st.expander("4. Real-World Applied Scenarios (7 Minutes)", expanded=True):
                for ex in active_content.get("real_world_examples", []):
                    st.markdown(f"**Scenario:** {ex.get('scenario')} (`{ex.get('method_used', '')}`)")
                    st.markdown(ex.get("explanation", ""))
                    st.divider()

            with st.expander("5. Practical Industry Applications", expanded=False):
                st.markdown(active_content.get("practical_applications", ""))

            with st.expander("6. Learning Activities (7 Minutes)", expanded=True):
                for act in active_content.get("learning_activities", []):
                    st.markdown(f"**Exercise:** {act.get('activity_title')}")
                    st.markdown(f"**Instructions:**\n{act.get('instructions')}")
                    st.info(f"**Expected Outcome:** {act.get('expected_outcome')}")

            with st.expander("7. Knowledge Check Questions (5 Minutes)", expanded=True):
                for q in active_content.get("knowledge_check_questions", []):
                    st.markdown(f"**Q{q.get('question_id')}: {q.get('question')}**")
                    for opt in q.get("options", []):
                        st.markdown(f"- {opt}")
                    st.success(f"**Correct Answer:** {q.get('correct_answer')}\n\n*Explanation:* {q.get('explanation')}")

            with st.expander("8. Answers and Pedagogical Explanations", expanded=False):
                st.markdown(active_content.get("answers_and_explanations", ""))

            with st.expander("9. Lesson Summary (3 Minutes)", expanded=False):
                st.markdown(active_content.get("lesson_summary", ""))

            with st.expander("10. Additional Learning Resources & References", expanded=False):
                st.markdown("**YouTube Videos:**")
                for res in active_content.get("additional_learning_resources", []):
                    st.markdown(f"- [{res.get('title')}]({res.get('url')}) ({res.get('type')})")
                st.markdown("**Research Documentation & Books:**")
                for ref in active_content.get("references_and_source_links", []):
                    st.markdown(f"- [{ref.get('source')}]({ref.get('url')})")

# =====================================================================
# VIEW 5: FACTUAL ACCURACY QC
# =====================================================================
elif "5. 🛡️ Factual Accuracy QC" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        report = lesson.get("factual_qc_report")
        st.subheader(f"🛡️ QC Agent 1: Research & Factual Accuracy Audit")
        st.caption(f"Lesson: {lesson['title']}")

        if not report:
            st.info("Factual accuracy audit has not been generated for this lesson.")
            if st.button("Run Factual Accuracy QC"):
                with st.spinner("Auditing factual claims against research evidence..."):
                    updated = lesson_service.retry_stage(lesson["id"], "qc")
                    st.rerun()
        else:
            score = report.get("overall_score", 0)
            status = report.get("verification_status", "Passed")
            score_color = get_score_color(score)

            # Header Score Card
            st.markdown(f"""
            <div class="content-box" style="display: flex; justify-content: space-between; align-items: center; border-left: 6px solid {score_color};">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 700; color: #0f172a;">Overall Factual Accuracy Score</span><br/>
                    <span style="font-size: 0.85rem; color: #64748b;">Auditor Verification Status: <b>{status}</b></span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: {score_color};">{score} <span style="font-size: 1rem; color: #94a3b8;">/ 100</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Claim Statistics
            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1:
                st.metric("Claims Evaluated", report.get("claims_evaluated_count", 0))
            with sc2:
                st.metric("Supported Claims", report.get("supported_claims_count", 0))
            with sc3:
                st.metric("Unsupported Claims", report.get("unsupported_claims_count", 0))
            with sc4:
                st.metric("Questionable Claims", report.get("questionable_claims_count", 0))

            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown("#### 🔍 Identified Issues & Auditor Findings")
            issues = report.get("identified_issues", [])
            if not issues:
                st.success("✅ No factual discrepancies, outdated claims, or unsupported assertions detected!")
            else:
                for idx, iss in enumerate(issues, 1):
                    sev = iss.get("severity", "Medium")
                    sev_class = f"severity-{sev.lower()}"
                    with st.container():
                        st.markdown(f"""
                        <div class="content-box">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: 600; color: #1e3a8a;">#{idx}. {iss.get('issue_type')}</span>
                                <span class="{sev_class}">{sev.upper()} SEVERITY</span>
                            </div>
                            <p style="margin: 0.4rem 0; font-size: 0.9rem;"><b>Audited Claim:</b> <i>"{iss.get('claim')}"</i></p>
                            <p style="color: #475569; font-size: 0.88rem; margin: 0.3rem 0;"><b>Explanation:</b> {iss.get('explanation')}</p>
                            <div style="background: #f8fafc; padding: 0.5rem; border-radius: 6px; font-size: 0.85rem; margin-top: 0.4rem;">
                                <b>Suggested Correction:</b> {iss.get('suggested_correction')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("#### 📚 Source Credibility & Evidence Verification")
            for sc in report.get("source_credibility_audit", []):
                st.markdown(f"- **{sc.get('domain')}**: Credibility `{sc.get('credibility')}` | Relevance `{sc.get('relevance')}`")

            st.markdown("#### 📝 Auditor Summary")
            st.info(report.get("final_summary", "Factual audit complete."))

            if st.button("🔄 Re-run Factual QC Audit", key="btn_rerun_fact_qc"):
                with st.spinner("Re-evaluating factual accuracy..."):
                    lesson_service.retry_stage(lesson["id"], "qc")
                    st.success("QC Report updated!")
                    st.rerun()

# =====================================================================
# VIEW 6: INSTRUCTIONAL QUALITY QC
# =====================================================================
elif "6. 🎯 Instructional Quality QC" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        report = lesson.get("instructional_qc_report")
        st.subheader(f"🎯 QC Agent 2: Instructional Quality & Pacing Audit")
        st.caption(f"Lesson: {lesson['title']}")

        if not report:
            st.info("Instructional quality audit has not been generated for this lesson.")
            if st.button("Run Instructional Quality QC"):
                with st.spinner("Auditing pedagogical flow and 45-minute pacing..."):
                    updated = lesson_service.retry_stage(lesson["id"], "qc")
                    st.rerun()
        else:
            score = report.get("overall_score", 0)
            status = report.get("status", "High Quality")
            score_color = get_score_color(score)

            st.markdown(f"""
            <div class="content-box" style="display: flex; justify-content: space-between; align-items: center; border-left: 6px solid {score_color};">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 700; color: #0f172a;">Instructional Quality Score</span><br/>
                    <span style="font-size: 0.85rem; color: #64748b;">Pedagogical Standard: <b>{status}</b></span>
                </div>
                <div style="font-size: 2.2rem; font-weight: 800; color: {score_color};">{score} <span style="font-size: 1rem; color: #94a3b8;">/ 100</span></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 📊 Pedagogical Sub-Scores")
            sub1, sub2, sub3, sub4, sub5 = st.columns(5)
            with sub1:
                st.metric("Objective Alignment", f"{report.get('objective_alignment_score', 0)}/100")
            with sub2:
                st.metric("Explanation Clarity", f"{report.get('explanation_clarity_score', 0)}/100")
            with sub3:
                st.metric("Example Relevance", f"{report.get('example_relevance_score', 0)}/100")
            with sub4:
                st.metric("Activity Effectiveness", f"{report.get('activity_effectiveness_score', 0)}/100")
            with sub5:
                st.metric("Knowledge Check", f"{report.get('knowledge_check_quality_score', 0)}/100")

            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown("#### ⏱️ Time Allocation & 45-Minute Ceiling Audit")
            t_audit = report.get("time_allocation_audit", {})
            st.markdown(f"""
            <div class="content-box" style="background: #f8fafc;">
                <b>Total Allocated Time:</b> {t_audit.get('total_allocated_minutes', 45)} Minutes &nbsp;|&nbsp;
                <b>Within 45-Min Constraint:</b> {'✅ Compliant' if t_audit.get('is_within_limit', True) else '❌ Exceeded'}<br/>
                <p style="color: #475569; font-size: 0.9rem; margin-top: 0.4rem;">{t_audit.get('evaluation', '')}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### ⚠️ Identified Instructional Gaps & Improvements")
            gaps = report.get("instructional_gaps", [])
            if not gaps:
                st.success("✅ No pedagogical bottlenecks or instructional gaps identified.")
            else:
                for idx, g in enumerate(gaps, 1):
                    sev = g.get("severity", "Medium")
                    sev_class = f"severity-{sev.lower()}"
                    with st.container():
                        st.markdown(f"""
                        <div class="content-box">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: 600; color: #1e3a8a;">#{idx}. Section: {g.get('section')}</span>
                                <span class="{sev_class}">{sev.upper()} SEVERITY</span>
                            </div>
                            <p style="color: #334155; font-size: 0.9rem; margin: 0.4rem 0;"><b>Instructional Gap:</b> {g.get('gap')}</p>
                            <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 6px; font-size: 0.85rem;">
                                <b>Suggested Improvement:</b> {g.get('suggested_improvement')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("#### 👥 Dual-Mode Pedagogical Suitability")
            dual = report.get("dual_mode_suitability", {})
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"**Self-Directed Learning Rating:** `{dual.get('self_learning_rating', 'Good')}`")
            with d2:
                st.markdown(f"**Instructor-Led Facilitation Rating:** `{dual.get('instructor_led_rating', 'Good')}`")
            if dual.get("notes"):
                st.caption(dual.get("notes"))

            st.markdown("#### 📝 Auditor Summary")
            st.info(report.get("final_summary", "Instructional audit complete."))

            if st.button("🔄 Re-run Instructional QC Audit", key="btn_rerun_inst_qc"):
                with st.spinner("Re-evaluating instructional quality..."):
                    lesson_service.retry_stage(lesson["id"], "qc")
                    st.success("QC Report updated!")
                    st.rerun()

# =====================================================================
# VIEW 7: REVIEW AND EDIT
# =====================================================================
elif "7. ✏️ Review and Edit" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        st.subheader(f"✏️ Instructor Review & Editing Suite")
        st.caption("Inspect generated content, apply automated QC recommendations, regenerate individual sections, or edit text directly.")

        # Active content: edited version takes precedence
        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson", {})
        original_lesson = lesson.get("generated_lesson", {})

        tab_edit, tab_recs, tab_regen = st.tabs([
            "📝 Direct Section Editor",
            "💡 Apply QC Recommendations",
            "⚡ Section-by-Section AI Regeneration"
        ])

        with tab_edit:
            st.markdown("#### Edit Lesson Content Directly")
            st.caption("Changes will be saved into the instructor-revised version without overwriting the original AI generation.")

            with st.form("instructor_edit_form"):
                new_title = st.text_input("Lesson Title", value=active_lesson.get("lesson_title", lesson["title"]))
                new_obj = st.text_area("Learning Objective", value=active_lesson.get("learning_objective", lesson["learning_objective"]), height=90)
                new_intro = st.text_area("Introduction (3 Mins)", value=active_lesson.get("introduction", ""), height=120)
                new_detailed = st.text_area("Detailed Explanations (15 Mins)", value=active_lesson.get("detailed_explanations", ""), height=220)
                new_practical = st.text_area("Practical Applications", value=active_lesson.get("practical_applications", ""), height=110)
                new_summary = st.text_area("Lesson Summary (3 Mins)", value=active_lesson.get("lesson_summary", ""), height=100)

                save_submitted = st.form_submit_button("💾 Save Instructor Edits", type="primary")

            if save_submitted:
                updated_copy = dict(active_lesson)
                updated_copy["lesson_title"] = new_title
                updated_copy["learning_objective"] = new_obj
                updated_copy["introduction"] = new_intro
                updated_copy["detailed_explanations"] = new_detailed
                updated_copy["practical_applications"] = new_practical
                updated_copy["lesson_summary"] = new_summary

                lesson_service.save_instructor_edits(lesson["id"], updated_copy)
                st.success("✅ Instructor edits successfully saved!")
                st.rerun()

        with tab_recs:
            st.markdown("#### QC Recommendation System")
            st.caption("Synthesized recommendations from both QC Agent 1 (Factual Accuracy) and QC Agent 2 (Instructional Quality).")

            f_rep = lesson.get("factual_qc_report")
            i_rep = lesson.get("instructional_qc_report")
            recs = rec_agent.extract_recommendations(f_rep, i_rep)
            applied_ids = lesson.get("applied_recommendations") or []

            if not recs:
                st.info("No specific recommendations generated yet. Both QC reports must be completed first.")
            else:
                for r in recs:
                    rid = r["id"]
                    is_applied = rid in applied_ids
                    sev = r["severity"]
                    sev_class = f"severity-{sev.lower()}"

                    with st.container():
                        st.markdown(f"""
                        <div class="content-box" style="border-left: 4px solid {'#10b981' if is_applied else '#3b82f6'};">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: 600; color: #1e3a8a;">{r.get('title')}</span>
                                <div>
                                    <span class="{sev_class}">{sev.upper()}</span>
                                    <span style="font-size: 0.8rem; margin-left: 8px; color: #64748b;">Source: {r.get('source')}</span>
                                </div>
                            </div>
                            <p style="font-size: 0.88rem; color: #334155; margin: 0.35rem 0;"><b>Issue:</b> {r.get('description')}</p>
                            <p style="font-size: 0.88rem; color: #047857; margin: 0.35rem 0;"><b>Proposed Action:</b> {r.get('recommendation')}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        col_btn, _ = st.columns([1, 4])
                        with col_btn:
                            if is_applied:
                                st.success("✅ Applied")
                            else:
                                if st.button(f"Apply Recommendation", key=f"apply_{rid}"):
                                    lesson_service.apply_qc_recommendation(lesson["id"], r)
                                    st.success(f"Applied {rid} to active lesson!")
                                    st.rerun()

                st.divider()
                if st.button("🔄 Rerun Dual QC on Revised Lesson", key="btn_rerun_dual_qc"):
                    with st.spinner("Rerunning both QC Agents on latest instructor revisions..."):
                        qc_service.rerun_qc_for_lesson(lesson["id"])
                        st.success("Both QC reports successfully updated for the revised lesson!")
                        st.rerun()

        with tab_regen:
            st.markdown("#### Selective AI Section Regeneration")
            st.caption("Instruct the AI to rewrite only one section (e.g. Detailed Explanations or Learning Activities) while preserving the rest of the lesson.")

            sec_choice = st.selectbox(
                "Select Section to Regenerate",
                [
                    "detailed_explanations",
                    "learning_activities",
                    "real_world_examples",
                    "introduction",
                    "knowledge_check_questions",
                    "lesson_summary"
                ]
            )

            prompt_instructions = st.text_area(
                "Instructor Prompt / Specific Improvements Needed",
                placeholder="e.g. Include a comparative ASCII table of HTTP headers, or simplify the explanation for beginner developers.",
                height=90
            )

            if st.button("⚡ Regenerate Selected Section", type="primary"):
                with st.spinner(f"Regenerating section '{sec_choice}' with AI..."):
                    lesson_service.regenerate_lesson_section(lesson["id"], sec_choice, prompt_instructions)
                    st.success(f"Section '{sec_choice}' successfully regenerated and saved!")
                    st.rerun()

# =====================================================================
# VIEW 8: PREVIEW LESSON
# =====================================================================
elif "8. 👁️ Preview Lesson" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson", {})
        st.subheader("👁️ Live Preview: Student & Classroom View")
        st.markdown(f"**Viewing:** *{active_lesson.get('lesson_title', lesson['title'])}*")
        st.divider()

        # Render complete markdown preview
        rendered_md = md_exporter.export_lesson(active_lesson)
        st.markdown(rendered_md)

        # Interactive Student Knowledge Check
        questions = active_lesson.get("knowledge_check_questions", [])
        if questions:
            st.divider()
            st.markdown("### 📝 Interactive Student Knowledge Check")
            st.caption("Test your understanding directly. Select an answer and submit to receive immediate pedagogical feedback.")
            for q in questions:
                qid = q.get("question_id", 1)
                q_text = q.get("question", "")
                opts = q.get("options", [])
                correct = q.get("correct_answer", "")
                explanation = q.get("explanation", "")

                st.markdown(f"**Question {qid}:** {q_text}")
                user_choice = st.radio(f"Select option for Q{qid}:", opts, key=f"quiz_radio_{lesson['id'][:6]}_{qid}", label_visibility="collapsed")

                if st.button(f"Submit Answer for Q{qid}", key=f"btn_check_q_{lesson['id'][:6]}_{qid}"):
                    if user_choice.strip() == correct.strip():
                        st.success(f"🎉 **Correct!**\n\n{explanation}")
                    else:
                        st.error(f"❌ **Incorrect.** The correct answer is: **{correct}**\n\n*Pedagogical Explanation:* {explanation}")
                st.write("")

# =====================================================================
# VIEW 9: EXPORT LESSON
# =====================================================================
elif "9. 📤 Export Lesson" in selected_nav:
    render_top_lesson_switcher()
    lesson = get_active_lesson()
    if not lesson:
        st.warning("No active lesson loaded. Please select or create a lesson first.")
    else:
        active_lesson = lesson.get("edited_lesson") or lesson.get("generated_lesson", {})
        title = active_lesson.get("lesson_title", lesson["title"])
        f_rep = lesson.get("factual_qc_report", {})
        i_rep = lesson.get("instructional_qc_report", {})

        st.subheader(f"📤 Export Educational Package: {title}")
        st.markdown("Export the final lesson, research citations, and independent QC reports in professional PDF, Markdown, and JSON formats.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📄 Document Exports (PDF & Markdown)")

            # 1. Lesson PDF
            pdf_path = os.path.join("exports", f"Lesson_{lesson['id'][:8]}.pdf")
            try:
                pdf_exporter.export_lesson_pdf(active_lesson, pdf_path)
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "📥 Download Lesson as PDF",
                    data=pdf_bytes,
                    file_name=f"{title.replace(' ', '_')}_Lesson.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF export error: {e}")

            # 2. Lesson Markdown
            md_content = md_exporter.export_lesson(active_lesson)
            st.download_button(
                "📥 Download Lesson as Markdown",
                data=md_content,
                file_name=f"{title.replace(' ', '_')}_Lesson.md",
                mime="text/markdown",
                use_container_width=True
            )

            # 3. Complete Markdown Package
            pkg_md = md_exporter.export_complete_package(lesson)
            st.download_button(
                "📥 Download Complete Package (.md)",
                data=pkg_md,
                file_name=f"{title.replace(' ', '_')}_Complete_Dossier.md",
                mime="text/markdown",
                use_container_width=True
            )

            # 4. Master Dossier PDF (Lesson + Both QC Reports)
            master_pdf_path = os.path.join("exports", f"Master_Dossier_{lesson['id'][:8]}.pdf")
            try:
                pdf_exporter.export_complete_package_pdf(lesson, master_pdf_path)
                with open(master_pdf_path, "rb") as f:
                    master_pdf_bytes = f.read()
                st.download_button(
                    "📥 Download Master Dossier PDF (All-in-One)",
                    data=master_pdf_bytes,
                    file_name=f"{title.replace(' ', '_')}_Master_Dossier.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Master Dossier PDF error: {e}")

        with col2:
            st.markdown("#### 🛡️ Quality Control Reports")

            # Factual QC PDF
            if f_rep:
                fqc_pdf_path = os.path.join("exports", f"Factual_QC_{lesson['id'][:8]}.pdf")
                try:
                    pdf_exporter.export_factual_qc_pdf(f_rep, title, fqc_pdf_path)
                    with open(fqc_pdf_path, "rb") as f:
                        fqc_bytes = f.read()
                    st.download_button(
                        "📥 Download Factual QC Report (PDF)",
                        data=fqc_bytes,
                        file_name=f"{title.replace(' ', '_')}_Factual_QC.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Factual QC PDF error: {e}")

            # Instructional QC PDF
            if i_rep:
                iqc_pdf_path = os.path.join("exports", f"Instructional_QC_{lesson['id'][:8]}.pdf")
                try:
                    pdf_exporter.export_instructional_qc_pdf(i_rep, title, iqc_pdf_path)
                    with open(iqc_pdf_path, "rb") as f:
                        iqc_bytes = f.read()
                    st.download_button(
                        "📥 Download Instructional QC Report (PDF)",
                        data=iqc_bytes,
                        file_name=f"{title.replace(' ', '_')}_Instructional_QC.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Instructional QC PDF error: {e}")

            # Complete JSON Dump
            json_str = json.dumps(lesson, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Download Raw Structured Data (.json)",
                data=json_str,
                file_name=f"{title.replace(' ', '_')}_data.json",
                mime="application/json",
                use_container_width=True
            )

# =====================================================================
# VIEW 10: SAVED LESSONS
# =====================================================================
elif "10. 💾 Saved Lessons" in selected_nav:
    st.subheader("💾 Saved Lessons Repository")
    st.caption("Browse, search, load, and manage previously saved lessons in the SQLite database.")

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        search_kw = st.text_input("🔍 Search Lessons by Title or Objective", placeholder="Type keywords...")
    with col_s2:
        filter_status = st.selectbox("Filter Status", ["all", "completed", "needs_review", "processing", "failed"])

    lessons = db.list_lessons(limit=100, status_filter=filter_status, search_query=search_kw)

    if not lessons:
        st.info("No saved lessons match the criteria.")
    else:
        st.write(f"Showing **{len(lessons)}** saved lesson(s):")
        for item in lessons:
            lid = item["id"]
            title = item["title"]
            obj = item["learning_objective"]
            status = item["status"]
            created = item["created_at"].split("T")[0]
            status_class = f"status-{status.replace('_', '-')}"

            with st.container():
                st.markdown(f"""
                <div class="content-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; font-size: 1.1rem; color: #1e3a8a;">{title}</span>
                        <span class="status-badge {status_class}">{status.upper()}</span>
                    </div>
                    <p style="color: #475569; font-size: 0.9rem; margin: 0.4rem 0;">{obj}</p>
                    <span style="font-size: 0.8rem; color: #94a3b8;">Created: {created} &nbsp;|&nbsp; ID: <code>{lid}</code></span>
                </div>
                """, unsafe_allow_html=True)

                b1, b2, _ = st.columns([1, 1, 4])
                with b1:
                    if st.button("Load Workspace", key=f"load_btn_{lid}"):
                        st.session_state["active_lesson_id"] = lid
                        st.session_state["edit_buffer"] = {}
                        st.success(f"Loaded '{title}'!")
                        st.rerun()
                with b2:
                    if st.button("🗑️ Delete", key=f"del_btn_{lid}"):
                        st.session_state["delete_confirm_id"] = lid
                        st.rerun()

                # Confirmation modal
                if st.session_state.get("delete_confirm_id") == lid:
                    st.warning(f"⚠️ Are you sure you want to delete '{title}'? This action cannot be undone.")
                    cb1, cb2 = st.columns([1, 4])
                    with cb1:
                        if st.button("Yes, Confirm Delete", key=f"conf_del_{lid}", type="primary"):
                            db.delete_lesson(lid)
                            if st.session_state.get("active_lesson_id") == lid:
                                st.session_state["active_lesson_id"] = None
                            st.session_state["delete_confirm_id"] = None
                            st.success(f"Lesson deleted.")
                            st.rerun()
                    with cb2:
                        if st.button("Cancel", key=f"cancel_del_{lid}"):
                            st.session_state["delete_confirm_id"] = None
                            st.rerun()

