import { pipeline, formatBRL, formatCompact } from '../data/pipeline';

export default function PipelineWidget() {
  const maxValor = Math.max(...pipeline.map(s => s.valor));

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Pipeline de Prospecção</h2>
      <div className="space-y-3">
        {pipeline.map((stage) => {
          const pct = maxValor > 0 ? (stage.valor / maxValor) * 100 : 0;
          return (
            <div key={stage.name}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-700">{stage.name}</span>
                  <span className="text-[11px] text-gray-400">({stage.count} imóveis)</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-gray-800">{formatBRL(stage.valor)}</span>
                  <span className="text-[10px] text-gray-400 ml-1.5">({formatCompact(stage.valor)})</span>
                </div>
              </div>
              <div className="h-6 bg-gray-100 rounded-lg overflow-hidden relative">
                <div
                  className={`h-full rounded-lg ${stage.color} flex items-center justify-end pr-2 transition-all`}
                  style={{ width: `${Math.max(pct, 8)}%` }}
                >
                  {pct > 20 && <span className="text-[10px] font-bold text-white">{Math.round(pct)}%</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-gray-500">Total no Pipeline</span>
        <span className="text-base font-black text-gray-800">
          {formatBRL(pipeline.reduce((sum, s) => sum + s.valor, 0))}
        </span>
      </div>
    </div>
  );
}
