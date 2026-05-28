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

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 8

    # Threshold de variação que exige justificativa (%)
    variacao_threshold_pct: float = 10.0

    # Email / SMTP
    email_enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "fpa@philozon.com.br"
    # Lista de aprovadores: e-mails separados por vírgula
    email_aprovadores: str = ""
    # E-mail que recebe notificação de aprovação/reprovação
    email_notificacao_workflow: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
