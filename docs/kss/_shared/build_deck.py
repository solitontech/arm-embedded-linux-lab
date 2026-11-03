#!/usr/bin/env python3
"""Generate deck-content.js (presenter notes per step) from a session's STORY.md.

Usage:
    python3 docs/kss/_shared/build_deck.py session-01-boot-flow
    python3 docs/kss/_shared/build_deck.py session-01-boot-flow --check   # exit 1 if stale

STORY.md contract
    <!-- step: some-id -->   starts a beat; prose runs until the next marker,
                             the next "## " heading, or <!-- /steps -->
    **Visual:** / **Rail state:**  paragraphs are authoring notes and are dropped
    Supported markdown: ##/###/#### headings, paragraphs, **bold**, *em*,
    `code`, fenced code blocks, - / 1. lists, > quotes, | pipe | tables |,
    horizontal rules (---). Anything else is passed through as text.

Output
    window.KSS_CONTENT = { "some-id": "<p>…</p>", … };
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KSS = os.path.dirname(HERE)

STEP_RE = re.compile(r"^<!--\s*step:\s*([\w-]+)\s*-->\s*$")
END_RE = re.compile(r"^<!--\s*/steps\s*-->\s*$")
NOTE_RE = re.compile(r"^\*\*(Visual|Rail state):\*\*")


# ---------------------------------------------------------------------------
# Split STORY.md into {id: [lines]}
# ---------------------------------------------------------------------------
def split_steps(text: str) -> dict[str, list[str]]:
    steps: dict[str, list[str]] = {}
    current: str | None = None
    order: list[str] = []
    for line in text.splitlines():
        m = STEP_RE.match(line)
        if m:
            current = m.group(1)
            if current in steps:
                raise SystemExit(f"duplicate step marker: {current}")
            steps[current] = []
            order.append(current)
            continue
        if END_RE.match(line) or line.startswith("## "):
            current = None
            continue
        if current is not None:
            steps[current].append(line)
    return steps


# ---------------------------------------------------------------------------
# Inline markdown
# ---------------------------------------------------------------------------
def inline(s: str) -> str:
    # protect code spans first
    codes: list[str] = []

    def stash(m):
        codes.append(f"<code>{html.escape(m.group(1))}</code>")
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", stash, s)
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)
    return s


# ---------------------------------------------------------------------------
# Block markdown (subset)
# ---------------------------------------------------------------------------
def render(lines: list[str]) -> str:
    out: list[str] = []
    i = 0
    n = len(lines)

    def flush_para(buf: list[str]):
        if not buf:
            return
        text = " ".join(x.strip() for x in buf)
        if NOTE_RE.match(text):
            return  # authoring note
        out.append(f"<p>{inline(text)}</p>")

    para: list[str] = []
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # blank line ends a paragraph
        if not stripped:
            flush_para(para); para = []
            i += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            flush_para(para); para = []
            lang = stripped[3:].strip()
            buf = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1  # closing fence
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        # headings (### and #### inside a step; ## never reaches here)
        m = re.match(r"^(#{3,4})\s+(.*)$", stripped)
        if m:
            flush_para(para); para = []
            level = len(m.group(1)) + 1  # ### -> h4, #### -> h5 (presenter notes sit under a step title)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # horizontal rule
        if re.match(r"^-{3,}$", stripped):
            flush_para(para); para = []
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            flush_para(para); para = []
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip()); i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        # table
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            flush_para(para); para = []
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")
            continue

        # lists
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            flush_para(para); para = []
            ordered = m.group(2)[0].isdigit()
            tag = "ol" if ordered else "ul"
            items = []
            while i < n:
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not mm:
                    # continuation line of the previous item (indented, non-blank)
                    if items and lines[i].startswith("  ") and lines[i].strip():
                        items[-1] += " " + lines[i].strip(); i += 1; continue
                    break
                if (mm.group(2)[0].isdigit()) != ordered:
                    break
                items.append(mm.group(3)); i += 1
            lis = "".join(f"<li>{inline(it)}</li>" for it in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue

        # paragraph text
        para.append(line)
        i += 1

    flush_para(para)
    return "\n".join(out)


# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__); return 2
    session, check = argv[1], "--check" in argv
    sdir = os.path.join(KSS, session)
    story = os.path.join(sdir, "STORY.md")
    if not os.path.isfile(story):
        print(f"no STORY.md in {sdir}"); return 1
    steps = split_steps(open(story, encoding="utf-8").read())
    if not steps:
        print("no <!-- step: id --> markers found in STORY.md"); return 1
    content = {sid: render(lines) for sid, lines in steps.items()}
    empty = [sid for sid, h in content.items() if not h.strip()]
    if empty:
        print("steps with no presenter prose:", empty); return 1
    js = (
        "/* GENERATED from STORY.md by _shared/build_deck.py — do not edit by hand. */\n"
        "window.KSS_CONTENT = " + json.dumps(content, indent=2, ensure_ascii=False) + ";\n"
    )
    out = os.path.join(sdir, "deck-content.js")
    if check:
        current = open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        if current != js:
            print(f"STALE: {os.path.relpath(out, KSS)} differs from STORY.md — run build_deck.py {session}")
            return 1
        print(f"up to date: {os.path.relpath(out, KSS)} ({len(content)} steps)")
        return 0
    open(out, "w", encoding="utf-8").write(js)
    print(f"wrote {os.path.relpath(out, KSS)} — {len(content)} steps: {', '.join(content)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
