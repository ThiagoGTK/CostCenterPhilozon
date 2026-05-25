import { useState } from "react";
import { useContasSia, useContasGerenciais } from "../hooks/useDimensoes";
import {
  useMapeamentosContas,
  useCriarMapeamentoConta,
  useDesativarMapeamentoConta,
} from "../hooks/useMapeamentos";
import styles from "./PageGeneric.module.css";

// Empresa padrão: Philozon EMP_COD 1
const ID_EMPRESA_PADRAO = 1;

export default function MapeamentoContas() {
  const [form, setForm] = useState({ id_conta_sia: "", id_conta_gerencial: "" });
  const [erro, setErro] = useState("");

  const { data: mapeamentos = [], isLoading } = useMapeamentosContas(ID_EMPRESA_PADRAO);
  const { data: contasSia = [] } = useContasSia({ codpla: 2 }); // plano mais recente
  const { data: contasGer = [] } = useContasGerenciais({ apenas_ativas: true });

  const criar = useCriarMapeamentoConta();
  const desativar = useDesativarMapeamentoConta();

  // Contas SIA ainda não mapeadas
  const idsMapeados = new Set(mapeamentos.map((m) => m.id_conta_sia));
  const contasSiaDisponiveis = contasSia.filter((c) => !idsMapeados.has(c.id));

  async function handleCriar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    if (!form.id_conta_sia || !form.id_conta_gerencial) {
      setErro("Selecione a conta SIA e a conta gerencial.");
      return;
    }
    try {
      await criar.mutateAsync({
        id_conta_sia: Number(form.id_conta_sia),
        id_conta_gerencial: Number(form.id_conta_gerencial),
        id_empresa: ID_EMPRESA_PADRAO,
      });
      setForm({ id_conta_sia: "", id_conta_gerencial: "" });
    } catch {
      setErro("Erro ao criar mapeamento. Verifique se já existe um ativo para esta conta SIA.");
    }
  }

  function contaGerNome(id: number) {
    const c = contasGer.find((x) => x.id === id);
    return c ? `${c.codigo} — ${c.nome}` : `ID ${id}`;
  }

  return (
    <div className={styles.page}>
      {/* Formulário de novo mapeamento */}
      <div className={styles.card} style={{ marginBottom: 16 }}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Novo Mapeamento: Conta SIA → Conta Gerencial</span>
        </div>
        <form onSubmit={handleCriar} style={{ display: "flex", gap: 12, padding: "12px 0", flexWrap: "wrap", alignItems: "flex-end" }}>
          <label className={styles.filterItem}>
            <span>Conta SIA</span>
            <select value={form.id_conta_sia} onChange={(e) => setForm((f) => ({ ...f, id_conta_sia: e.target.value }))}>
              <option value="">— selecione —</option>
              {contasSiaDisponiveis.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.conta_class ?? c.conta_codigo} — {c.conta_nome}
                </option>
              ))}
            </select>
          </label>

          <label className={styles.filterItem}>
            <span>Conta Gerencial</span>
            <select value={form.id_conta_gerencial} onChange={(e) => setForm((f) => ({ ...f, id_conta_gerencial: e.target.value }))}>
              <option value="">— selecione —</option>
              {contasGer.filter((c) => c.aceita_lancamento).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.codigo} — {c.nome}
                </option>
              ))}
            </select>
          </label>

          <button type="submit" className={styles.btnPrimary} disabled={criar.isPending}>
            {criar.isPending ? "Salvando..." : "+ Adicionar"}
          </button>
        </form>
        {erro && <p style={{ color: "#dc2626", fontSize: 13, margin: "4px 0 0" }}>{erro}</p>}
      </div>

      {/* Tabela de mapeamentos ativos */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Mapeamentos Ativos</span>
          <span style={{ fontSize: 13, color: "#64748b" }}>{mapeamentos.length} registros</span>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Conta SIA</th>
                <th>Nome SIA</th>
                <th>Conta Gerencial</th>
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
                    <td><code>{m.conta_sia?.conta_class ?? m.conta_sia?.conta_codigo ?? m.id_conta_sia}</code></td>
                    <td>{m.conta_sia?.conta_nome ?? "—"}</td>
                    <td>{contaGerNome(m.id_conta_gerencial)}</td>
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
