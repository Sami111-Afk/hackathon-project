#!/usr/bin/env bash
# Montajul videoului de 3:00 din scenele înregistrate (video/rec/*.webm) + cardurile (video/cards/).
# Rulare din rădăcina repo-ului:  video/compose.sh            → video/out/orb_mut.mp4 (fără voce)
#                                 VOICE=video/voice/voice.m4a video/compose.sh → video/out/orb_final.mp4
# Duratele scenelor sunt în tabelul SEG de mai jos (total 180 s); se ajustează după voce.
set -euo pipefail
cd "$(dirname "$0")/.."
REC=video/rec; CARDS=video/cards; OUT=video/out; TMP=$OUT/tmp
mkdir -p "$OUT" "$TMP"
FPS=30
V="-r $FPS -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -an"

# imagine fixă cu zoom lent (Ken Burns) — $1 png, $2 durată, $3 ieșire, $4 zoom final (1.06 implicit)
still() {
  local frames=$(( $2 * FPS )) z=${4:-1.06}
  ffmpeg -v error -y -loop 1 -framerate $FPS -i "$1" -t "$2" \
    -vf "scale=3840:-2,zoompan=z='1+($z-1)*on/$frames':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$frames:s=1920x1080:fps=$FPS,format=yuv420p" \
    $V "$3"
}

# clip: $1 sursă, $2 start (s), $3 viteză (1 = normal, 2 = de două ori mai repede), $4 durată finală, $5 ieșire
# dacă sursa e mai scurtă, ultimul cadru e ținut pe ecran (tpad)
clip() {
  ffmpeg -v error -y -ss "$2" -i "$1" \
    -vf "setpts=PTS/$3,fps=$FPS,scale=1920:1080:flags=lanczos,tpad=stop_mode=clone:stop_duration=60,format=yuv420p" \
    -t "$4" $V "$5"
}

# telefon: clipul vertical (390×844) mărit, cu ramă, pe fundal închis
phone() {
  ffmpeg -v error -y -ss "$2" -i "$1" -f lavfi -i "color=c=#111418:s=1920x1080:r=$FPS" \
    -filter_complex "[0:v]setpts=PTS/$3,fps=$FPS,scale=-2:960:flags=lanczos,pad=iw+28:ih+28:14:14:color=#2A2F37[p];[1:v][p]overlay=(W-w)/2:(H-h)/2:shortest=0,tpad=stop_mode=clone:stop_duration=60,format=yuv420p" \
    -t "$4" $V "$5"
}

# documentele Mariei pentru scena 1 (pan lent peste fiecare)
DOCS=$TMP/docs; mkdir -p "$DOCS"
[ -f "$DOCS/extras-1.png" ] || pdftoppm -png -r 110 -f 1 -l 1 data/demo/maria/extras.pdf "$DOCS/extras"
for f in buletin fluturas; do
  [ -f "$DOCS/$f.png" ] || magick data/demo/maria/$f.jpg -resize 1920x1080 -background '#EDEFF2' -gravity center -extent 1920x1080 "$DOCS/$f.png"
done
[ -f "$DOCS/extras.png" ] || magick "$DOCS"/extras-1*.png -resize 1920x1080 -background '#EDEFF2' -gravity center -extent 1920x1080 "$DOCS/extras.png"

echo "▶ segmente"
still "$CARDS/01_title.png" 3 "$TMP/00.mp4" 1.03
still "$DOCS/buletin.png" 5 "$TMP/01a.mp4" 1.08
still "$DOCS/fluturas.png" 5 "$TMP/01b.mp4" 1.10
still "$DOCS/extras.png" 4 "$TMP/01c.mp4" 1.08
clip "$REC/s2_dashboard.webm" 1.5 1    9  "$TMP/02.mp4"
clip "$REC/s3_honest.webm"    1.0 1.35 18 "$TMP/03.mp4"
clip "$REC/s4_maria.webm"     2.0 1    48 "$TMP/04.mp4"
clip "$REC/s5_graph.webm"     3.0 1    10 "$TMP/05.mp4"
clip "$REC/s6_risk.webm"      2.5 1    24 "$TMP/06.mp4"
clip "$REC/s7_privacy.webm"   2.5 1    24 "$TMP/07.mp4"
still "$CARDS/05_numbers.png" 16 "$TMP/08.mp4" 1.04
phone "$REC/s9_arena.webm"    7.5 1    4  "$TMP/09a.mp4"
clip "$REC/s9b_rule.webm"     "${RULE_START:-0}" "${RULE_SPEED:-2}" 5 "$TMP/09b.mp4"
still "$CARDS/09_end.png" 5 "$TMP/10.mp4" 1.03

printf "file '%s'\n" 00.mp4 01a.mp4 01b.mp4 01c.mp4 02.mp4 03.mp4 04.mp4 05.mp4 06.mp4 07.mp4 08.mp4 09a.mp4 09b.mp4 10.mp4 > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$TMP/base.mp4"

echo "▶ texte mari peste imagine"
# overlay <png> <de la> <până la>  (fade 0,3 s la intrare și la ieșire)
OVL=(); i=1; FILT="[0:v]null[v0]"
add() {
  OVL+=(-loop 1 -i "$CARDS/$1")
  local d; d=$(awk "BEGIN{print $3 - $2}")
  FILT+=";[$i:v]format=rgba,trim=duration=$d,fade=t=in:st=0:d=0.3:alpha=1,fade=t=out:st=$(awk "BEGIN{print $d - 0.3}"):d=0.3:alpha=1,setpts=PTS-STARTPTS+$2/TB[o$i];[v$((i-1))][o$i]overlay=0:0:enable='between(t,$2,$3)'[v$i]"
  i=$((i+1))
}
add 02_twenty_minutes_overlay.png 8 14
add 03_twenty_seconds_overlay.png 19 25
add 10_realtime_overlay.png 47 52
add 04_net_mismatch_overlay.png 63 69
add 06_ring_overlay.png 94 100
add 07_ai_doesnt_decide_overlay.png 110 116
add 08_privacy_overlay.png 134 140
ffmpeg -v error -y -i "$TMP/base.mp4" "${OVL[@]}" -filter_complex "$FILT" -map "[v$((i-1))]" -t 180 $V "$TMP/video.mp4"

if [ -n "${VOICE:-}" ]; then
  echo "▶ vocea"
  ffmpeg -v error -y -i "$TMP/video.mp4" -i "$VOICE" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
    -af "afade=t=out:st=178:d=2" -t 180 "$OUT/orb_final.mp4"
  echo "gata: $OUT/orb_final.mp4"
else
  ffmpeg -v error -y -i "$TMP/video.mp4" -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a -c:v copy -c:a aac -t 180 "$OUT/orb_mut.mp4"
  echo "gata: $OUT/orb_mut.mp4"
fi
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"/orb_*.mp4
