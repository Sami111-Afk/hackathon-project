# ORB — AI agents that do the repetitive checks on loan applications, without customer data leaving the bank

> Hackathon · **Raiffeisen Bank: Operational Efficiency** — *"Explore how AI agents can reduce repetitive work involving documents, data, and verification."*

**Live demo:** https://orb-raiffeisen.vercel.app (the bank login token is provided to the jury separately) · **Arena (no login, works on a phone):** https://orb-raiffeisen.vercel.app/arena

## The problem

For every consumer-loan application, a back-office analyst reads the ID card, the payslip and the bank statement, recalculates the
taxes on the payslip, looks the employer up at ANAF (the Romanian tax authority), checks that the salary actually arrives in the
statement — and only rarely has time to check whether the same IBAN or phone number appears in other applications.
That is **~20 minutes of repetitive work per application** (our informal test + a step-by-step estimate of 14–21 min; vendor
studies on mortgages report hours per file), and identity-fraud rings slip through because they are invisible one file at a time.

## What ORB does

ORB runs the same checks in **~12–20 seconds** (8–9 s fully local), shows every finding **on the document itself**, and leaves the
decision to the analyst.

| Role | What it does |
|---|---|
| 🛡️ **Guard** | OCR; finds and hides personal data (CNP, IBAN, names, addresses, ID-card MRZ) **before any AI sees the text**; keeps the real values in an encrypted vault; HMAC fingerprints to link applications without storing identifiers |
| 📄 **Clerk** | Extracts the fields (gross/net pay, balances, dates…). **Every value must be found verbatim in the document**, otherwise it is discarded |
| 🔍 **Verifier** | Recalculates Romanian payroll taxes, checks the statement balance row by row and that the net pay arrives, looks the employer up at ANAF, Romanian ID checks (CNP ↔ ID card ↔ MRZ, age, IBAN bank) |
| 🔬 **Detector** | Image/PDF tampering: error-level analysis, JPEG ghosts, PDF editor and incremental saves, EXIF |
| 🕵️ **Detective** | Links applications through fingerprints → fraud rings (e.g. one IBAN used by 6 identities) |
| ⚖️ **Compliance** | Combines the evidence into a **risk level** (deterministic, not decided by the AI), writes a short summary — **every number in it is checked against the evidence** — and hands it to the analyst |

The **analyst decides** (approving a file flagged for investigation requires a written reason) and every AI call is audited.

### Privacy by design
- The cloud AI (Claude on AWS Bedrock) only ever sees pseudonymised text: `[PERSOANA_1]`, `[CNP_1]`, `[IBAN_1]`.
- A **PII gate** re-scans every outgoing request and blocks it if a known personal value is still in it.
- **ID cards and unclear phone photos never go to the cloud** (if OCR confidence is low we can't guarantee the redaction) — the file goes to a human instead.
- **One button switches to 100% local AI** (Ollama on the bank's own machine): zero external calls.
- Documents and personal values are **encrypted at rest**. The app's *Privacy* panel shows the evidence for each file (what the AI saw, the encrypted bytes on disk, the audit).

## Measured results (synthetic data — see limits below)

| What | Result | How to reproduce |
|---|---|---|
| Real AI (Claude Haiku on Bedrock), 60 applications | **0 personal values sent to the cloud · 0 values invented by the AI · 0/12 honest applicants accused** (3/12 sent to a human) · **36/36 planted forgeries caught** · 56–60/60 per field extracted correctly · ~12 s per application | `backend/.venv/bin/python scripts/benchmark_pipeline.py --n 60 --llm bedrock` |
| Phone photos (simulated: perspective, blur, shadows), real AI, 20 applications | 0 sent to the cloud · 0/4 honest accused (3/4 sent to a human) · extraction drops a lot → ORB routes to a human instead of guessing | `... --n 20 --phone --llm bedrock` |
| Cost | ~0.005 $ per application (Haiku extracts, Sonnet summarises); 0 in local mode | per-call usage in the audit |
| Local mode (RTX 4060 laptop, Qwen 4B via Ollama) | ~8–9 s per application, same verdict as the cloud | `LLM_MODE=local` |

Raw results: [`data/benchmark/pipeline_results.json`](data/benchmark/pipeline_results.json). Tests: `cd backend && .venv/bin/python -m pytest -q` (272 passing).

### Limits — said up front
- **All data is synthetic** (generated documents, invented CNPs/IBANs/companies) and **the forgeries are ours**: the benchmark proves the
  pipeline is correct on the cases we designed, **not** accuracy on real-world fraud. The next step is labelled files from the bank.
- A **"perfect" forgery** (taxes recomputed correctly) is not visible from the payslip alone — only via the statement/ANAF.
- The risk level is a **severity score, not a probability**.
- The demo's inactive employer comes from a **demo company registry** (real ANAF is queried for real companies).
- Demo-grade: a single shared access token (production: the bank's SSO/roles), SQLite, Bedrock in `us-west-2` on the organisers'
  account (production: an EU region under the bank's AWS contract, or fully on-prem).

## Implemented vs prototype

| Part | Status |
|---|---|
| 6-role pipeline, live updates (SSE), evidence on the document, risk level + "Why this score?", human decision + audit | ✅ implemented |
| PII redaction, encrypted vault and files, PII gate, cloud refusal for ID cards / unclear photos, local mode (Ollama) | ✅ implemented, measured above |
| Romanian tax recalculation, ANAF lookup (real API + demo registry), statement checks, tampering detection, fraud-ring graph | ✅ implemented |
| **Arena** — anyone tries to fool ORB with a forged payslip from their phone; live projector screen; an automatic (algorithmic) attacker | ✅ implemented (demo feature) |
| **Self-learning** — the AI proposes detection rules (limited JSON format, no code) from forgeries that slipped through; rules are back-tested against honest files and **approved by a human** | ✅ implemented, evaluated on synthetic data only |
| **Homomorphic encryption** (CKKS/TenSEAL) — a third-party verifier recomputes the payslip formula on encrypted amounts | 🧪 prototype (in the demo the verifier runs next to the bank) |
| **Zero-knowledge income proof** (Noir + Barretenberg) — the customer proves "net income ≥ threshold" without revealing it | 🧪 prototype (employer and customer wallet simulated server-side) |

## Run it

```bash
cp .env.example .env            # fill the secrets (generation commands are in the comments)
cd backend && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt && uvicorn app.main:app --port 8000
cd ../frontend && npm install && npm run dev      # http://localhost:5173  (?mock=1 = demo without backend)
```
Requires Tesseract with the Romanian language pack. Demo data: `python -m data.generator.build_demo`, then
`POST /api/admin/seed-demo` and `POST /api/admin/rerun-demo` (bank token). One-command demo machine: `scripts/start_bank.sh`.
Details: [ARCHITECTURE.md](ARCHITECTURE.md) (in Romanian) · ZK: [zk/README.md](zk/README.md).

## Stack
Python 3.11 · FastAPI · SQLite · Tesseract · Claude (Haiku/Sonnet/Opus) on AWS Bedrock · Ollama (Qwen) · TenSEAL · Noir/Barretenberg ·
React + Vite + TypeScript + Tailwind + TanStack Query + Recharts · Vercel + ngrok.

## Team
Samuel (orchestrator, Compliance, Arena, self-learning, ZK) · Narcis (Guard, Detector, local AI, deployment) ·
Stefan (Clerk, Verifier, homomorphic encryption, ANAF) · Erin (frontend, Detective) · Lorena (test data, benchmark, ZK page, slides).

*Internal team notes (Romanian): [`notes/`](notes/) — plan, pitch, reviews.*
