import React from "react";
import type { TimelineEntry } from "../types";
import { Shield, AlertTriangle, CheckCircle, Clock, FileText, Ban } from "lucide-react";

export const TimelineView: React.FC<{ entries: TimelineEntry[] }> = ({ entries }) => {
  const getIcon = (entryType: string) => {
    switch (entryType) {
      case "INCIDENT_CREATED":
        return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case "ACTION_EXECUTED":
      case "ACTION_APPROVED":
        return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case "ACTION_DENIED":
        return <Ban className="w-4 h-4 text-red-400" />;
      case "STATE_TRANSITION":
        return <Shield className="w-4 h-4 text-blue-400" />;
      case "ANALYST_NOTE":
        return <FileText className="w-4 h-4 text-purple-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="relative border-l border-slate-800 ml-4 space-y-6 py-2">
      {entries.map((item) => (
        <div key={item.id} className="relative pl-6">
          <div className="absolute -left-3 top-1 w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center">
            {getIcon(item.entry_type)}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-white">{item.title}</span>
              {item.mitre_tactic && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  {item.mitre_tactic} {item.mitre_technique ? `(${item.mitre_technique})` : ""}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
            <div className="flex items-center space-x-3 text-[10px] text-slate-500 mt-1 font-mono">
              <span>{new Date(item.timestamp).toUTCString()}</span>
              <span>•</span>
              <span>Actor: {item.actor}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
