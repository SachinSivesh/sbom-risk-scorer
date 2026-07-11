import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, GitFork } from 'lucide-react';
import DependencyGraphView from '../components/graph/DependencyGraphView';

export default function DependencyGraphPage() {
  const { sbomId } = useParams<{ sbomId: string }>();
  const navigate = useNavigate();

  return (
    <div className="w-full h-screen p-6 bg-sg-bg flex flex-col justify-between">
      
      {/* Header bar */}
      <div className="flex justify-between items-center mb-4 shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3.5 py-2 text-xs font-bold text-gray-500 hover:bg-gray-50 cursor-pointer shadow-sm"
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div className="flex items-center gap-2">
            <GitFork size={18} className="text-sg-red" />
            <h1 className="text-lg font-extrabold text-sg-navy uppercase tracking-tight">
              Topology Dependency Explorer
            </h1>
          </div>
        </div>
      </div>

      {/* Main flow wrapper */}
      <div className="flex-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        {sbomId ? (
          <DependencyGraphView sbomId={sbomId} height={window.innerHeight - 120} />
        ) : (
          <div className="p-8 text-center text-sg-danger font-bold text-sm">
            No SBOM identifier was specified for exploration.
          </div>
        )}
      </div>

    </div>
  );
}
