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
import { GuardrailReasoningCard } from "../components/GuardrailReasoningCard";

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [noteText, setNoteText] = useState("");
  const [submittingNote, setSubmittingNote] = useState(false);
  const [reportFormat, setReportFormat] = useState<"json" | "md" | "pdf">("pdf");
  const [redactedReport, setRedactedReport] = useState(false);
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
      const res = await api.generateReport(id, reportFormat, redactedReport);
      setReportUrl(res.download_url);
    } catch (err: any) {
      alert(`Report error: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const [downloadingReport, setDownloadingReport] = useState(false);

  const handleDownloadReport = async () => {
    if (!reportUrl) return;
    setDownloadingReport(true);
    try {
      const token = localStorage.getItem("sentinel_token");
      const res = await fetch(reportUrl, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Download failed: HTTP ${res.status}`);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `incident_report_${incident?.reference_id || id}.${reportFormat}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (e: any) {
      alert(`Download error: ${e.message}`);
    } finally {
      setDownloadingReport(false);
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
        {/* Left Column (2 Cols): Response Actions & Attack Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Response Actions & Guardrail Safety Engine */}
          <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>Automated Response & Safety Guardrails</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                      {actions.length} {actions.length === 1 ? "Action" : "Actions"}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Deterministic 11-guardrail evaluations, containment actions, and canary status
                  </p>
                </div>
              </div>
            </div>

            {actions.length === 0 ? (
              <div className="p-8 text-center bg-slate-950/40 rounded-xl border border-slate-800/60 text-slate-500 text-xs">
                No autonomous containment actions triggered for this incident.
              </div>
            ) : (
              <div className="space-y-4">
                {actions.map((act) => (
                  <div
                    key={act.id}
                    className="p-5 bg-slate-950/60 rounded-xl border border-slate-800/90 hover:border-slate-700/80 transition-all space-y-4 shadow-lg"
                  >
                    {/* Action Header */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center space-x-3">
                        <span className="font-mono text-sm font-bold text-white bg-slate-900 px-3 py-1 rounded-lg border border-slate-800">
                          {act.action_type.replace(/_/g, " ")}
                        </span>
                        <div className="text-xs font-mono text-slate-300 bg-blue-950/30 border border-blue-500/20 px-2.5 py-1 rounded-lg">
                          Target: <span className="text-blue-400 font-semibold">{act.target}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {act.ttl_seconds && (
                          <span className="text-[11px] text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800 flex items-center space-x-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span>TTL: {act.ttl_seconds}s</span>
                          </span>
                        )}

                        <span
                          className={`text-xs font-bold px-3 py-1 rounded-lg border ${
                            act.status === "SUCCEEDED"
                              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                              : act.status === "AWAITING_APPROVAL"
                              ? "bg-amber-500/20 border-amber-500/40 text-amber-300 animate-pulse"
                              : act.status === "DENIED"
                              ? "bg-red-500/20 border-red-500/40 text-red-300"
                              : act.status === "ROLLED_BACK"
                              ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {act.status}
                        </span>
                      </div>
                    </div>

                    {/* Action Execution Controls */}
                    {act.status === "AWAITING_APPROVAL" && (
                      <div className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-xl flex items-center justify-between gap-3">
                        <span className="text-xs text-amber-300 font-medium">
                          Action requires manual authorization (Protected Asset / High-Impact Policy).
                        </span>
                        <div className="flex items-center space-x-2 shrink-0">
                          <button
                            onClick={() => handleApproveAction(act.id)}
                            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors shadow-lg shadow-emerald-600/20"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Approve & Execute</span>
                          </button>
                          <button
                            onClick={() => handleDenyAction(act.id)}
                            className="px-4 py-1.5 bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Deny Action</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {act.status === "SUCCEEDED" && (
                      <div className="flex justify-end">
                        <button
                          onClick={() => handleRollbackAction(act.id)}
                          className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-300 hover:text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
                          <span>Roll Back Containment</span>
                        </button>
                      </div>
                    )}

                    {/* Explainable Guardrail Reasoning Card */}
                    {act.guardrail_decisions && act.guardrail_decisions.length > 0 && (
                      <GuardrailReasoningCard
                        decisions={act.guardrail_decisions}
                        actionType={act.action_type}
                        target={act.target}
                        isAutonomous={!act.approved_by}
                        status={act.status}
                      />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Attack Sequence Timeline */}
          <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-6 backdrop-blur-md shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Attack Sequence & Investigation Timeline</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Chronological trace of ingested events, triggers, and containment decisions</p>
                </div>
              </div>
              <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-lg">
                {timeline.length} Entries
              </span>
            </div>

            <TimelineView entries={timeline} />
          </div>
        </div>

        {/* Right Column (1 Col): Risk Gauge, Metadata, Reports & Notes */}
        <div className="space-y-6">
          {/* Risk Gauge Card */}
          <RiskGauge breakdown={incident.risk_breakdown} />

          {/* Incident Metadata Overview */}
          <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 backdrop-blur-md shadow-xl space-y-3.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Incident Metadata</h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Primary Host</span>
                <span className="text-slate-200 font-mono truncate block mt-0.5">{incident.primary_host || "N/A"}</span>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Source IP</span>
                <span className="text-blue-400 font-mono truncate block mt-0.5">{incident.primary_src_ip || "N/A"}</span>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">User Context</span>
                <span className="text-slate-200 font-mono truncate block mt-0.5">{incident.primary_username || "N/A"}</span>
              </div>
              <div className="p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/60">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Assigned Analyst</span>
                <span className="text-slate-300 font-mono text-[11px] truncate block mt-0.5">{incident.assigned_to || "Autonomous Triage"}</span>
              </div>
            </div>
          </div>

          {/* Report Generator Box */}
          <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 backdrop-blur-md shadow-xl space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <FileDown className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Incident Report Export</h3>
                <p className="text-[11px] text-slate-400">9-section report with on-chain cryptographic proof</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as any)}
                  className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500 font-medium"
                >
                  <option value="pdf">PDF Document</option>
                  <option value="md">Markdown (.md)</option>
                  <option value="json">JSON Schema</option>
                </select>
                <button
                  onClick={handleGenerateReport}
                  disabled={generatingReport}
                  className="flex-1 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition-colors disabled:opacity-50 shadow-lg shadow-blue-600/20"
                >
                  {generatingReport ? "Generating..." : "Generate"}
                </button>
              </div>

              <label className="flex items-center space-x-2.5 p-2 bg-slate-950/60 rounded-xl border border-slate-800/60 text-xs text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={redactedReport}
                  onChange={(e) => setRedactedReport(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-0 w-4 h-4"
                />
                <span className="text-[11px]">Redact PII (Auditor & Insurer Safe)</span>
              </label>
            </div>

            {reportUrl && (
              <button
                type="button"
                onClick={handleDownloadReport}
                disabled={downloadingReport}
                className="w-full py-2 bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 rounded-xl text-xs font-bold hover:bg-emerald-600/30 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>{downloadingReport ? "Downloading..." : "Download Generated Report"}</span>
              </button>
            )}
          </div>

          {/* Add Analyst Note Form */}
          <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 backdrop-blur-md shadow-xl space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Investigation Notes</h3>
            <form onSubmit={handleAddNote} className="space-y-3">
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Append findings or analyst observations to hash ledger..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                required
              />
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={submittingNote || !noteText.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl text-xs flex items-center space-x-1.5 disabled:opacity-50 transition-colors shadow-lg shadow-blue-600/20"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{submittingNote ? "Signing..." : "Append Note"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
