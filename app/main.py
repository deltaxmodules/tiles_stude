from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.infra.cache_layer import init_cache

app = FastAPI(title='Cognitive Streaming — Fase 2')
init_cache()
app.include_router(router)
app.mount('/static', StaticFiles(directory=Path(__file__).parent / 'web' / 'static'), name='static')


@app.get('/')
def homepage():
    ui_path = Path(__file__).parent / 'web' / 'index.html'
    return FileResponse(ui_path)
