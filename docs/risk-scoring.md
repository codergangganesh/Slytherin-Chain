# Explainable Risk Scoring & Prioritization

> **What this covers:** The risk scoring formula, factor weights, clamping, and worked examples.  
> **Who should read it:** Security analysts evaluating incident priority and developers extending scoring logic.

---

## 1. The Pure Scoring Formula

SentinelChain calculates incident risk using a pure, deterministic function:

$$\text{risk\_score} = 100 \times \text{clamp}\left( W_{\text{sev}} \cdot S + W_{\text{conf}} \cdot C + W_{\text{asset}} \cdot \left(\frac{A}{5}\right) + W_{\text{exp}} \cdot E + W_{\text{intel}} \cdot I + B_{\text{corr}},\, 0,\, 1 \right)$$

### Factor Breakdown & Default Weights
| Factor | Symbol | Default Weight | Value Range | Description |
|---|---|---|---|---|
| **Threat Severity** | $S$ | $0.30$ | $0.0 - 1.0$ | Defined in the triggering detection rule |
| **Detection Confidence** | $C$ | $0.20$ | $0.0 - 1.0$ | Probability rule is a true positive |
| **Asset Criticality** | $A$ | $0.25$ | $1 - 5$ | Asset posture (1=Workstation, 5=Tier-0 DB/DC) |
| **Network Exposure** | $E$ | $0.10$ | $0.2, 0.5, 1.0$ | Internet-facing ($1.0$), Internal ($0.5$), Isolated ($0.2$) |
| **Threat Intelligence** | $I$ | $0.15$ | $0.0 - 1.0$ | Malicious reputation of source IP / file hash |
| **Correlation Bonus** | $B_{\text{corr}}$ | Dynamic | $0.0 - 0.15$ | $+0.05$ per additional distinct alert (max $+0.15$) |

---

## 2. Priority Mapping

| Priority | Risk Score Range | Typical Response Policy |
|---|---|---|
| **P1 (Critical)** | $\ge 80.0$ | Automated containment / Immediate analyst escalation |
| **P2 (High)** | $60.0 - 79.9$ | Automated containment with guardrail checks |
| **P3 (Medium)** | $40.0 - 59.9$ | Investigation queue & account rate limiting |
| **P4 (Low)** | $< 40.0$ | Informational logging & monitoring |

---

## 3. Worked Examples

### Worked Example 1: Critical SSH Brute Force with Exfiltration (P1)
- **Rule Severity:** $0.85$ (Brute force then success)
- **Rule Confidence:** $0.90$
- **Asset Criticality:** $5$ (Production Tier-0 Domain Controller) $\rightarrow 5/5 = 1.0$
- **Exposure:** $1.0$ (Internet-facing API gateway)
- **Threat Intel:** $0.95$ (Known attacker IP reported on AbuseIPDB)
- **Correlated Alerts:** 2 additional alerts ($B_{\text{corr}} = +0.10$)

**Calculation:**
$$\text{Sum} = (0.30 \times 0.85) + (0.20 \times 0.90) + (0.25 \times 1.0) + (0.10 \times 1.0) + (0.15 \times 0.95) + 0.10$$
$$\text{Sum} = 0.255 + 0.18 + 0.25 + 0.10 + 0.1425 + 0.10 = 1.0275$$
$$\text{Clamped} = 1.0 \implies \mathbf{100.0} \implies \mathbf{P1}$$

### Worked Example 2: Low-Risk Internal Probe on Workstation (P4)
- **Rule Severity:** $0.40$
- **Rule Confidence:** $0.60$
- **Asset Criticality:** $2$ (Developer workstation) $\rightarrow 2/5 = 0.40$
- **Exposure:** $0.50$ (Internal LAN)
- **Threat Intel:** $0.0$ (Clean internal IP)
- **Correlated Alerts:** 0 ($B_{\text{corr}} = 0$)

**Calculation:**
$$\text{Sum} = (0.30 \times 0.40) + (0.20 \times 0.60) + (0.25 \times 0.40) + (0.10 \times 0.50) + 0 = 0.12 + 0.12 + 0.10 + 0.05 = 0.39$$
$$\text{Final Score} = \mathbf{39.0} \implies \mathbf{P4}$$
