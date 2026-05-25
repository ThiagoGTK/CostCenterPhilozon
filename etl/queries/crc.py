"""
Queries do módulo CRC (Contas a Receber) do SIA.
TODO: Validar nomes de colunas contra dicionário de dados real.
"""

SQL_CONTAS_RECEBER = """
    SELECT
        T.TIT_CODEMP,           -- empresa
        T.TIT_NUMERO,           -- número do título
        T.TIT_DTEMI,            -- data de emissão
        TP.PAR_DTVENC,          -- vencimento da parcela
        TP.PAR_DTPAGO,          -- data de pagamento (NULL se em aberto)
        TP.PAR_VALOR,           -- INT64 — dividir por 100
        TP.PAR_VALORPAGO,       -- INT64 — dividir por 100
        T.TIT_CLIFOR,           -- código do cliente
        T.TIT_HISTORICO         -- descrição
    FROM CRC_TITULO T
    JOIN CRC_TITULOPARC TP
      ON TP.PAR_CODEMP  = T.TIT_CODEMP
     AND TP.PAR_NUMERO  = T.TIT_NUMERO
    WHERE T.TIT_CODEMP = ?
      AND EXTRACT(YEAR  FROM TP.PAR_DTVENC) = ?
      AND EXTRACT(MONTH FROM TP.PAR_DTVENC) = ?
    ORDER BY TP.PAR_DTVENC
"""
