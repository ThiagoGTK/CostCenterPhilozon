import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getWorkflows,
  iniciarWorkflow,
  enviarWorkflow,
  aprovarWorkflow,
  reprovarWorkflow,
} from "../services/api";

const QUERY_KEY = "workflows";

export function useWorkflows(ano?: number) {
  return useQuery({
    queryKey: [QUERY_KEY, ano],
    queryFn: () => getWorkflows(ano),
  });
}

export function useIniciarWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: iniciarWorkflow,
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

export function useEnviarWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: { enviado_por: string } }) =>
      enviarWorkflow(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

export function useAprovarWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: { aprovado_por: string; comentario?: string };
    }) => aprovarWorkflow(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}

export function useReprovarWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: { reprovado_por: string; comentario: string };
    }) => reprovarWorkflow(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [QUERY_KEY] }),
  });
}
