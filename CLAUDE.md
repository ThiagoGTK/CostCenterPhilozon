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
- **Frontend**: React 18 + TypeScript + Vite + Recharts
- **BI**: Metabase (open-source, conectado ao schema `dw`)
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
- Conexão deve ser feita com `readonly=True` onde suportado

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

### 5. Campos INT64 do SIA precisam de normalização
```python
# Exemplo: CTB_MOVIMENTOS.MOV_VALOR é INT64, escala 100
valor = Decimal(str(valor_int64)) / Decimal("100")
```

O mapa de escalas fica em `etl/transformer.py → ESCALA_MONETARIA`.

### 6. Joins no SIA sempre com CODEMP
```sql
-- CORRETO
JOIN EST_PRODUTO P ON P.PRO_COD = M.MOV_PROCOD AND P.PRO_CODEMP = M.MOV_CODEMP

-- ERRADO — pode retornar dados de outras empresas
JOIN EST_PRODUTO P ON P.PRO_COD = M.MOV_PROCOD
```

---

## Arquitetura de Banco

O PostgreSQL tem dois schemas:

- **`dw`**: Data Warehouse — dimensões, fatos, workflow, mapeamentos.
  Conectado ao Metabase (leitura) e à API (leitura e escrita de orçamento).
- **`app`**: Reservado para tabelas de suporte da aplicação (futuro).

### Tabelas principais (schema `dw`)

**Dimensões:**
- `dim_empresa` — empresas (espelha GER_EMPRESAS do SIA)
- `dim_tempo` — calendário diário
- `dim_centro_custo` — CCs gerenciais (cadastro interno)
- `dim_conta_gerencial` — plano de contas gerencial (cadastro interno)
- `dim_conta_sia` — plano contábil do SIA (espelho, read-only na origem)
- `dim_versao_orcamento` — versões do orçamento (Original, Revisão, Forecast)

**Fatos:**
- `fato_lancamento_realizado` — lançamentos contábeis via ETL (nunca inserção manual)
- `fato_orcamento` — orçamento inserido pelos usuários via API
- `fato_receita` — receita bruta agregada via ETL
- `fato_despesa` — despesas agregadas via ETL

**Operacionais:**
- `workflow_orcamento` — ciclo de aprovação
- `justificativa_variacao` — justificativas obrigatórias para desvios > threshold
- `mapeamento_conta_sia_gerencial` — de-para contas
- `mapeamento_centro_custo_sia_gerencial` — de-para centros de custo

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
```

**TODO crítico antes de usar em produção:**
1. Confirmar nomes reais das colunas de cada tabela do SIA
2. Confirmar escala dos campos monetários por tabela
3. Instalar driver Firebird ODBC no servidor/container

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

## Próximas Fases

- **Fase 2**: ETL real com conexão Firebird + normalização de escalas
- **Fase 3**: CRUD completo de mapeamentos via API
- **Fase 4**: Workflow completo com notificações
- **Fase 5**: Frontend conectado à API real (substituir dados de exemplo)
- **Fase 6**: Dashboards Metabase configurados

---

## Convenções de Código

- Sem comentários óbvios — só onde o "porquê" não é evidente
- Tipagem completa no Python (Mapped[], TypedDict, etc.)
- Pydantic para validação de entrada; nunca validar manualmente
- SQL raw via `text()` apenas para queries analíticas complexas
- Para CRUD simples, usar SQLAlchemy ORM
- TypeScript strict mode no frontend — sem `any`
