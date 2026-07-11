export interface RiskReport {
  id: string;
  sbom_id: string;
  application_id: string;
  overall_score: number;
  category: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  vulnerability_subscore: number;
  license_subscore: number;
  maintenance_subscore: number;
  breakdown: RiskBreakdown | null;
  created_at: string;
  dependencies: DependencyWithFindings[];
}

export interface RiskBreakdown {
  weights_used: Record<string, number>;
  top_contributing_dependencies: TopContributor[];
  confidence: number;
  total_dependencies?: number;
  dependencies_with_complete_data?: number;
  note?: string;
}

export interface TopContributor {
  name: string;
  version: string;
  is_direct: boolean;
  vuln_score: number;
  license_score: number;
  maintenance_score: number | null;
  weighted_contribution: number;
}

export interface DependencyWithFindings {
  id: string;
  name: string;
  version: string;
  ecosystem: string;
  is_direct: boolean;
  license_id: string | null;
  license_risk: string | null;
  repo_url: string | null;
  vulnerabilities: VulnerabilityItem[];
  maintenance_score: number | null;
  maintenance_status: string | null;
}

export interface VulnerabilityItem {
  vuln_id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN';
  summary: string;
  fixed_version: string | null;
  source: string;
}

export interface RiskTrendPoint {
  sbom_id: string;
  overall_score: number;
  category: string;
  created_at: string;
}

export interface AIReport {
  id: string;
  risk_report_id: string;
  summary: string;
  top_actions: AIAction[];
  model_used: string;
  fallback_used: boolean;
  created_at: string;
}

export interface AIAction {
  title: string;
  description: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface SbomStatus {
  sbom_id: string;
  status: string;
  progress_step: string | null;
  error_detail: string | null;
  component_count: number | null;
  warnings: string[] | null;
  created_at: string;
}
