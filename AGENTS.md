# AGENTS.md — Standing Rules for Every Agent in This Repository

These rules apply to every task and every phase. If a task prompt conflicts with this file,
stop and ask before deviating.

## 1. Project in one paragraph

**SentinelChain** (working name) is an autonomous threat-response and incident-management
platform. It ingests security events, detects threats, scores and prioritizes incidents, takes
safe automated response actions (block / isolate / restrict) under strict guardrails, keeps a
complete incident history, generates structured incident reports, and anchors tamper-evident
integrity proofs of its audit trail on a blockchain.

**Blockchain is used ONLY for integrity anchoring** (hashes / Merkle roots). It is never used for
detection, response execution, or data storage. Response actions must never wait on the blockchain.

## 2. Code quality rules (non-negotiable)

1. **Layered architecture.** Dependencies flow one way:
   `api → services → domain ← repositories / adapters`.
   - `domain/` holds pure business objects and rules. No framework or database imports there.
   - `services/` holds use-case logic. It calls repositories and adapters through interfaces.
   - `api/` only parses requests, calls one service, and shapes responses. No business logic.
2. **One responsibility per file.** A file is normally under 300 lines. A function is normally
   under 40 lines. Split when larger.
3. **Descriptive names. No abbreviations** unless universal (`id`, `ip`, `url`, `api`).
4. **Forbidden file names:** `utils.py`, `helpers.py`, `misc.py`, `common.py`, `stuff.py`,
   `temp.py`, `new_file.py`, `test2.py`. Name files after what they do.
5. **Type everything.** Python: full type hints, `mypy --strict` passes. TypeScript:
   `strict: true`, no `any`.
6. **No magic numbers or strings.** Thresholds, weights, time windows, and TTLs live in
   configuration files or `enums.py` / `constants` modules with a comment explaining them.
7. **Explicit errors.** Define custom exceptions in `domain/exceptions.py`. Never use bare
   `except:`. Never swallow errors silently. Return clear, safe error messages to API clients.
8. **Docstrings** on every public class and function: what it does, arguments, return value,
   and raised exceptions. Add comments only to explain *why*, not *what*.
9. **Structured logging** (`structlog` in Python). Every log line carries a correlation ID.
   Never log secrets, passwords, tokens, or full raw payloads.
10. **Configuration through environment variables** (`pydantic-settings`). Provide a fully
    documented `.env.example`. No secrets in code, tests, or git history.
11. **No dead code, no commented-out code, no unused imports.** Linters must pass clean.
12. **Pure functions where possible** (risk scoring, hashing, Merkle tree, rule matching) so they
    are trivially unit-testable.

## 3. Naming conventions

| Thing | Convention | Good example | Bad example |
|---|---|---|---|
| Python files/modules | `snake_case`, purpose-describing | `risk_scoring_service.py` | `scoring.py`, `rs.py` |
| Python classes | `PascalCase` | `HashChainLedger` | `ledger_class` |
| Python functions/vars | `snake_case`, verb for functions | `calculate_risk_score()` | `calc()`, `doIt()` |
| React components | `PascalCase`, file = component | `IncidentTimeline.tsx` | `timeline.tsx` |
| TS functions/vars | `camelCase` | `fetchIncidentById` | `get_inc` |
| API routes | plural nouns, kebab-case | `/api/v1/response-actions` | `/api/getActions` |
| DB tables | plural `snake_case` | `response_actions` | `RA` |
| Env vars | `UPPER_SNAKE_CASE`, prefixed by area | `ANCHOR_CHAIN_RPC_URL` | `RPC` |
| Git commits | Conventional Commits | `feat(response): add rollback for block_ip` | `update` |

## 4. Testing rules

- Every new service or pure function ships with unit tests in the same change.
- Test names describe behavior: `test_blocklist_rejects_protected_asset`.
- Core domain logic (scoring, guardrails, hash chain, Merkle tree, rule engine) targets **≥ 85%**
  coverage. The whole backend targets **≥ 75%**.
- Tests must be deterministic: no real network calls, no real clocks (inject a clock), seeded
  randomness.
- Smart contracts have Foundry tests covering success, access control, and revert cases.

## 5. Security rules

- Default to **safe mode**: real enforcement on the host or network is OFF unless
  `ENABLE_REAL_ENFORCEMENT=true` is set explicitly. Default connectors are simulated.
- Blockchain work uses **testnet or local chain only**. Never use or ask for a mainnet key.
  Never commit private keys.
- Validate all inputs with Pydantic / Zod. Use parameterized queries only (SQLAlchemy).
- Passwords hashed with Argon2. JWTs short-lived. Role checks (RBAC) on every write endpoint.
- Every autonomous action must pass the guardrail checks in the master prompt before execution.
- Treat every ingested event as untrusted input: escape it in the UI and reports, never
  execute it, never interpolate it into shell commands.

## 6. Workflow rules for the agent

1. **Plan before coding.** For each phase, first produce or update `implementation_plan.md`
   and `task.md`. Then implement.
2. **Small, verified steps.** After each meaningful change, run linters and tests. Fix failures
   before moving on.
3. **Do not invent APIs.** Before using any library, framework, or SDK feature, check its
   current official documentation. Pin exact versions in lock files.
4. **Ask when ambiguous.** If a requirement is unclear or two requirements conflict, ask
   instead of guessing.
5. **Finish each phase with a `walkthrough.md` entry:** what was built, how to run it, how it
   was verified, and any known limitations.
6. **Keep docs in sync.** When behavior, configuration, or structure changes, update `README.md`
   and the relevant file in `docs/` in the same change.
7. **Never expand scope silently.** Anything not in the master prompt goes into a
   `docs/future-work.md` list, not into the code.
