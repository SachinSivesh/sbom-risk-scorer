import { useRef, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useDependencyGraph } from '../../hooks/useDependencyGraph';
import { Loader2, AlertCircle, Info } from 'lucide-react';
import type { GraphNode } from '../../types/graph';

interface DependencyGraphViewProps {
  sbomId: string;
  height?: number;
  onSelectNode?: (node: GraphNode | null) => void;
}

export default function DependencyGraphView({ sbomId, height = 500, onSelectNode }: DependencyGraphViewProps) {
  const { data: graphData, isLoading, error } = useDependencyGraph(sbomId);
  const fgRef = useRef<any>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Auto-center the graph on load
  useEffect(() => {
    if (graphData && fgRef.current) {
      setTimeout(() => {
        fgRef.current.zoomToFit(400, 50);
      }, 500);
    }
  }, [graphData]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: `${height}px` }}>
        <Loader2 className="animate-spin" size={32} style={{ color: 'var(--color-primary)' }} />
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: `${height}px`, color: 'var(--color-critical)' }}>
        <AlertCircle size={32} style={{ marginBottom: '0.5rem' }} />
        <span>Failed to load dependency graph.</span>
      </div>
    );
  }

  // Format node & edge objects for react-force-graph
  const nodes = graphData.nodes.map(n => ({
    ...n,
    // Add additional properties for force graph simulation
    val: n.is_direct ? 8 : 4, // size based on direct vs transitive
  }));

  const links = graphData.edges.map(e => ({
    source: e.from,
    target: e.to,
  }));

  const data = { nodes, links };

  // Color mapping
  const colors = {
    CRITICAL: '#ef4444',
    HIGH: '#f97316',
    MEDIUM: '#eab308',
    LOW: '#10b981',
    NONE: '#6b7280',
  };

  const handleNodeClick = (node: any) => {
    setSelectedNode(node);
    if (onSelectNode) {
      onSelectNode(node);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedNode ? '1fr 300px' : '1fr', height: `${height}px`, width: '100%', position: 'relative' }}>
      <div style={{ position: 'relative', width: '100%', height: '100%', background: '#07080c' }}>
        <ForceGraph2D
          ref={fgRef}
          graphData={data}
          width={selectedNode ? undefined : fgRef.current?.container?.clientWidth}
          height={height}
          nodeColor={(n: any) => colors[n.risk_level as keyof typeof colors] || colors.NONE}
          nodeVal="val"
          nodeRelSize={4}
          linkWidth={1.5}
          linkColor={() => 'rgba(255, 255, 255, 0.08)'}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          linkDirectionalArrowColor={() => 'rgba(255, 255, 255, 0.15)'}
          onNodeClick={handleNodeClick}
          cooldownTicks={100}
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.name;
            const fontSize = node.is_direct ? 12 / globalScale : 8 / globalScale;
            ctx.font = `${fontSize}px var(--font-sans)`;

            // Draw shadow/glow for direct dependencies
            if (node.is_direct) {
              ctx.shadowColor = colors[node.risk_level as keyof typeof colors] || colors.NONE;
              ctx.shadowBlur = 10;
            }

            // Draw node circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.is_direct ? 6 : 4, 0, 2 * Math.PI, false);
            ctx.fillStyle = colors[node.risk_level as keyof typeof colors] || colors.NONE;
            ctx.fill();

            // Reset shadow
            ctx.shadowBlur = 0;

            // Render node labels only when zoomed in
            if (globalScale > 0.8) {
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = 'rgba(255,255,255,0.7)';
              ctx.fillText(label, node.x, node.y + (node.is_direct ? 12 : 9));
            }
          }}
        />

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: '1rem',
          left: '1rem',
          background: 'rgba(11, 12, 16, 0.9)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem',
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
          zIndex: 10
        }}>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>Risk Colors</div>
          {Object.entries(colors).map(([level, color]) => (
            <div key={level} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: color }} />
              <span style={{ textTransform: 'uppercase' }}>{level}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Details drawer/panel */}
      {selectedNode && (
        <div style={{
          background: 'rgba(22, 24, 33, 0.95)',
          borderLeft: '1px solid var(--border-color)',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          overflowY: 'auto',
          height: '100%',
          zIndex: 10
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <h3 style={{ fontSize: '1.1rem', wordBreak: 'break-all' }}>{selectedNode.name}</h3>
            <button
              className="pointer"
              onClick={() => setSelectedNode(null)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', padding: '0 0.25rem' }}
            >
              &times;
            </button>
          </div>

          <div>
            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Version</div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{selectedNode.version}</div>
          </div>

          <div>
            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Ecosystem</div>
            <span className="badge" style={{ background: 'rgba(255,255,255,0.04)', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {selectedNode.ecosystem}
            </span>
          </div>

          <div>
            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Dependency Type</div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: selectedNode.is_direct ? 'var(--color-primary)' : 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {selectedNode.is_direct ? 'Direct Dependency' : 'Transitive Dependency'}
            </div>
          </div>

          <div>
            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>License</div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, marginTop: '0.25rem' }}>
              {selectedNode.license_id || 'Undeclared'}
            </div>
          </div>

          <div>
            <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>Vulnerabilities</div>
            <div style={{ marginTop: '0.25rem' }}>
              {selectedNode.vuln_count > 0 ? (
                <span className="badge badge-critical">{selectedNode.vuln_count} vulnerabilities</span>
              ) : (
                <span className="badge badge-low">Secure</span>
              )}
            </div>
          </div>

          {/* Action to find alternatives or inspect repo */}
          <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <Info size={14} />
              <span>Scroll to zoom. Drag to pan. Click nodes to inspect.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
