import { GapDetection } from "@/types/gap";

export function GeoDataSection({ gap }: { gap: GapDetection }) {
  const ev     = gap.evidence ?? {};
  const n      = (k: string) => ev[k] != null ? Number(ev[k]) : null;
  const s      = (k: string) => ev[k] != null ? String(ev[k]) : null;

  const area   = n("building_area_m2");
  const floors = n("floor_count");
  const effArea = n("effective_area_m2");
  const zone   = s("tsc_zone");
  const rate   = n("estimated_tsc_rate_mad_per_m2");

  const ZONE_LABELS: Record<string, string> = {
    downtown:    "Centre-ville (Zone A)",
    residential: "Résidentiel (Zone B)",
    peripheral:  "Périurbain (Zone C)",
  };

  return (
    <div className="space-y-2">
      <DataRow label="Surface OSM détectée" value={area != null ? `${area.toLocaleString("fr-MA")} m²` : "—"} />
      <DataRow label="Nombre d'étages"      value={floors != null ? String(floors) : "—"} />
      <DataRow label="Surface imposable"    value={effArea != null ? `${effArea.toLocaleString("fr-MA")} m²` : "—"} />
      <DataRow label="Zone fiscale"         value={zone ? (ZONE_LABELS[zone] ?? zone) : "—"} />
      <DataRow label="Taux TSC"             value={rate != null ? `${rate} MAD/m²/an` : "—"} />
      {gap.latitude != null && gap.longitude != null && (
        <DataRow
          label="Coordonnées GPS"
          value={`${gap.latitude.toFixed(5)}° N, ${Math.abs(gap.longitude).toFixed(5)}° O`}
        />
      )}
    </div>
  );
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-start gap-2 text-xs">
      <span className="text-slate-500 flex-shrink-0">{label}</span>
      <span className="text-white text-right font-medium">{value}</span>
    </div>
  );
}
