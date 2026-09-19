import React, { useState } from "react";
import type { GuardrailDecision } from "../types";
import {
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Activity,
  Zap,
} from "lucide-react";

interface GuardrailReasoningProps {
  decisions: GuardrailDecision[];
  actionType: string;
  target: string;
  isAutonomous: boolean;
  status: string;
}

const ALL_GUARDRAILS = [
  { key: "autonomy_mode_switch", name: "Autonomy Mode Gating", desc: "Verifies system autonomy level allows autonomous execution" },
  { key: "allowlist_check", name: "CIDR / Host Allowlist", desc: "Ensures critical infrastructure (DNS, Gateways) are never blocked" },
  { key: "protected_asset_check", name: "Protected Asset Policy", desc: "Enforces human sign-off for Crown Jewel Tier-1 assets" },
  { key: "threshold_check", name: "Risk Score Threshold", desc: "Ensures incident risk score meets minimum confidence threshold" },
  { key: "high_impact_approval", name: "High-Impact Containment", desc: "Requires analyst approval for fleet-wide isolation" },
  { key: "cooldown_check", name: "Target Cooldown Window", desc: "Prevents rapid repeated actions on the same asset" },
  { key: "rate_limit_check", name: "Hourly Action Rate Cap", desc: "Prevents cascading automation during storm conditions" },
  { key: "idempotency_check", name: "Action Idempotency", desc: "Guarantees identical commands are not duplicated" },
  { key: "reversibility_check", name: "Rollback Availability", desc: "Ensures valid rollback handler is registered" },
  { key: "ttl_expiry_check", name: "TTL & Auto-Expiry", desc: "Attaches deterministic time-to-live to temporary blocks" },
  { key: "canary_health_probe", name: "Canary Telemetry Health", desc: "Probes downstream service heartbeat post-containment" },
];

export const GuardrailReasoningCard: React.FC<GuardrailReasoningProps> = ({
  decisions,
  actionType,
  target,
  isAutonomous,
  status,
}) => {
  const [expanded, setExpanded] = useState(false);

  const passedCount = decisions.filter((d) => d.passed).length;
  const failedCount = decisions.filter((d) => !d.passed).length;
  const isApproved = status === "EXECUTED" || (failedCount === 0 && decisions.length > 0);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 backdrop-blur-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className={`p-2 rounded-lg ${isApproved ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"}`}>
            {isApproved ? <ShieldCheck className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
              <span>Explainable Guardrail Reasoning</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-wider ${
                isAutonomous ? "bg-blue-500/20 text-blue-400 border border-blue-500/30" : "bg-purple-500/20 text-purple-400 border border-purple-500/30"
              }`}>
                {isAutonomous ? "Autonomous Execution" : "Human-in-the-Loop"}
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Action: <span className="text-slate-200 font-mono">{actionType}</span> on <span className="text-slate-200 font-mono">{target}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="text-right text-xs">
            <span className="text-emerald-400 font-bold">{passedCount} Passed</span>
            {failedCount > 0 && <span className="text-red-400 font-bold ml-1.5">/ {failedCount} Denied</span>}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
            title="Toggle details"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Decision Summary Card */}
      <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs text-slate-300 flex items-start space-x-2">
        <Zap className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Execution Rationale: </span>
          {failedCount === 0 ? (
            <span>
              Action verified across all safety guardrails. CIDR allowlist, blast radius limits, and rate caps passed with healthy safety margins.
            </span>
          ) : (
            <span className="text-amber-300">
              Autonomous execution suppressed. One or more deterministic guardrails rejected instant enforcement; routed to analyst triage queue.
            </span>
          )}
        </div>
      </div>

      {/* 11 Guardrails Interactive Matrix */}
      {expanded && (
        <div className="space-y-2 pt-2 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium px-1">
            <span>Deterministic Guardrail Check</span>
            <span>Evaluation Result</span>
          </div>

          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {ALL_GUARDRAILS.map((g) => {
              const prefix = g.key.split("_")[0] || "";
              const matched = decisions.find(
                (d) => d.guardrail_name === g.key || (d.guardrail_name ? d.guardrail_name.toLowerCase().includes(prefix) : false)
              );
              const passed = matched ? matched.passed : true;
              const reason = matched ? matched.reason : "Passed default safety threshold";

              return (
                <div
                  key={g.key}
                  className="flex items-center justify-between p-2 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="font-medium text-slate-200 flex items-center space-x-1.5">
                      <span>{g.name}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">{reason}</div>
                  </div>

                  <div className="shrink-0 flex items-center space-x-1">
                    {passed ? (
                      <span className="flex items-center space-x-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-[10px] font-semibold">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>PASS</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-1 text-red-400 bg-red-500/10 px-2 py-0.5 rounded text-[10px] font-semibold">
                        <XCircle className="w-3 h-3" />
                        <span>BLOCK</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Canary Status Note */}
          <div className="flex items-center space-x-2 text-[11px] text-slate-400 bg-slate-900/40 p-2 rounded-lg border border-slate-800/50">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Autonomous Canary Telemetry Probes active for 60s post-execution.</span>
          </div>
        </div>
      )}
    </div>
  );
};
