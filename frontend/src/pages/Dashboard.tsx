import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line, CartesianGrid,
} from "recharts";
import KpiCard from "../components/ui/KpiCard";
import { DollarSign, TrendingDown, TrendingUp, Activity } from "lucide-react";
import { formatCurrency } from "../services/format";
import styles from "./Dashboard.module.css";

// Dados de exemplo — substituir por dados reais via React Query quando a API estiver rodando
const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

const dadosMensais = MESES.map((mes, i) => ({
  mes,
  orcado: 850000 + Math.random() * 100000,
  realizado: 820000 + Math.random() * 150000,
}));

const despesasPorCC = [
  { cc: "Comercial", valor: 280000 },
  { cc: "Operações", valor: 420000 },
  { cc: "TI", valor: 180000 },
  { cc: "RH", valor: 150000 },
  { cc: "Financeiro", valor: 95000 },
];

const kpis = {
  receitaOrcada: 10200000,
  receitaRealizada: 9850000,
  despesaOrcada: 7800000,
  despesaRealizada: 8100000,
  ebitda: 1750000,
  desvioAbsoluto: -350000,
  desvioPercentual: -3.43,
};

export default function Dashboard() {
  return (
    <div className={styles.page}>
      {/* KPIs */}
      <div className={styles.kpiGrid}>
        <KpiCard
          title="Receita Orçada"
          value={kpis.receitaOrcada}
          icon={DollarSign}
          destaque="neutral"
        />
        <KpiCard
          title="Receita Realizada"
          value={kpis.receitaRealizada}
          variacao={((kpis.receitaRealizada - kpis.receitaOrcada) / kpis.receitaOrcada) * 100}
          icon={TrendingUp}
          destaque={kpis.receitaRealizada >= kpis.receitaOrcada ? "success" : "danger"}
        />
        <KpiCard
          title="Despesa Orçada"
          value={kpis.despesaOrcada}
          icon={DollarSign}
          destaque="neutral"
        />
        <KpiCard
          title="Despesa Realizada"
          value={kpis.despesaRealizada}
          variacao={((kpis.despesaRealizada - kpis.despesaOrcada) / kpis.despesaOrcada) * 100}
          icon={TrendingDown}
          destaque={kpis.despesaRealizada <= kpis.despesaOrcada ? "success" : "danger"}
        />
        <KpiCard
          title="EBITDA"
          value={kpis.ebitda}
          icon={Activity}
          destaque="success"
        />
        <KpiCard
          title="Desvio Total"
          value={kpis.desvioAbsoluto}
          variacao={kpis.desvioPercentual}
          icon={Activity}
          destaque={kpis.desvioAbsoluto >= 0 ? "success" : "danger"}
        />
      </div>

      {/* Gráficos */}
      <div className={styles.chartsRow}>
        {/* Realizado × Orçado por mês */}
        <div className={styles.chartCard}>
          <h2 className={styles.chartTitle}>Realizado × Orçado por Mês</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dadosMensais} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
              <YAxis
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                formatter={(v: number) => formatCurrency(v)}
                contentStyle={{ fontSize: 13 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="orcado" name="Orçado" fill="#bfdbfe" radius={[3, 3, 0, 0]} />
              <Bar dataKey="realizado" name="Realizado" fill="#2563eb" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Despesas por Centro de Custo */}
        <div className={styles.chartCard}>
          <h2 className={styles.chartTitle}>Despesas por Centro de Custo (YTD)</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={despesasPorCC} layout="vertical" barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                type="number"
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                tick={{ fontSize: 12 }}
              />
              <YAxis dataKey="cc" type="category" tick={{ fontSize: 12 }} width={80} />
              <Tooltip
                formatter={(v: number) => formatCurrency(v)}
                contentStyle={{ fontSize: 13 }}
              />
              <Bar dataKey="valor" name="Despesa" fill="#7c3aed" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Receita por mês (linha) */}
      <div className={styles.chartCardFull}>
        <h2 className={styles.chartTitle}>Receita Líquida por Mês</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={dadosMensais}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
            <YAxis
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(v: number) => formatCurrency(v)}
              contentStyle={{ fontSize: 13 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="realizado"
              name="Realizado"
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="orcado"
              name="Orçado"
              stroke="#94a3b8"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
