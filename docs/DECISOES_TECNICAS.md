# Decisões Técnicas — Architecture Decision Records

Registro das decisões de arquitetura tomadas durante o desenvolvimento da plataforma FP&A, com contexto, alternativas consideradas e justificativas.

---

## ADR-001 — Decimal em vez de Float para valores monetários

**Status:** Aceito  
**Data:** 2025-01

### Contexto

Valores monetários precisam de precisão exata. `float` em Python usa IEEE 754 binary floating-point, que não representa exatamente valores como `0.10` (`0.1 + 0.2 ≠ 0.3`). Para um sistema financeiro, isso é inaceitável.

### Decisão

- Python: sempre `decimal.Decimal`, nunca `float`
- PostgreSQL: sempre `NUMERIC(15,2)`, nunca `FLOAT`, `REAL` ou `DOUBLE PRECISION`
- SQLAlchemy: coluna `NUMERIC(15,2)` mapeada automaticamente para `Decimal`
- Pydantic: serializa `Decimal` como string numérica (ex: `"15000.00"`)
- Frontend: `Number(valor)` apenas no momento de exibição/cálculo; armazenado como string

### Alternativas descartadas

- `float` — precisão insuficiente para finanças
- `int` (centavos) — mais difícil de debugar, conversões implícitas em todo lugar

### Consequências

Toda função que manipula valor monetário deve importar e usar `Decimal`. Qualquer `float` no código é um bug.

---

## ADR-002 — SIA é somente leitura

**Status:** Aceito  
**Data:** 2025-01

### Contexto

O SIA (System SIA, ERP em Firebird) é o sistema de registro oficial da empresa. Qualquer escrita incorreta pode corromper dados contábeis e fiscais, com impacto legal.

### Decisão

A conexão ao Firebird é configurada com `readonly=True`. O ETL só executa `SELECT`. Nenhum INSERT, UPDATE ou DELETE é permitido no SIA.

### Como isso é garantido

```python
# extractor.py
self._conn = pyodbc.connect(conn_str, autocommit=False, readonly=True)
```

O `readonly=True` do pyodbc sinaliza ao driver que é uma conexão somente leitura. Qualquer tentativa de escrita levantaria exceção no nível do driver.

### Consequências

Todo dado de planejamento (orçamento, mapeamentos, workflow) fica exclusivamente no PostgreSQL DW, nunca no SIA.

---

## ADR-003 — `MOV_CECT = NULL` — nenhum lançamento tem centro de custo

**Status:** Aceito  
**Data:** 2026-05

### Contexto

Durante a análise dos dados, foi constatado via MCP Firebird que **100% dos lançamentos em `CTB_MOVIMENTOS` têm `MOV_CECT = NULL`** para as empresas Philozon. Isso significa que o SIA não está sendo usado para registrar o CC nos lançamentos contábeis — os lançamentos são apenas por conta.

### Investigação

Consultado diretamente via:
```sql
SELECT COUNT(*) FROM CTB_MOVIMENTOS WHERE MOV_CODEMP = 1 AND MOV_CECT IS NOT NULL
-- Resultado: 0
```

### Impacto

A query original do comparativo fazia:
```sql
LEFT JOIN fato_lancamento_realizado lr ON lr.id_centro_custo = fo.id_centro_custo
```
Como `id_centro_custo` é sempre `NULL` e `NULL ≠ NULL` em SQL, o join **nunca casava** — `valor_realizado` retornava zero para todos os registros.

### Decisão

A estratégia correta para o comparativo Realizado × Orçado:

1. **Realizado**: agregar por `(conta_gerencial, empresa, ano, mes)` — ignorar CC
2. **Orçado**: somar todos os CCs da mesma conta-mes (`SUM(fo.valor)` sem filtrar CC)
3. **JOIN**: apenas por `(conta_gerencial, ano, mes)` (+ empresa quando filtrado)
4. **Output**: `centro_custo_codigo = NULL`, `centro_custo_nome = NULL` — documentado na API

### Implementação

- `api/routers/comparativo.py`: CTE `realizado_agg` sem CC, GROUP BY sem CC
- `migrations/004_fix_comparativo_cc.py`: corrige `v_comparativo_mensal`
- `api/schemas/comparativo.py`: campos CC declarados como `str | None = None`
- `frontend/src/services/api.ts`: `centro_custo_nome: string | null`

### Nota sobre o filtro CC no orçado

O filtro `id_centro_custo` na API do comparativo ainda funciona para o **orçado** (filtra quais CCs do orçamento entram na soma). O realizado não tem CC — é sempre o total da conta.

### Consequências

O campo `centro_custo_nome` é sempre `null` na resposta do comparativo. Isso é documentado e esperado. Se o SIA vier a registrar CCs no futuro, a estratégia precisaria ser revisada — mas a view `v_comparativo_mensal` na migration 004 teria que ser atualizada com uma nova migration.

---

## ADR-004 — Multi-empresa: filtro `id_empresa` deve ser aplicado nos dois lados

**Status:** Aceito  
**Data:** 2026-05

### Contexto

A plataforma suporta múltiplas empresas (`dim_empresa`). Quando o frontend filtra por empresa, é crítico que o filtro seja aplicado **tanto no realizado quanto no orçado**.

### O bug

A versão inicial do `realizado_agg` agrupava por `(conta, empresa, mes)`. O JOIN externo agrupava por `(conta, mes)` sem empresa. Com múltiplas empresas:

- empresa=1: realizado=300
- empresa=3: realizado=80
- `MAX(r.valor_realizado)` retornava 300 em vez de 380 (se consolidado) ou 300/80 separados

### A correção

Remover `id_empresa` do GROUP BY do CTE e aplicar o filtro dentro do WHERE do CTE:

```sql
WITH realizado_agg AS (
    SELECT id_conta_gerencial, ano, mes,
           SUM(valor * ...) AS valor_realizado
    FROM dw.fato_lancamento_realizado
    WHERE id_conta_gerencial IS NOT NULL
      AND (:id_empresa IS NULL OR id_empresa = :id_empresa)  -- filtro aqui
    GROUP BY id_conta_gerencial, ano, mes                    -- sem empresa
)
```

- Com `id_empresa = X`: o CTE agrega apenas a empresa X → uma linha por (conta, mes) → correto
- Sem filtro (`id_empresa IS NULL`): o CTE agrega todas as empresas → visão consolidada → correto

### Consequências

O filtro `id_empresa` deve sempre ser passado nas chamadas do frontend. O hook `useEmpresaAtiva()` resolve automaticamente o `id` correto a partir de `VITE_EMPRESA_CODEMP`. Nunca hardcodar `id_empresa = 1`.

---

## ADR-005 — `VITE_EMPRESA_CODEMP` em vez de hardcodar `id_empresa`

**Status:** Aceito  
**Data:** 2026-05

### Contexto

O campo `id` da tabela `dim_empresa` é autoincrement do DW, não previsível. O código SIA da empresa (`codemp`) é estável e definido no ERP. O frontend precisa de um jeito de saber qual empresa usar sem hardcodar um ID interno.

### Decisão

`VITE_EMPRESA_CODEMP` é definido no `.env` do frontend com o `EMP_COD` da empresa principal (ex: `1` para Philozon).

O hook `useEmpresaAtiva()` busca `GET /empresas/` na inicialização e encontra a empresa cujo `codemp === VITE_EMPRESA_CODEMP`. Retorna o `id` do DW correspondente.

```typescript
// hooks/useDimensoes.ts
export function useEmpresaAtiva() {
  const codemp = Number(import.meta.env.VITE_EMPRESA_CODEMP);
  const { data: empresas = [] } = useEmpresas();
  const empresa = empresas.find((e) => e.codemp === codemp);
  return { idEmpresa: empresa?.id ?? null, empresa };
}
```

### Alternativas descartadas

- Hardcodar `id_empresa = 1` — frágil: o ID pode mudar entre ambientes
- Passar empresa via URL — complexidade desnecessária para uso monoempresa

### Consequências

Todo componente que faz chamadas filtradas por empresa deve usar `useEmpresaAtiva()`. Nenhum valor de `id_empresa` deve ser hardcodado no frontend.

---

## ADR-006 — Sem autenticação na versão atual

**Status:** Aceito (revisitar em produção multi-usuário)  
**Data:** 2025-01

### Contexto

A plataforma é de uso interno, acessível apenas na rede da empresa. Implementar autenticação completa (OAuth, JWT, RBAC) adicionaria complexidade significativa.

### Decisão

A API não implementa autenticação. Em produção:
- Nginx protege o acesso com autenticação básica (HTTP Basic Auth) ou a rede está atrás de VPN
- Todos os endpoints são acessíveis para qualquer usuário autenticado via rede

### Campos "criado_por" / "aprovado_por"

Os campos de auditoria (`criado_por`, `enviado_por`, `aprovado_por`) são strings livres enviadas pelo frontend — não há validação de identidade. São apenas para rastreabilidade informativa.

### Quando revisar

Se a plataforma crescer para uso multi-usuário com controle de acesso granular (ex: gestor pode aprovar, analista só lança), implementar JWT + RBAC.

---

## ADR-007 — Plano gerencial separado do contábil SIA

**Status:** Aceito  
**Data:** 2025-01

### Contexto

O plano de contas do SIA (`CTB_CONTAS`) é contábil — segue as regras do SPED e da contabilidade fiscal brasileira. Para análise gerencial, o ideal é um plano simplificado e orientado para tomada de decisão.

### Decisão

Dois planos paralelos:
- `dim_conta_sia` — espelho do SIA (contábil, leitura)
- `dim_conta_gerencial` — cadastro interno (gerencial, read/write via API)

A conexão entre os dois é feita pela tabela `mapeamento_conta_sia_gerencial`:
```
CTB_CONTAS (SIA) → dim_conta_sia → mapeamento → dim_conta_gerencial
```

O ETL usa esse mapeamento para popular `id_conta_gerencial` em `fato_lancamento_realizado`.

### Consequências

Contas não mapeadas têm `id_conta_gerencial = NULL` no fato. Elas aparecem nos lançamentos mas não no comparativo gerencial. O usuário deve cadastrar os mapeamentos antes de usar o comparativo.

---

## ADR-008 — Versionamento do orçamento

**Status:** Aceito  
**Data:** 2025-01

### Contexto

Um orçamento anual passa por múltiplas revisões ao longo do ano (original, revisões, forecast trimestral). É necessário manter histórico de cada versão para comparação.

### Decisão

`dim_versao_orcamento` com `tipo ∈ {ORIGINAL, REVISAO, FORECAST}`. Cada versão tem uma flag `bloqueada` que é ativada ao aprovar via workflow, impedindo edições retroativas.

O comparativo sempre recebe `id_versao` explicitamente — nunca assume "a versão mais recente".

---

## ADR-009 — SQL raw para queries analíticas complexas

**Status:** Aceito  
**Data:** 2025-01

### Contexto

Queries do comparativo, DRE e lançamentos envolvem CTEs, CASE WHEN, EXTRACT, GROUP BY complexos. O ORM do SQLAlchemy dificulta expressá-los de forma legível.

### Decisão

- CRUD simples (dimensões, workflow) → SQLAlchemy ORM
- Queries analíticas (comparativo, DRE, lançamentos) → `sqlalchemy.text()` com SQL raw

```python
# Para CRUD simples
empresa = db.get(DimEmpresa, id)

# Para queries analíticas
rows = db.execute(text("WITH ... SELECT ..."), {"param": value}).mappings().all()
```

### Consequências

SQL analítico deve ser testado diretamente no PostgreSQL antes de integrar ao router. Parâmetros devem usar `:nome` (não `?`) — SQLAlchemy converte para o driver correto.

---

## ADR-010 — `fato_lancamento_realizado` vs views agregadas

**Status:** Aceito  
**Data:** 2025-01

### Contexto

Poderíamos agregar os lançamentos diretamente no ETL e carregar apenas totais mensais. Isso simplificaria as queries, mas perderia granularidade.

### Decisão

Carregar lançamentos individuais em `fato_lancamento_realizado` e agregar sob demanda via SQL e views. As views `v_comparativo_mensal`, `v_evolucao_mensal`, etc. materializam as agregações comuns para o Metabase.

### Consequências

- `fato_lancamento_realizado` pode crescer rapidamente (centenas de milhares de linhas por ano)
- Queries analíticas precisam de GROUP BY — as views do Metabase são a solução
- Para auditoria, o endpoint `GET /lancamentos/{mes_referencia}` retorna até 500 lançamentos individuais
