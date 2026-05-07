from urllib.parse import urlsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    ollama_base_url: str | None = Field(default=None, alias='OLLAMA_BASE_URL')
    ollama_host: str = Field(default='127.0.0.1', alias='OLLAMA_HOST')
    ollama_port: int = Field(default=11434, alias='OLLAMA_PORT')

    http_timeout_seconds: int = Field(default=120, alias='HTTP_TIMEOUT_SECONDS')
    prewarm_http_timeout_seconds: int = Field(default=30, alias='PREWARM_HTTP_TIMEOUT_SECONDS')
    history_size: int = Field(default=10, alias='HISTORY_SIZE')

    app_host: str = Field(default='0.0.0.0', alias='APP_HOST')
    app_port: int = Field(default=8000, alias='APP_PORT')

    default_tile_name: str = Field(default='general', alias='DEFAULT_TILE_NAME')
    default_tile_ttl_seconds: int = Field(default=3600, alias='DEFAULT_TILE_TTL_SECONDS')
    default_cache_similarity_threshold: float = Field(default=0.85, alias='DEFAULT_CACHE_SIMILARITY_THRESHOLD')
    embedding_model_name: str = Field(default='BAAI/bge-small-en-v1.5', alias='EMBEDDING_MODEL_NAME')

    @property
    def resolved_ollama_base_url(self) -> str:
        if self.ollama_base_url:
            return self.ollama_base_url.rstrip('/')

        host_value = self.ollama_host.strip().rstrip('/')
        if host_value.startswith('http://') or host_value.startswith('https://'):
            parsed = urlsplit(host_value)
            if parsed.port is not None:
                return host_value
            return f"{parsed.scheme}://{parsed.hostname}:{self.ollama_port}"

        return f"http://{host_value}:{self.ollama_port}"


settings = Settings()

# Backward-compatible constant exports
OLLAMA_HOST = settings.ollama_host
OLLAMA_PORT = settings.ollama_port
OLLAMA_BASE_URL = settings.resolved_ollama_base_url
HTTP_TIMEOUT_SECONDS = settings.http_timeout_seconds
PREWARM_HTTP_TIMEOUT_SECONDS = settings.prewarm_http_timeout_seconds
HISTORY_SIZE = settings.history_size
APP_HOST = settings.app_host
APP_PORT = settings.app_port
DEFAULT_TILE_NAME = settings.default_tile_name
DEFAULT_TILE_TTL_SECONDS = settings.default_tile_ttl_seconds
DEFAULT_CACHE_SIMILARITY_THRESHOLD = settings.default_cache_similarity_threshold
EMBEDDING_MODEL_NAME = settings.embedding_model_name
