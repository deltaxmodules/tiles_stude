from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
import app.api.routes as routes


client = TestClient(app)


def _fake_tile(name: str = 'general'):
    return SimpleNamespace(
        name=name,
        model='fake-model',
        system_prompt='',
        ttl_seconds=123,
        similarity_threshold=0.77,
    )


def test_health_returns_ok():
    resp = client.get('/health')
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'ok'
    assert isinstance(body['tiles'], list)


def test_chat_non_stream_cache_hit(monkeypatch):
    monkeypatch.setattr(routes, 'route', lambda query: ('general', 'fake-model'))
    monkeypatch.setattr(routes, 'get_cached', lambda *args, **kwargs: 'from-cache')
    monkeypatch.setattr(routes, 'get_tile', lambda name: _fake_tile(name or 'general'))

    resp = client.post(
        '/v1/chat/completions',
        json={'messages': [{'role': 'user', 'content': 'hello'}], 'stream': False},
    )

    assert resp.status_code == 200
    assert resp.json()['choices'][0]['message']['content'] == 'from-cache'


def test_chat_non_stream_cache_miss(monkeypatch):
    monkeypatch.setattr(routes, 'route', lambda query: ('general', 'fake-model'))
    monkeypatch.setattr(routes, 'get_cached', lambda *args, **kwargs: None)
    monkeypatch.setattr(routes, 'get_tile', lambda name: _fake_tile(name or 'general'))

    calls = {'set_cache': 0}

    async def fake_composite_stream(tile, messages, is_warm):
        yield 'foo'
        yield 'bar'

    def fake_set_cache(*args, **kwargs):
        calls['set_cache'] += 1

    monkeypatch.setattr(routes, 'composite_stream', fake_composite_stream)
    monkeypatch.setattr(routes, 'set_cache', fake_set_cache)

    resp = client.post(
        '/v1/chat/completions',
        json={'messages': [{'role': 'user', 'content': 'hello'}], 'stream': False},
    )

    assert resp.status_code == 200
    assert resp.json()['choices'][0]['message']['content'] == 'foobar'
    assert calls['set_cache'] == 1


def test_chat_streaming_mode(monkeypatch):
    monkeypatch.setattr(routes, 'route', lambda query: ('general', 'fake-model'))
    monkeypatch.setattr(routes, 'get_cached', lambda *args, **kwargs: None)
    monkeypatch.setattr(routes, 'get_tile', lambda name: _fake_tile(name or 'general'))

    async def fake_composite_stream(tile, messages, is_warm):
        yield 'hello '
        yield 'world'

    monkeypatch.setattr(routes, 'composite_stream', fake_composite_stream)
    monkeypatch.setattr(routes, 'set_cache', lambda *args, **kwargs: None)

    resp = client.post(
        '/v1/chat/completions',
        json={'messages': [{'role': 'user', 'content': 'hello'}], 'stream': True},
    )

    assert resp.status_code == 200
    assert resp.headers['content-type'].startswith('text/event-stream')
    assert 'data: hello ' in resp.text
    assert 'data: world' in resp.text
