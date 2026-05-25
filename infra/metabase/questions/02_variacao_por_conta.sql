-- Variação % por Conta Gerencial (Barras Horizontais)
-- Fonte: dw.v_dre_anual
-- Visualização: Bar chart horizontal, ordenado por |variacao_percentual| DESC

SELECT
    codigo,
    nome,
    tipo,
    valor_orcado,
    valor_realizado,
    variacao_percentual
FROM dw.v_dre_anual
WHERE versao_ano        = {{ano}}
  AND versao_nome       = {{versao}}
  AND empresa_nome      = {{empresa}}
  AND variacao_percentual IS NOT NULL
  AND ABS(variacao_percentual) > 0
ORDER BY ABS(variacao_percentual) DESC
LIMIT 20
