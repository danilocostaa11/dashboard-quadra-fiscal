import type { PipelineStage } from './types';

export const pipeline: PipelineStage[] = [
  { name: "Novo", count: 24, valor: 12500000, color: "bg-blue-500" },
  { name: "Contato", count: 18, valor: 9800000, color: "bg-purple-500" },
  { name: "Visita", count: 12, valor: 7200000, color: "bg-amber-500" },
  { name: "Proposta", count: 8, valor: 5600000, color: "bg-orange-500" },
  { name: "Fechado", count: 5, valor: 3800000, color: "bg-emerald-500" },
];

export function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value);
}

export function formatCompact(value: number): string {
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(0)}K`;
  return `R$ ${value}`;
}
