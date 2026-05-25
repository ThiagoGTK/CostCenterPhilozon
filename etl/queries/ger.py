"""
Queries do módulo GER (Cadastros Base) do SIA.
Colunas validadas via MCP Firebird em 2026-05.

Notas:
- GER_EMPRESAS: chave EMP_COD, campo ativo/inativo = EMP_ATIINA ('A'/'I').
  Empresas ativas: EMP_COD 1 (Philozon), 2 (O3R), 3, 4. EMP_COD 100 = inativa.
- GER_CLIDEST: chave CLI_CODEMP + CLI_COD. CLI_ATIINA é booleano (não char).
- GER_EMITENTES: NÃO tem CODEMP — cadastro global. Chave: EMI_COD.
  EMI_ATIINA é booleano.
"""

SQL_EMPRESAS = """
    SELECT
        E.EMP_COD,
        E.EMP_NOM,
        E.EMP_NOMFANT,
        E.EMP_CNPJCPF,
        E.EMP_ATIINA
    FROM GER_EMPRESAS E
    WHERE E.EMP_ATIINA = 'A'
    ORDER BY E.EMP_COD
"""

SQL_CLIENTES = """
    SELECT
        C.CLI_CODEMP,
        C.CLI_COD,
        C.CLI_DESC,
        C.CLI_FANT,
        C.CLI_CNPJCPF,
        C.CLI_ATIINA
    FROM GER_CLIDEST C
    WHERE C.CLI_CODEMP = ?
    ORDER BY C.CLI_COD
"""

SQL_FORNECEDORES = """
    SELECT
        E.EMI_COD,
        E.EMI_DESC,
        E.EMI_FANT,
        E.EMI_CNPJCPF,
        E.EMI_ATIINA
    FROM GER_EMITENTES E
    ORDER BY E.EMI_COD
"""
