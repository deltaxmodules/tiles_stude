from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_homepage_renders():
    resp = client.get('/')
    assert resp.status_code == 200
    assert 'Execution Trace' in resp.text
    assert 'Ask a question and run experiments...' in resp.text
