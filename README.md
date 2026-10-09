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
Recommended (no ElevenLabs transcription needed: word timings come from Whisper on the runner, free):
```json
{
  "id": "2026-10-10-us-egg-prices",          // release tag + file name (a-z, 0-9, -)
  "voice": {"url": "https://…content.mp3"},  // ElevenLabs media url (expires ~2 h after generation)
  "script": "Egg prices just hit a record. …", // EXACT text sent to ElevenLabs
  "music": {"url": "https://…wav", "gain_db": -13},   // optional bed, auto-ducked under the voice
  "display": [{"match": "seventy thousand", "text": "70,000", "em": true},
              {"match": "twenty-thirty", "text": "2030"}],  // caption rewrites (spoken words -> digits)
  "emphasis": ["record", "Europe"],          // caption words shown in the accent colour
  "scenes": [                                // in order; "at" = first words of the sentence where the cut happens
    {"type": "video", "src": "https://videos.pexels.com/…mp4", "in": 1.0},
    {"type": "photo", "src": "https://upload.wikimedia.org/…jpg", "zoom": [1.0, 1.1], "at": "And it comes down"},
    {"type": "card", "card": "headline", "at": "Now it has",
     "kicker": "The fallout", "text": "*Snap election* called", "sub": "after a fight over housing"},
    {"type": "card", "card": "stat", "at": "More than seventy", "kicker": "Madrid",
     "value": 70000, "suffix": "+", "sub": "people marched for housing", "source": "Reuters"},
    {"type": "card", "card": "end", "at": "Could rent decide", "kicker": "Your take",
     "text": "Could rent decide your next *election?*", "cta": "Tell us below ↓",
     "follow": "Follow for daily US & Europe news"}
  ],
  "titles": [                                // text over footage; *word* = accent colour
    {"style": "hook", "until": "ten years", "kicker": "Spain · Housing",
     "text": "Rent has almost *doubled* in 10 years"},   // hook = from 0 s until those words; hides captions
    {"style": "label", "at": "On Monday", "dur": 3.3, "kicker": "The vote", "text": "Spain votes on *Nov 29*"}
  ]
}
```
- Scene/title timing: either word anchors (`"at"`, `"until"`, `"dur"`) or explicit seconds (`"start"`, `"end"`).
  Anchors must be words that appear in the script, in order; cuts land in the pause just before them.
- `duration` is optional (voice length + 0.8 s). `words` (ElevenLabs Scribe `[{text,start,end}]`) can be
  given instead of `script`; then `display` may also use word indexes `{"i": 7, "n": 2, "text": "70,000"}`.
- Cards blur and darken the previous footage (`"bg": "prev"`, default) or use `"bg": {"src": …, "in": 2}`.
- Captions are hidden automatically during hook titles and cards. `words.json` (timings used) is attached
  to each release.

Local test: `python3 render/reel.py job.json out/test.mp4` or `--stills 0.5,4,9` for PNG frames.

Fonts: Inter (SIL OFL 1.1), JetBrains Mono (SIL OFL 1.1) — licences in `assets/fonts/`.
