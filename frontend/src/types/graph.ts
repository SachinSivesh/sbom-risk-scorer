export interface GraphNode {
  id: string;
  label: string;
  ecosystem: string;
  is_direct: boolean;
  risk_level: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  name: string;
  version: string;
  license_id: string | null;
  vuln_count: number;
}

export interface GraphEdge {
  from: string;
  to: string;
}

export interface DependencyGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
