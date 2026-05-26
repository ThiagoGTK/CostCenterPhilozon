# CLAUDE.md — Contexto do Projeto FP&A Financeiro

Este arquivo fornece contexto para o Claude Code trabalhar neste projeto.

---

## O que é este projeto

Plataforma interna de FP&A (Financial Planning & Analysis) para orçamento empresarial
e acompanhamento Realizado × Orçado. Integra com o ERP System SIA via ETL.

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy 2 + Alembic
- **Banco analítico**: PostgreSQL 15 (schemas: `dw` e `app`)
- **ETL**: Python + pandas + pyodbc (Firebird ODBC para o SIA)
- **Frontend**: React 18 + TypeScript + Vite + Recharts + TanStack Query v5
- **BI**: Metabase v0.50 (open-source, conectado ao schema `dw`)
- **Deploy**: Docker Compose + Nginx

---

## Regras Absolutas — Não Negociáveis

### 1. NUNCA usar float para valores monetários
```python
# CORRETO
from decimal import Decimal
valor = Decimal("1234.56")

# ERRADO — nunca fazer isso
valor = 1234.56  # float
```

No PostgreSQL: sempre `NUMERIC(15,2)`, nunca `FLOAT` ou `REAL`.

### 2. SIA é SOMENTE LEITURA
O banco do ERP System SIA nunca pode receber escrita.
- Nunca usar `INSERT`, `UPDATE`, `DELETE`, `MERGE` no SIA
- A classe `SIAExtractor` só executa `SELECT`
- Conexão feita com `readonly=True`: `pyodbc.connect(conn_str, autocommit=False, readonly=True)`

### 3. Secrets no .env — nunca no código
```python
# CORRETO
password = os.environ["DW_PASSWORD"]

# ERRADO
password = "minha_senha_123"
```

### 4. ETL idempotente
Todo upsert usa `ON CONFLICT DO UPDATE`. Rodar o pipeline duas vezes
com os mesmos dados não cria duplicatas.

### 5. Campos monetários do SIA já são NUMERIC — não dividir
```python
# CORRETO — MOV_VALOR é Firebird NUMERIC nativo
valor = Decimal(str(row["MOV_VALOR"]))

# ERRADO — divisão por 100 não se aplica a esta instância
valor = Decimal(str(row["MOV_VALOR"])) / Decimal("100")
```

Validado em 2026-05 via MCP Firebird. MOV_VALOR, TIT_VAL, TITPAR_VAL
são todos tipo 16 (NUMERIC) no Firebird — já vêm como decimal.

### 6. Joins no SIA — atenção às tabelas sem CODEMP
```sql
-- Tabelas transacionais: sempre incluir CODEMP no join
JOIN CRC_TITULOPARC TP ON TP.TITPAR_CODEMP = T.TIT_CODEMP AND TP.TITPAR_LANTIT = T.TIT_LAN

-- CTB_CONTAS e CTB_CCUSTOS NÃO têm CODEMP
-- Filtrar por plano da empresa em vez disso:
WHERE CTB_CONTAS.CON_CODPLA IN (1, 2)   -- planos Philozon
WHERE CTB_CCUSTOS.CC_CODCCPL = 3         -- plano "Philozon & Ozoncare"

-- GER_EMITENTES NÃO tem CODEMP — cadastro global de fornecedores
```

### 7. NUNCA hardcodar id_empresa = 1
O `id` de `dim_empresa` é autoincrement do DW — não é previsível.
Use `useEmpresaAtiva()` no frontend (resolve `VITE_EMPRESA_CODEMP` → `id` via API).
No backend, receba `id_empresa` como parâmetro de query.

---

## Problemas Resolvidos (histórico para não regredir)

### Bug: `valor_realizado = 0` em todo o comparativo
**Causa**: `MOV_CECT = NULL` em todos os lançamentos SIA da Philozon.
O join `ON lr.id_centro_custo = fo.id_centro_custo` nunca casava (NULL ≠ NULL).
**Fix**: `api/routers/comparativo.py` usa CTE `realizado_agg` que agrega por
`(conta, empresa, ano, mes)` sem CC. `migrations/004` corrige a view Metabase.

### Bug: dupla contagem multi-empresa no comparativo
**Causa**: CTE agrupava por `(conta, empresa, mes)`, mas outer GROUP BY não tinha empresa.
`MAX()` pegava o maior valor de uma empresa em vez de somar todas.
**Fix**: remover `id_empresa` do GROUP BY do CTE; filtrar empresa no WHERE do CTE.
Resultado: uma linha por `(conta, mes)`, correta para qualquer combinação de filtro.

### Bug: `ID_EMPRESA_PADRAO = 1` hardcodado
**Encontrado em**: `Workflow.tsx`, `Orcamento.tsx`, `MapeamentoContas.tsx`, `MapeamentoCentrosCusto.tsx`.
**Fix**: todos usam `useEmpresaAtiva()` do hook `useDimensoes.ts`.

---

## Arquitetura de Banco

O PostgreSQL tem dois schemas:

- **`dw`**: Data Warehouse — dimensões, fatos, workflow, mapeamentos.
  Conectado ao Metabase (leitura) e à API (leitura e escrita de orçamento).
- **`app`**: Reservado para tabelas de suporte da aplicação (futuro).

### Tabelas principais (schema `dw`)

**Dimensões:**
- `dim_empresa` — empresas (espelha GER_EMPRESAS do SIA)
- `dim_tempo` — calendário diário (gerado pelo transformer, não extraído)
- `dim_centro_custo` — CCs gerenciais (cadastro interno, via API)
- `dim_conta_gerencial` — plano de contas gerencial (cadastro interno, via API)
- `dim_conta_sia` — plano contábil do SIA (espelho, read-only na origem)
- `dim_versao_orcamento` — versões do orçamento (Original, Revisão, Forecast)

**Fatos:**
- `fato_lancamento_realizado` — lançamentos contábeis via ETL (nunca inserção manual)
  - `id_centro_custo` é **sempre NULL** (MOV_CECT = NULL no SIA)
- `fato_orcamento` — orçamento inserido pelos usuários via API
- `fato_receita` — receita bruta agregada via ETL
- `fato_despesa` — despesas agregadas via ETL

**Operacionais:**
- `workflow_orcamento` — ciclo de aprovação (RASCUNHO→ENVIADO→APROVADO|REPROVADO)
- `justificativa_variacao` — justificativas para desvios significativos
- `mapeamento_conta_sia_gerencial` — de-para contas
- `mapeamento_centro_custo_sia_gerencial` — de-para centros de custo

**Views (Metabase):**
- `v_lancamentos_detalhado` — lançamentos desnormalizados
- `v_comparativo_mensal` — realizado × orçado por mês/conta (corrigida migration 004)
- `v_evolucao_mensal` — totais mensais por tipo de conta
- `v_dre_anual` — DRE com hierarquia
- `v_workflow_resumo` — status de aprovação

---

## Migrations

Sequência atual: `001 → 002 → 003 → 004` (linear, sem branches)

```bash
alembic upgrade head    # aplicar todas
alembic downgrade -1    # reverter uma
alembic current         # ver revisão atual
```

---

## ETL — Fluxo

```
SIA (Firebird, read-only)
    ↓ SIAExtractor.extrair_*()
DataFrame pandas
    ↓ transformer.py
DataFrame normalizado (valores Decimal, chaves de upsert)
    ↓ DWLoader.upsert_*()
PostgreSQL DW (schema dw)
```

**Executar ETL manualmente:**
```bash
cd etl
python pipeline.py --ano 2025 --mes 1
python pipeline.py --ano 2025 --mes 1 --codemp 3  # forçar empresa
```

**4 passos por execução:**
1. `dim_tempo` — gera datas do período (local, sem SIA)
2. `dim_empresa` — espelho de GER_EMPRESAS
3. `dim_conta_sia` — espelho de CTB_CONTAS (planos 1 e 2)
4. `fato_lancamento_realizado` — lançamentos do período com FK resolution

---

## Mapeamento de Colunas Reais do SIA (validado 2026-05)

### CTB_MOVIMENTOS
| Campo SIA | Tipo | Descrição |
|-----------|------|-----------|
| MOV_CODEMP | INT | Empresa |
| MOV_NUMLAN | INT | Nº do lançamento (sequencial por empresa/data) |
| MOV_DATA | DATE | Data de competência |
| MOV_CODCON | INT | FK → CTB_CONTAS.CON_COD |
| MOV_CECT | INT/NULL | FK → CTB_CCUSTOS.CC_COD (**SEMPRE NULL na Philozon**) |
| MOV_TIPO | INT | 1=Débito, 2=Crédito, 3=Encerramento, 4=Transf. |
| MOV_VALOR | NUMERIC | Valor já decimal (sem divisão por escala) |
| MOV_HIST | VARCHAR | Histórico do lançamento |

### CTB_CONTAS (sem CODEMP — filtrar por CON_CODPLA)
Planos Philozon: `CON_CODPLA IN (1, 2)` (Philozon 2019, Philozon 2023)

| Campo SIA | Tipo | Descrição |
|-----------|------|-----------|
| CON_CODPLA | INT | Plano de contas |
| CON_COD | INT | Código da conta (PK parcial) |
| CON_CODSUP | INT | Conta pai |
| CON_CLASS | VARCHAR | Código hierárquico (ex: "1.01.02.03") |
| CON_NIVEL | INT | Nível hierárquico |
| CON_TIPO | CHAR(1) | Tipo da conta |
| CON_DESC | VARCHAR | Descrição |
| CON_INAT | CHAR(1) | 'S' = inativa |

### CTB_CCUSTOS (sem CODEMP — filtrar por CC_CODCCPL)
Plano Philozon: `CC_CODCCPL = 3` ("Philozon & Ozoncare")

| Campo SIA | Tipo | Descrição |
|-----------|------|-----------|
| CC_CODCCPL | INT | Plano de centros de custo |
| CC_COD | INT | Código do CC (PK parcial) |
| CC_CODSUP | INT | CC pai |
| CC_CLASS | VARCHAR | Código hierárquico |
| CC_NIVEL | INT | Nível hierárquico |
| CC_TIPO | CHAR(1) | Tipo |
| CC_DESC | VARCHAR | Descrição |
| CC_INAT | CHAR(1) | 'S' = inativo |

### CRC_TITULO + CRC_TITULOPARC
- CRC_TITULO: `TIT_CODEMP + TIT_LAN` = chave. Cliente = `TIT_CODCLI`. Valor = `TIT_VAL`.
- CRC_TITULOPARC: join por `TITPAR_CODEMP + TITPAR_LANTIT`. Parcela = `TITPAR_NUM`. Venc. = `TITPAR_DTVENC`. Saldo = `TITPAR_SAL`. Situação = `TITPAR_SIT`.

### CPG_TITULO + CPG_TITULOPARC
- CPG_TITULO: `TIT_CODEMP + TIT_LAN` = chave. Credor = `TIT_CODCRE` (FK GER_EMITENTES.EMI_COD).
- CPG_TITULOPARC: mesma estrutura da CRC.

### GER_EMPRESAS
- Chave: `EMP_COD`. Ativas: `EMP_ATIINA = 'A'`.
- Empresas Philozon: EMP_COD 1, 3, 4. O3R: EMP_COD 2. EMP_COD 100 = inativa.

### GER_CLIDEST / GER_EMITENTES
- Clientes: `CLI_CODEMP + CLI_COD`. Nome = `CLI_DESC`. CNPJ = `CLI_CNPJCPF`.
- Fornecedores (GER_EMITENTES): **sem CODEMP** — global. Chave = `EMI_COD`. Nome = `EMI_DESC`.

---

## Módulos do SIA relevantes

| Prefixo | Módulo | Tabelas principais |
|---------|--------|--------------------|
| `GER_` | Cadastros base | GER_EMPRESAS, GER_CLIDEST, GER_EMITENTES |
| `CTB_` | Contabilidade | CTB_MOVIMENTOS, CTB_CONTAS, CTB_CCUSTOS |
| `EST_` | Estoque/Vendas | EST_VENDA, EST_PEDVEN, EST_MOVIMENTO |
| `FIS_` | Fiscal/NF-e | FIS_MOVIMENTO, FIS_MOVPROD |
| `CRC_` | Contas a Receber | CRC_TITULO, CRC_TITULOPARC |
| `CPG_` | Contas a Pagar | CPG_TITULO |
| `RH_`  | Folha de Pagamento | RH_MOVIMENTO |
| `FLX_` | Fluxo de Caixa | — |

---

## Comandos Úteis

```bash
# Subir banco dev
docker compose -f docker-compose.dev.yml up -d

# Rodar API em modo desenvolvimento
cd api && uvicorn api.main:app --reload --port 8000

# Rodar migrations
alembic upgrade head

# Gerar nova migration
alembic revision --autogenerate -m "descricao"

# Rodar testes
cd api && pytest tests/ -v

# Frontend dev
cd frontend && npm run dev

# ETL manual
cd etl && python pipeline.py --ano 2025 --mes 1

# Ver logs do container
docker compose logs -f api
docker compose logs -f etl
```

---

## Convenções de Código

- Sem comentários óbvios — só onde o "porquê" não é evidente
- Tipagem completa no Python (Mapped[], TypedDict, etc.)
- Pydantic para validação de entrada; nunca validar manualmente
- SQL raw via `text()` apenas para queries analíticas complexas
- Para CRUD simples, usar SQLAlchemy ORM
- TypeScript strict mode no frontend — sem `any`
- TanStack Query v5 no frontend — `useQuery`, `useMutation`, invalidação de cache

---

## Status das Fases

- [x] **Fase 1**: Schema inicial, migrations 001–002, modelos ORM
- [x] **Fase 2**: Colunas reais do SIA validadas via MCP Firebird; escala NUMERIC confirmada
- [x] **Fase 3**: CRUD completo de mapeamentos via API
- [x] **Fase 4**: Workflow completo com notificações SMTP via BackgroundTasks
- [x] **Fase 5**: Frontend conectado à API (9 routers, 8 páginas React)
- [x] **Fase 6**: Views Metabase (migrations 003 + 004)
- [x] **Fase 7**: Correção bug comparativo CC (migration 004 + api/routers/comparativo.py)
- [x] **Fase 8**: Documentação completa (README, docs/API, docs/BANCO_DE_DADOS, docs/ETL, docs/DECISOES_TECNICAS)
- [ ] **Pendente**: Executar ETL em produção para popular `fato_lancamento_realizado`
- [ ] **Pendente**: Cadastrar mapeamentos conta SIA → gerencial via frontend
- [ ] **Pendente**: Cadastrar orçamento via frontend para o ano corrente
