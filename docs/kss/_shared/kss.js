/* ==========================================================================
   KSS Shared Interactions
   Zero dependencies. Progressive enhancement: the page is fully readable
   with JS disabled (all stage bodies are in the DOM; CSS collapses them).

   Markup contract (see docs/kss/_shared/COMPONENTS.md):

     <div class="kss-chain" data-kss-chain>
       <article class="kss-stage" id="stage-rbl"
                data-rail-memory="On-chip SRAM only"
                data-rail-memory-tone="blocked"
                data-rail-cpu="Executing from ROM"
                data-rail-code="Immutable (mask ROM)">
         <button class="kss-stage-head" aria-expanded="false" aria-controls="stage-rbl-body">…</button>
         <div class="kss-stage-body" id="stage-rbl-body" role="region"><div><div class="kss-stage-inner">…</div></div></div>
       </article>
       …
     </div>

     <dl data-kss-rail>
       <dt>Memory</dt><dd data-rail="memory">—</dd>
       <dt>CPU</dt>   <dd data-rail="cpu">—</dd>
       <dt>Code</dt>  <dd data-rail="code">—</dd>
     </dl>

   Behaviour:
   - One stage open at a time; clicking the open one closes it.
   - Rail <dd>s update from the active stage's data-rail-* attributes.
   - ArrowDown / ArrowUp / j / k step through stages (presenter-friendly).
   - URL hash (#stage-rbl) opens that stage on load and is kept in sync.
   - Nothing is locked during transitions; a second click mid-animation
     simply re-targets.
   ========================================================================== */
(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  document.querySelectorAll("[data-kss-chain]").forEach(initChain);

  function initChain(chain) {
    const stages = Array.from(chain.querySelectorAll(".kss-stage"));
    if (!stages.length) return;

    const rail = document.querySelector("[data-kss-rail]");
    const railFields = rail
      ? Array.from(rail.querySelectorAll("[data-rail]"))
      : [];
    const railDefaults = new Map(
      railFields.map((dd) => [dd, { text: dd.textContent, tone: dd.dataset.tone || "" }])
    );
    const navLinks = Array.from(document.querySelectorAll(".kss-rail-nav a[href^='#stage-']"));

    stages.forEach((stage) => {
      const head = stage.querySelector(".kss-stage-head");
      const body = stage.querySelector(".kss-stage-body");
      if (!head || !body) return;

      if (!body.id) body.id = `${stage.id || "stage"}-body`;
      head.setAttribute("aria-controls", body.id);
      head.setAttribute("aria-expanded", "false");

      head.addEventListener("click", () => toggle(stage));
    });

    function activeStage() {
      return stages.find((s) => s.classList.contains("is-active")) || null;
    }

    function toggle(stage) {
      const current = activeStage();
      if (current === stage) {
        close(stage);
        setHash("");
        return;
      }
      if (current) close(current);
      open(stage);
      setHash(stage.id);
    }

    function open(stage, { scroll = true } = {}) {
      stage.classList.add("is-active");
      chain.classList.add("has-active");
      stage.querySelector(".kss-stage-head").setAttribute("aria-expanded", "true");
      updateRail(stage);
      updateNav(stage);
      if (scroll) scrollIntoViewSoft(stage);
    }

    function close(stage) {
      stage.classList.remove("is-active");
      stage.querySelector(".kss-stage-head").setAttribute("aria-expanded", "false");
      if (!activeStage()) {
        chain.classList.remove("has-active");
        updateRail(null);
        updateNav(null);
      }
    }

    /* Rail ------------------------------------------------------------- */
    function updateRail(stage) {
      railFields.forEach((dd) => {
        const key = dd.dataset.rail;
        const next = stage
          ? { text: stage.dataset[`rail${cap(key)}`], tone: stage.dataset[`rail${cap(key)}Tone`] || "" }
          : railDefaults.get(dd);
        if (!next || next.text === undefined) return;
        swapText(dd, next.text, next.tone);
      });
    }

    function swapText(dd, text, tone) {
      if (dd.textContent === text && (dd.dataset.tone || "") === tone) return;
      if (reduceMotion.matches) {
        dd.textContent = text;
        setTone(dd, tone);
        return;
      }
      dd.classList.add("is-updating");
      const commit = () => {
        dd.textContent = text;
        setTone(dd, tone);
        dd.classList.remove("is-updating");
        dd.removeEventListener("transitionend", commit);
      };
      dd.addEventListener("transitionend", commit, { once: true });
      // Safety net if transitionend never fires (e.g. display:none rail on mobile)
      setTimeout(commit, 220);
    }

    function setTone(el, tone) {
      if (tone) el.dataset.tone = tone;
      else delete el.dataset.tone;
    }

    /* Rail nav highlight ------------------------------------------------ */
    function updateNav(stage) {
      navLinks.forEach((a) => {
        const match = stage && a.getAttribute("href") === `#${stage.id}`;
        if (match) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
    }

    navLinks.forEach((a) => {
      a.addEventListener("click", (e) => {
        const target = document.querySelector(a.getAttribute("href"));
        if (!target || !stages.includes(target)) return;
        e.preventDefault();
        const current = activeStage();
        if (current && current !== target) close(current);
        if (current !== target) open(target);
        else scrollIntoViewSoft(target);
        setHash(target.id);
      });
    });

    /* Keyboard: step through stages ------------------------------------ */
    document.addEventListener("keydown", (e) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      const tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;

      const next = e.key === "ArrowDown" || e.key === "j";
      const prev = e.key === "ArrowUp" || e.key === "k";
      if (!next && !prev) return;

      const current = activeStage();
      let idx = current ? stages.indexOf(current) : -1;
      idx = next ? Math.min(idx + 1, stages.length - 1) : Math.max(idx - 1, 0);
      const target = stages[idx];
      if (target === current) return;

      e.preventDefault();
      if (current) close(current);
      open(target);
      setHash(target.id);
      target.querySelector(".kss-stage-head").focus({ preventScroll: true });
    });

    /* Hash deep-linking ------------------------------------------------- */
    function setHash(id) {
      const url = id ? `#${id}` : location.pathname + location.search;
      history.replaceState(null, "", url);
    }

    function openFromHash() {
      const id = location.hash.slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (target && stages.includes(target) && !target.classList.contains("is-active")) {
        const current = activeStage();
        if (current) close(current);
        open(target, { scroll: false });
        // Let layout settle, then bring it into view
        requestAnimationFrame(() => scrollIntoViewSoft(target));
      }
    }
    window.addEventListener("hashchange", openFromHash);
    openFromHash();
  }

  /* Helpers ------------------------------------------------------------- */
  function scrollIntoViewSoft(el) {
    const rect = el.getBoundingClientRect();
    const margin = 24;
    const fullyVisible = rect.top >= margin && rect.top < window.innerHeight * 0.4;
    if (fullyVisible) return;
    el.scrollIntoView({
      behavior: reduceMotion.matches ? "auto" : "smooth",
      block: "start",
    });
  }

  function cap(s) {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
})();
