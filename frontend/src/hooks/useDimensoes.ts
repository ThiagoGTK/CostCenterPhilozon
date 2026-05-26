import { useQuery } from "@tanstack/react-query";
import {
  getEmpresas,
  getCentrosCusto,
  getContasGerenciais,
  getContasSia,
  getVersoesOrcamento,
} from "../services/api";

export function useEmpresas(apenasAtivas = true) {
  return useQuery({
    queryKey: ["empresas", apenasAtivas],
    queryFn: () => getEmpresas(apenasAtivas),
  });
}

/**
 * Retorna o id correto (dim_empresa.id) da empresa ativa no frontend.
 * Lê VITE_EMPRESA_CODEMP do .env (padrão: 1 = Philozon).
 * Nunca usa o autoincrement diretamente — resolve via API.
 */
export function useEmpresaAtiva() {
  const codemp = Number(import.meta.env.VITE_EMPRESA_CODEMP ?? 1);
  const { data: empresas = [], isLoading } = useEmpresas();
  const empresa = empresas.find((e) => e.codemp === codemp) ?? empresas[0] ?? null;
  return { empresa, idEmpresa: empresa?.id ?? null, isLoading };
}

export function useCentrosCusto(apenasAtivos = true) {
  return useQuery({
    queryKey: ["centros-custo", apenasAtivos],
    queryFn: () => getCentrosCusto(apenasAtivos),
  });
}

export function useContasGerenciais(params?: { tipo?: string; apenas_ativas?: boolean }) {
  return useQuery({
    queryKey: ["contas-gerenciais", params],
    queryFn: () => getContasGerenciais(params),
  });
}

export function useContasSia(params?: { codpla?: number; nivel?: number }) {
  return useQuery({
    queryKey: ["contas-sia", params],
    queryFn: () => getContasSia(params),
  });
}

export function useVersoes(ano: number) {
  return useQuery({
    queryKey: ["versoes", ano],
    queryFn: () => getVersoesOrcamento(ano),
    enabled: ano > 2000,
  });
}
