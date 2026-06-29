import { Property } from '../data/properties';

interface PipelineProps {
  properties: Property[];
}

export default function Pipeline({ properties }: PipelineProps) {
  const emNegociacao = properties.filter(p => p.status === 'Em Negociação');
  const semContato = properties.filter(p => p.status === 'Sem Contato');
  const fechados = properties.filter(p => p.status === 'Fechado');
  const naoVende = properties.filter(p => p.status === 'Não Vende');

  const stages = [
    { key: 'negociacao', label: 'Em Negociação', items: emNegociacao, color: '#f59e0b' },
    { key: 'semcontato', label: 'Sem Contato', items: semContato, color: '#6b7280' },
    { key: 'fechado', label: 'Fechado', items: fechados, color: '#22c55e' },
    { key: 'naovende', label: 'Não Vende', items: naoVende, color: '#ef4444' },
  ];

  return (
    <div className="pipeline">
      <h3>Pipeline de Negociação</h3>
      <div className="pipeline-stages">
        {stages.map(stage => (
          <div key={stage.key} className="pipeline-stage">
            <div className="stage-header" style={{ borderColor: stage.color }}>
              <span className="stage-dot" style={{ backgroundColor: stage.color }} />
              <span>{stage.label} ({stage.items.length})</span>
            </div>
            <div className="stage-items">
              {stage.items.map(p => (
                <div key={p.id} className="stage-item" style={{ borderLeftColor: stage.color }}>
                  <div className="item-title">{p.title}</div>
                  <div className="item-detail">{p.owner.name} · {p.formaPgto || p.owner.action}</div>
                </div>
              ))}
              {stage.items.length === 0 && (
                <div className="stage-empty">Nenhum imóvel</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
