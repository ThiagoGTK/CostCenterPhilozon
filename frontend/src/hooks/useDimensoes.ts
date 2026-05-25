import { useQuery } from "@tanstack/react-query";
import {
  getCentrosCusto,
  getContasGerenciais,
  getContasSia,
  getVersoesOrcamento,
} from "../services/api";

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
