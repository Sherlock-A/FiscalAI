"use client";

import { GapDetection } from "@/types/gap";
import { GeoDataSection }     from "./EvidenceSlideOver/GeoDataSection";
import { RegistreSection }     from "./EvidenceSlideOver/RegistreSection";
import { FinancialSection }    from "./EvidenceSlideOver/FinancialSection";
import { XaiScoreBreakdown }   from "./XaiScoreBreakdown";
import { WorkflowStepper }     from "./WorkflowStepper";

const GAP_TYPE_BADGES: Record<string, { label: string; className: string }> = {
  missing_declaration: { label: "Déclaration manquante",  className: "bg-red-500/15 text-red-400" },
  underdeclared:       { label: "Sous-déclaration",        className: "bg-orange-500/15 text-orange-400" },
  unlicensed_business: { label: "Commerce non déclaré",   className: "bg-purple-500/15 text-purple-400" },
};

const STATUS_LABELS: Record<string, string> = {
  new:          "Nouveau",
  under_review: "En révision",
  notice_sent:  "MED envoyée",
  paid:         "Payé",
  contested:    "Contesté",
  dismissed:    "Classé",
};

interface Props {
  gap: GapDetection;
  onClose: () => void;
}

export function EvidenceSlideOver({ gap, onClose }: Props) {
  const confidence = Math.round(Number(gap.confidence_score ?? 0) * 100);
  const badge      = GAP_TYPE_BADGES[gap.gap_type] ?? { label: gap.gap_type, className: "bg-slate-700 text-slate-300" };
  const statusLabel = STATUS_LABELS[gap.status] ?? gap.status;

  return (
    <div className="absolute top-0 right-0 h-full w-[360px] z-20 bg-slate-900 border-l border-slate-700 flex flex-col shadow-2xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-start justify-between gap-2 flex-shrink-0">
        <div className="min-w-0">
          <p className="text-white text-sm font-semibold truncate" title={gap.address_resolved ?? ""}>
            {gap.address_resolved ?? "Adresse inconnue"}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.className}`}>
              {badge.label}
            </span>
            <span className={`text-xs font-semibold ${
              confidence >= 70 ? "text-red-400" : confidence >= 55 ? "text-orange-400" : "text-yellow-400"
            }`}>
              {confidence}% confiance
            </span>
            <span className="text-xs text-slate-500">{statusLabel}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white transition-colors flex-shrink-0 mt-0.5"
          aria-label="Fermer"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800">
        {/* Données géospatiales */}
        <Section title="Données géospatiales">
          <GeoDataSection gap={gap} />
        </Section>

        {/* Registre communal */}
        <Section title="Registre communal">
          <RegistreSection gap={gap} />
        </Section>

        {/* Score de confiance IA */}
        <Section title="Score de confiance IA">
          <XaiScoreBreakdown gap={gap} />
        </Section>

        {/* Impact financier */}
        <Section title="Impact financier">
          <FinancialSection gap={gap} />
        </Section>

        {/* Workflow de traitement */}
        <Section title="Traitement du dossier">
          <WorkflowStepper gap={gap} />
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="px-4 py-4">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">{title}</h3>
      {children}
    </div>
  );
}
