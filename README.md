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
| 📄 **Clerk** | Extracts the fields (gross/net pay, balances, dates…). **Every value must be found in the document text** (amounts must match exactly), otherwise it is discarded |
| 🔍 **Verifier** | Recalculates Romanian payroll taxes, checks the statement balance row by row and that the net pay arrives, looks the employer up at ANAF, Romanian ID checks (CNP ↔ ID card ↔ MRZ, age, IBAN bank) |
| 🔬 **Detector** | Image/PDF tampering: error-level analysis, JPEG ghosts, PDF editor and incremental saves, EXIF |
| 🕵️ **Detective** | Links applications through fingerprints → fraud rings (e.g. one IBAN used by 6 identities) |
| ⚖️ **Compliance** | Combines the evidence into a **risk level** (deterministic, not decided by the AI), writes a short summary — **every number in it is checked against the evidence** — and hands it to the analyst |

The **analyst decides** (approving a file flagged for investigation requires a written reason) and every AI call is audited.

### Why a fixed pipeline, not an autonomous planner
The order of the steps is fixed in code (`backend/app/core/pipeline.py`: Guard → Clerk → [Verifier ∥ Detector ∥ Detective] →
Compliance), because a bank has to audit the same steps on every file. The LLM does exactly two narrow jobs — **reading**
(Clerk: every value must be found in the document text, otherwise it is discarded) and **summarising** (Compliance: a summary
that quotes a number not in the evidence is rejected and replaced) — while every decision is a written rule. How ORB handles
the unexpected, instead of guessing:

| Situation | What ORB does | Where |
|---|---|---|
| Blurry photo / low OCR confidence, or an ID card | the document is **not sent to the cloud AI**; the file goes to a human | `agents/paznic/agent.py` (`OCR_LOW_QUALITY`) |
| A personal value survived redaction | a second gate re-scans every outgoing AI request and **blocks** it; file to a human | `core/pii_gate.py`, `core/llm.py` (`PII_GATE_BLOCKED`) |
| A sum doesn't add up, but OCR may have misread a digit | the amount is **re-read from the image** (several crops, vote) → "to check", not "forged" | `agents/verificator/agent.py` (`AMOUNT_UNCERTAIN`) |
| An agent fails or times out | the others finish; dependent agents are marked `skipped`; the verdict is "incomplete" → never shown as clean | `core/pipeline.py`, `agents/compliance/scoring.py` |
| The payslip's net pay never arrives in the bank statement (the only trace of a "perfect" forgery) | not an accusation, but always sent to a human | `agents/verificator/statement.py` (`SALARY_NOT_IN_STATEMENT`) |
| The analyst approves a flagged file | a written reason is required and stored in the audit | `api/cases.py` |


### Privacy by design
- The cloud AI (Claude on AWS Bedrock) only ever sees pseudonymised text: `[PERSOANA_1]`, `[CNP_1]`, `[IBAN_1]`.
- A **PII gate** re-scans every outgoing request and blocks it if a known personal value is still in it.
- **ID cards and unclear phone photos never go to the cloud** (if OCR confidence is low we can't guarantee the redaction) — the file goes to a human instead.
- **One button switches to 100% local AI** (Ollama on the bank's own machine): zero external calls.
- Documents and personal values are **encrypted at rest**. The app's *Privacy* panel shows the evidence for each file (what the AI saw, the encrypted bytes on disk, the audit).

## Measured results (synthetic data — see limits below)

| What | Result | How to reproduce |
|---|---|---|
| Real AI (Claude Haiku on Bedrock), 60 applications | **0 personal values sent to the cloud · 0 values invented by the AI · 0/12 honest applicants accused** (3/12 sent to a human) · **36/36 simple forgeries caught** · **12/12 "perfect" forgeries (taxes recomputed correctly) sent to a human** — the only trace is that the payslip's net pay never arrives in the bank statement · 56–60/60 per field extracted correctly · ~9–12 s per application | `backend/.venv/bin/python scripts/benchmark_pipeline.py --n 60 --llm bedrock` |
| Phone photos (simulated: perspective, blur, shadows), real AI, 20 applications | 0 sent to the cloud · 0/4 honest accused (3/4 sent to a human) · 4/4 perfect forgeries sent to a human · extraction drops a lot → ORB routes to a human instead of guessing | `... --n 20 --phone --llm bedrock` |
| Cost | ~0.005 $ per application (Haiku extracts, Sonnet summarises); 0 in local mode | per-call usage in the audit |
| Local mode (RTX 4060 laptop, Qwen 4B via Ollama) | ~8–9 s per application, same verdict as the cloud | `LLM_MODE=local` |

Raw results: [`data/benchmark/pipeline_results.json`](data/benchmark/pipeline_results.json). Tests: `cd backend && .venv/bin/python -m pytest -q` (275 passing).

### Limits — said up front
- **All data is synthetic** (generated documents, invented CNPs/IBANs/companies) and **the forgeries are ours**: the benchmark proves the
  pipeline is correct on the cases we designed, **not** accuracy on real-world fraud. The next step is labelled files from the bank.
- A **"perfect" forgery** (taxes recomputed correctly) is not visible from the payslip alone: ORB flags it only because the salary never arrives in the bank statement, and sends it to a human — it is not accused. A forger who also fakes the statement would pass.
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

**Prerequisites:** Python 3.11+, Node 20+, **Tesseract with the Romanian language pack**
(`sudo apt install tesseract-ocr tesseract-ocr-ron` · macOS: `brew install tesseract tesseract-lang`; check with
`python -c "import pytesseract; print(pytesseract.get_languages())"` → must list `ron`).
Without `ron` the Guard cannot OCR the documents and runs as a **recorded stub** (it replays the demo case; a warning is logged).
Optional: Ollama (local AI), Bedrock or Featherless key (cloud AI). Docker is not needed.

```bash
cp .env.example .env
# generate the four required secrets (the app refuses to start without them):
python3 -c "import secrets;from cryptography.fernet import Fernet;print(f'HMAC_SECRET={secrets.token_hex(32)}\nARENA_HMAC_SECRET={secrets.token_hex(32)}\nVAULT_KEY={Fernet.generate_key().decode()}\nBANK_UI_TOKEN={secrets.token_urlsafe(24)}')" >> .env
cd backend && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt && uvicorn app.main:app --port 8000
cd ../frontend && npm install && npm run dev      # http://localhost:5173  (?mock=1 = demo without backend)
```
(`cryptography` is installed by `requirements-core.txt`; run the secrets line after `pip install` if it is missing.)

**No API key? It still runs end to end:** with the default `LLM_MODE=mock`, extraction falls back to rules and Compliance uses
its template summary. Real AI: `LLM_MODE=bedrock` (+ `AWS_BEARER_TOKEN_BEDROCK`), `cloud` (+ `FEATHERLESS_API_KEY`) or
`local` (Ollama, `MODEL_LOCAL=<the tag you pulled>`).

**Demo data:**
```bash
backend/.venv/bin/python -m data.generator.build_demo          # from the repo root: Maria's documents
TOKEN=$(grep ^BANK_UI_TOKEN .env | cut -d= -f2)
curl -X POST -H "Authorization: Bearer $TOKEN" localhost:8000/api/admin/seed-demo
curl -X POST -H "Authorization: Bearer $TOKEN" localhost:8000/api/admin/rerun-demo
```
`scripts/start_bank.sh` is our demo-laptop script (Ollama + backend + ngrok tunnel; needs `NGROK_DOMAIN`).

### Verify it in 5 minutes
```bash
cd backend && .venv/bin/python -m pytest -q                        # → 275 passed
cd .. && backend/.venv/bin/python scripts/benchmark_pipeline.py --n 12   # no API key needed (rules + template)
```
The benchmark prints the same table as above (leaks, honest applicants accused / sent to a human, forgeries caught);
the expected output for Maria's case is `shared/fixtures/maria_case.json`.
Details: [ARCHITECTURE.md](ARCHITECTURE.md) (in Romanian) · ZK: [zk/README.md](zk/README.md).

## Stack
Python 3.11 · FastAPI · SQLite · Tesseract · Claude (Haiku/Sonnet/Opus) on AWS Bedrock · Ollama (Qwen) · TenSEAL · Noir/Barretenberg ·
React + Vite + TypeScript + Tailwind + TanStack Query + Recharts · Vercel + ngrok.

## Team
Samuel (orchestrator, Compliance, Arena, self-learning, ZK) · Narcis (Guard, Detector, local AI, deployment) ·
Stefan (Clerk, Verifier, homomorphic encryption, ANAF) · Erin (frontend, Detective) · Lorena (test data, benchmark, ZK page, slides).

*Internal team notes (Romanian): [`notes/`](notes/) — plan, pitch, reviews.*
