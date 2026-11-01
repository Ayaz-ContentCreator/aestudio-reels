# Long-form YouTube videos (WWE stories channel)

16:9, 1920x1080, 30 fps, 18-22 min. Same design language as the Reels (Inter Display + JetBrains Mono,
yellow #FFD23F accent, left-aligned editorial titles, word-highlight captions) but landscape.
`render/reel.py` is imported and re-dimensioned; never edit it for long-form.

## Files

| Path | What |
|---|---|
| `longform/src/<id>.py` | Authoring source: script beats + what is on screen + footage slots. Run it to write the job. |
| `longform/<id>.json` | Render job (written by the source file). **Pushing it starts the render.** |
| `longform/media/<id>.json` | List of supplied footage on Google Drive. Pushing it starts `fetch-media`. |
| `longform/shotlists/<id>.html` | Shot list page given to Ayaz (numbered slots with links). Use as template. |
| `tools/longform_prep.py` | Voice (Kokoro), word timings (Whisper), scenes, footage slots, media, music, slices. |
| `render/longform.py` | Renders one slice / QA stills / thumbnail. |
| `tools/longform_assemble.py` | Joins slices, mixes voice + music (-14 LUFS), sheet, thumbnail. |
| `tools/fetch_media.py` | Downloads supplied footage from Drive, contact sheets for videos. |

## Workflow per video

1. **Research** the star (start, rise, key matches/feuds, titles, incidents, injuries, retirement, life now).
   Two reputable sources per fact. Note exact dates and numbers.
2. **Script** in `longform/src/<id>.py` (copy `2026-11-02-the-rock.py`): about 2,900 words =
   about 19-20 min with Kokoro `am_michael` at speed 1.03. Cold open (hook first line, 60-90 s), title card,
   10-12 chapters (`chapter()`), end card that names the next star and asks one question.
   `[[caption|spoken]]` for numbers/names; `*accent*` in on-screen text.
3. **Slots**: every beat that should show real footage gets `B[i]["show"]["slot"] = "Rxx"` (`SLOTMAP`),
   with `SLOT_CREDIT` (source shown top-right). Cards with words (headline, statement, quote, versus)
   become the footage + a label; photo/video scenes swap their source; stat/list/timeline/bars keep the
   card over a blurred still of the footage. Footage scenes over 5.5 s are cut into several shots.
   Without a file for a slot the scene keeps its Commons/studio visual, so a video can render with gaps.
4. **Shot list** `longform/shotlists/<id>.html` (copy the template): one row per slot with what to save
   and direct links (official WWE YouTube, news photo pages, free-licensed Commons files). Publish it as an
   artifact and send Ayaz the link: he saves the files into a Drive folder `WWE <Star>` (named R01.jpg,
   R15.mp4 ...; variants R01b.jpg) and sets the folder to "Anyone with the link: Viewer".
   Do not download photos/videos of real people from the web yourself; edit only files Ayaz supplies.
5. **Fetch**: list the folder with the Google Drive connector (`parentId = '<folder id>'`), write
   `longform/media/<id>.json` = `{"id": "<id>", "files": [{"drive": "<file id>", "name": "R01.jpg"}, ...]}`
   (rename to slot codes from the file names), push. `fetch-media` stores the files in the DRAFT release
   `media-<id>` with `sheet-Rxx.jpg` contact sheets for videos. Read the sheets
   (`gh api repos/Ayaz-ContentCreator/aestudio-reels/releases` -> draft `media-<id>` -> assets) and set
   `"slot_in": {"R15": [312.0, 330.5]}` (good moments, in order) in the source file.
6. **Render**: run the source file, push `longform/<id>.json`. `render-long` = prep (~15 min) -> 10 slices
   in parallel (~15 min) -> assemble. Release `<id>` "(ok)" has `<id>.mp4`, `<id>-thumb.jpg`, `<id>-sheet.jpg`,
   `chapters.txt`, `script.txt`, `render-log.txt`. QA the sheet, thumbnail and loudness line.
7. **Upload** through Metricool to the WWE channel brand: `providers: [{"network": "youtube"}]`,
   `youtubeData: {"title", "type": "video", "privacy": "public", "tags", "category": "SPORTS",
   "madeForKids": false, "isAiGeneratedContent": false}`, media = the release mp4 URL,
   `videoThumbnailUrl` = the thumb URL (only if the channel is verified). Description: 2-line hook,
   chapters from `chapters.txt`, sources, footage credits ("used for commentary and criticism"),
   3-5 hashtags. After Metricool has copied the media (static.metricool.com), delete the public release
   assets (`gh release delete <id> --cleanup-tag`) - keep `script.txt` locally if needed.

## Rules

- Original script and commentary over every shot (YouTube "inauthentic/reused content" policy):
  photos and short excerpts, our voice on top, source audio dropped, no long unedited match footage.
- AI disclosure: the voice is a generic TTS voice, not an imitation of a real person, and there are no
  realistic AI-generated images, so `isAiGeneratedContent` is false.
- Music: generated in code (`"music": {"gen": "ambient", "gain_db": -24}`), no samples, no AI music.
