import { useState } from "react";
import { useCentrosCusto, useEmpresaAtiva } from "../hooks/useDimensoes";
import {
  useMapeamentosCC,
  useCriarMapeamentoCC,
  useDesativarMapeamentoCC,
} from "../hooks/useMapeamentos";
import styles from "./PageGeneric.module.css";

export default function MapeamentoCentrosCusto() {
  const [form, setForm] = useState({ cc_sia_codigo: "", cc_sia_nome: "", id_centro_custo_gerencial: "" });
  const [erro, setErro] = useState("");

  const { idEmpresa } = useEmpresaAtiva();
  const { data: mapeamentos = [], isLoading } = useMapeamentosCC(idEmpresa ?? undefined);
  const { data: centrosGer = [] } = useCentrosCusto();
  const criar = useCriarMapeamentoCC();
  const desativar = useDesativarMapeamentoCC();

  function ccGerNome(id: number) {
    return centrosGer.find((c) => c.id === id)?.nome ?? `ID ${id}`;
  }

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    if (!form.cc_sia_codigo || !form.id_centro_custo_gerencial) {
      setErro("Preencha o código SIA e selecione o CC gerencial.");
      return;
    }
    try {
      await criar.mutateAsync({
        cc_sia_codigo: form.cc_sia_codigo.trim(),
        cc_sia_nome: form.cc_sia_nome.trim() || undefined,
        id_empresa: idEmpresa!,
        id_centro_custo_gerencial: Number(form.id_centro_custo_gerencial),
      });
      setForm({ cc_sia_codigo: "", cc_sia_nome: "", id_centro_custo_gerencial: "" });
    } catch {
      setErro("Erro ao criar mapeamento. Verifique se já existe um ativo para este código SIA.");
    }
  }

  return (
    <div className={styles.page}>
      {/* Formulário */}
      <div className={styles.card} style={{ marginBottom: 16 }}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Novo Mapeamento: CC SIA → CC Gerencial</span>
        </div>
        <form onSubmit={handleCriar} style={{ display: "flex", gap: 12, padding: "12px 0", flexWrap: "wrap", alignItems: "flex-end" }}>
          <label className={styles.filterItem}>
            <span>Código SIA (CC_COD)</span>
            <input
              type="text"
              value={form.cc_sia_codigo}
              onChange={(e) => setForm((f) => ({ ...f, cc_sia_codigo: e.target.value }))}
              placeholder="ex: 10"
              style={{ padding: "6px 10px", border: "1px solid #e2e8f0", borderRadius: 6 }}
            />
          </label>

          <label className={styles.filterItem}>
            <span>Nome SIA (opcional)</span>
            <input
              type="text"
              value={form.cc_sia_nome}
              onChange={(e) => setForm((f) => ({ ...f, cc_sia_nome: e.target.value }))}
              placeholder="ex: Vendas Internas"
              style={{ padding: "6px 10px", border: "1px solid #e2e8f0", borderRadius: 6 }}
            />
          </label>

          <label className={styles.filterItem}>
            <span>CC Gerencial</span>
            <select
              value={form.id_centro_custo_gerencial}
              onChange={(e) => setForm((f) => ({ ...f, id_centro_custo_gerencial: e.target.value }))}
            >
              <option value="">— selecione —</option>
              {centrosGer.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </label>

          <button type="submit" className={styles.btnPrimary} disabled={criar.isPending}>
            {criar.isPending ? "Salvando..." : "+ Adicionar"}
          </button>
        </form>
        {erro && <p style={{ color: "#dc2626", fontSize: 13, margin: "4px 0 0" }}>{erro}</p>}
      </div>

      {/* Tabela */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Mapeamentos Ativos</span>
          <span style={{ fontSize: 13, color: "#64748b" }}>{mapeamentos.length} registros</span>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Código SIA</th>
                <th>Nome SIA</th>
                <th>CC Gerencial</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={4} className={styles.emptyRow}>Carregando...</td></tr>
              ) : mapeamentos.length === 0 ? (
                <tr><td colSpan={4} className={styles.emptyRow}>Nenhum mapeamento cadastrado.</td></tr>
              ) : (
                mapeamentos.map((m) => (
                  <tr key={m.id}>
                    <td><code>{m.cc_sia_codigo}</code></td>
                    <td>{m.cc_sia_nome ?? "—"}</td>
                    <td>{ccGerNome(m.id_centro_custo_gerencial)}</td>
                    <td>
                      <button
                        className={styles.btnSecondary}
                        style={{ fontSize: 12, padding: "4px 10px", color: "#dc2626" }}
                        disabled={desativar.isPending}
                        onClick={() => desativar.mutate(m.id)}
                      >
                        Remover
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
