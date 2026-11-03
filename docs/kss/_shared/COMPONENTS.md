# KSS Shared Components

Every session page under `docs/kss/session-NN-*/index.html` is assembled from the pieces below. They live in [`kss.css`](kss.css) and [`kss.js`](kss.js). Zero dependencies; pages work from `file://` and offline.

If you need something a session page doesn't have yet, **add it here first**, then use it from the session. Session pages should contain content, not new CSS.

---

## Page skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KSS N — Title</title>
  <link rel="stylesheet" href="../_shared/kss.css">
</head>
<body>
<div class="kss-page">
  <aside class="kss-rail">…</aside>     <!-- sticky left rail -->
  <main class="kss-main">
    <header class="kss-hero">…</header>
    <section class="kss-section" id="…">…</section>
    …
    <footer class="kss-footer">…</footer>
  </main>
</div>
<script src="../_shared/kss.js"></script>
</body>
</html>
```

`.kss-page` is a two-column grid (rail + main). Below 900 px it collapses to one column and the rail's hardware-state block hides.

---

## Typography

| Class | Use for | Notes |
|---|---|---|
| `.t-display` | Page title (one per page) | Tight leading, negative tracking |
| `.t-title` | Section titles (`<h2>`) | |
| `.t-heading` | Stage names, sub-headings | |
| `.t-lead` | Opening paragraphs, intros | Secondary colour, larger |
| `.t-body` | Prose | Pair with `.prose` for spacing |
| `.t-small` | Stage one-liners, captions | |
| `.t-micro` | Eyebrow labels ("Before the chain") | Uppercase, tracked |

`.prose` caps line length at `--measure` (68ch) and adds vertical rhythm. Inside `.kss-stage-inner` the cap is removed because the column is already narrow.

---

## Side rail

```html
<aside class="kss-rail" aria-label="Session navigation">
  <nav class="kss-rail-nav" aria-label="Sections">
    <a href="#soc">The chip and the board</a>
    <a href="#stage-rbl">1 · ROM Bootloader</a>   <!-- links to stage ids get highlight + open-on-click -->
    …
  </nav>

  <div class="kss-rail-state" aria-live="polite">
    <div class="t-micro">Hardware state</div>
    <dl data-kss-rail>
      <div><dt>Memory</dt><dd data-rail="memory">Select a stage</dd></div>
      <div><dt>CPU</dt>   <dd data-rail="cpu">—</dd></div>
      <div><dt>Code</dt>  <dd data-rail="code">—</dd></div>
    </dl>
  </div>
</aside>
```

- `data-rail="<key>"` fields are filled from the active stage's `data-rail-<key>` attribute. Keys are free-form: a Session 2 page might use `privilege`, `address-space`, `who-owns-cpu`. Match the `dd` keys to whatever your stages declare.
- The initial text of each `dd` is restored when no stage is open.
- Optional `data-rail-<key>-tone="ok|blocked"` colours the value green/rose.

---

## Stage chain (the core interactive)

```html
<div class="kss-chain" data-kss-chain>

  <article class="kss-stage" id="stage-xyz"
           data-rail-memory="Full DRAM" data-rail-memory-tone="ok"
           data-rail-cpu="Executing from DRAM"
           data-rail-code="Open source, configured by you">

    <button class="kss-stage-head" type="button" aria-expanded="false">
      <span class="kss-stage-num">3</span>
      <span class="kss-stage-title">
        <span class="t-heading">U-Boot</span>
        <span class="t-small">The one that finds your kernel</span>
      </span>
      <span class="kss-stage-meta">
        <span class="kss-tag" data-owner="open">Open source · you configure</span>
        <svg class="kss-chevron" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M5 8l5 5 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </span>
    </button>

    <div class="kss-stage-body"><div>
      <div class="kss-stage-inner">
        <div class="prose t-body">
          <!-- text: what → why it exists → who writes it -->
        </div>
        <figure class="kss-visual">
          <!-- diagram built from dg-* primitives -->
          <figcaption>One sentence on what to notice.</figcaption>
        </figure>
      </div>
    </div></div>

  </article>

</div>
```

Behaviour provided by `kss.js`:

- One stage open at a time. Click the open one to close it. Others dim to 55 % but stay in place.
- `ArrowDown`/`ArrowUp` (or `j`/`k`) step through stages — handy while presenting.
- `#stage-xyz` in the URL opens that stage on load; the hash updates as you navigate, so you can link to a specific stage.
- Nothing is locked during the open/close animation; a second click re-targets mid-flight.
- Reduced motion: cross-fade only, no translate.

**Ownership tags** — `data-owner` on `.kss-tag`:

| Value | Colour | Meaning |
|---|---|---|
| `vendor` | neutral | Silicon or board vendor; you don't touch it |
| `open` | accent (blue) | Open source; you configure or extend it |
| `you` | warm (yellow) | You write it |

Keep the tag text short; it's a hint, not a sentence. The nuanced "who writes what" story belongs in the prose.

---

## Diagram primitives (`dg-*`)

Compose annotated visuals from these instead of drawing SVGs. They're deliberately whiteboard-plain.

```html
<div class="dg">                          <!-- vertical stack -->
  <div class="dg-row">                    <!-- horizontal row -->
    <div class="dg-box" data-state="focus"><b>Title</b><small>detail</small></div>
    <div class="dg-arrow" data-dir="right">label</div>
    <div class="dg-box" data-state="on"><b>Title</b><small>detail</small></div>
  </div>
  <div class="dg-arrow">label</div>       <!-- vertical arrow (default) -->
  <div class="dg-group" data-tone="faded">
    <span class="dg-label">Group label</span>
    …boxes…
  </div>
  <div class="dg-legend"><span data-k="on">usable</span><span data-k="off">not yet</span></div>
</div>
```

| Element | States / attrs | Use |
|---|---|---|
| `.dg-box` | `data-state="on"` (green) · `"off"` (dashed, dim) · `"focus"` (blue) · `"you"` (yellow) | Any labelled block |
| `.dg-arrow` | `data-dir="right"` for horizontal | Flow between boxes, with optional label text |
| `.dg-group` | `data-tone="faded"` | Dashed container with a floating label ("Inside the SoC") |
| `.dg-col` | — | Vertical sub-stack inside a `.dg-row` |
| `.dg-legend` | `span[data-k]` matching box states | Key under a diagram |
| `.dg-mem` | — | Address-space strip: alternate `.dg-mem-addr` and `.dg-mem-seg` children; seg states `focus` and `gap` |

Rule of thumb: a visual should have **one thing to notice**, named in the `figcaption`. If you need a legend with more than three entries, split the diagram.

---

## Other blocks

| Class | Purpose |
|---|---|
| `.kss-compare` | Two side-by-side cards (chip vs board, before vs after). Each child `<div>` gets `<h4>` + `<p>`/`<ul>`. |
| `.kss-summary` + `.kss-summary-row` | "The whole thing in one picture" — `<b>label</b><span>one line</span>` per row |
| `.kss-loop` | Horizontal chain of `<span>` steps with `<i>→</i>` separators; `data-pain` on a step turns it rose |
| `.kss-callout` | Side note. `data-tone="warm"` or `"neutral"` |
| `.kss-visual` with `style="position:static"` | Use the visual frame outside a stage (it's sticky by default inside one) |
| `.kss-footer` | Prev/next session links + link to `STORY.md` |

---

## Accessibility & preferences

Built in — nothing to do per page:

- `prefers-reduced-motion` → transitions collapse to cross-fades
- `prefers-reduced-transparency` → translucent surfaces become solid
- `prefers-contrast: more` → stronger borders and text
- Stage heads are real `<button>`s with `aria-expanded`/`aria-controls`
- Rail state has `aria-live="polite"`
- Print stylesheet expands all stages and drops the rail

---

## Extending

- **New rail keys:** just add `data-rail-<key>` to stages and a matching `<dd data-rail="<key>">`. No JS change.
- **New diagram shape:** add a `dg-*` class to `kss.css` under section 7, document it in the table above.
- **New interaction:** add to `kss.js` behind a `data-kss-*` attribute so pages opt in, and document the markup contract at the top of the file.

Do not fork `kss.css` into a session folder. If a session genuinely needs a one-off, put a `<style>` block in that page with a comment explaining why it isn't shared.

## Checking your work

```bash
python3 docs/kss/_shared/check.py
```

Runs on every session page and on `kss.css`. It exits non-zero on: dead rail-nav links, stages missing a `data-rail-*` key, unbalanced tags, classes used but not defined, and — the one that bit us — a stylesheet whose comment ended early.

> **Never type `*/` inside a CSS comment.** A glob like `session-*/index.html` ends the comment at `*/`; the browser then treats the rest of the comment plus the next selector as one invalid rule and drops it. If that rule is `:root`, every `var()` fails and the page renders as plain black-on-white text. `check.py` strips comments the way a browser does and verifies `:root` survived.
