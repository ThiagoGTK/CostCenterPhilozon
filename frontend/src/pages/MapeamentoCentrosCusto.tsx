import styles from "./PageGeneric.module.css";

const exemplos = [
  { siaCodigo: "001", siaNome: "Vendas", gerencial: "Comercial", ativo: true },
  { siaCodigo: "002", siaNome: "Producao", gerencial: "Operações", ativo: true },
  { siaCodigo: "003", siaNome: "TI Infra", gerencial: "TI", ativo: true },
  { siaCodigo: "004", siaNome: "RH", gerencial: "RH", ativo: true },
];

export default function MapeamentoCentrosCusto() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Mapeamento: CC SIA → CC Gerencial</span>
          <button className={styles.btnPrimary}>+ Novo Mapeamento</button>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Código SIA</th>
                <th>Nome SIA</th>
                <th>CC Gerencial</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {exemplos.map((row, idx) => (
                <tr key={idx}>
                  <td><code>{row.siaCodigo}</code></td>
                  <td>{row.siaNome}</td>
                  <td>{row.gerencial}</td>
                  <td>
                    <span style={{
                      padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 500,
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
