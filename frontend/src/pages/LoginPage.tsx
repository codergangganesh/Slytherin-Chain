import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Shield, Lock, User as UserIcon } from "lucide-react";
import { api } from "../api/client";

export const LoginPage: React.FC<{ onLoginSuccess: () => void }> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin_demo_password");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.login(username, password);
      onLoginSuccess();
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setLoading(false);
    }
  };

  const selectDemoAccount = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.15),rgba(255,255,255,0))]" />

      <div className="max-w-md w-full relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-xl shadow-blue-500/20 mb-3">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">SentinelChain</h1>
          <p className="text-sm text-slate-400 mt-1">Autonomous Threat Response & Integrity Platform</p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-7 shadow-2xl backdrop-blur-xl">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Username</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium py-2 rounded-lg text-sm transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 mt-2"
            >
              {loading ? "Authenticating..." : "Sign In"}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-800">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2 text-center">
              Quick Demo Logins
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => selectDemoAccount("admin", "admin_demo_password")}
                className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded text-xs text-slate-300 transition-colors"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => selectDemoAccount("analyst", "analyst_demo_password")}
                className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded text-xs text-slate-300 transition-colors"
              >
                Analyst
              </button>
              <button
                type="button"
                onClick={() => selectDemoAccount("viewer", "viewer_demo_password")}
                className="px-2 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded text-xs text-slate-300 transition-colors"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
