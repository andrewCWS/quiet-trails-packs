#!/usr/bin/env python3
"""Cut usable effect snippets out of long field recordings.

xeno-canto files are whole sessions — a minute of bush with a bird in it
somewhere, often quiet and often with wind underneath. This finds the most
energetic window of about the right length, trims it to the call, filters the
rumble out and levels it.

    python snip.py sfx/birds                 # every file, key guessed by name
    python snip.py "sfx/birds/XC123 - ...mp3" --key kookaburra --seconds 4

Candidates land in sfx/candidates/ with a preview reel alongside, so you can
listen before promoting one to sfx/<key>.mp3.
"""
import argparse
import re
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_leading_silence

# Filename fragment -> key, and how long that call wants to be.
SPECIES = {
    "kookaburra": ("kookaburra", 4.0),
    "lyrebird":   ("lyrebird-call", 3.0),
    "magpie":     ("magpie", 4.0),
    "whipbird":   ("whipbird", 2.5),
    "boobook":    ("boobook", 3.5),
    "car_door":   ("car-door", 1.0),
    "car door":   ("car-door", 1.0),
}

HOP_MS = 50
LEVEL_DBFS = -16.0
FADE_MS = 30
HIGHPASS_HZ = 150          # field recordings carry a lot of wind rumble


def key_for(path):
    name = path.stem.lower()
    for fragment, (key, seconds) in SPECIES.items():
        if fragment in name:
            return key, seconds
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:40], 3.0


def best_window(seg, seconds):
    """Start offset of the loudest window of `seconds`, in ms."""
    frames = [seg[i:i + HOP_MS].dBFS for i in range(0, len(seg) - HOP_MS, HOP_MS)]
    frames = [f if f != float("-inf") else -90.0 for f in frames]
    if not frames:
        return 0

    floor = sorted(frames)[len(frames) // 5]          # 20th percentile
    energy = [max(0.0, f - floor) for f in frames]
    width = max(1, int(seconds * 1000 / HOP_MS))
    if width >= len(energy):
        return 0

    running = sum(energy[:width])
    best, best_at = running, 0
    for i in range(width, len(energy)):
        running += energy[i] - energy[i - width]
        if running > best:
            best, best_at = running, i - width + 1
    return best_at * HOP_MS


def snip(path, key=None, seconds=None, out_dir=Path("sfx/candidates")):
    guessed_key, guessed_seconds = key_for(path)
    key = key or guessed_key
    seconds = seconds or guessed_seconds

    seg = AudioSegment.from_file(path).set_channels(1)
    seg = seg.high_pass_filter(HIGHPASS_HZ)

    start = best_window(seg, seconds)
    clip = seg[start:start + int(seconds * 1000)]

    # tighten onto the call itself, relative to this clip's own quiet parts
    floor = clip.dBFS - 12 if clip.dBFS != float("-inf") else -50
    lead = detect_leading_silence(clip, silence_threshold=floor)
    tail = detect_leading_silence(clip.reverse(), silence_threshold=floor)
    if lead + tail < len(clip):
        clip = clip[max(0, lead - 120):len(clip) - max(0, tail - 200)]

    if clip.dBFS != float("-inf"):
        clip = clip.apply_gain(LEVEL_DBFS - clip.dBFS)
    clip = clip.fade_in(FADE_MS).fade_out(FADE_MS)

    out_dir.mkdir(parents=True, exist_ok=True)
    n = 1
    while (out := out_dir / f"{key}-{n}.mp3").exists():
        n += 1
    clip.export(out, format="mp3", bitrate="192k")
    print(f"{path.name[:44]:46} -> {out.name:22} {len(clip)/1000:.1f}s "
          f"(from {start/1000:.0f}s in)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="+", help="audio file(s) or a directory")
    ap.add_argument("--key", help="output name; guessed from the filename otherwise")
    ap.add_argument("--seconds", type=float, help="target snippet length")
    ap.add_argument("--out", default="sfx/candidates")
    args = ap.parse_args()

    files = []
    for raw in args.source:
        p = Path(raw)
        if p.is_dir():
            files += sorted(f for f in p.rglob("*")
                            if f.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg", ".flac"})
        else:
            files.append(p)

    made = [snip(f, args.key, args.seconds, Path(args.out)) for f in files]

    reel = AudioSegment.empty()
    for f in sorted(made):
        reel += AudioSegment.silent(duration=500) + AudioSegment.from_file(f)
    if len(reel):
        out = Path(args.out) / "_preview.mp3"
        reel.export(out, format="mp3", bitrate="192k")
        print(f"\npreview: {out} ({len(reel)/1000:.0f}s)")
        for f in sorted(made):
            print(f"  {f.stem}")


if __name__ == "__main__":
    main()
