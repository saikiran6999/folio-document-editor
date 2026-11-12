# Live deployment verification

**Public editor:** https://folio-document-editor.onrender.com  
**API health:** https://folio-document-editor.onrender.com/api/health

The public site has not been independently loaded from the current environment. Check these items directly in a browser before submitting.

- [ ] Open public homepage in a private browser window, without Render credentials
- [ ] Open `/api/health` and confirm a successful JSON response
- [ ] As Alex, create a document named "Demo notes"
- [ ] Apply bold, italic, heading, and bulleted list formatting
- [ ] Wait for autosave, refresh the page, reopen the document, and confirm formatting
- [ ] Import `sample_files/team_update.md` as an editable document
- [ ] As Alex, share "Demo notes" with Jordan
- [ ] As Jordan, find it under "Shared with you", edit it, and save
- [ ] As Sam, check that "Demo notes" is not listed
- [ ] As Alex, revoke Jordan's access
- [ ] Check the mobile layout and browser console for obvious errors
- [ ] Record a **3–5 minute** walkthrough and update `video_url.txt`
- [ ] Create a shareable Google Drive folder and add its URL to `SUBMISSION.md`

## Honest scope disclosures

- Identity is mocked with seeded users and is not secure authentication.
- Editing is not real-time; concurrency conflicts are detected rather than merged.
- Render free ephemeral disks may lose SQLite data across restarts/redeployments.
- `.docx` import preserves basic content and formatting only.

## If the live service fails

Check Render's deployment logs. The expected start command is:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
