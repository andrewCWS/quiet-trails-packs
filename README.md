# Quiet Trails — trip packs

Content pipeline for [Quiet Trails](https://github.com/andrewCWS): tagged
markdown story scripts in, narrated MP3s and a podcast feed out.

The first pack is **Ganguddy** (Dunns Swamp, Wollemi NP) — short place-based
stories for the drive, each ending in a look-out-the-window mission.

This is a content repo. It contains no app code and depends on no app repo.

```bash
python narrate.py scripts/stories --dry-run       # parse + cost, no API calls
python narrate.py scripts/stories --single-voice  # generate
```

See `CLAUDE.md` for setup, script conventions and current tasks.

## Listening

**<https://andrewcws.github.io/quiet-trails-packs/>** — send that to anyone who
wants the pack. It has the feed address with a copy button and the steps for
iPhone and Android. The full story list is at
[/stories.html](https://andrewcws.github.io/quiet-trails-packs/stories.html).

The feed itself is
`https://andrewcws.github.io/quiet-trails-packs/audio/index.xml`.
