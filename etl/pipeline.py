"""
Orquestrador do pipeline ETL.

Fluxo por execução:
  1. dim_tempo        — garante datas do período no DW
  2. dim_empresa      — espelho de GER_EMPRESAS (atualiza cadastro)
  3. dim_conta_sia    — espelho de CTB_CONTAS planos 1 e 2 (atualiza cadastro)
  4. fato_lancamento_realizado — CTB_MOVIMENTOS do período, com FK resolution

Idempotência: pode ser executado múltiplas vezes sem duplicar dados.
Ordem importa: dim_* devem existir antes da fato (FKs).

Uso:
    python pipeline.py --ano 2025 --mes 1
    python pipeline.py --ano 2025 --mes 1 --codemp 2   # forçar empresa específica
"""

import argparse
import logging
import sys
from calendar import monthrange
from datetime import date

import pandas as pd
from sqlalchemy import create_engine

from etl.config import load_config
from etl.extractor import SIAExtractor
from etl.loader import DWLoader
from etl.transformer import (
    gerar_dim_tempo,
    transformar_empresas,
    transformar_lancamentos_contabeis,
    transformar_plano_contas,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("pipeline")


def _periodo(ano: int, mes: int) -> tuple[date, date]:
    """Retorna (primeiro_dia, ultimo_dia) do mês."""
    ultimo_dia = monthrange(ano, mes)[1]
    return date(ano, mes, 1), date(ano, mes, ultimo_dia)


def _resolver_fks_lancamentos(
    df: pd.DataFrame,
    loader: DWLoader,
    id_empresa_dw: int,
) -> pd.DataFrame:
    """
    Adiciona todas as FKs necessárias ao DataFrame de lançamentos:
    - id_empresa, id_tempo, id_conta_sia (obrigatórias — descarta linha se falhar)
    - id_conta_gerencial, id_centro_custo (opcionais — NULL enquanto não mapeado)

    id_empresa_dw: ID na dim_empresa (DW) da empresa sendo processada,
                   usado para buscar mapeamentos gerenciais.
    """
    codemp_list = df["codemp"].unique().tolist()
    datas_list  = df["data_referencia"].unique().tolist()
    contas_list = df["conta_sia_codigo"].astype(str).unique().tolist()

    emp_map     = loader.resolver_ids_empresa(codemp_list)
    tempo_map   = loader.resolver_ids_tempo(datas_list)
    conta_map   = loader.resolver_ids_conta_sia(contas_list)

    # Mapeamentos gerenciais (opcionais — podem não estar cadastrados ainda)
    conta_ger_map = loader.resolver_mapeamentos_conta(id_empresa_dw)
    cc_map        = loader.resolver_mapeamentos_cc(id_empresa_dw)

    df = df.copy()
    df["id_empresa"]   = df["codemp"].map(emp_map)
    df["id_tempo"]     = df["data_referencia"].astype(str).map(tempo_map)
    df["id_conta_sia"] = df["conta_sia_codigo"].astype(str).map(conta_map)

    # Gerenciais — opcionais
    df["id_conta_gerencial"] = df["conta_sia_codigo"].astype(str).map(conta_ger_map)
    df["id_centro_custo"]    = df["cc_sia_codigo"].map(cc_map)

    # Converter None/NaN para None explícito (SQL NULL)
    df["id_conta_gerencial"] = df["id_conta_gerencial"].where(
        df["id_conta_gerencial"].notna(), other=None
    )
    df["id_centro_custo"] = df["id_centro_custo"].where(
        df["id_centro_custo"].notna(), other=None
    )

    # Descartar linhas com FK obrigatória não resolvida
    antes = len(df)
    df = df.dropna(subset=["id_empresa", "id_tempo", "id_conta_sia"])
    descartados = antes - len(df)
    if descartados:
        logger.warning(
            "%d lançamentos descartados: FK não resolvida "
            "(empresa, data ou conta ausente no DW). "
            "Verifique se as dimensões foram carregadas.",
            descartados,
        )

    for col in ("id_empresa", "id_tempo", "id_conta_sia"):
        df[col] = df[col].astype(int)

    # Converter gerenciais para int onde não-nulo
    for col in ("id_conta_gerencial", "id_centro_custo"):
        df[col] = df[col].apply(lambda v: int(v) if v is not None and not pd.isna(v) else None)

    mapeados = df["id_conta_gerencial"].notna().sum()
    logger.info(
        "Mapeamento gerencial: %d/%d lançamentos com conta gerencial resolvida",
        mapeados, len(df),
    )

    return df


def executar_pipeline(ano: int, mes: int, codemp: int | None = None) -> None:
    cfg = load_config()

    # Permite sobrescrever empresa via argumento (útil para multiempresa)
    if codemp is not None:
        # Recria config com codemp forçado
        from dataclasses import replace
        cfg = replace(cfg, sia_codemp=codemp)

    engine = create_engine(cfg.dw_url, pool_pre_ping=True)
    loader = DWLoader(engine)

    logger.info("=== Pipeline ETL iniciado — %04d/%02d (empresa %d) ===", ano, mes, cfg.sia_codemp)

    # ── 1. Dimensão tempo ──────────────────────────────────────────────────
    data_inicio, data_fim = _periodo(ano, mes)
    df_tempo = gerar_dim_tempo(data_inicio, data_fim)
    loader.upsert_dim_tempo(df_tempo)
    logger.info("Passo 1/4 — dim_tempo OK (%d dias)", len(df_tempo))

    # ── 2–4. Extração do SIA ───────────────────────────────────────────────
    try:
        with SIAExtractor(cfg) as sia:

            # 2. dim_empresa — atualiza cadastro de empresas ativas
            df_emp = sia.extrair_empresas()
            recs_emp = transformar_empresas(df_emp)
            loader.upsert_dim_empresa(recs_emp)
            logger.info("Passo 2/4 — dim_empresa OK (%d empresas)", len(recs_emp))

            # 3. dim_conta_sia — plano de contas Philozon (planos 1 e 2)
            df_contas = sia.extrair_plano_de_contas()
            recs_contas = transformar_plano_contas(df_contas)
            loader.upsert_dim_conta_sia(recs_contas)
            logger.info("Passo 3/4 — dim_conta_sia OK (%d contas)", len(recs_contas))

            # 4. fato_lancamento_realizado
            df_lanc = sia.extrair_lancamentos_contabeis(ano, mes)
            if df_lanc.empty:
                logger.info("Passo 4/4 — sem lançamentos em %04d/%02d para empresa %d",
                            ano, mes, cfg.sia_codemp)
                return

            df_lanc = transformar_lancamentos_contabeis(df_lanc)

            # Resolve id da empresa no DW para buscar mapeamentos gerenciais
            emp_map = loader.resolver_ids_empresa([cfg.sia_codemp])
            id_empresa_dw = emp_map.get(cfg.sia_codemp)
            if id_empresa_dw is None:
                logger.error("Empresa CODEMP=%d não encontrada no DW. Abortar.", cfg.sia_codemp)
                sys.exit(1)

            df_lanc = _resolver_fks_lancamentos(df_lanc, loader, id_empresa_dw)

            if df_lanc.empty:
                logger.warning("Passo 4/4 — todos os lançamentos descartados por FK não resolvida")
                return

            colunas_fato = [
                "id_empresa", "id_tempo", "id_conta_sia",
                "id_conta_gerencial", "id_centro_custo",
                "sia_lancamento_id", "valor", "tipo_lancamento",
                "historico", "data_referencia",
            ]
            records_fato = df_lanc[colunas_fato].to_dict("records")
            n = loader.upsert_fato_lancamento_realizado(records_fato)
            logger.info("Passo 4/4 — fato_lancamento_realizado OK (%d registros)", n)

    except Exception as exc:
        logger.error("Erro ao conectar/extrair do SIA: %s", exc, exc_info=True)
        logger.warning("Pipeline encerrado sem carregar dados (SIA indisponível)")
        sys.exit(1)

    logger.info("=== Pipeline ETL concluído — %04d/%02d ===", ano, mes)


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL FP&A — SIA → DW PostgreSQL")
    parser.add_argument("--ano",    type=int, default=date.today().year,  help="Ano de referência")
    parser.add_argument("--mes",    type=int, default=date.today().month, help="Mês de referência (1-12)")
    parser.add_argument("--codemp", type=int, default=None,               help="Forçar empresa (sobrescreve .env)")
    args = parser.parse_args()

    if not (1 <= args.mes <= 12):
        parser.error("--mes deve ser entre 1 e 12")

    executar_pipeline(args.ano, args.mes, args.codemp)


if __name__ == "__main__":
    main()
