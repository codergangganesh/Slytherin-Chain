# Security Considerations

> **What this covers:** Threat model, known limitations, and production hardening checklist.
> **Who should read it:** Security reviewers, ops teams, and hackathon judges.

*Full security documentation will be added in Phase 9.*

## Threat Model (Summary)

- **Attacker with DB access:** Can modify incident data, but hash chain detects tampering
- **Attacker with app access:** Constrained by RBAC; actions logged to immutable ledger
- **Supply chain attack:** Dependency audit in CI (pip-audit, npm audit)
- **Event injection:** All input validated via Pydantic; event content treated as hostile

## What Blockchain Does and Does Not Protect Against

**Does protect:**
- Retroactive modification of audit trail (detectable via hash chain + on-chain anchor)
- Evidence tampering (SHA-256 verified on download)
- Report modification (report hash stored in ledger)

**Does NOT protect:**
- Authenticity of original event sources (the platform trusts what it receives)
- Real-time attack prevention (blockchain is for post-hoc verification)
- Data availability (if the database is destroyed, the hash chain is lost)
