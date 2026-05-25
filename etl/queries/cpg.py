"""
Queries do módulo CPG (Contas a Pagar) do SIA.
TODO: Validar nomes de colunas contra dicionário de dados real.
"""

SQL_CONTAS_PAGAR = """
    SELECT
        T.TIT_CODEMP,           -- empresa
        T.TIT_NUMERO,           -- número do título
        T.TIT_DTEMI,            -- data de emissão
        T.TIT_DTVENC,           -- vencimento
        T.TIT_DTPAGO,           -- data de pagamento
        T.TIT_VALOR,            -- INT64 — dividir por 100
        T.TIT_VALORPAGO,        -- INT64 — dividir por 100
        T.TIT_CLIFOR,           -- código do fornecedor
        T.TIT_HISTORICO
    FROM CPG_TITULO T
    WHERE T.TIT_CODEMP = ?
      AND EXTRACT(YEAR  FROM T.TIT_DTVENC) = ?
      AND EXTRACT(MONTH FROM T.TIT_DTVENC) = ?
    ORDER BY T.TIT_DTVENC
"""
