import { GapDetection } from "@/types/gap";

export function RegistreSection({ gap }: { gap: GapDetection }) {
  const ev = gap.evidence ?? {};
  const n  = (k: string) => ev[k] != null ? Number(ev[k]) : null;
  const s  = (k: string) => ev[k] != null ? String(ev[k]) : null;

  if (gap.gap_type === "underdeclared") {
    const declared = n("declared_m2");
    const actual   = n("actual_m2");
    const ratio    = n("area_ratio");
    const pct      = declared != null && actual != null && actual > 0
      ? Math.round((declared / actual) * 100)
      : 0;

    return (
      <div className="space-y-3">
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Surface déclarée</span>
          <span className="text-orange-400 font-medium">{declared != null ? `${declared} m²` : "—"}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Surface réelle (OSM)</span>
          <span className="text-red-400 font-medium">{actual != null ? `${actual} m²` : "—"}</span>
        </div>

        {/* Comparison bar */}
        {declared != null && actual != null && (
          <div className="space-y-1">
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden relative">
              <div
                className="absolute inset-y-0 left-0 bg-orange-500/60 rounded-full"
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
              <div className="absolute inset-y-0 left-0 right-0 bg-red-500/25 rounded-full" />
            </div>
            <div className="flex justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-sm bg-orange-500/60 inline-block" />
                Déclaré ({declared} m²)
              </span>
              <span className="flex items-center gap-1">
                Réel ({actual} m²)
                <span className="w-2 h-2 rounded-sm bg-red-500/40 inline-block" />
              </span>
            </div>
          </div>
        )}

        {ratio != null && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-xs">
            <span className="text-red-400 font-semibold">
              Ratio d'écart: {ratio.toFixed(2)}× — surface déclarée {Math.round((1 - 1 / ratio) * 100)}% inférieure à la réalité
            </span>
          </div>
        )}
      </div>
    );
  }

  if (gap.gap_type === "unlicensed_business") {
    const tag = s("commercial_tag");
    return (
      <div className="space-y-2">
        {tag && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500">Activité OSM détectée</span>
            <span className="bg-purple-500/15 text-purple-400 px-2 py-0.5 rounded-full font-medium">{tag}</span>
          </div>
        )}
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-xs text-red-400">
          Aucune taxe professionnelle enregistrée dans le rôle fiscal
        </div>
      </div>
    );
  }

  // missing_declaration
  const matchScore = n("address_match_score");
  return (
    <div className="space-y-2">
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-xs text-red-400">
        Bâtiment non trouvé dans le registre fiscal de la commune
      </div>
      {matchScore != null && (
        <div className="flex justify-between text-xs">
          <span className="text-slate-500">Score similarité adresse</span>
          <span className="text-slate-400">{(matchScore * 100).toFixed(0)}% (seuil: 72%)</span>
        </div>
      )}
    </div>
  );
}
