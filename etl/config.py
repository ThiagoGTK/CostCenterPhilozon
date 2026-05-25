"""
Configuração do ETL — lida via variáveis de ambiente.
Nunca commitar senhas ou connection strings reais.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ETLConfig:
    # Data Warehouse (PostgreSQL)
    dw_url: str

    # SIA — SOMENTE LEITURA
    sia_host: str
    sia_port: int
    sia_database: str
    sia_user: str
    sia_password: str
    sia_codemp: int

    # ETL
    batch_size: int
    log_level: str


def load_config() -> ETLConfig:
    return ETLConfig(
        dw_url=os.environ["DATABASE_URL"],
        sia_host=os.environ["SIA_HOST"],
        sia_port=int(os.getenv("SIA_PORT", "3050")),
        sia_database=os.environ["SIA_DATABASE"],
        sia_user=os.environ["SIA_USER"],
        sia_password=os.environ["SIA_PASSWORD"],
        sia_codemp=int(os.environ["SIA_CODEMP"]),
        batch_size=int(os.getenv("ETL_BATCH_SIZE", "1000")),
        log_level=os.getenv("ETL_LOG_LEVEL", "INFO"),
    )
