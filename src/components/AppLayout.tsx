import { LayoutDashboard, Map, Building, Users } from 'lucide-react';

type Tab = 'dashboard' | 'quadra' | 'imoveis' | 'leads';

interface Props {
  children: React.ReactNode;
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

const sidebarItems: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'quadra', label: 'Quadra', icon: Map },
  { id: 'imoveis', label: 'Imóveis', icon: Building },
  { id: 'leads', label: 'Leads', icon: Users },
];

export default function AppLayout({ children, activeTab, onTabChange }: Props) {
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 flex flex-col text-white shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-amber-500 flex items-center justify-center font-black text-slate-900 text-sm">DC</div>
            <div>
              <p className="font-bold text-sm leading-tight">Danilo Costa</p>
              <p className="text-[10px] text-slate-400">Corretor Premium</p>
            </div>
          </div>
        </div>
        {/* Nav */}
        <nav className="flex-1 p-3">
          <p className="text-[10px] uppercase font-semibold text-slate-500 tracking-widest px-3 mb-2">Menu</p>
          {sidebarItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all
                  ${isActive ? 'bg-amber-500 text-slate-900 shadow-lg shadow-amber-500/20' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </button>
            );
          })}
        </nav>
        {/* Footer */}
        <div className="p-4 border-t border-slate-800 text-[10px] text-slate-500">
          Quadra Fiscal Dashboard v2.0
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
