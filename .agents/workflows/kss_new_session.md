---
description: add a new Knowledge Sharing Session (story + two-window deck) under docs/kss/
---

# New KSS Session

## When to Use This Workflow
You are adding Session N to the KSS series in `docs/kss/` — a reviewed narrative (`STORY.md`) and a two-window deck (`deck.js` + audience/presenter pages) built on the shared engine.

## Prerequisites
- Read [`docs/kss/README.md`](../../docs/kss/README.md) for the series thread and the session index.
- Read the previous session's `STORY.md` end-to-end, including its *Review log*, and step through its deck once with both windows open.
- Invoke the [`kss-storytelling`](../skills/kss-storytelling/SKILL.md) skill — it holds the editorial rules; this workflow only sequences the steps.
- Read [`docs/kss/_shared/COMPONENTS.md`](../../docs/kss/_shared/COMPONENTS.md) for the deck contract and primitives.
- Work on a `kss/*` branch, not `main`.

## Steps

1. **Create the folder**
   Two-digit number, kebab-case slug describing the topic (not the title).
   ```bash
   mkdir -p docs/kss/session-02-userspace-kernel-boundary
   ```

2. **Write `STORY.md` with step markers — and stop there**
   Use the previous session's `STORY.md` as the template. It must contain, in order:
   - Header: status (`Draft`), audience, goal, format
   - *How this file drives the deck* (copy verbatim) and the *Who says what* table
   - Opening question
   - Physical/context section if the mechanism needs one
   - One `##` section per stage; inside, `<!-- step: id -->` markers between beats (3–5 per stage), each followed by its prose and `**Visual:**` / `**Rail state:**` intent notes
   - A summary step, a demo step if there is one, a footnote step for lab-hardware deviations, a close step
   - `<!-- /steps -->` then an empty *Review log* table

   Apply the cut rules from the skill before asking for review. Sort every item into screen / notes / cue as you write; mark intended cues inline as `_(cue)_` so they're easy to lift later.

3. **Review the story as prose**
   Share `STORY.md` (not a deck) for review. Iterate on flow, depth, and channel assignment. Record every accepted change in the *Review log*. Do not start `deck.js` until the status is `Reviewed and approved`.

4. **Generate the presenter notes**
   ```bash
   python3 docs/kss/_shared/build_deck.py session-02-userspace-kernel-boundary
   ```
   Re-run after every later edit to `STORY.md`. `check.py` fails if the generated file is stale.

5. **Write `deck.js`**
   Copy the previous session's `deck.js` and replace content. Rules:
   - One step per `STORY.md` marker — same `id`, same order
   - `section` eyebrow per stage; `title` ≤ ~2 lines; `caption` ≤ 1 sentence or empty
   - Visuals from `dg-*` primitives only. For diagrams that evolve across steps, write a helper that renders from a state map and give boxes stable `data-id`s so the engine morphs them
   - `rail` chips: 2–3 keys that change across the session
   - `cues`: lift the `_(cue)_` items from the story review; seed "ask the room" and demo prompts; leave them clearly editable
   - Set `id` (unique per session), `title`, `plannedMinutes`

   If a primitive you need doesn't exist, add it to `docs/kss/_shared/kss.css` (or an opt-in behaviour to `deck-engine.js`) and document it in `COMPONENTS.md` in the same commit. Never add CSS/JS to the session folder.

6. **Copy the three pages**
   ```bash
   cp docs/kss/session-01-boot-flow/{show,present,index}.html docs/kss/session-02-userspace-kernel-boundary/
   ```
   Edit only: `<title>` in `show.html` and `present.html`; the title, lead, and `target="kss-…-session-NN"` names in `index.html`. The script order in `show.html`/`present.html` is fixed (`deck-engine.js`, `deck-content.js`, `deck.js`).

7. **Update the series index**
   In `docs/kss/README.md`, set the session's row to `Ready` and link `index.html` and `STORY.md`. Update the "Next" step of the previous session's `deck.js` if it names this session.

8. **Verify**
   ```bash
   python3 docs/kss/_shared/check.py
   python3 -m http.server 8765 --directory docs/kss
   # open http://localhost:8765/session-02-…/  → presenter view → "Open audience window"
   ```
   - No red deck-error banner in either window
   - Step with `→`: the audience window follows; the header dot goes green
   - Morphing diagrams transition instead of cutting; nothing on the stage is clipped at 1600×900
   - Step through the **audience window alone**: do the titles tell the story?
   - `B` blanks, `F` fullscreens, `#12` in the URL opens step 12
   - Rehearse once against `plannedMinutes`

9. **Commit**
   One commit for the session (story, deck, generated content, pages, README row). Shared-component changes go in a separate preceding commit.

## Files Touched
- `[CREATE]` `docs/kss/session-NN-slug/STORY.md`
- `[CREATE]` `docs/kss/session-NN-slug/deck.js`
- `[CREATE]` `docs/kss/session-NN-slug/deck-content.js` (generated)
- `[CREATE]` `docs/kss/session-NN-slug/show.html`, `present.html`, `index.html` (copied)
- `[MODIFY]` `docs/kss/README.md` — session index row
- `[MODIFY, if needed]` previous session's `deck.js` — "Next" step
- `[MODIFY, if needed]` `docs/kss/_shared/kss.css`, `deck.css`, `deck-engine.js`, `COMPONENTS.md`

## Notes
- The story is the source of truth. Presenter notes are generated from it; if you find yourself wanting to change a note, change `STORY.md` and rebuild.
- `docs/` must not link to specific `projects/` (see `AGENTS.md`). If a session needs a code example from a project, inline the snippet.
- Two-window sync requires `http://`. The launcher says so; don't try to make `file://` work.
- Related: [`kss-storytelling`](../skills/kss-storytelling/SKILL.md), [`_shared/COMPONENTS.md`](../../docs/kss/_shared/COMPONENTS.md).
