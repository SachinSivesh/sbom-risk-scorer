import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, History, Settings, ShieldAlert } from 'lucide-react';
import { useUiStore } from '../../store/uiStore';

export default function Sidebar() {
  const location = useLocation();
  const { setIsUploadOpen, selectedApplicationId } = useUiStore();

  const menuItems = [
    {
      name: 'Dashboard',
      icon: LayoutDashboard,
      path: '/',
    },
    {
      name: 'Scan History',
      icon: History,
      path: '/history',
    },
    {
      name: 'Scoring Policy',
      icon: Settings,
      path: '/settings',
    }
  ];

  return (
    <aside className="w-64 border-r border-gray-200 bg-sg-navy text-white flex flex-col min-h-[calc(100vh-4rem)] shadow-sm print:hidden shrink-0">
      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-md text-sm font-semibold transition-all ${
                isActive
                  ? 'bg-sg-red text-white shadow-sm'
                  : 'text-gray-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <item.icon size={18} />
              <span>{item.name}</span>
            </Link>
          );
        })}

        {/* Global Quick-Upload Action */}
        <button
          onClick={() => setIsUploadOpen(true)}
          disabled={!selectedApplicationId}
          className={`flex w-full items-center gap-3 px-4 py-3 rounded-md text-sm font-semibold transition-all mt-4 border border-dashed ${
            selectedApplicationId
              ? 'border-sg-red text-white hover:bg-sg-red/10 cursor-pointer'
              : 'border-gray-700 text-gray-500 cursor-not-allowed'
          }`}
          title={!selectedApplicationId ? "Select an application first to enable quick upload" : ""}
        >
          <UploadCloud size={18} />
          <span>Upload SBOM</span>
        </button>
      </nav>

      {/* Footer / Context Info */}
      <div className="p-4 border-t border-white/5 text-[10px] text-gray-400">
        <div className="flex items-center gap-2 mb-1">
          <ShieldAlert size={12} className="text-sg-red" />
          <span className="font-bold text-white uppercase tracking-wider">Classification</span>
        </div>
        <p className="font-medium text-gray-500 uppercase">INTERNAL USE ONLY</p>
        <p className="mt-1 font-mono text-[9px] text-gray-600">SG-SEC-RISK-v1.2</p>
      </div>
    </aside>
  );
}
