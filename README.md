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

**Free voiceover (default since 31 Oct 2026):** `"voice": {"tts": "kokoro", "voice": "af_bella", "speed": 1.05}`
speaks the job's `"script"` on the runner with Kokoro (open-source, no credits). The voice is published as
`<id>-voice.mp3`; leave `duration` out (it becomes voice length + 0.8 s). `tools/tts.py` does this step.

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

## Original footage (preferred over stock)
Scene fields for `video` / `photo`:
- `"src"`: a direct media file (Wikimedia Commons `upload.wikimedia.org/...`, NASA `images-assets.nasa.gov/...`,
  Pexels) **or** a video page on a site yt-dlp supports (tested: DVIDS). Only the needed seconds are downloaded;
  big remote files are cut over HTTP. **YouTube does not work on GitHub runners** (bot check) — don't use it.
- `"in"`: where in the source the scene starts (seconds).
- `"credit"`: shown on screen as a quiet line above the kicker (`VIDEO: …` / `PHOTO: …`; text with `:` or `©`
  is shown as written). Cards keep the credit of the clip blurred behind them.
- Wikimedia Commons files are licence-checked on the runner: public domain, CC0, CC BY, OGL and the EU
  "Attribution" licence pass; CC BY-SA only with `"allow_sa": true`; anything else stops the render. Commons
  files get an automatic credit (author / licence / Wikimedia Commons) when `"credit"` is missing.
- `"fit"`: default is automatic — portrait media fills the frame, landscape media is shown whole across the
  width over a blurred fill ("band"). Force a crop with `"fit": "fill"` plus `"focus": 0.3` (x) or `[x, y]`.
  While a hook title is on screen the band sits lower so the headline never covers it.

### Reused news clips
Any video page link in `"src"` goes through yt-dlp (only the needed seconds, their audio is dropped — our
voiceover runs on top). Tested from GitHub: nbcnews.com video pages (`/news/amp-video/...`), `*.euronews.com/video/...`,
US local TV station sites (Gray/Arc, e.g. wrdw.com/video, kptv.com/video), dvidshub.net. Not working from GitHub:
YouTube (incl. whitehouse.gov embeds), cbsnews.com, abcnews.com, aljazeera.com. Probe anything else first.
Without `"credit"` the clip is credited to its channel or site name; better set the outlet's proper name
(`"credit": "NBC News"`).

### Find media (runs on GitHub, which can reach Commons/NASA/DVIDS)
Push `jobs/find-<id>.json`:
```json
{"id": "find-2026-10-12-tusk", "find": [
  {"commons": "Donald Tusk", "kind": "image"},
  {"commons": "European Parliament plenary", "kind": "video"},
  {"nasa": "Artemis II", "kind": "video"},
  {"probe": "https://www.dvidshub.net/video/1015038", "in": 10, "dur": 6},
  {"probe": "https://www.nbcnews.com/news/amp-video/mmvo42821701557", "sheet": true}]}
```
The release `find-<id>` gets `find.txt`: each result with `[OK to use]` / `[SA …]` / `[NO]`, size, duration,
licence, author and the direct URL to put in `"src"`. A probe with `"sheet": true` also attaches
`<id>-<n>.jpg`: frames every 2 s (first 60 s from `"in"`, or `"dur"`) with source timecodes, to pick the exact seconds.

### Topics
`python3 tools/trends.py --hours 24 --geos US,GB,CA,DE,FR` — Google Trends "Trending now" for the last 24 h,
sports removed, merged across countries (volume, countries, category, related searches).

Local test: `python3 render/reel.py job.json out/test.mp4` or `--stills 0.5,4,9` for PNG frames.

Fonts: Inter (SIL OFL 1.1), JetBrains Mono (SIL OFL 1.1) — licences in `assets/fonts/`.
