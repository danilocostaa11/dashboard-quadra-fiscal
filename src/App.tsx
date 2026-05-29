import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import AppLayout from './components/AppLayout';
import KPICards from './components/KPICards';
import PipelineWidget from './components/PipelineWidget';
import QuadraMap from './components/QuadraMap';
import PropertyCard from './components/PropertyCard';
import LeadCard from './components/LeadCard';
import { getProperties, saveProperties, defaultProperties } from './data/properties';
import { leads } from './data/leads';
import type { Property } from './data/types';

type Tab = 'dashboard' | 'quadra' | 'imoveis' | 'leads';

const situacaoOptions = ['Todas', 'Fechado', 'Em negociação', 'Em contato', 'Não vende'];
const estagioOptions = ['Todos', 'novo', 'contato', 'visita', 'proposta', 'fechado'];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [properties, _setProperties] = useState<Property[]>(() => {
    try { return getProperties(); } catch { return defaultProperties; }
  });
  const [searchImoveis, setSearchImoveis] = useState('');
  const [filtroSituacao, setFiltroSituacao] = useState('Todas');
  const [searchLeads, setSearchLeads] = useState('');
  const [filtroEstagio, setFiltroEstagio] = useState('Todos');

  useEffect(() => {
    saveProperties(properties);
  }, [properties]);

  const filteredProperties = properties.filter(p => {
    const matchSearch = searchImoveis === '' ||
      p.endereco.toLowerCase().includes(searchImoveis.toLowerCase()) ||
      p.proprietario.toLowerCase().includes(searchImoveis.toLowerCase()) ||
      p.codigo.includes(searchImoveis);
    const matchSituacao = filtroSituacao === 'Todas' || p.situacao === filtroSituacao;
    return matchSearch && matchSituacao;
  });

  const filteredLeads = leads.filter(l => {
    const matchSearch = searchLeads === '' ||
      l.nome.toLowerCase().includes(searchLeads.toLowerCase()) ||
      l.interesse.toLowerCase().includes(searchLeads.toLowerCase()) ||
      l.email.toLowerCase().includes(searchLeads.toLowerCase());
    const matchEstagio = filtroEstagio === 'Todos' || l.estagio === filtroEstagio;
    return matchSearch && matchEstagio;
  });

  return (
    <AppLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {/* Dashboard */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <div>
            <h1 className="text-2xl font-black text-gray-800">Dashboard</h1>
            <p className="text-sm text-gray-500">Visão geral da quadra fiscal e prospecções</p>
          </div>
          <KPICards properties={properties} />
          <PipelineWidget />
        </div>
      )}

      {/* Quadra */}
      {activeTab === 'quadra' && (
        <div className="space-y-4">
          <div>
            <h1 className="text-2xl font-black text-gray-800">Mapa da Quadra</h1>
            <p className="text-sm text-gray-500">Clique em um lote para ver detalhes</p>
          </div>
          <QuadraMap />
        </div>
      )}

      {/* Imóveis */}
      {activeTab === 'imoveis' && (
        <div className="space-y-4">
          <div>
            <h1 className="text-2xl font-black text-gray-800">Imóveis</h1>
            <p className="text-sm text-gray-500">{filteredProperties.length} de {properties.length} imóveis</p>
          </div>
          {/* Filtros */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por endereço, proprietário ou código..."
                value={searchImoveis}
                onChange={e => setSearchImoveis(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {situacaoOptions.map(opt => (
                <button
                  key={opt}
                  onClick={() => setFiltroSituacao(opt)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    filtroSituacao === opt
                      ? 'bg-amber-500 text-white'
                      : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredProperties.map(p => (
              <PropertyCard key={p.id} property={p} />
            ))}
          </div>
          {filteredProperties.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg font-semibold">Nenhum imóvel encontrado</p>
              <p className="text-sm">Tente ajustar os filtros de busca</p>
            </div>
          )}
        </div>
      )}

      {/* Leads */}
      {activeTab === 'leads' && (
        <div className="space-y-4">
          <div>
            <h1 className="text-2xl font-black text-gray-800">Leads</h1>
            <p className="text-sm text-gray-500">{filteredLeads.length} de {leads.length} leads</p>
          </div>
          {/* Filtros */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nome, interesse ou email..."
                value={searchLeads}
                onChange={e => setSearchLeads(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {estagioOptions.map(opt => (
                <button
                  key={opt}
                  onClick={() => setFiltroEstagio(opt)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    filtroEstagio === opt
                      ? 'bg-amber-500 text-white'
                      : 'bg-white border border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {opt === 'Todos' ? 'Todos' : opt.charAt(0).toUpperCase() + opt.slice(1)}
                </button>
              ))}
            </div>
          </div>
          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredLeads.map(l => (
              <LeadCard key={l.id} lead={l} />
            ))}
          </div>
          {filteredLeads.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <p className="text-lg font-semibold">Nenhum lead encontrado</p>
              <p className="text-sm">Tente ajustar os filtros de busca</p>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}

export default App;
