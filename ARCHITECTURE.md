# Architecture and prioritization

## Product slice

**Target user:** a small internal team that wants to create documents, format notes, import existing material, and share editable access without learning a complex product.

**Primary flow:** open workspace → create/import document → edit with formatting → autosave → share with teammate → teammate opens and edits.

I prioritized this full end-to-end flow over real-time collaboration. A credible single-user editing and sharing experience with persistence is more valuable in a 4–6 hour exercise than a partially functioning WebSocket implementation.

## System diagram

```text
Browser (vanilla JS + contenteditable)
  |  REST /api/*, X-User-Id demo identity
  v
FastAPI / Pydantic validation
  |-- Permission checks (owner or shared editor)
  |-- HTML allowlist sanitizer (Bleach)
  |-- File conversion (.txt, .md, .docx)
  |-- Optimistic version check
  v
SQLite
  |-- users (seeded demo accounts)
  |-- documents (owner, title, sanitized HTML, version, timestamps)
  |-- document_shares (document_id, user_id)
```

### Key data relationships

- `users(id, name, email)` — three seeded users.
- `documents(id, owner_id, title, content_html, version, created_at, updated_at)` — one owner per document.
- `document_shares(document_id, user_id, created_at)` — many-to-many sharing; shared users receive editor access.
- `app_meta` — records whether initial demo content has been seeded.

The `version` integer is incremented on every successful edit. The browser sends `expected_version`; a mismatch returns **409 Conflict**, preventing silent overwrites from stale tabs. The UI surfaces a warning and offers to reload, rather than auto-merging incompatible changes.

## Important engineering decisions

1. **Single FastAPI service** serves static UI and API on the same origin. No CORS setup, Node build, or deployment coordination required.
2. **SQLite** is enough for a scoped demo and makes setup nearly zero-config. Each request uses a short-lived database connection with foreign keys enabled.
3. **Sanitized HTML** preserves basic rich-text structure. Server allowlists tags and removes attributes, styles, scripts, images, and links to reduce XSS risk. This intentionally excludes embedded media and advanced formatting.
4. **Mock identity with server-side access checks** is explicit and testable. Owners can rename and manage sharing; shared editors can update content. Unshared users receive 404 so private document existence is not revealed through the API.
5. **Import creates a new document** instead of modifying an existing draft, avoiding confusing partial overwrites. Text/Markdown/DOCX are limited to 2 MB.
6. **Autosave + manual save** supports normal writing. A version conflict is reported rather than quietly replacing someone else's changes.
7. **No external JavaScript runtime dependencies** keeps first-run setup fast and reduces deployment risk. This sacrifices the richer editing semantics of a dedicated editor framework.

## Quality and verification

- Seven API tests cover formatting persistence, app restart, permissions, sharing/revocation, concurrency conflicts, sanitizer behavior, imports, invalid uploads, and mock identity validation.
- JavaScript passed `node --check`.
- Browser UI interactions were exercised in headless Chromium with Playwright, including creation, editing, save, reinitialization, sharing, account switching, unauthorized access, and responsive navigation. The local test harness used a Python API bridge because direct loopback navigation was restricted in the test environment; the backend was the real running FastAPI service.
- Screenshots of the editor, sharing, shared-user view, access-restricted view, and mobile navigation are included.

## Security and production boundaries

This is **not production authentication**. Any caller can select a seeded user ID in a header; the permission logic is meaningful within that mock model, but a real deployment would need verified user identity. No confidential documents should be uploaded to the public demo. A production service would also need CSRF/session design, rate limits, malware scanning, tighter DOCX resource limits, audit logging, backup/restore, and durable multi-instance storage.

The `execCommand` editing API is deprecated. For a production editor, replace it with a structured rich-text model such as TipTap/ProseMirror or Lexical; preserve a canonical document JSON schema and serialize safe HTML for display.

## What I deliberately did not build

- Simultaneous multi-cursor editing / CRDT or OT synchronization
- OAuth, password login, and enterprise access control
- Comments, suggestions, revision history, and document export
- Tables, embedded images, complex Word fidelity
- A heavy frontend framework and JavaScript build pipeline

## Next 2–4 hours

1. **First:** deploy with restart-durable storage, add a public smoke test, and verify sharing across independent browser sessions.
2. **Second:** add proper authentication (session or OIDC) and replace the mock identity header; keep authorization checks in the API.
3. **Third:** migrate the editor to TipTap/ProseMirror for better selection handling, paste behavior, and structured content.
4. **If time remains:** add a basic revision-history table and a restore action. Real-time multi-user cursors would come after reliable history and auth.

## Operational tradeoff

The bundled app works locally and in a single-instance demo. On a free host with ephemeral storage, data survives page refresh but not instance replacement. A persistent disk or managed database is required before claiming full deployment durability.