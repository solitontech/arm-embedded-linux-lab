# KSS — Knowledge Sharing Sessions

Interactive, intuition-first sessions on embedded Linux for a mixed audience (students, RTOS/firmware engineers, application and driver developers). Each session is a single web page plus a live demo on lab hardware.

The thread through the series: **"What sits between your code and the hardware, and why?"**

## Sessions

| # | Title | Core question | Status |
|---|---|---|---|
| 1 | [From power-on to a shell](session-01-boot-flow/index.html) · [story](session-01-boot-flow/STORY.md) | What runs before `main()`, who wrote it, and why there are five stages instead of one | Ready |
| 2 | Your code doesn't own the hardware anymore | What does the OS actually do between your code and the silicon? | Planned |
| 3 | How Linux knows your hardware exists | How does a peripheral at a fixed address become `/dev/something`? | Planned |

Open a session with any browser — no build step, no server needed:

```bash
# from the repo root
xdg-open docs/kss/session-01-boot-flow/index.html     # Linux
open     docs/kss/session-01-boot-flow/index.html     # macOS
```

Or serve the folder so hash links and the shared assets resolve the same way they will for the audience:

```bash
python3 -m http.server 8765 --directory docs/kss
# → http://localhost:8765/session-01-boot-flow/
```

## How a session is organised

```
docs/kss/
├── README.md                     ← this file: series index
├── _shared/
│   ├── kss.css                   ← design system (tokens, typography, stage chain, diagrams)
│   ├── kss.js                    ← interactions (expand/collapse, rail sync, keyboard, deep links)
│   ├── check.py                  ← structural checks for pages + stylesheet (run before committing)
│   └── COMPONENTS.md             ← component catalogue: copy-paste markup for every block
└── session-NN-slug/
    ├── STORY.md                  ← the reviewed narrative — source of truth for the page
    └── index.html                ← the page, built from STORY.md using _shared components
```

Two rules keep this maintainable:

1. **`STORY.md` first, `index.html` second.** The narrative is reviewed and approved as prose before any HTML exists. If the story changes, change `STORY.md`, then the page. The review log at the bottom of each story records what was cut and why, so the next session starts from those lessons.
2. **Session folders contain content, not CSS.** Anything visual or interactive that could serve more than one session lives in `_shared/`. See [`_shared/COMPONENTS.md`](_shared/COMPONENTS.md).

## Adding a session

Follow the workflow: [`.agents/workflows/kss_new_session.md`](../../.agents/workflows/kss_new_session.md).

The method for writing the story — what to include, what to cut, how to split speaker vs page — is captured in the skill: [`.agents/skills/kss-storytelling/SKILL.md`](../../.agents/skills/kss-storytelling/SKILL.md).

## Presenting

- The page is the written half; the speaker is the verbal half. The page never carries anecdotes, lab war stories, or "why we chose this approach" — those are yours to say out loud. Each `STORY.md` has a *Who says what* table.
- `↓` / `↑` step through stages. The URL hash follows, so you can bookmark a stage.
- The page is high-contrast and large-type by design; it reads on a projector without zooming.
- Print to PDF for a handout: all stages expand, the rail drops out.
