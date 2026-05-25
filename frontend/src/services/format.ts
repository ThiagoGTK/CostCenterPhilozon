export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
}

export function formatMesAno(ano: number, mes: number): string {
  return new Date(ano, mes - 1, 1).toLocaleDateString("pt-BR", {
    month: "short",
    year: "numeric",
  });
}
