import { useState } from "react";
import styles from "./PageGeneric.module.css";
import tableStyles from "./Comparativo.module.css";
import { formatCurrency, formatPercent } from "../services/format";

// Dados de exemplo
const dadosExemplo = [
  { mes: "Jan", conta: "Receita Bruta", cc: "Comercial", orcado: 850000, realizado: 920000 },
  { mes: "Fev", conta: "Receita Bruta", cc: "Comercial", orcado: 820000, realizado: 780000 },
  { mes: "Mar", conta: "Desp. Administrativas", cc: "Administração", orcado: 150000, realizado: 165000 },
  { mes: "Mar", conta: "Desp. Comerciais", cc: "Comercial", orcado: 90000, realizado: 87000 },
  { mes: "Abr", conta: "Receita Bruta", cc: "Comercial", orcado: 900000, realizado: 945000 },
];

function variacaoClass(variacao: number): string {
  if (variacao > 5) return tableStyles.positivo;
  if (variacao < -5) return tableStyles.negativo;
  return "";
}

export default function Comparativo() {
  const [ano, setAno] = useState(2025);

  return (
    <div className={styles.page}>
      <div className={styles.filterBar}>
        <label className={styles.filterItem}>
          <span>Ano</span>
          <select value={ano} onChange={(e) => setAno(Number(e.target.value))}>
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
          </select>
        </label>
        <label className={styles.filterItem}>
          <span>Versão</span>
          <select>
            <option>Original 2025</option>
            <option>Revisão 1</option>
          </select>
        </label>
        <label className={styles.filterItem}>
          <span>Centro de Custo</span>
          <select>
            <option value="">Todos</option>
            <option>Comercial</option>
            <option>Operações</option>
          </select>
        </label>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Realizado × Orçado — {ano}</span>
        </div>

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
              {dadosExemplo.map((row, idx) => {
                const varAbs = row.realizado - row.orcado;
                const varPct = row.orcado !== 0 ? (varAbs / Math.abs(row.orcado)) * 100 : 0;
                return (
                  <tr key={idx}>
                    <td>{row.mes}</td>
                    <td>{row.conta}</td>
                    <td>{row.cc}</td>
                    <td className={tableStyles.right}>{formatCurrency(row.orcado)}</td>
                    <td className={tableStyles.right}>{formatCurrency(row.realizado)}</td>
                    <td className={`${tableStyles.right} ${variacaoClass(varAbs)}`}>
                      {varAbs >= 0 ? "+" : ""}{formatCurrency(varAbs)}
                    </td>
                    <td className={`${tableStyles.right} ${variacaoClass(varPct)}`}>
                      {varPct >= 0 ? "+" : ""}{formatPercent(varPct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
