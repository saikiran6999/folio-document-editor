"""Small SQLite persistence layer; deliberately dependency-free beyond stdlib."""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(path: Path):
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL,
                content_html TEXT NOT NULL DEFAULT '',
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS document_shares (
                document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL,
                PRIMARY KEY(document_id, user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_id);
            CREATE INDEX IF NOT EXISTS idx_shares_user ON document_shares(user_id);
            CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        if conn.execute("SELECT 1 FROM app_meta WHERE key='seeded'").fetchone():
            return
        conn.executemany(
            "INSERT OR IGNORE INTO users(id, name, email) VALUES (?, ?, ?)",
            [
                (1, "Alex Morgan", "alex@folio.demo"),
                (2, "Jordan Lee", "jordan@folio.demo"),
                (3, "Sam Rivera", "sam@folio.demo"),
            ],
        )
        now = utc_now()
        sample = (
            "Welcome to Folio",
            "<h1>Welcome to Folio ✨</h1>"
            "<p>A calmer place to <strong>write, edit, and share</strong> ideas with your team.</p>"
            "<h2>Try these things</h2>"
            "<ul><li>Edit this document and watch it autosave.</li>"
            "<li>Use the toolbar to format text.</li>"
            "<li>Switch to Jordan to see this document under <em>Shared with me</em>.</li>"
            "<li>Switch to Sam to verify access is restricted.</li></ul>"
            "<p>This is a <u>demo workspace</u>, not a production identity system.</p>",
        )
        cursor = conn.execute(
            "INSERT INTO documents(owner_id,title,content_html,created_at,updated_at) VALUES(1,?,?,?,?)",
            (*sample, now, now),
        )
        conn.execute(
            "INSERT INTO document_shares(document_id,user_id,created_at) VALUES(?,?,?)",
            (cursor.lastrowid, 2, now),
        )
        conn.execute("INSERT INTO app_meta(key,value) VALUES('seeded','1')")