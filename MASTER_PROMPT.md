# MASTER PROMPT — Autonomous Response & Incident Management Platform

> **How to use this file**
> 1. Create an empty project folder. Save the `AGENTS.md` file in its root.
> 2. Open the folder in Antigravity. Use **Planning mode** with review before execution.
> 3. Paste everything between **PROMPT START** and **PROMPT END** as your first message.
> 4. Read the `implementation_plan.md` the agent produces and approve it before it writes code.
> 5. Work phase by phase (Section 16). Do not let the agent skip ahead.
>
> The project name **SentinelChain** is a placeholder. Rename it to whatever your team likes.

---

## PROMPT START

# 1. Role and objective

You are a senior security engineer and software architect. Build **SentinelChain**, a
production-quality, hackathon-demoable platform for **Autonomous Response & Incident
Management**.

The platform must:

1. **Automatically respond to detected threats** by blocking, isolating, or restricting suspicious
   activity, under strict safety guardrails.
2. **Prioritize incidents** using threat severity, affected assets, and potential impact.
3. **Maintain incident history** and track investigation, response, and resolution activities.
4. **Generate structured incident reports** containing threat details, attack sequence, impact,
   evidence, and response actions.
5. **Use blockchain for one specific purpose:** a tamper-evident integrity layer. Hashes of
   audit-trail entries are chained together, batched into Merkle roots, and anchored on a
   blockchain so that any later modification of incident history, evidence, or reports is
   detectable.

Read `AGENTS.md` first. Follow it in every task. Code quality, readable file names, tests, and a
clear README are hard requirements, not nice-to-haves.

# 2. Design decisions you must respect (and why)

- **Blockchain is not the database and not the response engine.** Detection and response must
  run in milliseconds to seconds, and smart contracts cannot call firewalls. Blockchain only
  stores a small hash/root per batch. Raw incident data never goes on-chain (privacy, cost,
  erasure rights).
- **Response never waits for the chain.** If the blockchain is slow or unreachable, anchoring is
  queued and retried. Incident handling continues normally.
- **Safe by default.** Autonomous blocking can cause outages if it is wrong. All actions go through
  guardrails (Section 8.6). Real enforcement is OFF by default. Simulated connectors are the
  default so the demo is safe and repeatable.
- **Explainable decisions.** Every risk score and every automated action stores *why* it happened.
- **Simple infrastructure.** Use PostgreSQL + Redis + MinIO. Do not add Kafka, Kubernetes,
  Elasticsearch, or Temporal in the MVP. Document them in `docs/future-work.md` as the scale-up
  path.

# 3. Working method (follow strictly)

1. Read `AGENTS.md`.
2. Produce `implementation_plan.md` covering all phases in Section 16. Wait for approval.
3. Create `task.md` as a checklist. Update it as you go.
4. Implement **one phase at a time**. At the end of each phase:
   - run linters, type checks, and tests, and fix all failures;
   - verify the phase's acceptance criteria (Section 16);
   - add a `walkthrough.md` entry: what was built, how to run it, how it was verified, known
     limitations;
   - stop and report before starting the next phase.
5. Before using any library or SDK feature, check its current official documentation. Do not
   rely on memory for APIs. Use the latest stable versions and pin exact versions in lock files.
6. If something is ambiguous, ask. Do not guess.

Priority tags used below: **[MUST]** = required for the demo, **[SHOULD]** = do if time permits,
**[STRETCH]** = only after everything else is done and polished.

# 4. Scope

## 4.1 In scope

| Capability | Priority |
|---|---|
| Event ingestion API + normalization + Redis Streams pipeline | MUST |
| Detection engine with YAML rules mapped to MITRE ATT&CK | MUST |
| Threat-intel enrichment with offline fallback | MUST |
| Explainable risk scoring and priority (P1–P4) | MUST |
| Alert correlation into incidents + incident lifecycle | MUST |
| Autonomous response engine with guardrails, approval flow, TTL, rollback | MUST |
| Full incident timeline / history | MUST |
| Structured incident reports (JSON + PDF + Markdown) | MUST |
| Blockchain integrity layer (hash chain, Merkle batches, on-chain anchor, verification UI) | MUST |
| Web dashboard (React) | MUST |
| Attack simulator with scripted scenarios | MUST |
| Auth with roles (viewer / analyst / admin) | MUST |
| Asset inventory with criticality | MUST |
| Docker Compose one-command startup | MUST |
| Tests + CI pipeline | MUST |
| README + `docs/` | MUST |
| Live WebSocket/SSE updates on dashboard | SHOULD |
| Optional LLM-written executive summary (provider-agnostic, off by default) | SHOULD |
| Notification webhook (Slack/Teams/email mock) | SHOULD |
| Wazuh alert JSON adapter | STRETCH |
| Real Linux `nftables` enforcement connector (behind flag) | STRETCH |
| STIX 2.1 export of incidents | STRETCH |
| On-chain Merkle proof verification (Solidity) | STRETCH |

## 4.2 Non-goals (do not build)

- A full SIEM, EDR agent, or log-collection agent.
- Machine-learning detection models. (Rule-based detection is enough and more explainable.)
- Storing incident data on the blockchain.
- Mainnet deployment or anything involving real funds.
- Multi-tenant SaaS features.

# 5. Architecture

```
 ┌──────────────┐   ┌────────────┐
 │ Simulator /  │   │ Real logs  │  (Wazuh adapter = STRETCH)
 │ scenarios    │   │ via HTTP   │
 └──────┬───────┘   └─────┬──────┘
        └────────┬────────┘
                 ▼
        POST /api/v1/events  (API key)
                 │
        ┌────────▼─────────┐
        │ Event normalizer │  → normalized event schema
        └────────┬─────────┘
                 ▼
        Redis Stream: events.normalized
                 │
        ┌────────▼─────────┐        ┌──────────────────┐
        │ Detection engine │◄───────│ YAML rule files  │
        └────────┬─────────┘        └──────────────────┘
                 ▼  alerts
        ┌──────────────────┐        ┌──────────────────┐
        │ Enrichment       │◄───────│ Threat intel     │
        │ (intel + asset)  │        │ (offline + API)  │
        └────────┬─────────┘        └──────────────────┘
                 ▼
        ┌──────────────────┐
        │ Risk scoring +   │
        │ correlation      │──► Incident (status, priority, score)
        └────────┬─────────┘
                 ▼
        ┌──────────────────┐        ┌──────────────────┐
        │ Response engine  │◄───────│ YAML playbooks   │
        │ policy+guardrails│        └──────────────────┘
        └───┬──────────┬───┘
   auto     │          │ needs approval
            ▼          ▼
     ┌───────────┐  ┌────────────────────┐
     │ Connector │  │ Analyst approves   │
     │ (simulated│  │ in dashboard       │
     │ firewall) │  └────────────────────┘
     └─────┬─────┘
           ▼
   Every step appends to ──► Audit ledger (hash chain) in PostgreSQL
                                     │
                          every N minutes / on incident close
                                     ▼
                       Merkle root of new entries
                                     ▼
                     IntegrityAnchor smart contract
                     (local Anvil in dev, Sepolia testnet in demo)

 Storage:  PostgreSQL (data + ledger)   Redis (streams, cache)   MinIO (evidence, reports)
 Frontend: React dashboard  ⇄  FastAPI REST + WebSocket
```

# 6. Technology stack

| Layer | Choice | Reason |
|---|---|---|
| Backend language | Python 3.12+ | Best ecosystem for security tooling |
| API framework | FastAPI + Pydantic v2 | Typed, fast, auto OpenAPI docs |
| ORM / migrations | SQLAlchemy 2.0 + Alembic | Standard, explicit, migration-safe |
| Database | PostgreSQL (JSONB + GIN indexes for event search) | Reliable; avoids running a search cluster |
| Queue / event bus | Redis Streams with consumer groups | Simple, durable enough, easy demo |
| Object storage | MinIO (S3-compatible) | Evidence and reports, hash-verified |
| Settings | pydantic-settings | Typed env config |
| Logging | structlog | Structured JSON logs with correlation IDs |
| Auth | JWT + Argon2 password hashing, RBAC | Simple and secure; Keycloak = future work |
| Reports | Jinja2 + WeasyPrint (PDF), Markdown, JSON | Structured and printable |
| Contracts | Solidity + Foundry (forge, anvil) | Fast tests, local chain for dev |
| Chain client | web3.py | Python-native anchoring worker |
| Chain (dev) | Local Anvil container | Free, instant, deterministic |
| Chain (demo) | Ethereum Sepolia testnet (Polygon Amoy is an acceptable alternative) | Public, verifiable on a block explorer, free test tokens |
| Frontend | React + TypeScript + Vite + Tailwind CSS | Fast to build, clean UI |
| Frontend data | TanStack Query, Recharts, React Router | Standard, minimal |
| Testing | pytest, pytest-asyncio, Foundry tests, Vitest, Playwright (smoke) | Full-stack coverage |
| Quality | ruff, mypy (strict), eslint, prettier, pre-commit | Consistent code |
| CI | GitHub Actions | Lint + type check + test on every push |
| Packaging | Docker + Docker Compose | One-command startup on any OS |

# 7. Repository structure (create exactly this, adjust only with a reason)

```
sentinelchain/
├── README.md
├── AGENTS.md
├── LICENSE
├── Makefile                          # convenience shortcuts; README also lists raw commands
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
│
├── docs/
│   ├── architecture.md               # diagrams + component responsibilities
│   ├── blockchain-integrity.md       # exactly what is hashed, chained, anchored, verified
│   ├── detection-rules-guide.md      # how to write a rule
│   ├── response-playbook-guide.md    # how to write a playbook + guardrail reference
│   ├── risk-scoring.md               # formula, weights, worked examples
│   ├── api-reference.md              # endpoint summary (OpenAPI is source of truth)
│   ├── security-considerations.md    # threat model + known limitations
│   ├── demo-script.md                # 5-minute demo walkthrough
│   ├── future-work.md                # Kafka, Keycloak, EDR agents, mainnet, etc.
│   └── images/
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── migrations/
│   ├── rules/                        # detection rules (YAML)
│   │   ├── ssh_brute_force.yaml
│   │   ├── brute_force_then_success.yaml
│   │   ├── port_scan.yaml
│   │   ├── suspicious_powershell.yaml
│   │   ├── mass_file_encryption.yaml
│   │   ├── large_outbound_transfer.yaml
│   │   └── web_injection_attempt.yaml
│   ├── playbooks/                    # response policies (YAML)
│   │   ├── brute_force_playbook.yaml
│   │   ├── malware_playbook.yaml
│   │   ├── ransomware_playbook.yaml
│   │   └── data_exfiltration_playbook.yaml
│   ├── data/
│   │   └── offline_threat_intel.json # seed reputation data so demo works without internet
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory + router registration
│   │   ├── config/
│   │   │   ├── settings.py
│   │   │   └── logging_config.py
│   │   ├── domain/                   # pure business objects and rules
│   │   │   ├── enums.py
│   │   │   ├── exceptions.py
│   │   │   ├── normalized_event.py
│   │   │   ├── alert.py
│   │   │   ├── incident.py
│   │   │   ├── asset.py
│   │   │   ├── response_action.py
│   │   │   ├── risk_score.py
│   │   │   └── incident_state_machine.py
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── event_normalizer.py
│   │   │   │   └── event_publisher.py
│   │   │   ├── detection/
│   │   │   │   ├── rule_loader.py
│   │   │   │   ├── rule_evaluator.py
│   │   │   │   ├── sliding_window_counter.py
│   │   │   │   └── detection_service.py
│   │   │   ├── enrichment/
│   │   │   │   ├── threat_intel_service.py
│   │   │   │   └── asset_context_service.py
│   │   │   ├── risk_scoring_service.py
│   │   │   ├── incident_correlation_service.py
│   │   │   ├── incident_lifecycle_service.py
│   │   │   ├── response/
│   │   │   │   ├── playbook_loader.py
│   │   │   │   ├── response_policy_engine.py
│   │   │   │   ├── guardrail_checker.py
│   │   │   │   ├── response_orchestrator.py
│   │   │   │   └── action_expiry_service.py
│   │   │   ├── integrity/
│   │   │   │   ├── canonical_json.py
│   │   │   │   ├── hash_chain_ledger.py
│   │   │   │   ├── merkle_tree.py
│   │   │   │   ├── anchor_batch_service.py
│   │   │   │   └── integrity_verification_service.py
│   │   │   ├── reporting/
│   │   │   │   ├── incident_report_builder.py
│   │   │   │   ├── report_renderers.py
│   │   │   │   └── executive_summary_generator.py
│   │   │   └── evidence_storage_service.py
│   │   ├── adapters/
│   │   │   ├── enforcement/
│   │   │   │   ├── enforcement_connector.py       # abstract interface
│   │   │   │   ├── simulated_firewall_connector.py
│   │   │   │   ├── simulated_identity_connector.py
│   │   │   │   └── linux_nftables_connector.py    # STRETCH, disabled by default
│   │   │   ├── threat_intel/
│   │   │   │   ├── offline_intel_provider.py
│   │   │   │   └── abuseipdb_provider.py          # optional, needs API key
│   │   │   ├── blockchain/
│   │   │   │   ├── anchor_chain_client.py         # web3.py wrapper
│   │   │   │   └── integrity_anchor_abi.json
│   │   │   ├── notifications/
│   │   │   │   └── webhook_notifier.py
│   │   │   └── object_storage/
│   │   │       └── minio_object_store.py
│   │   ├── repositories/             # one file per aggregate; all SQL lives here
│   │   │   ├── event_repository.py
│   │   │   ├── alert_repository.py
│   │   │   ├── incident_repository.py
│   │   │   ├── asset_repository.py
│   │   │   ├── response_action_repository.py
│   │   │   ├── audit_ledger_repository.py
│   │   │   ├── anchor_batch_repository.py
│   │   │   └── user_repository.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── orm_models.py
│   │   ├── api/
│   │   │   ├── dependencies.py       # auth, RBAC, db session, current user
│   │   │   ├── schemas/              # request/response models, one file per resource
│   │   │   └── routers/
│   │   │       ├── auth_router.py
│   │   │       ├── events_router.py
│   │   │       ├── incidents_router.py
│   │   │       ├── assets_router.py
│   │   │       ├── response_actions_router.py
│   │   │       ├── integrity_router.py
│   │   │       ├── reports_router.py
│   │   │       ├── dashboard_router.py
│   │   │       ├── settings_router.py
│   │   │       └── simulator_router.py
│   │   └── workers/
│   │       ├── detection_worker.py           # consumes events.normalized
│   │       ├── response_worker.py            # executes approved/auto actions
│   │       ├── anchor_worker.py              # periodic Merkle anchoring + retries
│   │       └── action_expiry_worker.py       # auto-expires TTL blocks
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
│
├── contracts/
│   ├── foundry.toml
│   ├── src/IntegrityAnchor.sol
│   ├── test/IntegrityAnchor.t.sol
│   └── script/DeployIntegrityAnchor.s.sol
│
├── simulator/
│   ├── run_scenario.py               # CLI: python run_scenario.py ssh_brute_force_compromise
│   ├── event_factory.py
│   └── scenarios/
│       ├── ssh_brute_force_compromise.py
│       ├── port_scan_recon.py
│       ├── ransomware_activity.py
│       ├── benign_admin_scan_false_positive.py
│       └── protected_asset_attack.py
│
├── scripts/
│   ├── seed_demo_data.py
│   ├── verify_integrity_cli.py       # independent verifier (does not use app code paths)
│   └── simulate_tampering.py         # edits a DB row to demo detection
│
└── frontend/
    ├── package.json
    ├── Dockerfile
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── api/                      # typed API client, one file per resource
        ├── types/
        ├── hooks/
        ├── components/               # shared UI: SeverityBadge.tsx, RiskGauge.tsx, ...
        └── pages/
            ├── LoginPage.tsx
            ├── DashboardPage.tsx
            ├── IncidentQueuePage.tsx
            ├── IncidentDetailPage.tsx
            ├── AssetsPage.tsx
            ├── ResponseActionsPage.tsx
            ├── PlaybooksPage.tsx
            ├── IntegrityPage.tsx
            └── SimulatorPage.tsx
```

# 8. Detailed module specifications

## 8.1 Normalized event schema

All incoming data is converted to this shape (inspired by Elastic Common Schema):

```json
{
  "event_id": "uuid",
  "occurred_at": "ISO-8601 UTC",
  "ingested_at": "ISO-8601 UTC",
  "source": "ssh | firewall | endpoint | web | cloud | simulator",
  "event_type": "login_failed | login_success | port_connection | process_started | file_modified | outbound_transfer | http_request | user_created",
  "host": "hostname or null",
  "username": "string or null",
  "src_ip": "string or null",
  "dst_ip": "string or null",
  "dst_port": "int or null",
  "process_name": "string or null",
  "command_line": "string or null",
  "file_path": "string or null",
  "file_hash_sha256": "string or null",
  "bytes_out": "int or null",
  "http_path": "string or null",
  "severity_hint": "int 0-10 or null",
  "raw": { "original": "payload" }
}
```

Ingestion endpoint accepts single events and batches (max 500). It authenticates with an
**API key** (hashed in DB), validates with Pydantic, normalizes, stores in `events`, and
publishes to the `events.normalized` Redis Stream. It returns quickly (target: p95 under 100 ms
for a single event) and never runs detection inline.

## 8.2 Detection engine [MUST]

- A `detection_worker` reads the stream through a consumer group (at-least-once delivery, so
  detection must be idempotent using `event_id`).
- Rules are YAML files loaded at startup and validated with Pydantic. Invalid rules stop startup
  with a clear message.
- Rule types:
  - `match`: field conditions (equals, in, regex, contains).
  - `threshold`: count of matching events per `group_by` field within a `window_seconds`.
  - `distinct_count`: number of distinct values of a field per group within a window
    (for port scans).
  - `sequence`: event A followed by event B for the same key within a window
    (for brute force followed by success).
- Sliding window state lives in Redis (sorted sets) so multiple workers share it.
- Example rule:

```yaml
id: SSH-BRUTE-001
title: SSH brute force attempt
description: Many failed SSH logins from one source IP in a short window.
type: threshold
severity: 0.6            # 0.0–1.0, feeds risk scoring
confidence: 0.7          # 0.0–1.0, how sure this rule is
match:
  event_type: login_failed
  source: ssh
group_by: src_ip
threshold: 10
window_seconds: 120
mitre:
  tactic: Credential Access
  technique_id: T1110
  technique_name: Brute Force
playbook_category: brute_force
suppress_for_seconds: 300   # do not re-alert on the same group inside this window
```

- Ship these rules **[MUST]**: SSH brute force (T1110), brute force followed by success
  (T1110 → T1078), port scan (T1046), suspicious encoded PowerShell (T1059.001), mass file
  encryption/rename (T1486), large outbound transfer to rare destination (T1041), web injection
  attempt (T1190).
- Alerts store: rule id, title, severity, confidence, MITRE mapping, matched event IDs, and the
  `group_by` key.

## 8.3 Enrichment [MUST]

- **Threat intel:** look up source IPs and file hashes. Use `offline_intel_provider` (reads
  `data/offline_threat_intel.json`) by default so the demo works with no internet or API keys.
  Optionally use AbuseIPDB when `ABUSEIPDB_API_KEY` is set. Cache results in Redis with a TTL.
  Returns a reputation score 0.0–1.0 and tags (e.g. `known-scanner`, `tor-exit`).
- **Asset context:** look up the target host in the `assets` table for criticality (1–5),
  environment, internet-facing flag, and protected flag. Unknown hosts get a conservative
  default (criticality 3) and are flagged `unknown_asset`.

## 8.4 Risk scoring and prioritization [MUST]

Implement as a **pure function** in `risk_scoring_service.py` so it is easy to test.

```
risk_score = 100 × clamp(
    W_SEVERITY   × severity            # from rule, 0–1
  + W_CONFIDENCE × confidence          # from rule, adjusted by correlation, 0–1
  + W_ASSET      × (asset_criticality / 5)
  + W_EXPOSURE   × exposure            # 1.0 internet-facing, 0.5 internal, 0.2 isolated segment
  + W_INTEL      × intel_reputation    # 0–1 from enrichment
  + CORRELATION_BONUS                  # +0.05 per additional distinct alert, max +0.15
, 0, 1)
```

Default weights (in `config`, not hard-coded): severity 0.30, confidence 0.20, asset 0.25,
exposure 0.10, intel 0.15.

Priority mapping: **P1** ≥ 80, **P2** 60–79, **P3** 40–59, **P4** < 40.

Every score stores a `risk_breakdown` JSON listing each factor, its input value, weight, and
contribution, so the UI can show "why this is P1". Document the formula with two worked examples
in `docs/risk-scoring.md`. Unit tests must cover boundaries (79.9 vs 80.0) and clamping.

## 8.5 Incident correlation and lifecycle [MUST]

- **Correlation:** alerts with the same primary key (source IP, or target host, or username)
  within a correlation window (default 30 minutes) attach to one open incident. Otherwise a new
  incident is created. Adding an alert re-scores the incident and appends a timeline entry.
- **Incident reference IDs:** human-friendly, e.g. `INC-2026-0001`.
- **State machine** (enforced in `incident_state_machine.py`; illegal transitions raise a domain
  exception):

```
NEW → TRIAGED → CONTAINED → INVESTIGATING → RESOLVED → CLOSED
 │        │           ▲
 │        └──► AWAITING_APPROVAL ──┘
 └──► FALSE_POSITIVE  (from NEW, TRIAGED, or INVESTIGATING; analyst or admin only)
```

  Automatic transitions: `NEW → TRIAGED` once scored; `TRIAGED → CONTAINED` after a successful
  containment action; `TRIAGED → AWAITING_APPROVAL` when a required action needs a human.
  Manual transitions require the analyst role, a required note, and are recorded in the ledger.
- **Timeline:** every event, alert, score change, action, approval, note, transition, and report
  generation is a timeline entry. The timeline is the incident history.

## 8.6 Autonomous response engine with guardrails [MUST]

### Playbooks

YAML files map a `playbook_category` to actions and conditions:

```yaml
id: BRUTE-FORCE-PLAYBOOK
applies_to_category: brute_force
autonomy_mode_required: auto          # auto | approval_required | recommend_only
conditions:
  min_risk_score: 60
  min_confidence: 0.7
actions:
  - action_type: block_ip
    target: incident.primary_src_ip
    ttl_seconds: 3600                 # auto-expire after 1 hour
    requires_approval_if:
      asset_criticality_at_least: 5
  - action_type: restrict_access       # e.g. force MFA / rate-limit the targeted account
    target: incident.primary_username
    ttl_seconds: 1800
  - action_type: notify
    channel: webhook
```

### Supported actions

| Action | Effect (simulated by default) | Reversible |
|---|---|---|
| `block_ip` | Add IP to simulated firewall blocklist with TTL | Yes |
| `isolate_host` | Mark host quarantined in the simulated network | Yes |
| `disable_user` | Disable account in simulated identity provider | Yes |
| `restrict_access` | Apply rate-limit / require-MFA flag | Yes |
| `notify` | Send webhook notification | No |

Each action implements a common interface: `validate()`, `dry_run()`, `execute()`, `rollback()`.
Connectors are behind the `EnforcementConnector` interface. Default: simulated connectors that
write to the database (visible in the UI). The real Linux `nftables` connector is a STRETCH item
and only loads if `ENABLE_REAL_ENFORCEMENT=true`.

### Guardrails (all must pass before ANY automatic execution; implement in `guardrail_checker.py`)

1. **Autonomy mode switch** (admin-controlled, stored in `system_settings`):
   `off` (nothing runs), `recommend_only` (proposes actions, human executes),
   `approval_required` (human approves everything), `auto` (auto-run when all guardrails pass).
2. **Allowlist:** never act on allowlisted IPs/CIDRs (gateways, the platform's own IP, admin
   jump hosts, DNS servers). Loaded from config.
3. **Protected assets:** assets flagged `is_protected` never get `isolate_host` or `disable_user`
   automatically. They always require human approval.
4. **Confidence and score thresholds** from the playbook.
5. **High-impact actions need approval:** `isolate_host` on criticality ≥ 4, `disable_user` on
   privileged accounts, or any action whose playbook rule says so.
6. **Blast-radius rate limit:** max N automatic actions per hour globally and per target type
   (defaults in config). Exceeding it flips the system to `approval_required` and raises an alert.
7. **Idempotency:** each action has an idempotency key (incident + type + target). Duplicates are
   ignored and logged.
8. **TTL and auto-expiry:** all blocks/restrictions expire unless extended by a human. An
   `action_expiry_worker` rolls them back and logs it.
9. **Dry-run mode:** any action can be simulated, showing exactly what would happen without doing
   it.
10. **Manual rollback:** an analyst can roll back any reversible action from the UI, with a
    required reason.
11. **Every decision is recorded:** allowed or denied, with the specific guardrail that decided,
    written to the timeline and ledger. A *denied* action is as important to record as an
    executed one.

### Action lifecycle

`PROPOSED → (AWAITING_APPROVAL →) APPROVED → EXECUTING → SUCCEEDED | FAILED`, then possibly
`ROLLED_BACK` or `EXPIRED`. Failures retry with exponential backoff (max 3 attempts), then mark
`FAILED` and notify.

## 8.7 Evidence handling [MUST]

- Evidence items (event bundles as JSON, sample log extracts, optional uploaded files) are stored
  in MinIO. The SHA-256 hash, size, collector, and timestamp are stored in `evidence_items`.
- When evidence is added, an `EVIDENCE_ADDED` ledger entry containing the hash is appended
  (so evidence tampering is detectable).
- Downloading evidence re-verifies the hash and reports a mismatch loudly.

## 8.8 Blockchain integrity layer [MUST]

This is the differentiator. Implement it precisely and document it in
`docs/blockchain-integrity.md`.

**A. Audit ledger (hash chain in PostgreSQL)**
- Table `audit_ledger_entries`: `sequence_number` (bigserial), `entry_type`, `incident_id`
  (nullable), `payload` (JSONB), `created_at`, `previous_hash`, `entry_hash`,
  `anchor_batch_id` (nullable).
- `entry_hash = SHA256( canonical_json(entry_type, incident_id, payload, created_at,
  sequence_number) || previous_hash )`. Genesis `previous_hash` is 64 zeros.
- `canonical_json.py` produces deterministic output: sorted keys, no extra whitespace, UTF-8,
  fixed timestamp format. This is the most critical function; test it heavily.
- Append happens in a database transaction with row locking on the latest entry, so concurrent
  workers cannot fork the chain.
- Add a PostgreSQL trigger that blocks `UPDATE` and `DELETE` on the hashed columns (only
  `anchor_batch_id` may be set once). This gives defense in depth, and the hash chain still
  detects tampering by anyone who bypasses the trigger.
- What gets a ledger entry: incident created, alert attached, score changed, state transition,
  action proposed/approved/denied/executed/failed/rolled back/expired, note added, evidence
  added, report generated (with the report file's SHA-256), autonomy-mode changes.

**B. Merkle batching**
- `merkle_tree.py`: leaves are `entry_hash` values. Use domain separation (prefix `0x00` for
  leaves, `0x01` for internal nodes) and promote odd nodes instead of duplicating them.
  Support generating and verifying an inclusion proof for one entry.
- `anchor_worker` runs every `ANCHOR_INTERVAL_SECONDS` (default 300) and also when a P1/P2
  incident is closed. It takes all entries with no `anchor_batch_id`, builds the tree, and
  records an `anchor_batches` row (`from_seq`, `to_seq`, `merkle_root`, status `PENDING`).

**C. Smart contract (`contracts/src/IntegrityAnchor.sol`)**
- Solidity, latest stable compiler, minimal and audited-style clean code.
- Functions/events:
  - `anchorRoot(bytes32 merkleRoot, uint64 fromSequence, uint64 toSequence)` restricted to
    authorized anchorers, emits `RootAnchored(batchId, merkleRoot, fromSequence, toSequence,
    timestamp)`.
  - `getBatch(batchId)` view returning the stored data.
  - Owner-managed anchorer allowlist (`addAnchorer`, `removeAnchorer`), using a standard,
    well-known access-control pattern. Do not invent custom cryptography.
  - Reject overlapping or non-increasing sequence ranges.
- Foundry tests: successful anchor, unauthorized caller reverts, overlapping range reverts,
  event emission, getter correctness.
- Deploy script for local Anvil and for Sepolia.

**D. Chain client (`anchor_chain_client.py`)**
- Uses web3.py. Config: `ANCHOR_CHAIN_RPC_URL`, `ANCHOR_CHAIN_ID`,
  `ANCHOR_CONTRACT_ADDRESS`, `ANCHOR_WALLET_PRIVATE_KEY` (testnet-only key from env, never
  committed).
- Submits the transaction, waits for the configured confirmations, records `tx_hash`,
  `block_number`, status `CONFIRMED`. On failure: status `FAILED`, retry with backoff, and
  **never** block incident handling.
- Health check endpoint shows chain connectivity and pending-anchor backlog.

**E. Verification**
- `integrity_verification_service.py` performs three checks:
  1. **Chain check:** re-walk the ledger and recompute every `entry_hash`. Report the first
     broken sequence number.
  2. **Batch check:** rebuild each Merkle root from the ledger and compare with the stored root.
  3. **On-chain check:** read the root from the smart contract and compare with the recomputed
     root.
- Result states: `VERIFIED`, `TAMPERED` (with the exact location), `PENDING_ANCHOR` (recent
  entries not yet anchored), `CHAIN_UNAVAILABLE`.
- Endpoints for whole-ledger verification, per-incident verification, and per-entry Merkle proof.
- `scripts/verify_integrity_cli.py` is an **independent verifier**. It reads the database and
  chain directly using its own small implementation and does not import application code. This
  proves the check does not just trust the app.
- `scripts/simulate_tampering.py` edits a stored timeline payload directly in the database
  (bypassing the app) so the demo can show `TAMPERED` appearing in the UI.
- The UI shows an integrity badge on each incident and a dedicated Integrity page with the
  ledger, batches, transaction links to the block explorer, and a "Verify now" button.

## 8.9 Reporting [MUST]

`incident_report_builder.py` assembles a versioned, structured report object
(`schema_version` field). `report_renderers.py` renders it to **JSON**, **Markdown**, and
**PDF** (Jinja2 template + WeasyPrint). Sections:

1. **Executive summary** (template-based by default; optional LLM summary behind
   `ENABLE_LLM_SUMMARY=false`, provider-agnostic interface, must fall back to the template on any
   error, and must never receive secrets)
2. **Incident metadata:** ID, title, priority, risk score, status, assignee, first/last seen,
   duration
3. **Threat details:** rules fired, MITRE tactics/techniques, indicators of compromise (IPs,
   hashes, usernames), threat-intel reputation
4. **Attack sequence:** ordered timeline table (time, event/alert, description, MITRE tag)
5. **Affected assets and impact:** asset list with criticality, environment, exposure, and a
   plain-language business impact statement derived from criticality and exposure
6. **Evidence:** list with SHA-256 hashes and collection times
7. **Response actions:** what was done, when, by whom (system/user), guardrail decisions, result,
   rollback/expiry status
8. **Resolution and recommendations:** resolution notes, recommended follow-ups (rule-based
   templates per playbook category)
9. **Integrity attestation:** ledger sequence range, chain head hash, Merkle root, transaction
   hash, block number, verification status at generation time

The generated report file's SHA-256 is written to the ledger as `REPORT_GENERATED`, so the
report itself becomes tamper-evident once anchored.

## 8.10 Authentication and authorization [MUST]

- Users with roles: `viewer` (read only), `analyst` (approve/deny actions, change incident
  state, add notes, roll back), `admin` (everything plus autonomy mode, assets, users).
- JWT access tokens (short-lived) with refresh flow; Argon2 password hashing.
- Ingestion uses separate hashed API keys, not user JWTs.
- Apply RBAC through FastAPI dependencies. Add tests proving each role can and cannot do what is
  expected.
- Seed demo users via `scripts/seed_demo_data.py` (demo passwords only in the seed script and
  README, flagged clearly as demo-only).

## 8.11 Attack simulator [MUST]

CLI and API-triggered scenarios that post realistic event streams:

1. `ssh_brute_force_compromise`: many failed logins, then a success, then a new admin user, then
   large outbound transfer. Should create one P1 incident with a multi-step attack sequence.
2. `port_scan_recon`: sequential port connections from one IP. Should create a P3/P2 incident.
3. `ransomware_activity`: suspicious process followed by mass file modifications on a
   high-criticality host. Should require approval for host isolation.
4. `benign_admin_scan_false_positive`: scan from an allowlisted admin IP. Guardrails must
   **deny** the action, and the denial must be visible in the timeline.
5. `protected_asset_attack`: attack against a protected asset. Must go to `AWAITING_APPROVAL`.

Scenarios accept a speed multiplier so the demo can run in about 30 seconds.

## 8.12 Observability [SHOULD]

- `/health` (liveness) and `/ready` (DB, Redis, MinIO, chain status).
- Prometheus metrics endpoint: events ingested, alerts raised, incidents by priority, actions by
  status, guardrail denials, anchoring latency, anchor backlog.
- Correlation ID propagated from ingestion through alert, incident, and action logs.

# 9. Database schema (Alembic migrations; use these table names)

`users`, `api_keys`, `assets`, `events`, `alerts`, `incidents`, `incident_alerts`,
`evidence_items`, `response_actions`, `blocklist_entries` (simulated firewall state),
`quarantined_hosts`, `disabled_users` (simulated identity state), `audit_ledger_entries`,
`anchor_batches`, `reports`, `system_settings`.

Requirements: foreign keys, sensible indexes (events by `occurred_at`, `src_ip`, `host`; GIN on
JSONB search fields), timestamps in UTC, and a documented data-retention note for `events`
(`docs/security-considerations.md`).

# 10. REST API (versioned under `/api/v1`)

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Events | `POST /events`, `POST /events/batch`, `GET /events` (filters) |
| Incidents | `GET /incidents` (filter/sort by priority, status), `GET /incidents/{id}`, `GET /incidents/{id}/timeline`, `POST /incidents/{id}/notes`, `POST /incidents/{id}/transition`, `GET /incidents/{id}/evidence`, `POST /incidents/{id}/evidence` |
| Response | `GET /response-actions`, `POST /response-actions/{id}/approve`, `POST /response-actions/{id}/deny`, `POST /response-actions/{id}/rollback`, `POST /response-actions/{id}/dry-run` |
| Assets | CRUD on `/assets` |
| Integrity | `GET /integrity/status`, `POST /integrity/verify`, `GET /integrity/incidents/{id}`, `GET /integrity/entries/{sequence}/proof`, `GET /integrity/batches` |
| Reports | `POST /incidents/{id}/reports` (`format=json|md|pdf`), `GET /reports/{id}/download` |
| Dashboard | `GET /dashboard/summary`, `GET /dashboard/trends` |
| Settings | `GET/PUT /settings/autonomy-mode` (admin), `GET /settings/playbooks` |
| Simulator | `GET /simulator/scenarios`, `POST /simulator/scenarios/{name}/run` (admin/analyst) |
| Live | `WS /ws/live` (or SSE) for new incidents, actions, and integrity status |

Use consistent error format `{ "error": { "code": "...", "message": "..." } }`, pagination on
list endpoints, and rate limiting on auth and ingestion routes. OpenAPI docs must be accurate.

# 11. Frontend (React + TypeScript)

Design for a clear, professional security-operations look with a dark theme option. Pages:

- **Dashboard:** KPI cards (open incidents, P1 count, mean time to contain, actions taken today,
  integrity status), incidents-over-time chart, priority distribution chart, live incident feed,
  autonomy mode indicator.
- **Incident Queue:** sortable, filterable table ordered by priority then risk score, with
  status badges and age.
- **Incident Detail** (the hero page): summary header; risk gauge with factor breakdown ("why
  this is P1"); attack-sequence timeline with MITRE tags; response actions panel with
  Approve / Deny / Dry-run / Roll back buttons and guardrail explanations; evidence list with
  hash-verified badges; notes; integrity badge; "Generate report" (PDF/MD/JSON).
- **Assets:** inventory with criticality, protected flag, and internet-facing flag.
- **Response Actions:** global log with filters, including guardrail-denied actions.
- **Playbooks:** read-only view of loaded playbooks and rules, and the admin autonomy-mode
  toggle with a confirmation dialog.
- **Integrity:** ledger table, anchor batches with block explorer links, "Verify now", and
  per-entry Merkle proof viewer.
- **Simulator:** buttons to launch each scenario with a speed control.

UI quality requirements: loading and empty states everywhere, error boundaries, responsive down
to tablet width, accessible colors/contrast (severity is not conveyed by color alone),
escaping of all event-derived text, and no business logic in components (use hooks and the API
client).

# 12. Security requirements

- Treat all event content as hostile. Escape in UI, PDF, and Markdown output. Never build shell
  commands from event data.
- Secrets only via environment variables. `.env` is git-ignored; `.env.example` documents all.
- CORS restricted to configured origins. Security headers set. Request size limits on ingestion.
- Dependency audit in CI (`pip-audit`, `npm audit`) as a non-blocking report.
- Write `docs/security-considerations.md` with: a short threat model (what an attacker could do
  to this platform), what the blockchain layer does and does not protect against, known
  limitations (for example: hash chain proves tamper-evidence, not authenticity of the original
  event source), and the production hardening checklist.

# 13. Testing and CI

- **Unit tests:** risk scoring (boundaries, clamping, worked examples), rule evaluation for every
  rule type, state machine (legal and illegal transitions), each guardrail individually,
  canonical JSON determinism, hash chain (append, tamper detection), Merkle tree (roots, proofs,
  odd leaf counts, single leaf).
- **Integration tests** (Docker Compose test profile): full pipeline from ingested events to
  incident to action to ledger; RBAC per role; anchoring against local Anvil; tamper detection
  end to end; report generation and hash recorded in the ledger.
- **Contract tests:** Foundry, as specified in 8.8.
- **Frontend tests:** Vitest for hooks/components; one Playwright smoke test that logs in, runs a
  simulator scenario, and opens the incident.
- **Scenario tests:** each simulator scenario asserts its expected incident priority and action
  outcome, including the guardrail-denial and approval cases.
- **CI (`.github/workflows/ci.yml`):** ruff, mypy strict, pytest with coverage report, forge
  test, eslint, tsc, Vitest, and a Docker build check. CI must pass on a fresh clone.

# 14. Developer experience

- `docker compose up --build` starts Postgres, Redis, MinIO, Anvil, the backend API, all
  workers, and the frontend. The contract is auto-deployed to Anvil on startup and its address is
  written to the backend configuration.
- `Makefile` shortcuts (`make up`, `make down`, `make seed`, `make test`, `make lint`,
  `make demo`), but the README must also list the plain commands so Windows users without `make`
  are not blocked.
- `.env.example` fully commented. `pre-commit` config with ruff, mypy, prettier, eslint.
- Seed script creates demo users, assets (including a protected asset and an allowlisted admin
  IP), and threat-intel data.

# 15. Documentation and README requirements

The root `README.md` must be clear enough that a stranger can run the project in 5 minutes and
understand it in 2. Required sections, in this order:

1. **Title, one-line pitch, status badges** (CI, license)
2. **The problem:** why manual incident response is too slow and why the audit trail must be
   trustworthy
3. **What it does:** the four core capabilities plus the integrity layer, each in one or two
   sentences
4. **Screenshots / GIF** of the dashboard, incident detail, and integrity verification
   (placeholders with instructions if images are not yet captured)
5. **Architecture:** Mermaid diagram plus a short data-flow description
6. **How and why blockchain is used:** what is anchored, what is not, and why this design is
   better than putting everything on-chain (be honest and precise; this is what impresses
   judges)
7. **Safety design:** guardrails summary (autonomy modes, allowlist, protected assets, TTL,
   rollback, approval)
8. **Tech stack** table
9. **Quick start:** prerequisites, `cp .env.example .env`, `docker compose up --build`,
   seeding, URLs and demo logins
10. **Run the demo:** step-by-step (launch a scenario, watch the incident, approve an action,
    generate a report, tamper with the DB, see the verification fail)
11. **Configuration reference:** table of all environment variables with defaults and
    descriptions
12. **Project structure:** annotated tree (top two levels)
13. **API overview** and link to `/docs` (OpenAPI)
14. **Testing:** how to run each test suite
15. **Security notes and limitations** (link to `docs/security-considerations.md`)
16. **Roadmap** (link to `docs/future-work.md`)
17. **Contributing, license, team**

Also produce all `docs/` files listed in Section 7. Each doc starts with a short "what this
covers and who should read it" line.

# 16. Phased execution plan (with acceptance criteria)

Implement in this order. Stop after each phase, verify, and report.

**Phase 0 — Foundation**
Repo scaffold exactly as in Section 7, `AGENTS.md` respected, Docker Compose with all services,
`.env.example`, CI skeleton, pre-commit, health endpoints, empty frontend shell, Foundry project.
*Accept when:* `docker compose up --build` starts everything; `/health` and `/ready` return OK;
CI passes on the empty skeleton.

**Phase 1 — Data model, auth, assets**
Domain models, ORM, Alembic migrations, users/roles/JWT/RBAC, API keys, asset CRUD, seed script.
*Accept when:* migrations apply cleanly on a fresh DB; RBAC tests pass for all three roles; assets
can be created via API and UI stub.

**Phase 2 — Ingestion pipeline**
Event schema, normalizer, ingestion endpoints, Redis Stream publisher, event storage, simulator
CLI skeleton with one scenario.
*Accept when:* a scenario posts events, they are stored normalized, and appear in the stream;
invalid payloads are rejected with clear errors.

**Phase 3 — Detection**
Rule loader/validator, all four rule types, all seven shipped rules, Redis sliding windows,
detection worker, alert storage, suppression.
*Accept when:* each rule triggers on its scenario and stays silent on benign traffic; detection
is idempotent on redelivered events.

**Phase 4 — Enrichment, scoring, incidents**
Threat intel (offline + optional API), asset context, risk scoring with breakdown, correlation,
incident state machine, timeline.
*Accept when:* the brute-force scenario yields one correlated P1 incident with a readable risk
breakdown and complete timeline; state-machine and scoring tests pass.

**Phase 5 — Response engine**
Playbook loader, policy engine, all guardrails, connectors (simulated), approval flow, dry-run,
rollback, TTL expiry, retries, response worker.
*Accept when:* auto-block works and expires; the false-positive scenario is denied by the
allowlist with the denial in the timeline; the protected-asset and ransomware scenarios wait for
approval; rollback works; the blast-radius limit trips correctly.

**Phase 6 — Blockchain integrity**
Canonical JSON, hash chain, DB immutability trigger, Merkle tree, `IntegrityAnchor` contract with
Foundry tests, chain client, anchor worker, verification service, independent CLI verifier,
tamper script.
*Accept when:* entries are anchored on Anvil; verification returns `VERIFIED`; after running
`simulate_tampering.py`, verification returns `TAMPERED` pointing to the exact sequence number,
in both the app and the independent CLI; chain outage does not affect incident handling.

**Phase 7 — Reporting and evidence**
Evidence storage with hash verification, report builder, JSON/Markdown/PDF renderers, template
executive summary (LLM optional), report hash written to the ledger.
*Accept when:* a generated PDF for the brute-force incident contains all nine sections and the
integrity attestation.

**Phase 8 — Frontend**
All pages in Section 11 connected to the real API, live updates, polished states.
*Accept when:* the full demo (Section 17) can be run only through the browser.

**Phase 9 — Hardening and documentation**
Coverage targets met, security review against Section 12, metrics, `docs/` complete, final
README, demo script rehearsed, seed data reset command.
*Accept when:* a fresh clone follows the README and reaches a working demo with no
undocumented steps; CI green; coverage targets met.

# 17. Target demo (design everything to make this work smoothly, about 5 minutes)

1. Open the dashboard: quiet, integrity status green, autonomy mode `auto`.
2. Run `ssh_brute_force_compromise` from the Simulator page.
3. Watch a P1 incident appear live. Open it: attack timeline with MITRE tags, risk breakdown,
   the automatic IP block with its TTL and the guardrail decisions shown.
4. Run `benign_admin_scan_false_positive`: show that the allowlist guardrail **denied** the
   block and recorded why.
5. Run `ransomware_activity`: show the host isolation waiting for approval; approve it as an
   analyst; then roll something back to show reversibility.
6. Generate the PDF incident report and show the integrity attestation section.
7. Open the Integrity page: show anchored batches and the transaction on the block explorer
   (Sepolia) or the local chain.
8. Run `simulate_tampering.py` to alter a past timeline entry directly in the database, click
   "Verify now", and show `TAMPERED` with the exact entry. Then show the independent CLI
   verifier agreeing.

# 18. Definition of done

- All **[MUST]** items work end to end and the demo in Section 17 runs reliably from a fresh
  clone.
- Lint, type checks, and all test suites pass locally and in CI; coverage targets from
  `AGENTS.md` are met.
- No secrets in the repository; safe mode is the default; testnet/local chain only.
- The README and `docs/` are complete, accurate, and match the code.
- File and folder names are descriptive and follow `AGENTS.md`; no forbidden names.
- `walkthrough.md` documents each phase, and `docs/future-work.md` lists everything deferred.

# 19. Things you must not do

- Do not put raw incident data, logs, or personal data on the blockchain.
- Do not make any response action depend on blockchain confirmation.
- Do not enable real enforcement by default or execute shell commands built from event data.
- Do not use mainnet, real funds, or real private keys.
- Do not add technologies beyond Section 6 without asking.
- Do not skip tests or docs to move faster. Do not mark a phase done until its acceptance
  criteria pass.
- Do not silently expand or shrink scope. Ask, or record it in `docs/future-work.md`.

## PROMPT END
