# FP&A Financeiro — Plataforma de Planejamento Orçamentário

Plataforma interna para orçamento empresarial e acompanhamento **Realizado × Orçado**, integrada ao ERP System SIA via ETL.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 · FastAPI · SQLAlchemy 2 · Alembic |
| Banco analítico | PostgreSQL 15 (schemas `dw` e `app`) |
| ETL | Python · pandas · pyodbc (Firebird ODBC) |
| Frontend | React 18 · TypeScript · Vite · Recharts · TanStack Query v5 |
| BI | Metabase v0.50 (conectado ao schema `dw`) |
| Deploy | Docker Compose · Nginx |

---

## Funcionalidades

- **Orçamento** — lançamento por conta gerencial, centro de custo e mês; versionamento (Original, Revisão, Forecast)
- **Comparativo Realizado × Orçado** — por versão, empresa e período
- **DRE Gerencial** — hierarquia de contas com realizado e orçado
- **Workflow de Aprovação** — RASCUNHO → ENVIADO → APROVADO | REPROVADO; notificações SMTP
- **Mapeamentos** — contas SIA → gerenciais; CCs SIA → gerenciais
- **Metabase** — 5 views analíticas prontas para dashboard

---

## Pré-requisitos

- Docker + Docker Compose v2
- Python 3.11+ (desenvolvimento local)
- Node.js 20+ (desenvolvimento local)
- Driver ODBC Firebird instalado no servidor do ETL

---

## Setup — Desenvolvimento local

### 1. Variáveis de ambiente

```bash
cp .env.example .env
# Preencha .env com as credenciais reais — nunca commitar!
```

Variáveis obrigatórias:

```
DW_HOST / DW_PORT / DW_NAME / DW_USER / DW_PASSWORD
DATABASE_URL
SIA_HOST / SIA_PORT / SIA_DATABASE / SIA_USER / SIA_PASSWORD / SIA_CODEMP
VITE_API_URL=http://localhost:8000/api/v1
VITE_EMPRESA_CODEMP=1          # EMP_COD da empresa principal no SIA
```

### 2. Banco de dados (dev)

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 3. Backend

```bash
cd api
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

cd ..
alembic upgrade head             # aplica todas as migrations

cd api
uvicorn api.main:app --reload --port 8000
# Docs interativa: http://localhost:8000/docs
```

### 4. Frontend

```bash
cd frontend
cp .env.example .env             # ou crie com VITE_API_URL e VITE_EMPRESA_CODEMP
npm install
npm run dev
# http://localhost:5173
```

### 5. ETL (manual)

```bash
cd etl
pip install -r requirements.txt
python pipeline.py --ano 2025 --mes 1
# Opções: --ano, --mes, --codemp (forçar empresa)
```

---

## Deploy — Produção

```bash
# 1. Build do frontend
cd frontend && npm run build && cd ..

# 2. Subir todos os serviços
docker compose up -d --build
```

| Serviço  | URL |
|----------|-----|
| Frontend | `http://servidor/` |
| API REST | `http://servidor/api/v1/` |
| Swagger  | `http://servidor/docs` |
| Metabase | `http://servidor/metabase/` |

---

## Migrations

```bash
alembic upgrade head                        # aplicar todas
alembic downgrade -1                        # reverter uma
alembic revision --autogenerate -m "descr" # gerar nova
```

Sequência atual: `001 → 002 → 003 → 004`

| Migration | Descrição |
|-----------|-----------|
| 001 | Schema inicial — todas as tabelas do DW |
| 002 | Fix `dim_conta_sia` (`codemp→codpla`, adiciona `conta_class`); remove `codemp` de `dim_fornecedor` |
| 003 | 5 views analíticas para Metabase |
| 004 | Corrige `v_comparativo_mensal` — remove join por CC (todos os lançamentos SIA têm `MOV_CECT = NULL`) |

---

## Estrutura de Pastas

```
financeiro-fpa/
├── api/
│   ├── config.py           # Settings via pydantic-settings (.env)
│   ├── main.py             # FastAPI app + CORS + routers
│   ├── db/                 # Engine, session, Base
│   ├── models/             # ORM: dimensoes, fatos, workflow, mapeamento
│   ├── schemas/            # Pydantic I/O schemas
│   ├── routers/            # 9 routers REST
│   └── services/
│       └── email.py        # Notificações SMTP (stdlib smtplib)
├── etl/
│   ├── pipeline.py         # Orquestrador: 4 passos por execução
│   ├── extractor.py        # SIA read-only via pyodbc
│   ├── transformer.py      # Normalização, Decimal, chave de idempotência
│   ├── loader.py           # Upserts idempotentes no DW
│   ├── config.py           # ETLConfig (dataclass)
│   └── queries/            # SQL separado por módulo (ctb, ger, crc, cpg, fis)
├── frontend/src/
│   ├── pages/              # 8 páginas React
│   ├── hooks/              # React Query hooks (5 arquivos)
│   ├── services/
│   │   ├── api.ts          # Axios client + todos os tipos TS + funções HTTP
│   │   └── format.ts       # formatCurrency, formatPercent
│   └── components/         # Layout, KpiCard, etc.
├── migrations/
│   └── versions/           # 001–004
├── infra/
│   ├── nginx/nginx.conf
│   ├── postgres/init.sql   # Cria roles (fpa_user, metabase_reader)
│   └── metabase/           # SETUP.md + SQLs prontos para Metabase
├── docs/                   # Documentação técnica detalhada
│   ├── API.md
│   ├── BANCO_DE_DADOS.md
│   ├── ETL.md
│   └── DECISOES_TECNICAS.md
├── .env.example
├── docker-compose.yml      # Produção (db, api, etl, metabase, nginx)
├── docker-compose.dev.yml  # Dev (só db)
├── alembic.ini
└── CLAUDE.md               # Contexto para Claude Code
```

---

## Endpoints da API

Documentação completa em [`docs/API.md`](docs/API.md). Resumo:

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/api/v1/empresas/` | Lista empresas |
| GET | `/api/v1/centros-custo/` | Lista CCs gerenciais |
| POST | `/api/v1/centros-custo/` | Cria CC |
| GET | `/api/v1/contas-gerenciais/` | Lista plano gerencial |
| POST | `/api/v1/contas-gerenciais/` | Cria conta |
| GET | `/api/v1/versoes-orcamento/{ano}` | Lista versões |
| POST | `/api/v1/versoes-orcamento/` | Cria versão |
| GET | `/api/v1/orcamento/{ano}/{id_versao}` | Carrega orçamento |
| POST | `/api/v1/orcamento/` | Salva célula (upsert) |
| GET | `/api/v1/comparativo/{ano}/{id_versao}` | Realizado × Orçado |
| GET | `/api/v1/dre/{ano}/{id_versao}` | DRE gerencial |
| GET | `/api/v1/lancamentos/{YYYY-MM}` | Lançamentos realizados |
| GET | `/api/v1/workflow/` | Lista workflows |
| POST | `/api/v1/workflow/iniciar` | Cria RASCUNHO |
| POST | `/api/v1/workflow/{id}/enviar` | RASCUNHO → ENVIADO |
| POST | `/api/v1/workflow/{id}/aprovar` | ENVIADO → APROVADO |
| POST | `/api/v1/workflow/{id}/reprovar` | ENVIADO → REPROVADO |
| GET | `/api/v1/mapeamentos/contas` | Lista mapeamentos de contas |
| POST | `/api/v1/mapeamentos/contas` | Cria mapeamento |
| GET | `/api/v1/mapeamentos/centros-custo` | Lista mapeamentos de CC |
| POST | `/api/v1/mapeamentos/centros-custo` | Cria mapeamento de CC |

---

## Regras absolutas

1. **Nunca float** — `Decimal` no Python, `NUMERIC(15,2)` no PostgreSQL
2. **SIA é read-only** — zero INSERT/UPDATE/DELETE no banco Firebird
3. **Secrets no .env** — nunca commitar senhas ou tokens
4. **ETL idempotente** — `ON CONFLICT DO UPDATE` em todos os upserts
5. **Filtrar por empresa** — queries no SIA sempre usam `CODEMP` ou equivalente
6. **Escala monetária SIA** — `MOV_VALOR` é `NUMERIC` nativo no Firebird, **não dividir por escala**

---

## Testes

```bash
# Backend
cd api && pytest tests/ -v

# ETL
cd etl && pytest tests/ -v
```

---

## Documentação adicional

| Documento | Conteúdo |
|-----------|---------|
| [`docs/API.md`](docs/API.md) | Todos os endpoints com parâmetros e exemplos |
| [`docs/BANCO_DE_DADOS.md`](docs/BANCO_DE_DADOS.md) | Schema completo, tabelas, índices, views |
| [`docs/ETL.md`](docs/ETL.md) | Pipeline ETL passo a passo, colunas SIA validadas |
| [`docs/DECISOES_TECNICAS.md`](docs/DECISOES_TECNICAS.md) | ADRs, limitações do SIA, estratégias adotadas |
| [`infra/metabase/SETUP.md`](infra/metabase/SETUP.md) | Configuração do Metabase e dashboards |
| [`CLAUDE.md`](CLAUDE.md) | Contexto completo para o Claude Code |
