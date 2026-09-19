import React, { useEffect, useState } from "react";
import { Zap, CheckCircle, XCircle, RotateCcw, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { ResponseAction } from "../types";
import { GuardrailDecisionsList } from "../components/GuardrailDecisionsList";

export const ResponseActionsPage: React.FC = () => {
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchActions = async () => {
    setLoading(true);
    try {
      const res = await api.getResponseActions();
      setActions(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await api.approveAction(id);
      await fetchActions();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleDeny = async (id: string) => {
    const reason = prompt("Enter reason for denying this action:");
    if (!reason) return;
    try {
      await api.denyAction(id, reason);
      await fetchActions();
    } catch (err: any) {
      alert(`Denial error: ${err.message}`);
    }
  };

  const handleRollback = async (id: string) => {
    const reason = prompt("Enter reason for rolling back this action:");
    if (!reason) return;
    try {
      await api.rollbackAction(id, reason);
      await fetchActions();
    } catch (err: any) {
      alert(`Rollback error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Global Response Action Log</h1>
          <p className="text-xs text-slate-400 mt-0.5">Audit history of autonomous executions, approvals, and guardrail denials</p>
        </div>
        <button
          onClick={fetchActions}
          className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12 text-slate-500 text-xs">Loading response action history...</div>
        ) : actions.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-xs">No response actions recorded yet.</div>
        ) : (
          actions.map((act) => (
            <div key={act.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5">
                  <div className={`p-2 rounded-lg ${
                    act.status === "SUCCEEDED" ? "bg-emerald-500/20 text-emerald-400" :
                    act.status === "AWAITING_APPROVAL" ? "bg-amber-500/20 text-amber-400 animate-pulse" :
                    act.status === "DENIED" ? "bg-red-500/20 text-red-400" :
                    act.status === "ROLLED_BACK" ? "bg-purple-500/20 text-purple-400" :
                    "bg-slate-800 text-slate-400"
                  }`}>
                    <Zap className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white uppercase">{act.action_type.replace("_", " ")}</h3>
                    <p className="font-mono text-xs text-blue-400">Target: {act.target}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${
                    act.status === "SUCCEEDED" ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" :
                    act.status === "AWAITING_APPROVAL" ? "bg-amber-500/20 border-amber-500/30 text-amber-400 animate-pulse" :
                    act.status === "DENIED" ? "bg-red-500/20 border-red-500/30 text-red-400" :
                    act.status === "ROLLED_BACK" ? "bg-purple-500/20 border-purple-500/30 text-purple-400" :
                    "bg-slate-800 text-slate-400 border-slate-700"
                  }`}>
                    {act.status}
                  </span>

                  {act.status === "AWAITING_APPROVAL" && (
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={() => handleApprove(act.id)}
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center space-x-1"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Approve</span>
                      </button>
                      <button
                        onClick={() => handleDeny(act.id)}
                        className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded text-xs font-semibold flex items-center space-x-1"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Deny</span>
                      </button>
                    </div>
                  )}

                  {act.status === "SUCCEEDED" && (
                    <button
                      onClick={() => handleRollback(act.id)}
                      className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded text-xs font-medium flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Roll Back</span>
                    </button>
                  )}
                </div>
              </div>

              {act.denial_reason && (
                <div className="p-2.5 bg-red-950/20 border border-red-500/30 rounded text-xs text-red-300">
                  <span className="font-semibold">Guardrail Denial Reason: </span>
                  {act.denial_reason}
                </div>
              )}

              {act.rollback_reason && (
                <div className="p-2.5 bg-purple-950/20 border border-purple-500/30 rounded text-xs text-purple-300">
                  <span className="font-semibold">Rollback Reason: </span>
                  {act.rollback_reason}
                </div>
              )}

              {act.guardrail_decisions && act.guardrail_decisions.length > 0 && (
                <div className="pt-2 border-t border-slate-800">
                  <GuardrailDecisionsList decisions={act.guardrail_decisions} />
                </div>
              )}

              <div className="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500 font-mono flex items-center justify-between">
                <span>Created: {new Date(act.created_at).toLocaleString()}</span>
                {act.ttl_seconds && <span>TTL: {act.ttl_seconds}s</span>}
                {act.approved_by && <span>Sign-off: {act.approved_by}</span>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
