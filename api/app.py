import os, sqlite3, json, urllib.request, urllib.parse
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
MAX_FILE_MB = 25


def db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        name TEXT, phone TEXT, email TEXT, task TEXT, comment TEXT, file_name TEXT
    )""")
    return con


def tg_send_text(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15)
    except Exception as e:
        app.logger.error("tg text: %s", e)


def tg_send_file(path, caption):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    boundary = "----leadform"
    body = b""
    def part(name, value):
        body = ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + name + "\"\r\n\r\n" + value + "\r\n").encode()
        return body
    fields = [("chat_id", TELEGRAM_CHAT_ID), ("caption", caption)]
    for n, v in fields:
        body += part(n, v)
    with open(path, "rb") as f:
        body += ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"document\"; filename=\"" + os.path.basename(path) + "\"\r\nContent-Type: application/octet-stream\r\n\r\n").encode()
        body += f.read()
        body += ("\r\n--" + boundary + "--\r\n").encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    try:
        urllib.request.urlopen(req, timeout=60)
    except Exception as e:
        app.logger.error("tg file: %s", e)


@app.post("/api/lead")
def lead():
    try:
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip()
        task = (request.form.get("task") or "").strip()
        comment = (request.form.get("comment") or "").strip()
    except Exception:
        return jsonify({"error": "Неверный формат запроса"}), 400

    if len(name) < 2:
        return jsonify({"error": "Введите корректное имя"}), 400
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 6:
        return jsonify({"error": "Введите корректный телефон"}), 400
    if email and not "@" in email:
        return jsonify({"error": "Введите корректный e-mail"}), 400

    file_name = None
    f = request.files.get("file")
    if f and f.filename:
        if f.content_length and f.content_length > MAX_FILE_MB * 1024 * 1024:
            return jsonify({"error": f"Файл больше {MAX_FILE_MB} МБ"}), 400
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_MB * 1024 * 1024:
            return jsonify({"error": f"Файл больше {MAX_FILE_MB} МБ"}), 400
        safe = secure_filename(f.filename) or "file"
        file_path = os.path.join(UPLOAD_DIR, datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + safe)
        f.save(file_path)
        file_name = os.path.basename(file_path)

    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    con = db()
    cur = con.execute(
        "INSERT INTO leads (created_at, name, phone, email, task, comment, file_name) VALUES (?,?,?,?,?,?,?)",
        (created, name, phone, email, task, comment, file_name),
    )
    con.commit()
    lead_id = cur.lastrowid
    con.close()

    text = (
        f"<b>Новая заявка #{lead_id}</b>\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Телефон:</b> {phone}\n"
    )
    if email:
        text += f"<b>E-mail:</b> {email}\n"
    text += f"<b>Задача:</b> {task or '-'}\n"
    if comment:
        text += f"<b>Комментарий:</b> {comment}\n"
    text += f"<b>Дата:</b> {created} UTC"

    if file_name:
        tg_send_text(text + "\n📎 Файл прикреплён к заявке.")
        tg_send_file(os.path.join(UPLOAD_DIR, file_name), f"Заявка #{lead_id} — {name}, {phone}")
    else:
        tg_send_text(text)

    return jsonify({"ok": True, "id": lead_id})


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.get("/api/admin")
def admin():
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        return "Unauthorized", 401
    con = db()
    rows = con.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 200").fetchall()
    con.close()
    return render_template_string("""
    <!doctype html><html><meta charset="utf-8"><title>Заявки Синтегра 3D</title>
    <style>body{font-family:sans-serif;margin:24px;background:#f5f6f8}table{border-collapse:collapse;width:100%;background:#fff}
    th,td{border:1px solid #ddd;padding:8px 10px;text-align:left;font-size:14px}th{background:#284693;color:#fff}
    td:nth-child(8){font-size:12px;word-break:break-all}a{color:#284693}</style>
    <h2>Заявки Синтегра 3D</h2>
    <table><tr><th>#</th><th>Дата</th><th>Имя</th><th>Телефон</th><th>E-mail</th><th>Задача</th><th>Комментарий</th><th>Файл</th></tr>
    {% for r in rows %}
    <tr><td>{{r[0]}}</td><td>{{r[1]}}</td><td>{{r[2]}}</td><td>{{r[3]}}</td><td>{{r[4]}}</td><td>{{r[5]}}</td><td>{{r[6]}}</td>
    <td>{% if r[7] %}<a href="/api/admin/file?token={{request.args.get('token')}}&name={{r[7]}}">{{r[7]}}</a>{% endif %}</td></tr>
    {% endfor %}
    </table>""")


@app.get("/api/admin/file")
def admin_file():
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        return "Unauthorized", 401
    name = os.path.basename(request.args.get("name", ""))
    if not name:
        return "Not found", 404
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.exists(path):
        return "Not found", 404
    return app.send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)