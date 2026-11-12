# Folio — lightweight collaborative document editor

A focused, Google Docs–inspired writing workspace built for Ajaia's AI-Native Full Stack Developer assignment. **Folio** is intentionally a small, working product slice rather than a Google Docs clone.

**Live demo:** https://folio-document-editor.onrender.com  
**API health:** https://folio-document-editor.onrender.com/api/health  
**GitHub:** https://github.com/saikiran6999/folio-document-editor  
**Walkthrough:** https://www.loom.com/share/89410187f7844bd78ad3046578d4bf00

Desktop, sharing, and mobile screenshots are included in the submission ZIP under `screenshots/`.

## What works

- **Create, rename, edit, save, and reopen** rich-text documents.
- **Rich-text toolbar:** bold, italic, underline, headings 1–3, bulleted lists, numbered lists, and clear formatting.
- **Autosave** after a short pause in typing, plus manual Save / Ctrl+S.
- **Import** `.txt`, `.md`, and `.docx` files (maximum **2 MB**) as new editable documents.
  - `.txt`: UTF-8 plain text with paragraph breaks.
  - `.md`: Markdown headings, lists, and emphasis converted to rich text.
  - `.docx`: paragraphs, headings, basic list styles, and bold/italic/underline. Complex tables, embedded images, comments, and advanced layouts are **not** preserved.
- **Share** documents with another seeded user as an **editor**; owners can grant and revoke access.
- **Owned vs. shared** sections, visible ownership and access labels, and demo-account switching.
- **SQLite persistence** for documents, HTML formatting, owners, and shares. Survives page refresh and application restart when the database file is on persistent storage.
- **Server-side permission checks**, HTML sanitization, upload validation, and optimistic version checks (409 on conflicting saves).
- **Responsive UI** with a document sidebar, editing canvas, and sharing panel.

## Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | HTML, CSS, vanilla JavaScript, browser `contenteditable` | No build step; fast to ship and review |
| API | Python, FastAPI, Pydantic | Clear REST contracts, validation, easy tests |
| Storage | SQLite (stdlib `sqlite3`) | Durable local persistence with minimal setup |
| Rich text | Sanitized HTML | Preserves basic formatting across reloads |
| File imports | Mistune, python-docx | Markdown and basic Word document support |
| Tests | pytest + FastAPI TestClient | Permission, persistence, import, security, concurrency coverage |

## Run locally

Requires **Python 3.11+**. No accounts, API keys, paid services, or Node.js are required.

```bash
# From this folder
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The app automatically creates `data/folio.sqlite3` and seeds three demo users plus one example document.

Alternative with Docker:

```bash
docker build -t folio .
docker run --rm -p 8000:8000 -v folio_data:/app/data folio
```

The named Docker volume keeps the SQLite database between container restarts.

### Run automated tests

```bash
pytest -q
```

Expected: **7 passing tests**. They cover creating and reopening formatted content after an app restart, sharing/revoking and editor restrictions, optimistic concurrency, HTML sanitization, `.txt`/`.md`/`.docx` imports, validation, and demo identity checks.

### Demo users — no password required

| User | Demo email | How to test |
|---|---|---|
| **Alex Morgan** | `alex@folio.demo` | Owner of seeded “Welcome to Folio” document; can share and rename |
| **Jordan Lee** | `jordan@folio.demo` | Seeded editor on Alex's welcome document; sees it under “Shared with you” |
| **Sam Rivera** | `sam@folio.demo` | No initial document access; confirms that unshared documents are hidden |

Switch accounts using the **Demo account** selector at the bottom-left of the app. This is **mock identity, not authentication**: the client sends `X-User-Id`, and the server enforces access for that selected identity. It is intended solely for reviewer demonstration and must not be used for sensitive data.

### Suggested 90-second reviewer flow

1. Open the seeded document as **Alex**; edit a sentence and use bold or a list. Wait for **All changes saved** and refresh.
2. Create a document and rename it. Optionally import `sample_files/team_update.md` using **Import a file** (or use any `.txt` / `.md` / `.docx` file).
3. With Alex selected, use the right-side **People with access** panel to grant **Jordan** editing access to your new document.
4. Switch to **Jordan** and open the document under **Shared with you**. Edit its content; the title remains owner-controlled.
5. Switch to **Sam** to verify the document does not appear. Switch back to Alex and revoke Jordan's access if desired.

## API overview

All document endpoints require `X-User-Id: 1`, `2`, or `3`. Demo identity is deliberately untrusted and is **not** a production login.

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/users` | Seeded demo accounts |
| GET | `/api/documents` | Owned and shared documents for selected user |
| POST | `/api/documents` | Create document (`{"title":"..."}`) |
| GET | `/api/documents/{id}` | Fetch document if authorized |
| PATCH | `/api/documents/{id}` | Update content; owner can also rename; requires `expected_version` |
| POST | `/api/documents/{id}/share` | Owner grants editing access (`{"user_id":2}`) |
| DELETE | `/api/documents/{id}/share/{user_id}` | Owner revokes access |
| POST | `/api/import` | Multipart file import, creates owned document |

API docs are available at **http://127.0.0.1:8000/docs**.

## Deployment

A `Dockerfile` and `render.yaml` are included. A simple deployment path is to push this folder to a GitHub repository and deploy a **Python web service** on Render (subject to current free-tier availability):

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health endpoint: `/api/health`
- `FOLIO_DB_PATH`: defaults to `data/folio.sqlite3` in the app directory.

**Persistence caveat:** Some free hosts (including Render's ephemeral instances) do not retain local files across restarts or redeployments. On those hosts, documents persist across page refreshes while the instance remains alive, but **not** across instance replacement. For restart-durable production hosting, mount a persistent volume at `/app/data` (Docker) or move storage to a managed database. Do not describe an ephemeral deployment as fully durable.

**Live deployment:** https://folio-document-editor.onrender.com (reported Live by submitter; final browser verification pending). The walkthrough URL is available; verify that it is publicly viewable. The Google Drive folder still needs to be supplied. See `SUBMISSION.md` and `PUBLIC_TEST_CHECKLIST.md`.

## Known limitations / intentional scope cuts

- **Not real-time collaborative editing.** Multiple people can edit a shared document at different times; concurrent saves use version checks and return a conflict rather than silently overwrite.
- **No real login or security-grade identity.** Demo users are switchable by design.
- **No granular roles beyond owner/editor**, comments, presence, suggestions, history, export, or advanced rich-text features.
- Uses browser `contenteditable` and `execCommand` for a lightweight formatting toolbar. `execCommand` is deprecated but remains supported by major browsers; a production editor should migrate to TipTap/ProseMirror or Lexical.
- SQLite is appropriate for this small demo; for multi-instance deployment, migrate to Postgres and a proper authentication/authorization layer.

See [ARCHITECTURE.md](ARCHITECTURE.md) for decisions and next steps, [AI_WORKFLOW.md](AI_WORKFLOW.md) for AI usage, and [SUBMISSION.md](SUBMISSION.md) for deliverable status.