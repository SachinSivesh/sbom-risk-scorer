import { HashRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ShieldCheck } from 'lucide-react';
import Portfolio from './routes/Portfolio';
import ApplicationDetail from './routes/ApplicationDetail';
import DependencyGraphPage from './routes/DependencyGraphPage';
import RiskReportPage from './routes/RiskReportPage';
import Settings from './routes/Settings';
import './App.css';

// Initialize Query Client for TanStack React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand">
        <ShieldCheck size={26} />
        <span>SBOM Risk Analyzer</span>
      </Link>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
          Portfolio
        </Link>
        <Link to="/settings" className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}>
          Scoring Policy
        </Link>
      </div>
    </nav>
  );
}

function AppContent() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar />
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Portfolio />} />
          <Route path="/application/:id" element={<ApplicationDetail />} />
          <Route path="/graph/:sbomId" element={<DependencyGraphPage />} />
          <Route path="/report/:sbomId" element={<RiskReportPage />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppContent />
      </Router>
    </QueryClientProvider>
  );
}
