import { useState, useEffect } from 'react';
import { ReactFlow, Background, Controls, MiniMap, Panel, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useDependencyGraph } from '../../hooks/useDependencyGraph';
import { useRiskReport } from '../../hooks/useRiskReport';
import { useUiStore } from '../../store/uiStore';
import { Loader2, AlertCircle, Info, ExternalLink } from 'lucide-react';
import type { GraphNode } from '../../types/graph';

interface DependencyGraphViewProps {
  sbomId: string;
  height?: number;
  onSelectNode?: (node: GraphNode | null) => void;
}

export default function DependencyGraphView({ sbomId, height = 600, onSelectNode }: DependencyGraphViewProps) {
  const { data: graphData, isLoading, error } = useDependencyGraph(sbomId);
  const { data: report } = useRiskReport(sbomId);
  const { currentApplicationName } = useUiStore();

  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

  // Category styling based on risk-colored rectangular cards
  const getRiskStyle = (risk: string) => {
    switch (risk) {
      case 'CRITICAL':
        return {
          background: '#FEF2F2',
          borderColor: '#DC2626',
          borderWidth: '2.5px',
          color: '#991B1B',
          fontWeight: 'bold' as const,
        };
      case 'HIGH':
        return {
          background: '#FFF7ED',
          borderColor: '#EA580C',
          borderWidth: '2.5px',
          color: '#C2410C',
          fontWeight: 'bold' as const,
        };
      case 'MEDIUM':
        return {
          background: '#FEFCE8',
          borderColor: '#CA8A04',
          borderWidth: '2.5px',
          color: '#854D0E',
          fontWeight: 'bold' as const,
        };
      case 'LOW':
        return {
          background: '#F0FDF4',
          borderColor: '#16A34A',
          borderWidth: '2.5px',
          color: '#166534',
          fontWeight: 'bold' as const,
        };
      default:
        return {
          background: '#F9FAFB',
          borderColor: '#9CA3AF',
          borderWidth: '2px',
          color: '#374151',
        };
    }
  };

  // Helper to resolve detailed package properties from the risk report hook
  const getFullNodeDetails = (name: string, version: string) => {
    if (!report || !report.dependencies) return null;
    return report.dependencies.find(d => d.name === name && d.version === version) || null;
  };

  useEffect(() => {
    if (!graphData) return;

    const directNodes = graphData.nodes.filter(n => n.is_direct);
    const transitiveNodes = graphData.nodes.filter(n => !n.is_direct);

    const mappedNodes: any[] = [];
    const mappedEdges: any[] = [];

    // Adjacency List for children mapping
    const adj: { [id: string]: string[] } = {};
    adj['root-app'] = directNodes.map(n => n.id);
    graphData.edges.forEach(e => {
      if (!adj[e.from]) adj[e.from] = [];
      adj[e.from].push(e.to);
    });

    // Parent mapping for ancestor path tracing
    const parentMap: { [childId: string]: string } = {};
    directNodes.forEach(n => { parentMap[n.id] = 'root-app'; });
    graphData.edges.forEach(e => {
      parentMap[e.to] = e.from;
    });

    // --- Deterministic Force-Directed Radial Simulation ---
    const positions: { [nodeId: string]: { x: number; y: number } } = {};
    const velocities: { [nodeId: string]: { x: number; y: number } } = {};

    const cx = 600;
    const cy = 400;

    // Pin the root node to the canvas center
    positions['root-app'] = { x: cx, y: cy };
    velocities['root-app'] = { x: 0, y: 0 };

    // Deterministic radial layout: arrange direct dependencies in a circle
    directNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(1, directNodes.length)) * 2 * Math.PI;
      const radius = 220; // Direct links length
      positions[node.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle)
      };
      velocities[node.id] = { x: 0, y: 0 };
    });

    // Deterministic placement for transitive dependencies fanned around parent
    transitiveNodes.forEach((node) => {
      const parentId = parentMap[node.id] || 'root-app';
      const parentPos = positions[parentId] || { x: cx, y: cy };
      
      const siblings = adj[parentId] || [];
      const siblingIdx = siblings.indexOf(node.id);
      
      const angle = (siblingIdx / Math.max(1, siblings.length)) * 2 * Math.PI;
      const radius = 150; // Transitive link spacing
      positions[node.id] = {
        x: parentPos.x + radius * Math.cos(angle),
        y: parentPos.y + radius * Math.sin(angle)
      };
      velocities[node.id] = { x: 0, y: 0 };
    });

    const nodeIds = graphData.nodes.map(n => n.id).concat(['root-app']);
    const numTicks = 240;

    // Simulation Coefficients
    const linkLength = 160;
    const kLink = 0.055;
    const kRepel = 240000;
    const kGravity = 0.004;
    const minNodeSepX = 220; // Width collision check
    const minNodeSepY = 85;  // Height collision check

    for (let tick = 0; tick < numTicks; tick++) {
      const forces: { [id: string]: { x: number; y: number } } = {};
      nodeIds.forEach(id => { forces[id] = { x: 0, y: 0 }; });

      // 1. Repulsion forces & Bounding Box overlap collision avoidance
      for (let i = 0; i < nodeIds.length; i++) {
        const idA = nodeIds[i];
        const posA = positions[idA];
        for (let j = i + 1; j < nodeIds.length; j++) {
          const idB = nodeIds[j];
          const posB = positions[idB];

          const dx = posA.x - posB.x;
          const dy = posA.y - posB.y;
          const distSq = dx * dx + dy * dy + 0.1;
          const dist = Math.sqrt(distSq);

          // Coulomb repulsion
          const forceMag = kRepel / distSq;
          const fx = (dx / dist) * forceMag;
          const fy = (dy / dist) * forceMag;

          forces[idA].x += fx;
          forces[idA].y += fy;
          forces[idB].x -= fx;
          forces[idB].y -= fy;

          // Box collision push
          const absDx = Math.abs(dx);
          const absDy = Math.abs(dy);
          if (absDx < minNodeSepX && absDy < minNodeSepY) {
            const overlapX = minNodeSepX - absDx;
            const overlapY = minNodeSepY - absDy;
            if (overlapX < overlapY) {
              const pushX = overlapX * 0.18 * (dx > 0 ? 1 : -1);
              forces[idA].x += pushX;
              forces[idB].x -= pushX;
            } else {
              const pushY = overlapY * 0.18 * (dy > 0 ? 1 : -1);
              forces[idA].y += pushY;
              forces[idB].y -= pushY;
            }
          }
        }
      }

      // 2. Link Attraction forces pulling linked nodes together
      // Root Link attractions
      directNodes.forEach(node => {
        const posA = positions['root-app'];
        const posB = positions[node.id];
        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const diff = dist - 220; // direct dependency length
        const fx = (dx / dist) * diff * kLink;
        const fy = (dy / dist) * diff * kLink;

        forces['root-app'].x += fx;
        forces['root-app'].y += fy;
        forces[node.id].x -= fx;
        forces[node.id].y -= fy;
      });

      // Child Links attractions
      graphData.edges.forEach(edge => {
        const posA = positions[edge.from];
        const posB = positions[edge.to];
        if (!posA || !posB) return;

        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.1;
        const diff = dist - linkLength;
        const fx = (dx / dist) * diff * kLink;
        const fy = (dy / dist) * diff * kLink;

        forces[edge.from].x += fx;
        forces[edge.from].y += fy;
        forces[edge.to].x -= fx;
        forces[edge.to].y -= fy;
      });

      // 3. Gravity pulling nodes toward the canvas center
      nodeIds.forEach(id => {
        if (id === 'root-app') return; // Pin center root node
        const pos = positions[id];
        forces[id].x -= (pos.x - cx) * kGravity;
        forces[id].y -= (pos.y - cy) * kGravity;
      });

      // 4. Update coordinates & apply damping
      const damping = 0.82;
      nodeIds.forEach(id => {
        if (id === 'root-app') return; // Pin center root node
        const v = velocities[id];
        const f = forces[id];

        v.x = (v.x + f.x) * damping;
        v.y = (v.y + f.y) * damping;

        // Cap maximum velocity to prevent graph explosions
        const maxV = 28;
        const speed = Math.sqrt(v.x * v.x + v.y * v.y);
        if (speed > maxV) {
          v.x = (v.x / speed) * maxV;
          v.y = (v.y / speed) * maxV;
        }

        positions[id].x += v.x;
        positions[id].y += v.y;
      });
    }

    // Adjust position formats to match center coordinate bounds
    const finalPositions: { [nodeId: string]: { x: number; y: number } } = {};
    nodeIds.forEach(id => {
      finalPositions[id] = {
        x: positions[id].x - 90,
        y: positions[id].y - 27.5
      };
    });

    // Compute interactive highlighting path
    const activeId = selectedNodeId || hoveredNodeId;
    const highlightedNodes = new Set<string>();
    const highlightedEdges = new Set<string>();

    if (activeId) {
      highlightedNodes.add(activeId);

      // Trace ancestors up to root
      let curr = activeId;
      while (curr && curr !== 'root-app') {
        const parent = parentMap[curr];
        if (parent) {
          highlightedNodes.add(parent);
          highlightedEdges.add(`edge-root-${curr}`);
          graphData.edges.forEach((e, idx) => {
            if (e.from === parent && e.to === curr) {
              highlightedEdges.add(`edge-${idx}`);
            }
          });
          curr = parent;
        } else {
          break;
        }
      }

      // Trace descendants down (DFS)
      const traverseDescendants = (nodeId: string) => {
        const children = adj[nodeId] || [];
        children.forEach(childId => {
          if (!highlightedNodes.has(childId)) {
            highlightedNodes.add(childId);
            graphData.edges.forEach((e, idx) => {
              if (e.from === nodeId && e.to === childId) {
                highlightedEdges.add(`edge-${idx}`);
              }
            });
            traverseDescendants(childId);
          }
        });
      };
      traverseDescendants(activeId);
    }

    // 1. Central Root Node
    const appName = currentApplicationName || 'Application Root';
    const isRootActive = !activeId || highlightedNodes.has('root-app');
    mappedNodes.push({
      id: 'root-app',
      position: finalPositions['root-app'],
      data: {
        label: (
          <div className="flex flex-col text-[11px] items-center justify-center h-full">
            <div className="font-extrabold uppercase tracking-wider text-white">Application Root</div>
            <div className="font-bold text-[10px] text-gray-300 truncate max-w-[160px] mt-0.5">{appName}</div>
          </div>
        ),
      },
      style: {
        background: '#0F172A',
        borderColor: '#FF1338',
        borderWidth: '2.5px',
        color: '#FFFFFF',
        width: '180px',
        height: '55px',
        borderRadius: '6px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
        opacity: isRootActive ? 1 : 0.22,
        transition: 'opacity 250ms ease',
      },
    });

    // 2. Direct and Transitive Dependency Cards
    graphData.nodes.forEach((node) => {
      const isNodeActive = !activeId || highlightedNodes.has(node.id);
      const isSelected = selectedNodeId === node.id;
      const baseStyle = getRiskStyle(node.risk_level);

      mappedNodes.push({
        id: node.id,
        position: finalPositions[node.id] || { x: 0, y: 0 },
        data: {
          label: (
            <div className="flex flex-col text-center justify-center h-full px-2">
              <div className="font-bold text-[10px] truncate leading-tight">{node.name}</div>
              <div className="text-[9px] font-mono mt-0.5 opacity-80 leading-none">{node.version}</div>
            </div>
          ),
          raw: node
        },
        style: {
          ...baseStyle,
          width: '180px',
          height: '55px',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          boxShadow: isSelected ? '0 0 0 3px #FF1338, 0 4px 6px -1px rgb(0 0 0 / 0.1)' : '0 2px 4px -1px rgb(0 0 0 / 0.06)',
          opacity: isNodeActive ? 1 : 0.22,
          transition: 'opacity 250ms ease, box-shadow 250ms ease',
        },
      });
    });

    // 3. Root links: Application Root -> Direct Dependency
    directNodes.forEach(node => {
      const isEdgeActive = !activeId || highlightedEdges.has(`edge-root-${node.id}`);
      mappedEdges.push({
        id: `edge-root-${node.id}`,
        source: 'root-app',
        target: node.id,
        style: {
          stroke: '#1E293B',
          strokeWidth: isEdgeActive ? 3.5 : 1.5,
          opacity: isEdgeActive ? 0.95 : 0.08,
          transition: 'opacity 250ms ease, stroke-width 250ms ease',
        },
      });
    });

    // 4. Sub links: Direct -> Transitive & Transitive -> Transitive
    graphData.edges.forEach((edge, idx) => {
      const sourceNode = graphData.nodes.find(n => n.id === edge.from);
      const isSourceDirect = sourceNode ? sourceNode.is_direct : false;
      const edgeId = `edge-${idx}`;
      const isEdgeActive = !activeId || highlightedEdges.has(edgeId);

      mappedEdges.push({
        id: edgeId,
        source: edge.from,
        target: edge.to,
        style: {
          stroke: isSourceDirect ? '#475569' : '#94A3B8',
          strokeWidth: isEdgeActive ? (isSourceDirect ? 2.5 : 1.8) : 1,
          strokeDasharray: isSourceDirect ? undefined : '5,5',
          opacity: isEdgeActive ? (isSourceDirect ? 0.8 : 0.6) : 0.08,
          transition: 'opacity 250ms ease, stroke-width 250ms ease',
        },
      });
    });

    setNodes(mappedNodes);
    setEdges(mappedEdges);
  }, [graphData, currentApplicationName, selectedNodeId, hoveredNodeId]);

  const onNodeClick = (_: any, node: any) => {
    const raw = node.data?.raw;
    if (raw) {
      if (node.id === 'root-app') return;
      setSelectedNode(raw);
      setSelectedNodeId(node.id);
      if (onSelectNode) onSelectNode(raw);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center bg-white border border-gray-200 rounded-lg" style={{ height: `${height}px` }}>
        <Loader2 className="animate-spin text-sg-red" size={32} />
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="flex flex-col items-center justify-center bg-white border border-gray-200 rounded-lg text-sg-danger" style={{ height: `${height}px` }}>
        <AlertCircle size={32} className="mb-2" />
        <span className="font-bold text-sm">Failed to load dependency graph.</span>
      </div>
    );
  }

  return (
    <div className="flex flex-row bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden" style={{ height: `${height}px` }}>
      
      {/* React Flow Canvas */}
      <div className="flex-1 relative bg-gray-50/30">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onNodeMouseEnter={(_, node) => setHoveredNodeId(node.id)}
          onNodeMouseLeave={() => setHoveredNodeId(null)}
          fitView
          minZoom={0.05}
          maxZoom={1.5}
        >
          <Background color="#CBD5E1" gap={16} />
          <Controls className="bg-white border border-gray-200 rounded shadow-sm text-sg-navy" />
          <MiniMap nodeStrokeWidth={3} zoomable pannable className="border border-gray-200 rounded shadow-sm" />
          
          {/* Pinned Legend Matching Node Rectangles */}
          <Panel position="bottom-left" className="bg-white/95 border border-gray-200 rounded-lg p-4 shadow-md text-[10px] space-y-3 backdrop-blur-sm pointer-events-auto w-48 m-4">
            <div className="font-extrabold text-sg-navy uppercase border-b border-gray-100 pb-1.5 tracking-wider">
              Graph Legend
            </div>
            
            {/* Rectangular Node Colors */}
            <div className="space-y-2">
              <div className="font-bold text-gray-400 uppercase tracking-widest text-[8px]">Node Severities</div>
              
              <div className="flex items-center gap-2">
                <div className="h-3 w-5 rounded border border-red-600 bg-red-50" />
                <span className="font-semibold text-gray-600">Critical Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-5 rounded border border-orange-600 bg-orange-50" />
                <span className="font-semibold text-gray-600">High Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-5 rounded border border-yellow-600 bg-yellow-50" />
                <span className="font-semibold text-gray-600">Medium Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-5 rounded border border-green-600 bg-green-50" />
                <span className="font-semibold text-gray-600">Low Risk</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-3 w-5 rounded border border-gray-400 bg-gray-50" />
                <span className="font-semibold text-gray-600">No Known Issues</span>
              </div>
            </div>

            {/* Edge Layout Style */}
            <div className="space-y-1.5 pt-1.5 border-t border-gray-100">
              <div className="font-bold text-gray-400 uppercase tracking-widest text-[8px]">Connections</div>
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-6 bg-[#1E293B]" />
                <span className="font-semibold text-gray-600">Root Link</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-6 bg-[#475569]" />
                <span className="font-semibold text-gray-600">Direct Link</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="h-0.5 w-6 border-t-2 border-dashed border-[#94A3B8]" />
                <span className="font-semibold text-gray-600">Transitive Link</span>
              </div>
            </div>
          </Panel>

          {/* Floating Instruction Box */}
          <Panel position="top-left" className="bg-white/95 border border-gray-200 rounded p-2.5 shadow-sm text-[10px] text-gray-500 font-semibold flex items-center gap-1.5 backdrop-blur-sm pointer-events-none m-4">
            <Info size={12} className="text-sg-red" />
            <span>Hover to Trace Path • Click Node to Inspect findings</span>
          </Panel>

        </ReactFlow>
      </div>

      {/* Details Side Panel Drawer */}
      {selectedNode && (
        <div className="w-85 border-l border-gray-200 bg-white p-6 overflow-y-auto flex flex-col justify-between shrink-0 shadow-lg">
          <div className="space-y-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xs font-extrabold text-sg-navy uppercase tracking-tight break-all">
                  {selectedNode.name}
                </h3>
                <div className="text-[10px] text-gray-400 font-mono mt-0.5">{selectedNode.version}</div>
              </div>
              <button
                onClick={() => {
                  setSelectedNode(null);
                  setSelectedNodeId(null);
                }}
                className="text-gray-400 hover:text-sg-red font-bold text-lg cursor-pointer transition-colors"
              >
                &times;
              </button>
            </div>

            {(() => {
              const details = getFullNodeDetails(selectedNode.name, selectedNode.version);
              const recs: string[] = [];
              if (details) {
                if (details.vulnerabilities.length > 0) {
                  recs.push(`Upgrade ${selectedNode.name} to patch active CVE vulnerabilities.`);
                }
                if (details.license_risk === 'HIGH' || details.license_risk === 'MEDIUM') {
                  recs.push(`Audit ${selectedNode.name} usage to resolve dual-licensing or strong copyleft compliance risks.`);
                }
                if (details.maintenance_score !== null && details.maintenance_score < 55) {
                  recs.push(`Decommission ${selectedNode.name} to avoid unmaintained software operational risks.`);
                }
              }
              const finalRec = recs.length > 0 ? recs.join(' ') : 'No remediation required. Component is secure and compliant.';

              return (
                <div className="space-y-5 text-xs text-gray-600">
                  {/* Basic Metadata */}
                  <div className="grid grid-cols-2 gap-3.5 bg-gray-50/50 p-3 rounded-md border border-gray-100">
                    <div>
                      <span className="block text-[9px] font-bold uppercase text-gray-400 tracking-wider">Ecosystem</span>
                      <span className="font-bold text-sg-navy uppercase">{selectedNode.ecosystem}</span>
                    </div>
                    <div>
                      <span className="block text-[9px] font-bold uppercase text-gray-400 tracking-wider">Scope</span>
                      <span className={`inline-block font-extrabold uppercase text-[8px] mt-0.5 rounded px-1.5 py-0.5 ${
                        selectedNode.is_direct
                          ? 'bg-red-50 text-sg-red border border-sg-red/20'
                          : 'bg-gray-100 text-gray-400 border border-gray-200'
                      }`}>
                        {selectedNode.is_direct ? 'Direct' : 'Transitive'}
                      </span>
                    </div>
                  </div>

                  {/* Vulnerability CVEs List */}
                  <div className="space-y-2">
                    <span className="block text-[9px] font-bold uppercase text-gray-400 tracking-wider">Vulnerabilities</span>
                    {details && details.vulnerabilities.length > 0 ? (
                      <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                        {details.vulnerabilities.map((v, vIdx) => (
                          <div key={vIdx} className="p-2 border border-red-100 bg-red-50/20 rounded flex flex-col gap-1">
                            <div className="flex justify-between items-center">
                              <span className="font-mono font-bold text-sg-red text-[10px]">{v.vuln_id}</span>
                              <span className={`px-1 py-0.5 rounded text-[8px] font-bold uppercase ${
                                v.severity === 'CRITICAL' || v.severity === 'HIGH'
                                  ? 'bg-red-100 text-sg-danger'
                                  : 'bg-amber-100 text-sg-warning'
                              }`}>
                                {v.severity}
                              </span>
                            </div>
                            <p className="text-[10px] text-gray-500 leading-normal line-clamp-2">{v.summary}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="inline-block rounded bg-green-50 text-sg-success border border-sg-success/20 px-2 py-0.5 font-bold">
                        Secure (0 CVEs)
                      </span>
                    )}
                  </div>

                  {/* License Info */}
                  <div className="space-y-2">
                    <span className="block text-[9px] font-bold uppercase text-gray-400 tracking-wider">License Compliance</span>
                    <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                      <span className="font-mono font-bold text-sg-navy">{selectedNode.license_id || 'Undeclared'}</span>
                      {details && (
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase ${
                          details.license_risk === 'HIGH' ? 'bg-red-100 text-sg-danger' : details.license_risk === 'MEDIUM' ? 'bg-amber-100 text-sg-warning' : 'bg-green-100 text-sg-success'
                        }`}>
                          {details.license_risk || 'NONE'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Maintenance Signals */}
                  <div className="space-y-2">
                    <span className="block text-[9px] font-bold uppercase text-gray-400 tracking-wider">Maintenance Health</span>
                    <div className="flex items-center justify-between border-b border-gray-100 pb-1.5">
                      <span className="font-bold text-sg-navy">
                        {details && details.maintenance_score !== null ? `${details.maintenance_score}/100` : '—'}
                      </span>
                      {details && (
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 text-[8px] font-bold uppercase">
                          {details.maintenance_status || 'UNKNOWN'}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Customized Security Recommendation */}
                  <div className="p-3 bg-red-50/10 border border-sg-red/10 rounded-md">
                    <span className="block text-[9px] font-bold uppercase text-sg-red tracking-wider mb-1">Priority Recommendation</span>
                    <p className="text-[10px] text-gray-600 leading-relaxed font-medium">
                      {finalRec}
                    </p>
                  </div>
                </div>
              );
            })()}
          </div>

          {selectedNode.repo_url && (
            <div className="pt-4 border-t border-gray-100 mt-6">
              <a
                href={selectedNode.repo_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex w-full items-center justify-center gap-1.5 rounded bg-sg-navy px-4 py-2 text-xs font-bold text-white hover:bg-sg-navy/90 no-underline shadow-xs"
              >
                <span>Browse Code Repository</span>
                <ExternalLink size={12} />
              </a>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
