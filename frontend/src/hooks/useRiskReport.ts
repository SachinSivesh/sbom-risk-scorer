import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../services/apiClient';
import type { RiskReport, AIReport } from '../types/riskReport';

export function useRiskReport(sbomId: string) {
  return useQuery<RiskReport>({
    queryKey: ['riskReport', sbomId],
    queryFn: () => reportsApi.get(sbomId),
    enabled: !!sbomId,
    retry: (failureCount, error: any) => {
      // Don't retry if the analysis is not complete yet (409)
      if (error?.status === 409) return false;
      return failureCount < 3;
    },
  });
}

export function useAIReport(sbomId: string) {
  return useQuery<AIReport>({
    queryKey: ['aiReport', sbomId],
    queryFn: () => reportsApi.aiSummary(sbomId),
    enabled: !!sbomId,
  });
}
