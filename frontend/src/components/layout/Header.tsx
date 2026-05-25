import { useLocation } from "react-router-dom";
import styles from "./Header.module.css";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/orcamento": "Lançamento de Orçamento",
  "/comparativo": "Realizado × Orçado",
  "/workflow": "Fila de Aprovação",
  "/mapeamento/contas": "Mapeamento — Contas SIA → Gerencial",
  "/mapeamento/centros-custo": "Mapeamento — Centros de Custo",
  "/cadastros/centros-custo": "Centros de Custo Gerenciais",
  "/cadastros/contas-gerenciais": "Plano de Contas Gerencial",
};

export default function Header() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] ?? "FP&A";

  return (
    <header className={styles.header}>
      <h1 className={styles.title}>{title}</h1>
      <div className={styles.actions}>
        <span className={styles.user}>Administrador</span>
      </div>
    </header>
  );
}
