import sqlite3
from contextlib import closing

DB_PATH = "jobs.db"


def init_db(db_path: str = DB_PATH) -> None:
    """إنشاء الجدول، وترحيل المعرّفات القديمة (أرقام فقط) لتبقى تابعة لنفذلي."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT,
                seen_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "UPDATE OR IGNORE seen_jobs "
            "SET job_id = 'nafezly:' || job_id WHERE job_id NOT LIKE '%:%'"
        )
        conn.commit()


def is_job_seen(job_id: str, db_path: str = DB_PATH) -> bool:
    """هل الوظيفة دي اتسجلت قبل كده؟"""
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    return row is not None


def mark_job_seen(job_id: str, title: str, db_path: str = DB_PATH) -> None:
    """تسجيل الوظيفة كـ 'تم التعامل معها'."""
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_jobs (job_id, title) VALUES (?, ?)",
            (job_id, title),
        )
        conn.commit()


def count_seen_jobs(platform: str | None = None, db_path: str = DB_PATH) -> int:
    """عدد الوظائف المسجلة (لمنصة معينة أو للكل). بنستخدمها لمعرفة أول تشغيل."""
    with closing(sqlite3.connect(db_path)) as conn:
        if platform:
            query = "SELECT COUNT(*) FROM seen_jobs WHERE job_id LIKE ?"
            return conn.execute(query, (f"{platform}:%",)).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]

import os

def get_last_update_id():
    if not os.path.exists("last_update.txt"):
        return 0
    with open("last_update.txt", "r") as f:
        return int(f.read().strip())

def save_last_update_id(update_id):
    with open("last_update.txt", "w") as f:
        f.write(str(update_id))
