import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Search, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { IncidentPriority, IncidentStatus, IncidentSummary } from "../types";
import { PriorityBadge, StatusBadge } from "../components/SeverityBadge";

export const IncidentQueuePage: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | "">("");
  const [priorityFilter, setPriorityFilter] = useState<IncidentPriority | "">("");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const res = await api.getIncidents({
        status: statusFilter ? statusFilter : undefined,
        priority: priorityFilter ? priorityFilter : undefined,
      });
      setIncidents(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, priorityFilter]);

  const filteredIncidents = incidents.filter((inc) => {
    const q = searchQuery.toLowerCase();
    return (
      inc.title.toLowerCase().includes(q) ||
      inc.reference_id.toLowerCase().includes(q) ||
      (inc.primary_src_ip && inc.primary_src_ip.includes(q)) ||
      (inc.primary_host && inc.primary_host.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Incident Queue</h1>
          <p className="text-xs text-slate-400 mt-0.5">Correlated security incidents ordered by priority and risk score</p>
        </div>
        <button
          onClick={fetchIncidents}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs text-slate-300 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 backdrop-blur-sm flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by ID, title, IP, or host..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Priorities</option>
            <option value="P1">P1 - Critical</option>
            <option value="P2">P2 - High</option>
            <option value="P3">P3 - Medium</option>
            <option value="P4">P4 - Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="NEW">New</option>
            <option value="TRIAGED">Triaged</option>
            <option value="AWAITING_APPROVAL">Awaiting Approval</option>
            <option value="CONTAINED">Contained</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-4">Ref ID</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Incident Title</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Risk Score</th>
              <th className="py-3 px-4">Target / Attacker</th>
              <th className="py-3 px-4">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-xs">
            {loading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-500">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-500" />
                  Loading incident queue...
                </td>
              </tr>
            ) : filteredIncidents.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-500">
                  No incidents match the selected criteria.
                </td>
              </tr>
            ) : (
              filteredIncidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-semibold text-blue-400">
                    <Link to={`/incidents/${inc.id}`}>{inc.reference_id}</Link>
                  </td>
                  <td className="py-3 px-4">
                    <PriorityBadge priority={inc.priority} />
                  </td>
                  <td className="py-3 px-4 font-medium text-white max-w-xs truncate">
                    <Link to={`/incidents/${inc.id}`} className="hover:text-blue-400 transition-colors">
                      {inc.title}
                    </Link>
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={inc.status} />
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-bold text-white">{inc.risk_score}</span>
                    <span className="text-[10px] text-slate-500"> / 100</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-300 text-[11px]">
                    {inc.primary_host || inc.primary_src_ip || "Internal Target"}
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-[11px]">
                    {new Date(inc.created_at).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
