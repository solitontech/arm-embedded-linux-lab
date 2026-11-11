/* ==========================================================================
   Session 03 — How Linux knows your hardware exists — deck definition
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
(() => {
  /* ---- morphing diagram helper ----------------------------------------
     Render the whole picture from a state map so each step only says what
     changed. `s` maps data-id → data-state ("focus" | "on" | "off" | "you" |
     "pain" | "ghost"); `extra` overrides the small text under a box.
     Rename the ids/labels for this session's main diagram.              */
  function mainDiagram(s = {}, extra = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const ex = (id, dflt) => (extra[id] !== undefined ? extra[id] : dflt);
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-id="a"${st("a")}><b>Thing A</b><small>${ex("a", "what it is")}</small></div>
    <div class="dg-arrow" data-dir="right">relation</div>
    <div class="dg-box" data-id="b"${st("b")}><b>Thing B</b><small>${ex("b", "what it is")}</small></div>
    <div class="dg-arrow" data-dir="right">relation</div>
    <div class="dg-box" data-id="c"${st("c")}><b>Thing C</b><small>${ex("c", "what it is")}</small></div>
  </div>
</div>`;
  }

  /* ---- rail presets: 2–3 keys that CHANGE across this session ---------- */
  const rail = {
    start: { Described by: "start value", Bound to: "start value", Visible as: "start value" },
    end:   { Described by: ["end value", "ok"], Bound to: ["end value", "ok"], Visible as: ["end value", "ok"] },
  };

  KSS.defineDeck({
    id: "session-03",
    title: "How Linux knows your hardware exists",
    plannedMinutes: 60,
    steps: [

      /* ===== Opening ===================================================== */
      {
        id: "open-question",
        section: "Session 03",
        title: "EXAMPLE — How Linux knows your hardware exists",
        caption: "EXAMPLE — the question the whole session answers.",
        visual: { key: "intro", html: `
<div class="dg">
  <div class="dg-row dg-center">
    <div class="dg-box" data-grow="2" data-state="focus"><b>The familiar thing</b><small>what they already know</small></div>
    <div class="dg-arrow" data-dir="right">?</div>
    <div class="dg-box" data-grow="2"><b>The result</b><small>what they see happen</small></div>
  </div>
</div>` },
        cues: [
          "EXAMPLE — Ask the room: …",
          "EXAMPLE — Set the frame: what today is and is not about.",
        ],
      },

      /* ===== Stage 1 ==================================================== */
      {
        id: "stage1-what",
        section: "1 · First stage",
        title: "EXAMPLE — The claim, in one line",
        caption: "EXAMPLE — the consequence, in one sentence.",
        rail: rail.start,
        visual: { key: "main", html: mainDiagram({ a: "focus" }) },
        cues: ["EXAMPLE — bridge from what they know: …"],
      },
      {
        id: "stage1-why",
        section: "1 · First stage",
        title: "EXAMPLE — What changes, and why",
        caption: "EXAMPLE — let the morph land before you speak.",
        rail: rail.end,
        // same key as the previous step → the engine morphs a → b in place
        visual: { key: "main", html: mainDiagram({ a: "on", b: "focus" }, { b: "now active" }) },
        cues: ["EXAMPLE — WAR STORY (optional, verbal): …"],
      },

    ],
  });
})();
