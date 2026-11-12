# Folio — Ajaia AI-Native Full Stack Developer assignment

## Submission status

- **Source code:** included in this folder.
- **README with local setup:** included (`README.md`).
- **Architecture note:** included (`ARCHITECTURE.md`).
- **AI workflow note:** included (`AI_WORKFLOW.md`).
- **Screenshots:** included (`screenshots/`).
- **Automated tests:** included; **7 passed locally**.
- **Live product URL:** **PENDING — must deploy and paste the public URL here.**
- **Walkthrough video URL:** **PENDING — must record and replace `video_url.txt`.**
- **Google Drive folder URL:** **PENDING — must upload this project and paste the folder URL here.**

## Reviewer quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
# Open http://127.0.0.1:8000
pytest -q
```

## Seeded accounts

- **Alex Morgan** (`alex@folio.demo`) — document owner; can create, rename, edit, share, revoke.
- **Jordan Lee** (`jordan@folio.demo`) — shared editor on Alex's seeded welcome document.
- **Sam Rivera** (`sam@folio.demo`) — initially no access to Alex's documents.

Use the **Demo account** dropdown at the bottom of the sidebar. No passwords are needed. This is intentionally mocked authentication, not a secure login.

## Working functionality

Create, rename, rich-text edit, autosave, reopen, `.txt`/`.md`/basic `.docx` import (2 MB maximum), owner/editor sharing, owned/shared separation, permission checks, sanitized content, and 409 conflict detection. SQLite persists document content and sharing on a durable filesystem.

## Incomplete / intentionally deprioritized

No real-time simultaneous collaboration, production authentication, comments, history, or complex Word formatting. On hosts with ephemeral disks, SQLite does not survive instance replacement. **The deployment and video are not yet completed.**

## What I would build with another 2–4 hours

First, deploy with durable storage and test public access. Next, implement real authentication and upgrade the editor to TipTap/ProseMirror. Then add basic revision history.

## Included files

```text
folio_assignment/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── storage.py
├── static/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── favicon.svg
├── tests/
│   └── test_app.py
├── sample_files/
│   └── team_update.md
├── screenshots/
│   ├── 01-editor-desktop.png
│   ├── 02-sharing-owner.png
│   ├── 03-shared-editor.png
│   ├── 04-no-access.png
│   └── 05-mobile.png
├── README.md
├── ARCHITECTURE.md
├── AI_WORKFLOW.md
├── WALKTHROUGH_SCRIPT.md
├── SUBMISSION.md
├── video_url.txt
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── render.yaml
└── start.sh
```