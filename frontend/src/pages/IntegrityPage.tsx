import React, { useEffect, useState } from "react";
import {
  Database,
  CheckCircle,
  AlertTriangle,
  ShieldCheck,
  Key,
} from "lucide-react";
import { api } from "../api/client";
import type {
  AnchorBatch,
  AuditLedgerEntry,
  IntegrityVerificationReport,
  MerkleProof,
} from "../types";
import { MerkleProofModal } from "../components/MerkleProofModal";

export const IntegrityPage: React.FC = () => {
  const [report, setReport] = useState<IntegrityVerificationReport | null>(null);
  const [entries, setEntries] = useState<AuditLedgerEntry[]>([]);
  const [batches, setBatches] = useState<AnchorBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [anchoring, setAnchoring] = useState(false);
  const [activeProof, setActiveProof] = useState<MerkleProof | null>(null);

  const fetchIntegrityData = async () => {
    setLoading(true);
    try {
      const [rep, entRes, batRes] = await Promise.all([
        api.getIntegrityStatus(),
        api.getLedgerEntries(),
        api.getAnchorBatches(),
      ]);
      setReport(rep);
      setEntries(entRes.items);
      setBatches(batRes.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrityData();
  }, []);

  if (loading && !report && entries.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-400">
        Loading integrity audit ledger...
      </div>
    );
  }

  const handleVerifyNow = async () => {
    setVerifying(true);
    try {
      const res = await api.triggerVerify();
      setReport(res);
    } catch (err: any) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleAnchorNow = async () => {
    setAnchoring(true);
    try {
      await api.anchorNow();
      await fetchIntegrityData();
    } catch (err: any) {
      alert(`Anchoring error: ${err.message}`);
    } finally {
      setAnchoring(false);
    }
  };

  const handleViewProof = async (seq: number) => {
    try {
      const proof = await api.getMerkleProof(seq);
      setActiveProof(proof);
    } catch (err: any) {
      alert(`Merkle proof unavailable: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Blockchain Integrity & Audit Ledger</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Tamper-evident cryptographic hash chains anchored to the Ethereum IntegrityAnchor smart contract
          </p>
        </div>
        <div className="flex items-center space-x-2.5">
          <button
            onClick={handleVerifyNow}
            disabled={verifying}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>{verifying ? "Verifying Ledger..." : "Verify Now"}</span>
          </button>

          <button
            onClick={handleAnchorNow}
            disabled={anchoring}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
          >
            <Database className="w-4 h-4" />
            <span>{anchoring ? "Anchoring..." : "Anchor Batch Now"}</span>
          </button>
        </div>
      </div>

      {/* Verification Status Card */}
      {report && (
        <div className={`border rounded-2xl p-5 backdrop-blur-xl ${
          report.status === "VERIFIED"
            ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
            : report.status === "TAMPERED"
            ? "bg-red-950/30 border-red-500 text-red-300 animate-pulse"
            : "bg-amber-950/20 border-amber-500/30 text-amber-300"
        }`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className={`p-2.5 rounded-xl ${report.status === "VERIFIED" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                {report.status === "VERIFIED" ? <CheckCircle className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Cryptographic Status: {report.status}</h3>
                <p className="text-xs mt-0.5">{report.explanation}</p>
              </div>
            </div>
            <div className="text-right text-xs">
              <span className="text-slate-400">Audited Entries:</span> <span className="font-mono font-bold text-white">{report.total_entries_checked}</span>
              {report.tampered_sequence_number && (
                <div className="text-red-400 font-bold font-mono mt-1">
                  Tamper Point: Sequence #{report.tampered_sequence_number}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Anchor Batches Section */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur-sm space-y-3 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <Database className="w-4 h-4 text-blue-400" />
          <span>On-Chain Merkle Root Anchor Batches</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] font-semibold text-slate-400 uppercase">
                <th className="py-2.5 px-3">Batch ID</th>
                <th className="py-2.5 px-3">Sequence Range</th>
                <th className="py-2.5 px-3">Merkle Root</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">On-Chain Tx Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-500">
                    No on-chain batches anchored yet. Click "Anchor Batch Now" to anchor recent records.
                  </td>
                </tr>
              ) : (
                batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-mono text-slate-300">{b.id.substring(0, 8)}...</td>
                    <td className="py-2.5 px-3 font-mono font-semibold text-white">#{b.from_sequence} - #{b.to_sequence} ({b.entry_count} entries)</td>
                    <td className="py-2.5 px-3 font-mono text-indigo-400 truncate max-w-[180px]">{b.merkle_root}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        {b.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-400 truncate max-w-[200px]">
                      {b.tx_hash ? (
                        <span className="text-blue-400">{b.tx_hash.substring(0, 18)}...</span>
                      ) : (
                        "Local Testnet"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Ledger Hash Chain Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-sm shadow-xl">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Key className="w-4 h-4 text-emerald-400" />
            <span>Audit Ledger (SHA-256 Hash Chain)</span>
          </h3>
          <span className="text-xs text-slate-400 font-mono">{entries.length} Total Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/40 text-[11px] font-semibold text-slate-400 uppercase">
                <th className="py-3 px-4">Seq #</th>
                <th className="py-3 px-4">Entry Type</th>
                <th className="py-3 px-4">Previous Hash</th>
                <th className="py-3 px-4">Entry Hash</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Proof</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {entries.map((e) => (
                <tr key={e.sequence_number} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-bold text-white">#{e.sequence_number}</td>
                  <td className="py-3 px-4 font-sans font-semibold text-blue-400">{e.entry_type}</td>
                  <td className="py-3 px-4 text-slate-500 truncate max-w-[130px]">{e.previous_hash.substring(0, 16)}...</td>
                  <td className="py-3 px-4 text-emerald-400 truncate max-w-[150px]">{e.entry_hash.substring(0, 18)}...</td>
                  <td className="py-3 px-4 text-slate-400 font-sans text-[11px]">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="py-3 px-4 font-sans">
                    {e.anchor_batch_id ? (
                      <button
                        onClick={() => handleViewProof(e.sequence_number)}
                        className="px-2 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 rounded text-[11px] font-semibold transition-colors"
                      >
                        View Merkle Proof
                      </button>
                    ) : (
                      <span className="text-[10px] text-slate-500">Unanchored</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Merkle Proof Modal */}
      <MerkleProofModal proof={activeProof} onClose={() => setActiveProof(null)} />
    </div>
  );
};
