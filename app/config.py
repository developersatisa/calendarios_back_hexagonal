from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    ADMIN_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FILE_STORAGE_ROOT: str
    CLIENT_ID: Optional[str] = None
    CLIENT_SECRET: Optional[str] = None
    TENANT_ID: Optional[str] = None
    REDIRECT_URI: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
