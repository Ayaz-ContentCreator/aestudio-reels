#!/usr/bin/env python3
"""Free voiceover on the GitHub runner (Kokoro, open-source, Apache-2.0).

usage: tts.py <job.json> <outdir> <resolved-job.json>

If the job's "voice" is {"tts": "kokoro", "voice": "af_bella", "speed": 1.05}, the "script" is spoken
with Kokoro, saved as <outdir>/<id>-voice.mp3 (published with the release) and a copy of the job with
"voice": {"url": <local wav>} is written to <resolved-job.json>. Any other job is copied unchanged.
"""
import json
import os
import subprocess
import sys

MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))


def main():
    job_path, outdir, resolved = sys.argv[1:4]
    job = json.load(open(job_path))
    voice = job.get("voice") or {}
    if voice.get("tts") == "kokoro":
        import soundfile as sf
        from kokoro_onnx import Kokoro
        script = job["script"]
        k = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
        audio, sr = k.create(script, voice=voice.get("voice", "af_bella"),
                             speed=float(voice.get("speed", 1.05)), lang=voice.get("lang", "en-us"))
        os.makedirs(outdir, exist_ok=True)
        wav = os.path.abspath(os.path.join(outdir, "..", job["id"] + "-voice.wav"))
        sf.write(wav, audio, sr)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "192k",
                        os.path.join(outdir, job["id"] + "-voice.mp3")], check=True)
        print(f"kokoro {voice.get('voice', 'af_bella')}: {len(audio) / sr:.2f} s")
        job["voice"] = {"url": wav}
    json.dump(job, open(resolved, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
