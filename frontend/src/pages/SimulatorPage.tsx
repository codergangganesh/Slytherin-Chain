import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Play, CheckCircle, ArrowRight, Gauge } from "lucide-react";
import { api } from "../api/client";
import type { ScenarioInfo } from "../types";

export const SimulatorPage: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [speed, setSpeed] = useState(2.0);
  const [executionResult, setExecutionResult] = useState<any | null>(null);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const list = await api.getScenarios();
        setScenarios(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, []);

  if (loading && scenarios.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        Loading attack scenarios...
      </div>
    );
  }

  const handleLaunchScenario = async (name: string) => {
    setRunningScenario(name);
    setExecutionResult(null);
    try {
      const res = await api.runScenario(name, speed);
      setExecutionResult(res);
    } catch (err: any) {
      alert(`Simulation error: ${err.message}`);
    } finally {
      setRunningScenario(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Attack Simulator & Scenario Launcher</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Inject realistic multi-stage cyber attacks to validate autonomous response & guardrails in real time
          </p>
        </div>

        {/* Speed Multiplier Controls */}
        <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-xl p-1.5 text-xs">
          <Gauge className="w-4 h-4 text-blue-400 ml-1.5" />
          <span className="text-slate-400 font-medium">Speed:</span>
          {[1.0, 2.0, 5.0].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                speed === s ? "bg-blue-600 text-white shadow" : "text-slate-400 hover:text-white"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Execution Result Alert */}
      {executionResult && (
        <div className="p-4 bg-emerald-950/30 border border-emerald-500/40 rounded-xl flex items-center justify-between text-emerald-300 backdrop-blur-sm">
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <div>
              <h4 className="font-bold text-sm text-white">Scenario Injected Successfully!</h4>
              <p className="text-xs mt-0.5">
                Injected {executionResult.events_injected} events, triggered {executionResult.alerts_triggered} alerts across {executionResult.incidents_impacted} incident(s).
              </p>
            </div>
          </div>
          <Link
            to="/incidents"
            className="flex items-center space-x-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            <span>View Incidents</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {scenarios.map((sc) => (
          <div key={sc.name} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                  Target: {sc.target_asset}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                  Expected: {sc.expected_priority}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white">{sc.title}</h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{sc.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800 space-y-2.5">
              <div className="text-[11px] text-slate-400 flex items-center justify-between font-mono">
                <span>Guardrail / Response:</span>
                <span className="text-indigo-400">{sc.expected_response}</span>
              </div>

              <button
                onClick={() => handleLaunchScenario(sc.name)}
                disabled={runningScenario === sc.name}
                className="w-full py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center justify-center space-x-1.5 shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{runningScenario === sc.name ? "Injecting Attack Scenario..." : "Launch Scenario"}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
