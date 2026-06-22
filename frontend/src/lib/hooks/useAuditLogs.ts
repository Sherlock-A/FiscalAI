import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/components/providers";
import { AuditLogListResponse } from "@/types/audit";

interface UseAuditLogsParams {
  page?: number;
  pageSize?: number;
}

export function useAuditLogs(params: UseAuditLogsParams = {}) {
  const { isReady } = useAuth();
  const { page = 1, pageSize = 50 } = params;

  return useQuery<AuditLogListResponse>({
    queryKey: ["audit-logs", page, pageSize],
    queryFn: async () => {
      const sp = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      return apiClient.get<AuditLogListResponse>(`/audit?${sp}`);
    },
    enabled: isReady,
    staleTime: 30_000,
  });
}
