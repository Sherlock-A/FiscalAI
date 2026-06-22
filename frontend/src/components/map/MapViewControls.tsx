"use client";

type DisplayMode = "pins" | "heatmap";
type BasemapStyle = "streets" | "satellite";

interface MapViewControlsProps {
  displayMode: DisplayMode;
  basemap: BasemapStyle;
  onDisplayModeChange: (mode: DisplayMode) => void;
  onBasemapChange: (style: BasemapStyle) => void;
}

function ToggleGroup<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="bg-slate-900/95 border border-slate-700 rounded-lg p-1 flex shadow-lg">
      {options.map(opt => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`text-xs px-3 py-1.5 rounded transition-colors font-medium ${
            value === opt.value
              ? "bg-green-600 text-white"
              : "text-slate-400 hover:text-white"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export function MapViewControls({
  displayMode,
  basemap,
  onDisplayModeChange,
  onBasemapChange,
}: MapViewControlsProps) {
  return (
    <div className="absolute bottom-3 right-3 z-10 flex flex-col gap-2 items-end">
      <ToggleGroup<BasemapStyle>
        options={[
          { value: "streets",   label: "Vue" },
          { value: "satellite", label: "Satellite" },
        ]}
        value={basemap}
        onChange={onBasemapChange}
      />
      <ToggleGroup<DisplayMode>
        options={[
          { value: "pins",    label: "Épingles" },
          { value: "heatmap", label: "Chaleur" },
        ]}
        value={displayMode}
        onChange={onDisplayModeChange}
      />
    </div>
  );
}
