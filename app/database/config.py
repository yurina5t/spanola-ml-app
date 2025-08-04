from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DB_HOST: Optional[str] = "localhost"
    DB_PORT: Optional[int] = 5432
    DB_USER: Optional[str] = "postgres"
    DB_PASS: Optional[str] = "postgres"
    DB_NAME: Optional[str] = "spanola"
    
    # Application settings
    APP_NAME: Optional[str] = "My App"
    DEBUG: bool = True
    API_VERSION: Optional[str] = "1.0"
    
    @property
    def DATABASE_URL_asyncpg(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    @property
    def DATABASE_URL_psycopg(self):
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    def validate(self) -> None:
        required = {
            "DB_HOST": self.DB_HOST,
            "DB_USER": self.DB_USER,
            "DB_PASS": self.DB_PASS,
            "DB_NAME": self.DB_NAME,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Отсутствуют обязательные параметры конфигурации БД: {', '.join(missing)}")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
