import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getMapeamentosContas,
  criarMapeamentoConta,
  atualizarMapeamentoConta,
  desativarMapeamentoConta,
  getMapeamentosCC,
  criarMapeamentoCC,
  desativarMapeamentoCC,
} from "../services/api";

// ── Contas ─────────────────────────────────────────────────────────────────

export function useMapeamentosContas(idEmpresa?: number) {
  return useQuery({
    queryKey: ["mapeamentos-contas", idEmpresa],
    queryFn: () => getMapeamentosContas(idEmpresa),
  });
}

export function useCriarMapeamentoConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: criarMapeamentoConta,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mapeamentos-contas"] }),
  });
}

export function useAtualizarMapeamentoConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: { id_conta_gerencial: number; observacao?: string } }) =>
      atualizarMapeamentoConta(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mapeamentos-contas"] }),
  });
}

export function useDesativarMapeamentoConta() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: desativarMapeamentoConta,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mapeamentos-contas"] }),
  });
}

// ── Centros de Custo ───────────────────────────────────────────────────────

export function useMapeamentosCC(idEmpresa?: number) {
  return useQuery({
    queryKey: ["mapeamentos-cc", idEmpresa],
    queryFn: () => getMapeamentosCC(idEmpresa),
  });
}

export function useCriarMapeamentoCC() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: criarMapeamentoCC,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mapeamentos-cc"] }),
  });
}

export function useDesativarMapeamentoCC() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: desativarMapeamentoCC,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mapeamentos-cc"] }),
  });
}
