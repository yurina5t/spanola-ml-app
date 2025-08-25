from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- Database (всегда валидные дефолты) ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "spanola"

    APP_NAME: str = "Spanola App"
    APP_DESCRIPTION: str = "API for managing Spanola data"
    API_VERSION: str = "1.0"
    DEBUG: bool = True

    USE_ASYNC: bool = False  # True → asyncpg, False → psycopg
    TESTING: bool = False    # форсим SQLite в тестах

    # --- JWT / Security ---
    SECRET_KEY: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # --- MQ ---
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    @property
    def DATABASE_URL(self) -> str:
        if self.TESTING:
            # заглушка; реальный engine выберем в database.py
            return "sqlite://"
        if self.USE_ASYNC:
            return (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return (
            f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    # Мягкая «валидация»: не падаем, а возвращаем список полей, взятых из дефолтов
    def defaults_used(self) -> list[str]:
        provided = getattr(self, "__pydantic_fields_set__", set())
        return [name for name in self.model_fields.keys() if name not in provided]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
