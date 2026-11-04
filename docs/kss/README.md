# KSS — Knowledge Sharing Sessions

Intuition-first sessions on embedded Linux for a mixed audience (students, RTOS/firmware engineers, application and driver developers). Each session is a **two-window deck** plus a live demo on lab hardware:

- **Audience window** — shared on the call. One title, one visual, one line per step. No paragraphs.
- **Presenter window** — on the speaker's own screen. Live mirror of the audience, full notes, cues, next step, timer.

The thread through the series: **"What sits between your code and the hardware, and why?"**

## Sessions

| # | Title | Core question | Status |
|---|---|---|---|
| 1 | [From power-on to a shell](session-01-boot-flow/index.html) · [story](session-01-boot-flow/STORY.md) | What runs before `main()`, who wrote it, and why there are five stages instead of one | Ready |
| 2 | Your code doesn't own the hardware anymore | What does the OS actually do between your code and the silicon? | Planned |
| 3 | How Linux knows your hardware exists | How does a peripheral at a fixed address become `/dev/something`? | Planned |

## Running a session

Serve the folder (sync between the two windows needs `http://`; `file://` pages are isolated from each other):

```bash
# from the repo root
python3 docs/kss/_shared/serve.py              # serve + open session 1 launcher
python3 docs/kss/_shared/serve.py 1 present    # session 1, presenter view
```

Runs in the foreground (Ctrl+C stops it) on `127.0.0.1`, picking the next free port if 8765 is taken. Over VS Code Remote-SSH, run it in the integrated terminal: VS Code forwards the printed `localhost` URL, so Ctrl+click opens it in your local browser.

The launcher page explains the Teams flow: open the presenter view on your screen, open the audience window from it, share **that window** (not your screen) in Teams, drive with `→`/`←` or a clicker. `B` blanks the audience window while you switch the share to a terminal for the demo.

## How a session is organised

```
docs/kss/
├── README.md                     ← this file: series index
├── _shared/
│   ├── kss.css                   ← tokens + dg-* diagram primitives
│   ├── deck.css                  ← audience stage + presenter console layouts, animations
│   ├── deck-engine.js            ← rendering, navigation, two-window sync, timer, validation
│   ├── new_session.py            ← scaffold a session folder (story + deck skeletons, pages)
│   ├── build_deck.py             ← STORY.md → deck-content.js (presenter prose)
│   ├── serve.py                  ← serve the decks locally and open a session's page
│   ├── check.py                  ← structural checks for every session (run before committing)
│   └── COMPONENTS.md             ← the contract + primitive catalogue for building a deck
└── session-NN-slug/
    ├── STORY.md                  ← the reviewed narrative with <!-- step: id --> markers — source of truth
    ├── deck.js                   ← what the audience sees per step + presenter cues
    ├── deck-content.js           ← GENERATED presenter prose; never hand-edited
    ├── show.html                 ← audience window
    ├── present.html              ← presenter window
    └── index.html                ← launcher + Teams instructions
```

Three rules keep this maintainable:

1. **Story first.** `STORY.md` is reviewed and approved as prose before `deck.js` exists. Presenter notes are generated from it, so there is exactly one copy of the prose. Each story ends with a *Review log* of what was cut and why.
2. **One idea per step.** The audience sees a title, a visual and at most one line. If a caption needs two sentences, it's two steps.
3. **Content in sessions, components in `_shared/`.** Session folders never carry their own CSS/JS. See [`_shared/COMPONENTS.md`](_shared/COMPONENTS.md).

## Adding a session

```bash
python3 docs/kss/_shared/new_session.py 02 userspace-kernel-boundary \
    --title "Your code doesn't own the hardware anymore" --rail Privilege,Memory,Who
```

Then follow the workflow: [`.agents/workflows/kss_new_session.md`](../../.agents/workflows/kss_new_session.md).

Two skills carry the method:
- [`kss-storytelling`](../../.agents/skills/kss-storytelling/SKILL.md) — the editorial half: what goes on the audience screen, in the presenter notes, or in spoken cues; the stage pattern; the cut rules.
- [`kss-deck-builder`](../../.agents/skills/kss-deck-builder/SKILL.md) — the build half: story beat → deck step, which diagram shape fits which concept, morphing, rail conventions, cue prefixes.

## Presenting

- The audience window is a fixed 16:9 stage that scales to any window, so it looks identical on your display and in the Teams share.
- Steps that share a diagram **morph** instead of cutting — let the change land before you speak over it.
- The presenter header dot: green = audience window in sync, amber = waiting, grey = no audience window answered, red = no sync channel (opened from `file://`).
- Print `STORY.md` (or share the link) as the post-session reference; the audience window is deliberately not readable on its own.
