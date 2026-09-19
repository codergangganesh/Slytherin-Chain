import React, { useEffect, useState } from "react";
import { BookOpen, Settings, CheckCircle } from "lucide-react";
import { api } from "../api/client";

export const PlaybooksPage: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<any[]>([]);
  const [autonomyMode, setAutonomyMode] = useState("auto");
  const [loading, setLoading] = useState(true);
  const [savingMode, setSavingMode] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pb, modeRes] = await Promise.all([
        api.getPlaybooks(),
        api.getAutonomyMode(),
      ]);
      setPlaybooks(pb);
      setAutonomyMode(modeRes.autonomy_mode);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && playbooks.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        Loading response playbooks...
      </div>
    );
  }

  const handleModeChange = async (newMode: string) => {
    if (!confirm(`Are you sure you want to change system autonomy mode to '${newMode}'?`)) return;
    setSavingMode(true);
    try {
      await api.updateAutonomyMode(newMode);
      setAutonomyMode(newMode);
    } catch (err: any) {
      alert(`Error updating autonomy mode: ${err.message}`);
    } finally {
      setSavingMode(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Response Playbooks & Automation Policies</h1>
          <p className="text-xs text-slate-400 mt-0.5">Declarative threat response workflows and autonomy guardrail controls</p>
        </div>
      </div>

      {/* Autonomy Mode Switcher Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3 shadow-xl">
        <div className="flex items-center space-x-2.5">
          <Settings className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-bold text-white">System Runtime Autonomy Mode</h3>
        </div>
        <p className="text-xs text-slate-400">
          Controls whether the platform executes containment actions automatically or holds them for analyst review.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2">
          {[
            { id: "auto", label: "Auto (Default)", desc: "Execute automatically when all 11 guardrails pass" },
            { id: "approval_required", label: "Approval Required", desc: "Escalate all actions to human sign-off" },
            { id: "recommend_only", label: "Recommend Only", desc: "Propose actions in timeline without executing" },
            { id: "off", label: "Off", desc: "Completely disable autonomous response actions" },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => handleModeChange(mode.id)}
              disabled={savingMode}
              className={`p-3 rounded-lg border text-left transition-all ${
                autonomyMode === mode.id
                  ? "bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                  : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-xs text-white">{mode.label}</span>
                {autonomyMode === mode.id && <CheckCircle className="w-3.5 h-3.5 text-blue-400" />}
              </div>
              <p className="text-[10px] text-slate-400 leading-relaxed">{mode.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Playbooks Catalog */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {playbooks.map((pb) => (
          <div key={pb.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">{pb.id}</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Category: {pb.applies_to_category}
              </span>
            </div>

            <div className="text-xs text-slate-400 space-y-1 bg-slate-950 p-2.5 rounded border border-slate-800">
              <div>Trigger Score: <span className="font-mono text-white">&gt;= {pb.conditions?.min_risk_score}</span></div>
              <div>Min Confidence: <span className="font-mono text-white">&gt;= {pb.conditions?.min_confidence}</span></div>
            </div>

            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-semibold text-slate-300">Target Actions:</span>
              {pb.actions?.map((act: any, idx: number) => (
                <div key={idx} className="p-2 bg-slate-950/60 rounded border border-slate-800 text-xs font-mono flex items-center justify-between">
                  <span className="text-blue-400">{act.action_type}</span>
                  <span className="text-slate-400">Target: {act.target}</span>
                  {act.ttl_seconds && <span className="text-slate-500">TTL {act.ttl_seconds}s</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
