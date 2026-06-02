import { properties } from '../data/properties';
import { lots } from '../data/lots';

interface PropertyCardProps {
  lotId: string | null;
}

export default function PropertyCard({ lotId }: PropertyCardProps) {
  if (!lotId) {
    return (
      <div className="property-card empty">
        <div className="card-icon">🗺️</div>
        <h3>Selecione um lote no mapa</h3>
        <p>Clique em um lote para ver detalhes do imóvel</p>
      </div>
    );
  }

  const prop = properties.find(p => p.lotId === lotId);
  const lot = lots.find(l => l.id === lotId);

  if (!prop || !lot) {
    return (
      <div className="property-card empty">
        <div className="card-icon">📋</div>
        <h3>Lote sem dados cadastrais</h3>
        <p>{lot?.lote} — {lot?.numero}</p>
      </div>
    );
  }

  const statusColor = prop.status === 'Em Negociação' ? '#f59e0b' : prop.status === 'Sem Contato' ? '#6b7280' : '#374151';

  const formatCurrency = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);

  return (
    <div className="property-card">
      <div className="card-header" style={{ borderColor: statusColor }}>
        <div className="card-header-left">
          <span className="card-lote">{lot.lote}</span>
          <span className="card-numero">{lot.numero}</span>
        </div>
        <span className="card-status" style={{ backgroundColor: statusColor }}>{prop.status}</span>
      </div>

      <div className="card-body">
        <div className="card-row">
          <label>Endereço</label>
          <span>{prop.address}</span>
        </div>
        <div className="card-row">
          <label>Inscrição</label>
          <span>{prop.code}</span>
        </div>
        <div className="card-row">
          <label>Área</label>
          <span>{prop.area}m²</span>
        </div>
        <div className="card-row">
          <label>Tipo</label>
          <span>{prop.type === 'casa' ? '🏠 Casa' : '🏗️ Terreno'}</span>
        </div>
        <div className="card-row">
          <label>Preço estimado</label>
          <span className="price">{formatCurrency(prop.price)}</span>
        </div>

        <div className="card-divider" />

        <div className="card-row">
          <label>Proposta MAC</label>
          <span className="proposal">{prop.propostaMAC}</span>
        </div>
        <div className="card-row">
          <label>Forma pgto</label>
          <span>{prop.formaPgto}</span>
        </div>
        <div className="card-row">
          <label>Cash</label>
          <span>{formatCurrency(prop.cash)}</span>
        </div>
        {prop.permutaFisica > 0 && (
          <div className="card-row">
            <label>Permuta física</label>
            <span>{formatCurrency(prop.permutaFisica)}</span>
          </div>
        )}

        <div className="card-divider" />

        <div className="card-row">
          <label>Proprietário</label>
          <span>{prop.owner.name}</span>
        </div>
        <div className="card-row">
          <label>Última ação</label>
          <span>{prop.owner.action}</span>
        </div>
      </div>
    </div>
  );
}