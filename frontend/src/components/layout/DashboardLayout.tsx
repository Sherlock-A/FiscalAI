"use client";

import { BarChart3, Map, FileText, Settings, LogOut, Building2, ClipboardList } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { useAuth } from "@/components/providers";

const NAV_ITEMS = [
  { href: "/app",          icon: BarChart3,     label: "Tableau de bord"  },
  { href: "/app/map",      icon: Map,           label: "Carte"            },
  { href: "/app/notices",  icon: FileText,      label: "Mises en demeure" },
  { href: "/app/audit",    icon: ClipboardList, label: "Journal d'audit"  },
  { href: "/app/settings", icon: Settings,      label: "Paramètres"       },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <div className="flex flex-col h-screen bg-slate-950 overflow-hidden">
      {/* Demo mode banner */}
      <div className="bg-green-600/10 border-b border-green-600/20 px-4 py-2 flex items-center justify-between flex-shrink-0">
        <span className="text-green-400 text-xs font-medium">
          Mode démo · Commune de Salé · Données synthétiques
        </span>
        <a
          href="mailto:okhalouki47@gmail.com"
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          Intéressé par la solution ? → okhalouki47@gmail.com
        </a>
      </div>

      {/* Sidebar + main */}
      <div className="flex flex-1 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-white font-bold text-sm leading-none">FiscalAI</p>
              <p className="text-slate-500 text-xs mt-0.5">Revenus Communaux</p>
            </div>
          </div>
        </div>

        {/* Commune selector (placeholder) */}
        <div className="px-4 py-3 border-b border-slate-800">
          <div className="bg-slate-800 rounded-lg px-3 py-2">
            <p className="text-slate-400 text-xs">Commune</p>
            <p className="text-white text-sm font-medium">Salé</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                pathname === href
                  ? "bg-green-600/15 text-green-400 font-medium"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom user section */}
        <div className="px-4 py-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs text-slate-300 font-medium">
              AG
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-xs font-medium truncate">Agent SIT</p>
              <p className="text-slate-500 text-xs truncate">Commune de Salé</p>
            </div>
            <button
              onClick={logout}
              title="Déconnexion"
              className="text-slate-500 hover:text-red-400 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
    </div>
  );
}
