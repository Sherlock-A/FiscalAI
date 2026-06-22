from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "FiscalAI"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql://fiscalai:fiscalai_dev_secret@localhost:5432/fiscalai"

    # Redis / Celery
    redis_url: str = "redis://:redis_dev_secret@localhost:6379/0"
    celery_broker_url: str = ""  # defaults to redis_url if empty
    celery_result_backend: str = ""  # defaults to redis_url if empty

    # Security
    secret_key: str = "dev_secret_change_in_prod_32chars!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS origins (comma-separated in env)
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # External APIs
    osm_overpass_url: str = "https://overpass-api.de/api/interpreter"
    copernicus_user: str = ""
    copernicus_password: str = ""

    # PDF generation
    pdf_template_dir: str = "/app/app/templates"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def model_post_init(self, __context):
        if not self.celery_broker_url:
            object.__setattr__(self, "celery_broker_url", self.redis_url)
        if not self.celery_result_backend:
            object.__setattr__(self, "celery_result_backend", self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
