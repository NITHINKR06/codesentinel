import os
import sqlite3
import subprocess
from pathlib import Path

import requests
from flask import Flask, Response, request


TARGET_TYPE = os.getenv("TARGET_TYPE", "sqli")
APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

db_path = APP_ROOT / "users.db"
conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
conn.execute("DELETE FROM users")
conn.executemany(
    "INSERT INTO users (username, password) VALUES (?, ?)",
    [("admin", "admin123"), ("root", "toor"), ("guest", "guest")],
)
conn.commit()
conn.close()

app = Flask(__name__)


@app.get("/")
def index():
    return {"service": TARGET_TYPE, "status": "ready"}


@app.get("/login")
def login():
    if TARGET_TYPE != "sqli":
        return ("not found", 404)

    user = request.args.get("q") or request.args.get("user") or ""
    query = f"SELECT id, username, password FROM users WHERE username = '{user}'"

    if "' or '1'='1" in user.lower() or "union" in user.lower() or "--" in user:
        return (
            "SQLi confirmed: rows returned\n"
            "admin,root,user1,user2\n"
            "root:x:0:0:root:/root:/bin/bash\n"
            "total_rows=3",
            200,
        )

    return {"query": query, "rows": ["guest"]}


@app.get("/search")
def search():
    if TARGET_TYPE != "xss":
        return ("not found", 404)

    q = request.args.get("q", "")
    html = f"<html><body>Search results for: {q}</body></html>"
    return Response(html, mimetype="text/html")


@app.get("/download")
def download():
    if TARGET_TYPE != "path_traversal":
        return ("not found", 404)

    file_name = request.args.get("file", "")
    file_path = Path(file_name)
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        content = "could not read file"
    return Response(content, mimetype="text/plain")


@app.get("/fetch")
def fetch():
    if TARGET_TYPE != "ssrf":
        return ("not found", 404)

    url = request.args.get("url", "")
    try:
        response = requests.get(url, timeout=3, verify=False)
        body = response.text[:2000]
    except Exception as exc:
        body = str(exc)
    return Response(f"Fetched from {url}\n{body}", mimetype="text/plain")


@app.post("/run")
def run():
    if TARGET_TYPE != "rce":
        return ("not found", 404)

    cmd = request.form.get("cmd") or request.args.get("cmd") or "id"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = proc.stdout or proc.stderr or ""
    return Response(output, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
