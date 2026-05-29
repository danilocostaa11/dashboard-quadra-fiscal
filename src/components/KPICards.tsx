import { Banknote, Ruler, DollarSign, Building2, Coins, Home } from 'lucide-react';
import type { Property } from '../data/types';

interface Props {
  properties: Property[];
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value);
}

export default function KPICards({ properties }: Props) {
  const valorTotal = properties.reduce((sum, p) => sum + p.preco, 0);
  const metragemTotal = properties.reduce((sum, p) => sum + p.area, 0);
  const totalCash = properties.reduce((sum, p) => sum + p.cash, 0);
  const totalPermutaFisica = properties.reduce((sum, p) => sum + p.permutaFisica, 0);
  const totalPermutaFinanceira = properties.reduce((sum, p) => sum + p.permutaFinanceira, 0);
  const totalImoveis = properties.length;

  const cards = [
    { label: 'Valor Total', value: formatBRL(valorTotal), icon: Banknote, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Metragem Total', value: `${metragemTotal.toLocaleString('pt-BR')} m²`, icon: Ruler, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Total Cash', value: formatBRL(totalCash), icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Permuta Física', value: formatBRL(totalPermutaFisica), icon: Building2, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Permuta Financeira', value: formatBRL(totalPermutaFinanceira), icon: Coins, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Total Imóveis', value: totalImoveis.toString(), icon: Home, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map(card => {
        const Icon = card.icon;
        return (
          <div key={card.label} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <span className="text-[11px] text-gray-500 font-medium uppercase tracking-wider">{card.label}</span>
            </div>
            <p className="text-lg font-black text-gray-800">{card.value}</p>
          </div>
        );
      })}
    </div>
  );
}
