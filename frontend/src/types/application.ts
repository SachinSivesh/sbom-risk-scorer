export interface Application {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationListItem {
  id: string;
  name: string;
  description?: string | null;
  latest_score: number | null;
  latest_category: string | null;
  last_analyzed_at: string | null;
  sbom_count: number;
  created_at: string;
}

export interface ApplicationDetail extends Application {
  sboms: SbomSummary[];
}

export interface SbomSummary {
  id: string;
  original_filename: string;
  format: string;
  status: string;
  component_count: number | null;
  created_at: string;
}
