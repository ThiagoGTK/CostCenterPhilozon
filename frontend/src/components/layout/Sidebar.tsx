import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Calculator,
  BarChart3,
  GitBranch,
  ArrowLeftRight,
  FolderTree,
  Settings,
  Users,
  LogOut,
} from "lucide-react";
import { useAuth, type Perfil } from "../../contexts/AuthContext";
import styles from "./Sidebar.module.css";

interface NavItem {
  to: string;
  icon: React.ElementType;
  label: string;
  perfisPermitidos?: Perfil[];
}

interface Divider {
  divider: true;
  label: string;
  perfisPermitidos?: Perfil[];
}

type Item = NavItem | Divider;

const NAV_ITEMS: Item[] = [
  { to: "/dashboard",   icon: LayoutDashboard, label: "Dashboard" },
  { to: "/orcamento",   icon: Calculator,      label: "Orçamento",          perfisPermitidos: ["ADMIN", "GESTOR"] },
  { to: "/comparativo", icon: BarChart3,        label: "Realizado × Orçado" },
  { to: "/workflow",    icon: GitBranch,        label: "Aprovações" },
  { divider: true, label: "Mapeamentos", perfisPermitidos: ["ADMIN", "GESTOR"] },
  { to: "/mapeamento/contas",        icon: ArrowLeftRight, label: "Contas SIA → Gerencial", perfisPermitidos: ["ADMIN", "GESTOR"] },
  { to: "/mapeamento/centros-custo", icon: ArrowLeftRight, label: "Centros de Custo",        perfisPermitidos: ["ADMIN", "GESTOR"] },
  { divider: true, label: "Cadastros", perfisPermitidos: ["ADMIN", "GESTOR"] },
  { to: "/cadastros/centros-custo",    icon: FolderTree, label: "Centros de Custo",  perfisPermitidos: ["ADMIN", "GESTOR"] },
  { to: "/cadastros/contas-gerenciais", icon: Settings,  label: "Plano Gerencial",   perfisPermitidos: ["ADMIN", "GESTOR"] },
  { divider: true, label: "Administração", perfisPermitidos: ["ADMIN"] },
  { to: "/admin/usuarios", icon: Users, label: "Usuários", perfisPermitidos: ["ADMIN"] },
];

export default function Sidebar() {
  const { usuario, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const perfil = usuario?.perfil as Perfil | undefined;

  function visivel(item: Item): boolean {
    if (!item.perfisPermitidos) return true;
    return perfil != null && item.perfisPermitidos.includes(perfil);
  }

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
          if (!visivel(item)) return null;

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
        {usuario && (
          <div className={styles.userInfo}>
            <span className={styles.userName}>{usuario.nome}</span>
            <span className={styles.userPerfil}>{usuario.perfil}</span>
          </div>
        )}
        <button className={styles.btnLogout} onClick={handleLogout} title="Sair">
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  );
}
