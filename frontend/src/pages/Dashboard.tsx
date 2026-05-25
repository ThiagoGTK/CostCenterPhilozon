import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  LineChart, Line, CartesianGrid,
} from "recharts";
import KpiCard from "../components/ui/KpiCard";
import { DollarSign, TrendingDown, TrendingUp, Activity } from "lucide-react";
import { formatCurrency } from "../services/format";
import { useVersoes } from "../hooks/useDimensoes";
import { useComparativo } from "../hooks/useComparativo";
import { ComparativoItem } from "../services/api";
import styles from "./Dashboard.module.css";
import { useState } from "react";

const NOMES_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

function agruparPorMes(itens: ComparativoItem[]) {
  const mapa: Record<number, { orcado: number; realizado: number }> = {};
  for (const item of itens) {
    if (!mapa[item.mes]) mapa[item.mes] = { orcado: 0, realizado: 0 };
    mapa[item.mes].orcado += Number(item.valor_orcado);
    mapa[item.mes].realizado += Number(item.valor_realizado);
  }
  return Object.entries(mapa)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([mes, vals]) => ({ mes: NOMES_MESES[Number(mes) - 1], ...vals }));
}

function agruparDespesasPorCC(itens: ComparativoItem[]) {
  const mapa: Record<string, number> = {};
  for (const item of itens.filter((i) => i.conta_gerencial_codigo.startsWith("4"))) {
    const cc = item.centro_custo_nome;
    mapa[cc] = (mapa[cc] ?? 0) + Number(item.valor_realizado);
  }
  return Object.entries(mapa)
    .map(([cc, valor]) => ({ cc, valor }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 6);
}

export default function Dashboard() {
  const anoAtual = new Date().getFullYear();
  const [ano, setAno] = useState(anoAtual);

  const { data: versoes = [] } = useVersoes(ano);
  const primeiraVersao = versoes[0];

  const { data: comparativo, isLoading, isError } = useComparativo(ano, primeiraVersao?.id);

  const dadosMensais = comparativo ? agruparPorMes(comparativo.itens) : [];
  const despesasPorCC = comparativo ? agruparDespesasPorCC(comparativo.itens) : [];

  const totalOrcado = Number(comparativo?.total_orcado ?? 0);
  const totalRealizado = Number(comparativo?.total_realizado ?? 0);
  const varAbs = Number(comparativo?.variacao_absoluta_total ?? 0);
  const varPct = Number(comparativo?.variacao_percentual_total ?? 0);

  // KPIs derivados: despesas são contas que começam com "4"
  const despesaOrcada = comparativo
    ? comparativo.itens.filter((i) => i.conta_gerencial_codigo.startsWith("4")).reduce((s, i) => s + Number(i.valor_orcado), 0)
    : 0;
  const despesaRealizada = comparativo
    ? comparativo.itens.filter((i) => i.conta_gerencial_codigo.startsWith("4")).reduce((s, i) => s + Number(i.valor_realizado), 0)
    : 0;

  if (isError && !isLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <p>Não foi possível carregar os dados. Verifique se a API está rodando e se há versões de orçamento cadastradas.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Seletor de ano + versão */}
      <div className={styles.filterRow}>
        <select
          value={ano}
          onChange={(e) => setAno(Number(e.target.value))}
          className={styles.select}
        >
          {[anoAtual - 1, anoAtual, anoAtual + 1].map((a) => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        {primeiraVersao && (
          <span className={styles.versaoLabel}>{primeiraVersao.nome}</span>
        )}
        {isLoading && <span className={styles.loading}>Carregando...</span>}
      </div>

      {/* KPIs */}
      <div className={styles.kpiGrid}>
        <KpiCard title="Receita Orçada" value={totalOrcado} icon={DollarSign} destaque="neutral" />
        <KpiCard
          title="Receita Realizada"
          value={totalRealizado}
          variacao={totalOrcado ? ((totalRealizado - totalOrcado) / totalOrcado) * 100 : 0}
          icon={TrendingUp}
          destaque={totalRealizado >= totalOrcado ? "success" : "danger"}
        />
        <KpiCard title="Despesa Orçada" value={despesaOrcada} icon={DollarSign} destaque="neutral" />
        <KpiCard
          title="Despesa Realizada"
          value={despesaRealizada}
          variacao={despesaOrcada ? ((despesaRealizada - despesaOrcada) / despesaOrcada) * 100 : 0}
          icon={TrendingDown}
          destaque={despesaRealizada <= despesaOrcada ? "success" : "danger"}
        />
        <KpiCard
          title="Resultado"
          value={totalRealizado - despesaRealizada}
          icon={Activity}
          destaque={totalRealizado - despesaRealizada >= 0 ? "success" : "danger"}
        />
        <KpiCard
          title="Desvio Total"
          value={varAbs}
          variacao={varPct}
          icon={Activity}
          destaque={varAbs >= 0 ? "success" : "danger"}
        />
      </div>

      {/* Gráficos */}
      {comparativo && comparativo.itens.length > 0 ? (
        <>
          <div className={styles.chartsRow}>
            <div className={styles.chartCard}>
              <h2 className={styles.chartTitle}>Realizado × Orçado por Mês</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={dadosMensais} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ fontSize: 13 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="orcado" name="Orçado" fill="#bfdbfe" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="realizado" name="Realizado" fill="#2563eb" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className={styles.chartCard}>
              <h2 className={styles.chartTitle}>Despesas Realizadas por CC (YTD)</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={despesasPorCC} layout="vertical" barSize={20}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
                  <YAxis dataKey="cc" type="category" tick={{ fontSize: 12 }} width={90} />
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ fontSize: 13 }} />
                  <Bar dataKey="valor" name="Despesa" fill="#7c3aed" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className={styles.chartCardFull}>
            <h2 className={styles.chartTitle}>Receita: Realizado × Orçado por Mês</h2>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={dadosMensais}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ fontSize: 13 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="realizado" name="Realizado" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="orcado" name="Orçado" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      ) : !isLoading && (
        <div className={styles.emptyState}>
          <p>
            {versoes.length === 0
              ? "Nenhuma versão de orçamento cadastrada para este ano."
              : "Nenhum dado de comparativo disponível. Execute o ETL e cadastre o orçamento."}
          </p>
        </div>
      )}
    </div>
  );
}
