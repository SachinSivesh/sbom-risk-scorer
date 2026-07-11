import apiClient from './api';
import type { ApplicationListItem, ApplicationDetail } from '../types/application';
import type { RiskTrendPoint } from '../types/riskReport';

export const applicationsApi = {
  create: (data: { name: string; description?: string }): Promise<ApplicationDetail> =>
    apiClient.post('/applications', data),

  list: (): Promise<ApplicationListItem[]> =>
    apiClient.get('/applications'),

  get: (id: string): Promise<ApplicationDetail> =>
    apiClient.get(`/applications/${id}`),

  trend: (id: string): Promise<RiskTrendPoint[]> =>
    apiClient.get(`/applications/${id}/trend`),
};
