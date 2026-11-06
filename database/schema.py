"""
Database schema definitions for the AI Lesson Creator.
"""

CREATE_LESSONS_TABLE = """
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    learning_objective TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing',
    research_sources TEXT,
    youtube_resources TEXT,
    book_sources TEXT,
    generated_lesson TEXT,
    edited_lesson TEXT,
    factual_qc_report TEXT,
    instructional_qc_report TEXT,
    applied_recommendations TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_lessons_status ON lessons(status);",
    "CREATE INDEX IF NOT EXISTS idx_lessons_created ON lessons(created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_lessons_title ON lessons(title);"
]
