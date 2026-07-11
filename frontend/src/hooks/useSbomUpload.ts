import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sbomsApi } from '../services/apiClient';

export function useSbomUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ applicationId, file }: { applicationId: string; file: File }) =>
      sbomsApi.upload(applicationId, file),
    onSuccess: (_, variables) => {
      // Invalidate application detail and list to show the new pending/completed SBOM
      queryClient.invalidateQueries({ queryKey: ['application', variables.applicationId] });
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
  });
}
