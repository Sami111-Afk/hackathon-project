# Videoul de 3:00 — montaj la secundă

Textul vocii: `notes/video.md` („Varianta finală a vocii”). Cardurile: `video/cards/` (regenerare:
`backend/.venv/bin/python scripts/make_video_cards.py`). `*_overlay.png` = fundal transparent, se pun PESTE clip.

| # | De la → la | Durată | Imagine | Card / overlay | Vocea |
|---|---|---|---|---|---|
| 0 | 0:00 → 0:03 | 3 s | — | `01_title.png` (plin) | — (doar muzică) |
| 1 | 0:03 → 0:17 | 14 s | documentele Mariei, zoom încet | `02_twenty_minutes_overlay` din 0:08 | [0:00] „Every loan application…” |
| 2 | 0:17 → 0:26 | 9 s | Dashboard | `03_twenty_seconds_overlay` din 0:19 | [0:15] „ORB does that work…” |
| 3 | 0:26 → 0:44 | 18 s | New application → `data/demo/honest/` → aprobat | — | [0:25] „Here's a normal application…” |
| 4 | 0:44 → 1:32 | 48 s | Maria: Re-run live (agenții la **2x**) → dovezi → chenar pe fluturaș → Edit map | `10_realtime_overlay` pe agenți; `04_net_mismatch_overlay` pe „net pay doesn't follow” | [0:45] „Now Maria…” |
| 5 | 1:32 → 1:42 | 10 s | graful rețelei | `06_ring_overlay` | [1:35] „the same bank account…” |
| 6 | 1:42 → 2:06 | 24 s | Very high → Why this score? → Approve fără motiv (cere motiv) | `07_ai_doesnt_decide_overlay` | [1:45] „The AI doesn't decide…” |
| 7 | 2:06 → 2:30 | 24 s | Privacy → What the AI saw → butonul Local | `08_privacy_overlay` | [2:10] „The cloud AI only ever sees labels…” |
| 8 | 2:30 → 2:46 | 16 s | — | `05_numbers.png` (plin) | [2:35] „We measured it…” |
| 9 | 2:46 → 2:55 | 9 s | telefonul: Arena, fals prins | — | [2:50] „Try to fool it yourself…” |
| 10 | 2:55 → 3:00 | 5 s | — | `09_end.png` (plin) | „…never instead of them.” se termină aici |
| | **total** | **180 s** | | | |

Reguli: vocea comandă — dacă un paragraf iese mai lung, scurtezi imaginea scenei, nu vocea. Overlay-urile stau 2–3 s, cu fade 0,3 s.
Sunete: click la apăsări, whoosh la pornirea agenților (scena 4), alertă scurtă la `04_net_mismatch`. Muzica −25 dB, fade out pe ultimele 2 s.
Export: 1080p, 30 fps, MP4. Verificat: durata **≤ 3:00**, o vizionare fără sunet (subtitrări), una pe telefon.
