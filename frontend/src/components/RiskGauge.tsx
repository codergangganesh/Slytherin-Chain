import React from "react";
import type { RiskBreakdown } from "../types";

export const RiskGauge: React.FC<{ breakdown?: RiskBreakdown | null }> = ({ breakdown }) => {
  if (!breakdown) return null;
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium text-slate-400">Calculated Risk Score</h3>
          <p className="text-2xl font-bold text-white mt-0.5">
            {breakdown.score} <span className="text-xs text-slate-500 font-normal">/ 100</span>
          </p>
        </div>
        <div className={`text-sm font-semibold px-3 py-1 rounded-md border ${
          breakdown.score >= 80 ? "bg-red-500/10 border-red-500/30 text-red-400" :
          breakdown.score >= 60 ? "bg-orange-500/10 border-orange-500/30 text-orange-400" :
          breakdown.score >= 40 ? "bg-yellow-500/10 border-yellow-500/30 text-yellow-400" :
          "bg-slate-500/10 border-slate-500/30 text-slate-400"
        }`}>
          {breakdown.priority} Priority
        </div>
      </div>

      <div className="space-y-3">
        {breakdown.factors.map((factor) => (
          <div key={factor.factor_name} className="text-xs">
            <div className="flex justify-between text-slate-300 mb-1">
              <span>{factor.factor_name}</span>
              <span className="font-mono text-slate-400">+{factor.contribution.toFixed(1)}</span>
            </div>
            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                style={{ width: `${Math.min(100, (factor.contribution / (factor.weight * 100)) * 100)}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">{factor.explanation}</p>
          </div>
        ))}

        {breakdown.correlation_bonus > 0 && (
          <div className="text-xs pt-1 border-t border-slate-800 flex justify-between text-indigo-400">
            <span>Multi-Alert Correlation Bonus</span>
            <span className="font-mono">+{breakdown.correlation_bonus.toFixed(1)}</span>
          </div>
        )}
      </div>

      <div className="mt-4 p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs text-slate-400">
        <span className="font-semibold text-slate-300">Explanation: </span>
        {breakdown.summary}
      </div>
    </div>
  );
};
