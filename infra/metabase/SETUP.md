# Metabase — Guia de Configuração

## 1. Subir o ambiente

```bash
# Produção (inclui Metabase)
docker compose up -d

# Verificar se o Metabase subiu (pode demorar ~2 min na primeira vez)
docker compose logs -f metabase
```

Acesse: **http://localhost/metabase**

---

## 2. Configuração inicial (primeira vez)

1. Clique em **"Let's get started"**
2. Crie a conta de administrador (e-mail + senha)
3. Clique em **"Add your data"** → escolha **PostgreSQL**

### Dados da conexão (banco do DW — leitura):

| Campo           | Valor                           |
|-----------------|--------------------------------|
| Nome            | FP&A — Data Warehouse          |
| Host            | `db`                           |
| Port            | `5432`                         |
| Database name   | `financeiro_dw`               |
| Username        | `metabase_reader`              |
| Password        | `metabase_reader_changeme`     |
| Schemas         | `dw` (apenas este)             |

> ⚠️ Em produção, altere a senha do `metabase_reader` antes de expor o Metabase.
> ```sql
> ALTER ROLE metabase_reader PASSWORD 'nova_senha_segura';
> ```

4. Clique em **"Test Connection"** → **"Next"** → **"Finish"**

---

## 3. Views disponíveis no schema `dw`

Criadas pela migration 003. Use-as como fonte nos dashboards:

| View                       | Descrição                                                          |
|----------------------------|--------------------------------------------------------------------|
| `v_lancamentos_detalhado`  | Todos os lançamentos com empresa, conta SIA/gerencial, CC e valor |
| `v_comparativo_mensal`     | Realizado × Orçado por mês, conta e CC — base do comparativo      |
| `v_evolucao_mensal`        | Totais mensais por tipo de conta (RECEITA / DESPESA)               |
| `v_dre_anual`              | DRE com hierarquia de contas, orçado e realizado por ano           |
| `v_workflow_resumo`        | Status dos ciclos de aprovação por versão e empresa                |

---

## 4. Dashboards recomendados

### Dashboard 1 — DRE Gerencial

**Perguntas a criar** (New Question → Native query):
- `questions/01_dre_anual.sql` — Tabela da DRE com valores orçado/realizado
- `questions/02_variacao_por_conta.sql` — Barras de variação % por conta

**Filtros sugeridos:** `versao_nome`, `versao_ano`, `empresa_nome`

---

### Dashboard 2 — Realizado × Orçado Mensal

**Perguntas:**
- `questions/03_comparativo_mensal.sql` — Linha dupla: realizado vs orçado por mês
- `questions/04_variacao_mensal.sql` — Barras de variação absoluta por mês

**Filtros:** `versao_nome`, `conta_tipo`, `cc_nome`, `empresa_nome`

---

### Dashboard 3 — Evolução de Receitas e Despesas

**Perguntas:**
- `questions/05_evolucao_mensal.sql` — Área/linha por tipo de conta ao longo do tempo

**Filtros:** `ano`, `empresa`

---

### Dashboard 4 — Lançamentos Contábeis

**Perguntas:**
- `questions/06_lancamentos_por_conta.sql` — Top contas por valor lançado

**Filtros:** `ano`, `mes`, `empresa`, `conta_tipo`, `cc_nome`

---

## 5. Dicas de configuração do Metabase

### Configurar locale PT-BR
Admin → Localization:
- **Language**: Portuguese (Brazil)
- **Currency**: BRL
- **First day of week**: Segunda-feira

### Agendar refresh de dados
Admin → Databases → FP&A — Data Warehouse → **Sync database schema now**

Para cache automático:
Admin → Caching → Custom → 1 hora (dados mudam via ETL)

### Compartilhar dashboards
- Dashboard → Share → **Enable sharing** para gerar link público
- Dashboard → Subscriptions → agendar envio por e-mail (ex: toda segunda-feira)

---

## 6. Configurar e-mail no Metabase (opcional)

Admin → Email:
- SMTP Host: mesmo do `SMTP_HOST` no `.env`
- SMTP Port: `587`
- From address: `fpa@philozon.com.br`
- Username/Password: credenciais SMTP

---

## 7. Troubleshooting

**Metabase não sobe:**
```bash
docker compose logs metabase | tail -50
# Comum: aguardar mais ~2 min na primeira vez (JVM startup)
```

**Erro "connection refused" ao conectar ao DB:**
```bash
# Verifique se o container db está healthy
docker compose ps
# Espere o healthcheck passar antes de configurar a conexão
```

**Views não aparecem no Metabase:**
```bash
# Rode as migrations primeiro
cd api && alembic upgrade head
# Depois force sync no Metabase: Admin → Databases → Sync now
```
