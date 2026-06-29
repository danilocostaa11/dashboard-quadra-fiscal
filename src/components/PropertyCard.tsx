import { useState } from 'react';
import { Property } from '../data/properties';
import { lots } from '../data/lots';

interface PropertyCardProps {
  lotId: string | null;
  onUpdate: (lotId: string, updates: Partial<Property>) => void;
  onDelete: (lotId: string) => void;
}

export default function PropertyCard({ lotId, onUpdate, onDelete }: PropertyCardProps) {
  const [editing, setEditing] = useState(false);

  if (!lotId) {
    return (
      <div className="property-card empty">
        <div className="card-icon">🗺️</div>
        <h3>Selecione um lote no mapa</h3>
        <p>Clique em um lote para ver detalhes do imóvel</p>
      </div>
    );
  }

  // Get properties from localStorage to stay in sync
  const STORAGE_KEY = 'dashboard-quadra-properties';
  let allProps: Property[] = [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) allProps = JSON.parse(raw);
  } catch { /* ignore */ }

  const prop = allProps.find(p => p.lotId === lotId);
  const lot = lots.find(l => l.id === lotId);

  if (!lot) {
    return (
      <div className="property-card empty">
        <div className="card-icon">❌</div>
        <h3>Lote não encontrado</h3>
        <p>{lotId}</p>
      </div>
    );
  }

  const formatArea = (v: number) => `${v.toLocaleString('pt-BR')} m²`;
  const streetLabel = lot.rua === 'R PROF APRIGIO GONZAGA'
    ? 'R. Prof. Aprígio Gonzaga'
    : lot.rua === 'R MARIA FAGNANI'
      ? 'R. Maria Fagnani'
      : lot.rua;

  if (editing) {
    return (
      <EditForm
        lotId={lotId}
        lot={lot}
        prop={prop}
        streetLabel={streetLabel}
        onSave={(updates) => {
          onUpdate(lotId, updates);
          setEditing(false);
        }}
        onCancel={() => setEditing(false)}
        onDelete={() => {
          if (confirm('Remover este imóvel do cadastro?')) {
            onDelete(lotId);
            setEditing(false);
          }
        }}
      />
    );
  }

  if (prop) {
    const statusColor = prop.status === 'Em Negociação' ? '#f59e0b' : prop.status === 'Sem Contato' ? '#6b7280' : '#374151';
    const formatCurrency = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);

    return (
      <div className="property-card">
        <div className="card-header" style={{ borderColor: statusColor }}>
          <div className="card-header-left">
            <span className="card-lote">{lot.lote}</span>
            <span className="card-numero">Nº {lot.numero}</span>
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

        <button className="btn-edit" onClick={() => setEditing(true)}>
          ✏️ Editar negociação
        </button>
      </div>
    );
  }

  // No property — show lot info + "Cadastrar" button
  return (
    <div className="property-card">
      <div className="card-header" style={{ borderColor: '#374151' }}>
        <div className="card-header-left">
          <span className="card-lote">{lot.lote}</span>
          <span className="card-numero">Nº {lot.numero}</span>
        </div>
        <span className="card-status" style={{ backgroundColor: '#374151' }}>Sem dados</span>
      </div>

      <div className="card-body">
        <div className="card-row">
          <label>Rua</label>
          <span>{streetLabel}</span>
        </div>
        <div className="card-row">
          <label>Área do terreno</label>
          <span>{formatArea(lot.areaTerreno)}</span>
        </div>
        <div className="card-row">
          <label>Quadra</label>
          <span>047/097</span>
        </div>
        <div className="card-row">
          <label>Bairro</label>
          <span>Cid. Patriarca</span>
        </div>

        <div className="card-divider" />

        <button className="btn-edit btn-new" onClick={() => setEditing(true)}>
          ➕ Cadastrar imóvel neste lote
        </button>
      </div>
    </div>
  );
}

/* ── Edit Form (inline) ──────────────────────────── */

interface EditFormProps {
  lotId: string;
  lot: { lote: string; numero: string; rua: string; areaTerreno: number };
  prop: Property | undefined;
  streetLabel: string;
  onSave: (updates: Partial<Property>) => void;
  onCancel: () => void;
  onDelete: () => void;
}

function EditForm({ lotId, lot, prop, streetLabel, onSave, onCancel, onDelete }: EditFormProps) {
  const fmt = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v);

  const [form, setForm] = useState({
    address: prop?.address || `${streetLabel}, ${lot.numero}`,
    code: prop?.code || '',
    area: prop?.area || lot.areaTerreno,
    type: prop?.type || 'terreno',
    status: prop?.status || 'Sem Contato',
    price: prop?.price || 0,
    propostaMAC: prop?.propostaMAC || '',
    formaPgto: prop?.formaPgto || '',
    cash: prop?.cash || 0,
    permutaFisica: prop?.permutaFisica || 0,
    ownerName: prop?.owner?.name || '',
    ownerAction: prop?.owner?.action || '',
  });

  const set = (key: string, val: any) => setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      address: form.address,
      code: form.code,
      area: Number(form.area) || 0,
      type: form.type,
      status: form.status,
      price: Number(form.price) || 0,
      propostaMAC: form.propostaMAC,
      formaPgto: form.formaPgto,
      cash: Number(form.cash) || 0,
      permutaFisica: Number(form.permutaFisica) || 0,
      owner: { name: form.ownerName, action: form.ownerAction },
    });
  };

  return (
    <div className="property-card editing">
      <div className="card-header" style={{ borderColor: '#3b82f6' }}>
        <div className="card-header-left">
          <span className="card-lote">{lot.lote}</span>
          <span className="card-numero">Nº {lot.numero}</span>
        </div>
        <span className="card-status" style={{ backgroundColor: '#3b82f6' }}>
          {prop ? '✏️ Editando' : '➕ Novo'}
        </span>
      </div>

      <form className="edit-form" onSubmit={handleSubmit}>
        {/* Situação */}
        <fieldset>
          <legend>📋 Situação</legend>
          <div className="form-row">
            <label>Status</label>
            <select value={form.status} onChange={e => set('status', e.target.value)}>
              <option value="Sem Contato">Sem Contato</option>
              <option value="Em Negociação">Em Negociação</option>
              <option value="Fechado">Fechado</option>
              <option value="Não Vende">Não Vende</option>
            </select>
          </div>
          <div className="form-row">
            <label>Última ação</label>
            <input type="text" value={form.ownerAction} onChange={e => set('ownerAction', e.target.value)}
              placeholder="Ex: Contato realizado, Proposta enviada..." />
          </div>
        </fieldset>

        {/* Imóvel */}
        <fieldset>
          <legend>🏠 Imóvel</legend>
          <div className="form-row">
            <label>Endereço</label>
            <input type="text" value={form.address} onChange={e => set('address', e.target.value)} />
          </div>
          <div className="form-row half">
            <div>
              <label>Inscrição</label>
              <input type="text" value={form.code} onChange={e => set('code', e.target.value)}
                placeholder="047.097.XXXX-X" />
            </div>
            <div>
              <label>Área (m²)</label>
              <input type="number" value={form.area} onChange={e => set('area', e.target.value)} />
            </div>
          </div>
          <div className="form-row half">
            <div>
              <label>Tipo</label>
              <select value={form.type} onChange={e => set('type', e.target.value)}>
                <option value="terreno">🏗️ Terreno</option>
                <option value="casa">🏠 Casa</option>
              </select>
            </div>
            <div>
              <label>Preço estimado</label>
              <input type="number" value={form.price} onChange={e => set('price', e.target.value)} />
            </div>
          </div>
        </fieldset>

        {/* Negociação */}
        <fieldset>
          <legend>💰 Negociação</legend>
          <div className="form-row">
            <label>Proposta MAC</label>
            <input type="text" value={form.propostaMAC} onChange={e => set('propostaMAC', e.target.value)}
              placeholder="Ex: R$ 450k Cash + 80m² residencial = R$ 1.49M" />
          </div>
          <div className="form-row">
            <label>Forma de pagamento</label>
            <input type="text" value={form.formaPgto} onChange={e => set('formaPgto', e.target.value)}
              placeholder="Ex: 50% permuta, 100% cash..." />
          </div>
          <div className="form-row half">
            <div>
              <label>Cash (R$)</label>
              <input type="number" value={form.cash} onChange={e => set('cash', e.target.value)} />
            </div>
            <div>
              <label>Permuta física (R$)</label>
              <input type="number" value={form.permutaFisica} onChange={e => set('permutaFisica', e.target.value)} />
            </div>
          </div>
        </fieldset>

        {/* Proprietário */}
        <fieldset>
          <legend>👤 Proprietário</legend>
          <div className="form-row">
            <label>Nome</label>
            <input type="text" value={form.ownerName} onChange={e => set('ownerName', e.target.value)}
              placeholder="Nome do proprietário" />
          </div>
        </fieldset>

        {/* Preview */}
        {(form.cash > 0 || form.permutaFisica > 0) && (
          <div className="edit-preview">
            <span>Total proposta:</span>
            <strong>{fmt(form.cash + form.permutaFisica)}</strong>
          </div>
        )}

        {/* Actions */}
        <div className="edit-actions">
          <button type="submit" className="btn-save">💾 Salvar</button>
          <button type="button" className="btn-cancel" onClick={onCancel}>Cancelar</button>
          {prop && (
            <button type="button" className="btn-delete" onClick={onDelete}>🗑️ Remover</button>
          )}
        </div>
      </form>
    </div>
  );
}
