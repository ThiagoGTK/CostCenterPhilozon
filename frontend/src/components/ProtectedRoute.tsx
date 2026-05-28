import { Navigate, useLocation } from "react-router-dom";
import { useAuth, type Perfil } from "../contexts/AuthContext";

interface Props {
  children: React.ReactNode;
  /** Perfis permitidos. Se omitido, qualquer usuário autenticado pode acessar. */
  perfisPermitidos?: Perfil[];
}

export default function ProtectedRoute({ children, perfisPermitidos }: Props) {
  const { usuario } = useAuth();
  const location = useLocation();

  if (!usuario) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (perfisPermitidos && !perfisPermitidos.includes(usuario.perfil)) {
    return <Navigate to="/acesso-negado" replace />;
  }

  return <>{children}</>;
}
