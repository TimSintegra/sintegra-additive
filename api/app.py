import html
import io
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename


app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set to a long random value")
app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
MAX_FILE_MB = 25
MAX_REQUEST_BYTES = MAX_FILE_MB * 1024 * 1024 + 1024 * 1024
MAX_FIELD_LENGTHS = {"name": 120, "phone": 40, "email": 254, "task": 500, "comment": 5000}
ALLOWED_FILE_EXTENSIONS = {".stl", ".obj", ".3mf", ".step", ".stp", ".pdf", ".dxf", ".dwg", ".jpg", ".jpeg", ".png", ".zip"}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_REQUESTS = 10
rate_limit_lock = threading.Lock()
rate_limit_state = {}
STATUS_LABELS = {
    "new": "Новая",
    "in_work": "В работе",
    "completed": "Выполнена",
    "cancelled": "Отменена",
}
ARCHIVE_LABEL = "В архиве"


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def check_csrf():
    supplied = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    return bool(expected and supplied and secrets.compare_digest(supplied, expected))


def rate_limited():
    now = time.monotonic()
    # API is reachable through our nginx proxy, which overwrites X-Real-IP.
    client = request.headers.get("X-Real-IP") or request.remote_addr or "unknown"
    with rate_limit_lock:
        recent = [stamp for stamp in rate_limit_state.get(client, []) if now - stamp < RATE_LIMIT_WINDOW]
        if len(recent) >= RATE_LIMIT_REQUESTS:
            rate_limit_state[client] = recent
            return True
        recent.append(now)
        rate_limit_state[client] = recent
    return False


app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES


@app.errorhandler(413)
def request_too_large(error):
    if request.path == "/api/lead":
        return jsonify({"error": f"Запрос или файл больше {MAX_FILE_MB} МБ"}), 413
    return "Запрос слишком большой", 413


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        name TEXT, phone TEXT, email TEXT, task TEXT, comment TEXT, file_name TEXT,
        status TEXT NOT NULL DEFAULT 'new',
        archived INTEGER NOT NULL DEFAULT 0
    )""")
    columns = {row[1] for row in con.execute("PRAGMA table_info(leads)").fetchall()}
    if "status" not in columns:
        con.execute("ALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
    if "archived" not in columns:
        con.execute("ALTER TABLE leads ADD COLUMN archived INTEGER NOT NULL DEFAULT 0")
    if "status" not in columns or "archived" not in columns:
        con.commit()
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
        return ("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + name + "\"\r\n\r\n" + value + "\r\n").encode()

    for name, value in (("chat_id", TELEGRAM_CHAT_ID), ("caption", caption)):
        body += part(name, value)
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


def get_filters():
    return {
        "q": request.args.get("q", "").strip(),
        "date_from": request.args.get("date_from", "").strip(),
        "date_to": request.args.get("date_to", "").strip(),
        "status": request.args.get("status", "").strip(),
        "show_archived": request.args.get("show_archived", "") == "1",
    }


def get_leads(filters):
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if not filters.get("show_archived"):
        query += " AND archived = 0"
    if filters["q"]:
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ? OR task LIKE ? OR comment LIKE ?)"
        value = f"%{filters['q']}%"
        params.extend([value] * 5)
    if filters["date_from"]:
        query += " AND date(created_at) >= date(?)"
        params.append(filters["date_from"])
    if filters["date_to"]:
        query += " AND date(created_at) <= date(?)"
        params.append(filters["date_to"])
    if filters["status"] in STATUS_LABELS:
        query += " AND status = ?"
        params.append(filters["status"])
    query += " ORDER BY id DESC"
    con = db()
    rows = con.execute(query, params).fetchall()
    con.close()
    return rows


def xlsx_cell(value, style=None):
    attrs = f' s="{style}"' if style is not None else ""
    if value is None:
        return f"<c{attrs}/>"
    text = xml_escape(str(value)).replace("\n", "&#10;")
    return f'<c t="inlineStr"{attrs}><is><t xml:space="preserve">{text}</t></is></c>'


def build_xlsx(rows):
    headers = ["№", "Дата", "Статус", "Имя", "Телефон", "E-mail", "Задача", "Комментарий", "Файл"]
    data_rows = [headers]
    for row in rows:
        data_rows.append([row["id"], row["created_at"], STATUS_LABELS.get(row["status"], "Новая"), row["name"], row["phone"], row["email"], row["task"], row["comment"], row["file_name"]])

    sheet_rows = []
    for row_num, values in enumerate(data_rows, 1):
        style = 1 if row_num == 1 else None
        cells = "".join(xlsx_cell(value, style) for value in values)
        sheet_rows.append(f'<row r="{row_num}">{cells}</row>')
    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<dimension ref="A1:I{max(1, len(data_rows))}"/><sheetViews><sheetView workbookViewId="0"/></sheetViews>
<sheetFormatPr defaultRowHeight="18"/><cols><col min="1" max="1" width="8"/><col min="2" max="2" width="22"/><col min="3" max="3" width="18"/><col min="4" max="6" width="24"/><col min="7" max="8" width="42"/><col min="9" max="9" width="32"/></cols>
<sheetData>{''.join(sheet_rows)}</sheetData><autoFilter ref="A1:I{max(1, len(data_rows))}"/></worksheet>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
    workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Заявки" sheetId="1" r:id="rId1"/></sheets></workbook>'''
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0"/></cellXfs></styleSheet>'''

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        archive.writestr("xl/styles.xml", styles)
    output.seek(0)
    return output


def admin_required():
    return bool(session.get("admin_authenticated"))


ADMIN_TEMPLATE = '''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Заявки — Синтегра 3D</title>
<style>
:root{--bg:#f3f6fb;--text:#172033;--muted:#667085;--line:#e2e8f0;--blue:#1264e8;--red:#b42318}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 Arial,sans-serif}
button,input,select{font:inherit}
button,a,input,select{-webkit-tap-highlight-color:transparent}
form{margin:0}
a{color:var(--blue)}
:focus-visible{outline:3px solid #91b9fb;outline-offset:3px}
.wrap{max-width:1600px;margin:0 auto;padding:28px 24px 48px}
.top{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:24px}
h1{font-size:26px;line-height:1.25;margin:0;font-weight:700}
.brand small{display:block;font-size:13px;color:var(--muted);margin-top:6px}
.actions{display:flex;gap:10px;align-items:center}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:40px;padding:0 16px;border:1px solid transparent;border-radius:7px;background:var(--blue);color:#fff;cursor:pointer;text-decoration:none;font-size:14px;font-weight:600;line-height:1;white-space:nowrap}
.btn:hover{background:#0e54c6}
.btn.secondary{background:#fff;color:var(--blue);border-color:#cbd5e1}
.btn.secondary:hover{background:#f0f5ff;border-color:#91b9fb}
.btn.danger{background:#fff;color:var(--red);border-color:#efb7b7}
.btn.danger:hover{background:#fff1f1}
.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-bottom:20px}
.stat,.panel{background:#fff;border:1px solid var(--line);border-radius:12px}
.stat{padding:16px 20px;display:flex;align-items:center;gap:14px}
.stat b{font-size:28px;line-height:1.2}
.stat span{color:var(--muted);font-size:13px}
.filters{padding:20px;display:grid;grid-template-columns:minmax(0,2fr) repeat(3,minmax(0,1fr));gap:14px 16px}
.field{display:flex;flex-direction:column;gap:6px;min-width:0}
.field label{font-size:12px;font-weight:600;color:var(--muted)}
.field input,.field select,.status-form select{width:100%;min-width:0;height:40px;border:1px solid #cbd5e1;border-radius:7px;padding:0 10px;background:#fff;color:var(--text)}
.filter-footer{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:16px}
.archive-check{display:flex;align-items:center;gap:8px;color:var(--muted);cursor:pointer;font-size:13px}
.archive-check input{width:16px;height:16px;margin:0;accent-color:var(--blue);flex-shrink:0}
.filter-actions{display:grid;grid-template-columns:repeat(2,120px);gap:10px}
.list-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 20px;border-top:1px solid var(--line)}
.list-heading h2{margin:0;font-size:16px}
.list-heading span{font-size:13px;color:var(--muted)}
table{width:100%;border-collapse:collapse;table-layout:fixed}
.col-lead{width:132px}.col-contact{width:27%}.col-management{width:242px}
th,td{text-align:left;vertical-align:top;padding:18px 20px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}
th{background:#f7f9fc;color:var(--muted);font-size:12px;font-weight:600;padding-top:12px;padding-bottom:12px}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fafcff}
.lead-id{display:block;font-size:15px;margin-bottom:6px}
.lead-date{display:block;font-size:12px;color:var(--muted)}
.lead-date span{display:block}
.contact-name,.task-title{font-weight:600;margin-bottom:6px}
.contact-links{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.contact-links a{text-decoration:none;color:var(--text);max-width:100%}
.contact-links a:hover{color:var(--blue);text-decoration:underline}
.comment{margin-top:12px;color:#475467;white-space:pre-wrap}
.comment-label{display:block;color:var(--muted);font-size:11px;margin-bottom:3px}
.task-title{white-space:pre-wrap}
.attachment{display:inline-flex;align-items:center;gap:6px;margin-top:12px;text-decoration:none;font-size:13px;font-weight:600}
.attachment:hover{text-decoration:underline}
.status-stack{display:grid;gap:8px}
.status-form{min-width:0}
.row-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.row-actions .btn{width:100%;padding:0 8px;font-size:12px}
.archive-badge{justify-self:start;display:inline-block;background:#eef1f5;color:var(--muted);font-size:11px;border-radius:4px;padding:3px 7px}
.muted{color:var(--muted)}
.login{max-width:420px;margin:12vh auto;padding:24px}
.login h1{font-size:23px;margin-bottom:12px}
.login input{width:100%;height:44px;margin:8px 0 16px;border:1px solid #cbd5e1;border-radius:7px;padding:0 12px;font-size:16px}
.login .btn{width:100%}
.error{background:#fff1f1;color:#a42323;border-radius:7px;padding:10px;margin-bottom:15px}
.hint{color:var(--muted);font-size:13px}
.empty{text-align:center;color:var(--muted);padding:42px 20px}
@media(max-width:1100px){.wrap{padding:24px 16px}.col-lead{width:112px}.col-contact{width:26%}.col-management{width:218px}th,td{padding-left:14px;padding-right:14px}}
@media(max-width:900px){
.filters{grid-template-columns:repeat(2,minmax(0,1fr))}
.table-wrap{padding:0 20px 20px}
table,tbody{display:block}colgroup,thead{display:none}
tbody{display:grid;gap:14px}
tbody tr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);border:1px solid var(--line);border-radius:9px;padding:16px;gap:16px}
th,td{display:block;min-width:0;padding:0;border:0}
.lead-meta{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid var(--line)}
.lead-id{margin:0}.lead-date span{display:inline;margin-left:6px}
.management-cell{grid-column:1/-1;padding-top:14px;border-top:1px solid var(--line)}
.status-stack{grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:center;gap:10px 16px}
.archive-badge{grid-column:1/-1;grid-row:1}
}
@media(max-width:600px){
.wrap{padding:20px 12px 32px}.top{align-items:flex-start;flex-direction:column;gap:16px;margin-bottom:20px}h1{font-size:23px}
.actions{width:100%;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.actions .btn{width:100%}
.stats{gap:8px}.stat{padding:12px 8px;flex-direction:column;align-items:flex-start;gap:6px}.stat b{font-size:24px}.stat span{font-size:11px;line-height:1.4}
.filters{padding:16px;gap:12px}.field-search{grid-column:1/-1}.field-status{grid-column:1/-1}.field input,.field select,.status-form select{font-size:16px}
.filter-footer{align-items:stretch;flex-direction:column;gap:14px}.filter-actions{grid-template-columns:repeat(2,minmax(0,1fr))}
.list-heading{padding:16px}.table-wrap{padding:0 12px 12px}tbody tr{padding:14px;grid-template-columns:minmax(0,1fr);gap:16px}
.lead-meta,.management-cell{grid-column:1}.status-stack{grid-template-columns:minmax(0,1fr)}.row-actions .btn{font-size:13px}.login{margin:8vh auto}
}
</style>
</head>
<body>
<main class="wrap">
{% if login %}
<section class="panel login">
<h1>Вход в админ-панель</h1><p class="hint">Синтегра 3D · заявки с сайта</p>
{% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
<form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><label for="password">Пароль администратора</label><input id="password" name="password" type="password" required autofocus><button class="btn" type="submit">Войти</button></form>
</section>
{% else %}
{% macro filter_fields(archive_value) %}
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<input type="hidden" name="q" value="{{ filters.q }}">
<input type="hidden" name="date_from" value="{{ filters.date_from }}">
<input type="hidden" name="date_to" value="{{ filters.date_to }}">
<input type="hidden" name="filter_status" value="{{ filters.status }}">
<input type="hidden" name="show_archived" value="{{ archive_value }}">
{% endmacro %}
<header class="top">
<div class="brand"><h1>Заявки Синтегра 3D</h1><small>Административная панель</small></div>
<div class="actions"><a class="btn" href="{{ export_url }}">Скачать Excel</a><form method="post" action="{{ url_for('admin_logout') }}"><input type="hidden" name="csrf_token" value="{{ csrf_token }}"><button class="btn danger" type="submit">Выйти</button></form></div>
</header>
<section class="stats" aria-label="Статистика заявок">
<div class="stat"><b>{{ total_count }}</b><span>Всего заявок</span></div>
<div class="stat"><b>{{ filtered_count }}</b><span>В текущем фильтре</span></div>
<div class="stat"><b>{{ with_files }}</b><span>С файлами</span></div>
</section>
<section class="panel" aria-label="Список заявок">
<form class="filters" method="get">
<div class="field field-search"><label for="search">Поиск</label><input id="search" name="q" value="{{ filters.q }}" placeholder="Имя, телефон, e-mail, задача…"></div>
<div class="field"><label for="date-from">Дата от</label><input id="date-from" name="date_from" type="date" value="{{ filters.date_from }}"></div>
<div class="field"><label for="date-to">Дата до</label><input id="date-to" name="date_to" type="date" value="{{ filters.date_to }}"></div>
<div class="field field-status"><label for="filter-status">Статус</label><select id="filter-status" name="status"><option value="">Все статусы</option>{% for value, label in status_labels.items() %}<option value="{{ value }}"{% if filters.status == value %} selected{% endif %}>{{ label }}</option>{% endfor %}</select></div>
<div class="filter-footer">
<label class="archive-check"><input name="show_archived" type="checkbox" value="1"{% if filters.show_archived %} checked{% endif %}>Показать архив</label>
<div class="filter-actions"><button class="btn" type="submit">Применить</button><a class="btn secondary" href="{{ url_for('admin') }}">Сбросить</a></div>
</div>
</form>
<div class="list-heading"><h2>Список заявок</h2><span>Найдено: {{ filtered_count }}</span></div>
<div class="table-wrap">
{% if rows %}
<table aria-label="Заявки с сайта">
<colgroup><col class="col-lead"><col class="col-contact"><col><col class="col-management"></colgroup>
<thead><tr><th scope="col">Заявка / дата</th><th scope="col">Клиент и контакты</th><th scope="col">Задача и комментарий</th><th scope="col">Статус и действия</th></tr></thead>
<tbody>
{% for row in rows %}
<tr>
<td class="lead-meta"><strong class="lead-id">№ {{ row.id }}</strong><time class="lead-date" datetime="{{ row.created_at|replace(' ', 'T') }}Z">{{ row.created_at[:10] }}<span>{{ row.created_at[11:] }} UTC</span></time></td>
<td><div class="contact-name">{{ row.name or '—' }}</div><div class="contact-links">{% if row.phone %}<a href="tel:{{ row.phone }}">{{ row.phone }}</a>{% else %}<span class="muted">Телефон не указан</span>{% endif %}{% if row.email %}<a href="mailto:{{ row.email }}">{{ row.email }}</a>{% endif %}</div></td>
<td><div class="task-title">{{ row.task or 'Задача не указана' }}</div>{% if row.comment %}<div class="comment"><span class="comment-label">Комментарий</span>{{ row.comment }}</div>{% endif %}{% if row.file_name %}<a class="attachment" href="{{ url_for('admin_file', name=row.file_name) }}">Скачать файл</a>{% endif %}</td>
<td class="management-cell">
<div class="status-stack">
{% if row.archived %}<span class="archive-badge">{{ archive_label }}</span>{% endif %}
<form id="status-{{ row.id }}" class="status-form" method="post" action="{{ url_for('admin_status_update', lead_id=row.id) }}">
{{ filter_fields('1' if filters.show_archived else '') }}
<select name="status" aria-label="Статус заявки №{{ row.id }}">{% for value, label in status_labels.items() %}<option value="{{ value }}"{% if row.status == value %} selected{% endif %}>{{ label }}</option>{% endfor %}</select>
</form>
<div class="row-actions">
<button class="btn" type="submit" form="status-{{ row.id }}" aria-label="Сохранить статус заявки №{{ row.id }}">Сохранить</button>
<form class="archive-form" method="post" action="{{ url_for('admin_archive', lead_id=row.id) }}" onsubmit="return confirm('{{ 'Вернуть заявку в активные?' if row.archived else 'Переместить заявку в архив? Данные не будут удалены.' }}');">
{{ filter_fields('1') }}
<button class="btn {{ 'secondary' if row.archived else 'danger' }}" type="submit" aria-label="{{ 'Вернуть из архива' if row.archived else 'В архив' }} заявку №{{ row.id }}">{{ 'Вернуть' if row.archived else 'В архив' }}</button>
</form>
</div>
</div>
</td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}<div class="empty">Заявок по выбранным условиям нет.</div>{% endif %}
</div>
</section>
{% endif %}
</main>
</body>
</html>
'''


@app.post("/api/lead")
def lead():
    if rate_limited():
        return jsonify({"error": "Слишком много запросов. Попробуйте через минуту."}), 429
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    task = (request.form.get("task") or "").strip()
    comment = (request.form.get("comment") or "").strip()
    for field, value in (("name", name), ("phone", phone), ("email", email), ("task", task), ("comment", comment)):
        if len(value) > MAX_FIELD_LENGTHS[field]:
            return jsonify({"error": "Слишком длинное значение в поле формы"}), 400
    if request.form.get("consent") not in {"1", "on", "true"}:
        return jsonify({"error": "Необходимо согласие на обработку персональных данных"}), 400
    if len(name) < 2:
        return jsonify({"error": "Введите корректное имя"}), 400
    if not task:
        return jsonify({"error": "Опишите, что необходимо изготовить"}), 400
    if len("".join(c for c in phone if c.isdigit())) < 6:
        return jsonify({"error": "Введите корректный телефон"}), 400
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "Введите корректный e-mail"}), 400

    file_name = None
    f = request.files.get("file")
    if f and f.filename:
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_MB * 1024 * 1024:
            return jsonify({"error": f"Файл больше {MAX_FILE_MB} МБ"}), 400
        safe = secure_filename(f.filename) or "file"
        extension = os.path.splitext(safe)[1].lower()
        if extension not in ALLOWED_FILE_EXTENSIONS:
            return jsonify({"error": "Недопустимый тип файла"}), 400
        stored_name = secrets.token_hex(16) + extension
        file_path = os.path.join(UPLOAD_DIR, stored_name)
        f.save(file_path)
        file_name = stored_name

    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    con = db()
    cur = con.execute("INSERT INTO leads (created_at, name, phone, email, task, comment, file_name) VALUES (?,?,?,?,?,?,?)", (created, name, phone, email, task, comment, file_name))
    con.commit()
    lead_id = cur.lastrowid
    con.close()

    text = f"<b>Новая заявка #{lead_id}</b>\n<b>Имя:</b> {html.escape(name)}\n<b>Телефон:</b> {html.escape(phone)}\n"
    if email:
        text += f"<b>E-mail:</b> {html.escape(email)}\n"
    text += f"<b>Задача:</b> {html.escape(task or '-')}\n"
    if comment:
        text += f"<b>Комментарий:</b> {html.escape(comment)}\n"
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


@app.route("/api/admin", methods=["GET", "POST"])
def admin():
    if not ADMIN_PASSWORD:
        return "Админ-панель не настроена: задайте ADMIN_PASSWORD на сервере.", 503
    if request.method == "POST":
        if not check_csrf():
            return "Недействительный CSRF-токен", 400
        if request.form.get("password", "") != ADMIN_PASSWORD:
            return render_template_string(ADMIN_TEMPLATE, login=True, error="Неверный пароль", csrf_token=csrf_token()), 401
        session["admin_authenticated"] = True
        return redirect(url_for("admin"))
    if not admin_required():
        return render_template_string(ADMIN_TEMPLATE, login=True, error=None, csrf_token=csrf_token())

    filters = get_filters()
    rows = get_leads(filters)
    all_rows = get_leads({"q": "", "date_from": "", "date_to": "", "status": "", "show_archived": filters["show_archived"]})
    query_filters = dict(filters)
    query_filters["show_archived"] = "1" if filters["show_archived"] else ""
    query = urllib.parse.urlencode({key: value for key, value in query_filters.items() if value})
    return render_template_string(ADMIN_TEMPLATE, login=False, filters=filters, rows=rows, status_labels=STATUS_LABELS, archive_label=ARCHIVE_LABEL, total_count=len(all_rows), filtered_count=len(rows), with_files=sum(1 for row in all_rows if row["file_name"]), export_url=url_for("admin_export") + ("?" + query if query else ""), csrf_token=csrf_token())


@app.post("/api/admin/status/<int:lead_id>")
def admin_status_update(lead_id):
    if not admin_required():
        return redirect(url_for("admin"))
    if not check_csrf():
        return "Недействительный CSRF-токен", 400
    status = request.form.get("status", "")
    if status not in STATUS_LABELS:
        return "Недопустимый статус", 400
    con = db()
    con.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    con.commit()
    con.close()
    params = {"q": request.form.get("q", ""), "date_from": request.form.get("date_from", ""), "date_to": request.form.get("date_to", ""), "status": request.form.get("filter_status", ""), "show_archived": request.form.get("show_archived", "")}
    return redirect(url_for("admin", **{key: value for key, value in params.items() if value}))


@app.post("/api/admin/archive/<int:lead_id>")
def admin_archive(lead_id):
    if not admin_required():
        return redirect(url_for("admin"))
    if not check_csrf():
        return "Недействительный CSRF-токен", 400
    con = db()
    current = con.execute("SELECT archived FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if current is None:
        con.close()
        return "Заявка не найдена", 404
    con.execute("UPDATE leads SET archived = ? WHERE id = ?", (0 if current["archived"] else 1, lead_id))
    con.commit()
    con.close()
    params = {"q": request.form.get("q", ""), "date_from": request.form.get("date_from", ""), "date_to": request.form.get("date_to", ""), "status": request.form.get("filter_status", ""), "show_archived": request.form.get("show_archived", "")}
    return redirect(url_for("admin", **{key: value for key, value in params.items() if value}))


@app.post("/api/admin/logout")
def admin_logout():
    if not check_csrf():
        return "Недействительный CSRF-токен", 400
    session.clear()
    return redirect(url_for("admin"))


@app.get("/api/admin/export.xlsx")
def admin_export():
    if not admin_required():
        return redirect(url_for("admin"))
    rows = get_leads(get_filters())
    return send_file(build_xlsx(rows), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"sintegra-zayavki-{datetime.now().strftime('%Y-%m-%d')}.xlsx")


@app.get("/api/admin/file/<path:name>")
def admin_file(name):
    if not admin_required():
        return redirect(url_for("admin"))
    safe_name = os.path.basename(name)
    path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.isfile(path):
        return "Файл не найден", 404
    return send_file(path, as_attachment=True, download_name=safe_name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
