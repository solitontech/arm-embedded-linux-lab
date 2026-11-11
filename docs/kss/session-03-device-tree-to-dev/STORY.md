# Session 03 — How Linux knows your hardware exists

> **Status:** Scaffolded, not yet planned. The beats below are placeholders. The deck is built from this file.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py session-03-device-tree-to-dev`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** How a peripheral at a fixed address becomes a device you can open from user space, and who wrote each link in that chain.
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live demo. Launcher: [index.html](index.html).

## Planning notes

**Where this sits in the series:** continues [session 2](../session-02-userspace-kernel-boundary/STORY.md), where user code reaches the kernel through system calls. Session 1 introduced the Device Tree briefly in the kernel stage; this session expands that one beat into the whole story: [session 1](../session-01-boot-flow/STORY.md).

**Core question:** how does a peripheral at a fixed address become `/dev/something`?

**Candidate beats (not yet reviewed):** silent peripherals at fixed addresses · the Device Tree as the announcement (`.dts` to `.dtb`, layering, overlays) · `compatible` matching and the driver's `probe()` · the device node and the file operations behind `/dev` · demo: an out-of-tree kernel module on the board that binds to a Device Tree node.

**From the audience form:** drivers and "how the kernel talks to hardware" were top asks, so this session is where the driver-minded people get their payoff. Real mistakes and how they were fixed (for example a wrong `compatible` or an overlapping Device Tree overlay) suit this one well.

## How this file drives the deck

- `<!-- step: id -->` marks the start of one beat. The prose that follows, up to the next marker or the next `##` heading, becomes the **presenter's notes** for that beat.
- The matching entry in [`deck.js`](deck.js) (same `id`) defines what the **audience** sees: title, visual, caption, hardware-state chips — and the presenter's **cues** (things to say that are *not* on screen).
- Paragraphs starting with `**Visual:**` or `**Rail state:**` are authoring notes; the generator drops them.
- Prose outside any marker (this header, the review log) is not shown anywhere.

## Who says what

| Speaker (verbal — lives in `deck.js` cues) | Audience sees (`deck.js` visuals) | Presenter reads (this file) |
|---|---|---|
| Why we're looking at this today; the alternatives; why this approach | One title, one visual, one caption per beat | What each thing *is*, why it exists, who writes it |
| Bridges between sections | Hardware-state chips | Terms defined on first use |
| War stories, "we learned the hard way" | — | — |
| Live demo narration | A frame of what to watch for | Demo checklist |

The audience never sees paragraphs. The page never carries anecdotes. Those are the speaker's.

---

## 0. Opening

<!-- step: open-question -->
EXAMPLE — replace me. Start from an experience the audience already has, then ask what happened in between. Definitions come after curiosity.

**Visual:** the familiar thing on the left, a question mark in the middle, the result on the right.

---

## 1. First stage — "_the one that …_"

<!-- step: stage1-what -->
EXAMPLE — replace me. **What it is**, in one or two plain sentences, with every term defined inline on first use (e.g. **SRAM** — a small, fast memory built into the chip).

**Visual:** the diagram this stage lives in, with this stage's element in focus.

**Rail state:** Key1: value · Key2: value · Key3: value

<!-- step: stage1-why -->
EXAMPLE — replace me. **Why it exists** — the constraint that makes it necessary — and **why it doesn't skip ahead**: the obvious shortcut and the reason it isn't taken.

**Who writes it:** vendor / board maker / open source / you — woven into the prose, not a badge.

**Visual:** same diagram, one element changes state. The audience should *see* the constraint.

<!-- /steps -->

---

## Review log

Changes made during story review, kept so future sessions can learn from them:

| Feedback | Change |
|---|---|
| | |
