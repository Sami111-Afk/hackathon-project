"""Raportul de anchetă (HTML printabil → PDF din browser). Fără date personale: doar etichete și amprente."""
from html import escape

from app.core.store import store
from app.models import Case

SEV = {"critical": ("CRITICAL", "#b3261e"), "high": ("HIGH", "#c2410c"), "medium": ("MEDIUM", "#a16207"),
       "low": ("LOW", "#4b5563"), "info": ("INFO", "#4b5563")}
REC = {"escalate": "Fraud investigation", "review": "Manual review", "clear": "No issues"}


def linked_cases(case: Case) -> list[Case]:
    mine = {fp for values in case.fingerprints.values() for fp in values}
    return [c for c in store.list() if c.id != case.id and c.source == "bank"
            and mine & {fp for values in c.fingerprints.values() for fp in values}]


def render(case: Case) -> str:
    v = case.verdict
    rows = "".join(
        f"<tr><td>{escape(r.agent)}</td><td><b style='color:{SEV[f.severity][1]}'>{SEV[f.severity][0]}</b></td>"
        f"<td>{escape(f.code)}</td><td>{escape(f.message)}</td></tr>"
        for r in case.results if r.agent != "compliance" for f in r.findings)
    links = linked_cases(case)
    link_rows = "".join(
        f"<tr><td>{escape(c.id)}</td><td>{escape(c.created_at[:10])}</td><td>{escape(c.applicant_token or '')}</td>"
        f"<td>{(c.requested_amount_ron or 0):,.0f} lei</td><td>{escape(c.status)}</td></tr>" for c in links)
    decision = (f"{escape(case.decision.action)} — {escape(case.decision.decided_by)}, {escape(case.decision.decided_at or '')}"
                if case.decision else "awaiting decision")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Report {escape(case.id)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:32px auto;padding:0 16px;color:#111}}
h1{{margin:0}}.muted{{color:#555}}table{{width:100%;border-collapse:collapse;margin:12px 0}}
td,th{{border-bottom:1px solid #ddd;padding:6px;text-align:left;font-size:14px}}
.box{{border:2px solid #111;padding:12px 16px;margin:16px 0}}@media print{{.noprint{{display:none}}}}</style></head>
<body><p class="noprint"><button onclick="print()">Save as PDF</button></p>
<h1>Investigation report — {escape(case.id)}</h1>
<p class="muted">Created {escape(case.created_at)} · Applicant {escape(case.applicant_token or '—')} ·
Loan requested {(case.requested_amount_ron or 0):,.0f} lei · Personal data: labels only (real identities are in the bank vault)</p>
<div class="box"><b>Verdict:</b> {escape(v.label if v else '—')} · risk score {(v.risk * 100 if v else 0):.0f}/100 ·
<b>{escape(REC.get(v.recommendation, '—') if v else '—')}</b>{' · INCOMPLETE' if v and v.incomplete else ''}
<p>{escape(v.summary if v else '')}</p><b>Decision:</b> {decision}</div>
<h2>Evidence</h2><table><tr><th>Agent</th><th>Severity</th><th>Code</th><th>Detail</th></tr>{rows or '<tr><td colspan=4>—</td></tr>'}</table>
<h2>Linked applications (shared fingerprints)</h2>
<table><tr><th>Application</th><th>Date</th><th>Applicant</th><th>Amount</th><th>Status</th></tr>{link_rows or '<tr><td colspan=5>none</td></tr>'}</table>
<p class="muted">Generated automatically by ORB. The score is a risk indicator, not a probability; the decision belongs to the employee.</p>
</body></html>"""
