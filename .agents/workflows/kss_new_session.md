---
description: add a new Knowledge Sharing Session (story + interactive page) under docs/kss/
---

# New KSS Session

## When to Use This Workflow
You are adding Session N to the KSS series in `docs/kss/` — a reviewed narrative (`STORY.md`) and an interactive page (`index.html`) built from the shared components.

## Prerequisites
- Read [`docs/kss/README.md`](../../docs/kss/README.md) for the series thread and the session index.
- Read the previous session's `STORY.md` end-to-end, including its *Review log*.
- Invoke the [`kss-storytelling`](../skills/kss-storytelling/SKILL.md) skill — it holds the editorial rules; this workflow only sequences the steps.
- Work on a `kss/*` branch, not `main`.

## Steps

1. **Pick the slug and create the folder**
   Two-digit number, kebab-case slug describing the topic (not the title).
   ```bash
   mkdir -p docs/kss/session-02-userspace-kernel-boundary
   ```

2. **Write `STORY.md` — and stop there**
   Use the previous session's `STORY.md` as the template. It must contain, in order:
   - Header: status (`Draft`), audience, goal, format
   - *Who says what* table (speaker vs page)
   - Opening question
   - Physical/context section if the mechanism needs one
   - One section per stage, each with the four beats (what / why it exists / why not skip ahead / who writes it) plus `**Visual:**` and `**Rail state:**` notes
   - "The complete chain" summary
   - Footnote for lab-hardware deviations, if any
   - Empty *Review log* table

   Apply the cut rules from the skill before asking for review.

3. **Review the story as prose**
   Share `STORY.md` (not HTML) for review. Iterate on flow, depth, and ownership. Record every accepted change in the *Review log* (feedback → change). Do not start the page until the story status is `Reviewed and approved`.

4. **Build `index.html` from the approved story**
   Copy the previous session's `index.html` as a starting point and replace content. Rules:
   - Link `../_shared/kss.css` and `../_shared/kss.js`; do not add session-local CSS/JS
   - One `<article class="kss-stage">` per story stage, with `data-rail-*` attributes matching the story's *Rail state* notes
   - Rail `<dd data-rail="…">` keys must match the `data-rail-*` keys you chose for this session
   - One `.kss-visual` per stage, composed from `dg-*` primitives, with a one-sentence `figcaption`
   - Rail nav links for every section `id`
   - Footer: link to `STORY.md`, previous/next session titles

   If a component you need doesn't exist, add it to `docs/kss/_shared/kss.css` (or `kss.js` behind a `data-kss-*` opt-in) and document it in `docs/kss/_shared/COMPONENTS.md` in the same commit.

5. **Update the series index**
   In `docs/kss/README.md`, set the session's row to `Ready` and link `index.html` and `STORY.md`. Update the "Next:" text in the previous session's footer.

6. **Verify**
   ```bash
   python3 -m http.server 8765 --directory docs/kss
   # open http://localhost:8765/session-NN-slug/
   ```
   - Every stage opens/closes; `↓`/`↑` step through; `#stage-…` deep links open the right stage
   - Rail values change per stage and reset when all are closed
   - All rail-nav links resolve (no dead `#id`s)
   - Page reads with every stage closed; each stage reads on its own
   - No claims on the page that aren't in `STORY.md`
   - Check with `prefers-reduced-motion` on and at projector width (~1280 px)

   Structural check that catches the common mistakes (run from the repo root):
   ```bash
   python3 - <<'EOF'
   import re, sys, glob
   for page in glob.glob('docs/kss/session-*/index.html'):
       src = open(page).read()
       ids = set(re.findall(r'\bid="([^"]+)"', src))
       nav = re.search(r'class="kss-rail-nav".*?</nav>', src, re.S)
       dead = [h for h in re.findall(r'href="#([^"]+)"', nav.group(0) if nav else '') if h not in ids]
       stages = re.findall(r'<article class="kss-stage" id="([^"]+)"([^>]*)>', src)
       rail_keys = set(re.findall(r'data-rail="(\w+)"', src))
       missing = [(s, k) for s, a in stages for k in rail_keys if f'data-rail-{k}=' not in a]
       print(page, '| stages:', len(stages), '| dead nav links:', dead or 'none', '| missing rail attrs:', missing or 'none')
   EOF
   ```

7. **Commit**
   One commit for the session (story + page + README row). Shared-component changes may be a separate preceding commit if they're substantial.

## Files Touched
- `[CREATE]` `docs/kss/session-NN-slug/STORY.md`
- `[CREATE]` `docs/kss/session-NN-slug/index.html`
- `[MODIFY]` `docs/kss/README.md` — session index row
- `[MODIFY]` `docs/kss/session-(NN-1)-*/index.html` — footer "Next:" link
- `[MODIFY, if needed]` `docs/kss/_shared/kss.css`, `docs/kss/_shared/kss.js`, `docs/kss/_shared/COMPONENTS.md`

## Notes
- The story is the source of truth. If you find yourself changing wording in `index.html`, change `STORY.md` first.
- Keep the lab hardware out of the main chain; generic flow in the body, board quirks in a footnote.
- `docs/` must not link to specific `projects/` (see `AGENTS.md`). If a session needs a code example from a project, inline the snippet and don't link.
- Related: [`kss-storytelling`](../skills/kss-storytelling/SKILL.md) skill, [`_shared/COMPONENTS.md`](../../docs/kss/_shared/COMPONENTS.md).
