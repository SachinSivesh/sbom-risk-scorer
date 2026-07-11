import apiClient from './api';
import type { RiskReport, AIReport } from '../types/riskReport';

export const reportsApi = {
  get: (sbomId: string): Promise<RiskReport> =>
    apiClient.get(`/reports/${sbomId}`),

  aiSummary: (sbomId: string): Promise<AIReport> =>
    apiClient.get(`/reports/${sbomId}/ai-summary`),
};

export const graphApi = {
  get: (sbomId: string): Promise<{ nodes: any[]; edges: any[] }> =>
    apiClient.get(`/graph/${sbomId}`),
};
