"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { GapDetection } from "@/types/gap";
import { useUpdateGapStatus, useGenerateReport } from "@/lib/hooks/useGaps";

type GapStatus = GapDetection["status"];

interface StepDef {
  index: number;
  label: string;
}

const STEPS: StepDef[] = [
  { index: 0, label: "Analyser" },
  { index: 1, label: "Terrain" },
  { index: 2, label: "Valider" },
  { index: 3, label: "Rapport" },
  { index: 4, label: "Décision" },
];

function statusToStep(status: GapStatus): number {
  switch (status) {
    case "new":          return 0;
    case "under_review": return 2; // steps 1+2 are both actionable; show as past step 1
    case "notice_sent":  return 3;
    case "paid":
    case "contested":
    case "dismissed":    return 5;
    default:             return 0;
  }
}

export function WorkflowStepper({ gap }: { gap: GapDetection }) {
  const [noteText, setNoteText] = useState("");
  const [decision, setDecision] = useState<"" | "paid" | "contested" | "dismissed">("");

  const updateStatus   = useUpdateGapStatus();
  const generateReport = useGenerateReport();

  const gapId      = String(gap.id);
  const status     = gap.status;
  const activeStep = statusToStep(status);
  const isDone     = activeStep === 5;

  // Use mutate (not mutateAsync) so errors stay in mutation state and never
  // propagate as unhandled promise rejections.

  function handleAnalyser() {
    updateStatus.mutate({ gapId, status: "under_review" });
  }

  function handleSaveNote() {
    if (!noteText.trim()) return;
    updateStatus.mutate(
      { gapId, status: "under_review", note: noteText },
      { onSuccess: () => setNoteText("") },
    );
  }

  function handleValider() {
    updateStatus.mutate({ gapId, status: "notice_sent" });
  }

  function handleRapport() {
    generateReport.mutate({ gapId });
  }

  function handleDecision() {
    if (!decision) return;
    updateStatus.mutate(
      { gapId, status: decision },
      { onSuccess: () => setDecision("") },
    );
  }

  const mutationError = updateStatus.error ?? generateReport.error;

  return (
    <div className="space-y-4">
      {/* Step indicators */}
      <div className="flex items-center">
        {STEPS.map((step, i) => {
          const completed = step.index < activeStep;
          const current   = step.index === activeStep && !isDone;
          return (
            <div key={step.index} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                    isDone
                      ? "bg-green-600 text-white"
                      : completed
                      ? "bg-green-600 text-white"
                      : current
                      ? "bg-green-600 text-white ring-2 ring-green-400 ring-offset-1 ring-offset-slate-900"
                      : "bg-slate-700 text-slate-400"
                  }`}
                >
                  {completed || isDone ? <Check className="w-3.5 h-3.5" /> : step.index + 1}
                </div>
                <span className={`text-xs whitespace-nowrap ${current ? "text-white" : "text-slate-500"}`}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-px mb-4 mx-1 ${step.index < activeStep ? "bg-green-600" : "bg-slate-700"}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Action area */}
      {isDone ? (
        <div className="text-xs text-slate-500 text-center py-2">
          Dossier clôturé ({gap.status === "paid" ? "Payé" : gap.status === "contested" ? "Contesté" : "Classé"})
        </div>
      ) : status === "new" ? (
        <button
          onClick={handleAnalyser}
          disabled={updateStatus.isPending}
          className="w-full bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition-colors"
        >
          {updateStatus.isPending ? "En cours…" : "Analyser — passer en révision"}
        </button>
      ) : status === "under_review" ? (
        <div className="space-y-3">
          {/* Terrain note */}
          <div>
            <label className="text-xs text-slate-400 block mb-1">Note terrain (optionnelle)</label>
            <textarea
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              rows={2}
              placeholder="Ex: Vérification terrain effectuée le 22/06, bâtiment occupé…"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 px-3 py-2 resize-none focus:outline-none focus:border-green-500"
            />
            <button
              onClick={handleSaveNote}
              disabled={!noteText.trim() || updateStatus.isPending}
              className="mt-1 text-xs text-green-400 hover:text-green-300 disabled:opacity-40 transition-colors"
            >
              {updateStatus.isPending ? "Enregistrement…" : "Enregistrer la note"}
            </button>
          </div>
          {/* Validate */}
          <button
            onClick={handleValider}
            disabled={updateStatus.isPending}
            className="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition-colors"
          >
            {updateStatus.isPending ? "En cours…" : "Valider — envoyer mise en demeure"}
          </button>
        </div>
      ) : status === "notice_sent" ? (
        <div className="space-y-2">
          <button
            onClick={handleRapport}
            disabled={generateReport.isPending}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition-colors"
          >
            {generateReport.isPending ? "Génération…" : "Télécharger le rapport PDF"}
          </button>
          <div className="flex gap-2">
            <select
              value={decision}
              onChange={e => setDecision(e.target.value as typeof decision)}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white px-2 py-2 focus:outline-none focus:border-green-500"
            >
              <option value="">Décision communale…</option>
              <option value="paid">Payé</option>
              <option value="contested">Contesté</option>
              <option value="dismissed">Classé sans suite</option>
            </select>
            <button
              onClick={handleDecision}
              disabled={!decision || updateStatus.isPending}
              className="bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white text-xs font-medium px-3 py-2 rounded-lg transition-colors"
            >
              Confirmer
            </button>
          </div>
        </div>
      ) : null}

      {mutationError && (
        <p className="text-xs text-red-400 text-center">
          Erreur réseau — vérifier la connexion au serveur
        </p>
      )}
    </div>
  );
}
