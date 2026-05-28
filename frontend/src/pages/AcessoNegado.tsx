import { useNavigate } from "react-router-dom";
import { ShieldOff } from "lucide-react";

export default function AcessoNegado() {
  const navigate = useNavigate();
  return (
    <div style={{ padding: "60px 24px", textAlign: "center" }}>
      <ShieldOff size={48} color="#dc2626" style={{ marginBottom: 16 }} />
      <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1a2438", marginBottom: 8 }}>
        Acesso não autorizado
      </h2>
      <p style={{ fontSize: 14, color: "#5a6e8c", marginBottom: 24 }}>
        Você não tem permissão para acessar esta página.
      </p>
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          background: "var(--color-primary)",
          color: "white",
          border: "none",
          borderRadius: 6,
          padding: "8px 20px",
          fontSize: 14,
          cursor: "pointer",
        }}
      >
        Voltar ao Dashboard
      </button>
    </div>
  );
}
