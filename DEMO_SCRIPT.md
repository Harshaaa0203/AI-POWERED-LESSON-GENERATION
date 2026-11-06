# 🎬 Video Demonstration Script: AI-Powered Lesson Creation Tool
**Target Duration:** 5 to 7 Minutes  
**Audience:** Technical Interviewers, AI Research Leads, and Senior Engineering Evaluators  
**Application URL:** `http://localhost:8501`

---

## ⏱️ Video Timeline Summary
- **[0:00 - 0:45]** Part 1: Project Introduction & High-Level Architecture
- **[0:45 - 1:30]** Part 2: Starting the Workflow (Test Case 1: HTTP Requests & Responses)
- **[1:30 - 2:30]** Part 3: Real Multi-Source Research (Web, Books, YouTube)
- **[2:30 - 3:30]** Part 4: The 14-Section Structured 45-Minute Lesson
- **[3:30 - 4:45]** Part 5: Dual Independent Quality Control Agents (Factual & Instructional)
- **[4:45 - 5:45]** Part 6: Instructor Review, Applying QC Recommendations & Section Regeneration
- **[5:45 - 6:30]** Part 7: Live Preview & Multi-Format PDF / Markdown Export
- **[6:30 - 7:00]** Part 8: Technology Stack Summary & Conclusion

---

## 🎙️ Complete Word-for-Word Script

### [0:00 - 0:45] Part 1: Introduction & High-Level Architecture
*(Visual: Screen showing Streamlit Dashboard with KPI cards for Total Lessons, Completed Lessons, Average Factual Score, and Average Pedagogical Score.)*

**Presenter (Voiceover):**  
"Hello everyone, and welcome. Today, I'm presenting the **AI-Powered Lesson Creation Tool**, a full-stack educational system designed to solve one of generative AI's biggest flaws in education: hallucinated, unstructured, and bloated content.

Our system takes just two inputs—a **Lesson Title** and a **Learning Objective**—and autonomously executes a complete curriculum engineering workflow. 

It starts by conducting live, multi-source research across educational websites, bibliographic books, and YouTube videos. It then generates a structured lesson strictly calibrated to a 45-minute completion time. Most importantly, it subjects that lesson to **two independent Quality Control agents**: one for research factual accuracy, and another for pedagogical quality and pacing.

Let's see it in action."

---

### [0:45 - 1:30] Part 2: Starting the Workflow (Mandatory Benchmark Case 1)
*(Visual: Clicking on "2. ➕ Create New Lesson" in the sidebar navigation.)*

**Presenter (Voiceover):**  
"In the sidebar, we navigate to **Create New Lesson**. 

For this demonstration, we'll use the mandatory benchmark specified in our assignment guidelines:
- **Lesson Title:** `HTTP Requests and Responses`
- **Learning Objective:** `Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.`

I click **Start Creation**. 

Notice the real-time progress indicators:
First, it validates the inputs and initializes an ACID-compliant record in our SQLite database. 
Next, our dedicated Research Agent begins querying external web, book, and video sources.
Then, the Lesson Generator synthesizes the curriculum.
Finally, both independent QC agents audit the lesson in parallel. 

Within seconds, the complete pipeline is finished and verified!"

---

### [1:30 - 2:30] Part 3: Real Multi-Source Research
*(Visual: Clicking on "3. 🔍 Research Results" in the sidebar.)*

**Presenter (Voiceover):**  
"Now let's examine the **Research Dossier**. Unlike superficial tools that rely purely on internal LLM weights, our tool grounds every lesson in verified external evidence.

Here under **Web Sources**, you can see real technical documentation from MDN Web Docs, RFC specifications, and trusted educational platforms. Each source is evaluated by our `SourceValidator` for domain credibility and reachability.

Under **Book References**, our tool connects to the **Open Library Catalog** and Google Books API. Notice that it retrieves authentic titles like *'HTTP: The Definitive Guide'* with genuine author names and publication years—strictly avoiding fabricated references or hallucinated page numbers.

Under **YouTube Videos**, it discovers real, verified educational videos from top computer science channels such as *Gate Smashers*, *Traversy Media*, and *CS50*.

And finally, under **Verified Factual Anchors**, it extracts discrete factual claims directly supported by these sources."

---

### [2:30 - 3:30] Part 4: The 14-Section 45-Minute Lesson
*(Visual: Clicking on "4. 📖 Generated Lesson" in the sidebar.)*

**Presenter (Voiceover):**  
"Moving to **Generated Lesson**, we see our 14-section pedagogical framework designed strictly for a **45-minute completion time**:

1. **Introduction:** A 3-minute engaging hook and preview.
2. **Prerequisites & Key Concepts:** 5 minutes, defining Client-Server architecture, HTTP verbs, and Idempotency.
3. **Detailed Explanations:** 15 minutes of in-depth conceptual breakdown distinguishing GET and POST methods, followed by 2xx Success, 4xx Client Errors, and 5xx Server Errors.
4. **Real-World Applied Scenarios:** 7 minutes analyzing e-commerce search queries versus secure payment checkout.
5. **Practical Industry Applications:** Discussing REST API design.
6. **Learning Activities:** A 7-minute hands-on exercise guiding students through browser Developer Tools Network inspection.
7. **Knowledge Check Questions:** 5 minutes of diagnostic multiple-choice questions testing diagnostic ability.
8. **Answers and Explanations**
9. **Lesson Summary:** A 3-minute synthesis.
10. **Additional Resources & References:** Directly linking the verified books, documentation, and YouTube videos.

The lesson is structured to support both self-paced learners and instructor-led classroom teaching."

---

### [3:30 - 4:45] Part 5: Dual Independent Quality Control Agents
*(Visual: Clicking on "5. 🛡️ Factual Accuracy QC" then "6. 🎯 Instructional Quality QC".)*

**Presenter (Voiceover):**  
"Now let's inspect the core innovation of our system: **Dual Independent Quality Control**.

First, **QC Agent 1: Research & Factual Accuracy**.  
This agent acts as an adversarial fact-checker. It doesn't approve content just because it sounds fluent. It audits every claim against our retrieved research evidence. Here, it gives an overall accuracy score of **94 out of 100**, verifying 11 out of 12 claims. It highlights an identified nuance with a Low severity tag regarding RFC 7231 guidelines on GET request bodies, cites the exact RFC section, and suggests a technical correction.

Next, we switch to **QC Agent 2: Instructional Quality & Pacing**.  
This agent operates completely independently and evaluates pedagogical effectiveness against the stated learning objective. It provides distinct sub-scores:
- Objective Alignment: 98%
- Explanation Clarity: 94%
- Example Relevance: 92%
- Activity Effectiveness: 90%
- Knowledge Check Quality: 92%

Crucially, it executes a **Time Allocation Audit**, verifying that the minute breakdown precisely equals 45 minutes without cognitive overload, and evaluates dual-mode suitability for both self-study and classroom facilitation."

---

### [4:45 - 5:45] Part 6: Instructor Review & Recommendation System
*(Visual: Clicking on "7. ✏️ Review and Edit".)*

**Presenter (Voiceover):**  
"Our system firmly believes in human-in-the-loop governance. Under **Review and Edit**, instructors have total control:

In the **Direct Section Editor**, instructors can edit any section text or objective. Edits are saved into a separate revised version in SQLite—never silently overwriting the original AI draft.

In the **QC Recommendation System**, the findings of both QC agents are merged into actionable cards. An instructor can inspect an issue, see the auditor's recommendation, and click **Apply Recommendation** to automatically incorporate the enhancement into the revised lesson.

Furthermore, in **Section-by-Section AI Regeneration**, an instructor can select just one specific section—like *Detailed Explanations*—provide custom guidance, and regenerate only that section while leaving the other 13 sections completely intact. Instructors can then rerun the dual QC pipeline on their revised draft."

---

### [5:45 - 6:30] Part 7: Live Preview & Document Exports
*(Visual: Navigating to "8. 👁️ Preview Lesson" then "9. 📤 Export Lesson".)*

**Presenter (Voiceover):**  
"Under **Preview Lesson**, we get a full, distraction-free rendered preview of the latest instructor-approved version.

When it's time to distribute, we navigate to **Export Lesson**.
Our system features publication-grade exports built with **ReportLab**:
- **Download Lesson as PDF:** Produces a beautifully styled document with colored callouts, structured tables, and dynamic running headers with 'Page X of Y' numbering.
- **Download Lesson as Markdown:** Clean GitHub-Flavored Markdown for wikis or learning management systems.
- **Download Factual QC Report (PDF)** and **Instructional QC Report (PDF):** Independent audit certificates.
- **Complete Lesson Package:** A combined dossier containing the lesson, all research references, and both audit reports."

---

### [6:30 - 7:00] Part 8: Technology Stack & Conclusion
*(Visual: Navigating to "10. 💾 Saved Lessons" showing search, filtering, and delete confirmation, then returning to Dashboard.)*

**Presenter (Voiceover):**  
"To summarize our technology stack:
- **Frontend:** Streamlit with custom CSS.
- **Backend:** Modular Python service architecture.
- **AI Integration:** Google Gemini API with support for Gemini 2.0 Flash and 1.5, backed by an intelligent offline demonstration engine.
- **Research:** DuckDuckGo Search, Open Library API, and YouTube Data discovery.
- **Database:** SQLite for persistent ACID storage.
- **Exports:** ReportLab PDF and Markdown.

Every requirement from the Task and Submission Guide has been implemented, tested with 13 automated tests, and verified end-to-end.

Thank you for watching!"

