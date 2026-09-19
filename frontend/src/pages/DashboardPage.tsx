import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Shield,
  AlertTriangle,
  Zap,
  Database,
  ArrowUpRight,
  RefreshCw,
  Activity,
} from "lucide-react";
import { api } from "../api/client";
import type { DashboardKpis, IncidentSummary } from "../types";
import { PriorityBadge, StatusBadge } from "../components/SeverityBadge";

const DEFAULT_KPIS: DashboardKpis = {
  open_incidents_count: 0,
  p1_critical_count: 0,
  p2_high_count: 0,
  actions_executed_today: 0,
  mean_time_to_contain_seconds: 240,
  autonomy_mode: "auto",
  integrity_status: "VERIFIED",
  priority_distribution: { P1: 0, P2: 0, P3: 0, P4: 0 },
  status_distribution: { NEW: 0, TRIAGED: 0, CONTAINED: 0, RESOLVED: 0 },
};

export const DashboardPage: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKpis>(DEFAULT_KPIS);
  const [recentIncidents, setRecentIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [summary, incRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getIncidents(),
      ]);
      setKpis(summary);
      setRecentIncidents(incRes.items.slice(0, 5));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Security Operations Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">Autonomous Threat Response & Audit Integrity Overview</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs">
            <span className="text-slate-400">Autonomy:</span>
            <span className="font-semibold text-emerald-400 uppercase tracking-wider">{kpis.autonomy_mode}</span>
          </div>
          <button
            onClick={fetchDashboardData}
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Open Incidents</span>
            <AlertTriangle className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{kpis.open_incidents_count}</span>
            <span className="text-xs text-slate-500">Active threats</span>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">P1 Critical Incidents</span>
            <Shield className="w-4 h-4 text-red-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-red-400">{kpis.p1_critical_count}</span>
            <span className="text-xs text-red-500/80 font-medium">Immediate priority</span>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Actions Executed Today</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white">{kpis.actions_executed_today}</span>
            <span className="text-xs text-slate-500">Autonomous/Approved</span>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Audit Integrity</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className={`text-base font-bold ${kpis.integrity_status === "VERIFIED" ? "text-emerald-400" : "text-amber-400"}`}>
              {kpis.integrity_status}
            </span>
            <span className="text-xs text-slate-500">On-chain verified</span>
          </div>
        </div>
      </div>

      {/* Priority Distribution & Live Incidents Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority breakdown */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <h3 className="text-sm font-semibold text-white mb-4">Priority Distribution</h3>
          <div className="space-y-3">
            {Object.entries(kpis.priority_distribution).map(([p, count]) => (
              <div key={p} className="text-xs">
                <div className="flex justify-between text-slate-300 mb-1">
                  <span className="font-semibold">{p} Priority</span>
                  <span className="font-mono text-slate-400">{count} incidents</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      p === "P1" ? "bg-red-500" : p === "P2" ? "bg-orange-500" : p === "P3" ? "bg-yellow-500" : "bg-slate-500"
                    }`}
                    style={{ width: `${Math.min(100, (count / Math.max(1, kpis.open_incidents_count)) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Mean Time to Contain (MTTC):</span>
            <span className="font-semibold text-white">~4 mins</span>
          </div>
        </div>

        {/* Live Incident Feed */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <span>Active Incident Feed</span>
            </h3>
            <Link to="/incidents" className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1">
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentIncidents.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-xs">
              No active incidents detected. Run a scenario from the Simulator to generate attack activity.
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {recentIncidents.map((inc) => (
                <div key={inc.id} className="py-3 flex items-center justify-between hover:bg-slate-800/30 px-2 rounded-lg transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs text-slate-400">{inc.reference_id}</span>
                      <PriorityBadge priority={inc.priority} />
                      <StatusBadge status={inc.status} />
                    </div>
                    <Link to={`/incidents/${inc.id}`} className="text-xs font-semibold text-white hover:text-blue-400 transition-colors block">
                      {inc.title}
                    </Link>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-white">{inc.risk_score} <span className="text-[10px] text-slate-500">/ 100</span></div>
                    <div className="text-[10px] text-slate-500">{new Date(inc.created_at).toLocaleTimeString()}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
