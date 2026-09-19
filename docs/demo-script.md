# 5-Minute Hackathon Demo Script

> **What this covers:** A step-by-step 5-minute live demonstration of SentinelChain.  
> **Who should read it:** Presenters, hackathon judges, and evaluators.

---

## Demo Steps (Total Time: ~5 minutes)

### Step 1: Dashboard & System Posture (0:00 - 0:45)
1. Open the web dashboard at `http://localhost:5173`.
2. Point out:
   - Clean SecOps KPI cards (0 open incidents, 0 P1s, Integrity status: `VERIFIED`).
   - Autonomy mode badge showing `AUTO`.
   - Explain the 3-tier integrity architecture: blockchain is used exclusively for tamper-evident anchoring, never for high-latency response actions.

### Step 2: SSH Brute Force & Autonomous Response (0:45 - 2:00)
1. Navigate to **Attack Simulator** (`/simulator`).
2. Launch `ssh_brute_force_compromise` at $2\times$ speed.
3. Switch to **Incidents** (`/incidents`) and open the newly created **P1 Incident**.
4. Show the **Risk Score Gauge** with factor breakdown ("why this is P1": severity, threat intel reputation, internet exposure).
5. Show the **Attack Sequence Timeline** with MITRE ATT&CK tags (T1110 $\rightarrow$ T1078 $\rightarrow$ T1041).
6. Show the **Response Actions Panel**:
   - The IP `198.51.100.42` was automatically blocked with a 3600s TTL.
   - Expand the **Guardrail Decisions** list to show all safety checks that passed.
7. Click **Generate Report** $\rightarrow$ download the PDF report with its cryptographic integrity attestation.

### Step 3: False Positive & Allowlist Guardrail Denial (2:00 - 3:00)
1. Go back to **Attack Simulator** and launch `benign_admin_scan_false_positive`.
2. Open the generated incident.
3. Point out that the automated IP block was **DENIED** because the target IP (`10.0.0.1`) is protected under the trusted IP allowlist.
4. Highlight that the denial was recorded in the incident timeline and hashed into the cryptographic audit ledger.

### Step 4: Ransomware on High-Criticality Asset & Approval Flow (3:00 - 4:00)
1. Launch `ransomware_activity` against the Tier-0 database (`db-cluster-01.corp`).
2. Open the incident:
   - Notice the status is `AWAITING_APPROVAL`.
   - Because `db-cluster-01.corp` has Criticality 5, the high-impact host isolation action required human sign-off.
3. Click **Approve** as the analyst $\rightarrow$ status changes to `CONTAINED`.
4. Click **Roll Back Action** to demonstrate reversibility and safe recovery.

### Step 5: Cryptographic Tampering & Independent Verification (4:00 - 5:00)
1. Navigate to **Integrity & Chain** (`/integrity`).
2. Show the on-chain Merkle root batches and click **View Merkle Proof** for an entry.
3. Run the tampering simulation tool in terminal:
   ```bash
   python -m scripts.simulate_tampering
   ```
4. Click **Verify Now** in the UI:
   - Status immediately flips to **`TAMPERED`** (highlighting the exact sequence number that was modified).
5. Run the independent CLI verifier:
   ```bash
   python -m scripts.verify_integrity_cli
   ```
   - Show the CLI independently detecting the broken hash chain and proving that the platform is completely tamper-evident.
