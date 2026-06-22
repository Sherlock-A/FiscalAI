"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { GapMap } from "@/components/map/GapMap";

export default function MapPage() {
  return (
    <DashboardLayout>
      <div className="flex flex-col h-full">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Carte des anomalies</h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Visualisation géospatiale des incohérences fiscales détectées
            </p>
          </div>
          <p className="text-slate-600 text-xs max-w-sm text-right">
            Outil d'aide à la décision — toute action reste de la responsabilité de la commune
          </p>
        </div>
        <div className="flex-1 min-h-0">
          <GapMap />
        </div>
      </div>
    </DashboardLayout>
  );
}
