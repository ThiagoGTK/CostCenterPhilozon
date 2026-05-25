"""
Queries de extração do módulo CTB (Contabilidade) do SIA.

Colunas validadas via MCP Firebird em 2026-05.

Notas de estrutura:
- CTB_CONTAS não tem CODEMP — filtrar por CON_CODPLA (plano da empresa).
  Planos Philozon: 1 = "Philozon 2019", 2 = "Philozon 2023".
- CTB_CCUSTOS não tem CODEMP — filtrar por CC_CODCCPL.
  Plano 3 = "Philozon & Ozoncare".
- MOV_VALOR é NUMERIC nativo — não dividir por 100.
- MOV_TIPO: 1=Débito, 2=Crédito, 3=Encerramento exercício, 4=Transferência entre contas.
- MOV_CECT pode ser NULL (lançamentos sem CC).
"""

# Plano de contas contábil da Philozon (planos 1 e 2)
SQL_PLANO_CONTAS = """
    SELECT
        C.CON_CODPLA,
        C.CON_COD,
        C.CON_CODSUP,
        C.CON_CLASS,
        C.CON_NIVEL,
        C.CON_TIPO,
        C.CON_DESC,
        C.CON_INAT
    FROM CTB_CONTAS C
    WHERE C.CON_CODPLA IN (1, 2)
      AND C.CON_INAT <> 'S'
    ORDER BY C.CON_CODPLA, C.CON_CLASS
"""

# Centros de custo (plano 3 = Philozon & Ozoncare)
SQL_CENTROS_CUSTO = """
    SELECT
        CC.CC_CODCCPL,
        CC.CC_COD,
        CC.CC_CODSUP,
        CC.CC_CLASS,
        CC.CC_NIVEL,
        CC.CC_TIPO,
        CC.CC_DESC,
        CC.CC_INAT
    FROM CTB_CCUSTOS CC
    WHERE CC.CC_CODCCPL = 3
      AND CC.CC_INAT <> 'S'
    ORDER BY CC.CC_CLASS
"""

# Lançamentos contábeis — apenas Débito (1) e Crédito (2)
# Excluir tipo 3 (encerramento) e 4 (transferência entre contas)
SQL_LANCAMENTOS = """
    SELECT
        M.MOV_CODEMP,
        M.MOV_NUMLAN,
        M.MOV_DATA,
        M.MOV_CODCON,
        M.MOV_CECT,
        M.MOV_TIPO,
        M.MOV_VALOR,
        M.MOV_HIST
    FROM CTB_MOVIMENTOS M
    WHERE M.MOV_CODEMP = ?
      AND M.MOV_TIPO IN (1, 2)
      AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?
      AND EXTRACT(MONTH FROM M.MOV_DATA) = ?
    ORDER BY M.MOV_DATA, M.MOV_NUMLAN, M.MOV_CODCON
"""
