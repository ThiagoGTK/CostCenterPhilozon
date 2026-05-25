import { useState } from "react";
import { useVersoes, useCentrosCusto } from "../hooks/useDimensoes";
import { useComparativo } from "../hooks/useComparativo";
import { formatCurrency, formatPercent } from "../services/format";
import styles from "./PageGeneric.module.css";
import tableStyles from "./Comparativo.module.css";

const NOMES_MESES = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function variacaoClass(valor: number): string {
  if (valor > 5) return tableStyles.positivo;
  if (valor < -5) return tableStyles.negativo;
  return "";
}

export default function Comparativo() {
  const anoAtual = new Date().getFullYear();
  const [ano, setAno] = useState(anoAtual);
  const [idVersao, setIdVersao] = useState<number | "">("");
  const [idCC, setIdCC] = useState<number | "">("");

  const { data: versoes = [] } = useVersoes(ano);
  const { data: centros = [] } = useCentrosCusto();

  const versaoSelecionada = idVersao || versoes[0]?.id;

  const { data: comparativo, isLoading, isError } = useComparativo(
    ano,
    versaoSelecionada || undefined,
    idCC ? { id_centro_custo: Number(idCC) } : undefined
  );

  return (
    <div className={styles.page}>
      {/* Filtros */}
      <div className={styles.filterBar}>
        <label className={styles.filterItem}>
          <span>Ano</span>
          <select value={ano} onChange={(e) => { setAno(Number(e.target.value)); setIdVersao(""); }}>
            {[anoAtual - 1, anoAtual, anoAtual + 1].map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </label>

        <label className={styles.filterItem}>
          <span>Versão</span>
          <select value={idVersao} onChange={(e) => setIdVersao(e.target.value ? Number(e.target.value) : "")}>
            {versoes.map((v) => (
              <option key={v.id} value={v.id}>{v.nome}</option>
            ))}
            {versoes.length === 0 && <option value="">Nenhuma versão</option>}
          </select>
        </label>

        <label className={styles.filterItem}>
          <span>Centro de Custo</span>
          <select value={idCC} onChange={(e) => setIdCC(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Todos</option>
            {centros.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </label>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>
            Realizado × Orçado — {ano}
            {comparativo && ` — ${comparativo.nome_versao}`}
          </span>

          {/* Totais */}
          {comparativo && (
            <div className={tableStyles.totaisBar}>
              <span>Orçado: <strong>{formatCurrency(Number(comparativo.total_orcado))}</strong></span>
              <span>Realizado: <strong>{formatCurrency(Number(comparativo.total_realizado))}</strong></span>
              <span className={variacaoClass(Number(comparativo.variacao_percentual_total))}>
                Desvio: <strong>{formatPercent(Number(comparativo.variacao_percentual_total))}</strong>
              </span>
            </div>
          )}
        </div>

        {isLoading && <div className={styles.loadingMsg}>Carregando...</div>}
        {isError && <div className={styles.errorMsg}>Erro ao carregar. Verifique a API.</div>}

        {comparativo && (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Conta Gerencial</th>
                  <th>Centro de Custo</th>
                  <th className={tableStyles.right}>Orçado</th>
                  <th className={tableStyles.right}>Realizado</th>
                  <th className={tableStyles.right}>Variação R$</th>
                  <th className={tableStyles.right}>Variação %</th>
                </tr>
              </thead>
              <tbody>
                {comparativo.itens.length === 0 ? (
                  <tr>
                    <td colSpan={7} className={styles.emptyRow}>
                      Nenhum dado para os filtros selecionados.
                    </td>
                  </tr>
                ) : (
                  comparativo.itens.map((row, idx) => {
                    const varAbs = Number(row.valor_realizado) - Number(row.valor_orcado);
                    const varPct = Number(row.variacao_percentual);
                    return (
                      <tr key={idx}>
                        <td>{NOMES_MESES[row.mes]}</td>
                        <td>{row.conta_gerencial_nome}</td>
                        <td>{row.centro_custo_nome}</td>
                        <td className={tableStyles.right}>{formatCurrency(Number(row.valor_orcado))}</td>
                        <td className={tableStyles.right}>{formatCurrency(Number(row.valor_realizado))}</td>
                        <td className={`${tableStyles.right} ${variacaoClass(varAbs)}`}>
                          {varAbs >= 0 ? "+" : ""}{formatCurrency(varAbs)}
                        </td>
                        <td className={`${tableStyles.right} ${variacaoClass(varPct)}`}>
                          {varPct >= 0 ? "+" : ""}{formatPercent(varPct)}
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
