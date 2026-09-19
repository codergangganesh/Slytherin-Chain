import React, { useEffect, useState } from "react";
import { Server, Shield, Globe, Plus, Trash2, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { Asset } from "../types";

export const AssetsPage: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [hostname, setHostname] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [criticality, setCriticality] = useState(3);
  const [isProtected, setIsProtected] = useState(false);
  const [isInternetFacing, setIsInternetFacing] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    try {
      const res = await api.getAssets();
      setAssets(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createAsset({
        hostname,
        ip_address: ipAddress,
        criticality,
        is_protected: isProtected,
        is_internet_facing: isInternetFacing,
        environment: "production",
        owner: "SecOps",
        tags: ["managed-asset"],
      });
      setShowAddModal(false);
      setHostname("");
      setIpAddress("");
      await fetchAssets();
    } catch (err: any) {
      alert(`Error creating asset: ${err.message}`);
    }
  };

  const handleDeleteAsset = async (id: string) => {
    if (!confirm("Are you sure you want to delete this asset?")) return;
    try {
      await api.deleteAsset(id);
      await fetchAssets();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Managed Asset Inventory</h1>
          <p className="text-xs text-slate-400 mt-0.5">Asset posture, criticality weighting, and protection guardrails</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Asset</span>
          </button>
          <button
            onClick={fetchAssets}
            className="p-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-400 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {assets.map((asset) => (
          <div key={asset.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3 relative group">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-slate-800 border border-slate-700 text-blue-400">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">{asset.hostname}</h3>
                  <p className="font-mono text-xs text-slate-400">{asset.ip_address}</p>
                </div>
              </div>
              <button
                onClick={() => handleDeleteAsset(asset.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-opacity"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                asset.criticality >= 4 ? "bg-red-500/20 text-red-400 border-red-500/30" :
                asset.criticality === 3 ? "bg-amber-500/20 text-amber-400 border-amber-500/30" :
                "bg-slate-800 text-slate-400 border-slate-700"
              }`}>
                Criticality {asset.criticality}/5
              </span>

              {asset.is_protected && (
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
                  <Shield className="w-3 h-3" />
                  <span>Protected (Human Approval Req)</span>
                </span>
              )}

              {asset.is_internet_facing && (
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center space-x-1">
                  <Globe className="w-3 h-3" />
                  <span>Internet-Facing</span>
                </span>
              )}
            </div>

            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
              <span>Owner: {asset.owner}</span>
              <span className="uppercase">{asset.environment}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-white mb-4">Add Managed Asset</h3>
            <form onSubmit={handleCreateAsset} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 mb-1 font-semibold">Hostname</label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  placeholder="e.g. app-prod-02.corp"
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-semibold">IP Address</label>
                <input
                  type="text"
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  placeholder="e.g. 10.0.0.50"
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-semibold">Criticality Level (1 to 5)</label>
                <select
                  value={criticality}
                  onChange={(e) => setCriticality(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-white focus:outline-none"
                >
                  <option value={1}>1 - Low / Non-critical</option>
                  <option value={2}>2 - Internal Workstation</option>
                  <option value={3}>3 - Standard Server</option>
                  <option value={4}>4 - Core Application / Gateway</option>
                  <option value={5}>5 - Tier-0 Domain Controller / Database</option>
                </select>
              </div>

              <div className="flex items-center space-x-4 pt-1">
                <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isProtected}
                    onChange={(e) => setIsProtected(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-blue-600 focus:ring-0"
                  />
                  <span>Is Protected Asset</span>
                </label>

                <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isInternetFacing}
                    onChange={(e) => setIsInternetFacing(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-800 text-blue-600 focus:ring-0"
                  />
                  <span>Internet-Facing</span>
                </label>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-semibold transition-colors"
                >
                  Create Asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
