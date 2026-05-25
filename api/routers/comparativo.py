"""
Endpoint de comparativo Realizado × Orçado.
Junta fato_orcamento com fato_lancamento_realizado via contas e centros gerenciais.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from api.db import get_db
from api.schemas.comparativo import ComparativoItem, ComparativoResponse

router = APIRouter(prefix="/comparativo", tags=["Comparativo Realizado × Orçado"])


@router.get("/{ano}/{id_versao}", response_model=ComparativoResponse)
def comparativo(
    ano: int,
    id_versao: int,
    id_empresa: int | None = None,
    id_centro_custo: int | None = None,
    db: Session = Depends(get_db),
):
    # Query SQL direto para performance — resultado agregado por mes/conta/CC
    sql = text("""
        SELECT
            fo.mes,
            cg.codigo   AS conta_gerencial_codigo,
            cg.nome     AS conta_gerencial_nome,
            cc.codigo   AS centro_custo_codigo,
            cc.nome     AS centro_custo_nome,
            COALESCE(fo.valor, 0)              AS valor_orcado,
            COALESCE(SUM(lr.valor * CASE WHEN lr.tipo_lancamento = 'D' THEN 1 ELSE -1 END), 0) AS valor_realizado
        FROM dw.fato_orcamento fo
        JOIN dw.dim_conta_gerencial cg ON cg.id = fo.id_conta_gerencial
        JOIN dw.dim_centro_custo    cc ON cc.id = fo.id_centro_custo
        LEFT JOIN dw.fato_lancamento_realizado lr
               ON lr.id_conta_gerencial = fo.id_conta_gerencial
              AND lr.id_centro_custo    = fo.id_centro_custo
              AND lr.id_empresa         = fo.id_empresa
              AND EXTRACT(YEAR FROM lr.data_referencia)  = fo.ano
              AND EXTRACT(MONTH FROM lr.data_referencia) = fo.mes
        WHERE fo.ano       = :ano
          AND fo.id_versao = :id_versao
          AND (:id_empresa IS NULL OR fo.id_empresa = :id_empresa)
          AND (:id_centro_custo IS NULL OR fo.id_centro_custo = :id_centro_custo)
        GROUP BY fo.mes, cg.codigo, cg.nome, cc.codigo, cc.nome, fo.valor
        ORDER BY fo.mes, cg.codigo
    """)

    rows = db.execute(sql, {
        "ano": ano,
        "id_versao": id_versao,
        "id_empresa": id_empresa,
        "id_centro_custo": id_centro_custo,
    }).mappings().all()

    nome_versao = db.execute(
        text("SELECT nome FROM dw.dim_versao_orcamento WHERE id = :id"), {"id": id_versao}
    ).scalar()
    if nome_versao is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")

    itens = [ComparativoItem(**dict(row)) for row in rows]
    total_orcado = sum(i.valor_orcado for i in itens) or Decimal("0")
    total_realizado = sum(i.valor_realizado for i in itens) or Decimal("0")
    var_abs = total_realizado - total_orcado
    var_pct = (var_abs / abs(total_orcado) * 100).quantize(Decimal("0.01")) if total_orcado else Decimal("0")

    return ComparativoResponse(
        ano=ano,
        id_versao=id_versao,
        nome_versao=nome_versao,
        itens=itens,
        total_orcado=total_orcado,
        total_realizado=total_realizado,
        variacao_absoluta_total=var_abs,
        variacao_percentual_total=var_pct,
    )
