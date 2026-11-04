#!/usr/bin/env python3
"""Structural checks for KSS sessions (two-window decks).

Run from anywhere:  python3 docs/kss/_shared/check.py
Exit code 1 on any failure so it can gate a commit.

Checks
  stylesheets (kss.css, deck.css)
    - comments stripped the way a browser does (a comment ends at the FIRST */)
    - every rule prelude looks like a selector / at-rule (catches a comment that
      ended early and swallowed the next rule)
    - critical rules survived (:root tokens, body background, .stage, .console)
    - brace balance
  every docs/kss/session-*/
    - STORY.md has <!-- step: id --> markers, no duplicates
    - deck.js step ids == STORY.md marker ids (both directions), no duplicates
    - every deck.js step has title + visual.html
    - deck-content.js is up to date (re-generated output == committed file)
    - show.html / present.html / index.html exist and load the right scripts
      in the right order; present.html has every data-p slot the engine uses
    - HTML tags balanced, no duplicate ids
    - every class used in deck.js visuals and the HTML files is defined in CSS
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
KSS = os.path.dirname(HERE)

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print("  FAIL:", msg)


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_rules(css: str, name: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    buf, stack = "", []
    for ch in css:
        if ch == "{":
            stack.append(buf.split(";")[-1].strip())  # drop statement at-rules like @charset …;
            buf = ""
        elif ch == "}":
            out.append((stack.pop() if stack else "?", buf.strip()))
            buf = ""
        else:
            buf += ch
    if stack:
        fail(f"{name}: {len(stack)} unclosed block(s)")
    return out


SELECTOR_OK = re.compile(r"^(@[\w-]+[^{]*|[\w\s.#:\[\]=\"'*>+~(),%-]+)$")
CRITICAL = {
    "kss.css": {
        ":root": ["--bg", "--text", "--accent", "--surface"],
        "body": ["background: var(--bg)", "color: var(--text)"],
        ".dg-box": ["border"],
    },
    "deck.css": {
        ".stage": ["width: 1600px", "height: 900px"],
        ".console": ["display: grid"],
    },
}


def check_css(name: str) -> set[str]:
    print(name)
    raw = open(os.path.join(HERE, name), encoding="utf-8").read()
    css = strip_comments(raw)
    if css.count("{") != css.count("}"):
        fail(f"{name}: brace mismatch {css.count('{')} vs {css.count('}')}")
    rules = css_rules(css, name)
    for prelude, _ in rules:
        if prelude and not SELECTOR_OK.match(prelude):
            fail(f"{name}: suspicious rule prelude (comment ended early?): {prelude[:80]!r}")
    for sel, needles in CRITICAL.get(name, {}).items():
        bodies = [b for p, b in rules if p == sel]
        if not bodies:
            fail(f"{name}: critical rule missing: {sel}")
            continue
        for n in needles:
            if not any(n in b for b in bodies):
                fail(f"{name}: {sel} is missing {n!r}")
    defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    print(f"  rules: {len(rules)}  classes: {len(defined)}")
    return defined


# --------------------------------------------------------------------------
# HTML helpers
# --------------------------------------------------------------------------
VOID = {"meta", "link", "br", "hr", "img", "input", "path", "source", "circle", "rect", "line"}


class Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.dups: list[str] = []
        self.errs: list[str] = []
        self.classes: set[str] = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            if d["id"] in self.ids:
                self.dups.append(d["id"])
            self.ids.add(d["id"])
        if d.get("class"):
            self.classes.update(d["class"].split())
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errs.append(f"stray </{tag}> at line {self.getpos()[0]}")
            return
        opened = self.stack.pop()
        if opened != tag:
            self.errs.append(f"<{opened}> closed by </{tag}> at line {self.getpos()[0]}")


def parse_html(path: str, rel: str) -> Balance:
    p = Balance()
    p.feed(open(path, encoding="utf-8").read())
    for e in p.errs:
        fail(f"{rel}: {e}")
    if p.stack:
        fail(f"{rel}: unclosed tags {p.stack}")
    for d in p.dups:
        fail(f"{rel}: duplicate id {d!r}")
    return p


SCRIPT_ORDER = ["../_shared/deck-engine.js", "deck-content.js", "deck.js"]
PRESENT_SLOTS = ["deck-title", "counter", "sync", "prev", "next-btn", "blank", "reset-timer", "timer",
                 "open-show", "next", "outline", "eyebrow", "title", "cues", "notes"]


def check_view(sdir: str, rel: str, name: str, view: str, defined: set[str]) -> None:
    path = os.path.join(sdir, name)
    if not os.path.isfile(path):
        fail(f"{rel}/{name} missing")
        return
    src = open(path, encoding="utf-8").read()
    p = parse_html(path, f"{rel}/{name}")
    if f'data-kss-view="{view}"' not in src:
        fail(f"{rel}/{name}: body lacks data-kss-view=\"{view}\"")
    scripts = re.findall(r'<script src="([^"]+)"', src)
    if scripts != SCRIPT_ORDER:
        fail(f"{rel}/{name}: scripts must be {SCRIPT_ORDER}, got {scripts}")
    for css in ("../_shared/kss.css", "../_shared/deck.css"):
        if f'href="{css}"' not in src:
            fail(f"{rel}/{name}: does not link {css}")
    if view == "present":
        for slot in PRESENT_SLOTS:
            if f'data-p="{slot}"' not in src:
                fail(f"{rel}/{name}: missing data-p=\"{slot}\" slot")
        if 'class="mirror-wrap"' not in src:
            fail(f"{rel}/{name}: missing .mirror-wrap")
    if view == "show" and 'class="stage-viewport"' not in src:
        fail(f"{rel}/{name}: missing .stage-viewport")
    for u in sorted(p.classes - defined):
        fail(f"{rel}/{name}: class .{u} is not defined in shared CSS")


# --------------------------------------------------------------------------
# Session
# --------------------------------------------------------------------------
# A real marker is alone on its line (the docs mention `<!-- step: id -->` inline).
STEP_MARK = re.compile(r"^<!--\s*step:\s*([\w-]+)\s*-->\s*$", re.M)
DECK_ID = re.compile(r"^\s*id:\s*[\"']([\w-]+)[\"']", re.M)


def check_session(sdir: str, defined: set[str]) -> None:
    rel = os.path.relpath(sdir, KSS)
    print(rel)

    story = os.path.join(sdir, "STORY.md")
    deck = os.path.join(sdir, "deck.js")
    content = os.path.join(sdir, "deck-content.js")
    for f in (story, deck, content):
        if not os.path.isfile(f):
            fail(f"{rel}/{os.path.basename(f)} missing")
    if failures:
        return

    story_ids = STEP_MARK.findall(open(story, encoding="utf-8").read())
    deck_src = open(deck, encoding="utf-8").read()
    # Only ids inside the steps array; the deck's own `id:` comes before `steps: [`.
    steps_src = deck_src.split("steps:", 1)[1] if "steps:" in deck_src else deck_src
    deck_ids = DECK_ID.findall(steps_src)

    for name, ids in (("STORY.md", story_ids), ("deck.js", deck_ids)):
        dups = sorted({i for i in ids if ids.count(i) > 1})
        if dups:
            fail(f"{rel}/{name}: duplicate step ids {dups}")
    if not story_ids:
        fail(f"{rel}/STORY.md: no <!-- step: id --> markers")
    if not deck_ids:
        fail(f"{rel}/deck.js: no steps found (expected lines like  id: 'xyz',)")

    only_story = [i for i in story_ids if i not in deck_ids]
    only_deck = [i for i in deck_ids if i not in story_ids]
    if only_story:
        fail(f"{rel}: steps in STORY.md with no deck.js entry: {only_story}")
    if only_deck:
        fail(f"{rel}: steps in deck.js with no STORY.md marker: {only_deck}")
    if story_ids == deck_ids:
        pass
    elif sorted(story_ids) == sorted(deck_ids):
        fail(f"{rel}: step order differs between STORY.md and deck.js")

    # each deck step has a title and visual html (cheap regex per step block)
    blocks = re.split(r"\n\s*\{\s*\n\s*id:", deck_src)[1:]
    for b in blocks:
        sid = re.match(r"\s*[\"']([\w-]+)", b)
        sid = sid.group(1) if sid else "?"
        if not re.search(r"\btitle:\s*[\"'`]", b):
            fail(f"{rel}/deck.js: step {sid} has no title")
        if not re.search(r"\bvisual:\s*\{", b):
            fail(f"{rel}/deck.js: step {sid} has no visual")

    # generated content is fresh
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_deck.py"), rel, "--check"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"{rel}: {r.stdout.strip() or r.stderr.strip()}")

    # classes used inside deck.js visuals exist
    used = set()
    for m in re.findall(r'class="([^"]+)"', deck_src):
        used.update(m.split())
    for u in sorted(used - defined):
        fail(f"{rel}/deck.js: class .{u} is not defined in shared CSS")

    check_view(sdir, rel, "show.html", "show", defined)
    check_view(sdir, rel, "present.html", "present", defined)
    launcher = os.path.join(sdir, "index.html")
    if os.path.isfile(launcher):
        parse_html(launcher, f"{rel}/index.html")
        lsrc = open(launcher, encoding="utf-8").read()
        for target in ("present.html", "show.html"):
            if f'href="{target}"' not in lsrc:
                fail(f"{rel}/index.html: no link to {target}")
    else:
        fail(f"{rel}/index.html (launcher) missing")

    print(f"  steps: {len(deck_ids)}  (story markers: {len(story_ids)})")


# --------------------------------------------------------------------------
# JS (static — no interpreter available in every environment)
# --------------------------------------------------------------------------
def check_engine() -> None:
    """Catch the two bugs that have actually bitten: a `const` read inside the
    arguments of its own initialiser (TDZ ReferenceError when the callee calls
    back synchronously), and unbalanced brackets."""
    name = "deck-engine.js"
    print(name)
    src = open(os.path.join(HERE, name), encoding="utf-8").read()

    for m in re.finditer(r"\bconst\s+(\w+)\s*=\s*(\w+)\(", src):
        var, fn = m.group(1), m.group(2)
        i, depth = m.end(), 1
        while i < len(src) and depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        args = re.sub(r'"[^"]*"|\'[^\']*\'', '""', src[m.end():i])
        if re.search(rf"(?<![\w.]){var}\b", args):
            fail(f"{name}: `const {var}` is read inside the arguments of {fn}(...) — "
                 f"TDZ error if {fn} calls back synchronously; declare with `let` first")

    err = js_bracket_error(src)
    if err:
        fail(f"{name}: {err}")


def js_bracket_error(src: str) -> str | None:
    """Single-pass scan that skips comments, strings, template literals (with
    ${} nesting) and regex literals, then checks bracket balance."""
    depth = {"(": 0, "{": 0, "[": 0}
    close = {")": "(", "}": "{", "]": "["}
    i, n, line = 0, len(src), 1
    last_sig = ""  # last significant char, to tell regex literals from division
    while i < n:
        c = src[i]
        if c == "\n":
            line += 1
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                return "unterminated block comment"
            line += src[i:j].count("\n")
            i = j + 2
            continue
        if c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                elif src[j] == "\n":
                    return f"line {line}: newline inside string"
                j += 1
            i = j + 1
            last_sig = c
            continue
        if c == "`":
            j, tdepth = i + 1, 0
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src.startswith("${", j):
                    tdepth += 1
                    j += 2
                    continue
                if src[j] == "}" and tdepth:
                    tdepth -= 1
                    j += 1
                    continue
                if src[j] == "`" and not tdepth:
                    break
                if src[j] == "\n":
                    line += 1
                j += 1
            i = j + 1
            last_sig = "`"
            continue
        if c == "/" and last_sig in "(,=:[!&|?{};" or (c == "/" and last_sig == ""):
            # regex literal: skip to the unescaped closing slash (not inside a class)
            j, in_class = i + 1, False
            while j < n and (src[j] != "/" or in_class):
                if src[j] == "\\":
                    j += 1
                elif src[j] == "[":
                    in_class = True
                elif src[j] == "]":
                    in_class = False
                elif src[j] == "\n":
                    return f"line {line}: newline inside regex literal"
                j += 1
            i = j + 1
            while i < n and src[i].isalpha():  # flags
                i += 1
            last_sig = "/"
            continue
        if c in depth:
            depth[c] += 1
        elif c in close:
            depth[close[c]] -= 1
            if depth[close[c]] < 0:
                return f"line {line}: unexpected '{c}'"
        if not c.isspace():
            last_sig = c
        i += 1
    bad = {k: v for k, v in depth.items() if v}
    return f"unbalanced brackets at EOF: {bad}" if bad else None


def main() -> int:
    defined = check_css("kss.css") | check_css("deck.css")
    check_engine()
    sessions = sorted(d for d in glob.glob(os.path.join(KSS, "session-*")) if os.path.isdir(d))
    if not sessions:
        fail("no session folders found")
    for s in sessions:
        check_session(s, defined)
    print()
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
