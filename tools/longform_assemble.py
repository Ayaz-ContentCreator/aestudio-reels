#!/usr/bin/env python3
"""Join the rendered slices of a long-form video, mix voice + music, write the final MP4 + QA files.

usage: longform_assemble.py <plan_dir> <seg_dir> <out_dir>
out_dir gets <id>.mp4, <id>-thumb.jpg, <id>-sheet.jpg, chapters.txt, script.txt, words.json, render-log.txt
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print("+", " ".join(cmd)[:300], flush=True)
    subprocess.run(cmd, check=True)


def main(plan_dir, seg_dir, out_dir):
    plan = json.load(open(os.path.join(plan_dir, "plan.json")))
    vid = plan["id"]
    os.makedirs(out_dir, exist_ok=True)
    segs = sorted(glob.glob(os.path.join(seg_dir, "**", "seg_*.mp4"), recursive=True),
                  key=lambda p: int(re.search(r"seg_(\d+)", p).group(1)))
    if len(segs) != len(plan["slices"]):
        sys.exit(f"expected {len(plan['slices'])} slices, found {len(segs)}")
    lst = os.path.join(out_dir, "concat.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    video = os.path.join(out_dir, "video.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    total = plan["total"]
    voice = os.path.join(plan_dir, plan["voice"])
    audio = os.path.join(out_dir, "audio.m4a")
    if plan.get("music"):
        music = os.path.join(plan_dir, plan["music"])
        g = plan.get("music_gain_db", -24)
        fc = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={total},asplit=2[v1][v2];"
              f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={g}dB,afade=t=in:d=2.5,"
              f"apad=whole_dur={total}[m];"
              f"[m][v1]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=700:makeup=1[md];"
              f"[v2][md]amix=inputs=2:normalize=0:duration=longest,atrim=0:{total},"
              f"afade=t=out:st={total - 3.0:.2f}:d=3.0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
        run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-stream_loop", "-1", "-i", music, "-filter_complex", fc,
             "-map", "[out]", "-t", f"{total:.3f}", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", audio])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-i", voice, "-af",
             f"apad=whole_dur={total},loudnorm=I=-14:TP=-1.5:LRA=11", "-t", f"{total:.3f}", "-ar", "48000",
             "-ac", "2", "-c:a", "aac", "-b:a", "192k", audio])
    final = os.path.join(out_dir, f"{vid}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-c", "copy",
         "-movflags", "+faststart", "-t", f"{total:.3f}", final])
    os.remove(video)
    os.remove(audio)

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                final], capture_output=True, text=True).stdout.strip())
    run(["ffmpeg", "-v", "error", "-y", "-i", final, "-vf", f"fps=48/{dur},scale=320:-1,tile=8x6:padding=4:color=0x202020",
         "-frames:v", "1", "-q:v", "3", os.path.join(out_dir, f"{vid}-sheet.jpg")])
    run([sys.executable, os.path.join(HERE, "..", "render", "longform.py"), os.path.join(plan_dir, "plan.json"),
         os.path.join(out_dir, f"{vid}-thumb.jpg"), "--thumb"])
    for f in ("chapters.txt", "script.txt", "words.json"):
        if os.path.exists(os.path.join(plan_dir, f)):
            shutil.copy(os.path.join(plan_dir, f), out_dir)
    loud = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", final, "-af", "ebur128=peak=true", "-f", "null",
                           "-"], capture_output=True, text=True).stderr
    summary = loud[loud.find("Summary:"):] if "Summary:" in loud else loud[-600:]
    size = os.path.getsize(final) / 1e6
    with open(os.path.join(out_dir, "render-log.txt"), "a") as fh:
        fh.write(f"final: {final} {dur:.2f}s {size:.0f} MB, {len(segs)} slices\n{summary}\n")
    print(f"final {final}: {dur:.2f}s, {size:.0f} MB")
    print(summary)


if __name__ == "__main__":
    main(*sys.argv[1:4])
