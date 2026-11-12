"""Folio: a focused collaborative document editor demo."""

from io import BytesIO
from pathlib import Path
import html
import os
import re

import bleach
from docx import Document as WordDocument
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import mistune
from pydantic import BaseModel, Field

from app.storage import connect, initialize, utc_now

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_HTML_CHARS = 500_000
ALLOWED_TAGS = [
    "p", "br", "div", "h1", "h2", "h3", "ul", "ol", "li",
    "strong", "b", "em", "i", "u", "s", "blockquote", "span",
]


def sanitize_html(value: str) -> str:
    """Remove scripts, event handlers, styles, links, and other unsafe markup."""
    return bleach.clean(value, tags=ALLOWED_TAGS, attributes={}, strip=True)


def validate_title(value: str) -> str:
    title = value.strip()
    if not title or len(title) > 120:
        raise HTTPException(status_code=422, detail="Title must be 1–120 characters.")
    return title


def validate_content(value: str) -> str:
    if len(value) > MAX_HTML_CHARS:
        raise HTTPException(status_code=413, detail="Document content is too large.")
    return sanitize_html(value)


def text_to_html(value: str) -> str:
    paragraphs = re.split(r"\n\s*\n", value.replace("\r\n", "\n"))
    return "".join(
        f"<p>{html.escape(paragraph).replace(chr(10), '<br>')}</p>"
        for paragraph in paragraphs if paragraph.strip()
    )


def docx_to_html(raw: bytes) -> str:
    """Import basic DOCX paragraphs, headings, lists, and inline emphasis."""
    try:
        document = WordDocument(BytesIO(raw))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="This DOCX file could not be read.") from exc
    parts = []
    active_list = None
    for paragraph in document.paragraphs:
        style = paragraph.style.name.lower() if paragraph.style else ""
        if style.startswith("list bullet"):
            tag = "ul"
        elif style.startswith("list number"):
            tag = "ol"
        else:
            tag = None
        if active_list and tag != active_list:
            parts.append(f"</{active_list}>")
            active_list = None
        if tag and not active_list:
            parts.append(f"<{tag}>")
            active_list = tag
        text = ""
        for run in paragraph.runs:
            chunk = html.escape(run.text).replace("\n", "<br>")
            if run.underline:
                chunk = f"<u>{chunk}</u>"
            if run.italic:
                chunk = f"<em>{chunk}</em>"
            if run.bold:
                chunk = f"<strong>{chunk}</strong>"
            text += chunk
        if tag:
            parts.append(f"<li>{text or '<br>'}</li>")
        else:
            heading = re.match(r"heading\s+([1-3])", style)
            name = f"h{heading.group(1)}" if heading else "p"
            parts.append(f"<{name}>{text or '<br>'}</{name}>")
    if active_list:
        parts.append(f"</{active_list}>")
    return "".join(parts)


class CreateDocument(BaseModel):
    title: str = "Untitled document"


class UpdateDocument(BaseModel):
    expected_version: int = Field(ge=1)
    title: str | None = None
    content_html: str | None = None


class ShareDocument(BaseModel):
    user_id: int


def create_app(database_path: str | Path | None = None) -> FastAPI:
    path = Path(database_path or os.environ.get("FOLIO_DB_PATH", ROOT / "data" / "folio.sqlite3"))
    initialize(path)
    app = FastAPI(title="Folio API", version="1.0.0")
    app.state.database_path = path
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    def current_user(x_user_id: int | None = Header(default=None, alias="X-User-Id")) -> dict:
        if x_user_id is None:
            raise HTTPException(status_code=401, detail="Select a demo user.")
        with connect(path) as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (x_user_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Unknown demo user.")
        return dict(row)

    def authorized_doc(conn, document_id: int, user_id: int) -> dict:
        row = conn.execute(
            """SELECT d.*, u.name AS owner_name,
                CASE WHEN d.owner_id=? THEN 'owner' ELSE 'editor' END AS access
               FROM documents d JOIN users u ON u.id=d.owner_id
               WHERE d.id=? AND (d.owner_id=? OR EXISTS (
                   SELECT 1 FROM document_shares s
                   WHERE s.document_id=d.id AND s.user_id=?))""",
            (user_id, document_id, user_id, user_id),
        ).fetchone()
        if row is None:
            # Do not disclose whether a private document exists.
            raise HTTPException(status_code=404, detail="Document not found.")
        return dict(row)

    def require_owner(conn, document_id: int, user_id: int) -> dict:
        doc = authorized_doc(conn, document_id, user_id)
        if doc["owner_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only the owner can manage sharing or rename.")
        return doc

    def document_detail(conn, doc: dict) -> dict:
        shares = conn.execute(
            """SELECT u.id, u.name, u.email FROM document_shares s
               JOIN users u ON u.id=s.user_id
               WHERE s.document_id=? ORDER BY u.name""",
            (doc["id"],),
        ).fetchall()
        return {**doc, "shared_with": [dict(row) for row in shares]}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "static" / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/users")
    def users():
        with connect(path) as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY id")]

    @app.get("/api/documents")
    def list_documents(user: dict = Depends(current_user)):
        with connect(path) as conn:
            rows = conn.execute(
                """SELECT d.id, d.title, d.owner_id, u.name AS owner_name,
                          d.updated_at, d.created_at, d.version,
                          CASE WHEN d.owner_id=? THEN 'owner' ELSE 'editor' END AS access
                   FROM documents d JOIN users u ON u.id=d.owner_id
                   WHERE d.owner_id=? OR EXISTS (
                       SELECT 1 FROM document_shares s
                       WHERE s.document_id=d.id AND s.user_id=?)
                   ORDER BY d.updated_at DESC, d.id DESC""",
                (user["id"], user["id"], user["id"]),
            ).fetchall()
        return [dict(row) for row in rows]

    @app.post("/api/documents", status_code=201)
    def create_document(body: CreateDocument, user: dict = Depends(current_user)):
        title = validate_title(body.title)
        now = utc_now()
        with connect(path) as conn:
            cursor = conn.execute(
                """INSERT INTO documents(owner_id,title,content_html,created_at,updated_at)
                   VALUES(?,?,?,?,?)""",
                (user["id"], title, "", now, now),
            )
            doc = authorized_doc(conn, cursor.lastrowid, user["id"])
            return document_detail(conn, doc)

    @app.get("/api/documents/{document_id}")
    def get_document(document_id: int, user: dict = Depends(current_user)):
        with connect(path) as conn:
            return document_detail(conn, authorized_doc(conn, document_id, user["id"]))

    @app.patch("/api/documents/{document_id}")
    def update_document(document_id: int, body: UpdateDocument, user: dict = Depends(current_user)):
        if body.title is None and body.content_html is None:
            raise HTTPException(status_code=422, detail="No changes provided.")
        with connect(path) as conn:
            doc = authorized_doc(conn, document_id, user["id"])
            if body.title is not None and doc["owner_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="Only the owner can rename documents.")
            if doc["version"] != body.expected_version:
                raise HTTPException(status_code=409, detail="This document changed in another session. Reload to resolve the conflict.")
            title = validate_title(body.title) if body.title is not None else doc["title"]
            content = validate_content(body.content_html) if body.content_html is not None else doc["content_html"]
            result = conn.execute(
                """UPDATE documents SET title=?, content_html=?, version=version+1, updated_at=?
                   WHERE id=? AND version=?""",
                (title, content, utc_now(), document_id, body.expected_version),
            )
            if result.rowcount != 1:
                raise HTTPException(status_code=409, detail="Concurrent edit detected. Reload to resolve.")
            return document_detail(conn, authorized_doc(conn, document_id, user["id"]))

    @app.post("/api/documents/{document_id}/share", status_code=201)
    def share_document(document_id: int, body: ShareDocument, user: dict = Depends(current_user)):
        with connect(path) as conn:
            require_owner(conn, document_id, user["id"])
            if body.user_id == user["id"]:
                raise HTTPException(status_code=422, detail="You already own this document.")
            if not conn.execute("SELECT 1 FROM users WHERE id=?", (body.user_id,)).fetchone():
                raise HTTPException(status_code=404, detail="User not found.")
            if conn.execute(
                "SELECT 1 FROM document_shares WHERE document_id=? AND user_id=?",
                (document_id, body.user_id),
            ).fetchone():
                raise HTTPException(status_code=409, detail="This user already has access.")
            conn.execute(
                "INSERT INTO document_shares(document_id,user_id,created_at) VALUES(?,?,?)",
                (document_id, body.user_id, utc_now()),
            )
            return document_detail(conn, authorized_doc(conn, document_id, user["id"]))

    @app.delete("/api/documents/{document_id}/share/{target_user_id}", status_code=204)
    def revoke_share(document_id: int, target_user_id: int, user: dict = Depends(current_user)):
        with connect(path) as conn:
            require_owner(conn, document_id, user["id"])
            cursor = conn.execute(
                "DELETE FROM document_shares WHERE document_id=? AND user_id=?",
                (document_id, target_user_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Share not found.")

    @app.post("/api/import", status_code=201)
    async def import_document(file: UploadFile = File(...), user: dict = Depends(current_user)):
        filename = (file.filename or "").strip()
        suffix = Path(filename).suffix.lower()
        if suffix not in {".txt", ".md", ".docx"}:
            raise HTTPException(status_code=415, detail="Supported files: .txt, .md, .docx")
        raw = await file.read(MAX_UPLOAD_BYTES + 1)
        await file.close()
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Maximum upload size is 2 MB.")
        if not raw:
            raise HTTPException(status_code=422, detail="Cannot import an empty file.")
        if suffix == ".docx":
            content = docx_to_html(raw)
        else:
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                raise HTTPException(status_code=422, detail="Text files must be UTF-8 encoded.") from exc
            content = mistune.html(text) if suffix == ".md" else text_to_html(text)
        content = validate_content(content)
        title = validate_title(Path(filename).stem[:120] or "Imported document")
        now = utc_now()
        with connect(path) as conn:
            cursor = conn.execute(
                """INSERT INTO documents(owner_id,title,content_html,created_at,updated_at)
                   VALUES(?,?,?,?,?)""",
                (user["id"], title, content, now, now),
            )
            return document_detail(conn, authorized_doc(conn, cursor.lastrowid, user["id"]))

    return app


app = create_app()