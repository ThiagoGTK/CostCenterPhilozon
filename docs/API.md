# API — Referência Completa

Base URL: `http://servidor/api/v1`  
Documentação interativa (Swagger): `http://servidor/docs`

Todos os valores monetários são retornados como `string` numérica com precisão de 2 casas decimais (NUMERIC do PostgreSQL serializado via Pydantic).

---

## Sistema

### `GET /health`
Retorna status da API.

```json
{ "status": "ok", "env": "production" }
```

---

## Empresas

### `GET /empresas/`
Lista empresas cadastradas (espelho de `GER_EMPRESAS` do SIA).

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `apenas_ativas` | bool | `true` | Filtrar só ativas |

**Resposta:**
```json
[
  { "id": 1, "codemp": 1, "nome": "Philozon", "ativa": true },
  { "id": 2, "codemp": 3, "nome": "Philozon", "ativa": true }
]
```

> **Nota:** `id` é o autoincrement do DW. `codemp` é o `EMP_COD` no SIA. O frontend resolve o `id` correto via `VITE_EMPRESA_CODEMP` → `useEmpresaAtiva()`. Nunca hardcodar `id_empresa = 1`.

---

## Centros de Custo

### `GET /centros-custo/`
| Parâmetro | Tipo | Padrão |
|-----------|------|--------|
| `apenas_ativos` | bool | `true` |

```json
[{ "id": 1, "codigo": "CC01", "nome": "Comercial", "ativo": true, "id_pai": null }]
```

### `POST /centros-custo/`
```json
{ "codigo": "CC02", "nome": "Administrativo", "descricao": null, "id_pai": null }
```

### `PUT /centros-custo/{id}`
Campos opcionais: `nome`, `descricao`, `ativo`.

### `DELETE /centros-custo/{id}`
Soft delete — define `ativo = false`.

---

## Contas Gerenciais

### `GET /contas-gerenciais/`
| Parâmetro | Tipo | Padrão |
|-----------|------|--------|
| `tipo` | string | — | Filtrar por tipo (`RECEITA`, `DESPESA`, …) |
| `apenas_ativas` | bool | `true` |

```json
[{
  "id": 5,
  "codigo": "3.01.01",
  "nome": "Receita Bruta de Vendas",
  "tipo": "RECEITA",
  "natureza": "CREDORA",
  "nivel": 3,
  "id_pai": 3,
  "aceita_lancamento": true,
  "ativa": true
}]
```

### `POST /contas-gerenciais/`
Campos obrigatórios: `codigo`, `nome`, `tipo`, `natureza`.  
`tipo` ∈ `{RECEITA, DESPESA, ATIVO, PASSIVO, RESULTADO}`  
`natureza` ∈ `{DEVEDORA, CREDORA}`

### `PUT /contas-gerenciais/{id}` / `DELETE /contas-gerenciais/{id}`

---

## Versões de Orçamento

### `GET /versoes-orcamento/{ano}`
```json
[{
  "id": 1,
  "ano": 2025,
  "tipo": "ORIGINAL",
  "nome": "Orçamento Original 2025",
  "descricao": null,
  "data_criacao": "2025-01-01",
  "bloqueada": false
}]
```

### `POST /versoes-orcamento/`
```json
{
  "ano": 2025,
  "tipo": "ORIGINAL",
  "nome": "Orçamento Original 2025",
  "descricao": "Primeira versão aprovada"
}
```
`tipo` ∈ `{ORIGINAL, REVISAO, FORECAST}`

---

## Orçamento

### `GET /orcamento/{ano}/{id_versao}`
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id_empresa` | int | Filtrar por empresa |
| `id_centro_custo` | int | Filtrar por CC |

Retorna lista de células do orçamento (uma por conta × CC × mês).

### `POST /orcamento/`
Cria ou atualiza uma célula (upsert por `id_empresa + id_versao + id_conta_gerencial + id_centro_custo + ano + mes`).

```json
{
  "id_empresa": 1,
  "id_versao": 1,
  "id_conta_gerencial": 5,
  "id_centro_custo": 2,
  "ano": 2025,
  "mes": 1,
  "valor": "15000.00",
  "observacao": null
}
```

Retorna `409` se a versão estiver bloqueada.

---

## Comparativo Realizado × Orçado

### `GET /comparativo/{ano}/{id_versao}`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id_empresa` | int | **Recomendado.** Filtra orçado e realizado pela empresa. Sem filtro = visão consolidada de todas as empresas. |
| `id_centro_custo` | int | Filtra o orçado pelo CC (realizado sempre cobre o total, pois SIA não registra CC nos lançamentos) |

**Resposta:**
```json
{
  "ano": 2025,
  "id_versao": 1,
  "nome_versao": "Orçamento Original 2025",
  "itens": [
    {
      "mes": 1,
      "conta_gerencial_codigo": "3.01.01",
      "conta_gerencial_nome": "Receita Bruta",
      "centro_custo_codigo": null,
      "centro_custo_nome": null,
      "valor_orcado": "15000.00",
      "valor_realizado": "12500.50",
      "variacao_absoluta": "-2499.50",
      "variacao_percentual": "-16.66"
    }
  ],
  "total_orcado": "180000.00",
  "total_realizado": "150006.00",
  "variacao_absoluta_total": "-29994.00",
  "variacao_percentual_total": "-16.66"
}
```

> **Por que `centro_custo_codigo/nome` é `null`?**  
> Todos os lançamentos contábeis no SIA da Philozon têm `MOV_CECT = NULL` — o sistema não registra CC nos lançamentos. O realizado é, portanto, agregado apenas por conta + empresa + período. O orçado é somado em todos os CCs para a mesma conta-mês. Ver [`DECISOES_TECNICAS.md`](DECISOES_TECNICAS.md).

---

## DRE Gerencial

### `GET /dre/{ano}/{id_versao}`
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id_empresa` | int | Filtrar por empresa |

```json
{
  "ano": 2025,
  "id_versao": 1,
  "linhas": [
    {
      "id": 1,
      "codigo": "3",
      "nome": "RECEITAS",
      "tipo": "RECEITA",
      "natureza": "CREDORA",
      "nivel": 1,
      "id_pai": null,
      "valor_orcado": "180000.00",
      "valor_realizado": "150006.00"
    }
  ]
}
```

Retorna todas as contas gerenciais ativas com seus totais anuais (orçado e realizado). A hierarquia é resolvida no frontend via `id_pai`.

---

## Lançamentos Realizados

### `GET /lancamentos/{mes_referencia}`
Formato: `YYYY-MM` (ex: `2025-01`)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `id_empresa` | int | Filtrar por empresa |
| `id_conta_gerencial` | int | Filtrar por conta gerencial |

Retorna até 500 lançamentos (uso diagnóstico / auditoria).

---

## Mapeamentos

### `GET /mapeamentos/contas`
| Parâmetro | Tipo |
|-----------|------|
| `id_empresa` | int |

```json
[{
  "id": 1,
  "id_conta_sia": 42,
  "id_conta_gerencial": 5,
  "id_empresa": 1,
  "ativo": true,
  "conta_sia": {
    "id": 42,
    "conta_codigo": "312",
    "conta_class": "3.01.01",
    "conta_nome": "RECEITA BRUTA DE VENDAS"
  }
}]
```

### `POST /mapeamentos/contas`
```json
{ "id_conta_sia": 42, "id_conta_gerencial": 5, "id_empresa": 1 }
```
Retorna `409` se já existir mapeamento ativo para a conta SIA.

### `DELETE /mapeamentos/contas/{id}` — desativa (soft delete)

### `GET /mapeamentos/centros-custo`
```json
[{
  "id": 1,
  "cc_sia_codigo": "10",
  "cc_sia_nome": "Vendas",
  "id_empresa": 1,
  "id_centro_custo_gerencial": 2,
  "ativo": true
}]
```

### `POST /mapeamentos/centros-custo`
```json
{ "cc_sia_codigo": "10", "cc_sia_nome": "Vendas", "id_empresa": 1, "id_centro_custo_gerencial": 2 }
```

### `DELETE /mapeamentos/centros-custo/{id}` — desativa

---

## Workflow de Aprovação

### `GET /workflow/`
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `ano` | int | Filtrar por ano da versão |

```json
[{
  "id": 1,
  "id_versao": 1,
  "id_empresa": 1,
  "versao_nome": "Orçamento Original 2025",
  "versao_ano": 2025,
  "empresa_nome": "Philozon",
  "status": "ENVIADO",
  "criado_por": "Ana Silva",
  "enviado_por": "Ana Silva",
  "aprovado_por": null,
  "reprovado_por": null,
  "data_envio": "2025-02-10T09:30:00",
  "data_decisao": null,
  "comentario": null,
  "criado_em": "2025-02-08T14:00:00",
  "atualizado_em": "2025-02-10T09:30:00"
}]
```

### `GET /workflow/{id}` — detalhe

### `POST /workflow/iniciar`
Cria registro em status `RASCUNHO`. Retorna `409` se já existir workflow ativo (RASCUNHO ou ENVIADO) para a mesma versão+empresa.

```json
{ "id_versao": 1, "id_empresa": 1, "criado_por": "Ana Silva" }
```

### `POST /workflow/{id}/enviar`
Transição `RASCUNHO → ENVIADO`. Dispara e-mail para aprovadores em background.

```json
{ "enviado_por": "Ana Silva" }
```

### `POST /workflow/{id}/aprovar`
Transição `ENVIADO → APROVADO`. Bloqueia a versão (`bloqueada = true`). Dispara e-mail.

```json
{ "aprovado_por": "Carlos Gestor", "comentario": "Aprovado conforme reunião." }
```

### `POST /workflow/{id}/reprovar`
Transição `ENVIADO → REPROVADO`. Dispara e-mail.

```json
{ "reprovado_por": "Carlos Gestor", "comentario": "Reduzir despesas de TI em 10%." }
```
O campo `comentario` é **obrigatório** ao reprovar.

### `GET /workflow/{id}/justificativas` — lista justificativas de variação

### `POST /workflow/{id}/justificativas`
```json
{
  "id_empresa": 1,
  "id_versao": 1,
  "id_conta_gerencial": 5,
  "id_centro_custo": 2,
  "ano": 2025,
  "mes": 3,
  "valor_orcado": "15000.00",
  "valor_realizado": "18500.00",
  "variacao_absoluta": "3500.00",
  "variacao_percentual": "23.33",
  "justificativa": "Campanha de lançamento do produto X.",
  "criado_por": "Ana Silva"
}
```

---

## Códigos de erro

| Código | Significado |
|--------|-------------|
| `404` | Recurso não encontrado |
| `409` | Conflito — duplicata ou estado inválido (ex: versão bloqueada, workflow já ativo) |
| `422` | Dados inválidos (validação Pydantic) |
| `500` | Erro interno — verifique logs da API |

---

## Autenticação

A API não implementa autenticação na versão atual — uso exclusivo em rede interna. Em produção, coloque o Nginx na frente com autenticação básica ou VPN.
