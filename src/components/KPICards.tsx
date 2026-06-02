import { properties } from '../data/properties';
import { lots } from '../data/lots';

export default function KPICards() {
  const totalLots = lots.length;
  const lotsWithData = lots.filter(l => l.propertyId).length;
  const emNegociacao = properties.filter(p => p.status === 'Em Negociação').length;
  const semContato = properties.filter(p => p.status === 'Sem Contato').length;
  const totalCash = properties.reduce((s, p) => s + p.cash, 0);
  const totalPermuta = properties.reduce((s, p) => s + p.permutaFisica, 0);
  const totalValue = properties.reduce((s, p) => s + p.price, 0);

  const fmt = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);
  const fmtM = (v: number) => (v / 1_000_000).toFixed(1).replace('.', ',') + 'M';

  const cards = [
    { label: 'Lotes mapeados', value: totalLots, sub: `${lotsWithData} com dados`, icon: '🗺️' },
    { label: 'Em negociação', value: emNegociacao, sub: `de ${lotsWithData} imóveis`, icon: '🤝' },
    { label: 'Sem contato', value: semContato, sub: 'a abordar', icon: '📞' },
    { label: 'Valor total estimado', value: fmtM(totalValue), sub: fmt(totalValue), icon: '💰' },
    { label: 'Cash planejado', value: fmtM(totalCash), sub: fmt(totalCash), icon: '💵' },
    { label: 'Permuta física', value: fmtM(totalPermuta), sub: fmt(totalPermuta), icon: '🏠' },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div key={c.label} className="kpi-card">
          <div className="kpi-icon">{c.icon}</div>
          <div className="kpi-content">
            <div className="kpi-value">{c.value}</div>
            <div className="kpi-label">{c.label}</div>
            <div className="kpi-sub">{c.sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}