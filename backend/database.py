from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent / "dbFiles" / "users.db"  # ← добавили .parent

def add_user(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)",
                     (user_id,))


def init():
    """Создаём таблицу users, если её нет."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)