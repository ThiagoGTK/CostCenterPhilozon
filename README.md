# FP&A Financeiro — Plataforma de Planejamento Orçamentário

Plataforma interna de FP&A (Financial Planning & Analysis) com:
- Orçamento anual com versionamento (Original, Revisão, Forecast)
- Acompanhamento Realizado × Orçado
- Workflow de aprovação
- BI financeiro via Metabase
- ETL do ERP System SIA (read-only)

---

## Pré-requisitos

- Docker e Docker Compose (v2.x)
- Python 3.11+
- Node.js 20+
- Driver ODBC Firebird (para o ETL conectar ao SIA)

---

## Setup — Desenvolvimento

### 1. Variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com as credenciais reais (nunca commitar o .env!)
```

### 2. Subir o banco de dados (dev)

```bash
docker compose -f docker-compose.dev.yml up -d
```

O PostgreSQL ficará disponível em `localhost:5432`.

### 3. Backend (API FastAPI)

```bash
cd api
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt

# Rodar migrations
cd ..
alembic upgrade head

# Iniciar API
cd api
uvicorn api.main:app --reload --port 8000
```

Acesse: http://localhost:8000/docs

### 4. Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:3000

### 5. ETL (teste local)

```bash
cd etl
pip install -r requirements.txt
python pipeline.py --ano 2025 --mes 1
```

---

## Deploy — Produção

```bash
cp .env.example .env
# Configure .env com credenciais de produção

docker compose up -d --build
```

Serviços:
| Serviço   | URL                          |
|-----------|------------------------------|
| Frontend  | http://servidor/             |
| API       | http://servidor/api/v1/      |
| API Docs  | http://servidor/docs         |
| Metabase  | http://servidor/metabase/    |

---

## Estrutura de Pastas

```
financeiro-fpa/
├── api/                 # Backend FastAPI
│   ├── main.py          # App entry point
│   ├── config.py        # Configurações via .env
│   ├── db/              # SQLAlchemy engine e session
│   ├── models/          # Modelos ORM (dimensões, fatos, workflow)
│   ├── schemas/         # Pydantic schemas (request/response)
│   ├── routers/         # Endpoints REST
│   ├── services/        # Regras de negócio
│   └── tests/           # Testes pytest
├── etl/                 # Pipeline ETL SIA → DW
│   ├── config.py        # Configuração ETL
│   ├── extractor.py     # Extração do SIA (read-only)
│   ├── transformer.py   # Normalização e transformação
│   ├── loader.py        # Carga idempotente no DW
│   ├── pipeline.py      # Orquestrador
│   └── queries/         # SQL de extração por módulo
├── frontend/            # React + TypeScript
│   └── src/
│       ├── components/  # Layout, UI components
│       ├── pages/       # Dashboard, Orçamento, Comparativo, etc.
│       └── services/    # API client e formatadores
├── migrations/          # Alembic migrations
├── infra/               # Nginx, init.sql
└── metabase/            # Config e dashboards exportados
```

---

## Testes

```bash
# Testes da API (regras monetárias, schemas)
cd api
pytest tests/ -v

# Testes do ETL (transformação, idempotência)
cd etl
pytest tests/ -v
```

---

## Regras de Desenvolvimento

1. **Float nunca** — sempre `Decimal` no Python, `NUMERIC(15,2)` no PostgreSQL.
2. **SIA é read-only** — nunca INSERT/UPDATE/DELETE no banco SIA.
3. **Secrets no .env** — nunca commitar credenciais.
4. **ETL idempotente** — `ON CONFLICT DO UPDATE` em todos os upserts.
5. **Filtrar por empresa** — toda query no SIA usa `CODEMP`.
6. **Escala INT64** — campos monetários do SIA são divididos por 100 (confirmar por tabela).

---

## Endpoints Principais

| Método | Endpoint                              | Descrição                    |
|--------|---------------------------------------|------------------------------|
| GET    | `/health`                             | Health check                 |
| GET    | `/api/v1/centros-custo`               | Lista CCs gerenciais         |
| POST   | `/api/v1/centros-custo`               | Cria CC gerencial            |
| GET    | `/api/v1/contas-gerenciais`           | Lista plano gerencial        |
| GET    | `/api/v1/versoes-orcamento/{ano}`     | Versões do orçamento         |
| GET    | `/api/v1/orcamento/{ano}/{id_versao}` | Lançamentos de orçamento     |
| POST   | `/api/v1/orcamento`                   | Lança/atualiza orçamento     |
| GET    | `/api/v1/comparativo/{ano}/{versao}`  | Realizado × Orçado           |
| GET    | `/api/v1/dre/{ano}/{versao}`          | DRE gerencial                |
| POST   | `/api/v1/workflow/enviar`             | Envia para aprovação         |
| POST   | `/api/v1/workflow/aprovar`            | Aprova orçamento             |
| POST   | `/api/v1/workflow/reprovar`           | Reprova orçamento            |
