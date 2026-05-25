-- Realizado × Orçado por Mês (Linha Dupla)
-- Fonte: dw.v_comparativo_mensal
-- Visualização: Line chart — X: mes, Y: valor_orcado + valor_realizado (duas séries)

SELECT
    mes,
    nome_mes,
    SUM(valor_orcado)    AS total_orcado,
    SUM(valor_realizado) AS total_realizado
FROM dw.v_comparativo_mensal
WHERE ano          = {{ano}}
  AND versao_nome  = {{versao}}
  AND empresa_nome = {{empresa}}
  [[ AND conta_tipo = {{conta_tipo}} ]]   -- filtro opcional: RECEITA / DESPESA
  [[ AND cc_nome    = {{cc}} ]]           -- filtro opcional: centro de custo
GROUP BY mes, nome_mes
ORDER BY mes
