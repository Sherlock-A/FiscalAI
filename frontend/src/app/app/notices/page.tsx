"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useGaps, useUpdateGapStatus, useGenerateReport } from "@/lib/hooks/useGaps";
import { GapDetection } from "@/types/gap";
import {
  FileText,
  CheckCircle,
  XCircle,
  RefreshCw,
  Filter,
  Download,
} from "lucide-react";
import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  new:          "bg-red-500/15 text-red-400",
  under_review: "bg-blue-500/15 text-blue-400",
  notice_sent:  "bg-orange-500/15 text-orange-400",
  paid:         "bg-green-500/15 text-green-400",
  contested:    "bg-yellow-500/15 text-yellow-400",
  dismissed:    "bg-slate-500/15 text-slate-400",
};

const STATUS_LABELS: Record<string, string> = {
  new:          "Nouveau",
  under_review: "En révision",
  notice_sent:  "Mise en demeure",
  paid:         "Payé",
  contested:    "Contesté",
  dismissed:    "Classé",
};

const GAP_TYPE_LABELS: Record<string, string> = {
  missing_declaration: "Déclaration manquante",
  underdeclared:       "Sous-déclaration",
  unlicensed_business: "Activité non enregistrée",
};

const FILTER_OPTIONS = [
  { value: "",             label: "Tous les statuts" },
  { value: "new",          label: "Nouveau" },
  { value: "under_review", label: "En révision" },
  { value: "notice_sent",  label: "Mise en demeure" },
  { value: "paid",         label: "Payé" },
  { value: "dismissed",    label: "Classé" },
];

interface Toast {
  id: number;
  message: string;
  type: "success" | "error";
}

export default function NoticesPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (message: string, type: "success" | "error") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  };

  const { data, isLoading } = useGaps({
    page,
    pageSize: 20,
    statusFilter: statusFilter || undefined,
    sortBy: "estimated_gap_mad",
  });

  const gaps = data?.items ?? [];

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Mises en demeure</h1>
            <p className="text-slate-400 mt-1 text-sm">
              Gestion des dossiers d'incohérences — validation et rapports PDF
            </p>
          </div>

          {/* Status filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-slate-800 border border-slate-700 rounded-lg text-slate-300 text-sm px-3 py-2 focus:outline-none focus:ring-1 focus:ring-green-500"
            >
              {FILTER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-16 rounded-lg bg-slate-800/50 animate-pulse" />
              ))}
            </div>
          ) : gaps.length === 0 ? (
            <div className="py-16 text-center">
              <CheckCircle className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">Aucun dossier pour ce filtre.</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-900 border-b border-slate-800">
                <tr>
                  <th className="text-left px-5 py-3 text-slate-400 font-medium">Adresse</th>
                  <th className="text-left px-5 py-3 text-slate-400 font-medium">Type</th>
                  <th className="text-right px-5 py-3 text-slate-400 font-medium">Écart MAD/an</th>
                  <th className="text-center px-5 py-3 text-slate-400 font-medium">Confiance</th>
                  <th className="text-center px-5 py-3 text-slate-400 font-medium">Statut</th>
                  <th className="text-center px-5 py-3 text-slate-400 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map((gap) => (
                  <GapRow
                    key={String(gap.id)}
                    gap={gap}
                    expanded={expandedId === String(gap.id)}
                    onToggle={() =>
                      setExpandedId((prev) => (prev === String(gap.id) ? null : String(gap.id)))
                    }
                    onToast={addToast}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              {(page - 1) * 20 + 1}–{Math.min(page * 20, data.total)} sur {data.total} dossiers
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
              >
                ‹ Préc.
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.pages}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
              >
                Suiv. ›
              </button>
            </div>
          </div>
        )}

        {/* Legal notice */}
        <p className="text-slate-600 text-xs text-center border-t border-slate-800 pt-4">
          Les rapports générés sont des outils d'aide à la décision. Toute action administrative
          est de la responsabilité exclusive de la commune et de ses agents habilités.
        </p>
      </div>

      {/* Toast notifications */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-2 z-50">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg text-sm font-medium shadow-lg transition-all ${
              toast.type === "success"
                ? "bg-green-900/90 text-green-300 border border-green-700"
                : "bg-red-900/90 text-red-300 border border-red-700"
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
}

// ── Row component ─────────────────────────────────────────────────────────────

function GapRow({
  gap,
  expanded,
  onToggle,
  onToast,
}: {
  gap: GapDetection;
  expanded: boolean;
  onToggle: () => void;
  onToast: (message: string, type: "success" | "error") => void;
}) {
  const { mutate: updateStatus, isPending: isUpdating } = useUpdateGapStatus();
  const { mutate: generateReport, isPending: isGenerating } = useGenerateReport();

  const confidence = Math.round(Number(gap.confidence_score ?? 0) * 100);
  const gapMad = Number(gap.estimated_gap_mad ?? 0);

  const handleValidate = () =>
    updateStatus(
      { gapId: String(gap.id), status: "under_review" },
      { onSuccess: () => onToast("Dossier mis en révision", "success"), onError: () => onToast("Erreur lors de la mise à jour", "error") }
    );

  const handleDismiss = () =>
    updateStatus(
      { gapId: String(gap.id), status: "dismissed" },
      { onSuccess: () => onToast("Dossier classé sans suite", "success"), onError: () => onToast("Erreur lors de la mise à jour", "error") }
    );

  const handleReport = () =>
    generateReport(
      { gapId: String(gap.id) },
      { onSuccess: () => onToast("Rapport PDF généré", "success"), onError: () => onToast("Erreur lors de la génération du rapport", "error") }
    );

  return (
    <>
      <tr
        className={clsx(
          "border-b border-slate-800/50 cursor-pointer transition-colors",
          expanded ? "bg-slate-800/30" : "hover:bg-slate-800/20"
        )}
        onClick={onToggle}
      >
        <td className="px-5 py-3 max-w-xs">
          <p className="text-white text-xs font-medium truncate">{gap.address_resolved}</p>
        </td>
        <td className="px-5 py-3">
          <span className="text-slate-400 text-xs">
            {GAP_TYPE_LABELS[gap.gap_type] ?? gap.gap_type}
          </span>
        </td>
        <td className="px-5 py-3 text-right">
          <span className="text-red-400 font-semibold text-xs">
            {gapMad.toLocaleString("fr-MA", { maximumFractionDigits: 0 })}
          </span>
        </td>
        <td className="px-5 py-3 text-center">
          <span className={clsx(
            "text-xs font-medium",
            confidence >= 70 ? "text-red-400" : confidence >= 55 ? "text-orange-400" : "text-yellow-400"
          )}>
            {confidence}%
          </span>
        </td>
        <td className="px-5 py-3 text-center">
          <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", STATUS_STYLES[gap.status])}>
            {STATUS_LABELS[gap.status] ?? gap.status}
          </span>
        </td>
        <td className="px-5 py-3" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-center gap-2">
            {gap.status === "new" && (
              <button
                onClick={handleValidate}
                disabled={isUpdating}
                title="Mettre en révision"
                className="p-1.5 rounded bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors disabled:opacity-40"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={handleReport}
              disabled={isGenerating}
              title="Générer rapport PDF"
              className="p-1.5 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 transition-colors disabled:opacity-40"
            >
              {isGenerating ? (
                <Download className="w-3.5 h-3.5 animate-pulse" />
              ) : (
                <FileText className="w-3.5 h-3.5" />
              )}
            </button>

            {gap.status !== "dismissed" && gap.status !== "paid" && (
              <button
                onClick={handleDismiss}
                disabled={isUpdating}
                title="Classer sans suite"
                className="p-1.5 rounded bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors disabled:opacity-40"
              >
                <XCircle className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </td>
      </tr>

      {expanded && (
        <tr className="border-b border-slate-800/50 bg-slate-800/10">
          <td colSpan={6} className="px-5 py-4">
            <EvidencePanel gap={gap} />
          </td>
        </tr>
      )}
    </>
  );
}

function EvidencePanel({ gap }: { gap: GapDetection }) {
  const e = gap.evidence ?? {};

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
      <div>
        <p className="text-slate-500 mb-1">Surface bâtiment (OSM)</p>
        <p className="text-white font-medium">
          {e.building_area_m2 ? `${Number(e.building_area_m2).toLocaleString()} m²` : "—"}
        </p>
      </div>
      <div>
        <p className="text-slate-500 mb-1">Connexion électrique</p>
        <p className={clsx("font-medium", e.has_utility_hookup ? "text-green-400" : "text-slate-400")}>
          {e.has_utility_hookup ? "Confirmée (ONEE)" : "Non détectée"}
        </p>
      </div>
      <div>
        <p className="text-slate-500 mb-1">Score correspondance adresse</p>
        <p className="text-white font-medium">
          {e.address_match_score != null
            ? `${Math.round(Number(e.address_match_score) * 100)}%`
            : "—"}
        </p>
      </div>
      <div>
        <p className="text-slate-500 mb-1">Type d'incohérence</p>
        <p className="text-white font-medium">
          {GAP_TYPE_LABELS[gap.gap_type] ?? gap.gap_type}
        </p>
      </div>
      {!!e.declared_m2 && (
        <div>
          <p className="text-slate-500 mb-1">Surface déclarée</p>
          <p className="text-orange-400 font-medium">{Number(e.declared_m2).toLocaleString()} m²</p>
        </div>
      )}
      {!!e.actual_m2 && (
        <div>
          <p className="text-slate-500 mb-1">Surface réelle (OSM)</p>
          <p className="text-red-400 font-medium">{Number(e.actual_m2).toLocaleString()} m²</p>
        </div>
      )}
    </div>
  );
}
