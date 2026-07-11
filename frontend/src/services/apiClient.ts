/**
 * Typed API client for the SBOM Risk Scorer backend.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorData: ErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // ignore
    }
    throw new ApiError(
      response.status,
      errorData?.error?.code || 'UNKNOWN_ERROR',
      errorData?.error?.message || `Request failed with status ${response.status}`,
    );
  }

  return response.json();
}

// ── Applications ──────────────────────────────────────
export const applicationsApi = {
  create: (data: { name: string; description?: string }) =>
    request('/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  list: () => request<any[]>('/applications'),

  get: (id: string) => request<any>(`/applications/${id}`),

  trend: (id: string) => request<any[]>(`/applications/${id}/trend`),
};

// ── SBOMs ─────────────────────────────────────────────
export const sbomsApi = {
  upload: (applicationId: string, file: File) => {
    const formData = new FormData();
    formData.append('application_id', applicationId);
    formData.append('file', file);
    return request<{ sbom_id: string; status: string }>('/sboms', {
      method: 'POST',
      body: formData,
    });
  },

  status: (sbomId: string) =>
    request<any>(`/sboms/${sbomId}/status`),
};

// ── Reports ───────────────────────────────────────────
export const reportsApi = {
  get: (sbomId: string) => request<any>(`/reports/${sbomId}`),

  aiSummary: (sbomId: string) => request<any>(`/reports/${sbomId}/ai-summary`),
};

// ── Graph ─────────────────────────────────────────────
export const graphApi = {
  get: (sbomId: string) =>
    request<{ nodes: any[]; edges: any[] }>(`/graph/${sbomId}`),
};

export { ApiError };
