# The Ganguddy Stories — Story Engine v1

A reusable spec for generating short audio stories for family trips.
First destination: **Ganguddy (Dunns Swamp), Wollemi National Park, NSW.**

---

## 0. Tone — the one that overrules the rest

**Everybody should finish a story feeling happy, calm and lifted.** If a rule
below ever fights that, the rule loses.

The failure mode isn't dullness, it's a narrator who judges. It arrives quietly
and it sounds reasonable at the time, so it's worth knowing the specific shapes
it takes:

- **The narrator delivering a verdict on a child.** An early draft had Billy say
  "that's not fair" about the lyrebird and the narrator answer *"It is
  completely fair, and it is completely real."* That's an adult correcting a
  five-year-old for a reasonable reaction, and it was the single most
  off-putting thing in the pilot. Replaced with curiosity — Billy asks *how* it
  does that, Skye recognises the exact sound, Rori says "do it again", and it
  does. Same facts follow, no one is wrong.
- **Curiosity beats correction, every time.** When a child gets something wrong,
  the interesting move is not to correct them. It's to ask what would happen if
  they were right, or to have the world answer instead.
- **The narrator never tells you how to feel about a character.** No "which for
  Billy was a very big deal", no "she should have known better", no summarising
  someone's shortcoming for the listener. Show what they do; let the listener
  decide.
- **A running joke about a real child stops at one.** Two jokes about Skye
  talking too much is where affectionate turns into pointed. These are real kids
  and their parents are in the car.
- **Warm, not mocking.** Skye explaining the beetle situation to everybody in the
  house one at a time is funny *and* she is right. That's the register: the
  laugh never comes at the cost of the child's competence.
- **Nobody is the problem.** Things go wrong because things go wrong. A forgotten
  stick is not a failure of character.
- **Never end on a deficit.** The last thirty seconds are the mission, and the
  mission is an invitation, not homework.

A quick test before a story goes out: if a sentence would make one of the four
children feel got at were they old enough to notice, cut it. Not soften — cut.

---

## 1. Format rules

| Rule | Spec |
|---|---|
| Length | 900–1100 words (~5 min). See pacing note below. |
| Target listener | Smart 5-year-old, with a 2-year-old in the car |
| Speaker tags | `NARRATOR:` and `ECHO:` only. The kids speak inside the narrator's prose, attributed. See *Who is speaking* below. Any other `**ALLCAPS:**` tag is treated as metadata and silently dropped, so the generator warns when it sees one. |
| Stage directions | Round brackets only — `(whispering)`, `(a pause)`. Never italics; the generator strips brackets but italics are ambiguous against emphasis. |
| Fact budget | ~90 words max per story, in no more than 2 chunks, never in the final 60 seconds |
| Fact trigger | **No fact enters a story without a physical object the kids find.** No lecturing. |
| Stretch vocabulary | 2–3 new words per story, each used 3 times in context |
| Magic rule | Exactly one: the lyrebird can replay any sound. Everything else is true. |
| Ending | Every story ends with a **mission**, and the word "mission" is said out loud. Never "here's your first one" — a listener has no idea what "one" refers to, and stories are standalone, so there is no first. "Here's a mission for tonight." Not *task* or *job*; both sound like chores. A mission doesn't have to be doable from a car seat: some are for right now out the window, most are for later at camp, and it's the parents who bring them back up. Write it so it survives being remembered four hours later. |

### Who is speaking

Tested on a five-year-old. She liked both pilots and could not follow either
of them. The scripts were tagged dialogue with no attribution, so one voice
performed four children and nothing marked the handovers.

**Every line a child speaks is attributed, in the narrator's prose.**

```
"There's something there," whispered Rori.
"Well, you scared it," said Billy.
```

Not `**RORI:**`. The tag is invisible in audio; "said Rori" is the only thing
the listener actually receives. This is how audiobooks have always done it,
and the reason is the same: a reader can see who is speaking, a listener
cannot.

Two consequences worth knowing:

- **Echo keeps her own tag and her own voice.** She is the only character who
  gets one. Sounding different is what tells a child she isn't another kid —
  it is her attribution. She still gets introduced in prose the first time.
- **Verse is single voice, always.** In a rhyming story the metre carries the
  listener, and a voice change interrupts it. The narrator speaks every line,
  including the refrains.

It also made the audio better for a reason nobody planned. Story 12 went from
35 clips to 7, and story 1 to a single clip. Fewer clips means fewer joins to
smooth, and the model sees whole paragraphs at once instead of one line — so
it can put the emphasis where the sentence needs it.

### Pacing — measured, not assumed

The original 150 wpm estimate was wrong. Measured against the two pilots on
Fish Audio `s1`:

| | Words | Audio | Rate |
|---|---|---|---|
| Story 12, prose | 920 | 4:36 | **200 wpm** |
| Story 1, verse | 594 | 3:16 | **182 wpm** |

So a real five minutes is about **1000 words of prose** or **900 of verse** —
verse reads slower because the line breaks land as pauses. Synthetic narration
is simply faster than a human reading aloud, and the gap is large enough to
matter: at the old target a "5-minute story" arrives at about 3:30.

Re-measure if the provider or model changes. `--dry-run` estimates characters
and cost, not duration; duration only becomes real once a clip exists.

### Story skeleton

1. **Hook** (50 words) — in motion by the second sentence
2. **Want** — one of the kids wants something small and concrete
3. **Artefact** — they find a thing: a mark, a rust, a scribble, a track
4. **Lyrebird** — appears *only if they've gone still*; plays back what the thing sounds like
5. **Turn** — something goes wrong, or the thing is not what they thought
6. **Resolve** — the key kid's competence solves it
7. **Mission** — lyrebird sets the challenge, 30 seconds, then out

### The feelings layer (light touch)

Never the point of a story. Always underneath it.

**These are guidelines, not rules.** They exist to stop the stories becoming
therapy; followed too literally they will make fifty stories feel like one
story told fifty times. If a story needs to break one, break it. The balance is
the job.

- **Body first, label second.** "Her chest was going fast and her hands wanted to do something" beats "she felt anxious." Kids locate feelings in their bodies before they can name them.
- **One precise feeling word per story. Usually once is enough.** Not "sad" or "cross" — *frustrated, disappointed, nervous, relieved, proud, embarrassed, impatient, jealous*. The three-times rule for stretch vocabulary does **not** carry over here: a stretch word repeated three times teaches, a feeling word repeated three times nags. Twice is fine when the second one earns its place.
- **The little arc is allowed to be visible.** The feeling arrives in the body, it gets named, something the child tries doesn't work, something else does. That sequence is the valuable part and shouldn't be hidden — but it rarely needs all four beats, and two is often plenty. What turns it into a lecture isn't the arc, it's the narrator stopping the story to point at the arc. Show the thing that worked; don't explain that it worked.
- **Nothing is anyone's fault.** The mistake happens, another kid says the unkind true thing, and the story moves on. No narrator explaining what the child should have done instead.
- **Regulation is disguised as bushcraft.** Going still to see an animal, breathing out slowly so you don't scare a fish, counting to three before cold water. Echo never says "calm down" — she says "be still, or she won't come." Same skill, no therapy voice.
- **Not every feeling resolves.** Roughly one story in six should end with someone still a bit disappointed. Nobody learns a lesson out loud.
- **Ratio target across 50:** a feeling is *noticed* in about half, *named* in about a third, and *talked about* in maybe four.
- **Banned:** "big feelings", "use your words", "let's take a deep breath together", any adult explaining an emotion to a child, and any sentence that would work unchanged as a caption on a parenting infographic.

---

## 2. Character bible

**On the word "flaw".** These are real children and their parents are in the
car. Nobody should hear their kid's shortcoming announced and repeated fifty
times. So: tendencies, not flaws. A tendency is **shown by what the child does
and never named by the narrator**, it is what makes the plot happen rather than
a lesson attached to the plot, and no child carries the same one in every
story. Some stories a child is simply competent and it is somebody else's turn.

### Rori — 5 — the brave one
*Aurora. Traits from her parents: energetic, curious, funny, brave, protective
of her sister.*

- **Competence:** courage. First into the cold water, the dark, the narrow gap.
- **Also:** she *notices*. She sees the thing.
- **Protective of Adi.** Her bravery has a reason standing behind it — she goes
  first partly so her little sister doesn't have to. Use this rather than
  making her merely fearless.
- Funny on purpose, not by accident. She knows when she's being funny.
- **Tendency:** she moves too fast when she sees it, and it slips away.
- **Series arc:** learning to go still. This is the spine of the whole collection.
- **Dynamic with Billy:** they race. Constantly. It is even, affectionate and funny, and it is not a flaw in either of them.
- **Catchphrase shape:** "I saw it. I *saw* it."

### Billy — 5 — the other brave one
*Traits from his parents: curious, strong, thoughtful, silly and kind.*

- Matched pair with Rori, deliberately. Same age, same nerve.
- **Differentiated by kind of bravery:** Rori's is physical (heights, cold, dark). Billy's is strong and steady — he'll carry the heavy thing, go and ask, stay when it would be easier to leave.
- **Competence:** preparation, which comes out of being curious. He wanted to know what it would be like, so he thought it through, so he brought the thing nobody else thought of.
- **Tendency:** thoughtful takes time. Occasionally he's still working it out while everyone else has gone.
- **Silly on purpose.** He is not only the careful one. He does the ridiculous thing knowingly, usually right after the serious thing, and it's often what breaks a tense moment.
- **Kind:** he notices who needed it more, and hands it over without making a speech about it.
- **Dynamic:** races and dares with Rori drive plots — mutual, even, and fun. Competition between them is a *shared engine*, not a fault belonging to either of them. Neither has to lose a lesson at the end of it.

### Skye — 4 — the chatty watcher
*Traits from her parents: cheeky, animated, stubborn, caring and chatty.*

- **Competence:** observation. She sees it first — and now she's likely to say
  so, loudly, about everything except the thing that matters.
- **Tendency:** she has a lot to say, so the one thing that turns out to
  matter arrives in the middle of a great deal else and nobody catches it
  until later. Played as comedy and as competence — she *did* tell them — never
  as a fault.
- **Stubborn:** once she has decided a thing is so, it is so. Sometimes she's right.
- **Series arc:** her voice gets louder. By the late stories she's the one who stops the others.
- She and the lyrebird understand each other — both quiet, both watchful.

### Adi — 2 — the namer
*Adeline. Traits from her parents: happy, cheeky, funny, cuddly and independent.*

- **Competence:** she points and names the animal. Correctly. Every time.
- **Independent:** she does things herself, badly and completely. The bag she
  packed alone is the model — nobody asked her to, and she is not sorry.
- Vocabulary of maybe eight words, deployed devastatingly.
- The comic engine and, roughly one story in five, the accidental key.
- Anchor of all refrain stories.

### The Lyrebird — the guide
**Name: Echo.**

Note: Echo is a *character*, not the narrator. NARRATOR carries stories 1–11 and sets those missions. The kids don't meet Echo until story 12; from then on she sets the missions herself. This is what makes the two-voice split work later.

- **What she is:** a superb lyrebird. Shy, ground-dwelling, weak flier, scratches in leaf litter.
- **Her gift:** she replays sounds. Real lyrebirds learn mimicry from *other lyrebirds*, and repertoires pass down through generations with little change over decades — so she isn't remembering, she's carrying a sound handed down a chain of birds.
- **Her rule:** she will not appear to noisy children. Stillness summons her. This is the patience-teaching mechanism, built into the format.
- **Her voice:** never explains before she shows. Gets things slightly wrong so the kids can correct her. Answers questions with questions.
- **What she won't do:** tell Dreaming stories. She says plainly that some stories belong to the people of this Country and aren't hers to tell — and that this is a good thing, not a sad one.

---

## 3. Story arcs

1. Quest — go and find the thing
2. Overcoming fear
3. Small-one-saves-the-day
4. Voyage and return
5. Mystery — whose track, what made this mark
6. Trickster
7. Transformation — literal, for insects and frogs
8. Unlikely friendship
9. Time-slip — the lyrebird plays the past
10. Survival — weather, cold, lost
11. Race / competition
12. Patience — nothing happens until they stop moving *(the house special)*
13. How-it-works, told as adventure

**Modes:** Prose (default) · Refrain (Adi-led, short, repeated line to shout)

**Rhyming mode is retired.** The pilot held its metre on paper and lost it in
synthesis — the model reads verse as sentences, and the anapaests flatten into
prose with odd pauses where the line breaks were. Two adults and a five-year-old
agreed independently. Story 1's plot survived and was rewritten as prose; the
other rhyming rows in the matrix have been switched to Prose. Revisit only if a
future model actually performs metre.

---

## 4. Categories, with verified local hooks

| Code | Category | Anchor facts |
|---|---|---|
| **A** | Trip prep & logistics | Packing, the list, drinking water isn't provided, bring your own firewood, no bins |
| **B** | Water & the weir | Not a swamp. Kandos Weir, late 1920s/1930, built to supply the Kandos cement works. The Cudgegong River backed up behind it |
| **C** | Animals | Platypus and long-necked turtles in the weir, greater gliders at night, wallabies, yabbies |
| **D** | Birds | Purple swamphens, kookaburras, wedge-tailed eagles, the lyrebird herself |
| **E** | Insects & small things | Scribbly gum moth caterpillars, dragonflies, ants, spider webs at dawn |
| **F** | Plants | Scribbly gum woodland. Wollemi pine — known only from fossils until a ranger abseiled into a canyon in this park in 1994 |
| **G** | Rock & geology | Triassic sandstone ~200 my. Hard ironstone bands weather slower than soft sandstone → the beehive steps. Vertical cracks split blocks; water rounds the tops |
| **H** | Weather & sky | Frost, cold air sinking into the valley, fog on the water at dawn, dark-sky stars |
| **I** | Aboriginal culture & Country | Ganguddy, Dabee People of the Wiradjuri Nation. 120+ Aboriginal sites in Wollemi. Red ochre hand stencils thought to be 7,000+ years old. Grinding grooves, scarred trees |
| **J** | European history | Dunn brothers built a cottage and shearing shed there in 1877 — hence "Dunns Swamp". Sheep, wool, shearing |
| **K** | Modern history & fire | Around 90% of the park burned in the 2019–20 Gospers Mountain fire. Firefighters were winched into a canyon with irrigation lines to save the last wild Wollemi pines. Regrowth since |
| **M** | Camp craft | Setting up, fire, cooking, washing up, the long drop, torches, night sounds |
| **L** | Activities & games | Swimming, kayaking, fishing, damper, marshmallows, skimming stones, cubbies, tree and pagoda climbing, mud dams, painting rocks and bark, ochre and charcoal drawing, night walks |

---

## 5. The 50-story matrix

**Act I — Getting Ready (1–5)** · **Act II — The Drive (6–12)** · **Act III — At Camp (13–44)** · **Act IV — Going Home (45–50)**

| # | Working title | Cat | Arc | Mode | Key kid | Artefact / trigger | Mission |
|---|---|---|---|---|---|---|---|
| 1 | The List | A | How-it-works | Prose | Billy | The packing list | Find one thing that's missing |
| 2 | Too Much Stuff | A | Trickster | Prose | Rori | An overstuffed bag | Choose three things you'd take |
| 3 | Water You Can't Drink | A | How-it-works | Prose | Billy | Empty water container | Count the water bottles |
| 4 | The Wood You Can't Burn | A | Small-one-saves | Prose | Skye | A fallen log full of insects | Look under one log |
| 5 | Adi Packs a Bag | A | — | Refrain | Adi | Everything she owns | Say what Adi packed |
| 6 | Four Hours | A | Voyage & return | Prose | Rori | The odometer | Count the towns |
| 7 | Where the Mountains Go Blue | G | How-it-works | Prose | Billy | Blue haze on the ranges | Spot when the blue starts |
| 8 | The Last Shop | A | Quest | Prose | Billy | Kandos main street | Name the last shop you pass |
| 9 | The Grey Powder Town | B | Time-slip | Prose | Rori | Cement works chimney | Find something made of concrete |
| 10 | The Road That Isn't Sealed | A | Overcoming fear | Prose | Skye | Gravel noise under tyres | Listen for the change |
| 11 | Adi Names Everything | D | — | Refrain | Adi | Roadside animals | Name three animals |
| 12 | The Bird Who Was Waiting | D | Patience | Prose | Rori | First lyrebird sighting | Sit still for one minute |

**Act II-a — Making Camp (C1–C8), numbered 51–58 in the feed.** Slots between
#12 and #13 in listening order, but episode numbers have to be integers and
there are none free between 12 and 13. Written ones took 51–55 rather than
renumbering stories already published, since a podcast app remembers episode
numbers. Stories are standalone, so feed order is cosmetic. If it ever stops
being cosmetic, the fix is to renumber the block to 13–20 and shift 13–50 up by
eight — one pass over this table and the filenames.

Slots between #12 and #13. Highest emotional density in the collection — setting up camp is where tired kids and tired parents collide, so this is where the feelings layer does most of its work.

| # | Working title | Cat | Arc | Mode | Key kid | Artefact / trigger | Mission | Feeling |
|---|---|---|---|---|---|---|---|---|
| C1 | The Box That Turns Into a House | M | How-it-works | Prose | Billy | The camper trailer unfolding | Find the parts that fold | proud |
| C2 | Poles, Pegs and Tangles | M | Overcoming fear | Prose | Rori | A tent pole that won't go | Put in one peg yourself | frustrated |
| C3 | The Fire That Wouldn't Start | M | Patience | Prose | Rori | Smoke, no flame | Gather kindling, thinnest first | impatient |
| C4 | Smoke in Your Eyes | M | — | Refrain | Adi | Bacon on the BBQ | Say what's for breakfast | happy |
| C5 | The Long Drop | M | Overcoming fear | Prose | Skye | The pit toilet | Go once without help | nervous |
| C6 | Torches | M | Overcoming fear | Prose | Billy | A beam in the dark | Turn your torch off for ten seconds | brave |
| C7 | The Washing-Up Song | M | — | Refrain | Adi | A stack of plates | Wash one thing | — |
| C8 | What Was That Noise? | M | Mystery | Prose | Skye | An unexplained sound at night | Name three night sounds | scared → curious |

| 13 | The Rock That Grew Steps | G | Mystery | Prose | Billy | Stepped orange pagoda | Count the layers |
| 14 | Two Hundred Million Mornings | G | Time-slip | Prose | Skye | Ripple marks in sandstone | Find a pattern in the rock |
| 15 | The Handwriting on the Tree | E | Mystery | Prose | Skye | Scribbles on gum bark | Find the longest scribble |
| 16 | Who Ate This? | E | Mystery | Prose | Adi | Chewed seed pod | Find something that's been eaten |
| 17 | The Slide in the Mud | C | Patience | Prose | Rori | Slide mark and bubbles | Watch the water at dusk |
| 18 | The Animal That Broke the Rules | C | How-it-works | Prose | Billy | Platypus | Draw an animal made of parts |
| 19 | Turtle Neck | C | Unlikely friendship | Prose | Skye | A long-necked turtle | Find a shell or a shape like one |
| 20 | The Gliders Come Out | C | Overcoming fear | Prose | Rori | Torchlight eyeshine | Go out after dark |
| 21 | Adi Sees a Wallaby | C | — | Refrain | Adi | A swamp wallaby | Freeze when you see one |
| 22 | The Laughing Family | D | Trickster | Prose | Billy | Kookaburra at breakfast | Laugh back |
| 23 | The Eagle's Ladder | D | Quest | Prose | Rori | A wedge-tail circling | Watch one bird for 2 minutes |
| 24 | Six Legs and a Thousand Eyes | E | Transformation | Prose | Skye | Dragonfly on a reed | Find a shed skin |
| 25 | The Web at Six O'Clock | E | Patience | Prose | Skye | Dew on a web | Look for webs at dawn |
| 26 | The Tree That Came Back | K | Survival | Prose | Rori | Charred trunk, green shoots | Find green on black |
| 27 | The Secret Trees | F | Quest | Prose | Billy | A cone or fossil leaf shape | Draw a tree nobody's seen |
| 28 | The Night They Watered a Canyon | K | Small-one-saves | Prose | Billy | Smoke smell / burnt ridge | Ask what you'd save first |
| 29 | The Rusted Thing | B | Time-slip | Prose | Rori | Rusted machinery | Find something old and made |
| 30 | How to Turn Rock into Stone | B | How-it-works | Prose | Billy | A lump of concrete | Build a mud weir |
| 31 | The Mud Dam | L | Race | Prose | Rori | Wet clay at the edge | Build a dam that holds |
| 32 | The River That Stopped | B | Time-slip | Prose | Skye | Waterline on the rocks | Find the old shoreline |
| 33 | The Wool on the Wire | J | Mystery | Prose | Skye | Wool caught on fence wire | Find something soft outdoors |
| 34 | The Shearing Shed | J | Time-slip | Prose | Billy | Old post and rail | Count the fence posts |
| 35 | Grooves in the Stone | I | Patience | Prose | Rori | Grinding grooves | Look, don't touch |
| 36 | The Hands on the Wall | I | Patience | Prose | Skye | Ochre hand stencils | Trace your hand in the air |
| 37 | Stories That Aren't Ours | I | — | Prose | Rori | The lyrebird refuses | Ask a question, wait for the answer |
| 38 | Ochre, Charcoal, Water | L | How-it-works | Prose | Adi | Charcoal from the fire | Draw with charcoal |
| 39 | The Stone That Skipped Eight | L | Race | Prose | Billy | A flat stone | Beat your own record |
| 40 | Cold Water Courage | L | Overcoming fear | Prose | Rori | The first step in | Count to three, go in |
| 41 | The Paddle and the Wind | L | Voyage & return | Prose | Billy | A kayak turning sideways | Paddle to a landmark |
| 42 | Nothing Is Biting | L | Patience | Prose | Rori | A still float | Wait ten whole minutes |
| 43 | Damper, Ash and Patience | L | How-it-works | Prose | Skye | Dough that isn't ready | Make damper |
| 44 | The House of Sticks | L | Quest | Prose | Adi | A leaning branch | Build a cubby |
| 45 | Frost on the Tent | H | Survival | Prose | Billy | Ice on the fly | Feel the cold air pooling |
| 46 | The Fog That Sat on the Water | H | Patience | Prose | Skye | Dawn fog | Get up before the sun once |
| 47 | The Stars Nobody Owns | H | — | Prose | Rori | Dark sky | Find one constellation |
| 48 | Leave No Trace | A | How-it-works | Prose | Billy | The empty campsite | Find one piece of rubbish |
| 49 | Adi Says Goodbye | C | — | Refrain | Adi | Everything, one last time | Say goodbye to three things |
| 50 | What We Took Home | — | Voyage & return | Prose | Rori | An empty pocket | Tell one person one thing |

---

## 6. Before a story ships — the checklist

Every one of these was learned the expensive way on the two pilots.

1. **Tone.** Re-read section 0. Any narrator verdict on a child? Cut it.
2. **Attribution.** Every line a child speaks says who said it, in the prose.
   Only `NARRATOR:` and `ECHO:` tags exist.
3. **Feeling word** named once, body first. The little arc can show; the
   narrator must not point at it.
4. **Tendencies shown, never announced**, and not the same child every story.
5. **Length** 900–1100 words. Under 900 lands short of five minutes.
6. **Facts** ≤90 words, in ≤2 chunks, each triggered by an object they find,
   never in the last minute.
7. **Stretch words** 2–3, used three times each. Feeling words are exempt.
8. **Mission** at the end, with the word "mission" said aloud, and standalone —
   no "first", no reference to another story.
9. **Sound effects** as `(sfx: key)` inline. Check the key exists in `sfx/`;
   the generator warns but still produces the file without it.
10. **Names** — anything the model is likely to mangle goes in `PRONUNCIATION`
    or `PHONEMES` in `narrate.py`, not respelled in the script.
11. **Listen to it.** Every problem in this document was found by listening, and
    none of them by reading.

---

## 7. Open items

- Confirm Billy's and Skye's ages
- Confirm lyrebirds actually occur at Ganguddy (vs the wetter Wollemi gullies) — if not, keep her as a visitor from the gullies rather than a resident
- ~~Test one rhyming script before committing to the eight rhyming stories~~ — done, verse retired, see *Modes*
- Source the Common Ground Wiradjuri recordings to play alongside these
