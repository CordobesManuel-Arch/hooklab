import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("HOOKLAB_DB", BASE_DIR / "hooklab.db"))

app = FastAPI(title="HookLab", docs_url="/docs", redoc_url=None)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                query_string TEXT NOT NULL,
                headers TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


init_db()


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.api_route(
    "/hooks/{hook_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def capture(hook_path: str, request: Request):
    body = (await request.body()).decode("utf-8", errors="replace")
    headers = json.dumps(dict(request.headers), ensure_ascii=False)
    created_at = datetime.now(timezone.utc).isoformat()

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO requests(method, path, query_string, headers, body, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request.method,
                "/hooks/" + hook_path,
                request.url.query,
                headers,
                body,
                created_at,
            ),
        )
        request_id = cursor.lastrowid

    return {"ok": True, "id": request_id}


@app.get("/api/requests")
def list_requests(limit: int = 50):
    limit = max(1, min(limit, 200))
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, method, path, query_string, created_at
            FROM requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/requests/{request_id}")
def request_detail(request_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM requests WHERE id = ?", (request_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="request no encontrado")

    item = dict(row)
    item["headers"] = json.loads(item["headers"])
    return item


@app.delete("/api/requests")
def clear_requests():
    with connect() as conn:
        conn.execute("DELETE FROM requests")
    return {"ok": True}
