# Suggested 4-minute walkthrough recording

Record your own screen and narration with Loom, YouTube, or a similar tool. Do not submit this script in place of the required video.

**0:00–0:25 — Context and scope**

“Hi, I'm Sai Kiran. This is Folio, a lightweight collaborative document editor. I focused on a complete document lifecycle: create, edit, import, save, and share. I intentionally didn't build real-time cursors or a full Google Docs clone.”

**0:25–1:20 — Create, edit, format, persist**

As Alex, open the seeded welcome document. Create a new document called “Team planning notes.” Type a few lines, select text and apply bold, add a heading and bullet list. Show the save indicator, refresh the page, and reopen the document to demonstrate persisted content and formatting.

**1:20–1:55 — File import**

Click **Import a file** and upload a small `.md` or `.txt` file. Show that it becomes a new editable document. Mention support for `.txt`, `.md`, and basic `.docx` up to 2 MB, and that complex Word formatting isn't preserved.

**1:55–2:55 — Sharing and access**

As Alex, grant Jordan editing access to the new document in the right-side panel. Switch to Jordan using the demo-account selector. Show the document under **Shared with you** and edit its content. Explain that only Alex can rename or change access. Switch to Sam and demonstrate the document is not visible. Switch back to Alex and optionally revoke access.

**2:55–3:35 — Architecture and engineering quality**

Show `ARCHITECTURE.md` and briefly explain FastAPI, SQLite, server-side permission checks, sanitized HTML, autosave, and optimistic concurrency. Show `pytest -q` with seven passing tests.

**3:35–4:10 — AI workflow and tradeoffs**

“ChatGPT helped with scaffolding, test ideas, and documentation. I revised the approach to enforce permissions on the server, sanitize rich-text HTML, and handle conflicting saves. I chose a no-build frontend to prioritize a working end-to-end slice. Next I would add real authentication, durable hosted storage, and a structured editor like TipTap.”

**Before recording:** reset the demo database if you want a clean workspace; test your microphone and public video permissions; keep the live deployment open in a separate browser tab; verify the public URL works without your login.