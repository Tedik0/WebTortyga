import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from typing import List, Tuple
import sqlite3
from backend.sheets_config import GOOGLE_SHEETS

CREDS = Credentials.from_service_account_file(
    Path(__file__).with_name("creds.json"),
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
gc = gspread.authorize(CREDS)

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

def approve_ticket(ticket_id: int):
    # 1. Достаём тикет из базы
    with sqlite3.connect(TICKET_DB) as conn:
        cur = conn.execute("SELECT date, name, location FROM tickets WHERE id = ?", (ticket_id,))
        row = cur.fetchone()

    if not row:
        raise ValueError("Тикет не найден")

    date, name, location = row

    # 2. Ищем ID таблицы
    doc_id = GOOGLE_SHEETS.get(location)
    if not doc_id:
        raise ValueError("Неизвестная точка")

    sh = gc.open_by_key(doc_id)
    ws = sh.worksheet("Июль 2025")

    # 3. Ставим "З" по дате (в графике)
    raw = ws.get_all_values()
    days_row = raw[1][3:]  # D2 и далее
    col_offset = 3
    col = None
    for i, val in enumerate(days_row):
        if val.strip() == date.strip():
            col = i + col_offset + 1  # gspread — 1-based indexing
            break

    if col is None:
        raise ValueError(f"Дата {date} не найдена в графике")

    # Ищем первую пустую строку с именем (A3…A...)
    for row_num in range(3, len(raw) + 5):
        name_cell = ws.cell(row_num, 1).value
        if name_cell and name_cell.strip().lower() == name.strip().lower():
            ws.update_cell(row_num, col, "З")
            break

    # 4. Добавляем в таблицу замен
    # Ищем первую строку после D:X где колонка D пустая
    for row_num in range(3, len(raw) + 100):
        if not ws.cell(row_num, 4).value:
            # D:E — дата
            ws.merge_cells(f"D{row_num}:E{row_num}")
            ws.update(f"D{row_num}", date)

            # F:M — имя
            ws.merge_cells(f"F{row_num}:M{row_num}")
            ws.update(f"F{row_num}", name)

            # N:T — точка
            ws.merge_cells(f"N{row_num}:T{row_num}")
            ws.update(f"N{row_num}", location)
            break