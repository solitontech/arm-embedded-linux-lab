# Session 02 — Your code doesn't own the hardware anymore

> **Status:** Scaffolded, not yet planned. The beats below are placeholders. The deck is built from this file.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py session-02-userspace-kernel-boundary`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** What the OS does between your code and the silicon, and why your program can no longer touch hardware directly.
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live demo. Launcher: [index.html](index.html).

## Planning notes

**Where this sits in the series:** continues [session 1](../session-01-boot-flow/STORY.md), which ended with the kernel up and a shell running. Session 1 showed the kernel taking over the CPU and enabling the MMU; this session explains what that changes for your code. Leads into [session 3](../session-03-device-tree-to-dev/STORY.md), where the kernel meets the hardware.

**Core question:** what does the OS actually do between your code and the silicon?

**Candidate beats (not yet reviewed):** bare-metal vs RTOS vs Linux, what you could do before · processes and the CPU privilege split (user vs kernel mode) · virtual memory, one address space per process · system calls as the only door into the kernel · demo: `strace` of a trivial program on the board.

**From the audience form:** mostly newcomers, with firmware and application developers; top ask was *how the kernel talks to hardware*. RTOS folks will want the contrast with an RTOS; application developers want to see their own code in the picture. Keep it at mental-model depth.

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
