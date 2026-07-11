import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { applicationsApi } from '../services/apiClient';
import type { ApplicationListItem, ApplicationDetail } from '../types/application';

export function useApplications() {
  return useQuery<ApplicationListItem[]>({
    queryKey: ['applications'],
    queryFn: applicationsApi.list,
  });
}

export function useApplication(id: string) {
  return useQuery<ApplicationDetail>({
    queryKey: ['application', id],
    queryFn: () => applicationsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateApplication() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      applicationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}
