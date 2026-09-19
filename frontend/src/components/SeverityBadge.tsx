import React from "react";
import type { IncidentPriority, IncidentStatus } from "../types";

export const PriorityBadge: React.FC<{ priority: IncidentPriority }> = ({ priority }) => {
  const styles: Record<IncidentPriority, string> = {
    P1: "bg-red-500/20 text-red-400 border-red-500/30",
    P2: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    P3: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    P4: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${styles[priority] || styles.P4}`}>
      {priority}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: IncidentStatus }> = ({ status }) => {
  const styles: Record<IncidentStatus, string> = {
    NEW: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    TRIAGED: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
    AWAITING_APPROVAL: "bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse",
    CONTAINED: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    INVESTIGATING: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    RESOLVED: "bg-green-500/20 text-green-400 border-green-500/30",
    CLOSED: "bg-slate-500/20 text-slate-400 border-slate-500/30",
    FALSE_POSITIVE: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status] || styles.NEW}`}>
      {status.replace("_", " ")}
    </span>
  );
};
