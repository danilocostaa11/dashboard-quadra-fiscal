import { useState } from 'react';
import { lots } from '../data/lots';
import type { Lot } from '../data/types';

const statusColors: Record<string, string> = {
  'Fechado': '#22c55e',
  'Negociando': '#eab308',
  'Não Vende': '#ef4444',
  'Sem Contato': '#94a3b8',
  'Sem dados': '#f97316',
};

const cutouts = [
  { id: 'stair-1', x: 0, y: 28, w: 7, h: 5 },
  { id: 'stair-2', x: 0, y: 33, w: 27, h: 5 },
  { id: 'stair-3', x: 0, y: 38, w: 46, h: 5 },
  { id: 'stair-4', x: 0, y: 43, w: 71, h: 5 },
  { id: 'street-br', x: 72, y: 75, w: 25.5, h: 20 },
];

export default function QuadraMap() {
  const [selected, setSelected] = useState<Lot | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <div className="w-full">
      {/* Street labels */}
      <div className="text-center mb-2">
        <span className="text-xs font-bold tracking-widest text-amber-800/70">
          R. PROF. APRÍGIO GONZAGA
        </span>
      </div>

      <div className="relative w-full border-2 border-amber-600 rounded-[28px] overflow-hidden shadow-inner"
           style={{ aspectRatio: '1450/760', backgroundColor: '#fefce8', minWidth: 600 }}>
        
        {/* Cutouts */}
        {cutouts.map(c => (
          <div key={c.id} className="absolute bg-white/90" style={{
            left: `${c.x}%`, top: `${c.y}%`, width: `${c.w}%`, height: `${c.h}%`,
            borderTopLeftRadius: c.id === 'street-br' ? '40%' : undefined,
          }} />
        ))}

        {/* Lots */}
        {lots.map(lot => {
          const color = statusColors[lot.status] || '#f97316';
          const isHovered = hovered === lot.id;
          const isSelected = selected?.id === lot.id;
          return (
            <div key={lot.id}
              className="absolute cursor-pointer border-2 border-black/20 transition-all"
              style={{
                left: `${lot.x}%`, top: `${lot.y}%`,
                width: `${lot.width}%`, height: `${lot.height}%`,
                backgroundColor: color,
                transform: `rotate(${lot.rotation || 0}deg)`,
                transformOrigin: 'center bottom',
                filter: isHovered ? 'brightness(1.1)' : undefined,
                zIndex: isSelected ? 20 : isHovered ? 10 : 1,
                boxShadow: isSelected ? '0 0 0 3px rgba(59,130,246,0.4)' : undefined,
              }}
              onMouseEnter={() => setHovered(lot.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => setSelected(lot)}
            >
              <div className="flex flex-col items-center justify-center h-full">
                <span className="text-[0.6rem] font-black text-black/70 leading-tight">{lot.lote}</span>
                <span className="text-[0.55rem] font-semibold text-black/50">{lot.numero}</span>
              </div>
            </div>
          );
        })}

        {/* Bottom street bar */}
        <div className="absolute h-[0.4%] bg-amber-600" style={{ left: '18.8%', right: '1.8%', top: '80.5%' }} />
        
        <div className="absolute bottom-3 left-0 right-0 text-center">
          <span className="text-xs font-bold tracking-widest text-amber-800/70">R. MARIA FAGNANI</span>
        </div>
        
        <div className="absolute bottom-1 right-4 text-[10px] font-semibold" style={{ color: '#65441a' }}>
          Área total: 3.480 m²
        </div>
      </div>

      {/* Lot popup */}
      {selected && (
        <div className="mt-4 p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-amber-200 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-lg text-gray-800">{selected.lote} — {selected.numero}</h3>
            <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <span className="inline-block px-3 py-1 rounded-full text-sm font-medium text-white" style={{ backgroundColor: statusColors[selected.status] }}>
            {selected.status}
          </span>
          {selected.propertyId && (
            <p className="mt-2 text-sm text-gray-600">Vinculado à propriedade #{selected.propertyId}</p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-4 justify-center">
        {Object.entries(statusColors).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-xs text-gray-600">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
