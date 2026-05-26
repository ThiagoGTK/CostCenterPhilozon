import { useLocation } from "react-router-dom";
import styles from "./Header.module.css";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/orcamento": "Lançamento de Orçamento",
  "/comparativo": "Realizado × Orçado",
  "/workflow": "Fila de Aprovação",
  "/mapeamento/contas": "Contas SIA → Gerencial",
  "/mapeamento/centros-custo": "Centros de Custo",
  "/cadastros/centros-custo": "Centros de Custo Gerenciais",
  "/cadastros/contas-gerenciais": "Plano de Contas Gerencial",
};

const SECTIONS: Record<string, string> = {
  "/dashboard": "Início",
  "/orcamento": "Planejamento",
  "/comparativo": "Análises",
  "/workflow": "Workflow",
  "/mapeamento/contas": "Mapeamentos",
  "/mapeamento/centros-custo": "Mapeamentos",
  "/cadastros/centros-custo": "Cadastros",
  "/cadastros/contas-gerenciais": "Cadastros",
};

export default function Header() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] ?? "FP&A";
  const section = SECTIONS[pathname];

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <div className={styles.accent} />
        <h1 className={styles.title}>{title}</h1>
        {section && <span className={styles.breadcrumb}>{section}</span>}
      </div>
      <div className={styles.actions}>
        <span className={styles.user}>Administrador</span>
      </div>
    </header>
  );
}
