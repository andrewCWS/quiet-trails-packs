# Ganguddy Story Pack — working notes

Content pipeline for **Quiet Trails**. Turns tagged markdown story scripts into
audio files, plus a podcast RSS feed for immediate use in the car.

This folder is a *content* repo, not app code. It has no dependency on the
Quiet Trails app repos and should never contain app code. Equally, the MP3s
should never be committed to either Quiet Trails repo — git keeps every version
of every binary forever.

---

## Immediate goal

A family camping trip to Ganguddy (Dunns Swamp), Wollemi NP, leaving in ~2 days.
Four hours each way. Needs: enough 5-minute stories to make the drive good, in a
form playable offline in the car.

**This weekend's target is audio in a car, not a finished system.** Ship the
crude version. The app is the real destination and is not on this timeline.

---

## Files

| File | What it is |
|---|---|
| `narrate.py` | Parses scripts, calls a TTS API, joins clips, writes `index.xml` |
| `scripts/ganguddy-story-engine-v1.md` | The spec: format rules, character bible, arcs, 50-story matrix |
| `scripts/stories/NN-slug.md` | One story per file. `NN` is its number in the matrix |
| `scripts/pilot-test-checklist.md` | What to listen for in the first generation |
| `audio/` | Generated MP3s + `index.xml` — committed, served by Pages |

Repo: <https://github.com/andrewCWS/quiet-trails-packs>, public, Pages from
main/root. The feed lives at
`https://andrewcws.github.io/quiet-trails-packs/audio/index.xml`.

Audio is committed because Pages serves from the repo. That is a deliberate
two-day tradeoff, not the end state — the MP3s belong in Cloud Storage once
the app is real, and they still must never enter either Quiet Trails app repo.

---

## Setup

```bash
cd ~/ganguddy
source .venv/bin/activate
pip install requests pydub mutagen
brew install ffmpeg          # optional — only for clean joins with pauses
export ELEVENLABS_API_KEY=sk_...
```

`.gitignore` must contain `.venv/` and `.narrate-cache/`.

**Never put an API key in `narrate.py`.** Keys come from the environment. Voice
IDs go in the file; keys do not. The repo will be public.

## Commands

```bash
python narrate.py scripts/stories --dry-run                  # parse + cost, no API calls
python narrate.py scripts/stories --single-voice             # generate the whole pack
python narrate.py scripts/stories/01-the-list.md             # just one story
python narrate.py x --feed-only --out audio                  # rebuild index.xml only
```

A script argument can be a file or a directory; a directory expands to its
sorted `*.md`. Episode numbers come from the `# Story N —` heading, not from
run order, so a story keeps its number whether generated alone or with the
pack.

Clips are cached by content hash in `.narrate-cache/`, so re-running after an
edit only regenerates changed lines. Tweaking one sentence costs one sentence.

Verified: the two pilots parse to 35 and 36 speaker blocks, 7,791 characters
total — about $0.78 on ElevenLabs multilingual, $0.39 on Flash, $0.12 on Fish.

---

## Script conventions

These are load-bearing — the parser depends on them.

- Speaker tags are `**NARRATOR:**` and `**ECHO:**`. The kids' dialogue lives
  inside the narrator's prose, attributed — `"There's something there,"
  whispered Rori.` A five-year-old could not follow the earlier tagged-dialogue
  version; the tag is invisible in audio. Verse stories are single voice
  throughout. Full reasoning in the spec under *Who is speaking*.
- `**RORI:**`, `**BILLY:**`, `**SKYE:**`, `**ADI:**` and `**ALL:**` are still
  accepted by the parser but no longer used. Anything else in `**Bold:**` form
  is treated as metadata and ignored, which keeps header lines out of the
  audio — the parser warns on unknown all-caps tags.
- Stage directions in `(round brackets)` only. Never italics — italics are
  ambiguous against emphasis. `(whispering)` is stripped; `*that's not a number*`
  is dialogue and must survive.
- A tag can be inline (`**RORI:** Are we here?`) or on its own line with the
  speech beneath it (used by the rhyming scripts).
- Blank lines are paragraph breaks *within* a speaker's turn, not speaker
  changes. An earlier bug dropped every paragraph after the first — don't
  reintroduce it.
- `#` headings start a new story. `##` ends the dialogue section.
- The heading is `# Story N — Title`. `N` becomes the episode number and the
  `NN-` filename prefix; the title after the dash becomes the ID3 title.

---

## Open tasks

1. ~~Pick voices.~~ Done — Australian narrator and Echo IDs are in
   `ELEVENLABS_VOICES` and `FISH_VOICES` at the top of `narrate.py`. Whether
   they *sound* right is question 2.
2. Generate both pilots single-voice first. **Test whether two voices are needed
   at all** — if the narrator's Echo is distinct enough, the whole
   multi-voice/joining problem disappears.
3. Check the rhyming pilot holds its metre. TTS tends to flatten verse. If it
   fails, the eight rhyming stories in the matrix need rethinking before they're
   written.
4. Write the remaining stories against the matrix in the spec.
5. Publish: new public repo, MP3s + `index.xml` + `cover.jpg` (≥1400x1400) +
   empty `.nojekyll`, GitHub Pages from main/root. Set `BASE_URL` to the
   published URL, rebuild the feed, upload. Subscribe via
   *Apple Podcasts → Library → ⋯ → Add a Show by URL*.

---

## Relationship to Quiet Trails

The Ganguddy 50 is the first trip pack. Alignments already in place:

- Every story ends with a **mission** — that's the look-out-the-window prompt.
- One magic rule, everything else factually true and specific to this place.
- Calm by default: the guide character only appears when the kids are still,
  so patience is the format's mechanic rather than a message.

**Unresolved:** Quiet Trails specifies 30-minute stories in 6 chapters; this
engine produces 5-minute standalones. Six of ours is one of those, and the act
structure already groups that way (Getting Ready 5 · The Drive 7 · Making Camp 8
· At Camp 32 · Going Home 6). Decide deliberately which is canonical.

**Next structural step:** have `narrate.py` emit a JSON manifest alongside the
RSS — titles, durations, categories, missions, chapter grouping. That manifest is
the bridge to the app. RSS is the throwaway; the manifest is not.

Also unresolved, and not urgent: there are two Quiet Trails repos, an Expo
native app and a Firebase PWA. Two different products. That fork needs closing
eventually.

---

## Story engine, in brief

Full detail in `scripts/ganguddy-story-engine-v1.md`. The essentials:

- 600–1000 words, ~5 min. Smart 5-year-old, 2-year-old in the back.
- **No fact enters a story without a physical object the kids find.** Rusted
  machinery, a charred trunk with green shoots, scribbles on gum bark. Never
  lecture.
- ~90 words of fact max, in ≤2 chunks, never in the final minute.
- 2–3 stretch words per story, each used 3 times.
- One precise feeling word per story, out of the same vocabulary budget. Body
  sensation first, label second. Regulation disguised as bushcraft — Echo says
  "be still or she won't come", never "calm down".
- Cast: Rori 5 (courage, moves too fast — her arc is learning to go still),
  Billy 5 (preparation, wants to be first), Skye 4 (observation, doesn't speak
  up), Adi 2 (names the animal, correctly, every time). Echo the lyrebird
  guides, and only appears to children who have gone quiet.
- Echo will not tell Dreaming stories. She says plainly that some stories belong
  to the people of this Country and aren't hers to tell. Play the Common Ground
  Wiradjuri recordings alongside these instead.
