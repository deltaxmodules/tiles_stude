import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import DEFAULT_CACHE_SIMILARITY_THRESHOLD, DEFAULT_TILE_NAME, DEFAULT_TILE_TTL_SECONDS
from app.domain.schemas import ChatRequest
from app.infra.cache_layer import get_cached, set_cache
from app.services.router import route
from app.services.scheduler import scheduler
from app.services.streaming import composite_stream
from app.services.tile_loader import TILES, get_tile
from logger import log

router = APIRouter()


@router.post('/v1/chat/completions')
async def chat(req: ChatRequest):
    query = req.messages[-1].content

    t0 = time.perf_counter()
    route_name, model = route(query)
    routing_ms = (time.perf_counter() - t0) * 1000

    if route_name:
        scheduler.record_route(route_name)

    tile_name = route_name or DEFAULT_TILE_NAME
    tile = get_tile(route_name) if route_name else get_tile(DEFAULT_TILE_NAME)
    ttl = tile.ttl_seconds if tile else DEFAULT_TILE_TTL_SECONDS
    sim_threshold = tile.similarity_threshold if tile else DEFAULT_CACHE_SIMILARITY_THRESHOLD

    t1 = time.perf_counter()
    cached = get_cached(query, tile_name, sim_threshold)
    cache_ms = (time.perf_counter() - t1) * 1000

    if cached:
        log.info('request', route=route_name, model=model, cache='hit', routing_ms=round(routing_ms, 2), cache_ms=round(cache_ms, 2), tile_ttl=ttl)
        response = {'choices': [{'message': {'role': 'assistant', 'content': cached}}]}
        if req.include_trace:
            response['trace'] = {
                'route': route_name,
                'tile': tile_name,
                'model': model,
                'cache': 'hit',
                'warm': scheduler.is_warm(tile_name),
                'metrics_ms': {
                    'routing': round(routing_ms, 2),
                    'cache': round(cache_ms, 2),
                    'generation': 0.0,
                },
            }
        return response

    msgs = [m.model_dump() for m in req.messages]
    is_warm = scheduler.is_warm(tile_name)

    async def event_stream():
        full = []
        async for token in composite_stream(tile, msgs, is_warm):
            full.append(token)
            yield f'data: {token}\n\n'
        response_text = ''.join(full)
        set_cache(query, response_text, tile_name, ttl)
        log.info('request', route=route_name, model=model, cache='miss', routing_ms=round(routing_ms, 2), cache_ms=round(cache_ms, 2), warm=is_warm, tile_ttl=ttl)

    if req.stream:
        return StreamingResponse(event_stream(), media_type='text/event-stream')

    t2 = time.perf_counter()
    full_tokens = []
    async for token in composite_stream(tile, msgs, is_warm):
        full_tokens.append(token)
    response_text = ''.join(full_tokens)
    gen_ms = (time.perf_counter() - t2) * 1000
    set_cache(query, response_text, tile_name, ttl)

    log.info('request', route=route_name, model=model, cache='miss', routing_ms=round(routing_ms, 2), cache_ms=round(cache_ms, 2), gen_ms=round(gen_ms, 2), warm=is_warm, tile_ttl=ttl)

    response = {'choices': [{'message': {'role': 'assistant', 'content': response_text}}]}
    if req.include_trace:
        response['trace'] = {
            'route': route_name,
            'tile': tile_name,
            'model': model,
            'cache': 'miss',
            'warm': is_warm,
            'metrics_ms': {
                'routing': round(routing_ms, 2),
                'cache': round(cache_ms, 2),
                'generation': round(gen_ms, 2),
            },
        }
    return response


@router.get('/health')
def health():
    return {'status': 'ok', 'tiles': list(TILES.keys())}


@router.get('/tiles')
def list_tiles():
    return [{'name': t.name, 'model': t.model, 'ttl': t.ttl_seconds, 'warm': scheduler.is_warm(t.name)} for t in TILES.values()]
