import React, { useState } from "react";
import {
  Shield,
  Lock,
  User as UserIcon,
  ShieldCheck,
  ShieldAlert,
  Eye,
  CheckCircle2,
  XCircle,
  KeyRound,
  Sparkles,
  ArrowRight,
  Info,
} from "lucide-react";
import { api } from "../api/client";

interface LoginPageProps {
  onLoginSuccess: () => void;
}

interface RolePersona {
  role: "admin" | "analyst" | "viewer";
  title: string;
  username: string;
  defaultPass: string;
  tagline: string;
  badge: string;
  badgeColor: string;
  borderColor: string;
  gradient: string;
  icon: React.ElementType;
  capabilities: string[];
}

const ROLES: RolePersona[] = [
  {
    role: "admin",
    title: "System Administrator",
    username: "admin",
    defaultPass: "admin_demo_password",
    tagline: "Full system control, guardrail tuning & policy governance",
    badge: "Full Privilege",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    borderColor: "border-purple-500/40 hover:border-purple-400",
    gradient: "from-purple-600/20 via-indigo-600/10 to-transparent",
    icon: ShieldAlert,
    capabilities: [
      "Autonomy Mode Switching (Full vs Supervised)",
      "Asset Criticality & Crown Jewel Classification",
      "System Settings & Rate Limit Tuning",
      "Manual & Autonomous Action Execution",
      "On-Chain Anchor Sealing & Verification",
    ],
  },
  {
    role: "analyst",
    title: "SOC Lead Analyst",
    username: "analyst",
    defaultPass: "analyst_demo_password",
    tagline: "Incident triage, containment approvals & investigations",
    badge: "Operations & Triage",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    borderColor: "border-blue-500/40 hover:border-blue-400",
    gradient: "from-blue-600/20 via-cyan-600/10 to-transparent",
    icon: ShieldCheck,
    capabilities: [
      "Approve & Deny Containment Actions",
      "Rollback Automated Host/IP Blocks",
      "Sign Findings to Audit Hash Ledger",
      "Resolve Incidents & Mark False Positives",
      "Generate 9-Section Compliance Reports",
    ],
  },
  {
    role: "viewer",
    title: "Compliance Auditor & Viewer",
    username: "viewer",
    defaultPass: "viewer_demo_password",
    tagline: "Read-only access, blockchain proofs & audit compliance",
    badge: "Read-Only / Auditor",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    borderColor: "border-emerald-500/40 hover:border-emerald-400",
    gradient: "from-emerald-600/20 via-teal-600/10 to-transparent",
    icon: Eye,
    capabilities: [
      "Inspect Real-Time Attack Streams",
      "Verify Cryptographic Merkle Proofs On-Chain",
      "Export Redacted Compliance Reports",
      "Review Autonomous Guardrail Reasoning",
      "Zero-Trust Read-Only Guarantee (No Mutations)",
    ],
  },
];

const RBAC_MATRIX = [
  { permission: "View Dashboard, Incidents & Telemetry", viewer: true, analyst: true, admin: true },
  { permission: "Trigger Attack Simulator Scenarios", viewer: true, analyst: true, admin: true },
  { permission: "Verify On-Chain Cryptographic Proofs", viewer: true, analyst: true, admin: true },
  { permission: "Export Redacted Incident Reports", viewer: true, analyst: true, admin: true },
  { permission: "Approve / Deny Containment Actions", viewer: false, analyst: true, admin: true },
  { permission: "Rollback Active Containment Blocks", viewer: false, analyst: true, admin: true },
  { permission: "Sign Investigation Notes to Ledger", viewer: false, analyst: true, admin: true },
  { permission: "Resolve Incidents / Mark False Positive", viewer: false, analyst: true, admin: true },
  { permission: "Seal Manual Blockchain Anchor Batches", viewer: false, analyst: true, admin: true },
  { permission: "Update Asset Tier & Autonomy Modes", viewer: false, analyst: false, admin: true },
  { permission: "Manage System Settings & Guardrail Caps", viewer: false, analyst: false, admin: true },
];

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [selectedRole, setSelectedRole] = useState<RolePersona>(ROLES[0]);
  const [username, setUsername] = useState(ROLES[0].username);
  const [password, setPassword] = useState(ROLES[0].defaultPass);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showRbacMatrix, setShowRbacMatrix] = useState(false);

  const handleSelectRole = (rolePersona: RolePersona) => {
    setSelectedRole(rolePersona);
    setUsername(rolePersona.username);
    setPassword(rolePersona.defaultPass);
    setError(null);
  };

  const handleLogin = async (e?: React.FormEvent, customUser?: string, customPass?: string) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);

    const userToAuth = customUser || username;
    const passToAuth = customPass || password;

    try {
      await api.login(userToAuth, passToAuth);
      onLoginSuccess();
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickRoleLogin = (rolePersona: RolePersona) => {
    handleSelectRole(rolePersona);
    handleLogin(undefined, rolePersona.username, rolePersona.defaultPass);
  };

  const ActiveIcon = selectedRole.icon;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 sm:p-6 lg:p-8 relative overflow-x-hidden">
      {/* Dynamic Background Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.15),rgba(255,255,255,0))] pointer-events-none" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-blue-500/10 blur-[130px] rounded-full pointer-events-none" />

      <div className="max-w-4xl w-full relative z-10 space-y-6">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl shadow-blue-500/20">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center justify-center space-x-2">
            <span>SentinelChain</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono font-bold">
              RBAC v1.0
            </span>
          </h1>
          <p className="text-sm text-slate-400 max-w-lg mx-auto">
            Autonomous Threat Response, Deterministic Guardrails & Blockchain Integrity Ledger
          </p>
        </div>

        {/* 3 Role Persona Cards */}
        <div>
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Select Access Persona</span>
            </span>
            <span className="text-xs text-slate-500">Click a card for instant role sign-in</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {ROLES.map((r) => {
              const isSelected = selectedRole.role === r.role;
              const Icon = r.icon;
              return (
                <div
                  key={r.role}
                  onClick={() => handleSelectRole(r)}
                  className={`relative cursor-pointer rounded-2xl p-5 border transition-all duration-200 text-left flex flex-col justify-between backdrop-blur-xl ${
                    isSelected
                      ? `bg-slate-900/90 ${r.borderColor} ring-2 ring-blue-500/30 shadow-2xl shadow-blue-500/10`
                      : "bg-slate-900/50 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700"
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className={`p-2.5 rounded-xl bg-gradient-to-br ${r.gradient} border border-slate-800 text-white`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase border ${r.badgeColor}`}>
                        {r.badge}
                      </span>
                    </div>

                    <div>
                      <h3 className="text-base font-bold text-white flex items-center space-x-1.5">
                        <span>{r.title}</span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">{r.tagline}</p>
                    </div>

                    <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                      {r.capabilities.slice(0, 3).map((cap, i) => (
                        <div key={i} className="flex items-center space-x-1.5 text-[11px] text-slate-300">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                          <span className="truncate">{cap}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 mt-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleQuickRoleLogin(r);
                      }}
                      className={`w-full py-2 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-1.5 shadow-md ${
                        isSelected
                          ? "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20"
                          : "bg-slate-800 hover:bg-slate-700 text-slate-200"
                      }`}
                    >
                      <span>Launch as {r.username}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Credentials & Sign In Box */}
        <div className="bg-slate-900/80 border border-slate-800/90 rounded-2xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl">
          {error && (
            <div className="mb-4 p-3.5 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-xs font-medium flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={(e) => handleLogin(e)} className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <ActiveIcon className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-bold text-white">
                  Active Persona: <span className="text-blue-400 font-mono">{selectedRole.title}</span>
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                User: <span className="text-slate-200 font-bold">{username}</span>
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Username</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors font-medium"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-10 py-2 text-xs text-white focus:outline-none focus:border-blue-500 transition-colors font-medium"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 text-xs"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    <KeyRound className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-blue-600/20 disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <span>Authenticating JWT...</span>
              ) : (
                <>
                  <span>Sign In as {selectedRole.title}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Expandable RBAC Permission Breakdown */}
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-4 backdrop-blur-md">
          <button
            type="button"
            onClick={() => setShowRbacMatrix(!showRbacMatrix)}
            className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 font-medium transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Info className="w-4 h-4 text-blue-400" />
              <span>View SentinelChain RBAC Permission Matrix</span>
            </div>
            <span className="text-[11px] font-mono text-blue-400">
              {showRbacMatrix ? "Hide Matrix ▲" : "Expand Matrix ▼"}
            </span>
          </button>

          {showRbacMatrix && (
            <div className="mt-4 pt-3 border-t border-slate-800/80 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                    <th className="pb-2">Capability / Operation</th>
                    <th className="pb-2 text-center text-emerald-400">Viewer</th>
                    <th className="pb-2 text-center text-blue-400">Analyst</th>
                    <th className="pb-2 text-center text-purple-400">Admin</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850 text-slate-300">
                  {RBAC_MATRIX.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="py-2.5 font-medium">{row.permission}</td>
                      <td className="py-2.5 text-center">
                        {row.viewer ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 inline" />
                        ) : (
                          <XCircle className="w-4 h-4 text-slate-600 inline" />
                        )}
                      </td>
                      <td className="py-2.5 text-center">
                        {row.analyst ? (
                          <CheckCircle2 className="w-4 h-4 text-blue-400 inline" />
                        ) : (
                          <XCircle className="w-4 h-4 text-slate-600 inline" />
                        )}
                      </td>
                      <td className="py-2.5 text-center">
                        {row.admin ? (
                          <CheckCircle2 className="w-4 h-4 text-purple-400 inline" />
                        ) : (
                          <XCircle className="w-4 h-4 text-slate-600 inline" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
