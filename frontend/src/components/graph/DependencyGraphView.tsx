import { useState, useEffect } from 'react';
import { ReactFlow, Background, Controls, MiniMap, Panel, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useDependencyGraph } from '../../hooks/useDependencyGraph';
import { useRiskReport } from '../../hooks/useRiskReport';
import { useUiStore } from '../../store/uiStore';
import { Loader2, AlertCircle, Info, Search, Filter } from 'lucide-react';
import type { GraphNode } from '../../types/graph';
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

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
  
  // Interactive Filters & Layouts
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [licenseFilter] = useState<string>('ALL');
  const [scopeFilter, setScopeFilter] = useState<string>('ALL'); // ALL | DIRECT | TRANSITIVE
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());

  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [layoutLoading, setLayoutLoading] = useState(false);

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

  // Helper to resolve detailed package properties from the risk report
  const getFullNodeDetails = (name: string, version: string) => {
    if (!report || !report.dependencies) return null;
    return report.dependencies.find(d => d.name === name && d.version === version) || null;
  };

  // Run graph position calculations depending on layout selections
  useEffect(() => {
    if (!graphData) return;

    // Filter nodes based on user settings
    let visibleNodes = graphData.nodes.filter(n => {
      // Risk filtering
      if (riskFilter !== 'ALL' && n.risk_level !== riskFilter) return false;
      // Scope filtering
      if (scopeFilter === 'DIRECT' && !n.is_direct) return false;
      if (scopeFilter === 'TRANSITIVE' && n.is_direct) return false;
      // License filtering
      if (licenseFilter !== 'ALL') {
        const details = getFullNodeDetails(n.name, n.version);
        if (!details || details.license_risk !== licenseFilter) return false;
      }
      // Search matching
      if (searchQuery.trim() !== '') {
        const query = searchQuery.toLowerCase();
        if (!n.name.toLowerCase().includes(query) && !n.label.toLowerCase().includes(query)) return false;
      }
      return true;
    });

    const directNodes = visibleNodes.filter(n => n.is_direct);

    // Parent mapping for ancestor path tracing
    const parentMap: { [childId: string]: string } = {};
    directNodes.forEach(n => { parentMap[n.id] = 'root-app'; });
    
    // Map edges to only active components
    const visibleNodeIds = new Set(visibleNodes.map(n => n.id));
    visibleNodeIds.add('root-app');

    const activeEdges = graphData.edges.filter(e => 
      visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to)
    );

    activeEdges.forEach(e => {
      parentMap[e.to] = e.from;
    });

    // Collapse transitive nodes if parents are in collapsed set
    const collapsedVisibleNodes = visibleNodes.filter(n => {
      if (n.is_direct) return true;
      let curr = n.id;
      while (curr && curr !== 'root-app') {
        const parent = parentMap[curr];
        if (collapsedNodes.has(parent)) {
          return false;
        }
        curr = parent;
      }
      return true;
    });

    const finalNodeIds = new Set(collapsedVisibleNodes.map(n => n.id));
    finalNodeIds.add('root-app');

    const finalEdges = activeEdges.filter(e => 
      finalNodeIds.has(e.from) && finalNodeIds.has(e.to)
    );

    // Calculate layout coordinates
    setLayoutLoading(true);
    
    const elkNodes = collapsedVisibleNodes.map(n => ({
      id: n.id,
      width: 180,
      height: 55,
    }));

    elkNodes.push({
      id: 'root-app',
      width: 180,
      height: 55,
    });

    const elkEdges = finalEdges.map((e, idx) => ({
      id: `edge-${idx}`,
      sources: [e.from],
      targets: [e.to],
    }));

    // Add implicit edges from root to direct dependencies
    collapsedVisibleNodes.filter(n => n.is_direct).forEach((n, idx) => {
      elkEdges.push({
        id: `edge-root-implicit-${idx}`,
        sources: ['root-app'],
        targets: [n.id],
      });
    });

    const graph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered',
        'elk.direction': 'RIGHT',
        'elk.spacing.nodeNode': '60',
        'elk.layered.spacing.edgeNode': '60',
        'elk.layered.nodePlacement.strategy': 'SIMPLE',
      },
      children: elkNodes,
      edges: elkEdges,
    };

    elk.layout(graph)
      .then((layoutedGraph) => {
        const positions: { [id: string]: { x: number; y: number } } = {};
        layoutedGraph.children?.forEach((child) => {
          positions[child.id] = { x: child.x || 0, y: child.y || 0 };
        });

        renderGraphElements(collapsedVisibleNodes, finalEdges, positions, parentMap);
        setLayoutLoading(false);
      })
      .catch((err) => {
        console.error("ELK Layout failed", err);
        setLayoutLoading(false);
      });
  }, [graphData, riskFilter, licenseFilter, scopeFilter, searchQuery, collapsedNodes]);

  const renderGraphElements = (
    visibleNodes: GraphNode[], 
    edgesList: any[], 
    positions: { [id: string]: { x: number; y: number } },
    parentMap: { [childId: string]: string }
  ) => {
    const activeId = selectedNodeId || hoveredNodeId;
    const highlightedNodes = new Set<string>();
    const highlightedEdges = new Set<string>();

    if (activeId) {
      highlightedNodes.add(activeId);

      // Trace ancestors up
      let curr = activeId;
      while (curr && curr !== 'root-app') {
        const parent = parentMap[curr];
        if (parent) {
          highlightedNodes.add(parent);
          highlightedEdges.add(`edge-root-${curr}`);
          edgesList.forEach((e, idx) => {
            if (e.from === parent && e.to === curr) {
              highlightedEdges.add(`edge-${idx}`);
            }
          });
          curr = parent;
        } else {
          break;
        }
      }

      // Trace descendants down
      const adj: { [id: string]: string[] } = {};
      edgesList.forEach(e => {
        adj.setdefault = adj[e.from] || [];
        adj[e.from].push(e.to);
      });
      visibleNodes.filter(n => n.is_direct).forEach(n => {
        adj['root-app'] = adj['root-app'] || [];
        adj['root-app'].push(n.id);
      });

      const traverse = (nodeId: string) => {
        const children = adj[nodeId] || [];
        children.forEach(child => {
          if (!highlightedNodes.has(child)) {
            highlightedNodes.add(child);
            highlightedEdges.add(`edge-root-${child}`);
            edgesList.forEach((e, idx) => {
              if (e.from === nodeId && e.to === child) {
                highlightedEdges.add(`edge-${idx}`);
              }
            });
            traverse(child);
          }
        });
      };
      traverse(activeId);
    }

    // Build Nodes
    const mappedNodes: any[] = [];
    const appName = currentApplicationName || 'Application Root';
    const isRootActive = !activeId || highlightedNodes.has('root-app');

    mappedNodes.push({
      id: 'root-app',
      position: positions['root-app'] || { x: 0, y: 0 },
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

    visibleNodes.forEach((node) => {
      const isNodeActive = !activeId || highlightedNodes.has(node.id);
      const isSelected = selectedNodeId === node.id;
      const baseStyle = getRiskStyle(node.risk_level);
      const isCollapsed = collapsedNodes.has(node.id);

      mappedNodes.push({
        id: node.id,
        position: positions[node.id] || { x: 0, y: 0 },
        data: {
          label: (
            <div className="flex flex-col text-center justify-center h-full px-2 relative">
              <div className="font-bold text-[10px] truncate leading-tight">{node.name}</div>
              <div className="text-[9px] font-mono mt-0.5 opacity-80 leading-none">{node.version}</div>
              {!node.is_direct && (
                <span className="absolute bottom-0 right-0 h-1.5 w-1.5 rounded-full bg-slate-400" title="Transitive dependency" />
              )}
              {isCollapsed && (
                <span className="absolute top-0 right-0 text-[8px] bg-sg-navy text-white px-1 rounded-sm scale-75 font-extrabold">▶</span>
              )}
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

    // Build Edges
    const mappedEdges: any[] = [];
    
    // Root to direct edges
    visibleNodes.filter(n => n.is_direct).forEach(node => {
      const isEdgeActive = !activeId || highlightedEdges.has(`edge-root-${node.id}`);
      mappedEdges.push({
        id: `edge-root-${node.id}`,
        source: 'root-app',
        target: node.id,
        animated: isEdgeActive && !!activeId,
        style: {
          stroke: isEdgeActive ? '#FF1338' : '#1E293B',
          strokeWidth: isEdgeActive ? 3.5 : 1.5,
          opacity: isEdgeActive ? 0.95 : 0.08,
          transition: 'opacity 250ms ease, stroke-width 250ms ease',
        },
      });
    });

    // Internal sub-edges
    edgesList.forEach((edge, idx) => {
      const edgeId = `edge-${idx}`;
      const isEdgeActive = !activeId || highlightedEdges.has(edgeId);

      mappedEdges.push({
        id: edgeId,
        source: edge.from,
        target: edge.to,
        animated: isEdgeActive && !!activeId,
        style: {
          stroke: isEdgeActive ? '#FF1338' : '#94A3B8',
          strokeWidth: isEdgeActive ? 2.5 : 1,
          opacity: isEdgeActive ? 0.8 : 0.08,
          transition: 'opacity 250ms ease, stroke-width 250ms ease',
        },
      });
    });

    setNodes(mappedNodes);
    setEdges(mappedEdges);
  };

  const onNodeClick = (_: any, node: any) => {
    if (node.id === 'root-app') return;
    const raw = node.data?.raw;
    if (raw) {
      setSelectedNode(raw);
      setSelectedNodeId(node.id);
      if (onSelectNode) onSelectNode(raw);
    }
  };

  const toggleCollapseNode = (nodeId: string) => {
    setCollapsedNodes(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center bg-white border border-gray-200 rounded-lg gap-3" style={{ height: `${height}px` }}>
        <Loader2 className="animate-spin text-sg-red" size={32} />
        <span className="text-xs font-semibold text-gray-400">Loading graph topology...</span>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="flex flex-col items-center justify-center bg-white border border-gray-200 rounded-lg text-sg-danger" style={{ height: `${height}px` }}>
        <AlertCircle size={32} className="mb-2" />
        <span className="font-bold text-sm">Failed to load dependency graph topology.</span>
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
          
          {/* Interactive Toolbar Panel */}
          <Panel position="top-right" className="bg-white/95 border border-gray-200 rounded-lg p-3 shadow-md flex flex-wrap items-center gap-3 backdrop-blur-sm pointer-events-auto">
            {/* Search */}
            <div className="relative flex items-center">
              <Search size={14} className="absolute left-2.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search packages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-6 py-1.5 border border-gray-200 rounded text-xs focus:outline-none focus:border-sg-red w-36 font-semibold"
              />
              {layoutLoading && (
                <Loader2 className="animate-spin text-sg-red absolute right-2" size={12} />
              )}
            </div>

            {/* Severity Filter */}
            <div className="flex items-center gap-1">
              <Filter size={12} className="text-gray-400" />
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="border border-gray-200 rounded p-1 text-xs focus:outline-none font-bold"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical Risk</option>
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
                <option value="NONE">No Risk</option>
              </select>
            </div>

            {/* Scope Filter */}
            <select
              value={scopeFilter}
              onChange={(e) => setScopeFilter(e.target.value)}
              className="border border-gray-200 rounded p-1 text-xs focus:outline-none font-bold"
            >
              <option value="ALL">All Scopes</option>
              <option value="DIRECT">Direct Only</option>
              <option value="TRANSITIVE">Transitive Only</option>
            </select>
          </Panel>

          {/* Legend Panel */}
          <Panel position="bottom-left" className="bg-white/95 border border-gray-200 rounded-lg p-4 shadow-md text-[10px] space-y-3 backdrop-blur-sm pointer-events-auto w-48 m-4">
            <div className="font-extrabold text-sg-navy uppercase border-b border-gray-100 pb-1.5 tracking-wider">
              Topology Legend
            </div>
            
            <div className="space-y-2">
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
          </Panel>

          {/* Floating Instructions */}
          <Panel position="top-left" className="bg-white/95 border border-gray-200 rounded p-2.5 shadow-sm text-[10px] text-gray-500 font-semibold flex items-center gap-1.5 backdrop-blur-sm pointer-events-none m-4">
            <Info size={12} className="text-sg-red" />
            <span>Hover to Trace Lineage • Click to Inspect findings</span>
          </Panel>
        </ReactFlow>
      </div>

      {/* Details Side Drawer */}
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
              const isCollapsed = collapsedNodes.has(selectedNode.id);

              return (
                <div className="space-y-5 text-xs text-gray-600">
                  {/* Actions */}
                  <div className="flex flex-row gap-2">
                    <button
                      onClick={() => toggleCollapseNode(selectedNode.id)}
                      className="flex-1 rounded border border-gray-200 px-3 py-1.5 text-[10px] font-bold uppercase hover:bg-gray-50 text-sg-navy transition-all cursor-pointer"
                    >
                      {isCollapsed ? "Expand Transitives" : "Collapse Transitives"}
                    </button>
                  </div>

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
                          details.license_risk === 'HIGH' || details.license_risk === 'CRITICAL' 
                            ? 'bg-red-100 text-sg-danger' 
                            : details.license_risk === 'MEDIUM' 
                            ? 'bg-amber-100 text-sg-warning' 
                            : 'bg-green-100 text-sg-success'
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
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
