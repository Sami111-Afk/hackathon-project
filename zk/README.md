# ZK — „venitul meu net ≥ prag”, fără să arăt salariul

Responsabil: Samuel. Design complet: `ARCHITECTURE.md` §7.

## Versiuni fixate (compatibile între ele)
| Unealtă | Versiune | Instalare |
|---|---|---|
| `nargo` (Noir) | **1.0.0-beta.13** | `curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install \| bash` apoi `noirup -v 1.0.0-beta.13` |
| `bb` (Barretenberg, UltraHonk) | **1.2.0** | `curl -L https://raw.githubusercontent.com/AztecProtocol/aztec-packages/refs/heads/next/barretenberg/bbup/install \| bash` apoi `bbup -v 1.2.0` |
| (browser, opțional) `@noir-lang/noir_js` / `@aztec/bb.js` | `1.0.0-beta.13` / `1.2.0` | aceleași versiuni ca mai sus |

Perechea vine din tabelul oficial `bb-versions.json` (`1.0.0-beta.13 → 1.2.0`). `nargo` 1.0.0-rc.5 (cel instalat implicit) **nu** are încă `bb` compatibil.
Backend-ul caută binarele în `PATH`, `~/.nargo/bin/nargo`, `~/.bb/bb` (sau `ZK_NARGO_BIN` / `ZK_BB_BIN` în `.env`).
Fără ele, rutele `/api/zk/*` răspund 503 și testele ZK se sar (așa e în CI).

## Circuite
- `circuits/income_threshold` — privat `salary_bani, salt`; public `threshold_bani, commitment, case_nonce`.
  Verifică `pedersen_hash([salary, salt, nonce]) == commitment` și `salary >= threshold`. `nargo test` → 3 teste.
- `circuits/commitment` — ajutor pentru angajator: calculează același `pedersen_hash` (rulăm cod Noir, nu reimplementăm hash-ul în Python).
- Noir acceptă doar ASCII în comentarii/mesaje → fără diacritice în `.nr`.

## Din linia de comandă
```bash
cd zk/circuits/income_threshold
nargo execute                                   # cu Prover.toml completat
bb write_vk -b target/income_threshold.json -o target
bb prove -b target/income_threshold.json -w target/income_threshold.gz -k target/vk -o target
bb verify -k target/vk -p target/proof -i target/public_inputs   # exit 0 = valid
```
`public_inputs` = 3 × 32 octeți big-endian, în ordinea parametrilor `pub`: prag, commitment, nonce.

## Cifre (laptopul lui Samuel)
Dovadă ~0,35 s, 16 KB · verificare ~15 ms · prima rulare `write_vk` ~7 s (descarcă CRS-ul o dată).

## API (token de bancă)
`POST /api/zk/demo {net_salary_ron, installment_ron, cui, period, attack}` — tot fluxul; `attack` ∈
`none | lie_salary | lower_threshold | fake_signature | replay`. Pas cu pas: `/api/zk/nonce` → `/api/zk/employer/attest`
→ `/api/zk/client/prove` → `/api/zk/verify`. `GET /api/zk/status`, `GET /api/zk/registry`.
