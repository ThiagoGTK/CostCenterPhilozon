# Banco de Dados — Referência Completa

PostgreSQL 15. Dois schemas: **`dw`** (Data Warehouse — dimensões, fatos, workflow, mapeamentos) e **`app`** (reservado para uso futuro).

Todos os valores monetários usam `NUMERIC(15,2)`. Nunca `FLOAT` ou `REAL`.

---

## Diagrama de Dependências (resumo)

```
dim_empresa ◄─────────────────────────────────────────────────┐
dim_tempo   ◄──────┐                                           │
dim_conta_sia ◄────┤                                           │
dim_conta_gerencial ◄──┬── mapeamento_conta_sia_gerencial      │
dim_centro_custo ◄─────┴── mapeamento_centro_custo_sia_gerencial│
dim_versao_orcamento ◄─┐                                       │
                       │                                       │
fato_lancamento_realizado (id_empresa, id_tempo, id_conta_sia, id_conta_gerencial?, id_centro_custo?)
fato_orcamento            (id_empresa, id_versao, id_conta_gerencial, id_centro_custo)
workflow_orcamento        (id_empresa, id_versao) ─────────────┘
justificativa_variacao    (id_empresa, id_versao, id_conta_gerencial, id_centro_custo)
```

---

## Tabelas de Dimensão

### `dw.dim_empresa`

Espelho das empresas ativas do SIA (`GER_EMPRESAS`). Populada pelo ETL.

| Coluna   | Tipo         | Nullable | Descrição |
|----------|--------------|----------|-----------|
| `id`     | SERIAL PK    | NO       | Autoincrement interno do DW |
| `codemp` | INTEGER UNIQUE | NO     | `EMP_COD` no SIA — chave de negócio |
| `nome`   | VARCHAR(200) | NO       | Nome da empresa |
| `cnpj`   | VARCHAR(18)  | YES      | CNPJ formatado |
| `ativa`  | BOOLEAN      | NO       | `EMP_ATIINA = 'A'` no SIA |

**Empresas Philozon conhecidas:**

| `codemp` | Nome |
|----------|------|
| 1 | Philozon |
| 2 | O3R |
| 3 | Philozon |
| 4 | Philozon |
| 100 | Inativa |

> **Nunca hardcodar `id_empresa = 1`**. O `id` interno do DW é atribuído por autoincrement e pode diferir do `codemp`. O frontend resolve via `VITE_EMPRESA_CODEMP` → `useEmpresaAtiva()`.

---

### `dw.dim_tempo`

Calendário diário. Gerado pelo transformer, não extraído do SIA.

| Coluna      | Tipo          | Nullable | Descrição |
|-------------|---------------|----------|-----------|
| `id`        | SERIAL PK     | NO       | |
| `data`      | DATE UNIQUE   | NO       | Data completa |
| `ano`       | SMALLINT      | NO       | |
| `mes`       | SMALLINT      | NO       | 1–12 |
| `trimestre` | SMALLINT      | NO       | 1–4 |
| `semestre`  | SMALLINT      | NO       | 1–2 |
| `nome_mes`  | VARCHAR(20)   | NO       | Ex: "Janeiro" |

---

### `dw.dim_centro_custo`

Centros de custo **gerenciais** — cadastro interno, independente do SIA. Gerenciados via API.

| Coluna      | Tipo          | Nullable | Descrição |
|-------------|---------------|----------|-----------|
| `id`        | SERIAL PK     | NO       | |
| `codigo`    | VARCHAR(50) UNIQUE | NO  | Código gerencial (ex: "CC01") |
| `nome`      | VARCHAR(200)  | NO       | |
| `descricao` | TEXT          | YES      | |
| `id_pai`    | INTEGER FK    | YES      | Self-referência para hierarquia |
| `ativo`     | BOOLEAN       | NO       | Soft delete |

---

### `dw.dim_conta_gerencial`

Plano de contas **gerencial** — separado do plano contábil do SIA. Cadastro interno, gerenciado via API.

| Coluna              | Tipo          | Nullable | Descrição |
|---------------------|---------------|----------|-----------|
| `id`                | SERIAL PK     | NO       | |
| `codigo`            | VARCHAR(50) UNIQUE | NO  | Ex: "3.01.01" |
| `nome`              | VARCHAR(200)  | NO       | Ex: "Receita Bruta de Vendas" |
| `tipo`              | VARCHAR(30)   | NO       | `RECEITA`, `DESPESA`, `ATIVO`, `PASSIVO`, `RESULTADO` |
| `natureza`          | VARCHAR(10)   | NO       | `DEVEDORA` ou `CREDORA` |
| `id_pai`            | INTEGER FK    | YES      | Self-referência para hierarquia |
| `nivel`             | SMALLINT      | NO       | 1 = raiz, 2 = grupo, 3 = folha |
| `aceita_lancamento` | BOOLEAN       | NO       | `false` para contas-grupo (só agrupam) |
| `ativa`             | BOOLEAN       | NO       | Soft delete |

---

### `dw.dim_conta_sia`

Plano de contas contábil extraído do SIA (`CTB_CONTAS`). Somente leitura — nunca alterar manualmente.

| Coluna         | Tipo          | Nullable | Descrição |
|----------------|---------------|----------|-----------|
| `id`           | SERIAL PK     | NO       | |
| `codpla`       | INTEGER       | NO       | `CON_CODPLA` — plano de contas (Philozon usa 1 e 2) |
| `conta_codigo` | VARCHAR(50)   | NO       | `CON_COD` — código inteiro do SIA |
| `conta_class`  | VARCHAR(50)   | YES      | `CON_CLASS` — código hierárquico legível (ex: "3.01.01") |
| `conta_codsup` | INTEGER       | YES      | `CON_CODSUP` — conta pai |
| `conta_nome`   | VARCHAR(200)  | NO       | `CON_DESC` |
| `conta_tipo`   | VARCHAR(10)   | YES      | `CON_TIPO` |
| `conta_nivel`  | SMALLINT      | YES      | `CON_NIVEL` |

> `CTB_CONTAS` não tem `CODEMP`. O isolamento por empresa é feito via `CON_CODPLA` (planos 1 e 2 = Philozon).

---

### `dw.dim_versao_orcamento`

Versões do orçamento anual.

| Coluna        | Tipo          | Nullable | Descrição |
|---------------|---------------|----------|-----------|
| `id`          | SERIAL PK     | NO       | |
| `ano`         | SMALLINT      | NO       | Ano de referência |
| `tipo`        | VARCHAR(20)   | NO       | `ORIGINAL`, `REVISAO`, `FORECAST` |
| `nome`        | VARCHAR(100)  | NO       | Nome descritivo |
| `descricao`   | TEXT          | YES      | |
| `data_criacao`| DATE          | NO       | |
| `bloqueada`   | BOOLEAN       | NO       | `true` após aprovação — impede edição do orçamento |

---

### `dw.dim_cliente` / `dw.dim_fornecedor`

Auxiliares para análises futuras de receita e despesa.

**`dim_cliente`**: extraído de `GER_CLIDEST`. Campos: `codemp`, `cod_sia`, `nome`, `cnpj_cpf`, `ativo`.

**`dim_fornecedor`**: extraído de `GER_EMITENTES`. **Não tem `CODEMP`** — cadastro global.  
Campos: `cod_sia` (`EMI_COD`), `nome` (`EMI_DESC`), `nome_fantasia`, `cnpj_cpf`, `ativo`.

---

## Tabelas de Fato

### `dw.fato_lancamento_realizado`

Lançamentos contábeis realizados, extraídos de `CTB_MOVIMENTOS` via ETL. **Nunca inserir manualmente.**

| Coluna              | Tipo            | Nullable | Descrição |
|---------------------|-----------------|----------|-----------|
| `id`                | SERIAL PK       | NO       | |
| `id_empresa`        | INTEGER FK      | NO       | → `dim_empresa` |
| `id_tempo`          | INTEGER FK      | NO       | → `dim_tempo` |
| `id_conta_sia`      | INTEGER FK      | NO       | → `dim_conta_sia` |
| `id_conta_gerencial`| INTEGER FK      | YES      | → `dim_conta_gerencial` (NULL se não mapeado) |
| `id_centro_custo`   | INTEGER FK      | YES      | → `dim_centro_custo` (**SEMPRE NULL** — `MOV_CECT = NULL` no SIA) |
| `sia_lancamento_id` | VARCHAR(100) UNIQUE | NO   | Chave de idempotência: `CODEMP_DATA_NUMLAN_CODCON_TIPO` |
| `valor`             | NUMERIC(15,2)   | NO       | Valor absoluto (sem sinal) |
| `tipo_lancamento`   | VARCHAR(1)      | NO       | `D` = Débito, `C` = Crédito |
| `historico`         | VARCHAR(500)    | YES      | `MOV_HIST` |
| `data_referencia`   | DATE            | NO       | `MOV_DATA` |
| `data_carga`        | TIMESTAMP       | NO       | Preenchida automaticamente |

> **`id_centro_custo` é sempre NULL** porque `MOV_CECT = NULL` em todos os lançamentos contábeis do SIA da Philozon. Isso é uma característica do uso do sistema, não um bug. Todas as queries de comparativo devem agregar por `(conta, empresa, período)` ignorando CC.

---

### `dw.fato_orcamento`

Orçamento inserido pelos usuários via frontend/API. Upsert por chave composta.

| Coluna              | Tipo          | Nullable | Descrição |
|---------------------|---------------|----------|-----------|
| `id`                | SERIAL PK     | NO       | |
| `id_empresa`        | INTEGER FK    | NO       | → `dim_empresa` |
| `id_versao`         | INTEGER FK    | NO       | → `dim_versao_orcamento` |
| `id_conta_gerencial`| INTEGER FK    | NO       | → `dim_conta_gerencial` |
| `id_centro_custo`   | INTEGER FK    | NO       | → `dim_centro_custo` |
| `ano`               | SMALLINT      | NO       | |
| `mes`               | SMALLINT      | NO       | 1–12 |
| `valor`             | NUMERIC(15,2) | NO       | |
| `observacao`        | TEXT          | YES      | |
| `criado_por`        | VARCHAR(100)  | YES      | Nome do usuário |
| `criado_em`         | TIMESTAMP     | NO       | |
| `atualizado_em`     | TIMESTAMP     | NO       | Auto-updated |

**Chave de upsert** (único lógico): `(id_empresa, id_versao, id_conta_gerencial, id_centro_custo, ano, mes)`

---

### `dw.fato_receita` / `dw.fato_despesa`

Tabelas de fato auxiliares para receita bruta e despesas agregadas.

**`fato_receita`**: fonte `FIS_MOVIMENTO`. Campos: `receita_bruta`, `deducoes`, `receita_liquida`. Chave: `chave_upsert = empresa+ano+mes+cliente`.

**`fato_despesa`**: fonte `CTB_MOVIMENTOS` + mapeamento gerencial. Agrega por conta + CC. Chave: `chave_upsert`.

---

## Tabelas Operacionais

### `dw.workflow_orcamento`

Ciclo de aprovação do orçamento por versão/empresa.

| Coluna         | Tipo        | Nullable | Descrição |
|----------------|-------------|----------|-----------|
| `id`           | SERIAL PK   | NO       | |
| `id_versao`    | INTEGER FK  | NO       | → `dim_versao_orcamento` |
| `id_empresa`   | INTEGER FK  | NO       | → `dim_empresa` |
| `status`       | VARCHAR(20) | NO       | `RASCUNHO`, `ENVIADO`, `APROVADO`, `REPROVADO` |
| `criado_por`   | VARCHAR(100)| NO       | |
| `enviado_por`  | VARCHAR(100)| YES      | Preenchido na transição RASCUNHO→ENVIADO |
| `aprovado_por` | VARCHAR(100)| YES      | Preenchido na transição ENVIADO→APROVADO |
| `reprovado_por`| VARCHAR(100)| YES      | Preenchido na transição ENVIADO→REPROVADO |
| `data_envio`   | TIMESTAMP   | YES      | |
| `data_decisao` | TIMESTAMP   | YES      | Aprovação ou reprovação |
| `comentario`   | TEXT        | YES      | Obrigatório ao reprovar |
| `criado_em`    | TIMESTAMP   | NO       | |
| `atualizado_em`| TIMESTAMP   | NO       | Auto-updated |

**Transições de estado:**
```
RASCUNHO → ENVIADO   (POST /workflow/{id}/enviar)
ENVIADO  → APROVADO  (POST /workflow/{id}/aprovar) — bloqueia dim_versao_orcamento.bloqueada = true
ENVIADO  → REPROVADO (POST /workflow/{id}/reprovar) — comentario obrigatório
```

---

### `dw.justificativa_variacao`

Justificativas textuais para variações acima de threshold configurado.

| Coluna               | Tipo           | Nullable |
|----------------------|----------------|----------|
| `id`                 | SERIAL PK      | NO       |
| `id_empresa`         | INTEGER FK     | NO       |
| `id_versao`          | INTEGER FK     | NO       |
| `id_conta_gerencial` | INTEGER FK     | NO       |
| `id_centro_custo`    | INTEGER FK     | NO       |
| `ano`, `mes`         | INTEGER        | NO       |
| `valor_orcado`       | NUMERIC(15,2)  | NO       |
| `valor_realizado`    | NUMERIC(15,2)  | NO       |
| `variacao_absoluta`  | NUMERIC(15,2)  | NO       |
| `variacao_percentual`| NUMERIC(8,2)   | NO       |
| `justificativa`      | TEXT           | NO       |
| `criado_por`         | VARCHAR(100)   | NO       |
| `criado_em`          | TIMESTAMP      | NO       |

---

### `dw.mapeamento_conta_sia_gerencial`

De-para: conta contábil SIA → conta gerencial interna. Uma conta SIA mapeia para no máximo uma conta gerencial por empresa (restrição lógica via API — retorna 409 se já existir mapeamento ativo).

| Coluna               | Tipo       | Nullable | Descrição |
|----------------------|------------|----------|-----------|
| `id`                 | SERIAL PK  | NO       | |
| `id_conta_sia`       | INTEGER FK | NO       | → `dim_conta_sia` |
| `id_conta_gerencial` | INTEGER FK | NO       | → `dim_conta_gerencial` |
| `id_empresa`         | INTEGER FK | NO       | → `dim_empresa` |
| `ativo`              | BOOLEAN    | NO       | Soft delete |
| `observacao`         | TEXT       | YES      | |

---

### `dw.mapeamento_centro_custo_sia_gerencial`

De-para: centro de custo SIA → CC gerencial interno.

| Coluna                     | Tipo         | Nullable | Descrição |
|----------------------------|--------------|----------|-----------|
| `id`                       | SERIAL PK    | NO       | |
| `cc_sia_codigo`            | VARCHAR(50)  | NO       | `CC_COD` do SIA (como string) |
| `cc_sia_nome`              | VARCHAR(200) | YES      | `CC_DESC` — denormalizado para UI |
| `id_empresa`               | INTEGER FK   | NO       | → `dim_empresa` |
| `id_centro_custo_gerencial`| INTEGER FK   | NO       | → `dim_centro_custo` |
| `ativo`                    | BOOLEAN      | NO       | Soft delete |
| `observacao`               | TEXT         | YES      | |

> Na prática, o mapeamento de CC é irrelevante para o comparativo porque `id_centro_custo` é sempre NULL em `fato_lancamento_realizado`. O mapeamento existe para uso futuro ou se o SIA vier a registrar CC nos lançamentos.

---

## Views Analíticas (schema `dw`)

Criadas pelas migrations 003 e 004. Disponíveis ao Metabase via role `metabase_reader`.

### `dw.v_lancamentos_detalhado`

Lançamentos com todas as dimensões desnormalizadas (join com empresa, tempo, conta SIA, conta gerencial, CC).

**Campos:** `id`, `sia_lancamento_id`, `data_referencia`, `ano`, `mes`, `nome_mes`, `trimestre`, `semestre`, `id_empresa`, `empresa`, `sia_conta_codigo`, `sia_conta_class`, `sia_conta_nome`, `id_conta_gerencial`, `conta_gerencial_codigo`, `conta_gerencial_nome`, `conta_tipo`, `id_centro_custo`, `cc_codigo`, `cc_nome`, `tipo_lancamento`, `valor`, `valor_liquido` (valor × sinal D/C), `historico`, `data_carga`.

---

### `dw.v_comparativo_mensal`

Realizado × Orçado por mês/conta/versão/empresa. **Corrigida na migration 004** para ignorar CC no join (todos os lançamentos têm `id_centro_custo = NULL`).

**Estratégia:**
1. `realizado_agg` agrega por `(empresa, conta, ano, mes)` sem CC
2. `fato_orcamento` é agrupado somando todos os CCs por `(empresa, conta, versão, mes)`
3. LEFT JOIN por `(empresa, conta, ano, mes)`

**Campos:** `ano`, `mes`, `nome_mes`, `id_versao`, `versao_nome`, `versao_tipo`, `id_empresa`, `empresa_nome`, `id_conta_gerencial`, `conta_codigo`, `conta_nome`, `conta_tipo`, `conta_natureza`, `valor_orcado`, `valor_realizado`, `variacao_absoluta`, `variacao_percentual`.

---

### `dw.v_evolucao_mensal`

Totais mensais de realizado por tipo de conta (`RECEITA`, `DESPESA`, etc.) e empresa.

**Campos:** `ano`, `mes`, `nome_mes`, `trimestre`, `id_empresa`, `empresa`, `conta_tipo`, `valor_realizado`, `qtd_lancamentos`.

---

### `dw.v_dre_anual`

DRE completa com hierarquia de contas, orçado e realizado por ano/versão/empresa.

**Lógica:** CROSS JOIN entre `dim_conta_gerencial × dim_versao_orcamento × dim_empresa`, filtrado por `(o.valor_orcado IS NOT NULL OR r.valor_realizado IS NOT NULL)`. Inclui conta pai (`codigo_pai`, `nome_pai`) para resolução de hierarquia.

**Campos:** `id_conta_gerencial`, `codigo`, `nome`, `tipo`, `natureza`, `nivel`, `id_pai`, `codigo_pai`, `nome_pai`, `id_versao`, `versao_nome`, `ano`, `id_empresa`, `empresa_nome`, `valor_orcado`, `valor_realizado`, `variacao_absoluta`, `variacao_percentual`.

---

### `dw.v_workflow_resumo`

Status dos workflows com nomes de versão e empresa desnormalizados. Inclui `horas_para_decisao` calculado.

**Campos:** `id`, `status`, `id_versao`, `versao_nome`, `versao_ano`, `versao_tipo`, `versao_bloqueada`, `id_empresa`, `empresa_nome`, `criado_por`, `enviado_por`, `aprovado_por`, `reprovado_por`, `data_envio`, `data_decisao`, `comentario`, `criado_em`, `atualizado_em`, `horas_para_decisao`.

---

## Migrations

Sequência linear: `001 → 002 → 003 → 004`

```bash
alembic upgrade head    # aplicar todas
alembic downgrade -1    # reverter uma
alembic current         # ver revisão atual
```

| Revisão | Arquivo | Descrição |
|---------|---------|-----------|
| `001` | `001_initial_schema.py` | Schema inicial — todos os schemas (`dw`, `app`), todas as tabelas, roles (`fpa_user`, `metabase_reader`) |
| `002` | `002_fix_dim_conta_sia_fornecedor.py` | Fix `dim_conta_sia`: rename `codemp→codpla`, adiciona `conta_class`; remove `codemp` de `dim_fornecedor` |
| `003` | `003_views_analiticas.py` | 5 views analíticas para Metabase |
| `004` | `004_fix_comparativo_cc.py` | Corrige `v_comparativo_mensal` — remove join por CC (todos os lançamentos SIA têm `MOV_CECT = NULL`) |

---

## Roles e Permissões

| Role            | Permissões |
|-----------------|------------|
| `fpa_user`      | SELECT, INSERT, UPDATE, DELETE em todo o schema `dw` |
| `metabase_reader` | SELECT em todas as tabelas e views do schema `dw` |

Criados em `infra/postgres/init.sql`. Renovados via `GRANT SELECT ON ALL TABLES IN SCHEMA dw TO metabase_reader` ao final de cada migration que cria novas views.

---

## Índices relevantes

| Tabela | Coluna(s) | Tipo |
|--------|-----------|------|
| `dim_empresa` | `codemp` | UNIQUE |
| `dim_tempo` | `data` | UNIQUE |
| `dim_centro_custo` | `codigo` | UNIQUE |
| `dim_conta_gerencial` | `codigo` | UNIQUE |
| `fato_lancamento_realizado` | `sia_lancamento_id` | UNIQUE |
| `fato_receita` | `chave_upsert` | UNIQUE |
| `fato_despesa` | `chave_upsert` | UNIQUE |
