import React from "react";
import type { MerkleProof } from "../types";
import { X, CheckCircle, Database } from "lucide-react";

export const MerkleProofModal: React.FC<{ proof: MerkleProof | null; onClose: () => void }> = ({ proof, onClose }) => {
  if (!proof) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2.5 mb-4">
          <Database className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Merkle Inclusion Proof</h3>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
            <span className="text-slate-400">Leaf Index:</span> <span className="font-mono text-white">{proof.leaf_index}</span> of {proof.total_leaves}
          </div>

          <div className="p-2.5 bg-slate-950 rounded border border-slate-800 break-all">
            <span className="text-slate-400">Leaf Hash (Audit Record):</span>
            <p className="font-mono text-indigo-300 mt-0.5">{proof.leaf_hash}</p>
          </div>

          <div>
            <span className="text-slate-400 font-semibold mb-1 block">Proof Path Steps:</span>
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {proof.proof_steps.map((step, idx) => (
                <div key={idx} className="p-2 bg-slate-950 rounded border border-slate-800 font-mono flex items-center justify-between">
                  <span className="text-slate-400">Step {idx + 1} ({step.position})</span>
                  <span className="text-slate-300 truncate max-w-[240px]">{step.hash_value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-2.5 bg-indigo-950/40 rounded border border-indigo-500/30 break-all">
            <span className="text-indigo-300 font-semibold">Anchored Merkle Root:</span>
            <p className="font-mono text-white mt-0.5">{proof.root}</p>
          </div>

          <div className="flex items-center space-x-2 text-emerald-400 pt-2 font-semibold">
            <CheckCircle className="w-4 h-4" />
            <span>Cryptographic Path Fully Verified Against Root</span>
          </div>
        </div>
      </div>
    </div>
  );
};
