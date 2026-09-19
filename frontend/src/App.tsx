import React, { useEffect, useState } from "react";
import { Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import {
  Shield,
  LayoutDashboard,
  AlertTriangle,
  Server,
  Zap,
  BookOpen,
  Database,
  Play,
  LogOut,
  ShieldAlert,
  ShieldCheck,
  Eye,
} from "lucide-react";
import { DashboardPage } from "./pages/DashboardPage";
import { IncidentQueuePage } from "./pages/IncidentQueuePage";
import { IncidentDetailPage } from "./pages/IncidentDetailPage";
import { AssetsPage } from "./pages/AssetsPage";
import { ResponseActionsPage } from "./pages/ResponseActionsPage";
import { PlaybooksPage } from "./pages/PlaybooksPage";
import { IntegrityPage } from "./pages/IntegrityPage";
import { SimulatorPage } from "./pages/SimulatorPage";
import { LoginPage } from "./pages/LoginPage";
import { AttackSimulatorModal } from "./components/AttackSimulatorModal";
import { api } from "./api/client";
import type { UserProfile } from "./types";

const ROLE_INFO = {
  admin: {
    label: "Administrator",
    icon: ShieldAlert,
    badge: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    avatarBg: "bg-purple-500/10 border-purple-500/30 text-purple-400",
  },
  analyst: {
    label: "SOC Analyst",
    icon: ShieldCheck,
    badge: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    avatarBg: "bg-blue-500/10 border-blue-500/30 text-blue-400",
  },
  viewer: {
    label: "Auditor / Viewer",
    icon: Eye,
    badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    avatarBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
  },
};

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    () => !!localStorage.getItem("sentinel_token")
  );
  const [showSimModal, setShowSimModal] = useState(false);
  const location = useLocation();

  const fetchProfile = async () => {
    try {
      const profile = await api.getMyProfile();
      setUser(profile);
      setIsAuthenticated(true);
    } catch {
      // If token is invalid or expired, clear and prompt login
      localStorage.removeItem("sentinel_token");
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("sentinel_token");
    if (token) {
      fetchProfile();
    } else {
      // Auto-authenticate as admin by default for seamless hackathon onboarding
      api.login("admin", "admin_demo_password")
        .then(() => fetchProfile())
        .catch(() => setIsAuthenticated(false));
    }
  }, []);

  const handleLogout = () => {
    api.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  // If not authenticated, display full modern Login Screen
  if (!isAuthenticated || !user) {
    return <LoginPage onLoginSuccess={fetchProfile} />;
  }

  const roleMeta = ROLE_INFO[user.role as keyof typeof ROLE_INFO] || ROLE_INFO.admin;
  const RoleIcon = roleMeta.icon;

  const navLinks = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/incidents", icon: AlertTriangle, label: "Incidents" },
    { to: "/assets", icon: Server, label: "Assets" },
    { to: "/response-actions", icon: Zap, label: "Response Actions" },
    { to: "/playbooks", icon: BookOpen, label: "Playbooks" },
    { to: "/integrity", icon: Database, label: "Integrity & Chain" },
    { to: "/simulator", icon: Play, label: "Attack Simulator" },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 antialiased overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900/90 border-r border-slate-800/80 flex flex-col justify-between backdrop-blur-xl z-20">
        <div>
          {/* Logo Header */}
          <div className="h-16 flex items-center px-6 border-b border-slate-800/80 space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-md shadow-blue-500/20 text-white">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-sm text-white tracking-wide block">SentinelChain</span>
              <span className="text-[10px] text-blue-400 font-mono font-medium tracking-wider">v0.1.0 MVP</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.to ||
                (item.to !== "/" && location.pathname.startsWith(item.to));
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? "bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Quick Attack Simulator Trigger for Live Pitch */}
          <div className="p-3">
            <button
              onClick={() => setShowSimModal(true)}
              className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-red-600/20 transition-all transform active:scale-95"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Simulate Attack</span>
            </button>
          </div>
        </div>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-950/40">
          {/* Active User Card */}
          <div className="flex items-center space-x-3 px-2">
            <div className={`w-9 h-9 rounded-xl border flex items-center justify-center ${roleMeta.avatarBg}`}>
              <RoleIcon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-bold text-white block truncate">{user.username}</span>
              <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase border inline-block mt-0.5 ${roleMeta.badge}`}>
                {roleMeta.label}
              </span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 py-1.5 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs text-slate-400 hover:text-white transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 overflow-y-auto p-8 relative">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/incidents" element={<IncidentQueuePage />} />
          <Route path="/incidents/:id" element={<IncidentDetailPage />} />
          <Route path="/assets" element={<AssetsPage />} />
          <Route path="/response-actions" element={<ResponseActionsPage />} />
          <Route path="/playbooks" element={<PlaybooksPage />} />
          <Route path="/integrity" element={<IntegrityPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* Attack Simulator Live Launcher Modal */}
      <AttackSimulatorModal
        isOpen={showSimModal}
        onClose={() => setShowSimModal(false)}
      />
    </div>
  );
};

export default App;
