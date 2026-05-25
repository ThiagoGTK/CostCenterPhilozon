import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface CentroCusto {
  id: number;
  codigo: string;
  nome: string;
  descricao?: string;
  id_pai?: number;
  ativo: boolean;
}

export interface ContaGerencial {
  id: number;
  codigo: string;
  nome: string;
  tipo: "RECEITA" | "DESPESA" | "ATIVO" | "PASSIVO" | "RESULTADO";
  natureza: "DEVEDORA" | "CREDORA";
  id_pai?: number;
  nivel: number;
  aceita_lancamento: boolean;
  ativa: boolean;
}

export interface VersaoOrcamento {
  id: number;
  ano: number;
  tipo: "ORIGINAL" | "REVISAO" | "FORECAST";
  nome: string;
  descricao?: string;
  data_criacao: string;
  bloqueada: boolean;
}

export interface OrcamentoItem {
  id: number;
  id_empresa: number;
  id_versao: number;
  id_conta_gerencial: number;
  id_centro_custo: number;
  ano: number;
  mes: number;
  valor: string;
  observacao?: string;
}

export interface ComparativoItem {
  mes: number;
  conta_gerencial_codigo: string;
  conta_gerencial_nome: string;
  centro_custo_codigo: string;
  centro_custo_nome: string;
  valor_orcado: string;
  valor_realizado: string;
  variacao_absoluta: string;
  variacao_percentual: string;
}

export interface WorkflowItem {
  id: number;
  id_versao: number;
  id_empresa: number;
  status: "RASCUNHO" | "ENVIADO" | "APROVADO" | "REPROVADO";
  criado_por: string;
  enviado_por?: string;
  aprovado_por?: string;
  reprovado_por?: string;
  data_envio?: string;
  data_decisao?: string;
  comentario?: string;
}

// ── API calls ──────────────────────────────────────────────────────────────

export const getCentrosCusto = () =>
  api.get<CentroCusto[]>("/centros-custo").then((r) => r.data);

export const getContasGerenciais = () =>
  api.get<ContaGerencial[]>("/contas-gerenciais").then((r) => r.data);

export const getVersoesOrcamento = (ano: number) =>
  api.get<VersaoOrcamento[]>(`/versoes-orcamento/${ano}`).then((r) => r.data);

export const getOrcamento = (ano: number, idVersao: number) =>
  api.get<OrcamentoItem[]>(`/orcamento/${ano}/${idVersao}`).then((r) => r.data);

export const getComparativo = (ano: number, idVersao: number) =>
  api.get(`/comparativo/${ano}/${idVersao}`).then((r) => r.data);

export const getDRE = (ano: number, idVersao: number) =>
  api.get(`/dre/${ano}/${idVersao}`).then((r) => r.data);
