import { useState, useEffect, useCallback } from 'react';
import QuadraMap from './components/QuadraMap';
import PropertyCard from './components/PropertyCard';
import KPICards from './components/KPICards';
import Pipeline from './components/Pipeline';
import { Property, properties as defaultProperties } from './data/properties';
import './styles/app.css';

const STORAGE_KEY = 'dashboard-quadra-properties';

function loadProperties(): Property[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch { /* ignore */ }
  return defaultProperties;
}

function saveProperties(props: Property[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(props));
}

export default function App() {
  const [selectedLot, setSelectedLot] = useState<string | null>(null);
  const [properties, setProperties] = useState<Property[]>(loadProperties);

  // Persist on change
  useEffect(() => {
    saveProperties(properties);
  }, [properties]);

  const updateProperty = useCallback((lotId: string, updates: Partial<Property>) => {
    setProperties(prev => {
      const idx = prev.findIndex(p => p.lotId === lotId);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], ...updates };
        return next;
      }
      // Create new property for lot that didn't have one
      const newProp: Property = {
        id: String(Date.now()),
        lotId,
        code: '',
        title: updates.address || lotId,
        address: updates.address || '',
        neighborhood: 'Cid. Patriarca',
        city: 'São Paulo',
        price: updates.price || 0,
        area: updates.area || 0,
        type: updates.type || 'terreno',
        status: updates.status || 'Sem Contato',
        formaPgto: updates.formaPgto || '',
        propostaMAC: updates.propostaMAC || '',
        cash: updates.cash || 0,
        permutaFisica: updates.permutaFisica || 0,
        permutaFin: updates.permutaFin || 0,
        owner: updates.owner || { name: '', action: '' },
        ...updates,
      };
      return [...prev, newProp];
    });
  }, []);

  const deleteProperty = useCallback((lotId: string) => {
    setProperties(prev => prev.filter(p => p.lotId !== lotId));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Quadra Fiscal <span>047097</span></h1>
          <div className="subtitle">Cid. Patriarca · R. Prof. Aprígio Gonzaga / R. Maria Fagnani</div>
        </div>
      </header>

      <KPICards properties={properties} />

      <div className="map-section">
        <div className="map-title">Mapa da Quadra — Clique em um lote para detalhes</div>
        <QuadraMap selectedLot={selectedLot} onSelectLot={setSelectedLot} />
      </div>

      <div className="details-section">
        <PropertyCard
          lotId={selectedLot}
          onUpdate={updateProperty}
          onDelete={deleteProperty}
        />
        <Pipeline />
      </div>
    </div>
  );
}
