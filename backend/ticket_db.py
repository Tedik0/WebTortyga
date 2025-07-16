import sqlite3
from pathlib import Path
from typing import List, Tuple

TICKET_DB = Path(__file__).parent.parent / "dbFiles" / "tickets.db"

def init_ticket_db():
    TICKET_DB.parent.mkdir(exist_ok=True)  # создаём папку dbFiles если нет
    with sqlite3.connect(TICKET_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL
            )
        """)

def get_all_tickets() -> List[Tuple]:
    with sqlite3.connect(TICKET_DB) as conn:
        cur = conn.execute("""
            SELECT id, user_id, date, name, location
            FROM tickets
            ORDER BY id DESC
        """)
        return cur.fetchall()
