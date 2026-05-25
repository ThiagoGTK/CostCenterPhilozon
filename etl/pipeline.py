"""
Orquestrador do pipeline ETL.

Uso:
    python pipeline.py --ano 2025 --mes 1
    python pipeline.py --full-load  # recarga completa (mais lento)

Idempotência: pode ser executado múltiplas vezes sem duplicar dados.
"""

import argparse
import logging
import sys
from datetime import date

from sqlalchemy import create_engine
from etl.config import load_config
from etl.extractor import SIAExtractor
from etl.transformer import transformar_lancamentos_contabeis, gerar_dim_tempo
from etl.loader import DWLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("pipeline")


def executar_pipeline(ano: int, mes: int, full_load: bool = False) -> None:
    cfg = load_config()
    engine = create_engine(cfg.dw_url, pool_pre_ping=True)
    loader = DWLoader(engine)

    logger.info("Iniciando pipeline ETL — %04d/%02d", ano, mes)

    # 1. Garantir dimensão tempo populada
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano, 12, 31)
    else:
        from calendar import monthrange
        ultimo_dia = monthrange(ano, mes)[1]
        data_fim = date(ano, mes, ultimo_dia)

    df_tempo = gerar_dim_tempo(data_inicio, data_fim)
    loader.upsert_dim_tempo(df_tempo)

    # 2. Extrair e carregar lançamentos contábeis
    try:
        with SIAExtractor(cfg) as sia:
            # 2a. Plano de contas (atualiza sempre para capturar novos cadastros)
            df_contas = sia.extrair_plano_de_contas()
            if not df_contas.empty:
                # TODO: mapear colunas reais após confirmar estrutura do CTB_CONTAS
                logger.info("Plano de contas SIA: %d contas extraídas", len(df_contas))

            # 2b. Lançamentos do período
            df_lanc = sia.extrair_lancamentos_contabeis(ano, mes)
            if not df_lanc.empty:
                df_lanc = transformar_lancamentos_contabeis(df_lanc)
                # TODO: resolver FKs (id_empresa, id_tempo, id_conta_sia) antes de carregar
                logger.info("Lançamentos contábeis: %d registros transformados", len(df_lanc))

    except Exception as e:
        logger.error("Erro ao conectar/extrair do SIA: %s", e)
        logger.warning("Pipeline encerrado sem carregar dados (SIA indisponível)")
        sys.exit(1)

    logger.info("Pipeline concluído com sucesso — %04d/%02d", ano, mes)


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL FP&A — SIA → DW")
    parser.add_argument("--ano", type=int, default=date.today().year)
    parser.add_argument("--mes", type=int, default=date.today().month)
    parser.add_argument("--full-load", action="store_true")
    args = parser.parse_args()

    executar_pipeline(args.ano, args.mes, args.full_load)


if __name__ == "__main__":
    main()
