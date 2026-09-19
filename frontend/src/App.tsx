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
  User as UserIcon,
} from "lucide-react";
import { DashboardPage } from "./pages/DashboardPage";
import { IncidentQueuePage } from "./pages/IncidentQueuePage";
import { IncidentDetailPage } from "./pages/IncidentDetailPage";
import { AssetsPage } from "./pages/AssetsPage";
import { ResponseActionsPage } from "./pages/ResponseActionsPage";
import { PlaybooksPage } from "./pages/PlaybooksPage";
import { IntegrityPage } from "./pages/IntegrityPage";
import { SimulatorPage } from "./pages/SimulatorPage";
import { api } from "./api/client";
import type { UserProfile } from "./types";

const DEFAULT_USER: UserProfile = {
  id: "656d3c54-cddc-42b8-ba5b-40a9d3b4cb9f",
  username: "admin",
  email: "admin@sentinelchain.io",
  role: "admin",
  is_active: true,
  created_at: new Date().toISOString(),
};

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile>(DEFAULT_USER);
  const location = useLocation();

  useEffect(() => {
    const autoAuth = async () => {
      try {
        const token = localStorage.getItem("sentinel_token");
        if (!token) {
          await api.login("admin", "admin_demo_password");
        }
        const profile = await api.getMyProfile();
        setUser(profile);
      } catch {
        // Fallback to default admin profile
        setUser(DEFAULT_USER);
      }
    };
    autoAuth();
  }, []);

  const handleLogout = () => {
    // Reset/switch demo profile
    localStorage.removeItem("sentinel_token");
    setUser(DEFAULT_USER);
  };

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
              const isActive = location.pathname === item.to || (item.to !== "/" && location.pathname.startsWith(item.to));
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
        </div>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-slate-800/80 space-y-3">
          <div className="flex items-center space-x-3 px-2">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
              <UserIcon className="w-4 h-4" />
            </div>
            <div className="flex-1 truncate">
              <span className="text-xs font-semibold text-white block truncate">{user?.username}</span>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">{user?.role}</span>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 py-1.5 px-3 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs text-slate-400 hover:text-white transition-colors"
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
    </div>
  );
};

export default App;
