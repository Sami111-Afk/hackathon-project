"""Misiunile Arenei și registrul de firme (inventat) folosit de arbitru.

Toate datele sunt sintetice. CUI-urile au cifra de control validă.
"""
from datetime import date

# Firme inventate — „ANAF simulat” pentru Arenă
COMPANIES = {
    "Tehnoserv Construct SRL": {"cui": "RO9185472906", "active": True, "founded": date(2015, 4, 2),
                                "employees": 3, "median_gross": 5200,
                                "role_medians": {"Operator date": 4800, "Contabil": 6000, "Administrator": 7500}},
    "Bitwave Software SRL": {"cui": "RO9341910290", "active": True, "founded": date(2011, 9, 14),
                             "employees": 420, "median_gross": 13500,
                             "role_medians": {"Operator date": 5500, "Contabil": 9000, "Programator": 14000,
                                              "Team lead": 21000, "Director": 34000}},
    "Agro Prahova Distribuție SRL": {"cui": "RO9402119372", "active": False, "founded": date(2019, 1, 22),
                                     "employees": 0, "median_gross": 0, "role_medians": {}},
    "Nordic Consulting Grup SRL": {"cui": "RO9477321003", "active": True, "founded": date(2026, 6, 10),
                                   "employees": 2, "median_gross": 6000,
                                   "role_medians": {"Consultant": 6000, "Administrator": 8000}},
}

JOB_TITLES = sorted({r for c in COMPANIES.values() for r in c["role_medians"]})

MISSIONS = {
    "payslip_9000": {
        "id": "payslip_9000",
        "title": "The 9,000 payslip",
        "brief": "The bank requires a net income of at least 9,000 lei. Forge a payslip that passes verification.",
        "doc_type": "payslip",
        "target": {"field": "net_salary", "min": 9000},
        "template": {
            "employee": "[PERSOANA_DEMO]",
            "employer": "Tehnoserv Construct SRL",
            "job_title": "Operator date",
            "gross_salary": 10000,
            "net_salary": 5850,
            "issue_date": "2026-09-30",
        },
        "editable": {
            "gross_salary": {"type": "number", "label": "Gross salary (lei)", "min": 0, "max": 100000},
            "net_salary": {"type": "number", "label": "Net salary (lei)", "min": 0, "max": 100000},
            "employer": {"type": "select", "label": "Employer", "options": list(COMPANIES)},
            "job_title": {"type": "select", "label": "Job title", "options": JOB_TITLES},
            "issue_date": {"type": "date", "label": "Issue date"},
        },
        "tricks": {
            "recompute_taxes": "Recompute the taxes (net is calculated from gross)",
            "hide_injection": "Hide a text that tries to fool the AI",
            "ai_photo": "Replace the stamp with an AI-generated one",
        },
    },
    "payslip_ceo": {
        "id": "payslip_ceo",
        "title": "The ghost director",
        "brief": "Pretend to be a director with a net income of at least 20,000 lei. Pass verification.",
        "doc_type": "payslip",
        "target": {"field": "net_salary", "min": 20000},
        "template": {
            "employee": "[PERSOANA_DEMO]",
            "employer": "Bitwave Software SRL",
            "job_title": "Programator",
            "gross_salary": 14000,
            "net_salary": 8190,
            "issue_date": "2026-09-30",
        },
        "editable": None,  # aceleași câmpuri ca la prima misiune (completat mai jos)
        "tricks": None,
    },
}
MISSIONS["payslip_ceo"]["editable"] = MISSIONS["payslip_9000"]["editable"]
MISSIONS["payslip_ceo"]["tricks"] = MISSIONS["payslip_9000"]["tricks"]


def public_missions() -> list[dict]:
    return list(MISSIONS.values())
