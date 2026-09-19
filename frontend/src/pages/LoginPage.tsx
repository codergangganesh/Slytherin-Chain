import React, { useState } from "react";
import {
  Shield,
  Lock,
  User as UserIcon,
  ShieldCheck,
  ShieldAlert,
  Eye,
  KeyRound,
  CheckCircle2,
  XCircle,
  Activity,
  Zap,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "../api/client";
import socHeroImg from "../assets/soc_command_center.jpg";

interface LoginPageProps {
  onLoginSuccess: () => void;
}

interface RolePersona {
  role: "admin" | "analyst" | "viewer";
  title: string;
  username: string;
  defaultPass: string;
  badge: string;
  icon: React.ElementType;
}

const ROLES: RolePersona[] = [
  {
    role: "admin",
    title: "Admin",
    username: "admin",
    defaultPass: "admin_demo_password",
    badge: "Full Privilege",
    icon: ShieldAlert,
  },
  {
    role: "analyst",
    title: "Analyst",
    username: "analyst",
    defaultPass: "analyst_demo_password",
    badge: "SOC Operations",
    icon: ShieldCheck,
  },
  {
    role: "viewer",
    title: "Viewer",
    username: "viewer",
    defaultPass: "viewer_demo_password",
    badge: "Auditor",
    icon: Eye,
  },
];

const RBAC_MATRIX = [
  { permission: "View Dashboard, Incidents & Realtime Telemetry", viewer: true, analyst: true, admin: true },
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
  const [showRbacModal, setShowRbacModal] = useState(false);

  const handleSelectRole = (r: RolePersona) => {
    setSelectedRole(r);
    setUsername(r.username);
    setPassword(r.defaultPass);
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
      setError(err.message || "Authentication failed. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLaunch = (r: RolePersona) => {
    handleSelectRole(r);
    handleLogin(undefined, r.username, r.defaultPass);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 sm:p-6 md:p-8 relative overflow-x-hidden font-sans">
      {/* Ambient background styling */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(245,158,11,0.08),rgba(15,23,42,0.8))]" />

      {/* Floating Modern Container (Card Layout matching user reference image) */}
      <div className="max-w-5xl w-full bg-slate-950/95 border border-slate-800/90 rounded-[36px] shadow-2xl p-4 sm:p-5 grid grid-cols-1 lg:grid-cols-12 gap-5 relative z-10 backdrop-blur-2xl">
        
        {/* ========================================================================= */}
        {/* LEFT COLUMN (5.5 / 12 Cols): Form, Brand Pill, Role Selector & Inputs    */}
        {/* ========================================================================= */}
        <div className="lg:col-span-5 flex flex-col justify-between p-5 sm:p-7 bg-gradient-to-b from-slate-900/90 via-slate-900/60 to-amber-950/20 rounded-[28px] border border-slate-800/80 shadow-inner">
          
          <div className="space-y-6">
            {/* Top Brand Pill Button (Matching "Crextio" pill in reference) */}
            <div className="flex items-center justify-between">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/70 text-slate-200 text-xs font-bold tracking-wide shadow-sm">
                <Shield className="w-4 h-4 text-amber-400" />
                <span>SentinelChain</span>
              </div>
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">v1.0 SOC</span>
            </div>

            {/* Header Title & Subtitle */}
            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Sign in to Command</h1>
              <p className="text-xs text-slate-400">
                Autonomous threat defense & verifiable blockchain integrity.
              </p>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-300 text-xs font-medium flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Form Inputs (Floating Clean Style) */}
            <form onSubmit={(e) => handleLogin(e)} className="space-y-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 ml-1">
                  Identity / Username
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Username or role ID"
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-2xl pl-11 pr-4 py-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500/30 transition-all font-medium shadow-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 mb-1.5 ml-1">
                  Access Key / Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full bg-slate-950/90 border border-slate-800 rounded-2xl pl-11 pr-11 py-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500/30 transition-all font-medium shadow-sm"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3 text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    <KeyRound className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Main Submit Button (Yellow/Gold Rounded Pill like Reference Image) */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-amber-400 via-amber-500 to-yellow-500 hover:from-amber-300 hover:to-yellow-400 text-slate-950 font-bold rounded-2xl text-xs tracking-wide shadow-lg shadow-amber-500/20 transition-all transform active:scale-98 disabled:opacity-50 mt-2 flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <span>Authenticating JWT...</span>
                ) : (
                  <span>Sign In as {selectedRole.title}</span>
                )}
              </button>
            </form>

            {/* Quick Persona Pills (Styled like Apple / Google buttons in reference) */}
            <div className="space-y-2 pt-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block text-center">
                Quick Demo Personas (RBAC)
              </span>
              <div className="grid grid-cols-3 gap-2">
                {ROLES.map((r) => {
                  const isSelected = selectedRole.role === r.role;
                  const Icon = r.icon;
                  return (
                    <button
                      key={r.role}
                      type="button"
                      onClick={() => handleQuickLaunch(r)}
                      className={`py-2 px-3 rounded-2xl border text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all ${
                        isSelected
                          ? "bg-amber-500/10 border-amber-500/50 text-amber-300 shadow-sm"
                          : "bg-slate-950/60 hover:bg-slate-800/60 border-slate-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{r.title}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Footer Terms & Matrix Link (Matching reference image bottom links) */}
          <div className="pt-4 mt-4 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
            <span>
              Protected by <span className="text-slate-400 font-medium">Argon2 + Ed25519</span>
            </span>
            <button
              type="button"
              onClick={() => setShowRbacModal(!showRbacModal)}
              className="text-amber-400 hover:text-amber-300 font-semibold underline transition-colors"
            >
              {showRbacModal ? "Hide Matrix" : "RBAC Permissions"}
            </button>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN (6.5 / 12 Cols): Image Hero Card with Floating Widgets     */}
        {/* ========================================================================= */}
        <div className="lg:col-span-7 relative rounded-[28px] overflow-hidden min-h-[440px] lg:min-h-full flex flex-col justify-between p-6 shadow-2xl border border-slate-800/80 bg-slate-950">
          
          {/* Background Hero Image */}
          <img
            src={socHeroImg}
            alt="SentinelChain High-Tech SOC Command Center"
            className="absolute inset-0 w-full h-full object-cover object-center opacity-70 filter contrast-105"
          />

          {/* Dark Overlay Gradient for High Contrast Glassmorphic Cards */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-slate-950/60 pointer-events-none" />

          {/* TOP FLOATING WIDGET (Yellow/Amber Card like "First Session with Team" in reference) */}
          <div className="relative z-10 flex items-start justify-between">
            <div className="p-3.5 bg-amber-500/90 text-slate-950 rounded-2xl shadow-xl backdrop-blur-md max-w-xs space-y-1">
              <div className="flex items-center space-x-1.5 text-xs font-bold">
                <Activity className="w-3.5 h-3.5" />
                <span>Autonomous Threat Containment</span>
              </div>
              <p className="text-[11px] font-medium leading-tight text-slate-900">
                1.8s Mean Execution Latency • 11 Deterministic Safety Guardrails
              </p>
            </div>

            {/* Floating Role Avatar Badges */}
            <div className="flex -space-x-2 p-1.5 bg-slate-900/80 border border-slate-700/60 rounded-full backdrop-blur-md shadow-lg">
              <div className="w-7 h-7 rounded-full bg-purple-600/80 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white" title="Admin">
                AD
              </div>
              <div className="w-7 h-7 rounded-full bg-blue-600/80 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white" title="SOC Analyst">
                AN
              </div>
              <div className="w-7 h-7 rounded-full bg-emerald-600/80 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white" title="Auditor">
                AU
              </div>
            </div>
          </div>

          {/* MIDDLE FLOATING GLASSMORPHIC WIDGET (Like the calendar strip in reference) */}
          <div className="relative z-10 self-center w-full max-w-md my-auto">
            <div className="p-3.5 bg-slate-900/85 border border-white/10 rounded-2xl backdrop-blur-xl shadow-2xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-white flex items-center space-x-1.5">
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  <span>Deterministic Guardrail Checks</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full font-bold">
                  100% Passed
                </span>
              </div>

              {/* Guardrail Check Pill Grid */}
              <div className="grid grid-cols-4 gap-1.5 text-[10px] text-center font-mono">
                <div className="p-1.5 bg-slate-950/70 rounded-xl border border-slate-800 text-slate-300">
                  <span className="text-slate-500 block text-[8px]">ALLOWLIST</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
                <div className="p-1.5 bg-slate-950/70 rounded-xl border border-slate-800 text-slate-300">
                  <span className="text-slate-500 block text-[8px]">BLAST CAP</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
                <div className="p-1.5 bg-slate-950/70 rounded-xl border border-slate-800 text-slate-300">
                  <span className="text-slate-500 block text-[8px]">IDEMPOTENCY</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
                <div className="p-1.5 bg-slate-950/70 rounded-xl border border-slate-800 text-slate-300">
                  <span className="text-slate-500 block text-[8px]">CANARY</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
              </div>
            </div>
          </div>

          {/* BOTTOM FLOATING WHITE/LIGHT CARD (Like the Meeting card in reference) */}
          <div className="relative z-10 p-4 bg-slate-900/90 border border-slate-700/80 rounded-2xl backdrop-blur-xl shadow-2xl flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-bold text-white">EVM Blockchain Anchor Verified</span>
              </div>
              <p className="text-[10px] font-mono text-slate-400">
                Merkle Root: <span className="text-amber-400">0x9f4a...e3b1</span> • Foundry AnchorRegistry.sol
              </p>
            </div>

            <div className="px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl text-[10px] font-bold tracking-wider uppercase">
              Immutable
            </div>
          </div>
        </div>

      </div>

      {/* RBAC Permission Matrix Modal Drawer (if toggled) */}
      {showRbacModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-2xl w-full shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <Info className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">SentinelChain RBAC Permission Matrix</h3>
              </div>
              <button
                onClick={() => setShowRbacModal(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                ✕
              </button>
            </div>

            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                  <th className="pb-2">Capability / Operation</th>
                  <th className="pb-2 text-center text-emerald-400">Viewer</th>
                  <th className="pb-2 text-center text-blue-400">Analyst</th>
                  <th className="pb-2 text-center text-purple-400">Admin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {RBAC_MATRIX.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-2.5 font-medium">{row.permission}</td>
                    <td className="py-2.5 text-center">
                      {row.viewer ? <CheckCircle2 className="w-4 h-4 text-emerald-400 inline" /> : <XCircle className="w-4 h-4 text-slate-600 inline" />}
                    </td>
                    <td className="py-2.5 text-center">
                      {row.analyst ? <CheckCircle2 className="w-4 h-4 text-blue-400 inline" /> : <XCircle className="w-4 h-4 text-slate-600 inline" />}
                    </td>
                    <td className="py-2.5 text-center">
                      {row.admin ? <CheckCircle2 className="w-4 h-4 text-purple-400 inline" /> : <XCircle className="w-4 h-4 text-slate-600 inline" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
