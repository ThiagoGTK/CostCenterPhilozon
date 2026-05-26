# Queries — Referência Completa

Todas as queries do projeto, organizadas por origem, propósito e lógica de negócio.

---

## Índice

1. [ETL — Extração do SIA (Firebird, read-only)](#1-etl--extração-do-sia)
2. [ETL — Carga no DW (PostgreSQL, upserts)](#2-etl--carga-no-dw)
3. [ETL — Resolução de FKs (lookups internos)](#3-etl--resolução-de-fks)
4. [API — Queries Analíticas (PostgreSQL)](#4-api--queries-analíticas)
5. [API — Queries ORM (CRUD)](#5-api--queries-orm)
6. [Views Analíticas (Metabase)](#6-views-analíticas)

---

## 1. ETL — Extração do SIA

Todas as queries abaixo são executadas via `SIAExtractor` usando `pyodbc` em modo **somente leitura**.  
Parâmetros posicionais usam `?` (padrão do driver ODBC Firebird — não usar dicionário nem `:nome`).

---

### 1.1 `SQL_PLANO_CONTAS` — `etl/queries/ctb.py`

**Propósito:** Extrair o plano de contas contábil da Philozon para popular `dim_conta_sia`.

```sql
SELECT
    C.CON_CODPLA,   -- plano de contas (1 = Philozon 2019, 2 = Philozon 2023)
    C.CON_COD,      -- código numérico da conta (chave interna do SIA)
    C.CON_CODSUP,   -- código da conta pai (para hierarquia)
    C.CON_CLASS,    -- código hierárquico legível (ex: "3.01.02")
    C.CON_NIVEL,    -- nível na hierarquia (1 = raiz, 2 = grupo, 3+ = folha)
    C.CON_TIPO,     -- tipo da conta (analítica, sintética etc.)
    C.CON_DESC,     -- descrição/nome da conta
    C.CON_INAT      -- 'S' = inativa (filtrada no WHERE)
FROM CTB_CONTAS C
WHERE C.CON_CODPLA IN (1, 2)   -- apenas planos da Philozon
  AND C.CON_INAT <> 'S'        -- apenas contas ativas
ORDER BY C.CON_CODPLA, C.CON_CLASS
```

**Por que `CON_CODPLA IN (1, 2)`?**  
`CTB_CONTAS` não tem coluna `CODEMP`. O isolamento por empresa é feito pelo plano de contas. A Philozon usa o plano 1 (estrutura de 2019) e o plano 2 (estrutura de 2023 em diante).

**Destino:** `dim_conta_sia` via `loader.upsert_dim_conta_sia()`

---

### 1.2 `SQL_CENTROS_CUSTO` — `etl/queries/ctb.py`

**Propósito:** Extrair centros de custo do SIA para referência nos mapeamentos.

```sql
SELECT
    CC.CC_CODCCPL,  -- plano de CC (3 = "Philozon & Ozoncare")
    CC.CC_COD,      -- código numérico do CC
    CC.CC_CODSUP,   -- código do CC pai
    CC.CC_CLASS,    -- código hierárquico legível
    CC.CC_NIVEL,    -- nível hierárquico
    CC.CC_TIPO,     -- tipo do CC
    CC.CC_DESC,     -- descrição/nome do CC
    CC.CC_INAT      -- 'S' = inativo
FROM CTB_CCUSTOS CC
WHERE CC.CC_CODCCPL = 3    -- plano 3 = "Philozon & Ozoncare"
  AND CC.CC_INAT <> 'S'   -- apenas CCs ativos
ORDER BY CC.CC_CLASS
```

**Importante:** `CTB_CCUSTOS` não tem `CODEMP`, assim como `CTB_CONTAS`. O plano 3 cobre todas as empresas Philozon.

> **Nota de uso:** Esta query está implementada mas o dado de CC no ETL é apenas informativo. Na prática, `MOV_CECT = NULL` em todos os lançamentos do SIA da Philozon, então o mapeamento de CC no fato não é utilizado.

---

### 1.3 `SQL_LANCAMENTOS` — `etl/queries/ctb.py`

**Propósito:** Extrair lançamentos contábeis de um período para popular `fato_lancamento_realizado`. Esta é a query central do ETL.

```sql
SELECT
    M.MOV_CODEMP,   -- empresa (chave obrigatória, igual ao parâmetro ?)
    M.MOV_NUMLAN,   -- número sequencial do lançamento (por empresa + data)
    M.MOV_DATA,     -- data de competência do lançamento
    M.MOV_CODCON,   -- código da conta contábil (FK -> CTB_CONTAS.CON_COD)
    M.MOV_CECT,     -- código do centro de custo (SEMPRE NULL na Philozon)
    M.MOV_TIPO,     -- tipo: 1=Débito, 2=Crédito (3=Encerramento e 4=Transf. excluídos)
    M.MOV_VALOR,    -- valor do lançamento — NUMERIC nativo, não dividir por 100
    M.MOV_HIST      -- histórico livre do lançamento
FROM CTB_MOVIMENTOS M
WHERE M.MOV_CODEMP = ?                            -- parâmetro 1: empresa
  AND M.MOV_TIPO IN (1, 2)                        -- apenas Débito e Crédito
  AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?          -- parâmetro 2: ano
  AND EXTRACT(MONTH FROM M.MOV_DATA) = ?          -- parâmetro 3: mês
ORDER BY M.MOV_DATA, M.MOV_NUMLAN, M.MOV_CODCON
```

**Por que excluir tipos 3 e 4?**
- Tipo 3 (encerramento de exercício): lançamentos de ajuste de encerramento, não representam transações reais
- Tipo 4 (transferência entre contas): movimentação interna sem impacto na análise gerencial

**`MOV_VALOR`:** É `NUMERIC` nativo no Firebird. O `pyodbc` pode retornar como `float` dependendo do driver; o `transformer.py` converte para `Decimal` via `sia_decimal()` sem divisão.

**Chave de idempotência gerada no transformer:**
```python
sia_lancamento_id = f"{MOV_CODEMP}_{MOV_DATA}_{MOV_NUMLAN}_{MOV_CODCON}_{MOV_TIPO}"
```
`MOV_NUMLAN` sozinho não é globalmente único — é sequencial por empresa/data. O composto garante unicidade global.

**Destino:** `fato_lancamento_realizado` via `loader.upsert_fato_lancamento_realizado()`

---

### 1.4 `SQL_EMPRESAS` — `etl/queries/ger.py`

**Propósito:** Espelhar o cadastro de empresas do SIA no DW.

```sql
SELECT
    E.EMP_COD,      -- código da empresa (chave de negócio)
    E.EMP_NOM,      -- razão social
    E.EMP_NOMFANT,  -- nome fantasia (usado como fallback se EMP_NOM vazio)
    E.EMP_CNPJCPF,  -- CNPJ
    E.EMP_ATIINA    -- 'A' = ativa, 'I' = inativa
FROM GER_EMPRESAS E
WHERE E.EMP_ATIINA = 'A'    -- apenas empresas ativas
ORDER BY E.EMP_COD
```

**Sem parâmetro de empresa** — lista todas as empresas ativas do SIA de uma vez.

**Destino:** `dim_empresa` via `loader.upsert_dim_empresa()`

---

### 1.5 `SQL_CLIENTES` — `etl/queries/ger.py`

**Propósito:** Extrair cadastro de clientes por empresa.

```sql
SELECT
    C.CLI_CODEMP,   -- empresa (chave composta)
    C.CLI_COD,      -- código do cliente (chave composta)
    C.CLI_DESC,     -- razão social
    C.CLI_FANT,     -- nome fantasia
    C.CLI_CNPJCPF,  -- CNPJ/CPF
    C.CLI_ATIINA    -- booleano (diferente de GER_EMPRESAS que usa char)
FROM GER_CLIDEST C
WHERE C.CLI_CODEMP = ?    -- parâmetro: empresa
ORDER BY C.CLI_COD
```

**Destino:** `dim_cliente` via `loader.upsert_dim_cliente()`

---

### 1.6 `SQL_FORNECEDORES` — `etl/queries/ger.py`

**Propósito:** Extrair cadastro global de fornecedores.

```sql
SELECT
    E.EMI_COD,      -- código do fornecedor (chave única — sem CODEMP)
    E.EMI_DESC,     -- razão social
    E.EMI_FANT,     -- nome fantasia
    E.EMI_CNPJCPF,  -- CNPJ/CPF
    E.EMI_ATIINA    -- booleano (ativo/inativo)
FROM GER_EMITENTES E
ORDER BY E.EMI_COD
```

**`GER_EMITENTES` não tem `CODEMP`** — é um cadastro global compartilhado por todas as empresas do SIA. Portanto nenhum filtro por empresa é aplicado.

**Destino:** `dim_fornecedor` via `loader.upsert_dim_fornecedor()`

---

### 1.7 `SQL_CONTAS_RECEBER` — `etl/queries/crc.py`

**Propósito:** Extrair títulos a receber com parcelas para análise de inadimplência e fluxo.

```sql
SELECT
    T.TIT_CODEMP,       -- empresa
    T.TIT_LAN,          -- número do título (chave: CODEMP + LAN)
    T.TIT_CODCLI,       -- código do cliente (FK -> GER_CLIDEST)
    T.TIT_DOC,          -- número do documento (NF, boleto etc.)
    T.TIT_DTEMI,        -- data de emissão do título
    T.TIT_HIS,          -- histórico/observação
    TP.TITPAR_NUM,      -- número da parcela
    TP.TITPAR_DTVENC,   -- data de vencimento da parcela
    TP.TITPAR_VAL,      -- valor da parcela — NUMERIC nativo
    TP.TITPAR_SAL,      -- saldo em aberto da parcela — NUMERIC nativo
    TP.TITPAR_SIT       -- situação: 'A'=Aberta, 'L'=Liquidada, etc.
FROM CRC_TITULO T
JOIN CRC_TITULOPARC TP
  ON TP.TITPAR_CODEMP = T.TIT_CODEMP      -- join pelo CODEMP (obrigatório)
 AND TP.TITPAR_LANTIT = T.TIT_LAN         -- join pelo número do título
WHERE T.TIT_CODEMP = ?                    -- parâmetro 1: empresa
  AND EXTRACT(YEAR  FROM TP.TITPAR_DTVENC) = ?   -- parâmetro 2: ano
  AND EXTRACT(MONTH FROM TP.TITPAR_DTVENC) = ?   -- parâmetro 3: mês
ORDER BY TP.TITPAR_DTVENC, T.TIT_LAN, TP.TITPAR_NUM
```

**Filtra pelo vencimento da parcela**, não pela emissão do título. Isso dá a visão de fluxo de caixa do período.

**Join seguro:** O join sempre inclui `CODEMP` — se omitido, o join cruzaria parcelas de empresas diferentes.

---

### 1.8 `SQL_CONTAS_PAGAR` — `etl/queries/cpg.py`

**Propósito:** Extrair títulos a pagar com parcelas para análise de fluxo de saída.

```sql
SELECT
    T.TIT_CODEMP,       -- empresa
    T.TIT_LAN,          -- número do título
    T.TIT_CODCRE,       -- código do credor (FK -> GER_EMITENTES.EMI_COD)
    T.TIT_DOC,          -- número do documento (NF do fornecedor)
    T.TIT_DTEMI,        -- data de emissão
    T.TIT_DTENT,        -- data de entrada/recebimento da NF
    T.TIT_HIS,          -- histórico
    TP.TITPAR_NUM,      -- número da parcela
    TP.TITPAR_DTVENC,   -- data de vencimento
    TP.TITPAR_VAL,      -- valor da parcela — NUMERIC nativo
    TP.TITPAR_SAL,      -- saldo em aberto — NUMERIC nativo
    TP.TITPAR_SIT       -- situação da parcela
FROM CPG_TITULO T
JOIN CPG_TITULOPARC TP
  ON TP.TITPAR_CODEMP = T.TIT_CODEMP
 AND TP.TITPAR_LANTIT = T.TIT_LAN
WHERE T.TIT_CODEMP = ?
  AND EXTRACT(YEAR  FROM TP.TITPAR_DTVENC) = ?
  AND EXTRACT(MONTH FROM TP.TITPAR_DTVENC) = ?
ORDER BY TP.TITPAR_DTVENC, T.TIT_LAN, TP.TITPAR_NUM
```

Estrutura idêntica a `SQL_CONTAS_RECEBER`, mas no módulo CPG. A diferença principal é `TIT_CODCRE` (credor/fornecedor) em vez de `TIT_CODCLI` (cliente).

---

### 1.9 `SQL_RECEITAS` — `etl/queries/fis.py`

**Propósito:** Extrair receita bruta de faturamento via documentos fiscais.

```sql
SELECT
    M.MOV_CODEMP,         -- empresa
    M.MOV_NUMERO,         -- número do documento fiscal
    M.MOV_DATA,           -- data de emissão
    M.MOV_CLIFOR,         -- código do cliente
    M.MOV_VALORTOTAL,     -- TODO: verificar se INT64 (÷100) ou NUMERIC nativo
    M.MOV_VALORDESC,      -- descontos
    M.MOV_TIPO            -- 'S' = saída (faturamento)
FROM FIS_MOVIMENTO M
WHERE M.MOV_CODEMP = ?
  AND M.MOV_TIPO = 'S'                          -- apenas NFs de saída
  AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?
  AND EXTRACT(MONTH FROM M.MOV_DATA) = ?
ORDER BY M.MOV_DATA
```

> **ATENÇÃO:** Colunas do `FIS_MOVIMENTO` ainda não foram validadas via MCP Firebird. O campo `MOV_VALORTOTAL` pode ser `INT64` (necessitando divisão por 100) diferentemente do `CTB_MOVIMENTOS`. Validar antes de usar em produção.

---

## 2. ETL — Carga no DW

Queries executadas pelo `DWLoader` no PostgreSQL (`schema dw`). Todas usam `INSERT ... ON CONFLICT DO UPDATE` para garantir idempotência.

---

### 2.1 Upsert `dim_tempo`

```sql
INSERT INTO dw.dim_tempo (data, ano, mes, trimestre, semestre, nome_mes)
VALUES (:data, :ano, :mes, :trimestre, :semestre, :nome_mes)
ON CONFLICT (data) DO NOTHING
```

**Conflito em:** `data` (UNIQUE).  
**Ação:** `DO NOTHING` — datas já existentes são simplesmente ignoradas. Os dados de calendário não mudam.

---

### 2.2 Upsert `dim_empresa`

```sql
INSERT INTO dw.dim_empresa (codemp, nome, cnpj, ativa)
VALUES (:codemp, :nome, :cnpj, :ativa)
ON CONFLICT (codemp) DO UPDATE SET
    nome  = EXCLUDED.nome,
    cnpj  = EXCLUDED.cnpj,
    ativa = EXCLUDED.ativa
```

**Conflito em:** `codemp` (UNIQUE).  
**Ação:** Atualiza todos os campos — mantém o cadastro sincronizado com o SIA. Se uma empresa for desativada no SIA, `ativa` será atualizado para `false`.

---

### 2.3 Upsert `dim_conta_sia`

```sql
INSERT INTO dw.dim_conta_sia
    (codpla, conta_codigo, conta_class, conta_codsup, conta_nome, conta_tipo, conta_nivel)
VALUES
    (:codpla, :conta_codigo, :conta_class, :conta_codsup, :conta_nome, :conta_tipo, :conta_nivel)
ON CONFLICT (codpla, conta_codigo) DO UPDATE SET
    conta_class  = EXCLUDED.conta_class,
    conta_codsup = EXCLUDED.conta_codsup,
    conta_nome   = EXCLUDED.conta_nome,
    conta_tipo   = EXCLUDED.conta_tipo,
    conta_nivel  = EXCLUDED.conta_nivel
```

**Conflito em:** `(codpla, conta_codigo)` — par plano + código é único.  
**Ação:** Atualiza todos os metadados da conta. O código `CON_CLASS` (hierárquico) pode mudar quando o plano é reestruturado.

---

### 2.4 Upsert `dim_fornecedor`

```sql
INSERT INTO dw.dim_fornecedor (cod_sia, nome, nome_fantasia, cnpj_cpf, ativo)
VALUES (:cod_sia, :nome, :nome_fantasia, :cnpj_cpf, :ativo)
ON CONFLICT (cod_sia) DO UPDATE SET
    nome          = EXCLUDED.nome,
    nome_fantasia = EXCLUDED.nome_fantasia,
    cnpj_cpf      = EXCLUDED.cnpj_cpf,
    ativo         = EXCLUDED.ativo
```

**Conflito em:** `cod_sia` (`EMI_COD` — sem CODEMP pois é cadastro global).

---

### 2.5 Upsert `fato_lancamento_realizado`

```sql
INSERT INTO dw.fato_lancamento_realizado
    (id_empresa, id_tempo, id_conta_sia, id_conta_gerencial, id_centro_custo,
     sia_lancamento_id, valor, tipo_lancamento, historico, data_referencia)
VALUES
    (:id_empresa, :id_tempo, :id_conta_sia, :id_conta_gerencial, :id_centro_custo,
     :sia_lancamento_id, :valor, :tipo_lancamento, :historico, :data_referencia)
ON CONFLICT (sia_lancamento_id) DO UPDATE SET
    valor           = EXCLUDED.valor,
    tipo_lancamento = EXCLUDED.tipo_lancamento,
    historico       = EXCLUDED.historico,
    data_carga      = now()
```

**Conflito em:** `sia_lancamento_id` (chave composta `CODEMP_DATA_NUMLAN_CODCON_TIPO`).  
**Ação:** Atualiza valor e histórico — permite corrigir lançamentos alterados no SIA.  
**Não atualiza:** `id_conta_gerencial` nem `id_centro_custo` — se o mapeamento mudar após a carga, é necessário reprocessar o período.

---

### 2.6 Upsert `fato_receita`

```sql
INSERT INTO dw.fato_receita
    (id_empresa, id_tempo, id_cliente, chave_upsert,
     receita_bruta, deducoes, receita_liquida)
VALUES
    (:id_empresa, :id_tempo, :id_cliente, :chave_upsert,
     :receita_bruta, :deducoes, :receita_liquida)
ON CONFLICT (chave_upsert) DO UPDATE SET
    receita_bruta   = EXCLUDED.receita_bruta,
    deducoes        = EXCLUDED.deducoes,
    receita_liquida = EXCLUDED.receita_liquida,
    data_carga      = now()
```

**Conflito em:** `chave_upsert` (`empresa+ano+mes+cliente`).

---

## 3. ETL — Resolução de FKs

Queries de lookup executadas antes do upsert dos fatos, para transformar chaves do SIA em IDs do DW.

---

### 3.1 `resolver_ids_empresa`

```sql
SELECT id, codemp
FROM dw.dim_empresa
WHERE codemp = ANY(:vals)
```

**Entrada:** lista de `EMP_COD` do SIA.  
**Saída:** dicionário `{codemp → id}`.

---

### 3.2 `resolver_ids_tempo`

```sql
SELECT id, data::text
FROM dw.dim_tempo
WHERE data::text = ANY(:vals)
```

**Entrada:** lista de datas ISO (strings).  
**Saída:** dicionário `{data_str → id}`.  
O cast `data::text` permite comparação por `ANY(:vals)` com lista de strings.

---

### 3.3 `resolver_ids_conta_sia`

```sql
SELECT DISTINCT ON (conta_codigo) id, conta_codigo
FROM dw.dim_conta_sia
WHERE conta_codigo = ANY(:vals)
ORDER BY conta_codigo, codpla DESC
```

**Entrada:** lista de `CON_COD` (como strings).  
**Saída:** dicionário `{conta_codigo → id}`.  
`DISTINCT ON (conta_codigo)` com `ORDER BY codpla DESC` garante que, se o mesmo `CON_COD` existir em dois planos, o plano mais recente (maior `codpla`) tem prioridade.

---

### 3.4 `resolver_mapeamentos_conta`

```sql
SELECT cs.conta_codigo, m.id_conta_gerencial
FROM dw.mapeamento_conta_sia_gerencial m
JOIN dw.dim_conta_sia cs ON cs.id = m.id_conta_sia
WHERE m.id_empresa = :id_empresa
  AND m.ativo = true
```

**Entrada:** `id_empresa` (DW).  
**Saída:** dicionário `{conta_codigo → id_conta_gerencial}`.  
Usado para popular `id_conta_gerencial` em `fato_lancamento_realizado`. Se a conta não tiver mapeamento, o campo fica `NULL` e o lançamento não aparece no comparativo gerencial.

---

### 3.5 `resolver_mapeamentos_cc`

```sql
SELECT cc_sia_codigo, id_centro_custo_gerencial
FROM dw.mapeamento_centro_custo_sia_gerencial
WHERE id_empresa = :id_empresa
  AND ativo = true
```

**Entrada:** `id_empresa` (DW).  
**Saída:** dicionário `{cc_sia_codigo → id_centro_custo_gerencial}`.  
Na prática, sempre retorna vazio porque `MOV_CECT = NULL` em todos os lançamentos.

---

## 4. API — Queries Analíticas

Queries SQL raw executadas via `sqlalchemy.text()` nos routers da FastAPI. São as mais complexas do projeto.

---

### 4.1 Comparativo Realizado × Orçado — `api/routers/comparativo.py`

**Endpoint:** `GET /comparativo/{ano}/{id_versao}`  
**Propósito:** Principal query analítica. Junta orçado (por conta+CC+mês) com realizado (por conta+mês, sem CC) para mostrar desvios.

```sql
WITH realizado_agg AS (
    -- CTE 1: agrega realizado por (conta, ano, mes)
    -- Ignora CC porque MOV_CECT = NULL em todos os lançamentos do SIA.
    -- O filtro :id_empresa é aplicado AQUI dentro do CTE, não no JOIN externo,
    -- para evitar dupla contagem multi-empresa quando agrupando sem empresa.
    SELECT
        id_conta_gerencial,
        EXTRACT(YEAR  FROM data_referencia)::int AS ano,
        EXTRACT(MONTH FROM data_referencia)::int AS mes,
        SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END)
            AS valor_realizado
    FROM dw.fato_lancamento_realizado
    WHERE id_conta_gerencial IS NOT NULL
      AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
    GROUP BY id_conta_gerencial,
             EXTRACT(YEAR  FROM data_referencia),
             EXTRACT(MONTH FROM data_referencia)
)
SELECT
    fo.mes,
    cg.codigo                           AS conta_gerencial_codigo,
    cg.nome                             AS conta_gerencial_nome,
    NULL::varchar                        AS centro_custo_codigo,  -- sempre NULL
    NULL::varchar                        AS centro_custo_nome,    -- sempre NULL
    SUM(fo.valor)                       AS valor_orcado,          -- soma todos os CCs
    COALESCE(MAX(r.valor_realizado), 0) AS valor_realizado        -- um por (conta,mes)
FROM dw.fato_orcamento fo
JOIN dw.dim_conta_gerencial cg ON cg.id = fo.id_conta_gerencial
LEFT JOIN realizado_agg r
       ON  r.id_conta_gerencial = fo.id_conta_gerencial
      AND  r.ano                = fo.ano
      AND  r.mes                = fo.mes
WHERE fo.ano       = :ano
  AND fo.id_versao = :id_versao
  AND (:id_empresa     IS NULL OR fo.id_empresa     = :id_empresa)
  AND (:id_centro_custo IS NULL OR fo.id_centro_custo = :id_centro_custo)
GROUP BY fo.mes, cg.codigo, cg.nome
ORDER BY fo.mes, cg.codigo
```

**Parâmetros:** `:ano`, `:id_versao`, `:id_empresa` (opcional), `:id_centro_custo` (opcional, só filtra orçado).

**Cálculo do valor_realizado:**
- `tipo_lancamento = 'D'` (Débito): multiplica por +1
- `tipo_lancamento = 'C'` (Crédito): multiplica por -1
- Para contas de despesa (natureza DEVEDORA): débitos são positivos — correto
- Para contas de receita (natureza CREDORA): créditos são positivos (negativo × -1 = positivo) — correto

**Por que `MAX(r.valor_realizado)` e não `SUM`?**  
O CTE já agrupou sem empresa — há exatamente uma linha por `(conta, mes)` no `realizado_agg`. O `MAX()` é equivalente ao valor único; poderia ser `MIN()` também. O `COALESCE` trata contas sem realizado.

**Decisão de design:** Ver `docs/DECISOES_TECNICAS.md` ADR-003 e ADR-004.

---

### 4.2 DRE Gerencial — `api/routers/dre.py`

**Endpoint:** `GET /dre/{ano}/{id_versao}`  
**Propósito:** Retorna todas as contas gerenciais ativas com totais anuais de orçado e realizado. A hierarquia é resolvida no frontend via `id_pai`.

```sql
WITH orcado AS (
    -- Total orçado anual por conta (soma todos os meses e CCs)
    SELECT id_conta_gerencial, SUM(valor) AS total
    FROM dw.fato_orcamento
    WHERE ano = :ano AND id_versao = :id_versao
      AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
    GROUP BY id_conta_gerencial
),
realizado AS (
    -- Total realizado anual por conta (débitos positivos, créditos negativos)
    SELECT id_conta_gerencial,
           SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END) AS total
    FROM dw.fato_lancamento_realizado
    WHERE EXTRACT(YEAR FROM data_referencia) = :ano
      AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
      AND id_conta_gerencial IS NOT NULL
    GROUP BY id_conta_gerencial
)
SELECT
    cg.id,
    cg.codigo,
    cg.nome,
    cg.tipo,
    cg.natureza,
    cg.nivel,
    cg.id_pai,
    COALESCE(o.total, 0) AS valor_orcado,
    COALESCE(r.total, 0) AS valor_realizado
FROM dw.dim_conta_gerencial cg
LEFT JOIN orcado    o ON o.id_conta_gerencial = cg.id
LEFT JOIN realizado r ON r.id_conta_gerencial = cg.id
WHERE cg.ativa = true
ORDER BY cg.codigo
```

**Diferença em relação ao comparativo:** O DRE retorna totais **anuais** (sem desagregar por mês) e **todas as contas ativas** (mesmo as sem dados). A hierarquia é plana no banco — o frontend usa `id_pai` para montar a árvore.

---

### 4.3 Lançamentos Realizados — `api/routers/lancamentos.py`

**Endpoint:** `GET /lancamentos/{mes_referencia}`  
**Propósito:** Auditoria e diagnóstico. Retorna até 500 lançamentos individuais de um período.

```python
# Query ORM — equivalente SQL:
SELECT *
FROM dw.fato_lancamento_realizado
WHERE EXTRACT(YEAR  FROM data_referencia) = :ano
  AND EXTRACT(MONTH FROM data_referencia) = :mes
  AND (:id_empresa IS NULL OR id_empresa = :id_empresa)
  AND (:id_conta_gerencial IS NULL OR id_conta_gerencial = :id_conta_gerencial)
LIMIT 500
```

O limite de 500 é intencional — o endpoint não é para análise em massa, mas para verificar lançamentos específicos.

---

## 5. API — Queries ORM

Queries de CRUD executadas pelo SQLAlchemy ORM. Mais simples que as analíticas, mas com lógica de negócio importante.

---

### 5.1 Orçamento — Listar

```python
# api/routers/orcamento.py
db.query(FatoOrcamento)
  .filter(FatoOrcamento.ano == ano, FatoOrcamento.id_versao == id_versao)
  .filter(FatoOrcamento.id_empresa == id_empresa)       # se informado
  .filter(FatoOrcamento.id_centro_custo == id_centro_custo)  # se informado
  .all()
```

---

### 5.2 Orçamento — Upsert (criar ou atualizar célula)

A lógica de upsert é feita no Python (não via SQL) para retornar o objeto Pydantic correto:

```python
# Verifica se já existe lançamento para mesma combinação
existente = db.query(FatoOrcamento).filter(
    FatoOrcamento.id_empresa           == payload.id_empresa,
    FatoOrcamento.id_versao            == payload.id_versao,
    FatoOrcamento.id_conta_gerencial   == payload.id_conta_gerencial,
    FatoOrcamento.id_centro_custo      == payload.id_centro_custo,
    FatoOrcamento.ano                  == payload.ano,
    FatoOrcamento.mes                  == payload.mes,
).first()

if existente:
    existente.valor = payload.valor          # atualiza
    existente.observacao = payload.observacao
else:
    obj = FatoOrcamento(**payload.model_dump())  # insere
    db.add(obj)
```

Retorna `409` se a versão estiver `bloqueada`.

---

### 5.3 Workflow — Verificações de estado

```python
# Bloqueia duplicata de workflow ativo (RASCUNHO ou ENVIADO)
db.query(WorkflowOrcamento).filter(
    WorkflowOrcamento.id_versao == payload.id_versao,
    WorkflowOrcamento.id_empresa == payload.id_empresa,
    WorkflowOrcamento.status.in_(["RASCUNHO", "ENVIADO"]),
).first()
```

```python
# Validação de transição de estado
def _exige_status(wf, esperado):
    if wf.status != esperado.value:
        raise HTTPException(409, f"Status atual '{wf.status}' — esperado '{esperado.value}'")
```

**Transições:**
- `RASCUNHO → ENVIADO`: `enviar_para_revisao()` — dispara e-mail em background
- `ENVIADO → APROVADO`: `aprovar()` — bloqueia versão + e-mail
- `ENVIADO → REPROVADO`: `reprovar()` — comentário obrigatório + e-mail

---

### 5.4 Mapeamentos — Anti-duplicata

```python
# Antes de inserir mapeamento de conta, verifica se já existe ativo
db.query(MapeamentoContaSia).filter(
    MapeamentoContaSia.id_conta_sia == payload.id_conta_sia,
    MapeamentoContaSia.id_empresa   == payload.id_empresa,
    MapeamentoContaSia.ativo        == True,
).first()
# Se existir → HTTP 409 Conflict
```

A mesma lógica vale para `MapeamentoCentroCusto`.

**Delete = soft delete:**
```python
obj.ativo = False  # não remove do banco
db.commit()
```

---

### 5.5 Mapeamentos — Contas SIA disponíveis

```python
db.query(DimContaSia)
  .filter(DimContaSia.codpla == codpla)        # opcional
  .filter(DimContaSia.conta_nivel == nivel)    # opcional
  .order_by(DimContaSia.codpla, DimContaSia.conta_class)
  .all()
```

---

### 5.6 Justificativas de variação — listar por workflow

```python
db.query(JustificativaVariacao).filter(
    JustificativaVariacao.id_versao  == wf.id_versao,
    JustificativaVariacao.id_empresa == wf.id_empresa,
).all()
```

---

## 6. Views Analíticas

Views criadas pelas migrations 003 e 004. Usadas pelo Metabase e disponíveis para consulta direta.

---

### 6.1 `dw.v_lancamentos_detalhado` — migration 003

**Propósito:** Desnormaliza `fato_lancamento_realizado` com todos os JOINs de dimensão para facilitar relatórios no Metabase.

```sql
SELECT
    lr.id,
    lr.sia_lancamento_id,
    dt.data                     AS data_referencia,
    dt.ano, dt.mes, dt.nome_mes, dt.trimestre, dt.semestre,
    e.id AS id_empresa, e.nome AS empresa,
    cs.conta_codigo AS sia_conta_codigo,
    cs.conta_class  AS sia_conta_class,
    cs.conta_nome   AS sia_conta_nome,
    cg.id AS id_conta_gerencial,
    cg.codigo AS conta_gerencial_codigo,
    cg.nome   AS conta_gerencial_nome,
    cg.tipo   AS conta_tipo,
    cc.id     AS id_centro_custo,  -- sempre NULL
    cc.codigo AS cc_codigo,        -- sempre NULL
    cc.nome   AS cc_nome,          -- sempre NULL
    lr.tipo_lancamento,
    lr.valor,
    lr.valor * CASE WHEN lr.tipo_lancamento = 'D' THEN 1 ELSE -1 END AS valor_liquido,
    lr.historico,
    lr.data_carga
FROM dw.fato_lancamento_realizado lr
JOIN  dw.dim_tempo           dt ON dt.id = lr.id_tempo
JOIN  dw.dim_empresa          e ON  e.id = lr.id_empresa
JOIN  dw.dim_conta_sia       cs ON cs.id = lr.id_conta_sia
LEFT JOIN dw.dim_conta_gerencial cg ON cg.id = lr.id_conta_gerencial  -- NULL se não mapeado
LEFT JOIN dw.dim_centro_custo    cc ON cc.id = lr.id_centro_custo     -- sempre NULL
```

**`valor_liquido`:** valor com sinal (+D/-C). Útil para somar diretamente sem `CASE WHEN` no Metabase.

---

### 6.2 `dw.v_comparativo_mensal` — corrigida pela migration 004

**Propósito:** Comparativo mensal por conta/empresa/versão para dashboards do Metabase.

A versão da migration 003 tinha o bug do CC join. A migration 004 a substituiu:

```sql
WITH realizado_agg AS (
    -- Agrega por (empresa, conta, ano, mes) — sem CC
    SELECT
        id_empresa,
        id_conta_gerencial,
        EXTRACT(YEAR  FROM data_referencia)::int AS ano,
        EXTRACT(MONTH FROM data_referencia)::int AS mes,
        SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END) AS valor_realizado
    FROM dw.fato_lancamento_realizado
    WHERE id_conta_gerencial IS NOT NULL
    GROUP BY id_empresa, id_conta_gerencial,
             EXTRACT(YEAR  FROM data_referencia),
             EXTRACT(MONTH FROM data_referencia)
)
SELECT
    fo.ano, fo.mes, <nome_mes>,
    v.id AS id_versao, v.nome AS versao_nome, v.tipo AS versao_tipo,
    e.id AS id_empresa, e.nome AS empresa_nome,
    cg.id AS id_conta_gerencial,
    cg.codigo AS conta_codigo, cg.nome AS conta_nome,
    cg.tipo AS conta_tipo, cg.natureza AS conta_natureza,
    SUM(fo.valor)                       AS valor_orcado,
    COALESCE(MAX(r.valor_realizado), 0) AS valor_realizado,
    COALESCE(MAX(r.valor_realizado), 0) - SUM(fo.valor) AS variacao_absoluta,
    ROUND(((COALESCE(MAX(r.valor_realizado),0) - SUM(fo.valor)) / ABS(SUM(fo.valor)) * 100), 2)
        AS variacao_percentual
FROM dw.fato_orcamento fo
JOIN dw.dim_versao_orcamento v ON v.id = fo.id_versao
JOIN dw.dim_empresa          e ON e.id = fo.id_empresa
JOIN dw.dim_conta_gerencial cg ON cg.id = fo.id_conta_gerencial
LEFT JOIN realizado_agg r
    ON r.id_empresa = fo.id_empresa
   AND r.id_conta_gerencial = fo.id_conta_gerencial
   AND r.ano = fo.ano AND r.mes = fo.mes
GROUP BY fo.ano, fo.mes, v.id, v.nome, v.tipo,
         e.id, e.nome, cg.id, cg.codigo, cg.nome, cg.tipo, cg.natureza
```

**Diferença para a query da API:** A view mantém `id_empresa` no GROUP BY do CTE e no JOIN externo (para que o Metabase possa filtrar por empresa). A API endpoint remove empresa do CTE GROUP BY para suportar filtro pontual sem multi-empresa.

---

### 6.3 `dw.v_evolucao_mensal` — migration 003

**Propósito:** Totais mensais de realizado por tipo de conta. Útil para gráficos de tendência no Metabase.

```sql
SELECT
    dt.ano, dt.mes, dt.nome_mes, dt.trimestre,
    e.id AS id_empresa, e.nome AS empresa,
    cg.tipo AS conta_tipo,
    SUM(lr.valor * CASE WHEN lr.tipo_lancamento = 'D' THEN 1 ELSE -1 END) AS valor_realizado,
    COUNT(DISTINCT lr.sia_lancamento_id) AS qtd_lancamentos
FROM dw.fato_lancamento_realizado lr
JOIN dw.dim_tempo           dt ON dt.id = lr.id_tempo
JOIN dw.dim_empresa          e ON  e.id = lr.id_empresa
JOIN dw.dim_conta_gerencial cg ON cg.id = lr.id_conta_gerencial
WHERE lr.id_conta_gerencial IS NOT NULL
GROUP BY dt.ano, dt.mes, dt.nome_mes, dt.trimestre, e.id, e.nome, cg.tipo
```

**Casos de uso Metabase:** "Evolução de RECEITA vs DESPESA mês a mês por empresa."

---

### 6.4 `dw.v_dre_anual` — migration 003

**Propósito:** DRE completa com hierarquia, orçado e realizado por ano/versão/empresa.

```sql
WITH realizado_anual AS (
    SELECT id_conta_gerencial, id_empresa,
           EXTRACT(YEAR FROM data_referencia)::int AS ano,
           SUM(valor * CASE WHEN tipo_lancamento = 'D' THEN 1 ELSE -1 END) AS valor_realizado
    FROM dw.fato_lancamento_realizado WHERE id_conta_gerencial IS NOT NULL
    GROUP BY id_conta_gerencial, id_empresa, EXTRACT(YEAR FROM data_referencia)
),
orcado_anual AS (
    SELECT id_conta_gerencial, id_empresa, id_versao, ano,
           SUM(valor) AS valor_orcado
    FROM dw.fato_orcamento
    GROUP BY id_conta_gerencial, id_empresa, id_versao, ano
)
SELECT
    cg.id, cg.codigo, cg.nome, cg.tipo, cg.natureza, cg.nivel,
    cg.id_pai, pai.codigo AS codigo_pai, pai.nome AS nome_pai,
    v.id AS id_versao, v.nome AS versao_nome, v.ano,
    e.id AS id_empresa, e.nome AS empresa_nome,
    COALESCE(o.valor_orcado, 0)    AS valor_orcado,
    COALESCE(r.valor_realizado, 0) AS valor_realizado,
    COALESCE(r.valor_realizado, 0) - COALESCE(o.valor_orcado, 0) AS variacao_absoluta,
    ROUND(((COALESCE(r.valor_realizado,0) - COALESCE(o.valor_orcado,0))
           / ABS(COALESCE(o.valor_orcado,0)) * 100), 2) AS variacao_percentual
FROM dw.dim_conta_gerencial cg
LEFT JOIN dw.dim_conta_gerencial pai ON pai.id = cg.id_pai
CROSS JOIN dw.dim_versao_orcamento v         -- todas as versões
CROSS JOIN dw.dim_empresa e                  -- todas as empresas
LEFT JOIN orcado_anual   o ON o.id_conta_gerencial = cg.id AND o.id_empresa = e.id AND o.id_versao = v.id
LEFT JOIN realizado_anual r ON r.id_conta_gerencial = cg.id AND r.id_empresa = e.id AND r.ano = v.ano
WHERE cg.ativa = true AND e.ativa = true
  AND (o.valor_orcado IS NOT NULL OR r.valor_realizado IS NOT NULL)
```

**`CROSS JOIN`:** A view cruza todas as contas × versões × empresas e filtra apenas onde há dados (orçado ou realizado). Isso garante que toda combinação com dados apareça, mesmo se faltar um dos lados.

---

### 6.5 `dw.v_workflow_resumo` — migration 003

**Propósito:** Status de aprovação desnormalizado para dashboards.

```sql
SELECT
    w.id, w.status,
    v.id AS id_versao, v.nome AS versao_nome, v.ano AS versao_ano,
    v.tipo AS versao_tipo, v.bloqueada AS versao_bloqueada,
    e.id AS id_empresa, e.nome AS empresa_nome,
    w.criado_por, w.enviado_por, w.aprovado_por, w.reprovado_por,
    w.data_envio, w.data_decisao, w.comentario,
    w.criado_em, w.atualizado_em,
    CASE
        WHEN w.data_decisao IS NOT NULL AND w.data_envio IS NOT NULL
        THEN ROUND(EXTRACT(EPOCH FROM (w.data_decisao - w.data_envio)) / 3600, 1)
        ELSE NULL
    END AS horas_para_decisao
FROM dw.workflow_orcamento w
JOIN dw.dim_versao_orcamento v ON v.id = w.id_versao
JOIN dw.dim_empresa          e ON  e.id = w.id_empresa
```

**`horas_para_decisao`:** Calculado em horas com 1 casa decimal. `EXTRACT(EPOCH FROM ...)` retorna diferença em segundos; dividir por 3600 converte para horas. Útil para medir tempo médio de aprovação por período.

---

## Resumo — Mapa de Queries por Fluxo

```
USUÁRIO ACESSA DASHBOARD
    |
    +-- GET /comparativo/{ano}/{id_versao}
    |       |-- CTE realizado_agg: fato_lancamento_realizado
    |       |-- fato_orcamento (filtro versao+empresa+CC)
    |       `-- LEFT JOIN por (conta, ano, mes)
    |
    +-- GET /dre/{ano}/{id_versao}
    |       |-- CTE orcado: fato_orcamento GROUP BY conta
    |       |-- CTE realizado: fato_lancamento_realizado GROUP BY conta
    |       `-- dim_conta_gerencial (todas ativas) LEFT JOIN ambos CTEs
    |
    `-- GET /lancamentos/{YYYY-MM}  (auditoria)
            `-- fato_lancamento_realizado WHERE ano+mes LIMIT 500

PIPELINE ETL (mensal)
    |
    +-- Passo 1: GER_EMPRESAS → dim_empresa (upsert por codemp)
    +-- Passo 2: CTB_CONTAS → dim_conta_sia (upsert por codpla+codigo)
    +-- Passo 3: CTB_MOVIMENTOS → resolver FKs → fato_lancamento_realizado
    |       |-- resolver_ids_empresa: dim_empresa WHERE codemp = ANY(...)
    |       |-- resolver_ids_tempo: dim_tempo WHERE data = ANY(...)
    |       |-- resolver_ids_conta_sia: DISTINCT ON conta_codigo ORDER BY codpla DESC
    |       |-- resolver_mapeamentos_conta: JOIN mapeamento + dim_conta_sia
    |       `-- upsert fato ON CONFLICT (sia_lancamento_id) DO UPDATE
    `-- (dim_tempo gerado localmente, sem query ao SIA)
```
