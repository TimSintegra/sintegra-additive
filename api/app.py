import html
import io
import os
import sqlite3
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape

from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
MAX_FILE_MB = 25


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
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
    }


def get_leads(filters):
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
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
    headers = ["№", "Дата", "Имя", "Телефон", "E-mail", "Задача", "Комментарий", "Файл"]
    data_rows = [headers]
    for row in rows:
        data_rows.append([row["id"], row["created_at"], row["name"], row["phone"], row["email"], row["task"], row["comment"], row["file_name"]])

    sheet_rows = []
    for row_num, values in enumerate(data_rows, 1):
        style = 1 if row_num == 1 else None
        cells = "".join(xlsx_cell(value, style) for value in values)
        sheet_rows.append(f'<row r="{row_num}">{cells}</row>')
    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<dimension ref="A1:H{max(1, len(data_rows))}"/><sheetViews><sheetView workbookViewId="0"/></sheetViews>
<sheetFormatPr defaultRowHeight="18"/><cols><col min="1" max="1" width="8"/><col min="2" max="2" width="22"/><col min="3" max="5" width="24"/><col min="6" max="7" width="42"/><col min="8" max="8" width="32"/></cols>
<sheetData>{''.join(sheet_rows)}</sheetData><autoFilter ref="A1:H{max(1, len(data_rows))}"/></worksheet>'''

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
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Заявки — Синтегра 3D</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fb;color:#172033;font:14px/1.45 Arial,sans-serif}.wrap{max-width:1440px;margin:0 auto;padding:28px 20px 48px}
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:24px}.brand{font-size:25px;font-weight:700}.brand small{display:block;font-size:13px;color:#667085;font-weight:400;margin-top:3px}
.actions{display:flex;gap:10px;align-items:center}.btn{border:0;border-radius:8px;padding:10px 15px;background:#1264e8;color:#fff;cursor:pointer;text-decoration:none;font-weight:600}.btn.secondary{background:#fff;color:#1264e8;border:1px solid #cbd5e1}.btn.danger{background:#fff;color:#bd2c2c;border:1px solid #efb7b7}
.stats{display:grid;grid-template-columns:repeat(3,minmax(160px,1fr));gap:14px;margin-bottom:18px}.stat,.panel{background:#fff;border:1px solid #e2e8f0;border-radius:12px;box-shadow:0 4px 16px #17325d0b}.stat{padding:18px}.stat b{display:block;font-size:26px}.stat span{color:#667085}.panel{padding:16px;overflow:hidden}.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:end;margin-bottom:16px}.field{display:flex;flex-direction:column;gap:5px}.field label{font-size:12px;color:#667085}.field input{height:39px;border:1px solid #cbd5e1;border-radius:7px;padding:0 10px;min-width:180px}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:1000px}th,td{padding:11px 10px;border-bottom:1px solid #e7edf4;text-align:left;vertical-align:top}th{background:#f7f9fc;font-size:12px;color:#667085;white-space:nowrap}td{max-width:260px;word-break:break-word}.muted{color:#98a2b3}.file{white-space:nowrap}.login{max-width:420px;margin:12vh auto}.login h1{margin-top:0}.login input{width:100%;height:44px;margin:8px 0 16px;border:1px solid #cbd5e1;border-radius:7px;padding:0 12px;font-size:16px}.error{background:#fff1f1;color:#a42323;border-radius:7px;padding:10px;margin-bottom:15px}.hint{color:#667085;font-size:13px}.empty{text-align:center;color:#667085;padding:42px}
@media(max-width:700px){.top{align-items:flex-start;flex-direction:column}.actions{width:100%;flex-wrap:wrap}.stats{grid-template-columns:1fr}.wrap{padding:20px 12px}.btn{flex:1;text-align:center}}
</style></head><body><main class="wrap">
{% if login %}<section class="panel login"><h1>Вход в админ-панель</h1><p class="hint">Синтегра 3D · заявки с сайта</p>{% if error %}<div class="error">{{ error }}</div>{% endif %}<form method="post"><label for="password">Пароль администратора</label><input id="password" name="password" type="password" required autofocus><button class="btn" type="submit">Войти</button></form></section>
{% else %}<header class="top"><div class="brand">Заявки Синтегра 3D<small>Административная панель</small></div><div class="actions"><a class="btn" href="{{ export_url }}">Скачать Excel</a><form method="post" action="{{ url_for('admin_logout') }}"><button class="btn danger" type="submit">Выйти</button></form></div></header>
<section class="stats"><div class="stat"><b>{{ total_count }}</b><span>Всего заявок</span></div><div class="stat"><b>{{ filtered_count }}</b><span>В текущем фильтре</span></div><div class="stat"><b>{{ with_files }}</b><span>С файлами</span></div></section>
<section class="panel"><form class="filters" method="get"><div class="field"><label>Поиск</label><input name="q" value="{{ filters.q }}" placeholder="Имя, телефон, задача..."></div><div class="field"><label>Дата от</label><input name="date_from" type="date" value="{{ filters.date_from }}"></div><div class="field"><label>Дата до</label><input name="date_to" type="date" value="{{ filters.date_to }}"></div><button class="btn" type="submit">Применить</button><a class="btn secondary" href="{{ url_for('admin') }}">Сбросить</a></form>
<div class="table-wrap">{% if rows %}<table><thead><tr><th>№</th><th>Дата</th><th>Имя</th><th>Телефон</th><th>E-mail</th><th>Задача</th><th>Комментарий</th><th>Файл</th></tr></thead><tbody>{% for row in rows %}<tr><td>{{ row.id }}</td><td>{{ row.created_at }}</td><td>{{ row.name }}</td><td>{{ row.phone }}</td><td>{{ row.email or '—' }}</td><td>{{ row.task }}</td><td>{{ row.comment or '—' }}</td><td class="file">{% if row.file_name %}<a href="{{ url_for('admin_file', name=row.file_name) }}">Скачать</a>{% else %}<span class="muted">—</span>{% endif %}</td></tr>{% endfor %}</tbody></table>{% else %}<div class="empty">Заявок по выбранным условиям нет.</div>{% endif %}</div></section>{% endif %}</main></body></html>'''


@app.post("/api/lead")
def lead():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    task = (request.form.get("task") or "").strip()
    comment = (request.form.get("comment") or "").strip()
    if len(name) < 2:
        return jsonify({"error": "Введите корректное имя"}), 400
    if len("".join(c for c in phone if c.isdigit())) < 6:
        return jsonify({"error": "Введите корректный телефон"}), 400
    if email and "@" not in email:
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
        file_path = os.path.join(UPLOAD_DIR, datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + safe)
        f.save(file_path)
        file_name = os.path.basename(file_path)

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
        if request.form.get("password", "") != ADMIN_PASSWORD:
            return render_template_string(ADMIN_TEMPLATE, login=True, error="Неверный пароль"), 401
        session["admin_authenticated"] = True
        return redirect(url_for("admin"))
    if not admin_required():
        return render_template_string(ADMIN_TEMPLATE, login=True, error=None)

    filters = get_filters()
    rows = get_leads(filters)
    all_rows = get_leads({"q": "", "date_from": "", "date_to": ""})
    query = urllib.parse.urlencode({key: value for key, value in filters.items() if value})
    return render_template_string(ADMIN_TEMPLATE, login=False, filters=filters, rows=rows, total_count=len(all_rows), filtered_count=len(rows), with_files=sum(1 for row in all_rows if row["file_name"]), export_url=url_for("admin_export") + ("?" + query if query else ""))


@app.post("/api/admin/logout")
def admin_logout():
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
