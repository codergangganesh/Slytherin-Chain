"""Report renderers converting structured reports into JSON, Markdown, and PDF formats."""

from __future__ import annotations

import json

from jinja2 import Environment, select_autoescape

from app.services.reporting.incident_report_builder import IncidentReportDocument

HTML_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1e293b; margin: 40px; }
  h1 { color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
  h2 { color: #1e3a8a; margin-top: 25px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }
  .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
  .badge-p1 { background: #fee2e2; color: #991b1b; }
  .badge-p2 { background: #ffedd5; color: #9a3412; }
  .badge-p3 { background: #fef9c3; color: #854d0e; }
  .badge-p4 { background: #f1f5f9; color: #475569; }
  table { width: 100%; border-collapse: collapse; margin-top: 10px; }
  th, td { border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; font-size: 13px; }
  th { background: #f8fafc; }
  .box { background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; margin: 15px 0; }
  .attestation { background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 15px; }
</style>
</head>
<body>
  <h1>SentinelChain Incident Report</h1>
  <p><strong>Reference ID:</strong> {{ doc.metadata.reference_id }} | <strong>Generated:</strong> {{ doc.generated_at }}</p>
  
  <h2>1. Executive Summary</h2>
  <div class="box">{{ doc.executive_summary }}</div>

  <h2>2. Incident Metadata</h2>
  <table>
    <tr><th>Title</th><td>{{ doc.metadata.title }}</td><th>Priority</th><td><span class="badge badge-{{ doc.metadata.priority.lower() }}">{{ doc.metadata.priority }}</span></td></tr>
    <tr><th>Risk Score</th><td>{{ doc.metadata.risk_score }}/100</td><th>Status</th><td>{{ doc.metadata.status }}</td></tr>
    <tr><th>First Seen</th><td>{{ doc.metadata.first_seen }}</td><th>Duration</th><td>{{ doc.metadata.duration_seconds }}s</td></tr>
  </table>

  <h2>3. Threat Details & ATT&CK Mapping</h2>
  <table>
    <tr><th>Rule ID</th><th>Title</th><th>Severity</th><th>Tactics</th><th>Techniques</th></tr>
    {% for r in doc.threat_details.rules_fired %}
    <tr><td>{{ r.rule_id }}</td><td>{{ r.title }}</td><td>{{ r.severity }}</td><td>{{ r.tactic }}</td><td>{{ r.technique }}</td></tr>
    {% endfor %}
  </table>

  <h2>4. Attack Sequence Timeline</h2>
  <table>
    <tr><th>Timestamp (UTC)</th><th>Actor</th><th>Event / Action</th><th>MITRE</th></tr>
    {% for t in doc.attack_sequence %}
    <tr><td>{{ t.timestamp }}</td><td>{{ t.actor }}</td><td><strong>{{ t.title }}</strong><br><small>{{ t.description }}</small></td><td>{{ t.mitre_tactic or '-' }}</td></tr>
    {% endfor %}
  </table>

  <h2>5. Affected Assets & Business Impact</h2>
  <p>{{ doc.affected_assets_and_impact.business_impact_statement }}</p>

  <h2>6. Response Actions Executed & Guardrails</h2>
  <table>
    <tr><th>Action</th><th>Target</th><th>Status</th><th>Executed At</th><th>Approved By</th></tr>
    {% for a in doc.response_actions %}
    <tr><td>{{ a.action_type }}</td><td>{{ a.target }}</td><td>{{ a.status }}</td><td>{{ a.executed_at or '-' }}</td><td>{{ a.approved_by or 'Autonomous' }}</td></tr>
    {% endfor %}
  </table>

  <h2>7. Evidence Artifacts</h2>
  <table>
    <tr><th>Filename</th><th>SHA-256 Hash</th><th>Size</th><th>Collector</th></tr>
    {% for e in doc.evidence %}
    <tr><td>{{ e.filename }}</td><td><code>{{ e.file_hash_sha256 }}</code></td><td>{{ e.file_size_bytes }} B</td><td>{{ e.collected_by }}</td></tr>
    {% endfor %}
  </table>

  <h2>8. Resolution & Recommendations</h2>
  <p><strong>Notes:</strong> {{ doc.resolution_and_recommendations.resolution_notes }}</p>
  <ul>
    {% for rec in doc.resolution_and_recommendations.recommendations %}
    <li>{{ rec }}</li>
    {% endfor %}
  </ul>

  <h2>9. Cryptographic Integrity Attestation</h2>
  <div class="attestation">
    <p><strong>Verification Status:</strong> <span style="color: green; font-weight: bold;">{{ doc.integrity_attestation.verification_status }}</span></p>
    <p><strong>Ledger Sequence Range:</strong> #{{ doc.integrity_attestation.ledger_sequence_from }} - #{{ doc.integrity_attestation.ledger_sequence_to }}</p>
    <p><strong>Merkle Root:</strong> <code>{{ doc.integrity_attestation.merkle_root }}</code></p>
    <p><strong>Transaction Hash:</strong> <code>{{ doc.integrity_attestation.tx_hash or 'Pending Local Anchor' }}</code></p>
  </div>
</body>
</html>
"""


class ReportRenderers:
    """Renders IncidentReportDocument into JSON, Markdown, or PDF format."""

    @staticmethod
    def render_json(doc: IncidentReportDocument) -> bytes:
        """Render report to JSON bytes."""
        return json.dumps(doc.to_dict(), indent=2, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def render_markdown(doc: IncidentReportDocument) -> bytes:
        """Render report to GitHub Flavored Markdown bytes."""
        md = f"""# SentinelChain Incident Report — {doc.metadata.get("reference_id")}

**Generated At:** {doc.generated_at}  
**Status:** {doc.metadata.get("status")} | **Priority:** {doc.metadata.get("priority")} (Risk Score: {doc.metadata.get("risk_score")}/100)

---

## 1. Executive Summary
{doc.executive_summary}

---

## 2. Incident Metadata
- **Title:** {doc.metadata.get("title")}
- **First Seen:** {doc.metadata.get("first_seen")}
- **Last Updated:** {doc.metadata.get("last_updated")}
- **Assigned To:** {doc.metadata.get("assigned_to") or "Unassigned"}
- **Duration:** {doc.metadata.get("duration_seconds")} seconds

---

## 3. Threat Details & MITRE ATT&CK Mapping
| Rule ID | Title | Severity | Tactic | Technique |
|---|---|---|---|---|
"""
        for r in doc.threat_details.get("rules_fired", []):
            md += f"| `{r.get('rule_id')}` | {r.get('title')} | {r.get('severity')} | {r.get('tactic')} | {r.get('technique')} |\n"

        md += """
---

## 4. Attack Sequence Timeline
| Timestamp (UTC) | Actor | Event / Action | MITRE |
|---|---|---|---|
"""
        for t in doc.attack_sequence:
            md += f"| {t.get('timestamp')} | `{t.get('actor')}` | **{t.get('title')}** - {t.get('description')} | {t.get('mitre_tactic') or '-'} |\n"

        md += f"""
---

## 5. Affected Assets & Business Impact
{doc.affected_assets_and_impact.get("business_impact_statement")}

---

## 6. Response Actions Executed
| Action | Target | Status | Executed At | Approved By |
|---|---|---|---|---|
"""
        for a in doc.response_actions:
            md += f"| `{a.get('action_type')}` | `{a.get('target')}` | **{a.get('status')}** | {a.get('executed_at') or '-'} | {a.get('approved_by') or 'Autonomous'} |\n"

        md += """
---

## 7. Evidence Artifacts
| Filename | SHA-256 Hash | Size | Collector |
|---|---|---|---|
"""
        for e in doc.evidence:
            md += f"| {e.get('filename')} | `{e.get('file_hash_sha256')}` | {e.get('file_size_bytes')} B | {e.get('collected_by')} |\n"

        md += f"""
---

## 8. Resolution & Recommendations
**Resolution Notes:** {doc.resolution_and_recommendations.get("resolution_notes")}

**Follow-up Recommendations:**
"""
        for rec in doc.resolution_and_recommendations.get("recommendations", []):
            md += f"- {rec}\n"

        att = doc.integrity_attestation
        md += f"""
---

## 9. Cryptographic Integrity Attestation
> [!IMPORTANT]
> **Verification Status:** **{att.get("verification_status")}**  
> **Ledger Sequence Range:** #{att.get("ledger_sequence_from")} - #{att.get("ledger_sequence_to")}  
> **Chain Head Hash:** `{att.get("chain_head_hash")}`  
> **Merkle Root:** `{att.get("merkle_root")}`  
> **On-Chain Transaction:** `{att.get("tx_hash") or "Local Anchor / Pending"}`
"""
        return md.encode("utf-8")

    @staticmethod
    def render_pdf(doc: IncidentReportDocument) -> bytes:
        """Render report to PDF using WeasyPrint with HTML fallback."""
        env = Environment(autoescape=select_autoescape(["html", "xml"]))
        template = env.from_string(HTML_REPORT_TEMPLATE)
        rendered_html = template.render(doc=doc)

        try:
            from weasyprint import HTML

            pdf_bytes = HTML(string=rendered_html).write_pdf()
            return pdf_bytes
        except Exception:
            # Safe HTML fallback if system cairo/pango libraries are missing on Windows dev
            return rendered_html.encode("utf-8")
