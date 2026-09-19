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
  Activity,
  Zap,
  LockKeyhole,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "../api/client";

interface LoginPageProps {
  onLoginSuccess: () => void;
}

interface RolePersona {
  role: "admin" | "analyst" | "viewer";
  title: string;
  shortTitle: string;
  username: string;
  defaultPass: string;
  tagline: string;
  badge: string;
  badgeColor: string;
  activeRing: string;
  accentColor: string;
  gradient: string;
  icon: React.ElementType;
  capabilities: string[];
}

const ROLES: RolePersona[] = [
  {
    role: "admin",
    title: "System Administrator",
    shortTitle: "Admin",
    username: "admin",
    defaultPass: "admin_demo_password",
    tagline: "Full platform control, blast radius thresholds, asset criticality & policy governance.",
    badge: "Full Privilege",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    activeRing: "border-purple-500 text-purple-400 bg-purple-500/10 shadow-purple-500/20",
    accentColor: "text-purple-400",
    gradient: "from-purple-600 via-indigo-600 to-blue-600",
    icon: ShieldAlert,
    capabilities: [
      "Full Autonomy Mode Switching & Governance",
      "Asset Criticality & Crown Jewel Classification",
      "Deterministic 11-Guardrail Policy Tuning",
      "Manual & Autonomous Containment Enforcement",
      "On-Chain Anchor Sealing & Smart Contract Verification",
    ],
  },
  {
    role: "analyst",
    title: "SOC Lead Analyst",
    shortTitle: "SOC Analyst",
    username: "analyst",
    defaultPass: "analyst_demo_password",
    tagline: "Live incident triage, manual action approvals, containment rollbacks & findings sign-off.",
    badge: "Triage & Ops",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    activeRing: "border-blue-500 text-blue-400 bg-blue-500/10 shadow-blue-500/20",
    accentColor: "text-blue-400",
    gradient: "from-blue-600 via-cyan-600 to-indigo-600",
    icon: ShieldCheck,
    capabilities: [
      "Approve / Deny Pending Containment Actions",
      "Rollback Automated Host & IP Blocks",
      "Sign Analyst Findings Directly to Hash Ledger",
      "Transition Incident Lifecycle & Resolve Threats",
      "Generate 9-Section PDF/Markdown Compliance Reports",
    ],
  },
  {
    role: "viewer",
    title: "Compliance Auditor & Viewer",
    shortTitle: "Auditor",
    username: "viewer",
    defaultPass: "viewer_demo_password",
    tagline: "Zero-trust read-only telemetry, on-chain Merkle root proofs & redacted compliance exports.",
    badge: "Read-Only Auditor",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    activeRing: "border-emerald-500 text-emerald-400 bg-emerald-500/10 shadow-emerald-500/20",
    accentColor: "text-emerald-400",
    gradient: "from-emerald-600 via-teal-600 to-blue-600",
    icon: Eye,
    capabilities: [
      "Live Attack Sequence & Telemetry Stream Inspection",
      "Verify Cryptographic Merkle Proofs against Smart Contract",
      "Export Privacy-Redacted Compliance Reports (PII Masked)",
      "Explainable Guardrail Reasoning ('Why It Passed') Review",
      "Zero-Trust Read-Only Protection (Mutations Blocked by RBAC)",
    ],
  },
];

const RBAC_MATRIX = [
  { permission: "View Dashboard, Real-time Incidents & Telemetry", viewer: true, analyst: true, admin: true },
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
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4 sm:p-6 lg:p-10 relative overflow-x-hidden text-slate-100">
      {/* Background Ambient Glow Gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.18),rgba(255,255,255,0))] pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 -translate-x-1/2 w-[600px] h-[300px] bg-blue-600/10 blur-[140px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[250px] bg-indigo-600/10 blur-[130px] rounded-full pointer-events-none" />

      {/* Main 2-Column Split Container */}
      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch relative z-10">
        
        {/* ========================================================================= */}
        {/* LEFT COLUMN (7 Cols): Hero Showcase, Live Telemetry & Persona Capabilities */}
        {/* ========================================================================= */}
        <div className="lg:col-span-7 flex flex-col justify-between space-y-6 p-6 sm:p-8 bg-slate-900/60 border border-slate-850 rounded-3xl backdrop-blur-2xl shadow-2xl relative overflow-hidden">
          {/* Subtle Accent Glow Border */}
          <div className="absolute -top-24 -left-24 w-72 h-72 bg-blue-500/15 blur-3xl rounded-full pointer-events-none" />

          {/* Top Hero Brand Header */}
          <div className="space-y-4">
            <div className="flex items-center space-x-3.5">
              <div className="p-3 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 text-white shadow-xl shadow-blue-500/25 ring-1 ring-white/20">
                <Shield className="w-7 h-7" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-black text-white tracking-tight">SentinelChain</span>
                  <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono font-bold tracking-wider">
                    v1.0 SOC
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-medium mt-0.5">
                  Autonomous Threat Response & Cryptographic Blockchain Integrity Platform
                </p>
              </div>
            </div>

            {/* Live Telemetry KPI Strip */}
            <div className="grid grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
                <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] font-medium">
                  <Activity className="w-3.5 h-3.5 text-blue-400" />
                  <span>Avg Response</span>
                </div>
                <span className="text-lg font-bold text-white font-mono block mt-1">1.8s</span>
                <span className="text-[10px] text-emerald-400 font-medium block">Sub-3s SLA</span>
              </div>

              <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
                <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] font-medium">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Guardrails</span>
                </div>
                <span className="text-lg font-bold text-white font-mono block mt-1">11 Active</span>
                <span className="text-[10px] text-blue-400 font-medium block">Deterministic</span>
              </div>

              <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
                <div className="flex items-center space-x-1.5 text-slate-400 text-[11px] font-medium">
                  <Zap className="w-3.5 h-3.5 text-purple-400" />
                  <span>On-Chain Anchors</span>
                </div>
                <span className="text-lg font-bold text-white font-mono block mt-1">Merkle Proof</span>
                <span className="text-[10px] text-purple-400 font-medium block">EVM Immutable</span>
              </div>
            </div>
          </div>

          {/* Dynamic Active Persona Capabilities Showcase */}
          <div className="p-5 bg-slate-950/80 border border-slate-800/90 rounded-2xl space-y-3.5 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className={`p-2 rounded-xl bg-slate-900 border border-slate-800 ${selectedRole.accentColor}`}>
                  <ActiveIcon className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                    <span>{selectedRole.title}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase border ${selectedRole.badgeColor}`}>
                      {selectedRole.badge}
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">{selectedRole.tagline}</p>
                </div>
              </div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Authorized Persona Capabilities
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {selectedRole.capabilities.map((cap, i) => (
                  <div
                    key={i}
                    className="flex items-start space-x-2 p-2 rounded-xl bg-slate-900/50 border border-slate-800/60 text-xs text-slate-300"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span className="text-[11px] leading-tight font-medium">{cap}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Security Footer */}
          <div className="pt-3 border-t border-slate-800/60 flex flex-wrap items-center justify-between text-[11px] text-slate-400 gap-2">
            <div className="flex items-center space-x-2">
              <LockKeyhole className="w-3.5 h-3.5 text-blue-400" />
              <span>Argon2 Password Hashing & Short-Lived JWT RBAC</span>
            </div>
            <span className="text-slate-500 font-mono text-[10px]">Foundry Solidity AnchorRegistry.sol</span>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN (5 Cols): Authentication Form, Role Switcher Tabs & 1-Click Launch */}
        {/* ========================================================================= */}
        <div className="lg:col-span-5 flex flex-col justify-between space-y-6 p-6 sm:p-8 bg-slate-900/80 border border-slate-800 rounded-3xl backdrop-blur-2xl shadow-2xl">
          
          <div className="space-y-5">
            {/* Header */}
            <div>
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Command Center Portal</span>
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight mt-1">Sign In to SentinelChain</h2>
              <p className="text-xs text-slate-400 mt-1">
                Choose a pre-configured demo persona or enter credentials.
              </p>
            </div>

            {/* Role Switcher Segmented Cards */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-300">Access Persona (RBAC)</label>
              <div className="grid grid-cols-3 gap-2">
                {ROLES.map((r) => {
                  const isSelected = selectedRole.role === r.role;
                  const Icon = r.icon;
                  return (
                    <button
                      key={r.role}
                      type="button"
                      onClick={() => handleSelectRole(r)}
                      className={`p-3 rounded-2xl border text-left transition-all duration-200 flex flex-col justify-between relative ${
                        isSelected
                          ? `bg-slate-950 border-blue-500 ring-2 ring-blue-500/30 shadow-lg shadow-blue-500/10`
                          : "bg-slate-950/60 border-slate-800 hover:bg-slate-950 hover:border-slate-700"
                      }`}
                    >
                      {isSelected && (
                        <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                      )}
                      <div className="flex items-center justify-between w-full">
                        <Icon className={`w-4 h-4 ${isSelected ? r.accentColor : "text-slate-400"}`} />
                        {isSelected && <Check className="w-3 h-3 text-blue-400" />}
                      </div>
                      <div className="mt-2.5">
                        <span className="text-xs font-bold text-white block truncate">{r.shortTitle}</span>
                        <span className="text-[10px] text-slate-400 font-mono block">@{r.username}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 1-Click Instant Demo Launch Button */}
            <div className="p-3.5 bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-purple-950/40 border border-blue-500/30 rounded-2xl space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-medium">Quick Evaluator Sign-In:</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${selectedRole.badgeColor}`}>
                  {selectedRole.username}
                </span>
              </div>
              <button
                type="button"
                onClick={() => handleQuickRoleLogin(selectedRole)}
                disabled={loading}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-600/25 transition-all flex items-center justify-center space-x-2 transform active:scale-98 disabled:opacity-50"
              >
                <span>Instant Launch as {selectedRole.title}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Error Notification */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-xs font-medium flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Manual Form Inputs */}
            <form onSubmit={(e) => handleLogin(e)} className="space-y-3.5 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Username</label>
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
                <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
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

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-200 hover:text-white rounded-xl text-xs font-bold transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {loading ? <span>Signing In...</span> : <span>Sign In with Custom Password</span>}
              </button>
            </form>
          </div>

          {/* RBAC Permission Matrix Dropdown */}
          <div className="pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setShowRbacMatrix(!showRbacMatrix)}
              className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <div className="flex items-center space-x-1.5">
                <Info className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-medium">RBAC Security Matrix</span>
              </div>
              <span className="text-[10px] font-mono text-blue-400 flex items-center space-x-1">
                <span>{showRbacMatrix ? "Hide" : "Inspect Matrix"}</span>
                {showRbacMatrix ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </span>
            </button>

            {showRbacMatrix && (
              <div className="mt-3 p-3 bg-slate-950 rounded-2xl border border-slate-800 max-h-48 overflow-y-auto space-y-2">
                <table className="w-full text-left text-[11px]">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                      <th className="pb-1.5">Action</th>
                      <th className="pb-1.5 text-center text-emerald-400">View</th>
                      <th className="pb-1.5 text-center text-blue-400">Ana</th>
                      <th className="pb-1.5 text-center text-purple-400">Adm</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-900 text-slate-300">
                    {RBAC_MATRIX.map((row, idx) => (
                      <tr key={idx}>
                        <td className="py-1.5 font-medium pr-2 truncate max-w-[140px]">{row.permission}</td>
                        <td className="py-1.5 text-center">
                          {row.viewer ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 inline" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-slate-600 inline" />
                          )}
                        </td>
                        <td className="py-1.5 text-center">
                          {row.analyst ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 inline" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-slate-600 inline" />
                          )}
                        </td>
                        <td className="py-1.5 text-center">
                          {row.admin ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 inline" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5 text-slate-600 inline" />
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
    </div>
  );
};
