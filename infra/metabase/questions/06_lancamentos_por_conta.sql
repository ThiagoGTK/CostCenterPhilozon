-- Top Contas por Valor Lançado (Barras + Tabela Detalhada)
-- Fonte: dw.v_lancamentos_detalhado
-- Visualização: Bar chart (top 15) ou Table com paginação

SELECT
    conta_gerencial_codigo                        AS codigo,
    conta_gerencial_nome                          AS conta,
    conta_tipo,
    cc_nome                                       AS centro_custo,
    empresa,
    SUM(valor_liquido)                            AS valor_total,
    COUNT(*)                                      AS qtd_lancamentos,
    MIN(data_referencia)                          AS primeiro_lancamento,
    MAX(data_referencia)                          AS ultimo_lancamento
FROM dw.v_lancamentos_detalhado
WHERE id_conta_gerencial IS NOT NULL
  AND ano = {{ano}}
  [[ AND mes     = {{mes}} ]]
  [[ AND empresa = {{empresa}} ]]
  [[ AND conta_tipo = {{conta_tipo}} ]]
GROUP BY conta_gerencial_codigo, conta_gerencial_nome,
         conta_tipo, cc_nome, empresa
ORDER BY ABS(SUM(valor_liquido)) DESC
LIMIT 20
