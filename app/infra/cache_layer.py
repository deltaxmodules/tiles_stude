import os
import sqlite3
import time

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME, DEFAULT_CACHE_SIMILARITY_THRESHOLD, DEFAULT_TILE_TTL_SECONDS

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
DB_PATH = os.path.join(CACHE_DIR, 'cache.db')

_model = None
_cache_data: dict[str, list] = {}


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def init_cache():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY,
            tile TEXT,
            prompt TEXT,
            response TEXT,
            embedding BLOB,
            expires_at REAL
        )
    ''')
    conn.commit()
    now = time.time()
    rows = conn.execute(
        'SELECT tile, embedding, response, expires_at FROM cache WHERE expires_at > ?',
        (now,)
    ).fetchall()
    for tile, emb_bytes, response, expires_at in rows:
        emb = np.frombuffer(emb_bytes, dtype=np.float32)
        _cache_data.setdefault(tile, []).append((emb, response, expires_at))
    conn.close()


def get_cached(prompt: str, tile: str, threshold: float = DEFAULT_CACHE_SIMILARITY_THRESHOLD) -> str | None:
    entries = _cache_data.get(tile, [])
    if not entries:
        return None
    model = _get_model()
    emb = model.encode(prompt, normalize_embeddings=True)
    now = time.time()
    for stored_emb, response, expires_at in entries:
        if expires_at < now:
            continue
        if float(np.dot(emb, stored_emb)) >= threshold:
            return response
    return None


def set_cache(prompt: str, response: str, tile: str, ttl_seconds: int = DEFAULT_TILE_TTL_SECONDS):
    model = _get_model()
    emb = model.encode(prompt, normalize_embeddings=True)
    emb_bytes = emb.astype(np.float32).tobytes()
    expires_at = time.time() + ttl_seconds
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO cache (tile, prompt, response, embedding, expires_at) VALUES (?,?,?,?,?)',
        (tile, prompt, response, emb_bytes, expires_at)
    )
    conn.commit()
    conn.close()
    _cache_data.setdefault(tile, []).append((emb, response, expires_at))
