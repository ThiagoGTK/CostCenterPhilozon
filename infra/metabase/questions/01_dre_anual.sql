-- DRE Gerencial Anual
-- Fonte: dw.v_dre_anual
-- Filtros sugeridos: versao_nome, versao_ano, empresa_nome
-- Visualização: Table com agrupamento por tipo e código de conta

SELECT
    nivel,
    codigo,
    nome,
    tipo,
    natureza,
    codigo_pai,
    nome_pai,
    versao_nome,
    versao_ano     AS ano,
    empresa_nome,
    valor_orcado,
    valor_realizado,
    variacao_absoluta,
    variacao_percentual
FROM dw.v_dre_anual
WHERE versao_ano     = {{ano}}              -- parâmetro: Number, default = YEAR(NOW())
  AND versao_nome    = {{versao}}           -- parâmetro: Text
  AND empresa_nome   = {{empresa}}          -- parâmetro: Text
ORDER BY codigo
