import { properties } from '../data/properties';

export default function Pipeline() {
  const emNegociacao = properties.filter(p => p.status === 'Em Negociação');
  const semContato = properties.filter(p => p.status === 'Sem Contato');

  const stageColor = (s: string) => {
    if (s === 'Em Negociação') return '#f59e0b';
    if (s === 'Sem Contato') return '#6b7280';
    return '#374151';
  };

  return (
    <div className="pipeline">
      <h3>Pipeline de Negociação</h3>
      <div className="pipeline-stages">
        <div className="pipeline-stage">
          <div className="stage-header" style={{ borderColor: '#f59e0b' }}>
            <span className="stage-dot" style={{ backgroundColor: '#f59e0b' }} />
            <span>Em Negociação ({emNegociacao.length})</span>
          </div>
          <div className="stage-items">
            {emNegociacao.map(p => (
              <div key={p.id} className="stage-item" style={{ borderLeftColor: stageColor(p.status) }}>
                <div className="item-title">{p.title}</div>
                <div className="item-detail">{p.owner.name} · {p.formaPgto}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="pipeline-stage">
          <div className="stage-header" style={{ borderColor: '#6b7280' }}>
            <span className="stage-dot" style={{ backgroundColor: '#6b7280' }} />
            <span>Sem Contato ({semContato.length})</span>
          </div>
          <div className="stage-items">
            {semContato.map(p => (
              <div key={p.id} className="stage-item" style={{ borderLeftColor: stageColor(p.status) }}>
                <div className="item-title">{p.title}</div>
                <div className="item-detail">{p.owner.name} · {p.owner.action}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}