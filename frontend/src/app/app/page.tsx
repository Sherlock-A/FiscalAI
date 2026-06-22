import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { KPICards } from "@/components/dashboard/KPICards";
import { GapTypeBreakdown } from "@/components/dashboard/GapTypeBreakdown";
import { GapMap } from "@/components/map/GapMap";
import { GapTable } from "@/components/dashboard/GapTable";

export default function HomePage() {
  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6 p-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">
            Tableau de Bord — Écarts Fiscaux
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Propriétés non déclarées détectées dans votre commune · Mise à jour mensuelle
          </p>
        </div>

        {/* KPI summary rows */}
        <KPICards />

        {/* Gap type breakdown bar chart */}
        <GapTypeBreakdown />

        {/* Map + Table side by side */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="rounded-xl border border-slate-800 overflow-hidden" style={{ height: 520 }}>
            <GapMap />
          </div>
          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <GapTable />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
