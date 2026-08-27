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
import json
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
    "NARRATOR": "aa11a7d54bfd443cab3a8131b956a1bb",
    "ECHO": "04561fb2a7ca4e5b8e6be3885606cda7",
}

ELEVENLABS_MODEL = "eleven_multilingual_v2"   # or "eleven_flash_v2_5" — half price
FISH_MODEL = "s2-pro"                         # "s1" is cheaper and flatter

# Fish takes a speaking-rate multiplier (0.5-2.0). Slightly under 1 reads as
# calmer without sounding slowed down, and calm is the whole brief.
SPEED = 0.93

# Leading italic phrases that are performance directions, not dialogue.
# Everything in (round brackets) is stripped unconditionally, so prefer that
# form in new scripts.
STAGE_CUES = {
    "whispering", "quietly", "softly", "loudly", "a pause", "shouting",
    "gently", "slowly", "sadly", "brightly", "flatly", "under her breath",
    "under his breath", "to herself", "to himself", "calling", "muttering",
}

# Words the model says wrong, respelled for the ear only. The scripts keep
# the real spelling — this is applied to the text on its way to the API, so
# fixing one name here re-generates only the lines that contain it.
# Australian voices are non-rhotic, so an "ar" is a useful way to spell "ah".
PRONUNCIATION = {
    "Adi": "Addie",
}

# Where respelling isn't enough, say it in phonemes instead. Fish s2 takes CMU
# Arpabet between <|phoneme_start|> and <|phoneme_end|>, stress digits included
# (1 primary, 2 secondary, 0 unstressed). ElevenLabs uses an uploaded
# pronunciation dictionary instead, and only on eleven_flash_v2 / eleven_v3, so
# these words fall back to their ordinary spelling there.
#
#   kookaburra  /ˈkʊkəˌbaɹə/  KOOK-uh-burr-uh
PHONEMES = {
    "kookaburra": "K UH1 K AH0 B AH2 R AH0",
}

# Delivery tags the model actually acts on, written inline in scripts as
# [whisper]. Tested against Fish s2-pro on the same sentence: [whisper] was the
# only one anybody could hear. [excited], [gentle], [soft], [sad] and [warm]
# shifted the reading slightly or not at all, and the round-bracket
# paralanguage — (break), (breath) — did nothing whatsoever. (laugh) does
# produce a laugh, but a sarcastic one, which is no use in a story for a
# five-year-old. Add to this set only after hearing it work.
DELIVERY_TAGS = {"whisper"}

# Clips come back from the API with their own leading and trailing silence,
# and it varies — measured across one story, 160-310 ms in front and 100-320
# behind. Adding a fixed gap on top of that gives pauses that swing by a third
# of a second, which is what a sharp or draggy cut actually is. So each clip is
# trimmed to its own speech, levelled, and the pause is put back deliberately.
TRIM_DB = -45           # anything quieter than this counts as silence
KEEP_MS = 25            # breath left either side of the speech, so onsets live
LEVEL_DBFS = -16.0      # every clip lands here — no line jumps out at you
FADE_MS = 12            # kills the click at each edit point
PAUSE_SAME = 260        # beat between two turns by the same speaker
PAUSE_TURN = 500        # beat when the speaker changes
PAUSE_SFX = 320         # air either side of a sound effect
SFX_DBFS = -19.0        # effects sit under the narration, never startle

# Every story opens and closes on Echo's own call. Same two files across all
# fifty, so a child learns the boundary in one listen. Set to None to drop.
OPEN_STING = "lyrebird-call"
CLOSE_STING = "lyrebird-call"
SFX_DIR = Path("sfx")
SFX_MARK = "\x00"      # separates an sfx key from speech inside a block
CACHE_DIR = Path(".narrate-cache")

# ---- podcast feed -------------------------------------------------------
# BASE_URL is where the audio folder ends up once published. For GitHub Pages
# a project site lives at https://<user>.github.io/<repo>/
BASE_URL = "https://andrewcws.github.io/quiet-trails-packs/audio"
SHOW_TITLE = "Quiet Trails"
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
    text = re.sub(r"\(\s*sfx\s*:\s*([a-z0-9-]+)\s*\)",      # (sfx: kookaburra)
                  lambda m: SFX_MARK + m.group(1).lower() + SFX_MARK,
                  text, flags=re.IGNORECASE)
    text = re.sub(r"\([^)]*\)", "", text)          # (whispering)
    text = re.sub(                                 # [whispering], [whisper]
        r"\[([^\]]*)\]",
        lambda m: m.group(0) if m.group(1).strip().lower() in DELIVERY_TAGS else "",
        text)

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
    seen_unknown = set()

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
                if name.isupper() and name not in seen_unknown:
                    seen_unknown.add(name)
                    print(f"  warning: **{name}:** is not a speaker — "
                          f"that line will not be narrated ({Path(path).name})",
                          file=sys.stderr)
            continue

        if speaker:
            buffer.append(line)

    flush_block()
    flush_story()
    return stories

# ---------------------------------------------------------------- tts

def sfx_path(key):
    """First file in sfx/ named after this key, at any depth."""
    for ext in ("mp3", "wav", "m4a", "ogg", "flac"):
        hit = next(SFX_DIR.rglob(f"{key}.{ext}"), None)
        if hit:
            return hit
    return None


def split_sfx(text):
    """Split a block into ("speech", text) and ("sfx", key) pieces."""
    pieces = []
    for i, part in enumerate(text.split(SFX_MARK)):
        part = part.strip()
        if not part:
            continue
        pieces.append(("sfx", part) if i % 2 else ("speech", part))
    return pieces


def voice_for(speaker, provider, single_voice):
    table = ELEVENLABS_VOICES if provider == "elevenlabs" else FISH_VOICES
    if single_voice:
        return table["NARRATOR"]
    return table.get(speaker, table["NARRATOR"])


def check(r, provider):
    """raise_for_status, but with the provider's reason attached.

    Both APIs explain themselves in the response body — quota exhausted,
    voice not available on this plan, key not activated. Without this you
    just get a bare status code and have to guess.
    """
    if r.ok:
        return r
    try:
        detail = json.dumps(r.json(), separators=(", ", ": "))
    except ValueError:
        detail = r.text[:400]
    sys.exit(f"{provider} returned {r.status_code}: {detail}")


def elevenlabs_quota(key):
    """Characters left this period, or None if the endpoint won't say."""
    try:
        d = requests.get("https://api.elevenlabs.io/v1/user/subscription",
                         headers={"xi-api-key": key}, timeout=30).json()
        return d["tier"], d["character_limit"] - d["character_count"]
    except Exception:
        return None


def synth_elevenlabs(text, voice_id, key, model=ELEVENLABS_MODEL):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={"text": text, "model_id": model},
        timeout=180,
    )
    return check(r, "ElevenLabs").content


def synth_fish(text, reference_id, key, model=FISH_MODEL, speed=SPEED):
    r = requests.post(
        "https://api.fish.audio/v1/tts",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "model": model,
        },
        json={"text": text, "reference_id": reference_id, "format": "mp3",
              "prosody": {"speed": speed}},
        timeout=180,
    )
    return check(r, "Fish Audio").content


def say_as(text, provider="fish"):
    """Respell the text being spoken, leaving the script itself alone."""
    for word, spoken in PRONUNCIATION.items():
        text = re.sub(rf"\b{re.escape(word)}\b", spoken, text)
    if provider != "fish":
        # Only Fish acts on these; anywhere else they would be read out loud.
        text = re.sub(r"\[[^\]]*\]\s*", "", text)
    if provider == "fish":
        for word, arpabet in PHONEMES.items():
            text = re.sub(rf"\b{re.escape(word)}\b",
                          f"<|phoneme_start|>{arpabet}<|phoneme_end|>",
                          text, flags=re.IGNORECASE)
    return text


def synth(text, voice_id, provider, key, model=None, speed=None):
    """Generate one clip, caching by hash so re-runs cost nothing."""
    CACHE_DIR.mkdir(exist_ok=True)
    text = say_as(text, provider)
    # Both model names go into the hash so that the default arguments produce
    # the same digest they always have — an override only invalidates the
    # provider it applies to, never the clips you have already paid for.
    el = model if provider == "elevenlabs" and model else ELEVENLABS_MODEL
    fi = model if provider == "fish" and model else FISH_MODEL
    rate = speed if speed is not None else SPEED
    stamp = hashlib.sha256(
        f"{provider}|{voice_id}|{el}|{fi}|{rate}|{text}".encode()
    ).hexdigest()[:20]
    cached = CACHE_DIR / f"{stamp}.mp3"
    if cached.exists():
        return cached.read_bytes()

    resolved = model or (ELEVENLABS_MODEL if provider == "elevenlabs" else FISH_MODEL)
    if provider == "fish":
        audio = synth_fish(text, voice_id, key, resolved, rate)
    else:
        audio = synth_elevenlabs(text, voice_id, key, resolved)
    cached.write_bytes(audio)
    return audio

# ---------------------------------------------------------------- joining

def dress(seg, level=LEVEL_DBFS):
    """Trim a clip to its own sound, level it, and fade its edges."""
    from pydub.silence import detect_leading_silence

    lead = detect_leading_silence(seg, silence_threshold=TRIM_DB)
    tail = detect_leading_silence(seg.reverse(), silence_threshold=TRIM_DB)
    if lead + tail < len(seg):                      # not silence all the way
        seg = seg[max(0, lead - KEEP_MS):len(seg) - max(0, tail - KEEP_MS)]
    if seg.dBFS != float("-inf"):
        seg = seg.apply_gain(level - seg.dBFS)
    return seg.fade_in(FADE_MS).fade_out(FADE_MS)


def join(items, out_path, album=None, title=None, track=None):
    """Join a story's pieces into one file.

    `items` is a list of (kind, speaker, payload): kind is "speech" with MP3
    bytes, or "sfx" with a Path. Pauses follow the dialogue — shorter between
    two turns by the same speaker, longer when it changes, and a little air
    either side of an effect.

    Falls back to raw byte concatenation if pydub is unavailable — that plays
    in every player I know of, but the gaps and levels are whatever the API
    happened to return, so it says so rather than failing quietly.
    """
    try:
        from pydub import AudioSegment
        import io
    except ImportError as e:
        print(f"    warning: {e} — joining without pauses or levelling",
              file=sys.stderr)
        out_path.write_bytes(b"".join(d for k, _, d in items if k == "speech"))
        tag(out_path, album, title, track)
        return

    combined = AudioSegment.empty()
    previous = None
    for kind, speaker, payload in items:
        if previous is not None:
            if kind == "sfx" or previous[0] == "sfx":
                gap = PAUSE_SFX
            elif speaker == previous[1]:
                gap = PAUSE_SAME
            else:
                gap = PAUSE_TURN
            combined += AudioSegment.silent(duration=gap)

        if kind == "sfx":
            combined += dress(AudioSegment.from_file(payload), level=SFX_DBFS)
        else:
            combined += dress(AudioSegment.from_file(io.BytesIO(payload),
                                                     format="mp3"))
        previous = (kind, speaker)

    combined.export(out_path, format="mp3", bitrate="128k")
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
      <title>{episode}. {escape(title)}</title>
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
    <itunes:type>serial</itunes:type>
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
    ap.add_argument("--speed", type=float,
                    help=f"speaking rate multiplier, 0.5-2.0 (default {SPEED})")
    ap.add_argument("--model", help="override the provider's model for this run"
                                    " (e.g. s2-pro, eleven_flash_v2_5)")
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
            chars = sum(len(p) for _, t in blocks
                        for k, p in split_sfx(t) if k == "speech")
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

    needed = sum(len(t) for _, blocks in stories for _, t in blocks)
    if args.provider == "elevenlabs":
        quota = elevenlabs_quota(key)
        if quota:
            tier, left = quota
            print(f"ElevenLabs: {tier} tier, {left:,} characters left, "
                  f"{needed:,} needed")
            if left < needed:
                sys.exit("Not enough quota. Add credit, or use --provider fish.")

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    for n, (title, blocks) in enumerate(stories, start=1):
        num, name = story_number(title, n), display_title(title)
        print(f"[{n}/{len(stories)}] {title}")
        items = []

        def add_sfx(key_name):
            found = sfx_path(key_name)
            if found:
                items.append(("sfx", None, found))
            else:
                print(f"    warning: no sound file named {key_name} in {SFX_DIR}/",
                      file=sys.stderr)

        if OPEN_STING:
            add_sfx(OPEN_STING)
        for i, (spk, text) in enumerate(blocks, start=1):
            vid = voice_for(spk, args.provider, args.single_voice)
            for kind, payload in split_sfx(text):
                if kind == "sfx":
                    print(f"    {i}/{len(blocks)} sfx: {payload}")
                    add_sfx(payload)
                else:
                    print(f"    {i}/{len(blocks)} {spk} ({len(payload)} chars)")
                    items.append(("speech", spk,
                                  synth(payload, vid, args.provider, key,
                                        args.model, args.speed)))
        if CLOSE_STING:
            add_sfx(CLOSE_STING)

        path = out_dir / f"{num:02d}-{slugify(name)}.mp3"
        join(items, path, album=SEASON_NAME, title=name, track=num)
        print(f"    -> {path}")

    feed = write_feed(out_dir, args.base_url)
    if feed:
        print(f"\nFeed: {feed}")


if __name__ == "__main__":
    main()
