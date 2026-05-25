import styles from "./PageGeneric.module.css";
import wfStyles from "./Workflow.module.css";

const STATUS_COLORS: Record<string, string> = {
  RASCUNHO: wfStyles.rascunho,
  ENVIADO: wfStyles.enviado,
  APROVADO: wfStyles.aprovado,
  REPROVADO: wfStyles.reprovado,
};

const STATUS_LABELS: Record<string, string> = {
  RASCUNHO: "Rascunho",
  ENVIADO: "Aguardando aprovação",
  APROVADO: "Aprovado",
  REPROVADO: "Reprovado",
};

const exemplos = [
  { id: 1, versao: "Original 2025", empresa: "Empresa 1", status: "ENVIADO", enviadoPor: "Ana Silva", enviadoEm: "2025-01-15" },
  { id: 2, versao: "Revisão 1 — 2025", empresa: "Empresa 1", status: "APROVADO", enviadoPor: "Carlos Lima", enviadoEm: "2025-04-10" },
  { id: 3, versao: "Forecast Q3 2025", empresa: "Empresa 1", status: "RASCUNHO", enviadoPor: "—", enviadoEm: "—" },
];

export default function Workflow() {
  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <span className={styles.cardTitle}>Fila de Aprovação de Orçamentos</span>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Versão</th>
                <th>Empresa</th>
                <th>Enviado por</th>
                <th>Data de Envio</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {exemplos.map((wf) => (
                <tr key={wf.id}>
                  <td><strong>{wf.versao}</strong></td>
                  <td>{wf.empresa}</td>
                  <td>{wf.enviadoPor}</td>
                  <td>{wf.enviadoEm}</td>
                  <td>
                    <span className={`${wfStyles.badge} ${STATUS_COLORS[wf.status]}`}>
                      {STATUS_LABELS[wf.status]}
                    </span>
                  </td>
                  <td>
                    {wf.status === "ENVIADO" && (
                      <div className={wfStyles.acoes}>
                        <button className={wfStyles.btnAprovar}>Aprovar</button>
                        <button className={wfStyles.btnReprovar}>Reprovar</button>
                      </div>
                    )}
                    {wf.status === "RASCUNHO" && (
                      <button className={wfStyles.btnEnviar}>Enviar para revisão</button>
                    )}
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
