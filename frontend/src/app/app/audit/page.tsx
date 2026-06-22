"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { useAuditLogs } from "@/lib/hooks/useAuditLogs";
import { AuditLogItem } from "@/types/audit";
import { ChevronLeft, ChevronRight } from "lucide-react";

const PAGE_SIZE = 50;

function ActionBadge({ action }: { action: string }) {
  const cfg =
    action === "gap.status_update"    ? { label: "Statut mis à jour",  cls: "bg-blue-500/15 text-blue-400"   } :
    action === "gap.report_generated" ? { label: "Rapport généré",      cls: "bg-green-500/15 text-green-400" } :
                                        { label: action,                cls: "bg-slate-700 text-slate-400"    };
  return (
    <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${cfg.cls}`}>{cfg.label}</span>
  );
}

function PayloadDetail({ item }: { item: AuditLogItem }) {
  const p = item.payload;
  if (!p) return null;
  if (item.action === "gap.status_update") {
    return (
      <span className="text-xs text-slate-500">
        {String(p.old_status ?? "?")} <span className="text-slate-600">→</span> {String(p.new_status ?? "?")}
        {!!p.note && <span className="ml-2 italic text-slate-600">&ldquo;{String(p.note as string).slice(0, 60)}&rdquo;</span>}
      </span>
    );
  }
  const entries = Object.entries(p).slice(0, 3);
  return (
    <span className="text-xs text-slate-500">
      {entries.map(([k, v]) => `${k}: ${String(v)}`).join(" · ")}
    </span>
  );
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("fr-MA", { dateStyle: "short", timeStyle: "short" });
}

export default function AuditPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useAuditLogs({ page, pageSize: PAGE_SIZE });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <DashboardLayout>
      <div className="p-6 space-y-4">
        {/* Page header */}
        <div>
          <h1 className="text-white text-xl font-bold">Journal d'audit</h1>
          <p className="text-slate-400 text-sm mt-1">
            Historique complet des actions effectuées par les agents de la commune
          </p>
        </div>

        {/* Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-4 py-3 text-slate-400 font-medium text-xs">Date / Heure</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium text-xs">Action</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium text-xs">Ressource</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium text-xs">Agent</th>
                <th className="text-left px-4 py-3 text-slate-400 font-medium text-xs">Détails</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={5} className="text-center text-slate-500 py-12 text-sm">
                    Chargement…
                  </td>
                </tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={5} className="text-center text-red-400 py-12 text-sm">
                    Erreur de chargement du journal d'audit
                  </td>
                </tr>
              )}
              {!isLoading && !isError && data?.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-slate-500 py-12 text-sm">
                    Aucune entrée dans le journal
                  </td>
                </tr>
              )}
              {data?.items.map(item => (
                <tr key={item.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                    {formatDate(item.occurred_at)}
                  </td>
                  <td className="px-4 py-3">
                    <ActionBadge action={item.action} />
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {item.resource_type
                      ? <span>{item.resource_type}{item.resource_id ? <span className="text-slate-600"> #{String(item.resource_id).slice(0, 8)}</span> : null}</span>
                      : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-300 text-xs">
                    {item.actor_email ?? "Agent SIT"}
                  </td>
                  <td className="px-4 py-3">
                    <PayloadDetail item={item} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-slate-500 text-xs">
              {data ? `${data.total.toLocaleString("fr-MA")} entrée${data.total > 1 ? "s" : ""}` : ""}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-slate-400 text-xs">
                Page {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
