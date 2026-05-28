import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Orcamento from "./pages/Orcamento";
import Comparativo from "./pages/Comparativo";
import Workflow from "./pages/Workflow";
import MapeamentoContas from "./pages/MapeamentoContas";
import MapeamentoCentrosCusto from "./pages/MapeamentoCentrosCusto";
import CentrosCusto from "./pages/CentrosCusto";
import ContasGerenciais from "./pages/ContasGerenciais";
import Usuarios from "./pages/Usuarios";
import AcessoNegado from "./pages/AcessoNegado";

export default function App() {
  return (
    <Routes>
      {/* Rota pública */}
      <Route path="/login" element={<Login />} />

      {/* Rotas protegidas — qualquer usuário autenticado */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="acesso-negado" element={<AcessoNegado />} />

        {/* Visualização — todos os perfis */}
        <Route path="dashboard"   element={<Dashboard />} />
        <Route path="comparativo" element={<Comparativo />} />
        <Route path="workflow"    element={<Workflow />} />

        {/* Escrita operacional — ADMIN e GESTOR */}
        <Route
          path="orcamento"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN", "GESTOR"]}>
              <Orcamento />
            </ProtectedRoute>
          }
        />
        <Route
          path="mapeamento/contas"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN", "GESTOR"]}>
              <MapeamentoContas />
            </ProtectedRoute>
          }
        />
        <Route
          path="mapeamento/centros-custo"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN", "GESTOR"]}>
              <MapeamentoCentrosCusto />
            </ProtectedRoute>
          }
        />
        <Route
          path="cadastros/centros-custo"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN", "GESTOR"]}>
              <CentrosCusto />
            </ProtectedRoute>
          }
        />
        <Route
          path="cadastros/contas-gerenciais"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN", "GESTOR"]}>
              <ContasGerenciais />
            </ProtectedRoute>
          }
        />

        {/* Administração — somente ADMIN */}
        <Route
          path="admin/usuarios"
          element={
            <ProtectedRoute perfisPermitidos={["ADMIN"]}>
              <Usuarios />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
