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
    # Lançamentos do SIA não têm centro de custo (MOV_CECT = NULL para todas as empresas),
    # portanto id_centro_custo em fato_lancamento_realizado é sempre NULL.
    # A estratégia correta é:
    #   1. Pre-agregar realizado por (conta, empresa, ano, mes) ignorando CC.
    #   2. Agregar orcado somando todos os CCs por (conta, empresa, mes).
    #   3. LEFT JOIN pelos campos comuns (conta + empresa + período).
    # O filtro por CC aplica-se apenas ao orcado (WHERE fo.id_centro_custo).
    # Lançamentos do SIA não têm centro de custo (MOV_CECT = NULL para todas as empresas),
    # portanto id_centro_custo em fato_lancamento_realizado é sempre NULL.
    #
    # A estratégia correta:
    #   1. realizado_agg agrega por (conta, ano, mes) SEM empresa e SEM CC.
    #      O filtro :id_empresa é aplicado aqui para que, quando informado,
    #      apenas o realizado da empresa selecionada entre na soma.
    #      Quando NULL, cobre todas as empresas → visão consolidada consistente.
    #   2. fato_orcamento é filtrado pelo mesmo :id_empresa no WHERE externo.
    #      SUM(fo.valor) soma todos os CCs da empresa para cada conta-mes.
    #   3. O JOIN usa somente conta+período (sem empresa), de modo que há
    #      exatamente uma linha em realizado_agg para cada (conta, mes),
    #      eliminando o risco de MAX subesticar o realizado multi-empresa.
    sql = text("""
        WITH realizado_agg AS (
            SELECT
                id_conta_gerencial,
                EXTRACT(YEAR  FROM data_referencia)::int AS ano,
                EXTRACT(MONTH FROM data_referencia)::int AS mes,
                SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END)
                    AS valor_realizado
            FROM dw.fato_lancamento_realizado
            WHERE id_conta_gerencial IS NOT NULL
              AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
            GROUP BY id_conta_gerencial,
                     EXTRACT(YEAR  FROM data_referencia),
                     EXTRACT(MONTH FROM data_referencia)
        )
        SELECT
            fo.mes,
            cg.codigo                           AS conta_gerencial_codigo,
            cg.nome                             AS conta_gerencial_nome,
            NULL::varchar                        AS centro_custo_codigo,
            NULL::varchar                        AS centro_custo_nome,
            SUM(fo.valor)                       AS valor_orcado,
            COALESCE(MAX(r.valor_realizado), 0) AS valor_realizado
        FROM dw.fato_orcamento fo
        JOIN dw.dim_conta_gerencial cg ON cg.id = fo.id_conta_gerencial
        LEFT JOIN realizado_agg r
               ON  r.id_conta_gerencial = fo.id_conta_gerencial
              AND  r.ano                = fo.ano
              AND  r.mes                = fo.mes
        WHERE fo.ano       = :ano
          AND fo.id_versao = :id_versao
          AND (:id_empresa     IS NULL OR fo.id_empresa     = :id_empresa)
          AND (:id_centro_custo IS NULL OR fo.id_centro_custo = :id_centro_custo)
        GROUP BY fo.mes, cg.codigo, cg.nome
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
