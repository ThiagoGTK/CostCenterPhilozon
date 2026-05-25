import { useQuery } from "@tanstack/react-query";
import { getComparativo } from "../services/api";

export function useComparativo(
  ano: number,
  idVersao: number | undefined,
  params?: { id_empresa?: number; id_centro_custo?: number }
) {
  return useQuery({
    queryKey: ["comparativo", ano, idVersao, params],
    queryFn: () => getComparativo(ano, idVersao!, params),
    enabled: !!idVersao && ano > 2000,
  });
}
