# Folio — Ajaia AI-Native Full Stack Developer assignment

## Submission status

- **Source code:** included in this folder and published at https://github.com/saikiran6999/folio-document-editor.
- **README with local setup:** included (`README.md`).
- **Architecture note:** included (`ARCHITECTURE.md`).
- **AI workflow note:** included (`AI_WORKFLOW.md`).
- **Screenshots:** optional; separate screenshots are available in the original project package. Verify they were included in the uploaded Google Drive folder if referenced.
- **Automated tests:** included; **7 passed locally**.
- **Live product URL:** https://folio-document-editor.onrender.com (reported Live on Render; submitter tested creation, saving, sharing and imports).
- **Walkthrough video URL:** https://www.loom.com/share/89410187f7844bd78ad3046578d4bf00 (link supplied; public-view permissions and duration not independently verified).
- **Google Drive folder URL:** https://drive.google.com/drive/folders/1D_bGIJBO_fLPU6rEO3wZAM0t6dA_0-jD?usp=sharing (folder link supplied by submitter; viewer access and contents not independently verified).

## Public reviewer links

- **Application:** https://folio-document-editor.onrender.com
- **API health:** https://folio-document-editor.onrender.com/api/health
- **Source:** https://github.com/saikiran6999/folio-document-editor
- **Video:** https://www.loom.com/share/89410187f7844bd78ad3046578d4bf00 (check public playback in an incognito window)
- **Google Drive:** https://drive.google.com/drive/folders/1D_bGIJBO_fLPU6rEO3wZAM0t6dA_0-jD?usp=sharing

**Public verification boundary:** The submitter reports the Render service is Live and personally verified document creation/saving, sharing, and file import in a browser. All seven automated tests passed locally. Third-party public access to the live site, Loom video, and Google Drive folder has not been independently verified here. SQLite on Render's ephemeral disk is not durable across service replacements.

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

No real-time simultaneous collaboration, production authentication, comments, history, or complex Word formatting. On hosts with ephemeral disks, SQLite does not survive instance replacement. **The public application and walkthrough URL have been supplied. The submitter reports successful browser testing of creation, saving, sharing, and imports. Third-party public playback of the video has not been independently verified.**

## What I would build with another 2–4 hours

First, add durable hosted storage (managed Postgres or persistent volume) and verify redeploy persistence. Next, implement real authentication and upgrade the editor to TipTap/ProseMirror. Then add basic revision history.

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
├── PUBLIC_TEST_CHECKLIST.md
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