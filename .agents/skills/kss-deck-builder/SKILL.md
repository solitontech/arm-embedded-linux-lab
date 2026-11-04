---
name: kss-deck-builder
description: Build a KSS two-window deck from an approved STORY.md — translate each story beat into an audience step (title + dg-* diagram + caption + rail chips) and presenter cues in deck.js, using the morph pattern, the visual pattern library, and the scaffold/check tooling under docs/kss/_shared/.
---

# KSS Deck Builder

## Purpose
Turn a reviewed `STORY.md` into a working deck: **diagrams for the audience window, prose for the presenter window, spoken cues for the presenter only**. This skill is the mechanical half; [`kss-storytelling`](../kss-storytelling/SKILL.md) is the editorial half (what to include, what to cut, which channel). Use both.

## When to Use This Skill
- A `STORY.md` has status *Reviewed and approved* and needs a `deck.js`
- Adding or reshaping steps in an existing deck
- Choosing a diagram shape for a concept
- Deciding whether two steps should morph or cut
- Diagnosing a deck that shows the red error banner or fails `check.py`

## Prerequisites
- Contract and primitive catalogue: [`docs/kss/_shared/COMPONENTS.md`](../../../docs/kss/_shared/COMPONENTS.md)
- Reference deck to copy patterns from: [`docs/kss/session-01-boot-flow/deck.js`](../../../docs/kss/session-01-boot-flow/deck.js)
- Tooling (all zero-dependency Python 3):
  - `docs/kss/_shared/new_session.py NN slug --title "…"` — scaffold a session
  - `docs/kss/_shared/build_deck.py session-NN-slug` — regenerate presenter notes from `STORY.md`
  - `docs/kss/_shared/check.py` — structural checks; run before every commit
- Serve with `python3 -m http.server 8765 --directory docs/kss` (two-window sync needs `http://`)

---

## Instructions

### Step 1: Scaffold (new session) or regenerate (existing)
```bash
python3 docs/kss/_shared/new_session.py 02 userspace-kernel-boundary \
    --title "Your code doesn't own the hardware anymore" --rail Privilege,Memory,Who
```
This gives you a folder that already opens in both windows with three `EXAMPLE` steps and a morphing helper. Replace, don't append: `check.py` warns while any `EXAMPLE` / `EDIT ME` placeholder remains.

For an existing session, after any `STORY.md` edit:
```bash
python3 docs/kss/_shared/build_deck.py session-02-userspace-kernel-boundary
```

### Step 2: Translate each beat with the 5-line template
For every `<!-- step: id -->` in `STORY.md`, fill this in **before** writing HTML:

| Field | Rule | Session 1 example (`spl-dram`) |
|---|---|---|
| `title` | **The claim.** ≤ 2 lines at 54 px (~12 words). A sentence someone could disagree with, not a label. | *One job: initialise the DRAM controller* |
| `caption` | **The consequence or the number.** ≤ 1 sentence; may be empty. Never restates the title. | *Parameters specific to the DDR chips the board vendor chose.* |
| `visual` | **The one thing to notice.** Name it in a comment before drawing. | DRAM controller + DDR chips go dark → lit |
| `rail` | 2–3 chips that **change across the session**; same keys on every step that has them. | Memory: SRAM → DRAM · CPU: from SRAM · Code: first stage you can change |
| `cues` | What is **said and never shown**: the bridge, the war story, "ask the room", demo prompts. | *"Let the boxes turn green before you speak."* / *"If you designed your own board, this is the stage you'd touch first."* |

If you can't name the one thing to notice, the beat is two beats — go back to `STORY.md` and split the marker.

### Step 3: Pick the diagram shape from the pattern library
Match the concept to a shape, then compose it from `dg-*` primitives. Each row names a Session 1 step to open as a copy-paste reference.

| Concept | Shape | Primitives | Reference step |
|---|---|---|---|
| A chain / pipeline / relay | one `dg-row`, boxes with `dg-arrow[data-dir=right]` between | `chain()` helper | `open-relay`, `rbl-minimum`, `flow-demo` |
| Containment ("inside the chip", "on the board") | nested `dg-group`s with `dg-label` | `socBoard()` helper | `soc-chip` → `spl-handoff` |
| Before / after, dark → lit | two `dg-col`s side by side, or **the same diagram morphed** | `data-state="off"` → `"on"` | `spl-dram` (morph), `rbl-world` |
| Memory / address layout | `dg-mem` strip: `dg-mem-addr` + `dg-mem-seg`, `data-state="gap"` for spacing | — | `uboot-load` |
| Generic thing → your specifics | one wide box, arrow "you supply", a `dg-col` of `data-state="you"` boxes | `data-grow` | `uboot-why` |
| Choice among alternatives | a `dg-row` of equal boxes, one `focus` | — | `uboot-source`, `rootfs-build` |
| Ownership / who writes it | one or two boxes + a `dg-chips` row of attributes | `ownerBox()` helper | `rbl-owner`, `spl-owner` |
| Layers (base → extends → yours) | vertical stack of boxes with `dg-arrow` "includes" between, `you` on top | — | `kernel-layers` |
| Translation / indirection (virtual → physical) | `dg-col` → arrow → `focus` box → arrow → `dg-col` | — | `kernel-mmu` |
| Contrast (how X does it vs how Y does it) | two `dg-group`s side by side, one `data-tone="focus"` | — | `kernel-silent` |
| Data → match → effect | box with `dg-term` snippet → arrow "match" → box → arrow "creates" → box | `dg-term .hl` | `kernel-dt` |
| Commands / config | `dg-term` with `.p` prompt, `.c` command, `.o` output + a `dg-chips` row of key names | — | `uboot-env` |
| File tree | `dg-tree` with `.hl` on the lines that matter | — | `rootfs-tree` |
| A painful loop | `dg-chips` with `<i>→</i>` separators, `data-state="pain"` on the bad steps | — | `flow-pain` |
| Host ↔ board / network | `dg-group` per machine, `dg-arrow` "Ethernet" between, protocol names in box `small`s | — | `flow-network`, `flow-lab` |
| Summary of the whole thing | `dg-row` per item: narrow `ghost` label box + wide text box | `data-grow="3"` | `summary` |
| Generic vs our hardware | two `dg-group`s stacked, same shape, the differing box `data-grow="2"` | — | `rpi4` |
| Series / roadmap | `dg-row` of boxes: done `on`, now `focus`, later `ghost` | — | `end` |

Colour is vocabulary, not decoration — the same meaning on every step of every session:

| `data-state` | Means | Never use it for |
|---|---|---|
| `focus` (blue) | this stage / look here | "important" in general |
| `on` (green) | available, working, done | "good" |
| `off` (dashed, dim) | not available **yet** | "unimportant" |
| `you` (yellow) | you write / own this | emphasis |
| `pain` (red) | the problem being solved | errors in general |
| `ghost` (outline) | placeholder / later | — |

### Step 4: Morph, don't cut, when the subject doesn't change
Consecutive steps about the *same picture* must share `visual.key` and use stable `data-id`s. The engine then transitions only what changed, which is the animation the audience should be watching.

Recipe (this is `socBoard()` in Session 1):

```js
// 1. One helper renders the WHOLE picture from a state map.
function picture(s = {}, extra = {}) {
  const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
  const ex = (id, d) => (extra[id] !== undefined ? extra[id] : d);
  return `<div class="dg"><div class="dg-row">
    <div class="dg-box" data-id="sram"${st("sram")}><b>SRAM</b><small>${ex("sram", "small, on-chip")}</small></div>
    <div class="dg-box" data-id="dramc"${st("dramc")}><b>DRAM controller</b><small>${ex("dramc", "talks to the DDR chips")}</small></div>
  </div></div>`;
}

// 2. Each step passes ONLY the states that matter; everything else stays neutral.
{ id: "rbl-world", visual: { key: "soc", html: picture({ sram: "on", dramc: "off" }, { dramc: "not initialised" }) } },
{ id: "spl-dram",  visual: { key: "soc", html: picture({ sram: "on", dramc: "on"  }, { dramc: "configured ✓"   }) } },
//                                 ^ same key, same data-ids → dramc transitions off → on and pulses
```

Rules:
- Change **one or two** elements per morph step. If five things change, the audience can't see which one mattered.
- Text under a box (`small`) can change in a morph, but it doesn't animate — carry meaning in the state, use text to confirm it.
- A *new* `data-id` in a morph builds in; a removed one simply disappears. Keep the set of ids stable through a stage where you can.
- Different subject → different `key` → cross-fade + staggered build. That is also fine; just be deliberate.

### Step 5: Write the rail as a trajectory, not a label
Pick 2–3 keys at the start and keep them for the whole session. Declare presets once and reference them (`rail.rbl`, `rail.spl`…) so a stage's steps agree.

| Session | Suggested keys | Trajectory |
|---|---|---|
| 1 Boot | Memory · CPU · Code | SRAM only → DRAM → virtual · ROM → SRAM → DRAM → kernel → user · immutable → vendor → open → yours |
| 2 The wall | Privilege · Address space · Who owns the CPU | EL0 ↔ EL1 · virtual / physical · you → kernel → you |
| 3 Drivers | Described by · Bound to · Visible as | nothing → DT node · nothing → driver `probe()` · nothing → `/dev/x` |

A chip value can carry a tone: `Memory: ["on-chip SRAM only", "blocked"]`, `Code: ["yours", "you"]`. Use tone sparingly — it's a second colour channel.

### Step 6: Seed cues from the review, then hand them over
Every "I'll say that vocally" in the story review becomes a cue on the relevant step. Standard cue kinds, prefix them so they're scannable from the presenter view:

- `Ask the room: …` — a question to pause on
- `BRIDGE (verbal): …` — connects to an earlier/later section; never on screen
- `WAR STORY (optional): …` — the anecdote the story cut
- `CONTEXT (verbal): …` — alternatives considered, why this approach
- `DEMO: …` — what to do with the terminal / board; pair with `B` to blank
- `Transition: …` — the sentence that hands off to the next step

Cues are the presenter's property. Mark the file "CUES ARE THE PRESENTER'S TO EDIT" and don't polish their prose.

### Step 7: Wire, generate, check
```bash
python3 docs/kss/_shared/build_deck.py session-NN-slug   # STORY.md → deck-content.js
python3 docs/kss/_shared/check.py                        # ids, order, staleness, wiring, CSS, engine
python3 -m http.server 8765 --directory docs/kss          # then open the launcher
```
In the browser, no red banner in either window; step with `→`; the header dot turns green when the audience window acks.

### Step 8: Review the deck as an audience member, then as the presenter
- **Audience pass** (audience window only, no notes): read the titles in sequence. Do they tell the story by themselves? Is every visual's "one thing" obvious within two seconds? Any step where you'd want to read a paragraph is a step that needs a better visual or a split.
- **Presenter pass:** is each note readable in the time its step is on screen? A note twice as long as its neighbours hides a cue or a cut.
- **Fit pass:** the densest steps (summaries, two-group contrasts) must not clip at 1600×900 — scale the window small to see the whole stage.
- **Drift pass:** nothing in `deck.js` titles/captions that `STORY.md` doesn't say.

---

## Notes
- **Title before HTML.** If the title isn't a claim, the visual will be a decoration. Fix the title first.
- **Helpers over copies.** The moment a diagram appears twice, make it a function of a state map; morphing comes for free.
- **No session CSS/JS.** If a primitive is missing, add it to `_shared/kss.css`, document it in `COMPONENTS.md`, then use it. Session folders are content.
- **The engine validates on load** (ids, titles, visuals, notes present both ways) and shows a red banner on failure — check both windows after every change, not just the presenter.
- **Two bugs that have actually shipped and are now caught by `check.py`:** a `*/` inside a CSS comment (kills `:root`, page renders unstyled) and a `const` read inside its own initialiser's callback (TDZ error, controls dead). Run the check; it's one second.
- `docs/` must not reference `projects/`. Inline any code snippet you need.
