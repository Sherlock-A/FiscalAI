import { GapDetection } from "@/types/gap";

export function FinancialSection({ gap }: { gap: GapDetection }) {
  const ev       = gap.evidence ?? {};
  const n        = (k: string) => ev[k] != null ? Number(ev[k]) : null;
  const annual   = Number(gap.estimated_gap_mad ?? 0);
  const backlog  = n("estimated_backlog_mad");
  const years    = n("backlog_years");

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-slate-800 rounded-lg p-3">
          <p className="text-slate-500 text-xs mb-1">Écart annuel</p>
          <p className="text-red-400 font-bold text-base leading-none">
            {annual.toLocaleString("fr-MA", { maximumFractionDigits: 0 })}
          </p>
          <p className="text-slate-500 text-xs mt-1">MAD/an</p>
        </div>
        <div className="bg-slate-800 rounded-lg p-3">
          <p className="text-slate-500 text-xs mb-1">Arriérés cumulés</p>
          <p className="text-purple-400 font-bold text-base leading-none">
            {backlog != null
              ? backlog.toLocaleString("fr-MA", { maximumFractionDigits: 0 })
              : "—"}
          </p>
          <p className="text-slate-500 text-xs mt-1">
            {years != null ? `MAD (${years} an${years > 1 ? "s" : ""})` : "MAD"}
          </p>
        </div>
      </div>
      <p className="text-slate-600 text-xs">
        Estimation basée sur les taux TSC en vigueur (Décret n° 2-07-1336). Les montants indiqués sont
        indicatifs et restent soumis à la décision de la commune.
      </p>
    </div>
  );
}
