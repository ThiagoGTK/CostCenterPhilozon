import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOrcamento, salvarOrcamento } from "../services/api";

export function useOrcamento(
  ano: number,
  idVersao: number | "",
  params?: { id_empresa?: number; id_centro_custo?: number }
) {
  return useQuery({
    queryKey: ["orcamento", ano, idVersao, params],
    queryFn: () => getOrcamento(ano, idVersao as number, params),
    enabled: !!idVersao && ano > 2000,
  });
}

export function useSalvarOrcamentoItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: salvarOrcamento,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orcamento"] });
    },
  });
}
