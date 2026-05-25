-- Variação Absoluta por Mês (Barras)
-- Fonte: dw.v_comparativo_mensal
-- Visualização: Bar chart — barras verdes (>0) e vermelhas (<0)

SELECT
    mes,
    nome_mes,
    SUM(valor_orcado)                             AS total_orcado,
    SUM(valor_realizado)                          AS total_realizado,
    SUM(variacao_absoluta)                        AS variacao_absoluta,
    CASE
        WHEN SUM(valor_orcado) = 0 THEN NULL
        ELSE ROUND(
            (SUM(variacao_absoluta) / ABS(SUM(valor_orcado)) * 100)::numeric,
            2
        )
    END                                           AS variacao_percentual_consolidada
FROM dw.v_comparativo_mensal
WHERE ano          = {{ano}}
  AND versao_nome  = {{versao}}
  AND empresa_nome = {{empresa}}
GROUP BY mes, nome_mes
ORDER BY mes
