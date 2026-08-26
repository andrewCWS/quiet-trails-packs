#!/usr/bin/env python3
"""
narrate.py — turn tagged story scripts into audio files.

Reads a markdown file containing one or more stories with speaker tags like
**NARRATOR:** / **ECHO:** / **RORI:**, splits it into speaker blocks, sends each
block to a TTS API with the matching voice, and joins the clips into one MP3
per story.

Usage:
    python narrate.py scripts.md --dry-run          # parse only, no API calls, no cost
    python narrate.py scripts.md                    # generate audio
    python narrate.py scripts.md --provider fish
    python narrate.py scripts.md --single-voice     # everyone in one voice

Set your key first:
    export ELEVENLABS_API_KEY=sk_...
    export FISH_API_KEY=...
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Need requests:  pip install requests")

# ---------------------------------------------------------------- config

# Speakers the parser will recognise. Anything else in **Bold:** form is
# treated as metadata and ignored, which is what keeps the header lines
# ("**Mode:** Prose") out of the audio.
SPEAKERS = {"NARRATOR", "ECHO", "RORI", "BILLY", "SKYE", "ADI", "ALL"}

# Map each speaker to a voice id. Everyone except Echo shares the narrator
# voice by default — the narrator performs the kids' lines, as in an audiobook.
ELEVENLABS_VOICES = {
    "NARRATOR": "iIg0uI51lssRFauz7W21",
    "ECHO": "ssxGjYJjpi2zZlztJhZU",
}
FISH_VOICES = {
    "NARRATOR": "1f3f0e3b021d4acbb93ea239e69d65e3",
    "ECHO": "04561fb2a7ca4e5b8e6be3885606cda7",
}

ELEVENLABS_MODEL = "eleven_multilingual_v2"   # or "eleven_flash_v2_5" — half price
FISH_MODEL = "s1"                             # or "s2-pro"

# Leading italic phrases that are performance directions, not dialogue.
# Everything in (round brackets) is stripped unconditionally, so prefer that
# form in new scripts.
STAGE_CUES = {
    "whispering", "quietly", "softly", "loudly", "a pause", "shouting",
    "gently", "slowly", "sadly", "brightly", "flatly", "under her breath",
    "under his breath", "to herself", "to himself", "calling", "muttering",
}

PAUSE_MS = 350          # silence inserted between speaker turns
CACHE_DIR = Path(".narrate-cache")

# ---- podcast feed -------------------------------------------------------
# BASE_URL is where the audio folder ends up once published. For GitHub Pages
# a project site lives at https://<user>.github.io/<repo>/
BASE_URL = "https://andrewcws.github.io/quiet-trails-packs/audio"
SHOW_TITLE = "Stories from the Road"
SHOW_DESCRIPTION = ("Short adventure stories about the places we go. "
                    "Made for the car.")
SHOW_AUTHOR = "The Hicks family"
SHOW_IMAGE = "cover.jpg"        # 1400x1400 min, sits next to index.xml
SEASON = 1                      # bump this per trip
SEASON_NAME = "Ganguddy"

# ---------------------------------------------------------------- parsing

TAG_INLINE = re.compile(r"^\*\*([A-Z][A-Z ]*):\*\*\s*(.*)$")
HEADING = re.compile(r"^(#{1,3})\s+(.*)$")


def clean_line(text):
    """Strip markdown emphasis, bracketed directions, and leading stage cues."""
    text = re.sub(r"\([^)]*\)", "", text)          # (whispering)
    text = re.sub(r"\[[^\]]*\]", "", text)         # [whispering]

    # A leading *italic phrase.* that matches a known cue is a direction.
    m = re.match(r"^\s*\*([^*]{1,40}?)\*\s*(.*)$", text)
    if m:
        cue = m.group(1).strip().rstrip(".").lower()
        if cue in STAGE_CUES:
            text = m.group(2)

    text = text.replace("*", "")                   # remaining emphasis marks
    text = text.replace("—", ", ")                 # em dash reads as a gap
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)   # " ," left by a trailing dash
    text = re.sub(r",\s*$", ".", text)             # don't end a block on a comma
    text = re.sub(r"([,.;:!?]){2,}", r"\1", text)
    return text.strip()


STORY_NUM = re.compile(r"^Story\s+(\d+)\s*[—–-]?\s*")


def story_number(title, fallback):
    """Episode number from the heading ("Story 12 — ..." -> 12).

    Taken from the title rather than the run order so a story keeps the same
    number whether it is generated alone or with the whole pack.
    """
    m = STORY_NUM.match(title)
    return int(m.group(1)) if m else fallback


def display_title(title):
    """Heading without its "Story N —" prefix, for filenames and ID3."""
    return STORY_NUM.sub("", title).strip()


def script_files(paths):
    """Expand each argument, turning a directory into its sorted .md files."""
    out = []
    for raw in paths:
        p = Path(raw)
        out.extend(sorted(p.glob("*.md")) if p.is_dir() else [p])
    return out


def slugify(title):
    s = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-")[:60]


def parse(path):
    """Return [(story_title, [(speaker, text), ...]), ...]."""
    stories, blocks, title = [], [], None
    speaker, buffer = None, []

    def flush_block():
        nonlocal speaker, buffer
        if speaker and buffer:
            text = clean_line(" ".join(buffer))
            if text:
                blocks.append((speaker, text))
        speaker, buffer = None, []

    def flush_story():
        nonlocal blocks, title
        if title and blocks:
            stories.append((title, blocks))
        blocks = []

    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        h = HEADING.match(line)
        if h:
            flush_block()
            level, heading_text = len(h.group(1)), h.group(2).strip()
            if level == 1:
                flush_story()
                title = heading_text
            else:
                # A subheading ends the current story's dialogue.
                flush_story()
                title = None
            continue

        if set(line) <= {"-"} and line:
            flush_block()          # horizontal rule ends a block
            continue

        if not line:
            # Blank line is a paragraph break within the same speaker's turn,
            # not a change of speaker. Dropping the speaker here silently
            # loses every paragraph after the first.
            if speaker and buffer:
                buffer.append("\n")
            continue

        m = TAG_INLINE.match(line)
        if m:
            name, rest = m.group(1).strip(), m.group(2).strip()
            if name in SPEAKERS:
                flush_block()
                speaker = name
                if rest:
                    buffer.append(rest)
            else:
                flush_block()          # metadata line — ignore
            continue

        if speaker:
            buffer.append(line)

    flush_block()
    flush_story()
    return stories

# ---------------------------------------------------------------- tts

def voice_for(speaker, provider, single_voice):
    table = ELEVENLABS_VOICES if provider == "elevenlabs" else FISH_VOICES
    if single_voice:
        return table["NARRATOR"]
    return table.get(speaker, table["NARRATOR"])


def synth_elevenlabs(text, voice_id, key):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={"text": text, "model_id": ELEVENLABS_MODEL},
        timeout=180,
    )
    r.raise_for_status()
    return r.content


def synth_fish(text, reference_id, key):
    r = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "model": FISH_MODEL,
        },
        json={"text": text, "reference_id": reference_id, "format": "mp3"},
        timeout=180,
    )
    r.raise_for_status()
    return r.content


def synth(text, voice_id, provider, key):
    """Generate one clip, caching by hash so re-runs cost nothing."""
    CACHE_DIR.mkdir(exist_ok=True)
    stamp = hashlib.sha256(
        f"{provider}|{voice_id}|{ELEVENLABS_MODEL}|{FISH_MODEL}|{text}".encode()
    ).hexdigest()[:20]
    cached = CACHE_DIR / f"{stamp}.mp3"
    if cached.exists():
        return cached.read_bytes()

    audio = (synth_elevenlabs if provider == "elevenlabs" else synth_fish)(
        text, voice_id, key
    )
    cached.write_bytes(audio)
    return audio

# ---------------------------------------------------------------- joining

def join(clips, out_path, album=None, title=None, track=None):
    """Join MP3 clips. Uses pydub for clean joins with pauses if available,
    otherwise concatenates the bytes, which plays fine in every player I know
    of but gives you no control over gaps."""
    try:
        from pydub import AudioSegment
        import io

        combined = AudioSegment.empty()
        gap = AudioSegment.silent(duration=PAUSE_MS)
        for i, clip in enumerate(clips):
            if i:
                combined += gap
            combined += AudioSegment.from_file(io.BytesIO(clip), format="mp3")
        combined.export(out_path, format="mp3", bitrate="128k")
    except Exception:
        out_path.write_bytes(b"".join(clips))

    tag(out_path, album, title, track)


def tag(path, album, title, track):
    """Write ID3 tags so the car stereo shows a real title, not 'Track 01'."""
    if not title:
        return
    try:
        from mutagen.easyid3 import EasyID3
        from mutagen.mp3 import MP3

        try:
            audio = EasyID3(path)
        except Exception:
            audio = MP3(path)
            audio.add_tags()
            audio = EasyID3(path)

        audio["title"] = title
        audio["album"] = album or "The Ganguddy Stories"
        audio["artist"] = "The Ganguddy Stories"
        audio["albumartist"] = "The Ganguddy Stories"
        if track:
            audio["tracknumber"] = str(track)
        audio.save()
    except ImportError:
        pass

# ---------------------------------------------------------------- feed

def duration_of(path):
    """Seconds of audio, for the feed. Falls back to a bitrate estimate."""
    try:
        from mutagen.mp3 import MP3
        return int(MP3(path).info.length)
    except Exception:
        return int(path.stat().st_size / 16000)   # ~128kbps


def hhmmss(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def write_feed(out_dir, base_url=None):
    """Write index.xml listing every mp3 in out_dir, newest episode first.

    Rebuilt from the folder each run, so adding a new trip's files and
    re-running picks everything up. Publication dates are spaced a day apart
    in track order so podcast apps keep them in the right sequence.
    """
    from email.utils import formatdate
    from xml.sax.saxutils import escape
    import time

    base = (base_url or BASE_URL).rstrip("/")
    files = sorted(Path(out_dir).glob("*.mp3"))
    if not files:
        return None

    now = time.time()
    items = []
    for i, f in enumerate(files):
        prefix, _, rest = f.stem.partition("-")
        episode = int(prefix) if prefix.isdigit() else i + 1
        title = rest.replace("-", " ").title()
        try:
            from mutagen.easyid3 import EasyID3
            tags = EasyID3(f)
            title = tags.get("title", [title])[0]
        except Exception:
            pass

        secs = duration_of(f)
        pub = formatdate(now - (len(files) - i) * 86400, usegmt=True)
        items.append(f"""    <item>
      <title>{escape(title)}</title>
      <itunes:episode>{episode}</itunes:episode>
      <itunes:season>{SEASON}</itunes:season>
      <itunes:duration>{hhmmss(secs)}</itunes:duration>
      <guid isPermaLink="false">{escape(base)}/{f.name}</guid>
      <pubDate>{pub}</pubDate>
      <enclosure url="{escape(base)}/{f.name}" length="{f.stat().st_size}" type="audio/mpeg"/>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{escape(SHOW_TITLE)}</title>
    <link>{escape(base)}/</link>
    <description>{escape(SHOW_DESCRIPTION)}</description>
    <language>en-au</language>
    <itunes:author>{escape(SHOW_AUTHOR)}</itunes:author>
    <itunes:explicit>false</itunes:explicit>
    <itunes:image href="{escape(base)}/{SHOW_IMAGE}"/>
    <itunes:category text="Kids &amp; Family"/>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""
    feed = Path(out_dir) / "index.xml"
    feed.write_text(xml, encoding="utf-8")
    return feed

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="+",
                    help="script .md file(s), or a directory of them")
    ap.add_argument("--provider", choices=["elevenlabs", "fish"], default="elevenlabs")
    ap.add_argument("--out", default="audio")
    ap.add_argument("--single-voice", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="parse and report only — no API calls, no cost")
    ap.add_argument("--feed-only", action="store_true",
                    help="rebuild index.xml from existing mp3s, generate nothing")
    ap.add_argument("--base-url", help="overrides BASE_URL for the feed")
    args = ap.parse_args()

    if args.feed_only:
        feed = write_feed(args.out, args.base_url)
        print(f"Wrote {feed}" if feed else f"No mp3 files in {args.out}")
        return

    stories = [st for f in script_files(args.script) for st in parse(f)]
    if not stories:
        sys.exit("No speaker-tagged stories found.")

    if args.dry_run:
        grand = 0
        for title, blocks in stories:
            chars = sum(len(t) for _, t in blocks)
            grand += chars
            speakers = sorted({s for s, _ in blocks})
            print(f"\n{title}")
            print(f"  {len(blocks)} blocks · {chars:,} characters "
                  f"· ~{chars/1000:.1f} min · speakers: {', '.join(speakers)}")
            for spk, text in blocks[:3]:
                print(f"    {spk}: {text[:70]}...")
        print(f"\nTotal: {grand:,} characters")
        print(f"  ElevenLabs multilingual  ${grand/1000*0.10:.2f}")
        print(f"  ElevenLabs flash         ${grand/1000*0.05:.2f}")
        print(f"  Fish Audio               ${grand/1_000_000*15:.2f}")
        return

    key = os.environ.get(
        "ELEVENLABS_API_KEY" if args.provider == "elevenlabs" else "FISH_API_KEY"
    )
    if not key:
        sys.exit("Set your API key as an environment variable first.")

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    for n, (title, blocks) in enumerate(stories, start=1):
        num, name = story_number(title, n), display_title(title)
        print(f"[{n}/{len(stories)}] {title}")
        clips = []
        for i, (spk, text) in enumerate(blocks, start=1):
            vid = voice_for(spk, args.provider, args.single_voice)
            print(f"    {i}/{len(blocks)} {spk} ({len(text)} chars)")
            clips.append(synth(text, vid, args.provider, key))

        path = out_dir / f"{num:02d}-{slugify(name)}.mp3"
        join(clips, path, album=SEASON_NAME, title=name, track=num)
        print(f"    -> {path}")

    feed = write_feed(out_dir, args.base_url)
    if feed:
        print(f"\nFeed: {feed}")


if __name__ == "__main__":
    main()
