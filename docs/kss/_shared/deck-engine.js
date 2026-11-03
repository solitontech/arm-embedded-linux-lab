/* ==========================================================================
   KSS Deck Engine
   One deck, two windows. Zero dependencies.

   Load order on a page:
     <script src="../_shared/deck-engine.js"></script>   (this file)
     <script src="deck-content.js"></script>             (GENERATED presenter prose)
     <script src="deck.js"></script>                     (session steps → KSS.defineDeck)
   Then the engine boots on DOMContentLoaded according to
     <body data-kss-view="show">     audience stage
     <body data-kss-view="present">  presenter console

   Deck shape (deck.js):
     KSS.defineDeck({
       id: 'session-01',           // BroadcastChannel name suffix
       title: 'From power-on to a shell',
       plannedMinutes: 60,         // optional, timer turns red past it
       steps: [{
         id: 'spl-dram',           // must match <!-- step: spl-dram --> in STORY.md
         section: '2 · SPL',       // eyebrow on stage
         title: 'One job: initialise the DRAM controller',
         visual: { key: 'soc', html: '<div class="dg">…</div>' },
         caption: 'Parameters only the board vendor knows.',   // optional
         rail: { Memory: ['SRAM → DRAM', 'ok'], CPU: 'from SRAM', Code: 'yours' }, // optional
         cues: ['Ask: who here has written DDR timing by hand?'],              // optional
       }, …]
     });

   Sync protocol (BroadcastChannel 'kss:' + deck.id):
     {t:'goto', i, from}  navigate      {t:'hello', from}  new window asks for state
     {t:'state', i}       reply         {t:'ack', i}        audience applied step i
     {t:'blank', on}      black screen
   ========================================================================== */
(() => {
  "use strict";

  const KSS = (window.KSS = window.KSS || {});
  let deck = null;

  KSS.defineDeck = (d) => { deck = d; };

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const STAGE_W = 1600, STAGE_H = 900;

  /* ------------------------------------------------------------------ */
  /* Validation                                                         */
  /* ------------------------------------------------------------------ */
  function validate(d) {
    const errs = [];
    if (!d) return ["No deck defined — deck.js did not call KSS.defineDeck()."];
    if (!d.id) errs.push("deck.id missing");
    if (!Array.isArray(d.steps) || !d.steps.length) errs.push("deck.steps is empty");
    const seen = new Set();
    const content = window.KSS_CONTENT || {};
    (d.steps || []).forEach((s, i) => {
      const where = `step ${i} (${s.id || "?"})`;
      if (!s.id) errs.push(`${where}: id missing`);
      else if (seen.has(s.id)) errs.push(`${where}: duplicate id`);
      seen.add(s.id);
      if (!s.title) errs.push(`${where}: title missing`);
      if (!s.visual || !s.visual.html) errs.push(`${where}: visual.html missing`);
      if (s.id && !content[s.id]) errs.push(`${where}: no presenter prose in deck-content.js (missing <!-- step: ${s.id} --> in STORY.md?)`);
    });
    Object.keys(content).forEach((id) => {
      if (!seen.has(id)) errs.push(`STORY.md step "${id}" has no entry in deck.js`);
    });
    return errs;
  }

  function showErrors(errs) {
    if (!errs.length) return;
    const el = document.createElement("div");
    el.className = "deck-error";
    el.textContent = "Deck problems:\n• " + errs.join("\n• ");
    document.body.appendChild(el);
    console.error("[kss]", errs);
  }

  /* ------------------------------------------------------------------ */
  /* Stage rendering                                                    */
  /* ------------------------------------------------------------------ */
  function buildStage() {
    const stage = document.createElement("div");
    stage.className = "stage";
    stage.innerHTML = `
      <div class="stage-top">
        <div class="stage-eyebrow" data-r="eyebrow"></div>
        <div class="stage-counter" data-r="counter"></div>
      </div>
      <div class="stage-body">
        <h1 class="stage-title" data-r="title"></h1>
        <div class="stage-visual" data-r="visual"></div>
        <p class="stage-caption" data-r="caption"></p>
      </div>
      <div class="stage-bottom">
        <div class="stage-rail" data-r="rail"></div>
      </div>
      <div class="stage-progress"><i data-r="progress"></i></div>`;
    return stage;
  }

  function q(root, name) { return root.querySelector(`[data-r="${name}"]`); }

  function renderRail(el, rail) {
    el.innerHTML = "";
    if (!rail) return;
    Object.entries(rail).forEach(([k, v]) => {
      const [text, tone] = Array.isArray(v) ? v : [v, ""];
      const span = document.createElement("span");
      if (tone) span.dataset.tone = tone;
      span.innerHTML = `<i>${esc(k)}</i>${esc(text)}`;
      el.appendChild(span);
    });
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  // snapshot of data-id → data-state for morph detection
  function snapshot(visualEl) {
    const map = new Map();
    visualEl.querySelectorAll("[data-id]").forEach((n) => {
      map.set(n.dataset.id, { state: n.dataset.state || "", tone: n.dataset.tone || "" });
    });
    return map;
  }

  /**
   * Paint step `step` into `stage`. `prev` is the previously painted step
   * (or null). Returns nothing; animations are CSS-driven.
   */
  function paint(stage, step, index, total, prev, { animate = true } = {}) {
    const eyebrow = q(stage, "eyebrow"), counter = q(stage, "counter"),
          title = q(stage, "title"), visual = q(stage, "visual"),
          caption = q(stage, "caption"), rail = q(stage, "rail"),
          progress = q(stage, "progress");

    const sameKey = !!(prev && prev.visual && step.visual && prev.visual.key && prev.visual.key === step.visual.key);
    const doAnim = animate && !reduceMotion.matches;

    const apply = () => {
      eyebrow.textContent = step.section || "";
      counter.textContent = `${index + 1} / ${total}`;
      title.textContent = step.title || "";
      caption.textContent = step.caption || "";
      renderRail(rail, step.rail);
      progress.style.transform = `scaleX(${(index + 1) / total})`;

      const before = sameKey ? snapshot(visual) : null;
      visual.innerHTML = step.visual.html;
      stage.classList.remove("is-building");

      if (sameKey && before) {
        // Morph: new elements build in; changed elements transition from old state.
        visual.querySelectorAll("[data-id]").forEach((n) => {
          const old = before.get(n.dataset.id);
          if (!old) { n.classList.add("is-new"); return; }
          const newState = n.dataset.state || "", newTone = n.dataset.tone || "";
          if (old.state !== newState || old.tone !== newTone) {
            // apply the old value, force layout, then flip → CSS transition runs
            if (old.state) n.dataset.state = old.state; else delete n.dataset.state;
            if (old.tone) n.dataset.tone = old.tone; else delete n.dataset.tone;
            void n.offsetWidth;
            if (newState) n.dataset.state = newState; else delete n.dataset.state;
            if (newTone) n.dataset.tone = newTone; else delete n.dataset.tone;
            n.classList.add("is-changed");
          }
        });
      } else if (doAnim) {
        // Fresh visual: stagger-build every primitive
        let i = 0;
        visual.querySelectorAll(".dg-box, .dg-chip, .dg-mem-seg, .dg-group, .dg-term, .dg-tree").forEach((n) => {
          n.style.setProperty("--i", String(i++));
        });
        stage.classList.add("is-building");
      }
    };

    if (!doAnim || sameKey) {
      stage.classList.remove("is-leaving");
      apply();
      return;
    }
    // cross-fade: leave → swap → enter
    stage.classList.add("is-leaving");
    setTimeout(() => {
      apply();
      requestAnimationFrame(() => stage.classList.remove("is-leaving"));
    }, 180);
  }

  function fitStage(stage, viewport) {
    const w = viewport.clientWidth, h = viewport.clientHeight;
    if (!w || !h) return;
    const s = Math.min(w / STAGE_W, h / STAGE_H);
    stage.style.transform = `scale(${s})`;
  }

  /* ------------------------------------------------------------------ */
  /* Navigation + sync (shared by both views)                           */
  /* ------------------------------------------------------------------ */
  function makeController({ role, onStep, onBlank }) {
    const total = deck.steps.length;
    let index = clamp(indexFromHash(), 0, total - 1);
    let blank = false;
    let channel = null;
    const me = role + "-" + Math.random().toString(36).slice(2, 7);
    const listeners = { ack: [], peer: [] };

    try {
      channel = new BroadcastChannel("kss:" + deck.id);
      channel.onmessage = (ev) => {
        const m = ev.data || {};
        if (m.from === me) return;
        if (m.t === "goto" && Number.isInteger(m.i)) { go(m.i, { broadcast: false }); emit("peer"); }
        else if (m.t === "hello") { channel.postMessage({ t: "state", i: index, from: me, role }); emit("peer"); }
        else if (m.t === "state" && Number.isInteger(m.i) && role === "show") { go(m.i, { broadcast: false }); emit("peer"); }
        else if (m.t === "ack") { listeners.ack.forEach((f) => f(m.i)); }
        else if (m.t === "blank") { setBlank(!!m.on, { broadcast: false }); }
      };
      channel.postMessage({ t: "hello", from: me, role });
    } catch (e) {
      channel = null; // file:// or very old browser — single-window mode still works
    }

    function emit(kind, ...args) { listeners[kind].forEach((f) => f(...args)); }

    function go(i, { broadcast = true } = {}) {
      i = clamp(i, 0, total - 1);
      const prev = deck.steps[index];
      const changed = i !== index;
      index = i;
      history.replaceState(null, "", `#${index + 1}`);
      onStep(deck.steps[index], index, total, changed ? prev : null);
      if (broadcast && channel) channel.postMessage({ t: "goto", i: index, from: me });
      if (role === "show" && channel) channel.postMessage({ t: "ack", i: index, from: me });
    }

    function setBlank(on, { broadcast = true } = {}) {
      blank = on;
      onBlank && onBlank(blank);
      if (broadcast && channel) channel.postMessage({ t: "blank", on: blank, from: me });
    }

    document.addEventListener("keydown", (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;
      switch (e.key) {
        case "ArrowRight": case "ArrowDown": case "PageDown": case " ": case "Enter": case "j": case "n":
          e.preventDefault(); go(index + 1); break;
        case "ArrowLeft": case "ArrowUp": case "PageUp": case "Backspace": case "k": case "p":
          e.preventDefault(); go(index - 1); break;
        case "Home": e.preventDefault(); go(0); break;
        case "End":  e.preventDefault(); go(total - 1); break;
        case "b": case "B": case ".": e.preventDefault(); setBlank(!blank); break;
        case "f": case "F": e.preventDefault(); toggleFullscreen(); break;
        default: return;
      }
    });

    window.addEventListener("hashchange", () => {
      const i = indexFromHash();
      if (i !== index) go(i);
    });

    // initial paint (no animation, no broadcast — the hello/state exchange settles it)
    onStep(deck.steps[index], index, total, null, { animate: false });
    if (role === "show" && channel) channel.postMessage({ t: "ack", i: index, from: me });

    return {
      go, next: () => go(index + 1), prev: () => go(index - 1),
      get index() { return index; }, get total() { return total; },
      get hasChannel() { return !!channel; },
      on: (kind, f) => listeners[kind].push(f),
      setBlank,
    };
  }

  function indexFromHash() {
    const n = parseInt(location.hash.slice(1), 10);
    return Number.isFinite(n) && n > 0 ? n - 1 : 0;
  }
  function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

  function toggleFullscreen() {
    const el = document.documentElement;
    if (!document.fullscreenElement) (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el);
    else (document.exitFullscreen || document.webkitExitFullscreen || function () {}).call(document);
  }

  /* ------------------------------------------------------------------ */
  /* View: audience                                                     */
  /* ------------------------------------------------------------------ */
  function bootShow() {
    const viewport = document.querySelector(".stage-viewport") || document.body;
    const stage = buildStage();
    viewport.appendChild(stage);
    const fit = () => fitStage(stage, viewport);
    window.addEventListener("resize", fit);
    fit();
    document.title = `${deck.title} — audience`;

    makeController({
      role: "show",
      onStep: (step, i, total, prev, opts) => paint(stage, step, i, total, prev, opts),
      onBlank: (on) => { stage.dataset.blank = on ? "true" : "false"; },
    });

    // click/tap on the stage advances (handy on a touch screen)
    stage.addEventListener("click", (e) => {
      const rect = stage.getBoundingClientRect();
      const left = (e.clientX - rect.left) < rect.width * 0.25;
      document.dispatchEvent(new KeyboardEvent("keydown", { key: left ? "ArrowLeft" : "ArrowRight" }));
    });
  }

  /* ------------------------------------------------------------------ */
  /* View: presenter                                                    */
  /* ------------------------------------------------------------------ */
  function bootPresent() {
    document.title = `${deck.title} — presenter`;
    const content = window.KSS_CONTENT || {};

    const $ = (sel) => document.querySelector(sel);
    const mirrorWrap = $(".mirror-wrap");
    const mirror = buildStage();
    mirrorWrap.appendChild(mirror);
    const fitMirror = () => {
      const w = mirrorWrap.clientWidth;
      if (w) mirror.style.transform = `scale(${w / STAGE_W})`;
    };
    window.addEventListener("resize", fitMirror);

    const elTitle = $("[data-p='title']"), elEyebrow = $("[data-p='eyebrow']"),
          elNotes = $("[data-p='notes']"), elCues = $("[data-p='cues']"),
          elNext = $("[data-p='next']"), elCounter = $("[data-p='counter']"),
          elTimer = $("[data-p='timer']"), elSync = $("[data-p='sync']"),
          elOutline = $("[data-p='outline']"), elDeckTitle = $("[data-p='deck-title']");

    if (elDeckTitle) elDeckTitle.textContent = deck.title;

    // outline (grouped by section)
    if (elOutline) {
      let lastSec = null;
      deck.steps.forEach((s, i) => {
        if (s.section !== lastSec) {
          const h = document.createElement("div"); h.className = "sec"; h.textContent = s.section || ""; elOutline.appendChild(h);
          lastSec = s.section;
        }
        const a = document.createElement("a");
        a.href = `#${i + 1}`;
        a.innerHTML = `<span>${i + 1}</span><span>${esc(s.title)}</span>`;
        a.addEventListener("click", (e) => { e.preventDefault(); ctl.go(i); });
        elOutline.appendChild(a);
      });
    }

    // timer
    let startedAt = null;
    const planned = (deck.plannedMinutes || 0) * 60000;
    function tickTimer() {
      if (!elTimer) return;
      if (!startedAt) { elTimer.textContent = "00:00"; return; }
      const ms = Date.now() - startedAt;
      const m = Math.floor(ms / 60000), s = Math.floor((ms % 60000) / 1000);
      elTimer.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
      elTimer.dataset.over = planned && ms > planned ? "true" : "false";
    }
    setInterval(tickTimer, 500);
    const resetTimer = () => { startedAt = Date.now(); tickTimer(); };
    document.addEventListener("keydown", (e) => { if (e.key === "r" || e.key === "R") resetTimer(); });

    // sync indicator
    let ackTimer = null;
    function setSync(state) { if (elSync) elSync.dataset.state = state; }

    const ctl = makeController({
      role: "present",
      onStep: (step, i, total, prev, opts) => {
        if (!startedAt && i > 0) startedAt = Date.now();
        paint(mirror, step, i, total, prev, opts);
        if (elEyebrow) elEyebrow.textContent = step.section || "";
        if (elTitle) elTitle.textContent = step.title || "";
        if (elCounter) elCounter.textContent = `${i + 1} / ${total}`;
        if (elNotes) elNotes.innerHTML = content[step.id] || "<p><em>No notes for this step.</em></p>";
        if (elCues) {
          elCues.innerHTML = step.cues && step.cues.length
            ? `<div class="t-micro">Say — not on screen</div><ul>${step.cues.map((c) => `<li>${c}</li>`).join("")}</ul>`
            : "";
        }
        if (elNext) {
          const n = deck.steps[i + 1];
          elNext.innerHTML = n
            ? `<div class="t-micro">Next</div><div class="next-eyebrow">${esc(n.section || "")}</div><div class="next-title">${esc(n.title)}</div>${n.caption ? `<div class="next-caption">${esc(n.caption)}</div>` : ""}`
            : `<div class="t-micro">Next</div><div class="next-title">— end of deck —</div>`;
        }
        if (elOutline) {
          elOutline.querySelectorAll("a").forEach((a, k) => { if (k === i) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current"); });
          const cur = elOutline.querySelector("a[aria-current]"); if (cur) cur.scrollIntoView({ block: "nearest" });
        }
        if (elNotes) elNotes.scrollTop = 0;

        // expect an ack from the audience window
        if (ctl && ctl.hasChannel) {
          setSync("stale");
          clearTimeout(ackTimer);
          ackTimer = setTimeout(() => { if (elSync && elSync.dataset.state === "stale") setSync("none"); }, 1200);
        }
      },
    });

    if (!ctl.hasChannel) setSync("nochan");
    ctl.on("ack", (i) => { if (i === ctl.index) { clearTimeout(ackTimer); setSync("live"); } });
    ctl.on("peer", () => setSync("live"));

    // buttons
    $("[data-p='open-show']")?.addEventListener("click", () => {
      window.open("show.html#" + (ctl.index + 1), "kss-show-" + deck.id, "popup=yes,width=1280,height=720");
    });
    $("[data-p='prev']")?.addEventListener("click", ctl.prev);
    $("[data-p='next-btn']")?.addEventListener("click", ctl.next);
    $("[data-p='reset-timer']")?.addEventListener("click", resetTimer);
    $("[data-p='blank']")?.addEventListener("click", () => document.dispatchEvent(new KeyboardEvent("keydown", { key: "b" })));

    requestAnimationFrame(fitMirror);
    tickTimer();
  }

  /* ------------------------------------------------------------------ */
  document.addEventListener("DOMContentLoaded", () => {
    const view = document.body.dataset.kssView;
    const errs = validate(deck);
    if (errs.length) { showErrors(errs); if (!deck || !deck.steps || !deck.steps.length) return; }
    if (view === "show") bootShow();
    else if (view === "present") bootPresent();
  });
})();
