import { Property } from '../data/properties';
import { lots } from '../data/lots';

interface KPICardsProps {
  properties: Property[];
}

export default function KPICards({ properties }: KPICardsProps) {
  const totalLots = lots.length;
  const lotsWithData = properties.length;
  const emNegociacao = properties.filter(p => p.status === 'Em Negociação').length;
  const semContato = properties.filter(p => p.status === 'Sem Contato').length;
  const fechados = properties.filter(p => p.status === 'Fechado').length;
  const naoVende = properties.filter(p => p.status === 'Não Vende').length;

  const totalCash = properties.reduce((s, p) => s + (Number(p.cash) || 0), 0);
  const totalPermuta = properties.reduce((s, p) => s + (Number(p.permutaFisica) || 0), 0);
  const totalValue = properties.reduce((s, p) => s + (Number(p.price) || 0), 0);
  const totalProposta = totalCash + totalPermuta;
  const ticketMedio = lotsWithData > 0 ? totalProposta / lotsWithData : 0;
  const pctNegociacao = lotsWithData > 0 ? Math.round((emNegociacao / lotsWithData) * 100) : 0;

  const fmt = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);
  const fmtM = (v: number) => {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace('.', ',') + 'M';
    if (v >= 1_000) return (v / 1_000).toFixed(0) + 'k';
    return String(v);
  };

  const cards = [
    { label: 'Lotes mapeados', value: totalLots, sub: `${lotsWithData} com dados`, icon: '🗺️' },
    { label: 'Em negociação', value: emNegociacao, sub: `${pctNegociacao}% dos imóveis`, icon: '🤝' },
    { label: 'Sem contato', value: semContato, sub: 'a abordar', icon: '📞' },
    { label: 'Fechados', value: fechados, sub: fechados > 0 ? '✅ concretizado' : '—', icon: '✅' },
    { label: 'Valor total estimado', value: fmtM(totalValue), sub: fmt(totalValue), icon: '💰' },
    { label: 'Total propostas', value: fmtM(totalProposta), sub: fmt(totalProposta), icon: '📋' },
    { label: 'Cash planejado', value: fmtM(totalCash), sub: fmt(totalCash), icon: '💵' },
    { label: 'Permuta física', value: fmtM(totalPermuta), sub: fmt(totalPermuta), icon: '🏠' },
    { label: 'Ticket médio', value: fmtM(ticketMedio), sub: fmt(ticketMedio), icon: '📊' },
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
