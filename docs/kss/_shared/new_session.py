#!/usr/bin/env python3
"""Scaffold a new KSS session folder from the shared templates.

Usage:
    python3 docs/kss/_shared/new_session.py 02 userspace-kernel-boundary \
        --title "Your code doesn't own the hardware anymore" \
        [--minutes 60] [--rail Privilege,Memory,Who]

Creates docs/kss/session-02-userspace-kernel-boundary/ with:
    STORY.md          header, who-says-what table, 3 example beats with markers
    deck.js           deck skeleton: rail presets, one morphing helper, 3 example
                      steps matching the STORY.md markers, cues placeholders
    deck-content.js   generated from STORY.md (so the deck opens immediately)
    show.html, present.html, index.html   copied from the newest existing
                      session with titles/targets substituted

Nothing is overwritten: the script refuses to run if the folder exists.
After scaffolding, open the launcher and step through the 3 example beats —
then replace them with the real story. Example beats are tagged EXAMPLE so
check.py can warn if they are still there.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KSS = os.path.dirname(HERE)


def newest_session() -> str | None:
    dirs = sorted(d for d in glob.glob(os.path.join(KSS, "session-*")) if os.path.isdir(d))
    return dirs[-1] if dirs else None


STORY_TMPL = '''# Session {num} — {title}

> **Status:** Draft. The deck is built from this file.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py {slug}`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** _One sentence: the mental model the audience leaves with._
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live demo. Launcher: [index.html](index.html).

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
'''

DECK_TMPL = '''/* ==========================================================================
   Session {num} — {title} — deck definition
   What the AUDIENCE sees (title, visual, caption, hardware-state chips) and
   what the PRESENTER says but does not show (cues).
   Presenter prose comes from STORY.md via deck-content.js (generated).

   Visual rules (see _shared/COMPONENTS.md and the kss-deck-builder skill):
   - Build visuals from dg-* primitives only.
   - Consecutive steps that share visual.key MORPH: give boxes a stable
     data-id and change only data-state; the engine animates the change.
   - One thing to notice per step. Title = the claim, caption = the consequence.

   CUES ARE THE PRESENTER'S TO EDIT.
   ========================================================================== */
(() => {{
  /* ---- morphing diagram helper ----------------------------------------
     Render the whole picture from a state map so each step only says what
     changed. `s` maps data-id → data-state ("focus" | "on" | "off" | "you" |
     "pain" | "ghost"); `extra` overrides the small text under a box.
     Rename the ids/labels for this session's main diagram.              */
  function mainDiagram(s = {{}}, extra = {{}}) {{
    const st = (id) => (s[id] ? ` data-state="${{s[id]}}"` : "");
    const ex = (id, dflt) => (extra[id] !== undefined ? extra[id] : dflt);
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-id="a"${{st("a")}}><b>Thing A</b><small>${{ex("a", "what it is")}}</small></div>
    <div class="dg-arrow" data-dir="right">relation</div>
    <div class="dg-box" data-id="b"${{st("b")}}><b>Thing B</b><small>${{ex("b", "what it is")}}</small></div>
    <div class="dg-arrow" data-dir="right">relation</div>
    <div class="dg-box" data-id="c"${{st("c")}}><b>Thing C</b><small>${{ex("c", "what it is")}}</small></div>
  </div>
</div>`;
  }}

  /* ---- rail presets: 2–3 keys that CHANGE across this session ---------- */
  const rail = {{
    start: {{ {rail_start} }},
    end:   {{ {rail_end} }},
  }};

  KSS.defineDeck({{
    id: "session-{num}",
    title: "{title_js}",
    plannedMinutes: {minutes},
    steps: [

      /* ===== Opening ===================================================== */
      {{
        id: "open-question",
        section: "Session {num}",
        title: "EXAMPLE — {title_js}",
        caption: "EXAMPLE — the question the whole session answers.",
        visual: {{ key: "intro", html: `
<div class="dg">
  <div class="dg-row dg-center">
    <div class="dg-box" data-grow="2" data-state="focus"><b>The familiar thing</b><small>what they already know</small></div>
    <div class="dg-arrow" data-dir="right">?</div>
    <div class="dg-box" data-grow="2"><b>The result</b><small>what they see happen</small></div>
  </div>
</div>` }},
        cues: [
          "EXAMPLE — Ask the room: …",
          "EXAMPLE — Set the frame: what today is and is not about.",
        ],
      }},

      /* ===== Stage 1 ==================================================== */
      {{
        id: "stage1-what",
        section: "1 · First stage",
        title: "EXAMPLE — The claim, in one line",
        caption: "EXAMPLE — the consequence, in one sentence.",
        rail: rail.start,
        visual: {{ key: "main", html: mainDiagram({{ a: "focus" }}) }},
        cues: ["EXAMPLE — bridge from what they know: …"],
      }},
      {{
        id: "stage1-why",
        section: "1 · First stage",
        title: "EXAMPLE — What changes, and why",
        caption: "EXAMPLE — let the morph land before you speak.",
        rail: rail.end,
        // same key as the previous step → the engine morphs a → b in place
        visual: {{ key: "main", html: mainDiagram({{ a: "on", b: "focus" }}, {{ b: "now active" }}) }},
        cues: ["EXAMPLE — WAR STORY (optional, verbal): …"],
      }},

    ],
  }});
}})();
'''


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", help="two-digit session number, e.g. 02")
    ap.add_argument("slug", help="kebab-case topic slug, e.g. userspace-kernel-boundary")
    ap.add_argument("--title", required=True, help="session title shown on the stage and launcher")
    ap.add_argument("--minutes", type=int, default=60, help="planned length (timer turns red past it)")
    ap.add_argument("--rail", default="Memory,CPU,Code",
                    help="comma-separated rail chip keys that change across the session")
    a = ap.parse_args()

    num = a.number.zfill(2)
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.slug):
        print("slug must be kebab-case: lowercase letters, digits, hyphens"); return 2
    folder = f"session-{num}-{a.slug}"
    sdir = os.path.join(KSS, folder)
    if os.path.exists(sdir):
        print(f"refusing to overwrite existing {folder}"); return 1

    src = newest_session()
    if not src:
        print("no existing session to copy show/present/index.html from"); return 1
    src_name = os.path.basename(src)
    m = re.match(r"session-(\d+)-", src_name)
    src_num = m.group(1) if m else "01"

    keys = [k.strip() for k in a.rail.split(",") if k.strip()]
    rail_start = ", ".join(f'{k}: "start value"' for k in keys)
    rail_end = ", ".join(f'{k}: ["end value", "ok"]' for k in keys)
    title_js = a.title.replace("\\", "\\\\").replace('"', '\\"')

    os.makedirs(sdir)
    with open(os.path.join(sdir, "STORY.md"), "w", encoding="utf-8") as f:
        f.write(STORY_TMPL.format(num=num, title=a.title, slug=folder))
    with open(os.path.join(sdir, "deck.js"), "w", encoding="utf-8") as f:
        f.write(DECK_TMPL.format(num=num, title=a.title, title_js=title_js, minutes=a.minutes,
                                 rail_start=rail_start, rail_end=rail_end))

    # copy the three pages, substituting session-specific strings
    src_title = None
    for page in ("show.html", "present.html", "index.html"):
        text = open(os.path.join(src, page), encoding="utf-8").read()
        text = text.replace(f"kss-show-session-{src_num}", f"kss-show-session-{num}")
        text = text.replace(f"kss-present-session-{src_num}", f"kss-present-session-{num}")
        text = re.sub(r"<title>KSS \d+ — (audience|presenter)</title>", rf"<title>KSS {int(num)} — \1</title>", text)
        text = re.sub(r"KSS · Session \d+", f"KSS · Session {int(num)}", text)
        if page == "index.html":
            text = re.sub(r"<title>.*?</title>", f"<title>KSS {int(num)} — {a.title}</title>", text, count=1)
            # headline + lead are session copy; replace with placeholders the author must edit
            text = re.sub(r'(<h1 class="t-display">)(.*?)(</h1>)', rf"\1{a.title}\3", text, flags=re.S)
            text = re.sub(r'(<p class="t-lead">)(.*?)(</p>)',
                          r"\1EDIT ME — one sentence on what this session covers.\3", text, count=1, flags=re.S)
        with open(os.path.join(sdir, page), "w", encoding="utf-8") as f:
            f.write(text)

    r = subprocess.run([sys.executable, os.path.join(HERE, "build_deck.py"), folder], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print(r.stderr.strip()); return 1

    print(f"""
created docs/kss/{folder}/
  STORY.md         3 EXAMPLE beats with markers — replace with the reviewed story
  deck.js          3 EXAMPLE steps + a morphing helper — replace per marker
  deck-content.js  generated
  show.html, present.html, index.html   copied from {src_name}

next:
  python3 -m http.server 8765 --directory docs/kss   →  http://localhost:8765/{folder}/
  write STORY.md → review → python3 docs/kss/_shared/build_deck.py {folder} → write deck.js
  python3 docs/kss/_shared/check.py
  add a row to docs/kss/README.md
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
