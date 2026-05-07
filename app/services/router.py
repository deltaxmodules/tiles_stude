from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

from app.config import DEFAULT_TILE_NAME, EMBEDDING_MODEL_NAME
from app.services.tile_loader import get_tile


_route_code = Route(
    name='code',
    utterances=[
        'write a python function', 'fix this bug', 'how do I implement',
        'what does this code do', 'refactor this', 'write a class',
        'debug my script', 'syntax error', 'write unit tests',
    ],
)
_route_reason = Route(
    name='reasoning',
    utterances=[
        'explain why', 'what are the pros and cons', 'analyse this situation',
        'compare these options', 'what is the best approach', 'think step by step',
        'evaluate the trade-offs', 'what would happen if',
    ],
)
_route_general = Route(
    name='general',
    utterances=[
        'what is', 'tell me about', 'summarise', 'translate',
        'what year was', 'who is', 'give me a recipe', 'write a poem',
    ],
)

_layer: SemanticRouter | None = None


def _get_layer() -> SemanticRouter:
    global _layer
    if _layer is None:
        encoder = HuggingFaceEncoder(name=EMBEDDING_MODEL_NAME)
        layer = SemanticRouter(encoder=encoder)
        layer.add([_route_code, _route_reason, _route_general])
        _layer = layer
    return _layer


def route(query: str) -> tuple[str | None, str]:
    result = _get_layer()(query)
    name = result.name if result else None
    resolved_name = name or DEFAULT_TILE_NAME
    tile = get_tile(resolved_name)
    model = tile.model if tile else ''
    return name, model
