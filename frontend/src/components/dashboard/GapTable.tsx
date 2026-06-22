"use client";

import { useState } from "react";
import { useGaps } from "@/lib/hooks/useGaps";
import { GapDetection } from "@/types/gap";
import { FileText } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  new:           "bg-red-500/15 text-red-400",
  under_review:  "bg-blue-500/15 text-blue-400",
  notice_sent:   "bg-orange-500/15 text-orange-400",
  paid:          "bg-green-500/15 text-green-400",
  contested:     "bg-yellow-500/15 text-yellow-400",
  dismissed:     "bg-slate-500/15 text-slate-400",
};

const STATUS_LABELS: Record<string, string> = {
  new:           "Nouveau",
  under_review:  "En révision",
  notice_sent:   "Mise en demeure",
  paid:          "Payé",
  contested:     "Contesté",
  dismissed:     "Classé",
};

const GAP_TYPE_LABELS: Record<string, string> = {
  missing_declaration: "Déclaration manquante",
  underdeclared:       "Sous-déclaration",
  unlicensed_business: "Commerce non enregistré",
};

const GAP_TYPE_FILTERS = [
  { value: "",                    label: "Tous" },
  { value: "missing_declaration", label: "Manquants" },
  { value: "underdeclared",       label: "Sous-déclarés" },
  { value: "unlicensed_business", label: "Commerce" },
];

export function GapTable() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<"confidence_score" | "estimated_gap_mad">("estimated_gap_mad");
  const [gapType, setGapType] = useState<string>("");

  const { data, isLoading, isError } = useGaps({ page, pageSize: 20, sortBy, gapType: gapType || undefined });

  const gaps = data?.items ?? [];

  function handleGapTypeChange(value: string) {
    setGapType(value);
    setPage(1);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Table header */}
      <div className="px-4 py-3 border-b border-slate-800 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Détections prioritaires</h2>
          <div className="flex gap-2">
            {(["estimated_gap_mad", "confidence_score"] as const).map((key) => (
              <button
                key={key}
                onClick={() => setSortBy(key)}
                className={`text-xs px-2 py-1 rounded transition-colors ${
                  sortBy === key ? "bg-green-600 text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                {key === "estimated_gap_mad" ? "Par montant" : "Par confiance"}
              </button>
            ))}
          </div>
        </div>

        {/* Gap type filter pills */}
        <div className="flex gap-1.5 flex-wrap">
          {GAP_TYPE_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => handleGapTypeChange(value)}
              className={`text-xs px-2.5 py-0.5 rounded-full border transition-colors ${
                gapType === value
                  ? "bg-green-600 border-green-600 text-white"
                  : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 space-y-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-14 rounded-lg bg-slate-800/50 animate-pulse" />
            ))}
          </div>
        ) : isError ? (
          <div className="p-8 text-center text-red-400 text-sm">
            Erreur de chargement des données. Réessayez dans un moment.
          </div>
        ) : gaps.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            Aucune anomalie détectée. Importez des données pour lancer l&apos;analyse.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-slate-900 border-b border-slate-800">
              <tr>
                <th className="text-left px-4 py-2 text-slate-400 font-medium">Adresse</th>
                <th className="text-right px-4 py-2 text-slate-400 font-medium">Écart (MAD)</th>
                <th className="text-center px-4 py-2 text-slate-400 font-medium">Confiance</th>
                <th className="text-center px-4 py-2 text-slate-400 font-medium">Statut</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody>
              {gaps.map((gap) => (
                <GapRow key={String(gap.id)} gap={gap} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <div className="px-4 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
        <span>
          {data ? `${(page - 1) * 20 + 1}–${Math.min(page * 20, data.total)} sur ${data.total}` : "—"}
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
          >
            ‹ Préc.
          </button>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!data || page >= data.pages}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
          >
            Suiv. ›
          </button>
        </div>
      </div>
    </div>
  );
}

function GapRow({ gap }: { gap: GapDetection }) {
  const confidence = Math.round(Number(gap.confidence_score ?? 0) * 100);
  const gapMad = Number(gap.estimated_gap_mad ?? 0);

  return (
    <tr className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors group">
      <td className="px-4 py-3 max-w-[200px]">
        <p className="text-white text-xs truncate">{gap.address_resolved}</p>
        <p className="text-slate-500 text-xs mt-0.5">
          {GAP_TYPE_LABELS[gap.gap_type] ?? gap.gap_type}
        </p>
      </td>
      <td className="px-4 py-3 text-right">
        <span className="text-red-400 font-semibold">
          {gapMad.toLocaleString("fr-MA", { maximumFractionDigits: 0 })}
        </span>
      </td>
      <td className="px-4 py-3 text-center">
        <div className="flex items-center justify-center gap-1">
          <div className="w-16 bg-slate-700 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full"
              style={{
                width: `${confidence}%`,
                background: confidence >= 70 ? "#ef4444" : confidence >= 55 ? "#f97316" : "#eab308",
              }}
            />
          </div>
          <span className="text-slate-400 text-xs w-8">{confidence}%</span>
        </div>
      </td>
      <td className="px-4 py-3 text-center">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[gap.status] ?? "text-slate-400"}`}>
          {STATUS_LABELS[gap.status] ?? gap.status}
        </span>
      </td>
      <td className="px-4 py-3 text-right">
        <button className="opacity-0 group-hover:opacity-100 transition-opacity text-green-400 hover:text-green-300">
          <FileText className="w-4 h-4" />
        </button>
      </td>
    </tr>
  );
}
