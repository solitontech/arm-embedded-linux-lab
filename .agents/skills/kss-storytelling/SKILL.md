---
name: kss-storytelling
description: Turn a technical embedded-Linux topic into an intuition-first KSS deck for a mixed audience — split content across audience screen / presenter notes / spoken cues, apply the stage pattern and cut rules, and follow the story→review→deck process.
---

# KSS Storytelling

## Purpose
Produce Knowledge Sharing Session content that builds *intuition* rather than transferring facts, in a form that works on a video call: the audience sees one visual at a time; the presenter has the prose and the cues. This skill captures the editorial method refined while building Session 1 so every new session starts from the same bar.

## When to Use This Skill
- Drafting a new KSS session
- Reviewing a draft `STORY.md` or `deck.js`
- Deciding whether a detail belongs on the audience screen, in the presenter notes, in a spoken cue, or nowhere
- Converting an approved story into a deck

## Prerequisites
- [`docs/kss/README.md`](../../../docs/kss/README.md) — series thread, folder layout, how presenting works
- One finished story end-to-end including its *Review log*: [`docs/kss/session-01-boot-flow/STORY.md`](../../../docs/kss/session-01-boot-flow/STORY.md)
- The deck contract and primitives: [`docs/kss/_shared/COMPONENTS.md`](../../../docs/kss/_shared/COMPONENTS.md)
- Mechanics of adding a session: [`.agents/workflows/kss_new_session.md`](../../workflows/kss_new_session.md)
- The build half of the method: [`kss-deck-builder`](../kss-deck-builder/SKILL.md) — invoke it alongside this skill when a story is approved

---

## Instructions

### Step 1: Fix the audience and the single question
The audience is mixed: students, RTOS/firmware engineers, application developers, driver developers. Nobody is a beginner at computing; many are beginners at *this layer*.

Write one sentence the whole session answers. Session 1: *"What runs before `main()`, who wrote it, and why five stages instead of one?"* Anything that doesn't serve that sentence is a cut candidate.

### Step 2: Sort every piece of content into three channels
This is the core of the method. Each fact, diagram, or remark goes to exactly one place:

| Channel | Where it lives | What belongs there |
|---|---|---|
| **Audience screen** | `deck.js` → `title`, `visual`, `caption`, `rail` | One idea per step. A title (≤ ~2 lines), one diagram, at most one sentence. The hardware-state chips. **Never a paragraph.** |
| **Presenter notes** | `STORY.md` prose under a `<!-- step -->` marker (generated into `deck-content.js`) | What each thing *is*, why it exists, who writes it, terms defined on first use. Readable by someone who missed the talk. |
| **Spoken cues** | `deck.js` → `cues[]` | Why we're looking at this today; alternatives and why this approach; bridges between sections; war stories; "ask the room"; demo prompts. Things that are *said*, never shown and never written as prose. |

The test for a cue versus a note: would it still be true and useful if a different presenter gave the talk? If yes, it's a note. If it depends on *this* presenter's experience or on reading the room, it's a cue.

### Step 3: Open with the question, not the definition
Start from an experience the audience already has ("you plug in power; a second later there's a shell") and ask what happened in between. Definitions come after curiosity.

### Step 4: Add the physical context before the mechanism
If the mechanism lives on hardware, give the audience the hardware first. Session 1 needed "what is an SoC, who makes it, who builds the board around it" *before* the ROM bootloader made sense. Ask: *what must the reader be able to picture before stage 1?*

Keep that context self-contained. Do **not** pre-explain how it connects to the mechanism — that bridge is a cue.

### Step 5: Use the stage pattern for every unit
Each stage/component/layer gets the same four beats, in this order, and usually becomes 3–5 steps:

1. **What it is** — one or two plain sentences, no undefined jargon
2. **Why it exists** — the constraint that makes it necessary (SRAM is too small; DRAM timing is board-specific; peripherals don't announce themselves)
3. **Why it doesn't skip ahead** — the obvious shortcut and the reason it isn't taken ("why doesn't the SPL just load the kernel?")
4. **Who writes it** — silicon vendor / board vendor / open source / you — woven into the prose, not a rigid badge

The "why you customise X" beat has a fixed shape: *X is generic → your product isn't → here's the specific knowledge only you have → that's what you supply.* Reuse it (SPL → DRAM config, U-Boot → boot flow, Device Tree → your overlay). The repetition is what makes it intuitive; say so in a cue the third time.

### Step 6: Design the visual per step, then the title, then the caption
Work in that order — it keeps text minimal.

- **One thing to notice** per visual. If it needs a legend with more than three entries, split the step.
- Prefer a **morph** over a new diagram when consecutive steps are about the same thing: same `visual.key`, stable `data-id`s, only `data-state` changes. The DRAM box turning green *is* the SPL stage; the audience should see it happen, not read about it.
- Colour means the same thing on every slide: blue = look here, green = available/done, dashed = not yet, yellow = yours, red = the problem. Don't reassign.
- Title is the claim ("One job: initialise the DRAM controller"), caption is the consequence or the number ("Parameters only the board vendor knows"). Neither restates the other.
- Put the hardware state in the rail chips, not in the title.

### Step 7: Apply the cut rules
These are the edits that came up in review. Apply them before asking for review.

| Rule | Example from Session 1 |
|---|---|
| **One sentence of internals, never a paragraph.** Name the constraint; don't tour the datasheet. | DDR "row activation, ranks, banks" → "parameters specific to those chips, which only the board vendor knows" |
| **War stories are cues, never notes or screen.** | DTB-overlap debugging anecdote → cue on the U-Boot memory-map step |
| **"Why this matters for later" bridges are cues.** | "Why this split matters for booting" paragraph → cue on the three-authors step |
| **Mention the shortcut, don't teach it.** | Falcon mode: one sentence in notes, caption says it exists |
| **If a tool is broader than where it appears, say so in one line.** | Buildroot/Yocto: "full system build tools — they appear here because the rootfs is where their output is most visible" |
| **Define on first use, inline, in a clause — in the notes, not on screen.** | "eFuses (one-time-programmable bits inside the chip)" |
| **Numbers are for scale, not precision.** | "tens of MB vs a few hundred KB" |
| **Hedge what varies by board.** | `saveenv` "when the board provides storage for the environment" |
| **A paragraph on screen is a bug.** | The entire reason the first version was rebuilt |

### Step 8: Draft `STORY.md` with step markers, then stop
Write the prose with `<!-- step: id -->` markers between beats and `**Visual:**` / `**Rail state:**` notes describing intent. Do **not** write `deck.js` yet. Post the story for review and iterate on flow, depth, and channel assignment. Session 1 went through seven review edits before any deck existed; that is the expected shape.

Append to the *Review log* (feedback → change). Future sessions read it.

### Step 9: Build the deck from the approved story
Hand over to the [`kss-deck-builder`](../kss-deck-builder/SKILL.md) skill — it carries the beat→step template, the visual pattern library (concept → diagram shape, with Session 1 reference steps), the morph recipe, rail conventions per session, and the cue prefixes. In short:
- `python3 docs/kss/_shared/new_session.py NN slug --title "…"` for a new session
- One `deck.js` step per marker, same ids, same order; title = the claim, caption = the consequence, visual = the one thing to notice
- Cues: every "I'll say that vocally" from the review becomes a cue; they're the presenter's to edit
- `python3 docs/kss/_shared/build_deck.py session-NN-slug` then `python3 docs/kss/_shared/check.py`

### Step 10: Verify
- Step through the audience window alone: does the sequence of titles tell the story with no narration?
- Step through the presenter window: is every note readable in the time the step is on screen? If a note is twice as long as its neighbours, part of it is a cue or a cut.
- No claim in `deck.js` (title/caption) that isn't in `STORY.md`
- `python3 docs/kss/_shared/check.py` passes
- Rehearse once with both windows open and a timer running; the planned-minutes budget is in `deck.js`

---

## Notes
- **Abstract the board, keep the demo concrete.** Teach the generic flow even when lab hardware deviates; put the lab board's quirks in one footnote step near the end. Session 1 did this for the RPi4's GPU-first boot.
- **Repetition is a feature.** Same four beats, same "generic → your specifics" shape, same colours. Don't vary structure for novelty.
- **The demo is a step.** Give the audience a frame of what to watch *before* switching the share to a terminal, blank the stage (`B`), demo, come back to the same frame.
- **Density checks:** more than ~12 words in a title, more than one sentence in a caption, or a diagram with more than ~8 boxes → split the step.
- Visual/interaction rules (feedback on press, interruptible transitions, reduced-motion fallbacks, typography) come from the `design` skill and are baked into `_shared/kss.css` and `_shared/deck.css`.
