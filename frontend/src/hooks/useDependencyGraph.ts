import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../services/apiClient';
import type { DependencyGraph } from '../types/graph';

export function useDependencyGraph(sbomId: string) {
  return useQuery<DependencyGraph>({
    queryKey: ['dependencyGraph', sbomId],
    queryFn: () => graphApi.get(sbomId),
    enabled: !!sbomId,
  });
}
