from typing import Dict
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

# Авторизация
CREDS = Credentials.from_service_account_file(
    Path(__file__).with_name("creds.json"),
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
gc = gspread.authorize(CREDS)

# Эти значения считаем заменами
BAD_MARKS = {"з", "з.", "замена", "отп", "отп.", "otp", "оТП",
             "З", "З.", "ОТП", "ОТП.", "ОТПУСК"}

def load_and_filter(
    doc_id: str,
    sheet_name: str = "Июль 2025",
    period: str = "month"
) -> Dict:
    """Загружает и фильтрует таблицу по периоду (today, tomorrow, week, month).
    При этом всё ещё работает логика ЗАМЕН и ОТПУСКОВ в отдельной колонке."""

    ws = gc.open_by_key(doc_id).worksheet(sheet_name)
    raw = ws.get_all_values()

    days = [d.strip() for d in raw[1][3:] if d.strip()]  # D2… AH2
    employees, replacements = {}, {d: "" for d in days}

    for row in raw[2:]:
        name = row[0].strip()
        if not any(cell.strip() for cell in row):
            break
        shifts = [c.strip() for c in row[3:3+len(days)]]

        if not name:
            for d, s in zip(days, shifts):
                if s:
                    replacements[d] = s
            continue

        emp = {}
        for d, s in zip(days, shifts):
            if not s:
                continue
            if s.lower() in BAD_MARKS:
                replacements[d] = s
            else:
                emp[d] = s
        employees[name] = emp

    col_names = list(employees.keys())
    if any(replacements.values()):
        col_names.append("Замены")

    # ➜ фильтрация по периоду
    today = datetime.now().day
    if period == "today":
        wanted = {str(today)}
    elif period == "tomorrow":
        wanted = {str(today + 1)}
    elif period == "week":
        wanted = {str(today + i) for i in range(7)}
    else:
        wanted = set(days)  # месяц целиком

    # итоговая таблица
    info = {}
    for row in raw[2:]:
        name = row[0].strip()
        if not name:
            continue
        phone = row[1].strip() if len(row) > 1 and row[1].strip() else "не указано"
        telegram = row[2].strip() if len(row) > 2 and row[2].strip() else "не указано"
        info[name] = {"phone": phone, "telegram": telegram}

    table = []
    for d in days:
        if d not in wanted:
            continue
        row = [d]
        for name in employees:
            row.append(employees[name].get(d, ""))
        if "Замены" in col_names:
            row.append(replacements.get(d, ""))
        table.append(row)

    return {
        "days": list(wanted),
        "cols": col_names,
        "table": table,
        "info": info
    }
