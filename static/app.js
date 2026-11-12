/* Folio: dependency-free client. Demo identity is intentionally not authentication. */
(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const storedUser = (() => { try { return Number(sessionStorage.getItem('folio_demo_user') || 1); } catch { return 1; } })();
  const state = {
    userId: storedUser,
    users: [], docs: [], doc: null, dirty: false, saving: null,
    timer: null, conflict: false, savedRange: null, toastTimer: null,
  };
  const fileIcon = `<svg class="doc-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h8"/></svg>`;
  const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const initials = (name) => name.split(/\s+/).map(x => x[0] || '').slice(0, 2).join('').toUpperCase();
  const friendlyDate = (s) => {
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return 'Recently';
    const diff = Date.now() - d.getTime();
    if (diff < 60_000) return 'Just now';
    if (diff < 3_600_000) return `${Math.max(1, Math.floor(diff / 60_000))} min ago`;
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} hr ago`;
    return d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  };

  async function api(path, options = {}) {
    const headers = {'X-User-Id': String(state.userId), ...(options.headers || {})};
    if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    let response;
    try { response = await fetch(path, {...options, headers}); }
    catch { throw new Error('Could not connect to the server. Check your connection.'); }
    if (!response.ok) {
      let payload = {};
      try { payload = await response.json(); } catch { /* non-JSON error */ }
      const detail = Array.isArray(payload.detail) ? 'Please check the input and try again.' : payload.detail;
      const err = new Error(detail || `Request failed (${response.status}).`);
      err.status = response.status;
      throw err;
    }
    return response.status === 204 ? null : response.json();
  }

  function toast(message, isError = false) {
    const node = $('toast');
    node.textContent = message;
    node.className = `toast visible${isError ? ' error' : ''}`;
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => node.className = 'toast', 3500);
  }

  function status(message, kind = 'saved') {
    const node = $('saveIndicator');
    node.className = `save-indicator${kind === 'saved' ? '' : ` ${kind}`}`;
    node.innerHTML = `<span class="save-dot"></span> ${escapeHtml(message)}`;
  }

  function updateWordCount() {
    const text = $('editor').innerText.trim();
    const count = text ? text.split(/\s+/).filter(Boolean).length : 0;
    $('wordCount').textContent = `${count} word${count === 1 ? '' : 's'}`;
  }

  function renderAccount() {
    const user = state.users.find(u => u.id === state.userId) || state.users[0];
    if (!user) return;
    $('accountAvatar').textContent = initials(user.name);
    $('accountName').textContent = user.name;
    $('accountEmail').textContent = user.email;
    $('userSelect').value = String(state.userId);
  }

  function renderList(targetId, docs, emptyText) {
    const container = $(targetId);
    if (!docs.length) {
      container.innerHTML = `<div class="nav-empty">${escapeHtml(emptyText)}</div>`;
      return;
    }
    container.innerHTML = docs.map(doc => `
      <button class="doc-item${state.doc?.id === doc.id ? ' active' : ''}" data-doc-id="${doc.id}" aria-label="Open ${escapeHtml(doc.title)}">
        ${fileIcon}
        <span class="doc-item-copy"><span class="doc-item-title">${escapeHtml(doc.title)}</span>
        <span class="doc-item-meta">${doc.access === 'owner' ? 'Edited' : `By ${escapeHtml(doc.owner_name)}`} · ${escapeHtml(friendlyDate(doc.updated_at))}</span></span>
      </button>`).join('');
    container.querySelectorAll('[data-doc-id]').forEach(button => {
      button.addEventListener('click', () => openDocument(Number(button.dataset.docId)));
    });
  }

  function renderNav() {
    const search = $('searchInput').value.trim().toLowerCase();
    const owned = state.docs.filter(d => d.access === 'owner' && d.title.toLowerCase().includes(search));
    const shared = state.docs.filter(d => d.access !== 'owner' && d.title.toLowerCase().includes(search));
    $('ownedCount').textContent = String(state.docs.filter(d => d.access === 'owner').length);
    $('sharedCount').textContent = String(state.docs.filter(d => d.access !== 'owner').length);
    renderList('ownedDocs', owned, search ? 'No matching documents' : 'No documents yet');
    renderList('sharedDocs', shared, search ? 'No matching documents' : 'Nothing shared yet');
  }

  async function refreshDocs() {
    state.docs = await api('/api/documents');
    renderNav();
  }

  function showWelcome() {
    $('welcomeScreen').hidden = false;
    $('documentView').hidden = true;
    $('topShareBtn').disabled = true;
    $('breadcrumbTitle').textContent = 'Overview';
    $('detailsContent').innerHTML = '<div class="details-placeholder"><span>✳</span><p>Select a document to see its details and sharing options.</p></div>';
    status('Ready to write');
  }

  function renderDetails() {
    const doc = state.doc;
    if (!doc) return;
    const owner = state.users.find(u => u.id === doc.owner_id) || {name:doc.owner_name, email:'Owner'};
    const available = state.users.filter(u => u.id !== doc.owner_id && !doc.shared_with.some(s => s.id === u.id));
    const people = doc.shared_with.map(u => `
      <div class="share-person"><span class="person-avatar alt">${escapeHtml(initials(u.name))}</span>
      <span class="person-info"><strong>${escapeHtml(u.name)}</strong><small>Can edit</small></span>
      ${doc.access === 'owner' ? `<button class="remove-share" data-revoke-id="${u.id}" aria-label="Remove ${escapeHtml(u.name)}'s access" title="Remove access">×</button>` : ''}
      </div>`).join('');
    $('detailsContent').innerHTML = `
      <div class="details-label">DOCUMENT OWNER</div>
      <div class="detail-owner"><span class="person-avatar">${escapeHtml(initials(owner.name))}</span><span class="person-info"><strong>${escapeHtml(owner.name)}</strong><small>${escapeHtml(owner.email || 'Document owner')}</small></span></div>
      <div class="detail-rule"></div>
      <div class="share-header"><span class="details-label">PEOPLE WITH ACCESS</span><span class="share-count">${doc.shared_with.length + 1}</span></div>
      <div class="share-list">${people || '<p class="sharing-note">Only the owner has access so far.</p>'}</div>
      ${doc.access === 'owner' ? `
        <div class="share-form"><label for="shareUserSelect">Invite a teammate</label>
        <select id="shareUserSelect" ${available.length ? '' : 'disabled'}>
          ${available.length ? available.map(u => `<option value="${u.id}">${escapeHtml(u.name)} (${escapeHtml(u.email)})</option>`).join('') : '<option>Everyone already has access</option>'}
        </select><button class="invite-button" id="inviteBtn" ${available.length ? '' : 'disabled'}>Grant editing access</button></div>
        <p class="sharing-note">Teammates can edit document content. Only you can rename the document or manage access.</p>` : `
        <div class="shared-info">You have <strong>editing access</strong> to this document. Only the owner can rename it or invite others.</div>`}
      <div class="detail-card"><div class="detail-card-title">✳ &nbsp; A little reminder</div><p>Good writing is a team sport. <strong>Changes save automatically</strong> as you type.</p></div>`;
    const invite = $('inviteBtn');
    if (invite) invite.addEventListener('click', grantAccess);
    $('detailsContent').querySelectorAll('[data-revoke-id]').forEach(button => {
      button.addEventListener('click', () => revokeAccess(Number(button.dataset.revokeId)));
    });
  }

  async function openDocument(id, force = false) {
    if (!force && state.doc?.id === id) { closePanels(); return; }
    if (!force && !(await flushSave())) { toast('Save or resolve the current changes before switching.', true); return; }
    try {
      const doc = await api(`/api/documents/${id}`);
      state.doc = doc;
      state.dirty = false;
      state.conflict = false;
      $('conflictBanner').hidden = true;
      $('docTitle').value = doc.title;
      $('docTitle').disabled = doc.access !== 'owner';
      $('editor').innerHTML = doc.content_html;
      $('breadcrumbTitle').textContent = doc.title;
      $('documentOwnerTag').textContent = doc.access === 'owner' ? 'MY WORKSPACE' : 'SHARED WITH ME';
      $('docAccess').textContent = doc.access === 'owner' ? 'OWNER' : 'SHARED EDITOR';
      $('docAccess').className = `doc-access${doc.access === 'owner' ? '' : ' shared'}`;
      $('docOwnerLine').textContent = `Created by ${doc.owner_name}`;
      $('docUpdated').textContent = `Updated ${friendlyDate(doc.updated_at).toLowerCase()}`;
      $('documentView').hidden = false;
      $('welcomeScreen').hidden = true;
      $('topShareBtn').disabled = false;
      $('blockFormat').value = 'p';
      updateWordCount();
      renderDetails();
      renderNav();
      status('All changes saved');
      closePanels();
    } catch (err) { toast(err.message, true); }
  }

  function markDirty() {
    if (!state.doc || state.conflict) return;
    state.dirty = true;
    status('Unsaved changes', 'unsaved');
    clearTimeout(state.timer);
    state.timer = setTimeout(() => { void flushSave(); }, 850);
    updateWordCount();
  }

  async function flushSave() {
    clearTimeout(state.timer);
    if (state.conflict) return false;
    if (state.saving) {
      const result = await state.saving;
      if (!result) return false;
    }
    if (!state.dirty || !state.doc) return true;
    const id = state.doc.id;
    const body = {expected_version:state.doc.version, content_html:$('editor').innerHTML};
    if (state.doc.access === 'owner') body.title = $('docTitle').value.trim() || 'Untitled document';
    state.dirty = false;
    status('Saving…', 'unsaved');
    state.saving = (async () => {
      try {
        const updated = await api(`/api/documents/${id}`, {method:'PATCH', body:JSON.stringify(body)});
        if (state.doc?.id === id) {
          state.doc.version = updated.version;
          state.doc.updated_at = updated.updated_at;
          state.doc.title = updated.title;
          $('docUpdated').textContent = 'Updated just now';
          $('breadcrumbTitle').textContent = updated.title;
        }
        return true;
      } catch (err) {
        state.dirty = true;
        if (err.status === 409) {
          state.conflict = true;
          $('conflictBanner').hidden = false;
          status('Edit conflict', 'error');
        } else {
          status('Save failed — retry', 'error');
        }
        toast(err.message, true);
        return false;
      }
    })();
    const success = await state.saving;
    state.saving = null;
    if (!success) return false;
    if (state.dirty) return flushSave();
    status('All changes saved');
    try { await refreshDocs(); } catch { /* save succeeded; sidebar can refresh later */ }
    return true;
  }

  async function createDocument() {
    if (!(await flushSave())) return;
    try {
      const doc = await api('/api/documents', {method:'POST', body:JSON.stringify({title:'Untitled document'})});
      await refreshDocs();
      await openDocument(doc.id);
      $('docTitle').focus();
      $('docTitle').select();
      toast('New document created');
    } catch (err) { toast(err.message, true); }
  }

  async function importFile(file) {
    if (!file || !(await flushSave())) return;
    if (file.size > 2 * 1024 * 1024) { toast('Maximum file size is 2 MB.', true); return; }
    const data = new FormData();
    data.append('file', file);
    try {
      status('Importing…', 'unsaved');
      const doc = await api('/api/import', {method:'POST', body:data});
      await refreshDocs();
      await openDocument(doc.id);
      toast(`${file.name} imported successfully`);
    } catch (err) { toast(err.message, true); status('Ready to write'); }
    finally { $('fileInput').value = ''; }
  }

  async function grantAccess() {
    if (!state.doc || !(await flushSave())) return;
    const targetId = Number($('shareUserSelect')?.value);
    if (!targetId) return;
    try {
      const updated = await api(`/api/documents/${state.doc.id}/share`, {method:'POST', body:JSON.stringify({user_id:targetId})});
      state.doc.shared_with = updated.shared_with;
      renderDetails();
      toast('Editing access granted');
    } catch (err) { toast(err.message, true); }
  }

  async function revokeAccess(userId) {
    if (!state.doc || !(await flushSave())) return;
    try {
      await api(`/api/documents/${state.doc.id}/share/${userId}`, {method:'DELETE'});
      state.doc.shared_with = state.doc.shared_with.filter(u => u.id !== userId);
      renderDetails();
      toast('Access removed');
    } catch (err) { toast(err.message, true); }
  }

  function closePanels() {
    $('sidebar').classList.remove('open');
    $('detailsPanel').classList.remove('open');
    $('mobileOverlay').hidden = true;
  }

  function openPanel(panel) {
    closePanels();
    panel.classList.add('open');
    $('mobileOverlay').hidden = false;
  }

  function restoreSelection() {
    if (!state.savedRange) return;
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(state.savedRange);
  }

  function runCommand(command, value) {
    if (!state.doc) return;
    $('editor').focus();
    restoreSelection();
    document.execCommand(command, false, value);
    markDirty();
    $('editor').focus();
  }

  async function switchUser(id) {
    if (id === state.userId) return;
    const oldId = state.userId;
    if (!(await flushSave())) { $('userSelect').value = String(oldId); return; }
    state.userId = id;
    try { sessionStorage.setItem('folio_demo_user', String(id)); } catch { /* storage may be unavailable in restricted browsers */ }
    state.doc = null;
    state.dirty = false;
    state.conflict = false;
    renderAccount();
    try {
      await refreshDocs();
      if (state.docs.length) await openDocument(state.docs[0].id);
      else showWelcome();
      toast(`Switched to ${state.users.find(u => u.id === id)?.name || 'demo user'}`);
    } catch (err) { toast(err.message, true); }
  }

  function wireEvents() {
    $('newDocBtn').addEventListener('click', createDocument);
    $('welcomeCreateBtn').addEventListener('click', createDocument);
    $('importBtn').addEventListener('click', () => $('fileInput').click());
    $('fileInput').addEventListener('change', e => importFile(e.target.files[0]));
    $('searchInput').addEventListener('input', renderNav);
    $('userSelect').addEventListener('change', e => switchUser(Number(e.target.value)));
    $('docTitle').addEventListener('input', markDirty);
    $('editor').addEventListener('input', markDirty);
    $('saveNowBtn').addEventListener('click', async () => { if (await flushSave()) toast('Document saved'); });
    $('reloadDocBtn').addEventListener('click', () => {
      if (!state.doc) return;
      const id = state.doc.id;
      state.dirty = false;
      state.conflict = false;
      openDocument(id, true);
    });
    $('topShareBtn').addEventListener('click', () => {
      if (window.innerWidth <= 980) openPanel($('detailsPanel'));
      else { $('detailsPanel').scrollTo({top:0,behavior:'smooth'}); $('shareUserSelect')?.focus(); }
    });
    $('closeDetailsBtn').addEventListener('click', closePanels);
    $('menuBtn').addEventListener('click', () => openPanel($('sidebar')));
    $('mobileOverlay').addEventListener('click', closePanels);
    document.querySelectorAll('[data-command]').forEach(button => {
      button.addEventListener('mousedown', e => e.preventDefault());
      button.addEventListener('click', () => runCommand(button.dataset.command));
    });
    $('blockFormat').addEventListener('change', e => runCommand('formatBlock', `<${e.target.value}>`));
    document.addEventListener('selectionchange', () => {
      const selection = window.getSelection();
      if (selection.rangeCount && $('editor').contains(selection.anchorNode)) {
        state.savedRange = selection.getRangeAt(0).cloneRange();
      }
    });
    document.addEventListener('keydown', e => {
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === 's') { e.preventDefault(); void flushSave(); }
      if (mod && e.key.toLowerCase() === 'k') { e.preventDefault(); $('searchInput').focus(); }
      if (!mod && !e.altKey && e.key.toLowerCase() === 'n' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) && document.activeElement !== $('editor')) { e.preventDefault(); void createDocument(); }
    });
  }

  async function init() {
    wireEvents();
    try {
      state.users = await api('/api/users');
      if (!state.users.some(u => u.id === state.userId)) state.userId = state.users[0]?.id || 1;
      $('userSelect').innerHTML = state.users.map(u => `<option value="${u.id}">${escapeHtml(u.name)}</option>`).join('');
      renderAccount();
      await refreshDocs();
      if (state.docs.length) await openDocument(state.docs[0].id);
      else showWelcome();
    } catch (err) { showWelcome(); toast(`Unable to load workspace: ${err.message}`, true); }
  }
  void init();
})();