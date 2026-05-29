import { MapPin, Banknote } from 'lucide-react';
import type { Property } from '../data/types';

const situacaoColors: Record<string, string> = {
  'Fechado': 'bg-emerald-500',
  'Em negociação': 'bg-amber-500',
  'Em contato': 'bg-blue-500',
  'Não vende': 'bg-red-500',
};

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(value);
}

interface Props {
  property: Property;
}

export default function PropertyCard({ property }: Props) {
  const total = property.cash + property.permutaFisica + property.permutaFinanceira;
  const cashPct = total > 0 ? (property.cash / total) * 100 : 0;
  const pfPct = total > 0 ? (property.permutaFisica / total) * 100 : 0;
  const pfiPct = total > 0 ? (property.permutaFinanceira / total) * 100 : 0;
  const badgeColor = situacaoColors[property.situacao] || 'bg-gray-500';

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-[10px] font-mono text-gray-400 tracking-wider">{property.codigo}</span>
          <h3 className="font-bold text-gray-800 flex items-center gap-1.5 mt-0.5">
            <MapPin className="w-4 h-4 text-amber-500" />
            {property.endereco}
          </h3>
          <span className="text-xs text-gray-500">{property.tipo} · {property.area} m² · {property.proprietario}</span>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold text-white ${badgeColor}`}>
          {property.situacao}
        </span>
      </div>

      {/* Preço */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-2xl font-black text-gray-900">{formatBRL(property.preco)}</span>
        <Banknote className="w-4 h-4 text-gray-400" />
      </div>

      {/* Composição financeira */}
      <div className="mb-3">
        <div className="flex h-3 rounded-full overflow-hidden mb-2">
          <div className="bg-emerald-500" style={{ width: `${cashPct}%` }} />
          <div className="bg-blue-500" style={{ width: `${pfPct}%` }} />
          <div className="bg-purple-500" style={{ width: `${pfiPct}%` }} />
        </div>
        <div className="grid grid-cols-3 gap-1 text-[10px]">
          <div>
            <span className="text-emerald-600 font-semibold">Cash</span>
            <p className="text-gray-600">{formatBRL(property.cash)}</p>
          </div>
          <div>
            <span className="text-blue-600 font-semibold">Permuta Física</span>
            <p className="text-gray-600">{formatBRL(property.permutaFisica)}</p>
          </div>
          <div>
            <span className="text-purple-600 font-semibold">Permuta Fin.</span>
            <p className="text-gray-600">{formatBRL(property.permutaFinanceira)}</p>
          </div>
        </div>
      </div>

      {/* Proposta MAC */}
      <div className="border-t border-gray-100 pt-2 flex items-center justify-between">
        <span className="text-xs text-gray-500">Proposta MAC</span>
        <span className="text-sm font-bold text-amber-600">{formatBRL(property.propostaMAC)}</span>
      </div>

      {/* Observações */}
      {property.observacoes && (
        <p className="text-[11px] text-gray-400 mt-2 italic truncate">{property.observacoes}</p>
      )}
    </div>
  );
}
