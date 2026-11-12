"""API tests: permissions, persistence, formatting, import, concurrency, validation."""
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient
import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    return TestClient(create_app(tmp_path / "test.sqlite3"))


def as_user(user_id: int):
    return {"X-User-Id": str(user_id)}


def create_doc(client, title="Sprint notes"):
    res = client.post('/api/documents', json={"title": title}, headers=as_user(1))
    assert res.status_code == 201, res.text
    return res.json()


def test_create_format_save_reopen_and_persist_after_restart(tmp_path):
    path = tmp_path / 'persistent.sqlite3'
    client = TestClient(create_app(path))
    doc = create_doc(client)
    res = client.patch(f'/api/documents/{doc["id"]}', json={
        "expected_version": doc["version"],
        "title": "Planning notes",
        "content_html": '<h1>Launch</h1><p><strong>Important</strong> and <em>urgent</em></p><ul><li>Ship</li></ul>'
    }, headers=as_user(1))
    assert res.status_code == 200
    assert res.json()['version'] == doc['version'] + 1
    fresh_client = TestClient(create_app(path))
    saved = fresh_client.get(f'/api/documents/{doc["id"]}', headers=as_user(1))
    assert saved.status_code == 200
    assert saved.json()['title'] == 'Planning notes'
    assert '<strong>Important</strong>' in saved.json()['content_html']
    assert '<ul><li>Ship</li></ul>' in saved.json()['content_html']


def test_owner_sharing_editor_permissions_and_revocation(client):
    doc = create_doc(client)
    doc_id = doc['id']
    assert client.get(f'/api/documents/{doc_id}', headers=as_user(3)).status_code == 404
    shared = client.post(f'/api/documents/{doc_id}/share', json={"user_id": 2}, headers=as_user(1))
    assert shared.status_code == 201
    assert shared.json()['shared_with'][0]['name'] == 'Jordan Lee'
    listing = client.get('/api/documents', headers=as_user(2)).json()
    assert any(d['id'] == doc_id and d['access'] == 'editor' for d in listing)
    editor = client.get(f'/api/documents/{doc_id}', headers=as_user(2)).json()
    assert editor['access'] == 'editor'
    assert client.patch(f'/api/documents/{doc_id}', json={
        'expected_version': editor['version'], 'content_html': '<p>Jordan wrote this.</p>'
    }, headers=as_user(2)).status_code == 200
    assert client.patch(f'/api/documents/{doc_id}', json={
        'expected_version': editor['version'] + 1, 'title': 'Unauthorized rename'
    }, headers=as_user(2)).status_code == 403
    assert client.post(f'/api/documents/{doc_id}/share', json={'user_id': 3}, headers=as_user(2)).status_code == 403
    assert client.delete(f'/api/documents/{doc_id}/share/2', headers=as_user(1)).status_code == 204
    assert client.get(f'/api/documents/{doc_id}', headers=as_user(2)).status_code == 404


def test_stale_version_rejected_without_overwriting(client):
    doc = create_doc(client)
    path = f'/api/documents/{doc["id"]}'
    good = client.patch(path, json={"expected_version": 1, "content_html": "<p>New version</p>"}, headers=as_user(1))
    assert good.status_code == 200
    stale = client.patch(path, json={"expected_version": 1, "content_html": "<p>Stale overwrite</p>"}, headers=as_user(1))
    assert stale.status_code == 409
    assert 'New version' in client.get(path, headers=as_user(1)).json()['content_html']


def test_sanitizes_unsafe_markup(client):
    doc = create_doc(client)
    res = client.patch(f'/api/documents/{doc["id"]}', json={
        'expected_version': 1,
        'content_html': '<p onclick="evil()">Safe <strong>bold</strong><img src=x onerror=evil()></p><script>alert(1)</script>'
    }, headers=as_user(1))
    assert res.status_code == 200
    content = res.json()['content_html']
    assert '<strong>bold</strong>' in content
    assert '<script' not in content
    assert 'onclick=' not in content
    assert '<img' not in content


def test_import_txt_and_markdown(client):
    txt = client.post('/api/import', headers=as_user(1), files={
        'file': ('meeting.txt', b'First paragraph\n\nSecond & final', 'text/plain')
    })
    assert txt.status_code == 201
    assert txt.json()['title'] == 'meeting'
    assert '<p>First paragraph</p>' in txt.json()['content_html']
    assert '&amp;' in txt.json()['content_html']
    md = client.post('/api/import', headers=as_user(1), files={
        'file': ('ideas.md', b'# Ideas\n\n- One\n- Two', 'text/markdown')
    })
    assert md.status_code == 201
    assert '<h1>Ideas</h1>' in md.json()['content_html']
    assert '<li>One</li>' in md.json()['content_html']


def test_import_docx_with_basic_formatting(client):
    doc = Document()
    doc.add_heading('Release plan', level=1)
    paragraph = doc.add_paragraph()
    paragraph.add_run('Important').bold = True
    paragraph.add_run(' update')
    stream = BytesIO()
    doc.save(stream)
    res = client.post('/api/import', headers=as_user(1), files={
        'file': ('release.docx', stream.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    })
    assert res.status_code == 201, res.text
    assert '<h1>Release plan</h1>' in res.json()['content_html']
    assert '<strong>Important</strong>' in res.json()['content_html']


def test_upload_validation_and_auth(client):
    assert client.get('/api/documents').status_code == 401
    assert client.get('/api/documents', headers=as_user(999)).status_code == 401
    assert client.post('/api/import', headers=as_user(1), files={
        'file': ('malware.exe', b'hello', 'application/octet-stream')
    }).status_code == 415
    assert client.post('/api/import', headers=as_user(1), files={
        'file': ('large.txt', b'x' * (2 * 1024 * 1024 + 1), 'text/plain')
    }).status_code == 413
    assert client.post('/api/documents', json={'title': '   '}, headers=as_user(1)).status_code == 422