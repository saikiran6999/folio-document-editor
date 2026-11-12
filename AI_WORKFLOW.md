# AI-native workflow note

## Tools used

- **ChatGPT (GPT-6):** product scoping, backend/frontend scaffolding, test drafting, UI iteration, and writing implementation notes.
- **Python, pytest, FastAPI TestClient:** ran automated checks on the implementation.
- **Node.js syntax check:** verified the JavaScript file parses (`node --check static/app.js`).
- **Playwright / headless Chromium:** exercised real browser UI interactions against a running FastAPI API via a local test bridge.

No paid AI API or model is required to run Folio. No AI feature was added to the product solely to make the assignment look more AI-focused.

## Where AI accelerated the work

AI helped turn an ambiguous product brief into a bounded end-to-end flow, generate repetitive API/UI scaffolding, propose negative permission tests, and draft reviewer-facing documentation. The time saved went into verifying actual persistence, sharing behavior, error handling, and the visual quality of the editor.

## What I changed or rejected

- **Rejected:** attempting Google Docs–style real-time collaboration within the timebox. Implemented owner/editor sharing with optimistic version checks instead.
- **Rejected:** relying only on frontend hiding for access control. Every document read/write/share operation checks the selected identity on the server.
- **Changed:** added server-side HTML sanitization rather than trusting the browser's `contenteditable` output.
- **Changed:** added file-type, size, encoding, and empty-upload validation; DOCX conversion is deliberately limited to basic formatting.
- **Changed after browser testing:** guarded access to `sessionStorage` so the UI also initializes in restricted browser contexts.
- **Rejected:** a complex React + editor-library dependency chain for this small demo; used a no-build frontend and documented the `execCommand` limitation.

## How I verified correctness

1. Ran `pytest -q`: **7 tests passed**.
2. Ran `node --check static/app.js`: no syntax errors.
3. Started the actual FastAPI service and checked `/api/health`.
4. Exercised the browser UI using Playwright: open seeded document, create and rename a document, edit and save, reinitialize the UI and reopen persisted content, grant Jordan access, switch to Jordan and verify the shared document is editable, switch to Sam and verify no access, and open the mobile navigation.
5. Reviewed captured desktop/mobile screenshots for layout and readability.

**Verification boundary:** the browser smoke test used an API bridge because the test container blocked direct Chromium navigation to localhost. API calls still reached the real FastAPI server. A final end-to-end test against the eventual public deployment remains necessary.

## Human judgment and disclosure

AI was used as a coding collaborator, not as a substitute for product decisions or testing. The delivered code, architecture choices, and limitations are documented for review. A submitter should only claim additional tools (for example, Claude Code) if they actually used them on this assignment.