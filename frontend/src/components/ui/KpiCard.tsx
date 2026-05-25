import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";
import styles from "./KpiCard.module.css";
import { formatCurrency, formatPercent } from "../../services/format";

interface KpiCardProps {
  title: string;
  value: number;
  variacao?: number;
  variacaoLabel?: string;
  icon?: LucideIcon;
  tipo?: "currency" | "percent" | "number";
  destaque?: "success" | "danger" | "neutral";
}

export default function KpiCard({
  title,
  value,
  variacao,
  variacaoLabel,
  icon: Icon,
  tipo = "currency",
  destaque = "neutral",
}: KpiCardProps) {
  const formattedValue =
    tipo === "currency"
      ? formatCurrency(value)
      : tipo === "percent"
      ? formatPercent(value)
      : value.toLocaleString("pt-BR");

  const variacaoPositiva = variacao !== undefined && variacao > 0;
  const variacaoNegativa = variacao !== undefined && variacao < 0;

  return (
    <div className={`${styles.card} ${styles[destaque]}`}>
      <div className={styles.top}>
        <span className={styles.title}>{title}</span>
        {Icon && (
          <div className={styles.iconWrap}>
            <Icon size={18} />
          </div>
        )}
      </div>
      <div className={styles.value}>{formattedValue}</div>
      {variacao !== undefined && (
        <div
          className={`${styles.variacao} ${
            variacaoPositiva ? styles.positivo : variacaoNegativa ? styles.negativo : ""
          }`}
        >
          {variacaoPositiva ? (
            <TrendingUp size={13} />
          ) : variacaoNegativa ? (
            <TrendingDown size={13} />
          ) : (
            <Minus size={13} />
          )}
          <span>
            {variacao > 0 ? "+" : ""}
            {formatPercent(Math.abs(variacao))} {variacaoLabel ?? "vs orçado"}
          </span>
        </div>
      )}
    </div>
  );
}
