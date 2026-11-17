/* ==========================================================================
   Session 3 — How Linux knows your hardware exists — deck definition
   What the AUDIENCE sees (title, visual, caption, hardware-state chips) and
   what the PRESENTER says but does not show (cues).
   Presenter prose comes from STORY.md via deck-content.js (generated).

   The spine is three links — Describe → Bind → Expose — then your open().
   Consecutive steps that share visual.key MORPH: boxes keep a stable
   data-id and only data-state changes; the engine animates the change.

   Visual rules (see _shared/COMPONENTS.md and the kss-deck-builder skill):
   - Build visuals from dg-* primitives only.
   - One thing to notice per step. Title = the claim, caption = the consequence.

   CUES ARE THE PRESENTER'S TO EDIT — seeded from the story's planning notes.
   ========================================================================== */
(() => {
  /* ---- reusable fragments --------------------------------------------- */

  // The three-link chain plus the program that uses it. `s` maps data-id →
  // data-state; `ex` overrides the small text under a box.
  function chain3(s = {}, ex = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const t = (id, dflt) => (ex[id] !== undefined ? ex[id] : dflt);
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-id="describe"${st("describe")}><b>1 · Describe</b><small>${t("describe", "a Device Tree node")}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="bind"${st("bind")}><b>2 · Bind</b><small>${t("bind", "a driver matches · probe()")}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="expose"${st("expose")}><b>3 · Expose</b><small>${t("expose", "files in /dev and /sys")}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="use"${st("use")}><b>Your <code>open()</code></b><small>${t("use", "your program")}</small></div>
  </div>
</div>`;
  }

  // What a driver knows vs what it cannot know. `showCant` adds the second group.
  function ctxPic(showCant) {
    const cant = showCant ? `
  <div class="dg-group" data-id="g-cant" data-tone="you" data-grow="2">
    <span class="dg-label">Driver can't know — the where</span>
    <div class="dg-row">
      <div class="dg-box" data-id="c-addr" data-state="ghost"><b>Address</b><small>?</small></div>
      <div class="dg-box" data-id="c-irq" data-state="ghost"><b>Interrupt</b><small>?</small></div>
      <div class="dg-box" data-id="c-clk" data-state="ghost"><b>Clock</b><small>?</small></div>
      <div class="dg-box" data-id="c-pins" data-state="ghost"><b>Pins</b><small>?</small></div>
    </div>
  </div>` : "";
    return `
<div class="dg">
  <div class="dg-row">
  <div class="dg-group" data-id="g-knows" data-tone="focus" data-grow="2">
    <span class="dg-label">Driver — knows the how</span>
    <div class="dg-box" data-id="drv" data-state="focus"><b>PL011 driver</b><small>registers · bits · sequences</small></div>
    <div class="dg-row">
      <div class="dg-box" data-id="chip-a"><b>SoC A</b><small>same UART design</small></div>
      <div class="dg-box" data-id="chip-b"><b>SoC B</b><small>same UART design</small></div>
      <div class="dg-box" data-id="chip-c"><b>SoC C</b><small>same UART design</small></div>
    </div>
  </div>${cant}
  </div>
</div>`;
  }

  // The three DT layers. `s` = states, `ex` = text under each box.
  function layers(s = {}, ex = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const t = (id, dflt) => (ex[id] !== undefined ? ex[id] : dflt);
    return `
<div class="dg">
  <div class="dg-box" data-id="l-overlay"${st("l-overlay")}><b>Overlay</b><small>${t("l-overlay", "adds or changes a node for what you attached")}</small></div>
  <div class="dg-arrow">changes</div>
  <div class="dg-box" data-id="l-board"${st("l-board")}><b>Board <code>.dts</code></b><small>${t("l-board", "which peripherals are wired up, and how")}</small></div>
  <div class="dg-arrow">includes</div>
  <div class="dg-box" data-id="l-soc"${st("l-soc")}><b>SoC <code>.dtsi</code></b><small>${t("l-soc", "every peripheral on the chip")}</small></div>
</div>`;
  }

  // Node ↔ driver ↔ probe. `s` = states; `chips` adds the probe checklist row.
  function bindPic(s = {}, chips = false) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const steps = chips ? `
  <div class="dg-chips" data-id="probe-steps" style="justify-content:center">
    <span class="dg-chip" data-state="focus">map registers</span><i>→</i>
    <span class="dg-chip" data-state="focus">attach interrupt</span><i>→</i>
    <span class="dg-chip" data-state="focus">enable clock</span><i>→</i>
    <span class="dg-chip" data-state="focus">register</span>
  </div>` : "";
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-id="node"${st("node")}><b>DT node</b><small><code>compatible = "arm,pl011"</code></small></div>
    <div class="dg-arrow" data-dir="right">match</div>
    <div class="dg-box" data-id="driver"${st("driver")}><b>Driver</b><small>handles <code>"arm,pl011"</code></small></div>
    <div class="dg-arrow" data-dir="right">calls</div>
    <div class="dg-box" data-id="probe"${st("probe")}><b><code>probe()</code></b><small>the driver's hello</small></div>
  </div>${steps}
</div>`;
  }

  // Symptom → link rows (used by the `breaks` step).
  const symptomRow = (what, where, detail) =>
    `<div class="dg-row"><div class="dg-box" data-state="ghost"><b>${what}</b></div><div class="dg-box" data-grow="3"><b>${where}</b> — ${detail}</div></div>`;

  /* ---- rail presets: the three links lighting up ------------------------ */
  const rail = {
    describe: { "Described by": ["a DT node", "ok"], "Bound to": "nothing yet", "Visible as": "nothing yet" },
    bind:     { "Described by": "a DT node", "Bound to": ["a driver · probe()", "ok"], "Visible as": "nothing yet" },
    expose:   { "Described by": "a DT node", "Bound to": "a driver", "Visible as": ["/dev + /sys entries", "ok"] },
  };

  /* ---- the deck --------------------------------------------------------- */
  KSS.defineDeck({
    id: "session-03",
    title: "How Linux knows your hardware exists",
    plannedMinutes: 60,
    steps: [

      /* ===== Opening ===================================================== */
      {
        id: "open-question",
        section: "Session 3",
        title: "A write to a file turns on an LED",
        caption: "No register, no address, no pointer in sight.",
        visual: { key: "intro", html: `
<div class="dg">
  <div class="dg-row dg-center">
    <div class="dg-box" data-grow="3"><div class="dg-term"><span class="p">~ #</span> <span class="c">echo 1 &gt; /sys/class/leds/&lt;led&gt;/brightness</span></div></div>
    <div class="dg-arrow" data-dir="right">?</div>
    <div class="dg-box" data-state="on"><b>LED</b><small>on</small></div>
  </div>
</div>` },
        cues: [
          "Ask the room: how would you turn on an LED from a program on this board?",
          "Let the question hang: which file is that, who created it, and how did a file write become a voltage on a pin?",
        ],
      },
      {
        id: "open-chain",
        section: "Session 3",
        title: "Describe, bind, expose: three links",
        caption: "Each link has a different author.",
        visual: { key: "chain", html: chain3({ describe: "ghost", bind: "ghost", expose: "ghost", use: "ghost" }) },
        cues: [
          "BRIDGE (verbal): session 1 told the kernel what hardware exists; session 2 showed your program can't touch it and can only knock on the door. Today is the road between those two facts.",
          "Name the three links out loud before the next step; we reuse this chain at the end.",
        ],
      },
      {
        id: "open-today",
        section: "Session 3",
        title: "Today: what a driver needs, then three links",
        caption: "Then how it breaks, and a live look on the Pi.",
        visual: { key: "agenda", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · What a driver needs</b><small>the how vs the where</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Describe</b><small>the Device Tree node</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>3 · Bind</b><small>match, then <code>probe()</code></small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>4 · Expose</b><small>/dev and /sys</small></div>
  </div>
</div>` },
        cues: [
          "Set the time expectation (about an hour) and flag the live demo on the Pi near the end.",
        ],
      },
      {
        id: "open-series",
        section: "Session 3",
        title: "The last of three: closing the loop",
        caption: "Today: the other end of session 2's door.",
        visual: { key: "series", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="on"><b>1 · From power-on to a shell</b><small>done</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>2 · Your code doesn't own the hardware</b><small>done</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>3 · How Linux knows your hardware exists</b><small>today</small></div>
  </div>
  <div class="dg-group">
    <span class="dg-label">Later — built on this foundation</span>
    <div class="dg-row">
      <div class="dg-box" data-state="ghost"><b>Bring up a new board</b></div>
      <div class="dg-box" data-state="ghost"><b>Build an image</b><small>Yocto · Buildroot</small></div>
      <div class="dg-box" data-state="ghost"><b>Cross-compile &amp; deploy your app</b></div>
      <div class="dg-box" data-state="ghost"><b>Networking</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "Tie it back to the form: how the kernel talks to hardware and driver work were top asks, and this session is where they land.",
        ],
      },

      /* ===== Before the chain =========================================== */
      {
        id: "ctx-driver",
        section: "Before the chain",
        title: "A driver is the datasheet, written in C",
        caption: "It knows how to operate one kind of hardware.",
        visual: { key: "ctx", html: ctxPic(false) },
        cues: [
          "Keep it concrete: which register starts a transfer, which bit means busy, in what order to program it.",
        ],
      },
      {
        id: "ctx-where",
        section: "Before the chain",
        title: "But a driver can't know where its hardware lives",
        caption: "Different on every chip and board, even with the same UART.",
        visual: { key: "ctx", html: ctxPic(true) },
        cues: [
          "Pause on the question marks. The next beat answers them.",
        ],
      },

      /* ===== Link 1 — Describe ========================================== */
      {
        id: "dt-what",
        section: "1 · Describe",
        title: "A node answers five questions about one device",
        caption: "Data, not code.",
        rail: rail.describe,
        visual: { key: "node", html: `
<div class="dg">
  <div class="dg-box"><div class="dg-term">uart {
  <span class="hl">compatible = "arm,pl011";</span>
  reg = &lt;address size&gt;;
  interrupts = &lt;…&gt;;
  clocks = &lt;…&gt;;
  status = "okay";
};</div></div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip" data-state="focus">what is it</span><i>·</i>
    <span class="dg-chip">where</span><i>·</i>
    <span class="dg-chip">which interrupt</span><i>·</i>
    <span class="dg-chip">which clock</span><i>·</i>
    <span class="dg-chip">on or off</span>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): you met the Device Tree in session 1 as a one-line idea. Now we open it.",
        ],
      },
      {
        id: "dt-why",
        section: "1 · Describe",
        title: "Board facts move out of the kernel and into data",
        caption: "One kernel image can run on many boards.",
        rail: rail.describe,
        visual: { key: "why-dt", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group" data-tone="faded">
      <span class="dg-label">Before</span>
      <div class="dg-box" data-state="pain"><b>A board file in C</b><small>× hundreds of boards, each a kernel change</small></div>
    </div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-group" data-tone="on">
      <span class="dg-label">Now</span>
      <div class="dg-box" data-state="on"><b>One kernel</b><small>+ a small data file per board</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): this is why the kernel can't just look for the hardware either; fixed peripherals don't announce themselves, as we saw in session 1. Somebody has to write it down.",
        ],
      },
      {
        id: "dt-layers",
        section: "1 · Describe",
        title: "Third time: a generic base, then your specifics",
        caption: "Typical edits: flip a node's status, or add your sensor.",
        rail: rail.describe,
        visual: { key: "layers", html: layers({ "l-overlay": "you" }) },
        cues: [
          "CONTEXT (verbal): the third time we've seen generic → your specifics. SPL needed your DRAM parameters, U-Boot your boot flow, the Device Tree your overlay. Ask the room to say the pattern with you.",
        ],
      },
      {
        id: "dt-handoff",
        section: "1 · Describe",
        title: "The kernel receives the tree as a compiled blob",
        caption: "You can read it back at /proc/device-tree.",
        rail: rail.describe,
        visual: { key: "handoff", html: `
<div class="dg">
  <div class="dg-chips" style="justify-content:center; font-size:1.05em">
    <span class="dg-chip"><code>.dts</code></span><i>→</i>
    <span class="dg-chip" data-state="focus"><code>dtc</code></span><i>→</i>
    <span class="dg-chip"><code>.dtb</code></span><i>→</i>
    <span class="dg-chip">U-Boot / firmware</span><i>→</i>
    <span class="dg-chip">DRAM</span><i>→</i>
    <span class="dg-chip">kernel's tree</span><i>→</i>
    <span class="dg-chip" data-state="on"><code>/proc/device-tree</code></span>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): this is the handoff from session 1, where U-Boot passed the kernel the address of the blob.",
        ],
      },
      {
        id: "dt-owner",
        section: "1 · Describe",
        title: "Three authors; the kernel believes all of them",
        caption: "The tree is the only source of truth the kernel has.",
        rail: rail.describe,
        visual: { key: "layers", html: layers(
          { "l-overlay": "you", "l-board": "focus", "l-soc": "focus" },
          {
            "l-overlay": "you — e.g. an overlay for your sensor",
            "l-board": "board manufacturer — e.g. bcm2711-rpi-4-b.dts",
            "l-soc": "silicon vendor — e.g. bcm2711.dtsi",
          }) },
        cues: [
          "Only if someone opens the real file and asks: the Pi's UART shows as 0x7e201000. That's its bus address; the parent node's ranges property translates it to 0xFE201000, the CPU address we've used. Don't volunteer this.",
        ],
      },

      /* ===== Link 2 — Bind ============================================== */
      {
        id: "bind-what",
        section: "2 · Bind",
        title: "Match the compatible string, then call probe()",
        caption: "The handshake between the node and the driver.",
        rail: rail.bind,
        visual: { key: "bind", html: bindPic({ node: "focus", driver: "focus", probe: "ghost" }) },
        cues: [
          "BRIDGE (verbal): in session 1 this was one line, 'match compatible, call probe()'. Now both halves are on screen.",
        ],
      },
      {
        id: "bind-probe",
        section: "2 · Bind",
        title: "probe() reads the node and sets the hardware up",
        caption: "If a resource isn't ready, probe is retried later.",
        rail: rail.bind,
        // same key as bind-what → the engine morphs node/driver → on, probe → focus
        visual: { key: "bind", html: bindPic({ node: "on", driver: "on", probe: "focus" }, true) },
        cues: [
          "Say out loud: registers are mapped here, the deliberate mapping session 2 said only the kernel has.",
          "Name 'deferred probe' as the reason a device sometimes appears late.",
        ],
      },
      {
        id: "bind-why",
        section: "2 · Bind",
        title: "The driver holds the how, the tree holds the where",
        caption: "A new board with a known UART needs only a new node.",
        rail: rail.bind,
        visual: { key: "bind-why", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus" data-grow="2"><b>Driver</b><small>the how — written once</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-group" data-grow="2">
      <span class="dg-label">The where — written per board</span>
      <div class="dg-col">
        <div class="dg-box"><b>Board A</b><small>its own node</small></div>
        <div class="dg-box"><b>Board B</b><small>its own node</small></div>
        <div class="dg-box"><b>Board C</b><small>its own node</small></div>
      </div>
    </div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): an address says nothing about what's at it. The compatible string is the only thing that says 'this is a PL011'.",
        ],
      },
      {
        id: "bind-sees",
        section: "2 · Bind",
        title: "A device with no driver, or a driver with no device",
        caption: "Most 'my hardware doesn't work' problems are one of these.",
        rail: rail.bind,
        visual: { key: "bind-sees", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group" data-grow="3">
      <span class="dg-label">/sys/bus/platform/devices/</span>
      <div class="dg-col">
        <div class="dg-box" data-state="on"><b>UART</b><small>bound</small></div>
        <div class="dg-box" data-state="on"><b>LED</b><small>bound</small></div>
        <div class="dg-box" data-state="pain"><b>Your sensor</b><small>no driver bound</small></div>
      </div>
    </div>
    <div class="dg-col" style="flex:1; justify-content:center">
      <div class="dg-arrow" data-dir="both"></div>
      <div class="dg-arrow" data-dir="both"></div>
    </div>
    <div class="dg-group" data-grow="3">
      <span class="dg-label">/sys/bus/platform/drivers/</span>
      <div class="dg-col">
        <div class="dg-box" data-state="on"><b>UART driver</b><small>bound</small></div>
        <div class="dg-box" data-state="on"><b>LED driver</b><small>bound</small></div>
        <div class="dg-box" data-state="ghost"><b>An unused driver</b><small>no device to probe</small></div>
      </div>
    </div>
  </div>
</div>` },
        cues: [
          "WAR STORY (optional): a real compatible typo, or an overlapping DTB overlay, from the lab. Nothing complained; that's the point.",
        ],
      },
      {
        id: "bind-owner",
        section: "2 · Bind",
        title: "Vendors and the community write drivers; custom hardware is yours",
        caption: "The matching mechanism itself is part of the kernel.",
        rail: rail.bind,
        visual: { key: "bind-owner", html: `
<div class="dg">
  <div class="dg-box" data-state="focus"><b>match + <code>probe()</code></b><small>kernel</small></div>
  <div class="dg-arrow"></div>
  <div class="dg-row">
    <div class="dg-box"><b>Drivers for the SoC</b><small>vendor · community</small></div>
    <div class="dg-box" data-state="you"><b>Your own driver</b><small>custom hardware, or a part nobody has written for</small></div>
  </div>
</div>` },
        cues: [],
      },

      /* ===== Link 3 — Expose ============================================ */
      {
        id: "expose-what",
        section: "3 · Expose",
        title: "The driver registers with a subsystem, and files appear",
        caption: "With devtmpfs, the file appears the moment the driver registers.",
        rail: rail.expose,
        visual: { key: "expose", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box"><b>Driver</b><small>ends <code>probe()</code> by registering</small></div>
    <div class="dg-arrow" data-dir="right">registers with</div>
    <div class="dg-box" data-state="focus"><b>Subsystem</b><small>tty · LEDs · GPIO · I2C · input</small></div>
    <div class="dg-arrow" data-dir="right">publishes</div>
    <div class="dg-col">
      <div class="dg-box" data-state="on"><b><code>/dev/…</code></b><small>a device file</small></div>
      <div class="dg-box" data-state="on"><b><code>/sys/class/…</code></b><small>attributes</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): our rootfs mounts devtmpfs at boot, so the kernel creates the /dev node itself. That's why no extra tool is needed on this board.",
        ],
      },
      {
        id: "expose-why",
        section: "3 · Expose",
        title: "A common interface makes software portable",
        caption: "Many different UART chips, one serial-port interface.",
        rail: rail.expose,
        visual: { key: "expose-why", html: `
<div class="dg">
  <div class="dg-box" data-state="focus"><b>Serial port</b><small>same behaviour for every program</small></div>
  <div class="dg-arrow"></div>
  <div class="dg-row">
    <div class="dg-box"><b>UART chip A</b><small>its own driver</small></div>
    <div class="dg-box"><b>UART chip B</b><small>its own driver</small></div>
    <div class="dg-box"><b>UART chip C</b><small>its own driver</small></div>
  </div>
</div>` },
        cues: [],
      },
      {
        id: "expose-door",
        section: "3 · Expose",
        title: "The door from session 2 ends at the driver's handler",
        caption: "The driver uses the mapping it made in probe().",
        rail: rail.expose,
        visual: { key: "door", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group">
      <span class="dg-label">Your program</span>
      <div class="dg-box"><b><code>write()</code></b><small>on a device file</small></div>
    </div>
    <div class="dg-arrow" data-dir="right">syscall</div>
    <div class="dg-group" data-tone="focus" data-grow="3">
      <span class="dg-label">Kernel</span>
      <div class="dg-row">
        <div class="dg-box"><b>Finds the driver</b><small>that owns the file</small></div>
        <div class="dg-arrow" data-dir="right"></div>
        <div class="dg-box" data-state="focus"><b>Driver's <code>write</code> handler</b><small>registered earlier</small></div>
        <div class="dg-arrow" data-dir="right"></div>
        <div class="dg-box" data-state="on"><b>Register</b><small>via the <code>probe()</code> mapping</small></div>
      </div>
    </div>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): this is session 2's printf path with the driver zoomed in. Two ends of the same road.",
        ],
      },
      {
        id: "expose-led",
        section: "3 · Expose",
        title: "The opening command, link by link",
        caption: "Every link did its job so you didn't have to.",
        rail: rail.expose,
        visual: { key: "led", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="you"><b>Write <code>1</code></b><small>to <code>brightness</code></small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>LED subsystem</b><small>made the file</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>LED driver</b><small>bound to the node</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box"><b>GPIO pin</b><small>set by the driver</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>LED</b><small>on</small></div>
  </div>
</div>` },
        cues: [
          "Transition: go back to the first slide's command and say it again, now with every arrow filled in.",
        ],
      },
      {
        id: "expose-owner",
        section: "3 · Expose",
        title: "The interface is the kernel's; your app just uses it",
        caption: "That split keeps your application portable across boards.",
        rail: rail.expose,
        visual: { key: "expose-owner", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>Subsystem interface</b><small>kernel community</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box"><b>Driver</b><small>vendor · you</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="you"><b>Your application</b><small>you</small></div>
  </div>
</div>` },
        cues: [],
      },

      /* ===== Summary ===================================================== */
      {
        id: "summary",
        section: "The whole chain",
        title: "Three links turn silicon into a file you can open",
        caption: "",
        visual: { key: "summary", html: `
<div class="dg">
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>Describe</b></div><div class="dg-box" data-grow="3">A Device Tree node says what hardware exists and where. <small>Silicon vendor · board manufacturer · you</small></div></div>
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>Bind</b></div><div class="dg-box" data-grow="3">The kernel matches <code>compatible</code> to a driver and calls <code>probe()</code>. <small>Kernel community · vendors</small></div></div>
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>Expose</b></div><div class="dg-box" data-grow="3">The driver registers with a subsystem; <code>/dev</code> and <code>/sys</code> entries appear. <small>Kernel community · vendors · you</small></div></div>
  <div class="dg-row"><div class="dg-box" data-state="you"><b>Use</b></div><div class="dg-box" data-grow="3" data-state="you">Your program opens the file and makes system calls. <small>You</small></div></div>
</div>` },
        cues: [
          "Read it top to bottom once, slowly. Then: 'questions on the chain before we look at how it breaks?'",
        ],
      },
      {
        id: "breaks",
        section: "The whole chain",
        title: "The symptom tells you which link to check first",
        caption: "A compatible typo fails silently.",
        visual: { key: "breaks", html: `
<div class="dg">
  ${symptomRow("Not in <code>/sys/bus/platform/devices/</code>", "Describe", "the node is missing or disabled, or the overlay wasn't applied")}
  ${symptomRow("Device listed, no driver", "Bind", "a typo in <code>compatible</code>, or the driver isn't built or loaded")}
  ${symptomRow("<code>dmesg</code>: probe failed", "Bind, inside <code>probe()</code>", "a missing resource, or a deferred probe that never completes")}
  ${symptomRow("Bound, but no file in <code>/dev</code>", "Expose", "the driver didn't register, or <code>/dev</code> isn't being populated")}
</div>` },
        cues: [
          "Ask the room: which of these have you already stared at without knowing which link to blame?",
          "WAR STORY (optional): pick one real lab failure and name which of the four it was.",
        ],
      },

      /* ===== Live demo =================================================== */
      {
        id: "demo",
        section: "Live demo",
        title: "Watch the three links on the board",
        caption: "Switching to the terminal — this is what to look for.",
        visual: { key: "demo", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · Describe</b><small>open a node in <code>/proc/device-tree</code>: <code>compatible</code>, <code>reg</code>, <code>status</code></small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Bind</b><small>find its driver in <code>/sys/bus/platform/drivers/</code></small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="you"><b>3 · Expose</b><small>write to the LED's <code>brightness</code> and watch it</small></div>
  </div>
</div>` },
        cues: [
          "DEMO: press B to blank this window, switch the Teams share to the terminal, narrate each link as you go.",
          "Before the session, confirm the LED's name under /sys/class/leds/ and that a write to brightness visibly changes it.",
          "Come back here, un-blank, and point at the three boxes: 'that was the whole chain, on one board'.",
        ],
      },
      {
        id: "demo-repeat",
        section: "Live demo",
        title: "You can repeat this on your own board",
        caption: "The Pi 4 docs cover how the Device Tree is built and loaded.",
        visual: { key: "repeat", html: `
<div class="dg">
  <div class="dg-row dg-center">
    <div class="dg-box"><b>Boot architecture</b><small>docs/raspi4</small></div>
    <div class="dg-box"><b>Kernel + Device Tree build</b><small>docs/raspi4</small></div>
  </div>
</div>` },
        cues: [
          "Share the two links in the call chat so people can find them afterwards.",
        ],
      },

      /* ===== Footnote & close =========================================== */
      {
        id: "rpi4",
        section: "Footnote",
        title: "On the Pi, firmware merges overlays before the kernel",
        caption: "Check which Device Tree your boot path actually passes.",
        visual: { key: "rpi4", html: `
<div class="dg">
  <div class="dg-group">
    <span class="dg-label">Generic path</span>
    <div class="dg-row">
      <div class="dg-box"><b><code>.dtb</code></b><small>compiled from the layers</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box"><b>U-Boot / firmware</b><small>loads it into DRAM</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-state="on"><b>Kernel</b><small>walks the tree</small></div>
    </div>
  </div>
  <div class="dg-group" data-tone="focus">
    <span class="dg-label">Raspberry Pi 4</span>
    <div class="dg-row">
      <div class="dg-box"><b><code>bcm2711-rpi-4-b.dtb</code></b><small>the base tree</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-grow="2" data-state="focus"><b>GPU firmware</b><small>loads it and applies the overlays named in <code>config.txt</code></small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-state="on"><b>Kernel</b><small>walks the merged tree</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "This is why the tree the kernel sees can differ from the plain .dtb on disk. Everything after the load is identical to any other Cortex-A board.",
        ],
      },
      {
        id: "end",
        section: "Next",
        title: "Firmware, a wall, and drivers sit in between",
        caption: "Pick the 'later' topic you want first.",
        visual: { key: "end", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="on"><b>1 · From power-on to a shell</b><small>the firmware chain</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>2 · Your code doesn't own the hardware</b><small>the wall</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>3 · How Linux knows your hardware exists</b><small>descriptions and drivers</small></div>
  </div>
  <div class="dg-group" data-tone="focus">
    <span class="dg-label">Later — each works on one of these layers</span>
    <div class="dg-row">
      <div class="dg-box" data-state="focus"><b>Bring up a new board</b></div>
      <div class="dg-box" data-state="focus"><b>Build an image</b><small>Yocto · Buildroot</small></div>
      <div class="dg-box" data-state="focus"><b>Cross-compile &amp; deploy your app</b></div>
      <div class="dg-box" data-state="focus"><b>Networking</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "Answer the series question out loud: what sits between your code and the hardware, and why? Firmware that gets the board running, a wall that protects everyone, and descriptions plus drivers that turn silicon into files.",
          "Ask the room: which 'later' topic do you want first? Note the answers.",
        ],
      },
    ],
  });
})();
