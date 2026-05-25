import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Calculator,
  BarChart3,
  GitBranch,
  ArrowLeftRight,
  FolderTree,
  Settings,
  TrendingUp,
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
        <TrendingUp size={22} />
        <span>FP&amp;A Financeiro</span>
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
                <Icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            );
          }
          return null;
        })}
      </nav>

      <div className={styles.footer}>
        <span>v0.1.0 — MVP</span>
      </div>
    </aside>
  );
}
