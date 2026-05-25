"""
Queries de extração do módulo CTB (Contabilidade) do SIA.

ATENÇÃO: Nomes de colunas marcados com TODO precisam ser validados
contra o dicionário de dados real do SIA antes de usar em produção.
"""

# TODO: Confirmar nomes reais das colunas na CTB_CONTAS
SQL_PLANO_CONTAS = """
    SELECT
        C.CON_CODEMP,       -- TODO: confirmar nome
        C.CON_CODIGO,       -- TODO: código da conta
        C.CON_DESCRICAO,    -- TODO: nome da conta
        C.CON_TIPO,         -- TODO: tipo da conta (S/A/R)
        C.CON_NIVEL         -- TODO: nível hierárquico
    FROM CTB_CONTAS C
    WHERE C.CON_CODEMP = ?
    ORDER BY C.CON_CODIGO
"""

# TODO: Confirmar nomes reais das colunas na CTB_CCUSTOS
SQL_CENTROS_CUSTO = """
    SELECT
        CC.CCS_CODEMP,      -- TODO: confirmar nome
        CC.CCS_CODIGO,      -- TODO: código do CC
        CC.CCS_DESCRICAO    -- TODO: descrição do CC
    FROM CTB_CCUSTOS CC
    WHERE CC.CCS_CODEMP = ?
    ORDER BY CC.CCS_CODIGO
"""

# TODO: Confirmar nomes reais das colunas na CTB_MOVIMENTOS
# Campos monetários: MOV_VALOR é INT64, dividir por 100 (confirmar escala)
SQL_LANCAMENTOS = """
    SELECT
        M.MOV_CODEMP,       -- TODO: confirmar nome
        M.MOV_NUMERO,       -- TODO: número único do lançamento
        M.MOV_DATA,         -- TODO: data de competência
        M.MOV_CONTA,        -- TODO: código da conta contábil
        M.MOV_CCUSTO,       -- TODO: código do centro de custo
        M.MOV_VALOR,        -- INT64 — dividir por 100 para obter Decimal
        M.MOV_TIPO,         -- D=Débito, C=Crédito
        M.MOV_HISTORICO     -- TODO: histórico do lançamento
    FROM CTB_MOVIMENTOS M
    WHERE M.MOV_CODEMP = ?
      AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?
      AND EXTRACT(MONTH FROM M.MOV_DATA) = ?
    ORDER BY M.MOV_DATA, M.MOV_NUMERO
"""
