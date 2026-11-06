"""
Seed script: Populates the SQLite database with the two mandatory benchmark lessons:
1. HTTP Requests and Responses
2. Binary Search Algorithm
This ensures that the dashboard, QC reports, and exports are immediately visible
when launching the Streamlit app for the first time.
"""

import sys
import logging
from services.lesson_service import LessonService
from database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def seed_benchmarks():
    print("🌱 Seeding database with mandatory benchmark test cases...")
    db = DatabaseManager()
    service = LessonService(db_manager=db)

    # 1. HTTP Requests and Responses
    print("Creating Benchmark 1: HTTP Requests and Responses...")
    l1 = service.create_lesson_pipeline(
        title="HTTP Requests and Responses",
        learning_objective="Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories."
    )
    print(f"✅ Benchmark 1 created with ID: {l1['id']}")

    # 2. Binary Search Algorithm
    print("Creating Benchmark 2: Binary Search Algorithm...")
    l2 = service.create_lesson_pipeline(
        title="Binary Search Algorithm",
        learning_objective="Explain the divide-and-conquer principle of binary search and analyze its logarithmic O(log n) time complexity."
    )
    print(f"✅ Benchmark 2 created with ID: {l2['id']}")

    stats = db.get_dashboard_stats()
    print("\n📊 Database Seeding Complete!")
    print(f"Total Lessons: {stats['total_lessons']}")
    print(f"Completed Lessons: {stats['completed_lessons']}")
    print(f"Average Factual QC Score: {stats['avg_factual_score']}/100")
    print(f"Average Instructional QC Score: {stats['avg_instructional_score']}/100")


if __name__ == "__main__":
    seed_benchmarks()
