import threading
import time
from collections import Counter, deque

import httpx

from app.config import HISTORY_SIZE, OLLAMA_BASE_URL, PREWARM_HTTP_TIMEOUT_SECONDS
from app.services.tile_loader import TILES, TileConfig


class PrewarmScheduler:
    def __init__(self):
        self.history: deque[str] = deque(maxlen=HISTORY_SIZE)
        self.warm_tiles: dict[str, float] = {}
        self._lock = threading.Lock()

    def record_route(self, route_name: str):
        with self._lock:
            self.history.append(route_name)
        self._maybe_prewarm(route_name)

    def _maybe_prewarm(self, current_route: str):
        tile = TILES.get(current_route)
        if not tile:
            return
        for target_name in tile.prewarm_on:
            target = TILES.get(target_name)
            if target and target_name not in self.warm_tiles:
                threading.Thread(target=self._prewarm_tile, args=(target,), daemon=True).start()

    def _prewarm_tile(self, tile: TileConfig):
        try:
            resp = httpx.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": tile.model, "prompt": "", "keep_alive": f"{tile.keep_warm_after}s"},
                timeout=PREWARM_HTTP_TIMEOUT_SECONDS,
            )
            if resp.status_code == 200:
                self.warm_tiles[tile.name] = time.time()
        except Exception:
            pass

    def is_warm(self, tile_name: str) -> bool:
        return tile_name in self.warm_tiles

    def predict_next(self) -> str | None:
        if not self.history:
            return None
        counts = Counter(self.history)
        return counts.most_common(1)[0][0]


scheduler = PrewarmScheduler()
