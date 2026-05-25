import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Orcamento from "./pages/Orcamento";
import Comparativo from "./pages/Comparativo";
import Workflow from "./pages/Workflow";
import MapeamentoContas from "./pages/MapeamentoContas";
import MapeamentoCentrosCusto from "./pages/MapeamentoCentrosCusto";
import CentrosCusto from "./pages/CentrosCusto";
import ContasGerenciais from "./pages/ContasGerenciais";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="orcamento" element={<Orcamento />} />
        <Route path="comparativo" element={<Comparativo />} />
        <Route path="workflow" element={<Workflow />} />
        <Route path="mapeamento/contas" element={<MapeamentoContas />} />
        <Route path="mapeamento/centros-custo" element={<MapeamentoCentrosCusto />} />
        <Route path="cadastros/centros-custo" element={<CentrosCusto />} />
        <Route path="cadastros/contas-gerenciais" element={<ContasGerenciais />} />
      </Route>
    </Routes>
  );
}
