# KSS Shared Components

Every session under `docs/kss/session-NN-*/` is a **deck**: one list of steps, rendered into two windows.

| File | Role |
|---|---|
| [`kss.css`](kss.css) | Tokens, base, type scale, and the `dg-*` diagram primitives every visual is built from |
| [`deck.css`](deck.css) | Layouts: the 16:9 audience **stage** and the presenter **console**; build/morph animations |
| [`deck-engine.js`](deck-engine.js) | Renders steps, navigation keys, two-window sync, mirror, timer, deck validation |
| [`build_deck.py`](build_deck.py) | Generates `deck-content.js` (presenter prose) from `STORY.md` step markers |
| [`check.py`](check.py) | Structural checks — run before committing |

Zero dependencies. Pages work from `file://` for single-window use; **two-window sync needs `http://`** (`python3 -m http.server 8765 --directory docs/kss`).

If a session needs something that isn't here, **add it here first** and document it below. Session folders contain content (`STORY.md`, `deck.js`), not CSS or JS.

---

## The deck contract

### Files per session

```
session-NN-slug/
├── STORY.md          ← prose, with <!-- step: id --> markers      (you write)
├── deck.js           ← steps: title, visual, caption, rail, cues  (you write)
├── deck-content.js   ← presenter prose per step                   (GENERATED)
├── show.html         ← audience window                            (copy, edit <title>)
├── present.html      ← presenter window                           (copy, edit <title>)
└── index.html        ← launcher                                   (copy, edit text)
```

### `deck.js`

```js
KSS.defineDeck({
  id: "session-02",                 // sync channel name; unique per session
  title: "Your code doesn't own the hardware anymore",
  plannedMinutes: 60,               // timer turns red past this
  steps: [
    {
      id: "wall-intro",             // == <!-- step: wall-intro --> in STORY.md
      section: "1 · The wall",      // eyebrow on stage; groups the presenter outline
      title: "Your code has a landlord now",          // ≤ ~24 chars per line reads best
      caption: "One sentence the audience can read in 3 s.",   // optional
      rail: { Privilege: ["EL0", "you"], Memory: "virtual" },  // optional chips; value or [value, tone]
      visual: { key: "wall", html: `<div class="dg">…</div>` },
      cues: ["Ask the room: …", "WAR STORY: …"],      // optional; presenter only
    },
  ],
});
```

Rules the engine enforces (a red banner appears in both windows if broken):

- every step has `id`, `title`, `visual.html`
- ids are unique
- every step id has prose in `deck-content.js` (i.e. a marker in `STORY.md`), and vice versa

### `STORY.md` markers

```markdown
## 3. Stage 2 — SPL

<!-- step: spl-intro -->
The SPL is the first piece of software that *you* can change. …

**Visual:** same SoC diagram; SRAM shows "SPL"; DRAM still dark.
**Rail state:** Memory: SRAM → DRAM · CPU: from SRAM

<!-- step: spl-dram -->
The SPL has one critical job …
```

- A step's prose runs to the next marker, the next `##` heading, or `<!-- /steps -->`.
- `**Visual:**` / `**Rail state:**` paragraphs are authoring notes; the generator drops them.
- Supported markdown: `###`/`####` headings, paragraphs, `**bold**`, `*em*`, `` `code` ``, fenced code, lists, `>` quotes, pipe tables.
- Regenerate after every edit: `python3 docs/kss/_shared/build_deck.py session-NN-slug`. `check.py` fails if you forget.

---

## Visual primitives (`dg-*`, in `kss.css`)

All visuals are composed from these. They scale with `font-size`, so the same markup works on the big stage and in the presenter's mirror.

```html
<div class="dg">                                   <!-- vertical stack -->
  <div class="dg-row">                             <!-- horizontal row -->
    <div class="dg-box" data-state="focus"><b>Title</b><small>detail</small></div>
    <div class="dg-arrow" data-dir="right">label</div>
    <div class="dg-box" data-state="on" data-grow="2"><b>Wider</b><small>flex: 2</small></div>
  </div>
  <div class="dg-arrow">label</div>                <!-- vertical arrow -->
  <div class="dg-group" data-tone="focus">
    <span class="dg-label">Group label</span>
    …
  </div>
  <div class="dg-chips"><span class="dg-chip">a</span><i>→</i><span class="dg-chip" data-state="pain">b</span></div>
  <div class="dg-legend"><span data-k="on">usable</span><span data-k="off">not yet</span></div>
</div>
```

| Element | Attributes | Use |
|---|---|---|
| `.dg-box` | `data-state="on \| off \| focus \| you \| pain \| ghost"`, `data-grow="2 \| 3"` | Any labelled block |
| `.dg-group` | `data-tone="focus \| you \| on \| faded"` + child `.dg-label` | Dashed container ("Inside the SoC") |
| `.dg-row`, `.dg-col`, `.dg-center` | — | Layout |
| `.dg-arrow` | `data-dir="right \| both"` (default: down); inner text = label | Flow |
| `.dg-chips` / `.dg-chip` | chip: `data-state` as box; `<i>` between chips for separators | Pills, loops, capability lists |
| `.dg-mem` | children alternate `.dg-mem-addr` / `.dg-mem-seg[data-state="focus \| gap"]` | Address-space strip |
| `.dg-term` | spans `.p` prompt · `.c` command · `.o` output · `.hl` highlight | Terminal / code block |
| `.dg-tree` | spans `.hl` · `.dim` | Directory tree |
| `.dg-legend` | `span[data-k]` matching states | Key under a diagram |

Colour meaning is fixed across the series — don't reassign it:

| State | Colour | Means |
|---|---|---|
| `focus` | blue | this stage / look here |
| `on` | green | available, working, done |
| `off` | dashed, dim | not available yet |
| `you` | yellow | you write/own this |
| `pain` | red | the problem |
| `ghost` | dashed outline | placeholder / not yet |

---

## Morphing between steps

If two consecutive steps share `visual.key`, the engine does **not** cross-fade. It swaps the HTML, then for every element with a `data-id`:

- same `data-id`, different `data-state`/`data-tone` → the element **transitions** from the old state to the new one and pulses (`.is-changed`)
- `data-id` not present before → builds in (`.is-new`)
- unchanged → nothing moves

So: give boxes stable `data-id`s, write a helper that renders the whole diagram from a state map, and call it per step with different states. Session 1's `socBoard(states, tones, texts)` in `deck.js` is the pattern. Different keys → cross-fade + staggered build of every primitive.

---

## Stage layout facts

- Design surface is **1600 × 900 px**, scaled to the window. Font base on stage is 22 px; `dg-*` sizes follow in `em`.
- Title max ~24 characters per line, two lines max. Caption one sentence.
- Rail chips come from `step.rail`; keys are free-form per session (Session 1: Memory / CPU / Code).
- `B` blanks the stage (black) — use it while sharing a terminal.
- Click right/left quarter of the stage to step (touch screens).

## Presenter console slots

`present.html` is markup only; the engine fills `data-p` slots: `deck-title counter sync prev next-btn blank reset-timer timer open-show next outline eyebrow title cues notes`, plus the `.mirror-wrap` container. `check.py` fails if any is missing.

## Sync

`BroadcastChannel("kss:" + deck.id)`. Messages: `goto`, `hello`, `state`, `ack`, `blank`. Either window can drive; the presenter header dot is green when the audience window has acknowledged the current step, amber while waiting, grey if no audience window answered, red if the browser has no channel (e.g. `file://`).

---

## Checking your work

```bash
python3 docs/kss/_shared/build_deck.py session-NN-slug   # after editing STORY.md
python3 docs/kss/_shared/check.py                        # before committing
```

> **Never type `*/` inside a CSS comment.** A glob like `session-*/index.html` ends the comment at `*/`; the browser then drops the next rule. If that rule is `:root`, every `var()` fails and the page renders as plain black-on-white text. `check.py` strips comments the way a browser does and verifies `:root` survived.
