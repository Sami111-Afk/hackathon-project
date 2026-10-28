#!/usr/bin/env bash
# Deploy pe Vercel (producție) dintr-o copie FĂRĂ git a lui frontend/ + shared/.
# De ce: pe planul gratuit, cu repo privat, Vercel blochează deploy-ul dacă ultimul commit e al altcuiva
# decât proprietarul contului Vercel. Fără metadate git, verificarea nu mai apare.
# Folosire (din oricare folder al repo-ului, după `git pull`):  scripts/deploy_frontend.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

copy() {  # copy <sursă> <destinație> — fără node_modules, dist, .git
    mkdir -p "$2"
    tar -C "$1" --exclude=node_modules --exclude=dist --exclude=.git -cf - . | tar -C "$2" -xf -
}

copy "$REPO/frontend" "$TMP/frontend"
copy "$REPO/shared" "$TMP/shared"   # vite.config: @shared → ../shared (fixture-urile Mariei)

# Proiectul Vercel poate fi legat din rădăcina repo-ului (Root Directory = frontend în setări) sau din frontend/
if [[ -d "$REPO/.vercel" ]]; then
    cp -r "$REPO/.vercel" "$TMP/.vercel"
    DIR="$TMP"
elif [[ -d "$REPO/frontend/.vercel" ]]; then
    DIR="$TMP/frontend"
    echo "ℹ proiect legat din frontend/: dacă build-ul pe Vercel nu găsește ../shared, leagă-l din rădăcină:"
    echo "  (cd $REPO && npx vercel link) și setează în Vercel → Settings → Root Directory = frontend"
else
    echo "✗ proiectul Vercel nu e legat: rulează o dată 'npx vercel link' din rădăcina repo-ului" >&2
    exit 1
fi

echo "▶ Deploy fără git, versiunea locală: $(git -C "$REPO" log --oneline -1)"
cd "$DIR"
npx --yes vercel --prod --yes
