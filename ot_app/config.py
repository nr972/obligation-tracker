"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///data/obligations.db"
    ANTHROPIC_API_KEY: str = ""
    UPLOAD_DIR: str = "data/uploads"
    MAX_FILE_SIZE_MB: int = 50
    CORS_ORIGINS: list[str] = ["http://localhost:8501"]
    DEMO_MODE: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
