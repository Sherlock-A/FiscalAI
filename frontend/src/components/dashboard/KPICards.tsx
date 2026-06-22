"use client";

import { useGapStats } from "@/lib/hooks/useGaps";
import { TrendingUp, AlertTriangle, CheckCircle, Clock, Banknote } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  accent: string;
}

function KPICard({ title, value, subtitle, icon, accent }: KPICardProps) {
  return (
    <div className="rounded-xl border bg-slate-900 p-5 flex flex-col gap-3 border-slate-800">
      <div className="flex items-center justify-between">
        <p className="text-slate-400 text-sm font-medium">{title}</p>
        <div className={`p-2 rounded-lg ${accent}`}>{icon}</div>
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-slate-500 text-xs mt-1">{subtitle}</p>
      </div>
    </div>
  );
}

export function KPICards() {
  const { data, isLoading, isError } = useGapStats();

  if (isError) {
    return (
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <div className="col-span-2 xl:col-span-3 rounded-xl border border-red-800/50 bg-red-900/10 p-4 text-red-400 text-sm">
          Impossible de charger les statistiques. Vérifiez la connexion au serveur.
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="rounded-xl border border-slate-800 bg-slate-900 p-5 h-28 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="rounded-xl border border-slate-800 bg-slate-900 p-5 h-28 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const stats = data ?? {
    total_gaps: 0,
    total_gap_mad: 0,
    total_backlog_mad: 0,
    high_confidence_count: 0,
    notices_sent: 0,
    paid_count: 0,
    paid_mad: 0,
    gap_type_breakdown: {},
  };

  const backlogM = (stats.total_backlog_mad / 1_000_000).toFixed(1);
  const annualK  = Math.round(stats.total_gap_mad / 1000).toLocaleString("fr-MA");

  return (
    <div className="space-y-4">
      {/* Row 1 — revenue numbers */}
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <KPICard
          title="Écarts détectés"
          value={stats.total_gaps.toLocaleString("fr-MA")}
          subtitle="Propriétés non/sous-déclarées"
          icon={<AlertTriangle className="w-4 h-4 text-red-400" />}
          accent="bg-red-500/10"
        />
        <KPICard
          title="Revenus récupérables"
          value={`${annualK} K MAD`}
          subtitle="Estimation annuelle totale"
          icon={<TrendingUp className="w-4 h-4 text-orange-400" />}
          accent="bg-orange-500/10"
        />
        <KPICard
          title="Arriérés estimés"
          value={`${backlogM} M MAD`}
          subtitle="Cumul depuis première détection"
          icon={<Banknote className="w-4 h-4 text-purple-400" />}
          accent="bg-purple-500/10"
        />
      </div>

      {/* Row 2 — pipeline status */}
      <div className="grid grid-cols-2 gap-4">
        <KPICard
          title="Mises en demeure"
          value={stats.notices_sent.toLocaleString("fr-MA")}
          subtitle="Envoyées ce trimestre"
          icon={<Clock className="w-4 h-4 text-blue-400" />}
          accent="bg-blue-500/10"
        />
        <KPICard
          title="Revenus encaissés"
          value={`${Math.round(stats.paid_mad / 1000).toLocaleString("fr-MA")} K MAD`}
          subtitle={`${stats.paid_count} paiements reçus`}
          icon={<CheckCircle className="w-4 h-4 text-green-400" />}
          accent="bg-green-500/10"
        />
      </div>
    </div>
  );
}
