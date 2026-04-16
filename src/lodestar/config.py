"""Application configuration via environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global settings for the financial coach PoC.

    All values can be overridden via environment variables
    prefixed with ``COACH_``.
    """

    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen3:14b"
    llm_api_key: str = "not-needed"
    db_path: str = "data/coach.db"
    embedding_model: str = "BAAI/bge-m3"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    background_poll_interval: int = 30

    model_config = {"env_prefix": "COACH_"}

    def ensure_dirs(self) -> None:
        """Create data directories if they do not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
