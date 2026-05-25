import { useState } from "react";
import styles from "./PageGeneric.module.css";

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

const contas = [
  { codigo: "3.1.01", nome: "Receita Bruta de Vendas" },
  { codigo: "4.1.01", nome: "Custo dos Produtos Vendidos" },
  { codigo: "4.2.01", nome: "Despesas Comerciais" },
  { codigo: "4.3.01", nome: "Despesas Administrativas" },
];

const centros = [
  { id: 1, nome: "Comercial" },
  { id: 2, nome: "Operações" },
  { id: 3, nome: "TI" },
];

export default function Orcamento() {
  const [ano, setAno] = useState(new Date().getFullYear());
  const [versao, setVersao] = useState("Original 2025");
  const [cc, setCC] = useState("1");

  return (
    <div className={styles.page}>
      {/* Filtros */}
      <div className={styles.filterBar}>
        <label className={styles.filterItem}>
          <span>Ano</span>
          <select value={ano} onChange={(e) => setAno(Number(e.target.value))}>
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
            <option value={2026}>2026</option>
          </select>
        </label>
        <label className={styles.filterItem}>
          <span>Versão</span>
          <select value={versao} onChange={(e) => setVersao(e.target.value)}>
            <option>Original 2025</option>
            <option>Revisão 1</option>
            <option>Forecast Q3</option>
          </select>
        </label>
        <label className={styles.filterItem}>
          <span>Centro de Custo</span>
          <select value={cc} onChange={(e) => setCC(e.target.value)}>
            {centros.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
        </label>
      </div>

      {/* Tabela de orçamento */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Orçamento — {versao}</span>
          <button className={styles.btnPrimary}>Salvar Rascunho</button>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Conta</th>
                {MESES.map((m) => (
                  <th key={m}>{m.substring(0, 3)}</th>
                ))}
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {contas.map((conta) => (
                <tr key={conta.codigo}>
                  <td className={styles.tdLabel}>
                    <span className={styles.contaCodigo}>{conta.codigo}</span>
                    {conta.nome}
                  </td>
                  {MESES.map((_, i) => (
                    <td key={i}>
                      <input
                        type="number"
                        className={styles.valorInput}
                        placeholder="0,00"
                        step="0.01"
                        min="0"
                      />
                    </td>
                  ))}
                  <td className={styles.tdTotal}>R$ 0,00</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
