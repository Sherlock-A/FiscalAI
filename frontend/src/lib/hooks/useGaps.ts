import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/components/providers";
import { GapDetection, GapListResponse, GapStats } from "@/types/gap";

interface UseGapsParams {
  page?: number;
  pageSize?: number;
  statusFilter?: string;
  sortBy?: "confidence_score" | "estimated_gap_mad" | "detected_at";
  minConfidence?: number;
  gapType?: string;
}

export function useGaps(params: UseGapsParams = {}) {
  const { isReady } = useAuth();
  const { page = 1, pageSize = 50, statusFilter, sortBy = "estimated_gap_mad", minConfidence, gapType } = params;

  return useQuery<GapListResponse>({
    queryKey: ["gaps", page, pageSize, statusFilter, sortBy, minConfidence, gapType],
    queryFn: async () => {
      const searchParams = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        sort_by: sortBy,
      });
      if (statusFilter)  searchParams.set("status", statusFilter);
      if (minConfidence) searchParams.set("min_confidence", String(minConfidence));
      if (gapType)       searchParams.set("gap_type", gapType);

      return apiClient.get<GapListResponse>(`/gaps?${searchParams}`);
    },
    enabled: isReady,
    staleTime: 30_000,
  });
}

export function useGapStats() {
  const { isReady } = useAuth();

  return useQuery<GapStats>({
    queryKey: ["gap-stats"],
    queryFn: () => apiClient.get<GapStats>("/gaps/stats"),
    enabled: isReady,
    staleTime: 60_000,
  });
}

export function useUpdateGapStatus() {
  const queryClient = useQueryClient();

  return useMutation<GapDetection, Error, { gapId: string; status: string; note?: string }>({
    mutationFn: ({ gapId, status, note }) =>
      apiClient.patch<GapDetection>(`/gaps/${gapId}/status`, { status, note }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gaps"] });
      queryClient.invalidateQueries({ queryKey: ["gap-stats"] });
    },
  });
}

export function useGenerateReport() {
  return useMutation<void, Error, { gapId: string; agentNotes?: string }>({
    mutationFn: async ({ gapId, agentNotes }) => {
      const blob = await apiClient.postFile(`/gaps/${gapId}/report`, {
        agent_notes: agentNotes ?? null,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `FiscalAI_FA-${gapId.slice(0, 8).toUpperCase()}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });
}
