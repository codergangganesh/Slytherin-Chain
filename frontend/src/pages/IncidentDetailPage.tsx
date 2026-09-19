import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Shield,
  ArrowLeft,
  FileDown,
  CheckCircle,
  XCircle,
  RotateCcw,
  Send,
  FileText,
  Clock,
} from "lucide-react";
import { api } from "../api/client";
import type { IncidentDetail, ResponseAction, TimelineEntry } from "../types";
import { PriorityBadge, StatusBadge } from "../components/SeverityBadge";
import { RiskGauge } from "../components/RiskGauge";
import { TimelineView } from "../components/TimelineView";
import { GuardrailDecisionsList } from "../components/GuardrailDecisionsList";

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [noteText, setNoteText] = useState("");
  const [submittingNote, setSubmittingNote] = useState(false);
  const [reportFormat, setReportFormat] = useState<"json" | "md" | "pdf">("pdf");
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportUrl, setReportUrl] = useState<string | null>(null);

  const fetchIncidentData = async () => {
    if (!id) return;
    try {
      const [inc, tl, act] = await Promise.all([
        api.getIncident(id),
        api.getIncidentTimeline(id),
        api.getResponseActions(id),
      ]);
      setIncident(inc);
      setTimeline(tl);
      setActions(act.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidentData();
  }, [id]);

  const handleApproveAction = async (actionId: string) => {
    try {
      await api.approveAction(actionId);
      await fetchIncidentData();
    } catch (err: any) {
      alert(`Approval error: ${err.message}`);
    }
  };

  const handleDenyAction = async (actionId: string) => {
    const reason = prompt("Enter reason for denying this response action:");
    if (!reason) return;
    try {
      await api.denyAction(actionId, reason);
      await fetchIncidentData();
    } catch (err: any) {
      alert(`Denial error: ${err.message}`);
    }
  };

  const handleRollbackAction = async (actionId: string) => {
    const reason = prompt("Enter reason for rolling back this action:");
    if (!reason) return;
    try {
      await api.rollbackAction(actionId, reason);
      await fetchIncidentData();
    } catch (err: any) {
      alert(`Rollback error: ${err.message}`);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !noteText.trim()) return;
    setSubmittingNote(true);
    try {
      await api.addIncidentNote(id, noteText);
      setNoteText("");
      await fetchIncidentData();
    } catch (err: any) {
      alert(`Error adding note: ${err.message}`);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleTransitionState = async (targetStatus: any) => {
    if (!id) return;
    const notes = prompt(`Enter resolution / transition notes for ${targetStatus}:`);
    try {
      await api.transitionIncident(id, targetStatus, notes || undefined);
      await fetchIncidentData();
    } catch (err: any) {
      alert(`State transition error: ${err.message}`);
    }
  };

  const handleGenerateReport = async () => {
    if (!id) return;
    setGeneratingReport(true);
    setReportUrl(null);
    try {
      const res = await api.generateReport(id, reportFormat);
      setReportUrl(res.download_url);
    } catch (err: any) {
      alert(`Report error: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading || !incident) {
    return <div className="p-8 text-center text-slate-400">Loading incident details...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <Link to="/incidents" className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-mono text-sm font-bold text-blue-400">{incident.reference_id}</span>
              <PriorityBadge priority={incident.priority} />
              <StatusBadge status={incident.status} />
            </div>
            <h1 className="text-xl font-bold text-white mt-1">{incident.title}</h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {incident.status !== "RESOLVED" && incident.status !== "CLOSED" && (
            <button
              onClick={() => handleTransitionState("RESOLVED")}
              className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-semibold transition-colors"
            >
              Resolve Incident
            </button>
          )}
          {incident.status !== "FALSE_POSITIVE" && (
            <button
              onClick={() => handleTransitionState("FALSE_POSITIVE")}
              className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 rounded-lg text-xs font-medium transition-colors"
            >
              Mark False Positive
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Risk & Actions */}
        <div className="space-y-6">
          {/* Risk Gauge */}
          <RiskGauge breakdown={incident.risk_breakdown} />

          {/* Response Actions Panel */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Shield className="w-4 h-4 text-indigo-400" />
              <span>Response Actions</span>
            </h3>

            {actions.length === 0 ? (
              <p className="text-xs text-slate-500">No response actions triggered yet.</p>
            ) : (
              <div className="space-y-3">
                {actions.map((act) => (
                  <div key={act.id} className="p-3.5 bg-slate-950/80 rounded-lg border border-slate-800 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-white uppercase">{act.action_type.replace("_", " ")}</span>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${
                        act.status === "SUCCEEDED" ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" :
                        act.status === "AWAITING_APPROVAL" ? "bg-amber-500/20 border-amber-500/30 text-amber-400 animate-pulse" :
                        act.status === "DENIED" ? "bg-red-500/20 border-red-500/30 text-red-400" :
                        act.status === "ROLLED_BACK" ? "bg-purple-500/20 border-purple-500/30 text-purple-400" :
                        "bg-slate-800 text-slate-400"
                      }`}>
                        {act.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-300 font-mono">
                      Target: <span className="text-blue-400">{act.target}</span>
                    </div>

                    {act.ttl_seconds && (
                      <div className="text-[11px] text-slate-400 flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>TTL: {act.ttl_seconds}s</span>
                      </div>
                    )}

                    {/* Guardrail Checklist */}
                    {act.guardrail_decisions && act.guardrail_decisions.length > 0 && (
                      <GuardrailDecisionsList decisions={act.guardrail_decisions} />
                    )}

                    {/* Action Execution Controls */}
                    {act.status === "AWAITING_APPROVAL" && (
                      <div className="flex items-center space-x-2 pt-2 border-t border-slate-800">
                        <button
                          onClick={() => handleApproveAction(act.id)}
                          className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Approve</span>
                        </button>
                        <button
                          onClick={() => handleDenyAction(act.id)}
                          className="flex-1 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Deny</span>
                        </button>
                      </div>
                    )}

                    {act.status === "SUCCEEDED" && (
                      <button
                        onClick={() => handleRollbackAction(act.id)}
                        className="w-full py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded text-xs font-medium flex items-center justify-center space-x-1 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Roll Back Action</span>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Report Generator Box */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <FileDown className="w-4 h-4 text-blue-400" />
              <span>Incident Report</span>
            </h3>
            <p className="text-xs text-slate-400">
              Export comprehensive 9-section report with cryptographic integrity attestation.
            </p>
            <div className="flex items-center space-x-2">
              <select
                value={reportFormat}
                onChange={(e) => setReportFormat(e.target.value as any)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
              >
                <option value="pdf">PDF Document</option>
                <option value="md">Markdown</option>
                <option value="json">JSON Format</option>
              </select>
              <button
                onClick={handleGenerateReport}
                disabled={generatingReport}
                className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold transition-colors disabled:opacity-50"
              >
                {generatingReport ? "Generating..." : "Generate Report"}
              </button>
            </div>

            {reportUrl && (
              <a
                href={reportUrl}
                target="_blank"
                rel="noreferrer"
                className="block text-center py-1.5 bg-emerald-600/20 border border-emerald-500/30 text-emerald-400 rounded text-xs font-semibold hover:bg-emerald-600/30 transition-colors"
              >
                Download Generated Report
              </a>
            )}
          </div>
        </div>

        {/* Right Column: Attack Timeline & Notes */}
        <div className="lg:col-span-2 space-y-6">
          {/* Attack Timeline */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>Attack Sequence & Investigation Timeline</span>
              </h3>
              <span className="text-xs font-mono text-slate-500">{timeline.length} entries</span>
            </div>

            <TimelineView entries={timeline} />
          </div>

          {/* Add Analyst Note Form */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
            <h3 className="text-sm font-semibold text-white mb-3">Add Investigation Note</h3>
            <form onSubmit={handleAddNote} className="space-y-3">
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Document containment findings, IOC verification, or follow-up tasks..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                required
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submittingNote || !noteText.trim()}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg text-xs flex items-center space-x-1.5 disabled:opacity-50 transition-colors"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submittingNote ? "Saving..." : "Append Note to Ledger"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
