import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import { formatCurrency } from "../services/format";
import { useVersoes, useEmpresaAtiva, useContasGerenciais } from "../hooks/useDimensoes";
import { useComparativo } from "../hooks/useComparativo";
import { ComparativoItem, ContaGerencial } from "../services/api";
import styles from "./Dashboard.module.css";
import { useState } from "react";

const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

// Soma todos os meses por conta gerencial
function agruparPorConta(itens: ComparativoItem[]) {
  const mapa = new Map<string, { codigo: string; nome: string; orcado: number; realizado: number }>();
  for (const item of itens) {
    const key = item.conta_gerencial_codigo;
    if (!mapa.has(key)) {
      mapa.set(key, { codigo: key, nome: item.conta_gerencial_nome, orcado: 0, realizado: 0 });
    }
    const e = mapa.get(key)!;
    e.orcado += Number(item.valor_orcado);
    e.realizado += Number(item.valor_realizado);
  }
  return Array.from(mapa.values()).sort((a, b) => a.codigo.localeCompare(b.codigo));
}

// Agrega por mês para o gráfico de evolução
function agruparPorMes(itens: ComparativoItem[]) {
  const mapa: Record<number, { orcado: number; realizado: number }> = {};
  for (const item of itens) {
    if (!mapa[item.mes]) mapa[item.mes] = { orcado: 0, realizado: 0 };
    mapa[item.mes].orcado += Number(item.valor_orcado);
    mapa[item.mes].realizado += Number(item.valor_realizado);
  }
  return Object.entries(mapa)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([mes, v]) => ({ mes: MESES[Number(mes) - 1], ...v }));
}

function variacao(real: number, orc: number) {
  if (orc === 0) return null;
  return ((real - orc) / Math.abs(orc)) * 100;
}

function FmtVar({ real, orc, inverter = false }: { real: number; orc: number; inverter?: boolean }) {
  const v = variacao(real, orc);
  if (v === null) return <td className={styles.varCol}>—</td>;
  // Para despesas, consumir menos que o orçado é positivo → inverter=true
  const positivo = inverter ? v <= 0 : v >= 0;
  return (
    <td className={`${styles.varCol} ${positivo ? styles.pos : styles.neg}`}>
      {v > 0 ? "+" : ""}{v.toFixed(1)}%
    </td>
  );
}

export default function Dashboard() {
  const anoAtual = new Date().getFullYear();
  const [ano, setAno] = useState(anoAtual);

  const { idEmpresa, empresa } = useEmpresaAtiva();
  const { data: versoes = [] } = useVersoes(ano);
  const { data: contas = [] } = useContasGerenciais();
  const primeiraVersao = versoes[0];

  const { data: comparativo, isLoading, isError } = useComparativo(
    ano,
    primeiraVersao?.id,
    idEmpresa != null ? { id_empresa: idEmpresa } : undefined
  );

  // Mapa código → tipo da conta
  const tipoMap = new Map<string, ContaGerencial["tipo"]>();
  for (const c of contas) tipoMap.set(c.codigo, c.tipo);

  const contasAgg = comparativo ? agruparPorConta(comparativo.itens) : [];
  const dadosMensais = comparativo ? agruparPorMes(comparativo.itens) : [];

  // Separa receitas e despesas pelo tipo cadastrado ou pelo código
  const receitas = contasAgg.filter((c) => {
    const tipo = tipoMap.get(c.codigo);
    return tipo === "RECEITA" || (!tipo && c.codigo.startsWith("1"));
  });
  const despesas = contasAgg.filter((c) => {
    const tipo = tipoMap.get(c.codigo);
    return tipo === "DESPESA" || (!tipo && (c.codigo.startsWith("3") || c.codigo.startsWith("4") || c.codigo.startsWith("5")));
  });

  const totRecReal = receitas.reduce((s, c) => s + c.realizado, 0);
  const totRecOrc  = receitas.reduce((s, c) => s + c.orcado, 0);
  const totDespReal = despesas.reduce((s, c) => s + c.realizado, 0);
  const totDespOrc  = despesas.reduce((s, c) => s + c.orcado, 0);
  const ebitdaReal = totRecReal - totDespReal;
  const ebitdaOrc  = totRecOrc - totDespOrc;

  const pctRec   = totRecOrc  > 0 ? (totRecReal  / totRecOrc)  * 100 : 0;
  const pctDesp  = totDespOrc > 0 ? (totDespReal / totDespOrc) * 100 : 0;
  const pctEbitda = ebitdaOrc !== 0 ? (ebitdaReal / Math.abs(ebitdaOrc)) * 100 : 0;

  const hasData = comparativo && comparativo.itens.length > 0;

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

      {/* Barra de contexto */}
      <div className={styles.contextBar}>
        <div className={styles.contextLeft}>
          <select value={ano} onChange={(e) => setAno(Number(e.target.value))} className={styles.select}>
            {[anoAtual - 1, anoAtual, anoAtual + 1].map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          {primeiraVersao && <span className={styles.badgePlan}>{primeiraVersao.nome}</span>}
          {empresa && <span className={styles.badgeEmpresa}>{empresa.nome}</span>}
          {isLoading && <span className={styles.loading}>Carregando...</span>}
        </div>
        <span className={styles.horizonte}>Jan {ano} – Dez {ano}</span>
      </div>

      {/* Grid principal: DRE + Mapa de Indicadores */}
      <div className={styles.mainGrid}>

        {/* DRE resumida */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <h2 className={styles.cardTitle}>Demonstrativo de Resultados Resumido</h2>
              <p className={styles.cardSub}>Jan {ano} a Dez {ano}</p>
            </div>
          </div>

          {hasData ? (
            <table className={styles.dreTable}>
              <thead>
                <tr>
                  <th className={styles.colEstrutura}>Estrutura</th>
                  <th className={styles.colVal}>Realizado (R$)</th>
                  <th className={styles.colVal}>Planejado (R$)</th>
                  <th className={styles.colVar}>Variação</th>
                </tr>
              </thead>
              <tbody>
                {/* Receitas */}
                {receitas.map((c) => (
                  <tr key={c.codigo} className={styles.rowConta}>
                    <td>{c.nome}</td>
                    <td className={styles.valCol}>{formatCurrency(c.realizado)}</td>
                    <td className={styles.valCol}>{formatCurrency(c.orcado)}</td>
                    <FmtVar real={c.realizado} orc={c.orcado} />
                  </tr>
                ))}
                {receitas.length > 0 && (
                  <tr className={styles.rowSubtotal}>
                    <td>= Receita Total</td>
                    <td className={styles.valCol}>{formatCurrency(totRecReal)}</td>
                    <td className={styles.valCol}>{formatCurrency(totRecOrc)}</td>
                    <FmtVar real={totRecReal} orc={totRecOrc} />
                  </tr>
                )}

                <tr className={styles.rowSpacer}><td colSpan={4} /></tr>

                {/* Despesas */}
                {despesas.map((c) => (
                  <tr key={c.codigo} className={styles.rowConta}>
                    <td>- {c.nome}</td>
                    <td className={styles.valCol}>{formatCurrency(c.realizado)}</td>
                    <td className={styles.valCol}>{formatCurrency(c.orcado)}</td>
                    <FmtVar real={c.realizado} orc={c.orcado} inverter />
                  </tr>
                ))}
                {despesas.length > 0 && (
                  <tr className={styles.rowSubtotal}>
                    <td>= Total Despesas</td>
                    <td className={styles.valCol}>{formatCurrency(totDespReal)}</td>
                    <td className={styles.valCol}>{formatCurrency(totDespOrc)}</td>
                    <FmtVar real={totDespReal} orc={totDespOrc} inverter />
                  </tr>
                )}

                {/* EBITDA */}
                <tr className={styles.rowEbitda}>
                  <td>= EBITDA</td>
                  <td className={styles.valCol}>{formatCurrency(ebitdaReal)}</td>
                  <td className={styles.valCol}>{formatCurrency(ebitdaOrc)}</td>
                  <FmtVar real={ebitdaReal} orc={ebitdaOrc} />
                </tr>
              </tbody>
            </table>
          ) : !isLoading ? (
            <div className={styles.emptyState}>
              {versoes.length === 0
                ? "Nenhuma versão de orçamento cadastrada para este ano."
                : "Nenhum dado disponível. Execute o ETL e cadastre o orçamento."}
            </div>
          ) : null}
        </div>

        {/* Mapa de Indicadores */}
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Mapa de Indicadores</h2>
          <p className={styles.cardSub}>Valores Realizados</p>

          <div className={styles.mapaGrid}>
            {/* Receita */}
            <div className={styles.mapaBloco} style={{ background: "var(--color-primary)" }}>
              <span className={styles.mapaPct}>{pctRec.toFixed(1)}%</span>
              <span className={styles.mapaLabel}>Receita Total</span>
              <span className={styles.mapaValor}>{formatCurrency(totRecReal)}</span>
            </div>

            {/* Despesas */}
            <div
              className={styles.mapaBloco}
              style={{ background: pctDesp > 100 ? "var(--color-danger)" : "var(--color-primary)" }}
            >
              <span className={styles.mapaPct}>{pctDesp.toFixed(1)}%</span>
              <span className={styles.mapaLabel}>Despesas</span>
              <span className={styles.mapaValor}>{formatCurrency(totDespReal)}</span>
            </div>

            {/* EBITDA (full width) */}
            <div
              className={`${styles.mapaBloco} ${styles.mapaBlocoFull}`}
              style={{ background: ebitdaReal >= 0 ? "var(--color-accent)" : "var(--color-danger)" }}
            >
              <span className={styles.mapaPct}>{pctEbitda.toFixed(1)}%</span>
              <span className={styles.mapaLabel}>EBITDA</span>
              <span className={styles.mapaValor}>{formatCurrency(ebitdaReal)}</span>
            </div>
          </div>

          {/* Barra de progresso do EBITDA */}
          <div className={styles.gauge}>
            <div className={styles.gaugeHeader}>
              <span className={styles.gaugeLabel}>Realizado acumulado</span>
              <span className={styles.gaugePct}>{pctEbitda.toFixed(0)}% do planejado</span>
            </div>
            <div className={styles.gaugeValor}>{formatCurrency(ebitdaReal)}</div>
            <div className={styles.gaugeBar}>
              <div
                className={styles.gaugeFill}
                style={{ width: `${Math.min(Math.max(pctEbitda, 0), 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de evolução mensal */}
      {hasData && dadosMensais.length > 0 && (
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Evolução Mensal — Realizado × Planejado</h2>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={dadosMensais} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
              <defs>
                <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#005f9c" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#005f9c" stopOpacity={0.03} />
                </linearGradient>
                <linearGradient id="gradOrc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#08b0a0" stopOpacity={0.18} />
                  <stop offset="95%" stopColor="#08b0a0" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
              <XAxis dataKey="mes" tick={{ fontSize: 12, fill: "#5a6e8c" }} />
              <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12, fill: "#5a6e8c" }} />
              <Tooltip
                formatter={(v: number) => formatCurrency(v)}
                contentStyle={{ fontSize: 13, borderColor: "#e0e8f0", borderRadius: 8 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area
                type="monotone"
                dataKey="realizado"
                name="Realizado"
                stroke="#005f9c"
                strokeWidth={2.5}
                fill="url(#gradReal)"
                dot={{ r: 3, fill: "#005f9c", strokeWidth: 0 }}
                activeDot={{ r: 5 }}
              />
              <Area
                type="monotone"
                dataKey="orcado"
                name="Planejado"
                stroke="#08b0a0"
                strokeWidth={2}
                strokeDasharray="6 4"
                fill="url(#gradOrc)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
