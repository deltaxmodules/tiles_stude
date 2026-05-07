import json
from typing import AsyncIterator

import httpx

from app.config import HTTP_TIMEOUT_SECONDS, OLLAMA_BASE_URL


async def generate_stream(model: str, messages: list[dict]) -> AsyncIterator[str]:
    payload = {'model': model, 'messages': messages, 'stream': True}
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        async with client.stream('POST', f'{OLLAMA_BASE_URL}/api/chat', json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    if token := data.get('message', {}).get('content'):
                        yield token


async def generate(model: str, messages: list[dict]) -> str:
    result = []
    async for token in generate_stream(model, messages):
        result.append(token)
    return ''.join(result)
