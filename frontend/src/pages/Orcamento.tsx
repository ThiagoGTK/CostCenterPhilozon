import { useState, useEffect, useCallback } from "react";
import { useVersoes, useCentrosCusto, useContasGerenciais } from "../hooks/useDimensoes";
import { useOrcamento, useSalvarOrcamentoItem } from "../hooks/useOrcamento";
import { formatCurrency } from "../services/format";
import styles from "./PageGeneric.module.css";

const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const ID_EMPRESA_PADRAO = 1;

// key to identify a budget cell
function cellKey(contaId: number, mes: number) {
  return `${contaId}_${mes}`;
}

export default function Orcamento() {
  const anoAtual = new Date().getFullYear();
  const [ano, setAno] = useState(anoAtual);
  const [idVersao, setIdVersao] = useState<number | "">("");
  const [idCC, setIdCC] = useState<number | "">("");

  // Local grid state: cellKey → string value (raw input)
  const [valores, setValores] = useState<Record<string, string>>({});
  const [salvando, setSalvando] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const { data: versoes = [] } = useVersoes(ano);
  const { data: centros = [] } = useCentrosCusto();
  const { data: contas = [] } = useContasGerenciais({ apenas_ativas: true });
  const salvarItem = useSalvarOrcamentoItem();

  // Auto-select first versão when list loads
  useEffect(() => {
    if (versoes.length > 0 && idVersao === "") {
      setIdVersao(versoes[0].id);
    }
  }, [versoes, idVersao]);

  // Load existing orcamento entries when versão + CC changes
  const ccParam = idCC ? { id_centro_custo: Number(idCC) } : undefined;
  const { data: orcamentoExistente = [], isLoading: loadingOrc } = useOrcamento(
    ano,
    idVersao,
    { id_empresa: ID_EMPRESA_PADRAO, ...ccParam }
  );

  // Populate local state when existing data arrives
  useEffect(() => {
    if (!orcamentoExistente.length) return;
    const next: Record<string, string> = {};
    for (const item of orcamentoExistente) {
      const k = cellKey(item.id_conta_gerencial, item.mes);
      next[k] = String(item.valor);
    }
    setValores(next);
  }, [orcamentoExistente]);

  // Reset local values when filters change
  useEffect(() => {
    setValores({});
    setFeedbackMsg(null);
  }, [ano, idVersao, idCC]);

  const handleChange = useCallback((contaId: number, mes: number, raw: string) => {
    setValores((prev) => ({ ...prev, [cellKey(contaId, mes)]: raw }));
    setFeedbackMsg(null);
  }, []);

  function totalLinha(contaId: number): number {
    return MESES.reduce((acc, _, i) => {
      const mes = i + 1;
      const raw = valores[cellKey(contaId, mes)] ?? "";
      return acc + (parseFloat(raw) || 0);
    }, 0);
  }

  const versaoSelecionada = versoes.find((v) => v.id === idVersao);
  const bloqueada = versaoSelecionada?.bloqueada ?? false;

  // Contas that accept entries (leaf nodes)
  const contasLancamento = contas.filter((c) => c.aceita_lancamento);

  async function handleSalvar() {
    if (!idVersao) {
      setFeedbackMsg("Selecione uma versão antes de salvar.");
      return;
    }
    if (!idCC) {
      setFeedbackMsg("Selecione um centro de custo antes de salvar.");
      return;
    }
    setSalvando(true);
    setFeedbackMsg(null);

    try {
      const saves: Promise<unknown>[] = [];
      for (const conta of contasLancamento) {
        for (let mes = 1; mes <= 12; mes++) {
          const raw = valores[cellKey(conta.id, mes)] ?? "";
          const valor = parseFloat(raw) || 0;
          saves.push(
            salvarItem.mutateAsync({
              id_empresa: ID_EMPRESA_PADRAO,
              id_versao: idVersao as number,
              id_conta_gerencial: conta.id,
              id_centro_custo: Number(idCC),
              ano,
              mes,
              valor,
            })
          );
        }
      }
      await Promise.all(saves);
      setFeedbackMsg(`Orçamento salvo com sucesso! (${saves.length} células)`);
    } catch {
      setFeedbackMsg("Erro ao salvar. Verifique a API e tente novamente.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className={styles.page}>
      {/* Filtros */}
      <div className={styles.filterBar}>
        <label className={styles.filterItem}>
          <span>Ano</span>
          <select
            value={ano}
            onChange={(e) => {
              setAno(Number(e.target.value));
              setIdVersao("");
            }}
          >
            {[anoAtual - 1, anoAtual, anoAtual + 1].map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </label>

        <label className={styles.filterItem}>
          <span>Versão</span>
          <select
            value={idVersao}
            onChange={(e) => setIdVersao(e.target.value ? Number(e.target.value) : "")}
          >
            {versoes.length === 0 && <option value="">Nenhuma versão cadastrada</option>}
            {versoes.map((v) => (
              <option key={v.id} value={v.id}>
                {v.nome}{v.bloqueada ? " 🔒" : ""}
              </option>
            ))}
          </select>
        </label>

        <label className={styles.filterItem}>
          <span>Centro de Custo</span>
          <select
            value={idCC}
            onChange={(e) => setIdCC(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">— selecione —</option>
            {centros.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </label>
      </div>

      {/* Tabela de orçamento */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>
            Orçamento — {versaoSelecionada?.nome ?? "—"} — {ano}
          </span>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            {feedbackMsg && (
              <span style={{
                fontSize: 12,
                color: feedbackMsg.startsWith("Erro") ? "#dc2626" : "#16a34a",
              }}>
                {feedbackMsg}
              </span>
            )}
            {bloqueada ? (
              <span style={{ fontSize: 12, color: "#64748b" }}>
                🔒 Versão bloqueada (somente leitura)
              </span>
            ) : (
              <button
                className={styles.btnPrimary}
                onClick={handleSalvar}
                disabled={salvando || !idVersao || !idCC}
              >
                {salvando ? "Salvando..." : "Salvar Rascunho"}
              </button>
            )}
          </div>
        </div>

        {!idVersao && (
          <div className={styles.loadingMsg}>Selecione uma versão para editar o orçamento.</div>
        )}

        {!idCC && idVersao && (
          <div className={styles.loadingMsg}>Selecione um centro de custo.</div>
        )}

        {loadingOrc && idVersao && idCC && (
          <div className={styles.loadingMsg}>Carregando orçamento existente...</div>
        )}

        {idVersao && idCC && !loadingOrc && (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th style={{ minWidth: 240 }}>Conta Gerencial</th>
                  {MESES.map((m) => (
                    <th key={m} style={{ textAlign: "right", minWidth: 90 }}>{m}</th>
                  ))}
                  <th style={{ textAlign: "right", minWidth: 110 }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {contasLancamento.length === 0 ? (
                  <tr>
                    <td colSpan={14} className={styles.emptyRow}>
                      Nenhuma conta gerencial com aceita_lancamento cadastrada.
                    </td>
                  </tr>
                ) : (
                  contasLancamento.map((conta) => {
                    const total = totalLinha(conta.id);
                    return (
                      <tr key={conta.id}>
                        <td className={styles.tdLabel}>
                          <span className={styles.contaCodigo}>{conta.codigo}</span>
                          {conta.nome}
                        </td>
                        {MESES.map((_, i) => {
                          const mes = i + 1;
                          const key = cellKey(conta.id, mes);
                          return (
                            <td key={mes}>
                              <input
                                type="number"
                                className={styles.valorInput}
                                placeholder="0,00"
                                step="0.01"
                                min="0"
                                value={valores[key] ?? ""}
                                disabled={bloqueada}
                                onChange={(e) => handleChange(conta.id, mes, e.target.value)}
                              />
                            </td>
                          );
                        })}
                        <td className={styles.tdTotal}>
                          {total !== 0 ? formatCurrency(total) : "—"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
