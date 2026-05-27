# Como Rodar o Projeto com Docker

Guia passo a passo para subir a plataforma FP&A Philozon no servidor usando Docker Compose.

---

## Pré-requisitos

Instale no servidor antes de começar:

| Software | Versão mínima | Verificar |
|----------|--------------|-----------|
| Docker | 24+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | qualquer | `git --version` |
| Node.js | 18+ | `node --version` *(apenas para build do frontend)* |

> **Windows Server / Desktop:** instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/) que inclui tudo acima.

---

## 1. Clonar o repositório

```bash
git clone https://github.com/ThiagoGTK/CostCenterPhilozon.git financeiro-fpa
cd financeiro-fpa
```

---

## 2. Criar o arquivo `.env`

Copie o modelo e preencha com os valores reais:

```bash
cp .env.example .env
```

Abra o `.env` e substitua **todos** os campos marcados com `TROCAR`:

```env
# ── PostgreSQL (banco interno do FP&A) ────────────────────────
DW_PASSWORD=uma_senha_forte_aqui          # OBRIGATÓRIO

# ── SIA / ERP Firebird (somente leitura) ──────────────────────
SIA_HOST=192.168.70.13                    # IP do servidor SIA Firebird
SIA_PORT=3050                             # Porta padrão Firebird
SIA_DATABASE=/syspro/bd/sysdb.fbd        # Caminho do .fbd no servidor SIA
SIA_USER=PHILOZON                         # Usuário do SIA
SIA_PASSWORD=senha_do_sia                 # OBRIGATÓRIO para o ETL
SIA_ROLE=RLCONSULTA                       # Role de somente leitura do SIA
SIA_CODEMP=1                              # EMP_COD da empresa principal

# ── Metabase ───────────────────────────────────────────────────
MB_DB_PASS=senha_para_metabase            # OBRIGATÓRIO

# ── E-mail (opcional — deixe EMAIL_ENABLED=false para desligar) ─
EMAIL_ENABLED=false
```

> **Segurança:** nunca commite o `.env` com senhas reais. Ele já está no `.gitignore`.

---

## 3. Build do frontend

O Nginx serve o frontend como arquivos estáticos. Gere o build **uma vez** (ou após cada atualização de código):

```bash
cd frontend
npm install
npm run build
cd ..
```

Isso cria a pasta `frontend/dist/` que o Nginx vai servir.

---

## 4. Subir os containers

```bash
docker compose up -d
```

Isso inicia 5 serviços:

| Container | Função |
|-----------|--------|
| `fpa_db` | PostgreSQL 15 — banco de dados |
| `fpa_api` | FastAPI — backend / API REST |
| `fpa_etl` | Python — pipeline ETL (execução sob demanda) |
| `fpa_metabase` | Metabase v0.50 — BI e dashboards |
| `fpa_nginx` | Nginx — proxy reverso e frontend |

Aguarde cerca de **1–2 minutos** para todos os serviços ficarem saudáveis:

```bash
docker compose ps
```

Todos devem aparecer como `running` ou `healthy`.

---

## 5. Rodar as migrations (primeira vez)

Crie todas as tabelas do banco:

```bash
docker compose exec api alembic upgrade head
```

Saída esperada:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, schema inicial
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, fix dim_conta_sia
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, views analiticas
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, fix comparativo cc
```

---

## 6. Acessar o sistema

Tudo roda na **porta 80** do servidor, pelo Nginx:

| URL | O que é |
|-----|---------|
| `http://IP_DO_SERVIDOR/` | Frontend React (FP&A) |
| `http://IP_DO_SERVIDOR/api/v1/docs` | Documentação interativa da API (Swagger) |
| `http://IP_DO_SERVIDOR/metabase/` | Metabase BI |

> Substitua `IP_DO_SERVIDOR` pelo IP ou hostname da máquina.

---

## 7. Configurar o Metabase (primeira vez)

1. Acesse `http://IP_DO_SERVIDOR/metabase/`
2. Siga o wizard de configuração inicial
3. Na etapa **"Adicionar seus dados"**, conecte ao PostgreSQL:
   - **Host:** `db` *(nome do container interno)*
   - **Porta:** `5432`
   - **Banco:** `financeiro_dw`
   - **Usuário:** `metabase_reader`
   - **Senha:** `metabase_reader_changeme` → **troque isso depois!**
4. Selecione o schema **`dw`** — as views analíticas já estão criadas

> Para alterar a senha do `metabase_reader`:
> ```bash
> docker compose exec db psql -U fpa_user -d financeiro_dw -c \
>   "ALTER ROLE metabase_reader PASSWORD 'nova_senha_aqui';"
> ```

---

## 8. Executar o ETL

O ETL extrai dados do SIA e popula o banco FP&A. Execute **após** configurar as credenciais SIA no `.env`:

```bash
# Carregar um mês específico
docker compose run --rm etl python pipeline.py --ano 2025 --mes 1

# Carregar o mês atual (usa variáveis do .env)
docker compose run --rm etl python pipeline.py

# Forçar empresa específica (sobrescreve SIA_CODEMP)
docker compose run --rm etl python pipeline.py --ano 2025 --mes 1 --codemp 3
```

Para carregar um ano inteiro:

```bash
for mes in 1 2 3 4 5 6 7 8 9 10 11 12; do
  docker compose run --rm etl python pipeline.py --ano 2025 --mes $mes
done
```

---

## Comandos do dia a dia

```bash
# Ver status dos containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f api
docker compose logs -f etl

# Reiniciar um serviço específico
docker compose restart api

# Parar tudo (preserva os dados)
docker compose down

# Parar tudo E apagar os volumes (CUIDADO — apaga o banco!)
docker compose down -v

# Atualizar após novo git pull
git pull
cd frontend && npm run build && cd ..
docker compose up -d --build
docker compose exec api alembic upgrade head
```

---

## Atualização de versão

Sempre que houver novo código no repositório:

```bash
# 1. Baixar as mudanças
git pull origin main

# 2. Rebuild do frontend (se houve mudanças no frontend/)
cd frontend && npm run build && cd ..

# 3. Rebuild e reinício dos containers (se houve mudanças em api/ ou etl/)
docker compose up -d --build

# 4. Rodar migrations (se houve novas migrations)
docker compose exec api alembic upgrade head
```

---

## Troubleshooting

### Container não sobe / fica em `unhealthy`

```bash
# Ver os logs do container com problema
docker compose logs api
docker compose logs db
```

**Erro: `DW_PASSWORD obrigatorio`**
→ O arquivo `.env` não foi criado ou está faltando a variável `DW_PASSWORD`.

**Erro: `could not connect to server`**
→ O container `db` ainda está inicializando. Aguarde 30 segundos e tente novamente.

---

### Migration falha

```bash
# Ver revisão atual
docker compose exec api alembic current

# Reverter a última migration (se necessário)
docker compose exec api alembic downgrade -1
```

---

### Frontend mostra tela em branco

O build pode estar desatualizado. Refaça:
```bash
cd frontend && npm run build && cd ..
docker compose restart nginx
```

---

### ETL não conecta ao SIA

Verifique no `.env`:
- `SIA_HOST` aponta para o IP correto do servidor SIA
- `SIA_PORT` é `3050` (padrão Firebird)
- O servidor FP&A consegue acessar o SIA na rede (teste com `ping SIA_HOST`)
- O driver ODBC Firebird está instalado no container ETL (já incluso no `Dockerfile`)

---

## Arquitetura de rede

```
Usuário (navegador)
       ↓ porta 80
   [Nginx :80]
   ├── /           → frontend/dist/ (React estático)
   ├── /api/       → fpa_api:8000 (FastAPI)
   └── /metabase/  → fpa_metabase:3000 (Metabase)

   [fpa_api] ──────→ [fpa_db:5432] (PostgreSQL)
   [fpa_etl] ──────→ [fpa_db:5432] (PostgreSQL)
   [fpa_etl] ──────→ SIA:3050 (Firebird, somente leitura)
   [fpa_metabase] → [fpa_db:5432] (banco metabase + schema dw)
```

---

*Dúvidas: consulte o `README.md` ou a pasta `docs/` para documentação detalhada de cada componente.*
