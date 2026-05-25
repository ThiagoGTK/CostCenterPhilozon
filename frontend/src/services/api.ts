/**
 * Cliente HTTP centralizado + tipos de resposta da API FP&A.
 */

import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

// ── Tipos ──────────────────────────────────────────────────────────────────

export interface VersaoOrcamento {
  id: number;
  ano: number;
  tipo: "ORIGINAL" | "REVISAO" | "FORECAST";
  nome: string;
  descricao?: string;
  data_criacao: string;
  bloqueada: boolean;
}

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

export interface ContaSia {
  id: number;
  codpla: number;
  conta_codigo: string;
  conta_class?: string;
  conta_nome: string;
  conta_tipo?: string;
  conta_nivel?: number;
}

export interface ComparativoItem {
  mes: number;
  conta_gerencial_codigo: string;
  conta_gerencial_nome: string;
  centro_custo_codigo: string;
  centro_custo_nome: string;
  valor_orcado: number;
  valor_realizado: number;
  variacao_percentual: number;
}

export interface ComparativoResponse {
  ano: number;
  id_versao: number;
  nome_versao: string;
  itens: ComparativoItem[];
  total_orcado: number;
  total_realizado: number;
  variacao_absoluta_total: number;
  variacao_percentual_total: number;
}

export interface OrcamentoItem {
  id: number;
  id_empresa: number;
  id_versao: number;
  id_conta_gerencial: number;
  id_centro_custo: number;
  ano: number;
  mes: number;
  valor: number;
  observacao?: string;
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

export interface MapeamentoConta {
  id: number;
  id_conta_sia: number;
  id_conta_gerencial: number;
  id_empresa: number;
  ativo: boolean;
  observacao?: string;
  conta_sia?: ContaSia;
}

export interface MapeamentoCC {
  id: number;
  cc_sia_codigo: string;
  cc_sia_nome?: string;
  id_empresa: number;
  id_centro_custo_gerencial: number;
  ativo: boolean;
  observacao?: string;
}

// ── API calls ──────────────────────────────────────────────────────────────

// Dimensões
export const getCentrosCusto = (apenasAtivos = true) =>
  api.get<CentroCusto[]>("/centros-custo/", { params: { apenas_ativos: apenasAtivos } }).then((r) => r.data);

export const getContasGerenciais = (params?: { tipo?: string; apenas_ativas?: boolean }) =>
  api.get<ContaGerencial[]>("/contas-gerenciais/", { params }).then((r) => r.data);

export const getContasSia = (params?: { codpla?: number; nivel?: number }) =>
  api.get<ContaSia[]>("/contas-sia", { params }).then((r) => r.data);

export const getVersoesOrcamento = (ano: number) =>
  api.get<VersaoOrcamento[]>(`/versoes-orcamento/${ano}`).then((r) => r.data);

// Orçamento
export const getOrcamento = (ano: number, idVersao: number, params?: { id_empresa?: number; id_centro_custo?: number }) =>
  api.get<OrcamentoItem[]>(`/orcamento/${ano}/${idVersao}`, { params }).then((r) => r.data);

export const salvarOrcamento = (payload: {
  id_empresa: number;
  id_versao: number;
  id_conta_gerencial: number;
  id_centro_custo: number;
  ano: number;
  mes: number;
  valor: number;
  observacao?: string;
}) => api.post<OrcamentoItem>("/orcamento/", payload).then((r) => r.data);

// Comparativo
export const getComparativo = (ano: number, idVersao: number, params?: { id_empresa?: number; id_centro_custo?: number }) =>
  api.get<ComparativoResponse>(`/comparativo/${ano}/${idVersao}`, { params }).then((r) => r.data);

export const getDRE = (ano: number, idVersao: number) =>
  api.get(`/dre/${ano}/${idVersao}`).then((r) => r.data);

// Mapeamentos
export const getMapeamentosContas = (idEmpresa?: number) =>
  api.get<MapeamentoConta[]>("/mapeamentos/contas", {
    params: idEmpresa != null ? { id_empresa: idEmpresa } : {},
  }).then((r) => r.data);

export const criarMapeamentoConta = (payload: {
  id_conta_sia: number;
  id_conta_gerencial: number;
  id_empresa: number;
  observacao?: string;
}) => api.post<MapeamentoConta>("/mapeamentos/contas", payload).then((r) => r.data);

export const atualizarMapeamentoConta = (id: number, payload: { id_conta_gerencial: number; observacao?: string }) =>
  api.put<MapeamentoConta>(`/mapeamentos/contas/${id}`, payload).then((r) => r.data);

export const desativarMapeamentoConta = (id: number) =>
  api.delete(`/mapeamentos/contas/${id}`);

export const getMapeamentosCC = (idEmpresa?: number) =>
  api.get<MapeamentoCC[]>("/mapeamentos/centros-custo", {
    params: idEmpresa != null ? { id_empresa: idEmpresa } : {},
  }).then((r) => r.data);

export const criarMapeamentoCC = (payload: {
  cc_sia_codigo: string;
  cc_sia_nome?: string;
  id_empresa: number;
  id_centro_custo_gerencial: number;
  observacao?: string;
}) => api.post<MapeamentoCC>("/mapeamentos/centros-custo", payload).then((r) => r.data);

export const atualizarMapeamentoCC = (id: number, payload: { id_centro_custo_gerencial: number; cc_sia_nome?: string }) =>
  api.put<MapeamentoCC>(`/mapeamentos/centros-custo/${id}`, payload).then((r) => r.data);

export const desativarMapeamentoCC = (id: number) =>
  api.delete(`/mapeamentos/centros-custo/${id}`);
