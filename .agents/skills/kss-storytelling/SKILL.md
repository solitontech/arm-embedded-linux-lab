---
name: kss-storytelling
description: Turn a technical embedded-Linux topic into an intuition-first KSS story and interactive page for a mixed audience — what to include, what to cut, how to split speaker vs page, and the story→review→build process.
---

# KSS Storytelling

## Purpose
Produce Knowledge Sharing Session content that builds *intuition* rather than transferring facts. The output is a reviewed `STORY.md` and an interactive page under `docs/kss/session-NN-*/`. This skill captures the editorial method that was refined while building Session 1; apply it so each new session starts from the same bar instead of re-deriving it.

## When to Use This Skill
- Drafting a new KSS session (any topic in the series)
- Reviewing a draft story someone else wrote
- Deciding whether a detail belongs on the page, in the speaker's notes, or nowhere
- Converting an approved story into `index.html`

## Prerequisites
- Read [`docs/kss/README.md`](../../../docs/kss/README.md) for the series thread and folder layout
- Read one finished story end-to-end, e.g. [`docs/kss/session-01-boot-flow/STORY.md`](../../../docs/kss/session-01-boot-flow/STORY.md), including its *Review log*
- Component catalogue for the build step: [`docs/kss/_shared/COMPONENTS.md`](../../../docs/kss/_shared/COMPONENTS.md)

---

## Instructions

### Step 1: Fix the audience and the single question
The series audience is mixed: students, RTOS/firmware engineers, application developers, driver developers. Nobody is a beginner at computing; many are beginners at *this layer*.

Write one sentence the whole session answers. Session 1's was *"What runs before `main()`, who wrote it, and why five stages instead of one?"* If a paragraph doesn't serve that sentence, it's a candidate for cutting.

### Step 2: Decide who says what — speaker vs page
Make this table before writing. It drove most of the Session 1 edits.

| Speaker owns (verbal) | Page owns (written) |
|---|---|
| Why we're looking at this today | What each thing *is* |
| What the alternatives were and why we chose this approach | Why it exists — what gap it fills |
| Bridges between sections ("remember the SoC/board split? here's where it bites") | Who writes / owns it |
| Lab war stories, "we learned the hard way", debugging anecdotes | Terms defined on first use |
| Live demo narration | One annotated visual per concept |

The page must make sense to someone who missed the talk, but it must **not** try to be the talk. When in doubt, the anecdote goes to the speaker.

### Step 3: Open with the question, not the definition
Start from an experience the audience already has ("you plug in power; a second later there's a shell") and ask what happened in between. Definitions come after curiosity, never before.

### Step 4: Add the physical context before the mechanism
If the mechanism lives on hardware, give the audience the hardware first. Session 1 needed "what is an SoC, who makes it, who builds the board around it" *before* the ROM bootloader made sense. Ask: *what does the reader need to be able to picture before stage 1?*

Keep that context self-contained. Do **not** pre-explain how it connects to the mechanism — that bridge is the speaker's (see Step 2).

### Step 5: Use the stage pattern for every unit
Each stage/component/layer gets the same four beats, in this order:

1. **What it is** — one or two plain sentences, no jargon left undefined
2. **Why it exists** — the constraint that makes it necessary (SRAM is too small; DRAM timing is board-specific; peripherals don't announce themselves)
3. **Why it doesn't skip ahead** — the obvious shortcut and the reason it's not taken ("why doesn't the SPL just load the kernel?")
4. **Who writes it** — silicon vendor / board vendor / open source / you — woven into the prose, not a rigid badge

The "why you customise X" beat follows a fixed shape: *X is generic → your product isn't → here's the specific knowledge only you have → that's what you supply.* Use the same shape for SPL (DRAM config), U-Boot (boot flow), Device Tree (your wiring). Repetition of the shape is what makes it intuitive.

### Step 6: Apply the cut rules
These are the edits that came up in review. Apply them before asking for review.

| Rule | Example from Session 1 |
|---|---|
| **One sentence of internals, never a paragraph.** Name the constraint; don't tour the datasheet. | DDR "row activation, ranks, banks" → "parameters specific to those chips, which only the board vendor knows" |
| **No war stories on the page.** | DTB-overlap debugging anecdote removed; left for the speaker |
| **No "why this matters for later" bridges.** | "Why this split matters for booting" paragraph removed from the SoC section |
| **Mention the shortcut, don't teach it.** | Falcon mode: one sentence acknowledging it exists |
| **If a tool is broader than where it appears, say so in one line.** | Buildroot/Yocto: "full system build tools — they appear here because the rootfs is where their output is most visible" |
| **Define on first use, inline, in a clause.** | "eFuses (one-time-programmable bits inside the chip)" |
| **Numbers are for scale, not precision.** | "tens of MB vs a few hundred KB" — enough to make the constraint obvious |
| **Hedge what varies by board.** | `saveenv` "when the board provides storage for the environment" |

### Step 7: Draft the story, then stop
Write `STORY.md` as prose with `**Visual:**` and `**Rail state:**` notes per stage. Do **not** write HTML yet. Post the story for review and iterate on the flow alone. Session 1 went through seven review edits before a line of HTML existed; that is the expected shape.

Append a *Review log* table (feedback → change). Future sessions read it.

### Step 8: Build the page from the approved story
- One `.kss-stage` per stage; prose on the left, one `.kss-visual` on the right
- Each visual has **one thing to notice**, named in the `figcaption`
- Rail state per stage: pick 2–3 keys that change across the session (Session 1: memory / CPU / code ownership). Different sessions will use different keys
- Use only `_shared` components. If something is missing, add it to `_shared` and document it in `COMPONENTS.md`
- Progressive disclosure: the page should be scannable with every stage closed

### Step 9: Verify
- Read the page with all stages closed: does the chain alone tell the story?
- Open each stage: can a reader who skipped the talk follow it?
- Diff the page against `STORY.md`: no new claims were introduced during build
- Check on a projector-sized window and with `prefers-reduced-motion` on
- The *Who says what* table still matches what's on the page

---

## Notes
- **Abstract the board, keep the demo concrete.** Teach the generic flow (RBL → SPL → U-Boot → kernel) even when lab hardware deviates. Put the lab hardware's quirks in a short footnote, not in the main chain. Session 1 did this for the RPi4's GPU-first boot.
- **Repetition is a feature.** The same four beats and the same "generic → your specifics" shape, repeated per stage, are what let the audience predict the next section. Don't vary the structure for novelty.
- **Density check:** if a stage's prose is longer than its neighbours by half, something in it belongs to the speaker.
- **Visual check:** if a diagram needs a legend with more than three entries, split it.
- This skill is about *content*. The visual/interaction rules (feedback on press, interruptible transitions, reduced-motion fallbacks, typography) come from the `design` skill and are already baked into `_shared/kss.css`.
