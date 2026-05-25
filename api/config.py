from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "dev-secret-change-in-production"

    database_url: str = "postgresql+psycopg2://fpa_user:dev_password@localhost:5432/financeiro_dw"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Threshold de variação que exige justificativa (%)
    variacao_threshold_pct: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
