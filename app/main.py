from fastapi import FastAPI

from app.api.routes import router
from app.infra.cache_layer import init_cache

app = FastAPI(title='Cognitive Streaming — Fase 2')
init_cache()
app.include_router(router)
