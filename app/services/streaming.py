import asyncio
import json
from typing import AsyncIterator

import httpx

from app.config import HTTP_TIMEOUT_SECONDS, OLLAMA_BASE_URL
from app.services.tile_loader import TileConfig

PREAMBLES = {
    'code': 'Looking at your code request... ',
    'reasoning': 'Analyzing this carefully... ',
    'general': 'Let me help with that... ',
    None: 'Processing your request... ',
}


async def composite_stream(tile: TileConfig, messages: list[dict], is_warm: bool) -> AsyncIterator[str]:
    if not is_warm:
        preamble = PREAMBLES.get(tile.name, PREAMBLES[None])
        yield preamble
        await asyncio.sleep(0.05)

    msgs = []
    if tile.system_prompt.strip():
        msgs.append({'role': 'system', 'content': tile.system_prompt.strip()})
    msgs.extend(messages)

    payload = {'model': tile.model, 'messages': msgs, 'stream': True}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        async with client.stream('POST', f'{OLLAMA_BASE_URL}/api/chat', json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    if token := data.get('message', {}).get('content'):
                        yield token
