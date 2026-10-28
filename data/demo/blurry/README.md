# Dosar cinstit cu poze de telefon neclare — scena „situații neprevăzute” din video

Generat cu `scripts/benchmark_pipeline.py --n 8 --phone --seed 11 --generate-only` (dosarul `honest`, date inventate:
CNP cu `000`, IBAN sucursala 9999, propriu), apoi blur suplimentar (`magick -blur 0x1.6 -quality 55`).
Testat prin „New application” (30.000 lei): Paznicul dă `OCR_LOW_QUALITY` pe 2 documente → textul nu pleacă spre AI-ul
din cloud, recomandarea e **review** (risc 0,19), nicio legătură cu alte dosare.
