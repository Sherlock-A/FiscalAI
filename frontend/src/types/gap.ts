export interface GapDetection {
  id: string;
  commune_id: string;
  building_id: string | null;
  address_resolved: string;
  gap_type: "missing_declaration" | "underdeclared" | "unlicensed_business";
  confidence_score: string | null;   // Decimal serialized as string
  estimated_gap_mad: string | null;
  evidence: Record<string, unknown> | null;
  status: "new" | "under_review" | "notice_sent" | "paid" | "contested" | "dismissed";
  assigned_to: string | null;
  detected_at: string;              // ISO timestamp
  updated_at: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface GapListResponse {
  items: GapDetection[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface GapStats {
  total_gaps: number;
  total_gap_mad: number;
  total_backlog_mad: number;
  high_confidence_count: number;
  notices_sent: number;
  paid_count: number;
  paid_mad: number;
  gap_type_breakdown: Record<string, number>;
}
