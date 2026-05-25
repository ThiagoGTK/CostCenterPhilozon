"""
DRE Gerencial — estrutura hierárquica de contas com realizado e orçado.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.db import get_db

router = APIRouter(prefix="/dre", tags=["DRE Gerencial"])


@router.get("/{ano}/{id_versao}")
def dre(ano: int, id_versao: int, id_empresa: int | None = None, db: Session = Depends(get_db)):
    """
    Retorna DRE hierárquico: receitas, deduções, despesas, EBITDA.
    Agrupado por conta gerencial de nível 1 (cabeçalho) e detalhado por sub-contas.
    """
    sql = text("""
        WITH orcado AS (
            SELECT id_conta_gerencial, SUM(valor) AS total
            FROM dw.fato_orcamento
            WHERE ano = :ano AND id_versao = :id_versao
              AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
            GROUP BY id_conta_gerencial
        ),
        realizado AS (
            SELECT id_conta_gerencial,
                   SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END) AS total
            FROM dw.fato_lancamento_realizado
            WHERE EXTRACT(YEAR FROM data_referencia) = :ano
              AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
              AND id_conta_gerencial IS NOT NULL
            GROUP BY id_conta_gerencial
        )
        SELECT
            cg.id,
            cg.codigo,
            cg.nome,
            cg.tipo,
            cg.natureza,
            cg.nivel,
            cg.id_pai,
            COALESCE(o.total, 0) AS valor_orcado,
            COALESCE(r.total, 0) AS valor_realizado
        FROM dw.dim_conta_gerencial cg
        LEFT JOIN orcado  o ON o.id_conta_gerencial = cg.id
        LEFT JOIN realizado r ON r.id_conta_gerencial = cg.id
        WHERE cg.ativa = true
        ORDER BY cg.codigo
    """)

    rows = db.execute(sql, {
        "ano": ano,
        "id_versao": id_versao,
        "id_empresa": id_empresa,
    }).mappings().all()

    return {"ano": ano, "id_versao": id_versao, "linhas": [dict(r) for r in rows]}
