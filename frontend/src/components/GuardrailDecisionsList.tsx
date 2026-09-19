import React from "react";
import type { GuardrailDecision } from "../types";
import { Check, X, ShieldAlert } from "lucide-react";

export const GuardrailDecisionsList: React.FC<{ decisions: GuardrailDecision[] }> = ({ decisions }) => {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-blue-400" />
        <span>Guardrail Safety Evaluation</span>
      </h4>
      <div className="grid grid-cols-1 gap-2">
        {decisions.map((d, i) => (
          <div
            key={i}
            className={`p-2.5 rounded-lg border text-xs flex items-start space-x-2.5 ${
              d.passed
                ? "bg-slate-900/50 border-slate-800 text-slate-300"
                : "bg-red-950/20 border-red-500/30 text-red-300"
            }`}
          >
            <div className={`mt-0.5 p-0.5 rounded-full ${d.passed ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
              {d.passed ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
            </div>
            <div className="flex-1">
              <span className="font-semibold">{d.guardrail_name.replace(/_/g, " ")}: </span>
              <span>{d.reason}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
