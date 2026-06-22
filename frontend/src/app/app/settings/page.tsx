"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Server, Database, Shield, Globe } from "lucide-react";

interface InfoRow {
  label: string;
  value: string;
}

function InfoCard({
  title,
  icon,
  rows,
}: {
  title: string;
  icon: React.ReactNode;
  rows: InfoRow[];
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-green-400">{icon}</div>
        <h2 className="text-sm font-semibold text-white">{title}</h2>
      </div>
      <dl className="space-y-3">
        {rows.map((row) => (
          <div key={row.label} className="flex justify-between items-center">
            <dt className="text-slate-400 text-xs">{row.label}</dt>
            <dd className="text-white text-xs font-medium font-mono">{row.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export default function SettingsPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6 p-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-white">Paramètres</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Informations système — lecture seule dans cette version
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoCard
            title="Serveur API"
            icon={<Server className="w-4 h-4" />}
            rows={[
              { label: "URL", value: apiBase },
              { label: "Version", value: "v1" },
              { label: "Environnement", value: "Développement" },
            ]}
          />
          <InfoCard
            title="Base de données"
            icon={<Database className="w-4 h-4" />}
            rows={[
              { label: "Moteur", value: "PostgreSQL + PostGIS" },
              { label: "SRID", value: "EPSG:4326 (WGS 84)" },
              { label: "Extension", value: "PostGIS 3.x" },
            ]}
          />
          <InfoCard
            title="Conformité"
            icon={<Shield className="w-4 h-4" />}
            rows={[
              { label: "Cadre légal", value: "Loi 09-08 (CNDP)" },
              { label: "Mode", value: "Aide à la décision" },
              { label: "Journalisation", value: "Activée (audit_log)" },
            ]}
          />
          <InfoCard
            title="Sources de données"
            icon={<Globe className="w-4 h-4" />}
            rows={[
              { label: "Fonds cartographique", value: "OpenStreetMap (ODbL)" },
              { label: "Tuiles satellite", value: "Esri World Imagery" },
              { label: "Données fiscales", value: "Import CSV commune" },
            ]}
          />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 text-xs text-slate-500 leading-relaxed">
          <p className="font-semibold text-slate-400 mb-2">Avertissement légal</p>
          FiscalAI est un outil d'aide à la décision. Les détections produites par la plateforme
          sont des hypothèses basées sur des données publiques et des données transmises
          volontairement par la commune. Elles ne constituent en aucun cas des accusations ni
          des décisions administratives. Toute action sur la base de ces détections reste de
          la compétence exclusive des agents habilités de la commune.
        </div>
      </div>
    </DashboardLayout>
  );
}
