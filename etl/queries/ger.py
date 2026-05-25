"""
Queries do módulo GER (Cadastros Base) do SIA.
TODO: Validar nomes de colunas contra dicionário de dados real.
"""

SQL_EMPRESAS = """
    SELECT
        E.EMP_CODIGO,       -- TODO: código da empresa
        E.EMP_RAZAO,        -- TODO: razão social
        E.EMP_CNPJ          -- TODO: CNPJ
    FROM GER_EMPRESAS E
    WHERE E.EMP_CODIGO = ?
"""

SQL_CLIENTES = """
    SELECT
        C.CLI_CODEMP,
        C.CLI_CODIGO,       -- TODO: confirmar campo
        C.CLI_RAZAO,        -- TODO: razão social
        C.CLI_CNPJCPF       -- TODO: CNPJ/CPF
    FROM GER_CLIDEST C
    WHERE C.CLI_CODEMP = ?
    ORDER BY C.CLI_CODIGO
"""

SQL_FORNECEDORES = """
    SELECT
        F.EMI_CODEMP,
        F.EMI_CODIGO,       -- TODO: confirmar campo
        F.EMI_RAZAO,
        F.EMI_CNPJCPF
    FROM GER_EMITENTES F
    WHERE F.EMI_CODEMP = ?
    ORDER BY F.EMI_CODIGO
"""
