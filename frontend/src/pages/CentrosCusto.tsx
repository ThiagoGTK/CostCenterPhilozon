import styles from "./PageGeneric.module.css";

const exemplos = [
  { codigo: "CC01", nome: "Comercial", pai: "—", ativo: true },
  { codigo: "CC02", nome: "Operações", pai: "—", ativo: true },
  { codigo: "CC02.01", nome: "Produção", pai: "Operações", ativo: true },
  { codigo: "CC03", nome: "TI", pai: "—", ativo: true },
  { codigo: "CC04", nome: "RH", pai: "—", ativo: true },
  { codigo: "CC05", nome: "Financeiro", pai: "—", ativo: false },
];

export default function CentrosCusto() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Centros de Custo Gerenciais</span>
          <button className={styles.btnPrimary}>+ Novo Centro de Custo</button>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nome</th>
                <th>Centro Pai</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {exemplos.map((row, idx) => (
                <tr key={idx}>
                  <td><code>{row.codigo}</code></td>
                  <td>{row.nome}</td>
                  <td style={{ color: "var(--color-text-muted)" }}>{row.pai}</td>
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
