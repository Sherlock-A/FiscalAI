"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { FeatureCollection, Feature, Point } from "geojson";
import { useGaps } from "@/lib/hooks/useGaps";
import { GapDetection } from "@/types/gap";
import { EvidenceSlideOver } from "./EvidenceSlideOver";
import { MapViewControls } from "./MapViewControls";

const DEFAULT_CENTER: [number, number] = [-6.79, 34.05];
const DEFAULT_ZOOM = 12;

type DisplayMode = "pins" | "heatmap";
type BasemapStyle = "streets" | "satellite";

const STREETS_STYLE = "https://demotiles.maplibre.org/style.json";

const SATELLITE_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    esri: {
      type: "raster",
      tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      tileSize: 256,
      attribution: "Tiles &copy; Esri",
    },
  },
  layers: [{ id: "bg", type: "raster", source: "esri" }],
};

function confidenceToColor(score: number): string {
  if (score >= 0.70) return "#ef4444";
  if (score >= 0.55) return "#f97316";
  return "#eab308";
}

function buildGeoJSON(items: GapDetection[]): FeatureCollection {
  const features: Feature<Point>[] = items
    .filter(g => g.longitude != null && g.latitude != null)
    .map(g => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [g.longitude!, g.latitude!] },
      properties: { id: String(g.id), weight: Number(g.confidence_score ?? 0) },
    }));
  return { type: "FeatureCollection", features };
}

function renderPins(
  map: maplibregl.Map,
  items: GapDetection[],
  onSelect: (id: string) => void,
  markersRef: React.MutableRefObject<maplibregl.Marker[]>,
) {
  markersRef.current.forEach(m => m.remove());
  markersRef.current = [];
  items.forEach(gap => {
    if (!gap.longitude || !gap.latitude) return;
    const el = document.createElement("div");
    el.className = "gap-marker";
    el.style.cssText = `
      width: 14px; height: 14px; border-radius: 50%;
      background: ${confidenceToColor(Number(gap.confidence_score ?? 0))};
      border: 2px solid rgba(255,255,255,0.7);
      cursor: pointer;
      box-shadow: 0 0 6px rgba(0,0,0,0.5);
    `;
    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([gap.longitude, gap.latitude])
      .addTo(map);
    el.addEventListener("click", () => onSelect(String(gap.id)));
    markersRef.current.push(marker);
  });
}

function addHeatmapLayer(map: maplibregl.Map, items: GapDetection[]) {
  if (map.getSource("gap-heat")) {
    (map.getSource("gap-heat") as maplibregl.GeoJSONSource).setData(buildGeoJSON(items));
    return;
  }
  map.addSource("gap-heat", { type: "geojson", data: buildGeoJSON(items) });
  map.addLayer({
    id: "gap-heat-layer",
    type: "heatmap",
    source: "gap-heat",
    paint: {
      "heatmap-weight":   ["interpolate", ["linear"], ["get", "weight"], 0, 0, 1, 1],
      "heatmap-color": [
        "interpolate", ["linear"], ["heatmap-density"],
        0, "rgba(0,0,0,0)", 0.2, "#eab308", 0.6, "#f97316", 1.0, "#ef4444",
      ],
      "heatmap-radius":   ["interpolate", ["linear"], ["zoom"], 8, 20, 14, 40],
      "heatmap-opacity":  0.85,
    },
  });
}

function removeHeatmapLayer(map: maplibregl.Map) {
  if (map.getLayer("gap-heat-layer")) map.removeLayer("gap-heat-layer");
  if (map.getSource("gap-heat"))      map.removeSource("gap-heat");
}

export function GapMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef          = useRef<maplibregl.Map | null>(null);
  const markersRef      = useRef<maplibregl.Marker[]>([]);
  const displayModeRef  = useRef<DisplayMode>("pins");
  // Tracks whether the basemap effect has fired once for the current map instance.
  // Prevents setStyle() immediately after map construction, which would abort the
  // in-progress initial style fetch and throw an AbortError.
  const basemapReadyRef = useRef(false);

  const [displayMode, setDisplayMode]       = useState<DisplayMode>("pins");
  const [basemap, setBasemap]               = useState<BasemapStyle>("streets");
  const [selectedGapId, setSelectedGapId]   = useState<string | null>(null);

  const { data } = useGaps({ page: 1, pageSize: 500 });

  useEffect(() => { displayModeRef.current = displayMode; }, [displayMode]);

  const selectedGap = data?.items.find(g => String(g.id) === selectedGapId) ?? null;

  // MapLibre cancels in-flight tile/style fetches via AbortController when the map
  // is removed or setStyle is called. These are expected and harmless, but Next.js
  // dev mode surfaces them as "Unhandled Runtime Error". Suppress them globally.
  useEffect(() => {
    const handler = (e: PromiseRejectionEvent) => {
      if (e.reason?.name === "AbortError") e.preventDefault();
    };
    window.addEventListener("unhandledrejection", handler);
    return () => window.removeEventListener("unhandledrejection", handler);
  }, []);

  // Map init — runs once per mount
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: STREETS_STYLE,
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    return () => {
      // Reset basemapReadyRef so the next mount's basemap effect skips setStyle again.
      basemapReadyRef.current = false;
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      try { map.remove(); } catch (_) { /* AbortError suppressed above */ }
      mapRef.current = null;
    };
  }, []);

  // Render visualization whenever data or display mode changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data?.items) return;

    const applyVisualization = () => {
      if (!mapRef.current) return; // guard: component may have unmounted
      if (displayModeRef.current === "heatmap") {
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];
        addHeatmapLayer(map, data.items);
      } else {
        removeHeatmapLayer(map);
        renderPins(map, data.items, setSelectedGapId, markersRef);
      }
    };

    if (map.isStyleLoaded()) {
      applyVisualization();
    } else {
      map.once("style.load", applyVisualization);
      // Clean up the listener if this effect re-runs before the style loads.
      return () => { map.off("style.load", applyVisualization); };
    }
  }, [data, displayMode]);

  // Basemap switch — setStyle wipes all custom layers; re-apply after style.load
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // On initial render the map constructor already loaded STREETS_STYLE.
    // Calling setStyle here would abort that in-progress fetch → AbortError.
    if (!basemapReadyRef.current) {
      basemapReadyRef.current = true;
      return;
    }

    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    map.setStyle(basemap === "satellite" ? SATELLITE_STYLE : STREETS_STYLE);

    map.once("style.load", () => {
      if (!mapRef.current) return;
      if (displayModeRef.current === "heatmap") {
        addHeatmapLayer(map, data?.items ?? []);
      } else {
        renderPins(map, data?.items ?? [], setSelectedGapId, markersRef);
      }
    });
  // data is intentionally not in deps — we only re-run when the basemap changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [basemap]);

  return (
    <div className="relative w-full h-full">
      <div className="absolute top-3 left-3 z-10 bg-slate-900/90 rounded-lg px-3 py-2 text-xs space-y-1 border border-slate-700">
        <p className="text-slate-300 font-medium mb-1">Confiance</p>
        {([ ["#ef4444", "≥ 70%"], ["#f97316", "55–69%"], ["#eab308", "< 55%"] ] as const).map(
          ([color, label]) => (
            <div key={label} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ background: color }} />
              <span className="text-slate-400">{label}</span>
            </div>
          )
        )}
      </div>

      <div ref={mapContainerRef} className="w-full h-full" />

      <MapViewControls
        displayMode={displayMode}
        basemap={basemap}
        onDisplayModeChange={mode => {
          displayModeRef.current = mode;
          setDisplayMode(mode);
        }}
        onBasemapChange={setBasemap}
      />

      {selectedGap && (
        <EvidenceSlideOver
          gap={selectedGap}
          onClose={() => setSelectedGapId(null)}
        />
      )}
    </div>
  );
}
