#!/usr/bin/env bash
# Pornește laptopul băncii pentru demo: Ollama (GPU) + backend (ENV=demo) + tunel ngrok, apoi verifică totul.
# Ce rulează deja e lăsat în pace, deci scriptul se poate rula de câte ori vrei.
#   scripts/start_bank.sh          pornește tot
#   scripts/start_bank.sh --stop   oprește backend-ul, Ollama și ngrok
set -uo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOGS="$REPO/logs"
ENV_FILE="$REPO/.env"
mkdir -p "$LOGS"

envval() { grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2-; }
ok()   { printf '  \033[32m✔\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✘\033[0m %s\n' "$*"; FAILED=1; }
wait_for() { for _ in $(seq 1 "$2"); do eval "$1" >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }

if [[ "${1:-}" == "--stop" ]]; then
    pkill -f '[u]vicorn app.main:app' && echo "backend oprit"
    pkill -f '[o]llama serve' && echo "ollama oprit"
    pkill -f '[n]grok http' && echo "ngrok oprit"
    exit 0
fi

[[ -f "$ENV_FILE" ]] || { echo ".env lipsește în $REPO (vezi .env.example)"; exit 1; }
FAILED=0
NGROK_DOMAIN="$(envval NGROK_DOMAIN)"
TOKEN="$(envval BANK_UI_TOKEN)"
MODEL="$(envval MODEL_LOCAL)"

echo "▶ Ollama"
if curl -sf localhost:11434/api/version >/dev/null; then
    ok "rulează deja (setările de GPU rămân cele cu care a fost pornit)"
else
    # NUM_PARALLEL=2 = LLM_MAX_CONCURRENCY; cu 4 (implicit) Ollama mută 16% din model pe CPU
    OLLAMA_HOST=127.0.0.1:11434 OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=2 OLLAMA_FLASH_ATTENTION=1 \
        OLLAMA_KV_CACHE_TYPE=q8_0 OLLAMA_CONTEXT_LENGTH=8192 \
        setsid ollama serve >"$LOGS/ollama.log" 2>&1 < /dev/null & disown
    wait_for "curl -sf localhost:11434/api/version" 30 && ok "pornit pe 127.0.0.1:11434" || bad "nu pornește (vezi logs/ollama.log)"
fi
if [[ -n "$MODEL" ]]; then
    # un apel mic încarcă modelul în VRAM, ca primul dosar din demo să nu aștepte încărcarea
    curl -sf -m 60 localhost:11434/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"ok\",\"stream\":false}" >/dev/null \
        && ok "$MODEL încărcat: $(ollama ps | awk 'NR==2{print $5, $6}')" \
        || bad "$MODEL nu răspunde (ollama pull $MODEL?)"
fi

echo "▶ Backend"
if curl -sf localhost:8000/health >/dev/null; then
    ok "rulează deja (pentru cod nou: scripts/start_bank.sh --stop, apoi din nou)"
else
    # fără „( cd … && … & )”: cu ieșirea scriptului într-un pipe, bash aștepta după uvicorn și scriptul nu se mai termina
    cd "$REPO/backend"
    ENV=demo setsid .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
        >"$LOGS/backend.log" 2>&1 < /dev/null & disown
    cd "$REPO"
    wait_for "curl -sf localhost:8000/health" 30 && ok "pornit pe 127.0.0.1:8000 (ENV=demo)" || bad "nu pornește (vezi logs/backend.log)"
fi
echo "  mod LLM: $(envval LLM_MODE)"

echo "▶ ngrok"
if [[ -z "$NGROK_DOMAIN" ]]; then
    bad "NGROK_DOMAIN lipsește din .env"
else
    if curl -sf localhost:4040/api/tunnels | grep -q "$NGROK_DOMAIN"; then
        ok "tunelul rulează deja"
    else
        setsid ngrok http --url="https://$NGROK_DOMAIN" 8000 --log=stdout >"$LOGS/ngrok.log" 2>&1 < /dev/null & disown
        wait_for "curl -sf localhost:4040/api/tunnels | grep -q $NGROK_DOMAIN" 20 && ok "tunel pornit" \
            || bad "tunelul nu pornește (vezi logs/ngrok.log)"
    fi
    code=$(curl -s -m 10 -o /dev/null -w '%{http_code}' -H 'ngrok-skip-browser-warning: 1' "https://$NGROK_DOMAIN/health")
    [[ "$code" == 200 ]] && ok "https://$NGROK_DOMAIN/health → 200" || bad "https://$NGROK_DOMAIN/health → $code"
fi

echo "▶ Test: dosarul Mariei"
if [[ -z "$TOKEN" ]]; then
    bad "BANK_UI_TOKEN lipsește din .env, testul e sărit"
elif [[ $FAILED -eq 0 ]]; then
    # rerun-demo șterge rulările Mariei terminate (intenționat, ca Dashboard-ul să nu le numere de mai multe ori)
    t0=$(date +%s)
    id=$(curl -sf -X POST -H "Authorization: Bearer $TOKEN" localhost:8000/api/admin/rerun-demo \
         | python3 -c 'import sys,json;print(json.load(sys.stdin)["case_id"])' 2>/dev/null)
    status=""
    for _ in $(seq 1 90); do
        status=$(curl -sf -H "Authorization: Bearer $TOKEN" "localhost:8000/api/cases/$id" \
                 | python3 -c 'import sys,json;print(json.load(sys.stdin)["status"])' 2>/dev/null)
        [[ "$status" == awaiting_review ]] && break; sleep 1
    done
    [[ "$status" == awaiting_review ]] && ok "gata în $(( $(date +%s) - t0 )) s" || bad "nu s-a terminat (status: ${status:-?})"
fi

echo
if [[ $FAILED -eq 0 ]]; then
    echo "✅ Laptopul băncii e gata. Loguri: $LOGS/. Ține laptopul în priză, fără sleep."
else
    echo "❌ Ceva nu merge, vezi ✘ de mai sus."
    exit 1
fi
