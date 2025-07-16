import sqlite3
from pathlib import Path
from typing import List

DB_DIR  = Path(__file__).parent / "dbFiles"
DB_DIR.mkdir(exist_ok=True)
ADMINS_DB = DB_DIR / "admins.db"


def _connect():
    conn = sqlite3.connect(ADMINS_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)"
    )
    return conn


def add_admin(user_id: int) -> None:
    """Добавить ID в таблицу админов (idempotent)."""
    with _connect() as conn:
        conn.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))


def remove_admin(user_id: int) -> None:
    """Удалить ID из таблицы админов."""
    with _connect() as conn:
        conn.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом."""
    with _connect() as conn:
        cur = conn.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
        return cur.fetchone() is not None


def all_admins() -> List[int]:
    with _connect() as conn:
        cur = conn.execute("SELECT user_id FROM admins")
        return [row[0] for row in cur.fetchall()]
