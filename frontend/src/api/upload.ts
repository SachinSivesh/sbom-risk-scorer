import apiClient from './api';
import type { SbomStatus } from '../types/riskReport';

export const sbomsApi = {
  upload: (applicationId: string, file: File): Promise<{ sbom_id: string; status: string }> => {
    const formData = new FormData();
    formData.append('application_id', applicationId);
    formData.append('file', file);
    
    return apiClient.post('/sboms', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  status: (sbomId: string): Promise<SbomStatus> =>
    apiClient.get(`/sboms/${sbomId}/status`),
};
