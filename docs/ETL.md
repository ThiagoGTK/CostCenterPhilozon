# ETL — Documentação Técnica

Pipeline de extração do ERP System SIA (Firebird) para o Data Warehouse PostgreSQL.

---

## Visão Geral

```
SIA (Firebird, read-only)
    ↓ SIAExtractor.extrair_*()  — queries SELECT via pyodbc
DataFrame pandas
    ↓ transformer.py            — normalização, Decimal, chave de idempotência
Lista de dicts
    ↓ DWLoader.upsert_*()       — INSERT ... ON CONFLICT DO UPDATE
PostgreSQL DW (schema dw)
```

**Princípios:**
- SIA é **somente leitura** — zero escrita no Firebird
- Idempotente — pode rodar N vezes sem duplicar dados
- Campos monetários SIA são `NUMERIC` nativos — **não dividir por escala**
- Queries transacionais filtram por `CODEMP`; `CTB_CONTAS` e `CTB_CCUSTOS` filtram por plano

---

## Como Executar

```bash
cd etl
pip install -r requirements.txt   # se ainda não instalado

# Carga de um mês específico
python pipeline.py --ano 2025 --mes 1

# Forçar empresa específica (sobrescreve SIA_CODEMP do .env)
python pipeline.py --ano 2025 --mes 1 --codemp 3

# Sem argumentos: usa ano/mês atual + empresa do .env
python pipeline.py
```

**Variáveis de ambiente necessárias (`.env`):**

```
SIA_HOST=<hostname>
SIA_PORT=3050
SIA_DATABASE=<caminho do .fdb>
SIA_USER=<usuario>
SIA_PASSWORD=<senha>
SIA_CODEMP=1            # EMP_COD da empresa principal

DW_HOST=localhost
DW_PORT=5432
DW_NAME=fpa
DW_USER=fpa_user
DW_PASSWORD=<senha>
```

---

## Passos do Pipeline

### Passo 1 — `dim_tempo`

Gerado localmente pelo transformer (sem acesso ao SIA). Preenche todos os dias do mês solicitado.

```python
gerar_dim_tempo(data_inicio, data_fim)  # → DataFrame com colunas: data, ano, mes, trimestre, semestre, nome_mes
loader.upsert_dim_tempo(df_tempo)        # ON CONFLICT (data) DO NOTHING
```

---

### Passo 2 — `dim_empresa`

Extrai todas as empresas ativas do SIA e sincroniza com o DW.

**Query SIA:** `SELECT EMP_COD, EMP_NOM, EMP_NOMFANT, EMP_CNPJCPF, EMP_ATIINA FROM GER_EMPRESAS`

**Transformação:**
- `ativa = (EMP_ATIINA == 'A')`
- `nome = EMP_NOM` (fallback `EMP_NOMFANT`)

**Upsert:** `ON CONFLICT (codemp) DO UPDATE SET nome, cnpj, ativa`

---

### Passo 3 — `dim_conta_sia`

Extrai o plano de contas contábil do SIA (Philozon usa planos 1 e 2).

**Query SIA:**
```sql
SELECT CON_CODPLA, CON_COD, CON_CODSUP, CON_CLASS, CON_NIVEL, CON_TIPO, CON_DESC
FROM CTB_CONTAS
WHERE CON_CODPLA IN (1, 2)   -- planos Philozon 2019 e 2023
  AND CON_INAT <> 'S'        -- apenas ativas
```

> `CTB_CONTAS` **não tem coluna `CODEMP`**. O isolamento por empresa é feito pelo plano de contas (`CON_CODPLA`).

**Upsert:** `ON CONFLICT (codpla, conta_codigo) DO UPDATE SET conta_class, conta_nome, conta_tipo, conta_nivel`

---

### Passo 4 — `fato_lancamento_realizado`

Extrai lançamentos contábeis do período e resolve FKs para o DW.

#### 4a. Extração

**Query SIA:**
```sql
SELECT M.MOV_CODEMP, M.MOV_NUMLAN, M.MOV_DATA, M.MOV_CODCON,
       M.MOV_CECT, M.MOV_TIPO, M.MOV_VALOR, M.MOV_HIST
FROM CTB_MOVIMENTOS M
WHERE M.MOV_CODEMP = ?        -- SIA_CODEMP do .env
  AND EXTRACT(YEAR  FROM M.MOV_DATA) = ?
  AND EXTRACT(MONTH FROM M.MOV_DATA) = ?
  AND M.MOV_TIPO IN (1, 2)   -- apenas Débito e Crédito (excluindo encerramento/transferência)
```

**Parâmetros posicionais** (não dict — driver ODBC Firebird usa `?`):
```python
self._query(SQL_LANCAMENTOS, (self._cfg.sia_codemp, ano, mes))
```

#### 4b. Transformação

```python
transformar_lancamentos_contabeis(df)
```

- `MOV_VALOR` → `Decimal` via `sia_decimal()` (sem divisão — já é NUMERIC nativo)
- `MOV_TIPO` → `tipo_lancamento`: `1='D'`, `2='C'`
- `MOV_CECT` → `cc_sia_codigo`: `NULL` → string vazia
- Chave de idempotência:
  ```python
  sia_lancamento_id = f"{MOV_CODEMP}_{MOV_DATA}_{MOV_NUMLAN}_{MOV_CODCON}_{MOV_TIPO}"
  ```
  > `MOV_NUMLAN` é sequencial por empresa/data, não global — por isso inclui todos os discriminadores.

#### 4c. Resolução de FKs

```python
_resolver_fks_lancamentos(df, loader, id_empresa_dw)
```

| FK | Obrigatória | Comportamento se não resolvida |
|----|-------------|-------------------------------|
| `id_empresa` | SIM | Linha descartada com `logger.warning` |
| `id_tempo` | SIM | Linha descartada |
| `id_conta_sia` | SIM | Linha descartada |
| `id_conta_gerencial` | NÃO | Inserido com `NULL` — conta ainda não mapeada |
| `id_centro_custo` | NÃO | Inserido com `NULL` — `MOV_CECT` é sempre NULL no SIA |

#### 4d. Upsert

```python
loader.upsert_fato_lancamento_realizado(records)
# ON CONFLICT (sia_lancamento_id) DO UPDATE SET valor, tipo_lancamento, historico, id_conta_gerencial, id_centro_custo, data_carga
```

---

## Arquivos do ETL

```
etl/
├── pipeline.py      — Orquestrador: 4 passos, logging, argparse
├── extractor.py     — SIAExtractor: conexão read-only, queries por módulo
├── transformer.py   — Normalização, Decimal, chave de idempotência, dim_tempo
├── loader.py        — DWLoader: todos os upserts idempotentes
├── config.py        — ETLConfig (dataclass lida via .env)
└── queries/         — SQL separado por módulo do SIA
    ├── ctb.py       — CTB_MOVIMENTOS, CTB_CONTAS, CTB_CCUSTOS
    ├── ger.py       — GER_EMPRESAS
    ├── crc.py       — CRC_TITULO, CRC_TITULOPARC
    ├── cpg.py       — CPG_TITULO, CPG_TITULOPARC
    └── fis.py       — FIS_MOVIMENTO
```

---

## Mapeamento de Colunas SIA (validado 2026-05)

### `CTB_MOVIMENTOS` — Lançamentos contábeis

| Campo SIA    | Tipo    | Coluna DW           | Observação |
|--------------|---------|---------------------|------------|
| `MOV_CODEMP` | INT     | `id_empresa` (FK)   | Filtro obrigatório |
| `MOV_NUMLAN` | INT     | parte de `sia_lancamento_id` | Sequencial por empresa/data |
| `MOV_DATA`   | DATE    | `data_referencia`   | Competência |
| `MOV_CODCON` | INT     | `conta_sia_codigo`  | FK → `CTB_CONTAS.CON_COD` |
| `MOV_CECT`   | INT/NULL| `cc_sia_codigo`     | **Sempre NULL na Philozon** |
| `MOV_TIPO`   | INT     | `tipo_lancamento`   | 1→'D', 2→'C'; tipos 3 e 4 excluídos |
| `MOV_VALOR`  | NUMERIC | `valor`             | NUMERIC nativo — não dividir |
| `MOV_HIST`   | VARCHAR | `historico`         | Histórico livre |

### `CTB_CONTAS` — Plano de contas

> Não tem `CODEMP`. Filtrar por `CON_CODPLA IN (1, 2)` para Philozon.

| Campo SIA    | Tipo    | Coluna DW         |
|--------------|---------|-------------------|
| `CON_CODPLA` | INT     | `codpla`          |
| `CON_COD`    | INT     | `conta_codigo`    |
| `CON_CODSUP` | INT     | `conta_codsup`    |
| `CON_CLASS`  | VARCHAR | `conta_class`     |
| `CON_NIVEL`  | INT     | `conta_nivel`     |
| `CON_TIPO`   | CHAR(1) | `conta_tipo`      |
| `CON_DESC`   | VARCHAR | `conta_nome`      |
| `CON_INAT`   | CHAR(1) | filtro: `<> 'S'`  |

### `GER_EMPRESAS` — Empresas

| Campo SIA     | Tipo    | Coluna DW |
|---------------|---------|-----------|
| `EMP_COD`     | INT     | `codemp`  |
| `EMP_NOM`     | VARCHAR | `nome`    |
| `EMP_NOMFANT` | VARCHAR | fallback `nome` |
| `EMP_CNPJCPF` | VARCHAR | `cnpj`    |
| `EMP_ATIINA`  | CHAR(1) | `ativa` (`'A'` = ativo) |

### `CTB_CCUSTOS` — Centros de custo SIA

> Não tem `CODEMP`. Filtrar por `CC_CODCCPL = 3` (plano "Philozon & Ozoncare").

| Campo SIA    | Tipo    | Descrição |
|--------------|---------|-----------|
| `CC_CODCCPL` | INT     | Plano de CC |
| `CC_COD`     | INT     | Código (chave parcial) |
| `CC_CLASS`   | VARCHAR | Código hierárquico |
| `CC_DESC`    | VARCHAR | Descrição |
| `CC_INAT`    | CHAR(1) | 'S' = inativo |

---

## Campos Monetários — Regra Crítica

```python
def sia_decimal(valor) -> Decimal:
    """
    MOV_VALOR, TIT_VAL, TITPAR_VAL são NUMERIC nativos no Firebird.
    Não há divisão por 100 ou qualquer escala.
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return Decimal("0")
    return Decimal(str(valor))
```

Mesmo que `pyodbc` retorne `float` em alguns drivers, `Decimal(str(valor))` preserva a precisão original. **Nunca dividir por 100.**

---

## Idempotência

Cada tabela tem uma chave única que garante que rodar o pipeline duas vezes não duplica dados:

| Tabela | Chave de conflito |
|--------|-------------------|
| `dim_tempo` | `data` |
| `dim_empresa` | `codemp` |
| `dim_conta_sia` | `(codpla, conta_codigo)` |
| `fato_lancamento_realizado` | `sia_lancamento_id` |
| `fato_receita` | `chave_upsert` |
| `fato_despesa` | `chave_upsert` |

Todos os loaders usam `INSERT INTO ... ON CONFLICT (...) DO UPDATE SET ...`.

---

## Estratégia de Carga Incremental

O pipeline processa **um mês por vez**. Para carregar um ano completo:

```bash
for mes in 1 2 3 4 5 6 7 8 9 10 11 12; do
    python pipeline.py --ano 2025 --mes $mes
done
```

Ou no Docker Compose, o serviço `etl` pode ser configurado com um cron interno para executar mensalmente.

---

## Troubleshooting

### "FK não resolvida" — lançamentos descartados

```
WARNING — 42 lançamentos descartados: FK não resolvida (empresa, data ou conta ausente no DW).
```

**Causas possíveis:**
1. `dim_empresa` não foi carregada (passo 2 falhou) — reexecutar sem `--codemp`
2. `dim_conta_sia` não tem a conta — a query `CTB_CONTAS` excluiu contas inativas (`CON_INAT = 'S'`) que têm lançamentos históricos
3. `dim_tempo` não tem a data — improvável (gerado localmente), mas pode ocorrer se o período for inconsistente

### "Empresa CODEMP=X não encontrada no DW"

O passo 2 (dim_empresa) não carregou a empresa antes do passo 4. Verificar logs do passo 2.

### Valores realizados zerados no comparativo

Se `fato_lancamento_realizado` está populado mas `GET /comparativo` retorna `valor_realizado = 0`:

1. Verificar se os mapeamentos estão cadastrados (`GET /mapeamentos/contas`)
2. Os lançamentos têm `id_conta_gerencial = NULL` → precisam do mapeamento de contas
3. Após cadastrar mapeamentos, reexecutar o ETL para atualizar os lançamentos existentes

### Driver ODBC Firebird

O driver deve estar instalado no servidor onde o ETL roda:
- Windows: Firebird ODBC Driver de https://firebirdsql.org/
- Linux: pacote `libfbclient2` + ODBC driver

A connection string em `extractor.py` pode precisar de ajuste no nome do driver (`DRIVER={...}`) conforme o instalado.
