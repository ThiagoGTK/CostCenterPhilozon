import styles from "./PageGeneric.module.css";

const exemplos = [
  { sia: "3.1.01.001", siaNome: "Receita de Vendas Internas", gerencial: "3.1.01", gerencialNome: "Receita Bruta de Vendas", ativo: true },
  { sia: "3.1.01.002", siaNome: "Receita de Vendas Externas", gerencial: "3.1.01", gerencialNome: "Receita Bruta de Vendas", ativo: true },
  { sia: "4.1.01.001", siaNome: "CMV — Mercadoria", gerencial: "4.1.01", gerencialNome: "Custo dos Produtos Vendidos", ativo: true },
  { sia: "4.2.01.010", siaNome: "Salários Comerciais", gerencial: "4.2.01", gerencialNome: "Despesas Comerciais — Pessoal", ativo: false },
];

export default function MapeamentoContas() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Mapeamento: Conta SIA → Conta Gerencial</span>
          <button className={styles.btnPrimary}>+ Novo Mapeamento</button>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Conta SIA</th>
                <th>Nome SIA</th>
                <th>Conta Gerencial</th>
                <th>Nome Gerencial</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {exemplos.map((row, idx) => (
                <tr key={idx}>
                  <td><code>{row.sia}</code></td>
                  <td>{row.siaNome}</td>
                  <td><code>{row.gerencial}</code></td>
                  <td>{row.gerencialNome}</td>
                  <td>
                    <span style={{
                      padding: "2px 8px",
                      borderRadius: 12,
                      fontSize: 11,
                      fontWeight: 500,
                      background: row.ativo ? "#dcfce7" : "#f1f5f9",
                      color: row.ativo ? "#166534" : "#64748b",
                    }}>
                      {row.ativo ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td>
                    <button className={styles.btnSecondary} style={{ fontSize: 12, padding: "4px 10px" }}>
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
