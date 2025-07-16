from pathlib import Path
from flask import Flask, render_template, request, abort, jsonify, redirect
from backend.admin_db import is_admin          # ← база, созданная ранее
from backend.database import DB_PATH           # users.db – чтобы проверять, что uid существует
from backend.sheets_loader import load_and_filter
from backend.sheets_config import GOOGLE_SHEETS
import sqlite3
from typing import List, Tuple
from backend.ticket_db import get_all_tickets, init_ticket_db

app = Flask(__name__,
            template_folder="templates",
            static_folder="static")

TICKET_DB = Path(__file__).parent.parent / "dbFiles" / "tickets.db"

MONTH_RU = {
    1:"Январь",2:"Февраль",3:"Март",4:"Апрель",
    5:"Май",6:"Июнь",7:"Июль",8:"Август",
    9:"Сентябрь",10:"Октябрь",11:"Ноябрь",12:"Декабрь"
}

def user_exists(uid: int) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        # ➊ гарантируем, что таблица есть
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY
            )
        """)
        # ➋ ищем запись
        cur = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (uid,)
        )
        return cur.fetchone() is not None

# frontend/app.py
@app.route("/")
def index():
    uid = request.args.get("uid", type=int)
    if uid is None:
        return "UID не передан", 400
    if not user_exists(uid):
        return "Сначала нажмите /start в боте", 403
    if is_admin(uid):
        return render_template("admin.html", uid=uid)
    return render_template("user.html", uid=uid)


@app.route("/admin")
def admin_page():
    uid = request.args.get("uid", type=int)  # если нужен
    return render_template("admin.html", uid=uid)

@app.route("/user")
def user_page():
    uid = request.args.get("uid", type=int)
    return render_template("user.html", uid=uid)

@app.route("/api/whoami", methods=["POST"])
def whoami():
    data = request.get_json(silent=True) or {}
    uid  = data.get("uid")
    if uid is None or not user_exists(uid):
        return jsonify(role="unknown"), 403
    return jsonify(role="admin" if is_admin(uid) else "user")

@app.route("/schedule")
def list_sheets():
    uid = request.args.get("uid", type=int)
    if uid is None:
        return "UID не передан", 400
    if not user_exists(uid):
        return "Сначала нажмите /start в боте", 403

    return render_template("schedule_list.html", sheets=GOOGLE_SHEETS, uid=uid)


@app.route("/submit-ticket", methods=["POST"])
def submit_ticket():
    user_id  = request.form.get("user_id", type=int)
    date     = request.form.get("date")
    name     = request.form.get("name")
    location = request.form.get("location")
    print("FORM DATA:", request.form.to_dict())

    if not all([user_id, date, name, location]):
        print("FORM DATA:", request.form.to_dict())
        return "Не все поля заполнены", 400


    with sqlite3.connect(TICKET_DB) as conn:
        conn.execute("""
            INSERT INTO tickets (user_id, date, name, location)
            VALUES (?, ?, ?, ?)
        """, (user_id, date, name, location))

    return redirect(f"/schedule?uid={user_id}")



@app.route("/schedule/<doc_id>")
def schedule_pivot(doc_id):
    uid = request.args.get("uid", type=int)
    if uid is None:
        return "UID не передан", 400

    if doc_id not in GOOGLE_SHEETS.values():
        abort(404)

    point = next(k for k,v in GOOGLE_SHEETS.items() if v == doc_id)
    data  = load_and_filter(doc_id)
    title = f"Июль 2025 – {point}"

    return render_template("select_period.html", doc_id=doc_id, uid=uid)


@app.route("/schedule/<doc_id>/<period>")
def show_filtered_schedule(doc_id, period):
    uid = request.args.get("uid", type=int)
    if uid is None:
        return "UID не передан", 400
    data = load_and_filter(doc_id, sheet_name="Июль 2025", period=period)
    sheet_title = next((name for name, id_ in GOOGLE_SHEETS.items() if id_ == doc_id), doc_id)

    # переводим period
    RU_PERIODS = {
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "week": "Неделя",
        "month": "Месяц"
    }
    pretty_period = RU_PERIODS.get(period, period.capitalize())

    # финальный заголовок
    title = f"{pretty_period} — {sheet_title}"
    return render_template(
        "schedule_pivot.html",
        title=title,
        cols=data["cols"],
        table=data["table"],
        info=data.get("info", {}),
        doc_id=doc_id,
        uid=uid,  # ← вот это добавь
    )

@app.route("/tickets")
def show_tickets():
    uid = request.args.get("uid", type=int)
    if uid is None or not user_exists(uid):
        return "Сначала нажмите /start в боте", 403

    if not is_admin(uid):
        return "Доступ только для администраторов", 403

    tickets = get_all_tickets()
    return render_template("tickets.html", tickets=tickets, uid=uid)

if __name__ == "__main__":
    # Flask слушает 8080 — как и раньше
    init_ticket_db()
    app.run(debug=True, port=8080)
