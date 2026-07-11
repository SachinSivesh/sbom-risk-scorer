import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Portfolio from './routes/Portfolio';
import ApplicationDetail from './routes/ApplicationDetail';
import DependencyGraphPage from './routes/DependencyGraphPage';
import RiskReportPage from './routes/RiskReportPage';
import Settings from './routes/Settings';
import ScanHistory from './routes/ScanHistory';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import SbomUploadModal from './components/upload/SbomUploadModal';
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

function AppContent() {
  return (
    <div className="min-h-screen flex flex-col bg-sg-bg font-sans">
      {/* Top Navigation Header */}
      <Navbar />

      {/* Main Content Layout with Left Sidebar */}
      <div className="flex flex-1 flex-row">
        <Sidebar />
        
        <main className="flex-1 overflow-x-hidden min-h-[calc(100vh-4rem)]">
          <Routes>
            <Route path="/" element={<Portfolio />} />
            <Route path="/history" element={<ScanHistory />} />
            <Route path="/application/:id" element={<ApplicationDetail />} />
            <Route path="/graph/:sbomId" element={<DependencyGraphPage />} />
            <Route path="/report/:sbomId" element={<RiskReportPage />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>

      {/* Global Upload Modal */}
      <SbomUploadModal />
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
