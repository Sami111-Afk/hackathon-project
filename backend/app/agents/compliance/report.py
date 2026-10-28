"""Raportul de anchetă (HTML printabil → PDF din browser). Fără date personale: doar etichete și amprente."""
from html import escape

from app.core.store import store
from app.models import Case

SEV = {"critical": ("CRITIC", "#b3261e"), "high": ("MARE", "#c2410c"), "medium": ("MEDIU", "#a16207"),
       "low": ("MIC", "#4b5563"), "info": ("INFO", "#4b5563")}
REC = {"escalate": "Investigație de fraudă", "review": "Verificare manuală", "clear": "Fără probleme"}


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
                if case.decision else "în așteptarea deciziei")
    return f"""<!doctype html><html lang="ro"><head><meta charset="utf-8"><title>Raport {escape(case.id)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:32px auto;padding:0 16px;color:#111}}
h1{{margin:0}}.muted{{color:#555}}table{{width:100%;border-collapse:collapse;margin:12px 0}}
td,th{{border-bottom:1px solid #ddd;padding:6px;text-align:left;font-size:14px}}
.box{{border:2px solid #111;padding:12px 16px;margin:16px 0}}@media print{{.noprint{{display:none}}}}</style></head>
<body><p class="noprint"><button onclick="print()">Salvează ca PDF</button></p>
<h1>Raport de anchetă — {escape(case.id)}</h1>
<p class="muted">Creat {escape(case.created_at)} · Solicitant {escape(case.applicant_token or '—')} ·
Credit cerut {(case.requested_amount_ron or 0):,.0f} lei · Date personale: doar etichete (identitățile reale sunt în seiful băncii)</p>
<div class="box"><b>Verdict:</b> {escape(v.label if v else '—')} · scor de risc {(v.risk * 100 if v else 0):.0f}/100 ·
<b>{escape(REC.get(v.recommendation, '—') if v else '—')}</b>{' · INCOMPLET' if v and v.incomplete else ''}
<p>{escape(v.summary if v else '')}</p><b>Decizie:</b> {decision}</div>
<h2>Dovezi</h2><table><tr><th>Agent</th><th>Gravitate</th><th>Cod</th><th>Detaliu</th></tr>{rows or '<tr><td colspan=4>—</td></tr>'}</table>
<h2>Dosare legate (amprente comune)</h2>
<table><tr><th>Dosar</th><th>Data</th><th>Solicitant</th><th>Sumă</th><th>Stare</th></tr>{link_rows or '<tr><td colspan=5>niciunul</td></tr>'}</table>
<p class="muted">Generat automat de ORB. Scorul e un indicator de risc, nu o probabilitate; decizia aparține angajatului.</p>
</body></html>"""
