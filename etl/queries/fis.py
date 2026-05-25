"""
Queries do módulo FIS (Fiscal / Faturamento) do SIA.
TODO: Validar nomes de colunas contra dicionário de dados real.
"""

# Receita bruta via documentos fiscais de saída
SQL_RECEITAS = """
    SELECT
        M.MOV_CODEMP,
        M.MOV_NUMERO,
        M.MOV_DATA,             -- TODO: data de emissão
        M.MOV_CLIFOR,           -- TODO: código do cliente
        M.MOV_VALORTOTAL,       -- INT64 — dividir por 100
        M.MOV_VALORDESC,        -- INT64 — descontos, dividir por 100
        M.MOV_TIPO              -- TODO: S=Saída (faturamento)
    FROM FIS_MOVIMENTO M
    WHERE M.MOV_CODEMP = ?
      AND M.MOV_TIPO = 'S'      -- apenas saídas (vendas)
      AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?
      AND EXTRACT(MONTH FROM M.MOV_DATA) = ?
    ORDER BY M.MOV_DATA
"""
