# aestudio-reels

Free render pipeline for the AE Studio news Reels (Instagram, Facebook, TikTok, YouTube Shorts).

**How it works**
1. Commit a job file `jobs/<id>.json` (voiceover link, word timings, footage, titles, cards).
2. The `render` GitHub Action renders a 1080×1920 / 30 fps MP4 with `render/reel.py` (Python + ffmpeg).
3. The result is published as the release `<id>`:
   - `https://github.com/Ayaz-ContentCreator/aestudio-reels/releases/download/<id>/<id>.mp4` — the Reel (public URL for Metricool)
   - `<id>-cover.jpg`, `<id>-sheet.jpg` (12-frame contact sheet), `render-log.txt`, `probe.json`
   - The release title ends in `(ok)` or `(failed)`.

Re-rendering: push a changed job file (same `id` replaces the release), or run the workflow manually
(Actions → render → Run workflow) with the job path.

Note: voiceover links from ElevenLabs are signed and expire about 2 hours after generation, so commit
the job right after generating the voice.

## Style (fixed in code)
- Inter Display (headlines, captions) + JetBrains Mono (kicker labels); accent `#FFD23F`.
- No logo or corner mark. Left-aligned editorial titles; centred captions with a moving highlight on the
  spoken word; soft shadows instead of outlines.
- Safe zones: titles start at y=300, captions sit at y≈1262, max caption width 820 px.

## Job format
```json
{
  "id": "2026-10-09-spain-rent",            // release tag + file name (a-z, 0-9, -)
  "duration": 36.7,                          // seconds; = last scene end (voice length + ~0.8 s)
  "voice": {"url": "https://…content.mp3"},  // ElevenLabs media url
  "music": {"url": "https://…wav", "gain_db": -13},   // optional bed, auto-ducked under the voice
  "words": [{"text": "Rent", "start": 0.0, "end": 0.32}, …],   // ElevenLabs Scribe words
  "display": [{"i": 7, "text": "10"}, {"i": 43, "n": 2, "text": "70,000", "em": true}],
                                             // caption rewrites: word index i (n words merged)
  "emphasis": [5, 27],                       // word indexes shown in the accent colour
  "scenes": [                                // must cover 0 → duration without gaps
    {"type": "video", "src": "https://videos.pexels.com/…mp4", "in": 1.0, "start": 0.0, "end": 3.7},
    {"type": "photo", "src": "https://…jpg", "start": 3.7, "end": 6.0, "zoom": [1.0, 1.08]},
    {"type": "card", "card": "headline", "start": 6.0, "end": 8.7,
     "kicker": "The fallout", "text": "*Snap election* called", "sub": "after a fight over housing"},
    {"type": "card", "card": "stat", "start": 8.7, "end": 12.0, "kicker": "Madrid",
     "value": 70000, "suffix": "+", "sub": "people marched for housing", "source": "Reuters"},
    {"type": "card", "card": "end", "start": 32.7, "end": 36.7, "kicker": "Your take",
     "text": "Could rent decide your next *election?*", "cta": "Tell us below ↓",
     "follow": "Follow for daily US & Europe news"}
  ],
  "titles": [                                // text over footage; *word* = accent colour
    {"style": "hook", "start": 0.0, "end": 3.6, "kicker": "Spain · Housing",
     "text": "Rent has almost *doubled* in 10 years"},   // hook hides captions while shown
    {"style": "label", "start": 6.45, "end": 10.2, "kicker": "The vote", "text": "Spain votes on *Nov 29*"}
  ]
}
```
Cards blur and darken the previous footage (`"bg": "prev"`, default) or use `"bg": {"src": …, "in": 2}`.
Captions are hidden automatically during hook titles and cards.

Local test: `python3 render/reel.py job.json out/test.mp4` or `--stills 0.5,4,9` for PNG frames.

Fonts: Inter (SIL OFL 1.1), JetBrains Mono (SIL OFL 1.1) — licences in `assets/fonts/`.
