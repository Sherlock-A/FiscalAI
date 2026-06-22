"use client";

import { useGapStats } from "@/lib/hooks/useGaps";

const GAP_TYPE_CONFIG = [
  {
    key:    "missing_declaration",
    label:  "Déclaration manquante",
    color:  "#4ade80",  // green-400
    bg:     "bg-green-400",
  },
  {
    key:    "underdeclared",
    label:  "Sous-déclaration",
    color:  "#fb923c",  // orange-400
    bg:     "bg-orange-400",
  },
  {
    key:    "unlicensed_business",
    label:  "Commerce non enregistré",
    color:  "#c084fc",  // purple-400
    bg:     "bg-purple-400",
  },
];

export function GapTypeBreakdown() {
  const { data, isLoading } = useGapStats();

  if (isLoading || !data) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="h-4 w-40 bg-slate-800 rounded animate-pulse mb-4" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-8 bg-slate-800/50 rounded animate-pulse mb-3" />
        ))}
      </div>
    );
  }

  const breakdown = data.gap_type_breakdown ?? {};
  const total     = data.total_gaps || 1;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="text-sm font-semibold text-white mb-4">Répartition par type d&apos;anomalie</h2>
      <div className="space-y-3">
        {GAP_TYPE_CONFIG.map(({ key, label, bg }) => {
          const count = breakdown[key] ?? 0;
          const pct   = Math.round((count / total) * 100);
          return (
            <div key={key}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-400 text-xs">{label}</span>
                <span className="text-white text-xs font-medium tabular-nums">
                  {count.toLocaleString("fr-MA")} <span className="text-slate-500">({pct}%)</span>
                </span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full ${bg} rounded-full transition-all duration-500`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
