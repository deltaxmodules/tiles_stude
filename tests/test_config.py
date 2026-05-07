from app.config import Settings


def test_resolved_ollama_base_url_from_explicit_url():
    s = Settings(OLLAMA_BASE_URL='http://127.0.0.1:11434')
    assert s.resolved_ollama_base_url == 'http://127.0.0.1:11434'


def test_resolved_ollama_base_url_from_host_and_port():
    s = Settings(OLLAMA_HOST='localhost', OLLAMA_PORT=11435)
    assert s.resolved_ollama_base_url == 'http://localhost:11435'


def test_resolved_ollama_base_url_normalizes_host_url_without_port():
    s = Settings(OLLAMA_HOST='http://example.com', OLLAMA_PORT=11436)
    assert s.resolved_ollama_base_url == 'http://example.com:11436'
