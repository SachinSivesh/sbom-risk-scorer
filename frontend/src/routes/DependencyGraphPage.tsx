import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, GitFork } from 'lucide-react';
import DependencyGraphView from '../components/graph/DependencyGraphView';

export default function DependencyGraphPage() {
  const { sbomId } = useParams<{ sbomId: string }>();

  return (
    <div className="page-container" style={{ padding: '1rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link to={-1 as any} className="btn btn-secondary" style={{ padding: '0.5rem' }}>
            <ArrowLeft size={16} />
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <GitFork size={20} style={{ color: 'var(--color-primary)' }} />
            <h1 style={{ fontSize: '1.5rem', margin: 0 }}>Full-Screen Dependency Graph Explorer</h1>
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ flex: 1, padding: 0, overflow: 'hidden', background: '#07080c' }}>
        {sbomId ? (
          <DependencyGraphView sbomId={sbomId} height={window.innerHeight - 150} />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-critical)' }}>
            No SBOM ID provided.
          </div>
        )}
      </div>
    </div>
  );
}
