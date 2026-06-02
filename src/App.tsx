import { useState } from 'react';
import QuadraMap from './components/QuadraMap';
import PropertyCard from './components/PropertyCard';
import KPICards from './components/KPICards';
import Pipeline from './components/Pipeline';
import './styles/app.css';

export default function App() {
  const [selectedLot, setSelectedLot] = useState<string | null>(null);

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Quadra Fiscal <span>047097</span></h1>
          <div className="subtitle">Cid. Patriarca · R. Prof. Aprígio Gonzaga / R. Maria Fagnani</div>
        </div>
      </header>

      <KPICards />

      <div className="map-section">
        <div className="map-title">Mapa da Quadra — Clique em um lote para detalhes</div>
        <QuadraMap selectedLot={selectedLot} onSelectLot={setSelectedLot} />
      </div>

      <div className="details-section">
        <PropertyCard lotId={selectedLot} />
        <Pipeline />
      </div>
    </div>
  );
}