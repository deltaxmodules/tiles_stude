import glob
import os
from dataclasses import dataclass
from typing import Optional

import yaml


@dataclass
class TileConfig:
    name: str
    model: str
    system_prompt: str
    utterances: list[str]
    threshold: float
    priority: int
    ttl_seconds: int
    similarity_threshold: float
    keep_warm_after: int
    prewarm_on: list[str]
    eviction_priority: str


def load_tiles(tiles_dir: str = 'tiles') -> dict[str, TileConfig]:
    tiles = {}
    for path in glob.glob(os.path.join(tiles_dir, '*.yaml')):
        with open(path) as f:
            raw = yaml.safe_load(f)
        name = raw['metadata']['name']
        tiles[name] = TileConfig(
            name=name,
            model=raw['model']['base'],
            system_prompt=raw['model'].get('system_prompt', ''),
            utterances=raw['routing']['utterances'],
            threshold=raw['routing'].get('threshold', 0.75),
            priority=raw['routing'].get('priority', 5),
            ttl_seconds=raw['cache']['ttl_seconds'],
            similarity_threshold=raw['cache']['similarity_threshold'],
            keep_warm_after=raw['scheduler']['keep_warm_after'],
            prewarm_on=raw['scheduler'].get('prewarm_on', []),
            eviction_priority=raw['scheduler'].get('eviction_priority', 'medium'),
        )
    return tiles


TILES = load_tiles()


def get_tile(name: str) -> Optional[TileConfig]:
    return TILES.get(name)


def all_tiles() -> list[TileConfig]:
    return sorted(TILES.values(), key=lambda t: t.priority, reverse=True)
