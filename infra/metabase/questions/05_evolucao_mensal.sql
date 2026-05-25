-- Evolução Mensal de Receitas e Despesas (Área/Linha)
-- Fonte: dw.v_evolucao_mensal
-- Visualização: Area chart — X: ano+mes, séries por conta_tipo
-- Útil para visão histórica sem filtro de versão (usa dados reais do ETL)

SELECT
    ano,
    mes,
    nome_mes,
    CONCAT(ano, '-', LPAD(mes::text, 2, '0')) AS ano_mes,
    empresa,
    conta_tipo,
    valor_realizado,
    qtd_lancamentos
FROM dw.v_evolucao_mensal
WHERE empresa = {{empresa}}
  [[ AND ano  = {{ano}} ]]
ORDER BY ano, mes, conta_tipo
