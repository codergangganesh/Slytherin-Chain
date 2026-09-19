# Security Policy

## 1. Scope & Philosophy

**SentinelChain** is engineered as a zero-trust, autonomous security operations and incident response platform. Because autonomous systems make critical containment decisions, safety, integrity, and fault tolerance are treated as non-negotiable architectural requirements.

### Core Security Guarantees
1. **Safe-Mode by Default**: Real system/network enforcement is disabled (`ENABLE_REAL_ENFORCEMENT=false`) out-of-the-box. Simulated connectors execute safely unless explicitly configured for production environments.
2. **Deterministic Safety Guardrails**: Every autonomous containment action is gated by **11 deterministic guardrails** (e.g., CIDR allowlists, blast radius limits, action rate limits, cooldowns, and mandatory role approvals).
3. **Decoupled Asynchronous Blockchain Integrity**: Blockchain anchoring is used strictly for non-repudiation and cryptographic integrity proofs of the audit hash chain. Detection, triage, and response execution **never wait** on on-chain transactions.
4. **Untrusted Ingestion Boundary**: All incoming events and raw payloads are treated as untrusted data. They are parsed through strict Pydantic schemas, sanitized, and escaped before rendering in UI or generating PDF reports.

---

## 2. Supported Versions

Security updates and patches are actively maintained for the following versions:

| Version | Supported |
| :--- | :--- |
| `0.1.x` (Current Main) | :white_check_mark: |
| `< 0.1.0` | :x: |

---

## 3. Reporting a Vulnerability

We take the security of SentinelChain seriously. If you discover a security vulnerability, please disclose it responsibly:

1. **Email Disclosures**: Send vulnerability details to `security@sentinelchain.local` or open a private security advisory on GitHub.
2. **Details to Include**:
   - Component affected (`backend`, `frontend`, `smart-contracts`, or `ingestion pipeline`).
   - Detailed proof of concept (PoC) or reproduction steps.
   - Potential impact and severity assessment (CVSS v3.1 score if applicable).
3. **Response Timeline**:
   - Initial acknowledgement: **Within 24 hours**.
   - Assessment and triage: **Within 48 hours**.
   - Remediation / Patch deployment: **Within 7 business days**.

---

## 4. Role-Based Access Control (RBAC) Matrix

| Endpoint Group | Viewer | Operator | Analyst | Admin |
| :--- | :---: | :---: | :---: | :---: |
| `GET /api/v1/incidents` | :white_check_mark: | :white_check_mark: | :white_check_mark: | :white_check_mark: |
| `POST /api/v1/incidents/{id}/transition` | :x: | :x: | :white_check_mark: | :white_check_mark: |
| `POST /api/v1/response-actions/{id}/approve` | :x: | :x: | :white_check_mark: | :white_check_mark: |
| `POST /api/v1/response-actions/{id}/deny` | :x: | :x: | :white_check_mark: | :white_check_mark: |
| `POST /api/v1/response-actions/{id}/rollback` | :x: | :x: | :white_check_mark: | :white_check_mark: |
| `PATCH /api/v1/settings` | :x: | :x: | :x: | :white_check_mark: |
| `POST /api/v1/auth/users` | :x: | :x: | :x: | :white_check_mark: |

---

## 5. Secret Handling & Cryptographic Standards
* **Password Hashing**: Argon2id (`argon2-cffi`) with secure memory and iteration parameters.
* **Authentication**: Short-lived JWT tokens (HS256) with correlation ID tracking across micro-tasks.
* **Audit Trail**: SHA-256 linear hash-chain ledger with SHA-256 Merkle tree batching anchored to Solidity smart contracts (`IntegrityAnchor.sol`).
