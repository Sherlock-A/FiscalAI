"use client";

import { GapDetection } from "@/types/gap";

interface XaiContributor {
  label: string;
  contribution: number;
  detail?: string;
}

// Reverse-engineer confidence factors from gap_detector.py scoring formulas.
function computeFactors(gap: GapDetection): XaiContributor[] {
  const ev = gap.evidence ?? {};
  const n = (k: string) => ev[k] != null ? Number(ev[k]) : 0;
  const b = (k: string) => Boolean(ev[k]);

  if (gap.gap_type === "underdeclared") {
    const matchScore = n("address_match_score");
    const ratio      = n("area_ratio");
    const hasUtility = b("has_utility_hookup");

    let ratioContrib = 0.15;
    let ratioDetail  = `ratio ${ratio.toFixed(2)}×`;
    if (ratio >= 2.0)      { ratioContrib = 0.45; }
    else if (ratio >= 1.6) { ratioContrib = 0.35; }
    else if (ratio >= 1.4) { ratioContrib = 0.25; }

    return [
      { label: "Adresse confirmée dans le registre", contribution: matchScore * 0.25, detail: `score ${matchScore.toFixed(2)}` },
      { label: "Écart de surface incohérent", contribution: ratioContrib, detail: ratioDetail },
      ...(hasUtility ? [{ label: "Occupation détectée (réseau ONEE)", contribution: 0.15 }] : []),
    ];
  }

  if (gap.gap_type === "unlicensed_business") {
    const hasUtility = b("has_utility_hookup");
    const area       = n("building_area_m2");
    let areaContrib = 0; let areaDetail = "";
    if (area >= 200)      { areaContrib = 0.20; areaDetail = `${area} m²`; }
    else if (area >= 80)  { areaContrib = 0.12; areaDetail = `${area} m²`; }
    else if (area >= 40)  { areaContrib = 0.05; areaDetail = `${area} m²`; }

    return [
      { label: "Activité commerciale détectée (OSM)", contribution: 0.38 },
      ...(hasUtility ? [{ label: "Occupation détectée (réseau ONEE)", contribution: 0.35 }] : []),
      ...(areaContrib > 0 ? [{ label: "Surface", contribution: areaContrib, detail: areaDetail }] : []),
    ];
  }

  // missing_declaration
  const matchScore  = n("address_match_score");
  const hasUtility  = b("has_utility_hookup");
  const area        = n("building_area_m2");
  let areaContrib = 0; let areaDetail = "";
  if (area >= 200)      { areaContrib = 0.20; areaDetail = `${area} m²`; }
  else if (area >= 80)  { areaContrib = 0.12; areaDetail = `${area} m²`; }
  else if (area >= 40)  { areaContrib = 0.05; areaDetail = `${area} m²`; }

  return [
    { label: "Adresse absente du registre fiscal", contribution: (1 - matchScore) * 0.40, detail: `score ${matchScore.toFixed(2)}` },
    ...(hasUtility ? [{ label: "Occupation détectée (réseau ONEE)", contribution: 0.35 }] : []),
    ...(areaContrib > 0 ? [{ label: "Surface", contribution: areaContrib, detail: areaDetail }] : []),
  ];
}

export function XaiScoreBreakdown({ gap }: { gap: GapDetection }) {
  const factors     = computeFactors(gap);
  const confidence  = Math.round(Number(gap.confidence_score ?? 0) * 100);

  if (factors.length === 0) return null;

  return (
    <div className="space-y-2">
      {factors.map((f, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" />
          <span className="flex-1 text-slate-300 min-w-0 truncate">
            {f.label}{f.detail ? ` (${f.detail})` : ""}
          </span>
          <span className="text-green-400 font-mono w-9 text-right flex-shrink-0">
            +{Math.round(f.contribution * 100)}%
          </span>
          <div className="w-16 h-1 bg-slate-700 rounded-full overflow-hidden flex-shrink-0">
            <div
              className="h-full bg-green-500 rounded-full"
              style={{ width: `${Math.min((f.contribution / 0.45) * 100, 100)}%` }}
            />
          </div>
        </div>
      ))}
      <div className="flex items-center justify-between pt-1 border-t border-slate-700 text-xs">
        <span className="text-slate-500">Score total</span>
        <span
          className={`font-bold tabular-nums ${
            confidence >= 70 ? "text-red-400" : confidence >= 55 ? "text-orange-400" : "text-yellow-400"
          }`}
        >
          {confidence}%
        </span>
      </div>
    </div>
  );
}
