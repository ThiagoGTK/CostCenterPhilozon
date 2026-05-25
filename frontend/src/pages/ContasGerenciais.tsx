import styles from "./PageGeneric.module.css";

const exemplos = [
  { codigo: "3", nome: "RECEITAS", tipo: "RECEITA", natureza: "CREDORA", nivel: 1, aceita: false },
  { codigo: "3.1", nome: "Receita Bruta", tipo: "RECEITA", natureza: "CREDORA", nivel: 2, aceita: false },
  { codigo: "3.1.01", nome: "Receita Bruta de Vendas", tipo: "RECEITA", natureza: "CREDORA", nivel: 3, aceita: true },
  { codigo: "4", nome: "DESPESAS", tipo: "DESPESA", natureza: "DEVEDORA", nivel: 1, aceita: false },
  { codigo: "4.1", nome: "Custos", tipo: "DESPESA", natureza: "DEVEDORA", nivel: 2, aceita: false },
  { codigo: "4.1.01", nome: "CPV", tipo: "DESPESA", natureza: "DEVEDORA", nivel: 3, aceita: true },
  { codigo: "4.2", nome: "Desp. Operacionais", tipo: "DESPESA", natureza: "DEVEDORA", nivel: 2, aceita: false },
];

const TIPO_COLORS: Record<string, string> = {
  RECEITA: "#dcfce7",
  DESPESA: "#fee2e2",
  RESULTADO: "#eff6ff",
};

const TIPO_TEXT: Record<string, string> = {
  RECEITA: "#166534",
  DESPESA: "#991b1b",
  RESULTADO: "#1d4ed8",
};

export default function ContasGerenciais() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Plano de Contas Gerencial</span>
          <button className={styles.btnPrimary}>+ Nova Conta</button>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Código</th>
                <th>Nome</th>
                <th>Tipo</th>
                <th>Natureza</th>
                <th>Nível</th>
                <th>Lança?</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {exemplos.map((row, idx) => (
                <tr key={idx}>
                  <td>
                    <code style={{ paddingLeft: `${(row.nivel - 1) * 16}px` }}>
                      {row.codigo}
                    </code>
                  </td>
                  <td style={{ fontWeight: row.nivel === 1 ? 700 : 400 }}>{row.nome}</td>
                  <td>
                    <span style={{
                      padding: "2px 8px", borderRadius: 12, fontSize: 11, fontWeight: 500,
                      background: TIPO_COLORS[row.tipo] ?? "#f1f5f9",
                      color: TIPO_TEXT[row.tipo] ?? "#475569",
                    }}>
                      {row.tipo}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{row.natureza}</td>
                  <td style={{ textAlign: "center" }}>{row.nivel}</td>
                  <td style={{ textAlign: "center" }}>{row.aceita ? "✓" : "—"}</td>
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
