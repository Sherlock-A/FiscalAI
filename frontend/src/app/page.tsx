import Link from "next/link";
import {
  Building2, BarChart3, ArrowRight, ExternalLink,
  Database, Search, FileCheck, MapPin, Shield, Zap, Mail,
} from "lucide-react";

// TODO: Replace with your actual profile URLs
const GITHUB_URL = "https://github.com/YOUR_USERNAME";
const LINKEDIN_URL = "https://linkedin.com/in/YOUR_PROFILE";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">

      {/* ── Navbar ──────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white text-lg">FiscalAI</span>
          </div>
          <div className="flex items-center gap-4">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-400 hover:text-white text-sm transition-colors hidden sm:block"
            >
              GitHub
            </a>
            <Link
              href="/app"
              className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Voir la Démo
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 pt-16 pb-12">
        <div className="absolute inset-0 bg-gradient-to-b from-green-950/20 via-transparent to-transparent pointer-events-none" />

        <div className="relative z-10 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-green-600/10 border border-green-600/20 rounded-full px-4 py-1.5 text-xs text-green-400 font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Prototype actif · Commune de Salé
          </div>

          <h1 className="text-6xl sm:text-7xl font-bold text-white mb-4 tracking-tight">
            Fiscal<span className="text-green-500">AI</span>
          </h1>

          <p className="text-2xl sm:text-3xl text-slate-300 font-light mb-6">
            Intelligence Fiscale pour les Communes Marocaines
          </p>

          <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed mb-10">
            Les communes perdent en moyenne{" "}
            <span className="text-white font-medium">25–30% de leurs revenus TSC</span>{" "}
            par manque d'outils de détection. FiscalAI croise les données publiques —
            OpenStreetMap, connexions ONEE, registre fiscal — pour surfacer
            automatiquement les anomalies fiscales.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/app"
              className="flex items-center gap-2.5 bg-green-600 hover:bg-green-500 text-white font-semibold px-8 py-3.5 rounded-xl text-base transition-all hover:shadow-lg hover:shadow-green-900/30 w-full sm:w-auto justify-center"
            >
              Voir la Démo Live
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2.5 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-white font-medium px-8 py-3.5 rounded-xl text-base transition-colors w-full sm:w-auto justify-center"
            >
              <ExternalLink className="w-4 h-4" />
              Code source
            </a>
          </div>
        </div>
      </section>

      {/* ── Stats bar ───────────────────────────────────────────────────── */}
      <section className="border-y border-slate-800 bg-slate-900/50">
        <div className="max-w-5xl mx-auto px-6 py-10 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "488",       label: "Anomalies détectées",        color: "text-red-400"    },
            { value: "1.45M MAD", label: "Revenus récupérables / an",  color: "text-green-400"  },
            { value: "15.7M MAD", label: "Arriérés estimés",           color: "text-orange-400" },
            { value: "Salé",      label: "Commune pilote",             color: "text-blue-400"   },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className={`text-2xl font-bold ${s.color} mb-1`}>{s.value}</p>
              <p className="text-slate-500 text-sm">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Comment ça marche ───────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-center text-slate-500 text-sm font-medium uppercase tracking-wider mb-3">
            Fonctionnement
          </p>
          <h2 className="text-3xl font-bold text-white text-center mb-16">
            De la donnée publique à la décision communale
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {[
              {
                step: "01",
                icon: <Database className="w-6 h-6" />,
                title: "Données publiques",
                desc: "Croisement de OpenStreetMap (bâtiments), connexions électriques ONEE, et du registre fiscal fourni volontairement par la commune. Aucune donnée privée ou illégale.",
              },
              {
                step: "02",
                icon: <Search className="w-6 h-6" />,
                title: "Détection IA",
                desc: "Algorithme de cross-référencement avec scoring de confiance explicable (XAI). 3 types d'anomalies : déclaration manquante, sous-déclaration, activité non enregistrée.",
              },
              {
                step: "03",
                icon: <FileCheck className="w-6 h-6" />,
                title: "Workflow légal",
                desc: "Interface guidée en 5 étapes : analyse → terrain → validation agent → rapport PDF. Journal d'audit complet pour la traçabilité. Aide à la décision uniquement.",
              },
            ].map((item) => (
              <div key={item.step} className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-green-600/10 border border-green-600/20 flex items-center justify-center text-green-400">
                  {item.icon}
                </div>
                <div>
                  <p className="text-slate-600 text-xs font-mono mb-1">{item.step}</p>
                  <h3 className="text-white font-semibold text-lg mb-2">{item.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Fonctionnalités ─────────────────────────────────────────────── */}
      <section className="py-24 px-6 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <p className="text-center text-slate-500 text-sm font-medium uppercase tracking-wider mb-3">
            Fonctionnalités
          </p>
          <h2 className="text-3xl font-bold text-white text-center mb-16">
            Une plateforme complète pour les agents communaux
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: <BarChart3 className="w-8 h-8" />,
                gradient: "from-green-600/20 to-green-600/5",
                border: "border-green-700/30",
                iconColor: "text-green-400",
                title: "Tableau de bord",
                desc: "KPIs en temps réel : total anomalies, montant récupérable, arriérés estimés. Graphique de distribution par type de gap. Score XAI détaillé par détection.",
              },
              {
                icon: <MapPin className="w-8 h-8" />,
                gradient: "from-blue-600/20 to-blue-600/5",
                border: "border-blue-700/30",
                iconColor: "text-blue-400",
                title: "Carte interactive",
                desc: "MapLibre GL avec épingles colorées par confiance, vue heatmap de densité, basemap satellite Esri. Panneau d'évidence 360° avec XAI explicable.",
              },
              {
                icon: <Shield className="w-8 h-8" />,
                gradient: "from-orange-600/20 to-orange-600/5",
                border: "border-orange-700/30",
                iconColor: "text-orange-400",
                title: "Conformité & Audit",
                desc: "Outil d'aide à la décision uniquement. Journal d'audit complet, workflow en 5 étapes avec validation humaine. Conforme Loi 09-08 (CNDP Maroc).",
              },
            ].map((f) => (
              <div
                key={f.title}
                className={`rounded-2xl border ${f.border} bg-gradient-to-br ${f.gradient} p-6 flex flex-col gap-4`}
              >
                <div className={f.iconColor}>{f.icon}</div>
                <h3 className="text-white font-semibold text-lg">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stack technique ─────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-slate-500 text-sm font-medium uppercase tracking-wider mb-3">
            Stack Technique
          </p>
          <h2 className="text-3xl font-bold text-white mb-12">
            Technologies de production
          </h2>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              "FastAPI", "SQLAlchemy Async", "PostgreSQL", "PostGIS",
              "asyncpg", "Next.js 14", "React 18", "TanStack Query",
              "MapLibre GL", "Tailwind CSS", "Docker", "Terraform / AWS",
            ].map((tech) => (
              <span
                key={tech}
                className="px-4 py-2 rounded-full border border-slate-700 bg-slate-800/50 text-slate-300 text-sm font-medium hover:border-green-600/50 hover:text-white transition-colors"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA section ─────────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-600/10 border border-green-600/20 mb-6">
            <Zap className="w-7 h-7 text-green-400" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Essayez la démo en ligne
          </h2>
          <p className="text-slate-400 mb-8 text-lg">
            Explorez les 488 anomalies détectées sur la commune de Salé.
            Authentification automatique, données synthétiques.
          </p>
          <Link
            href="/app"
            className="inline-flex items-center gap-2.5 bg-green-600 hover:bg-green-500 text-white font-semibold px-10 py-4 rounded-xl text-base transition-all hover:shadow-lg hover:shadow-green-900/30"
          >
            Lancer la Démo
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800 py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <Building2 className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-white font-semibold text-sm">FiscalAI</p>
                <p className="text-slate-500 text-xs">Construit par Omar Khalouki</p>
              </div>
            </div>

            <p className="text-slate-400 text-sm text-center md:text-left">
              Disponible pour opportunités{" "}
              <span className="text-white">GovTech</span> ·{" "}
              <span className="text-white">Data Engineering</span> ·{" "}
              <span className="text-white">Full-Stack</span>
            </p>

            <div className="flex items-center gap-5">
              <a
                href={LINKEDIN_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
              >
                LinkedIn
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
              >
                GitHub
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href="mailto:okhalouki47@gmail.com"
                className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
              >
                <Mail className="w-4 h-4" />
                Contact
              </a>
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-slate-800">
            <p className="text-slate-600 text-xs text-center leading-relaxed max-w-3xl mx-auto">
              FiscalAI est un outil d'aide à la décision. Les détections produites sont des hypothèses
              basées sur des données publiques et des données transmises volontairement par la commune.
              Elles ne constituent en aucun cas des accusations ni des décisions administratives.
              Toute action reste de la compétence exclusive des agents habilités de la commune.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
