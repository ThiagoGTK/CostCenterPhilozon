"""
Queries do módulo CRC (Contas a Receber) do SIA.
Colunas validadas via MCP Firebird em 2026-05.

Estrutura:
- CRC_TITULO: cabeçalho do título (TIT_CODEMP + TIT_LAN = chave)
- CRC_TITULOPARC: parcelas (TITPAR_CODEMP + TITPAR_LANTIT + TITPAR_NUM = chave)
- TIT_VAL / TITPAR_VAL são NUMERIC nativos.
- TITPAR_SIT: situação da parcela ('A'=Aberta, 'L'=Liquidada, etc.)
"""

SQL_CONTAS_RECEBER = """
    SELECT
        T.TIT_CODEMP,
        T.TIT_LAN,
        T.TIT_CODCLI,
        T.TIT_DOC,
        T.TIT_DTEMI,
        T.TIT_HIS,
        TP.TITPAR_NUM,
        TP.TITPAR_DTVENC,
        TP.TITPAR_VAL,
        TP.TITPAR_SAL,
        TP.TITPAR_SIT
    FROM CRC_TITULO T
    JOIN CRC_TITULOPARC TP
      ON TP.TITPAR_CODEMP = T.TIT_CODEMP
     AND TP.TITPAR_LANTIT = T.TIT_LAN
    WHERE T.TIT_CODEMP = ?
      AND EXTRACT(YEAR  FROM TP.TITPAR_DTVENC) = ?
      AND EXTRACT(MONTH FROM TP.TITPAR_DTVENC) = ?
    ORDER BY TP.TITPAR_DTVENC, T.TIT_LAN, TP.TITPAR_NUM
"""
