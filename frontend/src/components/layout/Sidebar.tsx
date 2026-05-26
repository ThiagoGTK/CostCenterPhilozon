import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Calculator,
  BarChart3,
  GitBranch,
  ArrowLeftRight,
  FolderTree,
  Settings,
} from "lucide-react";
import styles from "./Sidebar.module.css";

const NAV_ITEMS = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/orcamento", icon: Calculator, label: "Orçamento" },
  { to: "/comparativo", icon: BarChart3, label: "Realizado × Orçado" },
  { to: "/workflow", icon: GitBranch, label: "Aprovações" },
  { divider: true, label: "Mapeamentos" },
  { to: "/mapeamento/contas", icon: ArrowLeftRight, label: "Contas SIA → Gerencial" },
  { to: "/mapeamento/centros-custo", icon: ArrowLeftRight, label: "Centros de Custo" },
  { divider: true, label: "Cadastros" },
  { to: "/cadastros/centros-custo", icon: FolderTree, label: "Centros de Custo" },
  { to: "/cadastros/contas-gerenciais", icon: Settings, label: "Plano Gerencial" },
];

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.brandLogo}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 12 L5 7 L8 9 L11 4 L14 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span>FP&amp;A Philozon</span>
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map((item, idx) => {
          if ("divider" in item && item.divider) {
            return (
              <div key={idx} className={styles.section}>
                {item.label}
              </div>
            );
          }
          if ("to" in item && item.to) {
            const Icon = item.icon!;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ""}`
                }
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </NavLink>
            );
          }
          return null;
        })}
      </nav>

      <div className={styles.footer}>
        v0.1.0 — MVP
      </div>
    </aside>
  );
}
