import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { api } from "../services/api";

export type Perfil = "ADMIN" | "GESTOR" | "COLABORADOR";

export interface UsuarioLogado {
  id: number;
  nome: string;
  email: string;
  perfil: Perfil;
  ativo: boolean;
}

interface AuthContextValue {
  usuario: UsuarioLogado | null;
  token: string | null;
  loading: boolean;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isGestor: boolean;
  isColaborador: boolean;
  canWrite: boolean;   // ADMIN ou GESTOR
}

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "fpa_token";
const USUARIO_KEY = "fpa_usuario";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [usuario, setUsuario] = useState<UsuarioLogado | null>(() => {
    const raw = localStorage.getItem(USUARIO_KEY);
    return raw ? (JSON.parse(raw) as UsuarioLogado) : null;
  });
  const [loading, setLoading] = useState(false);

  // Configura o header de autorização sempre que o token mudar
  useEffect(() => {
    if (token) {
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common["Authorization"];
    }
  }, [token]);

  const login = useCallback(async (email: string, senha: string) => {
    setLoading(true);
    try {
      const { data } = await api.post<{ access_token: string; usuario: UsuarioLogado }>(
        "/auth/login",
        { email, senha }
      );
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USUARIO_KEY, JSON.stringify(data.usuario));
      setToken(data.access_token);
      setUsuario(data.usuario);
      api.defaults.headers.common["Authorization"] = `Bearer ${data.access_token}`;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USUARIO_KEY);
    setToken(null);
    setUsuario(null);
    delete api.defaults.headers.common["Authorization"];
  }, []);

  const perfil = usuario?.perfil;

  return (
    <AuthContext.Provider
      value={{
        usuario,
        token,
        loading,
        login,
        logout,
        isAdmin: perfil === "ADMIN",
        isGestor: perfil === "GESTOR",
        isColaborador: perfil === "COLABORADOR",
        canWrite: perfil === "ADMIN" || perfil === "GESTOR",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  return ctx;
}
