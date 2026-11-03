#!/usr/bin/env python3
"""Structural checks for KSS pages and the shared stylesheet.

Run from anywhere:  python3 docs/kss/_shared/check.py
Exit code 1 on any failure so it can gate a commit.

Checks
  kss.css
    - comments stripped the way a browser does (a comment ends at the FIRST */)
    - every rule prelude looks like a selector / at-rule (catches a comment
      that ended early and swallowed the next rule)
    - critical rules survived: :root tokens, .kss-page grid, body background
    - brace balance
  every docs/kss/session-*/index.html
    - balanced tags, no duplicate ids
    - every rail-nav href="#id" resolves
    - every .kss-stage carries every data-rail-<key> the rail reads
    - every stage has head / body / inner / prose / visual
    - every class used is defined in kss.css
    - links ../_shared/kss.css and ../_shared/kss.js
"""
from __future__ import annotations

import glob
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
KSS = os.path.dirname(HERE)
CSS = os.path.join(HERE, "kss.css")

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print("  FAIL:", msg)


# --------------------------------------------------------------------------
# CSS
# --------------------------------------------------------------------------
def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def css_rules(css: str) -> list[tuple[str, str]]:
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
        fail(f"kss.css: {len(stack)} unclosed block(s)")
    return out


SELECTOR_OK = re.compile(r"^(@[\w-]+[^{]*|[\w\s.#:\[\]=\"'*>+~(),%-]+)$")
CRITICAL = {
    ":root": ["--bg", "--text", "--rail-w", "--accent", "--surface"],
    ".kss-page": ["display: grid", "grid-template-columns"],
    "body": ["background: var(--bg)", "color: var(--text)"],
    ".kss-stage.is-active .kss-stage-body": ["grid-template-rows: 1fr"],
}


def check_css() -> set[str]:
    print("kss.css")
    raw = open(CSS, encoding="utf-8").read()
    css = strip_comments(raw)
    if css.count("{") != css.count("}"):
        fail(f"brace mismatch: {css.count('{')} open vs {css.count('}')} close")
    rules = css_rules(css)
    for prelude, _ in rules:
        if prelude and not SELECTOR_OK.match(prelude):
            fail(f"suspicious rule prelude (comment ended early?): {prelude[:80]!r}")
    for sel, needles in CRITICAL.items():
        bodies = [b for p, b in rules if p == sel]
        if not bodies:
            fail(f"critical rule missing: {sel}")
            continue
        for n in needles:
            if not any(n in b for b in bodies):
                fail(f"{sel} is missing {n!r}")
    defined = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    print(f"  rules: {len(rules)}  classes: {len(defined)}")
    return defined


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
VOID = {"meta", "link", "br", "hr", "img", "input", "path", "source", "circle", "rect", "line"}


class Balance(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.ids: set[str] = set()
        self.dups: list[str] = []
        self.errs: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            if d["id"] in self.ids:
                self.dups.append(d["id"])
            self.ids.add(d["id"])
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


def check_page(path: str, defined_classes: set[str]) -> None:
    rel = os.path.relpath(path, KSS)
    print(rel)
    src = open(path, encoding="utf-8").read()

    p = Balance()
    p.feed(src)
    for e in p.errs:
        fail(f"{rel}: {e}")
    if p.stack:
        fail(f"{rel}: unclosed tags {p.stack}")
    for d in p.dups:
        fail(f"{rel}: duplicate id {d!r}")

    if 'href="../_shared/kss.css"' not in src:
        fail(f"{rel}: does not link ../_shared/kss.css")
    if 'src="../_shared/kss.js"' not in src:
        fail(f"{rel}: does not load ../_shared/kss.js")

    nav = re.search(r'class="kss-rail-nav".*?</nav>', src, re.S)
    for href in re.findall(r'href="#([^"]+)"', nav.group(0) if nav else ""):
        if href not in p.ids:
            fail(f"{rel}: rail nav links to missing #{href}")

    rail_keys = set(re.findall(r'data-rail="(\w+)"', src))
    stages = re.findall(r'<article class="kss-stage" id="([^"]+)"([^>]*)>', src)
    if not stages:
        fail(f"{rel}: no .kss-stage articles found")
    for sid, attrs in stages:
        for k in rail_keys:
            if f"data-rail-{k}=" not in attrs:
                fail(f"{rel}: {sid} missing data-rail-{k}")
        block = re.search(rf'id="{re.escape(sid)}".*?</article>', src, re.S).group(0)
        for cls in ("kss-stage-head", "kss-stage-body", "kss-stage-inner", "prose", "kss-visual"):
            if cls not in block:
                fail(f"{rel}: {sid} has no .{cls}")

    used: set[str] = set()
    for m in re.findall(r'class="([^"]+)"', src):
        used.update(m.split())
    for u in sorted(used - defined_classes):
        fail(f"{rel}: class .{u} is not defined in kss.css")

    print(f"  stages: {len(stages)}  rail keys: {sorted(rail_keys)}")


def main() -> int:
    defined = check_css()
    pages = sorted(glob.glob(os.path.join(KSS, "session-*", "index.html")))
    if not pages:
        fail("no session pages found")
    for page in pages:
        check_page(page, defined)
    print()
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
