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

The feed is at
`https://andrewcws.github.io/quiet-trails-packs/audio/index.xml` —
add it in Apple Podcasts via *Library → ⋯ → Add a Show by URL*.
