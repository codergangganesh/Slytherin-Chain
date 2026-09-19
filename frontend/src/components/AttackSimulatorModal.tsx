import React, { useState } from "react";
import {
  Zap,
  Play,
  CheckCircle2,
  X,
  AlertTriangle,
  Server,
  Lock,
  Radio,
  FileCode,
  ShieldCheck,
} from "lucide-react";
import { api } from "../api/client";

interface AttackSimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScenarioLaunched?: () => void;
}

interface ScenarioMeta {
  id: string;
  name: string;
  category: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  target: string;
  description: string;
  expectedResponse: string;
  icon: React.ReactNode;
}

const PRESET_SCENARIOS: ScenarioMeta[] = [
  {
    id: "ssh_brute_force_compromise",
    name: "SSH Brute Force + Privilege Escalation",
    category: "Credential Access & Execution",
    severity: "CRITICAL",
    target: "198.51.100.44 -> prod-api-01",
    description: "Rapid credential stuffing attacks triggering brute force detection, followed by root escalation.",
    expectedResponse: "Autonomous Block IP on Firewall (600s TTL)",
    icon: <Lock className="w-5 h-5 text-red-400" />,
  },
  {
    id: "ransomware_activity",
    name: "Ransomware Lateral Movement",
    category: "Impact & Lateral Movement",
    severity: "CRITICAL",
    target: "ws-finance-03",
    description: "Mass file encryption activity with volume shadow copy deletion and lateral SMB probing.",
    expectedResponse: "Host Quarantine via EDR + Canary Health Probe",
    icon: <Server className="w-5 h-5 text-orange-400" />,
  },
  {
    id: "protected_asset_attack",
    name: "Crown Jewel DB Attack (Protected Tier-1)",
    category: "Targeted Exploitation",
    severity: "HIGH",
    target: "prod-db-master",
    description: "SQL injection against primary PostgreSQL database. Triggers Protected Asset Guardrail.",
    expectedResponse: "Queued for Mandatory Analyst Review (Guardrail Gate)",
    icon: <ShieldCheck className="w-5 h-5 text-purple-400" />,
  },
  {
    id: "benign_admin_scan_false_positive",
    name: "Benign Corporate Vulnerability Scan",
    category: "Reconnaissance (Internal)",
    severity: "MEDIUM",
    target: "10.0.0.1 (Internal Gateway)",
    description: "Scheduled Qualys vulnerability scanner. Triggers CIDR Allowlist Guardrail suppression.",
    expectedResponse: "Action Suppressed (CIDR Allowlist Check)",
    icon: <Radio className="w-5 h-5 text-blue-400" />,
  },
];

export const AttackSimulatorModal: React.FC<AttackSimulatorModalProps> = ({
  isOpen,
  onClose,
  onScenarioLaunched,
}) => {
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [result, setResult] = useState<{ status: string; events_injected: number; alerts_triggered: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLaunch = async (scenarioId: string) => {
    setRunningScenario(scenarioId);
    setResult(null);
    setError(null);

    try {
      const res = await api.runScenario(scenarioId, 1.0);
      setResult(res);
      if (onScenarioLaunched) onScenarioLaunched();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to trigger simulation scenario";
      setError(msg);
    } finally {
      setRunningScenario(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Live Attack & Triage Simulator</h3>
              <p className="text-xs text-slate-400">Trigger multi-stage threat scenarios to evaluate real-time response & guardrails</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4 overflow-y-auto">
          {result && (
            <div className="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  <strong>Scenario Executed:</strong> Injected {result.events_injected} security telemetry events. Triggered {result.alerts_triggered} correlation alerts.
                </span>
              </div>
              <button
                onClick={() => {
                  onClose();
                  window.location.href = "/incidents";
                }}
                className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded text-[11px] font-semibold text-emerald-200 transition-colors"
              >
                View Incident &rarr;
              </button>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-950/30 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3">
            {PRESET_SCENARIOS.map((s) => {
              const isRunning = runningScenario === s.id;

              return (
                <div
                  key={s.id}
                  className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/80 hover:border-slate-700 transition-all space-y-2.5"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 shrink-0 mt-0.5">
                        {s.icon}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-semibold text-white">{s.name}</h4>
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                              s.severity === "CRITICAL"
                                ? "bg-red-500/20 text-red-400 border border-red-500/30"
                                : s.severity === "HIGH"
                                ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                                : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            }`}
                          >
                            {s.severity}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5">{s.description}</p>
                      </div>
                    </div>

                    <button
                      onClick={() => handleLaunch(s.id)}
                      disabled={Boolean(runningScenario)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shrink-0 ${
                        isRunning
                          ? "bg-blue-600/50 text-blue-200 cursor-not-allowed"
                          : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20"
                      }`}
                    >
                      <Play className={`w-3.5 h-3.5 ${isRunning ? "animate-spin" : ""}`} />
                      <span>{isRunning ? "Simulating..." : "Launch"}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/60 text-[11px]">
                    <div className="text-slate-400">
                      <span className="text-slate-500">Target Vector: </span>
                      <span className="text-slate-300 font-mono">{s.target}</span>
                    </div>
                    <div className="text-slate-400 text-right">
                      <span className="text-slate-500">Expected Guardrail Action: </span>
                      <span className="text-emerald-400 font-medium">{s.expectedResponse}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 flex items-center justify-between bg-slate-950/40 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <FileCode className="w-3.5 h-3.5 text-slate-500" />
            <span>Scenarios simulate Redis stream ingestion & real-time correlation.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
