from pathlib import Path
import sqlite3

DB_DIR = Path(__file__).parent / "dbFiles"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "users.db"          # <— единый путь

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