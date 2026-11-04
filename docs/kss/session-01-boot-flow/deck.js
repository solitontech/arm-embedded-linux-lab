/* ==========================================================================
   Session 1 — From power-on to a shell — deck definition
   What the AUDIENCE sees (title, visual, caption, hardware-state chips) and
   what the PRESENTER says but does not show (cues).
   Presenter prose comes from STORY.md via deck-content.js (generated).

   Visual rules:
   - Build visuals from dg-* primitives (see _shared/COMPONENTS.md).
   - Consecutive steps that share visual.key MORPH: give boxes a stable
     data-id and only change data-state; the engine animates the change.
   - One thing to notice per step. If the caption needs two sentences,
     split the step.

   CUES ARE YOURS TO EDIT — they're seeded from the story review.
   ========================================================================== */
(() => {
  /* ---- reusable fragments --------------------------------------------- */

  // The SoC + board picture used by the SoC intro, RBL and SPL stages.
  // `s` maps data-id → data-state; `t` maps group → data-tone; `extra` injects
  // text under a box. Keys not given fall back to neutral.
  function socBoard(s = {}, t = {}, extra = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const tn = (id) => (t[id] ? ` data-tone="${t[id]}"` : "");
    const ex = (id, dflt) => extra[id] !== undefined ? extra[id] : dflt;
    return `
<div class="dg">
  <div class="dg-group" data-id="g-sw"${tn("sw")}>
    <span class="dg-label">Software — open source + you</span>
    <div class="dg-row">
      <div class="dg-box" data-id="sw-spl"${st("sw-spl")}><b>SPL</b><small>U-Boot project</small></div>
      <div class="dg-box" data-id="sw-uboot"${st("sw-uboot")}><b>U-Boot</b><small>configured by you</small></div>
      <div class="dg-box" data-id="sw-kernel"${st("sw-kernel")}><b>Kernel + Device Tree</b><small>community · vendors · you</small></div>
      <div class="dg-box" data-id="sw-rootfs"${st("sw-rootfs")}><b>Root filesystem</b><small>your application</small></div>
    </div>
  </div>
  <div class="dg-group" data-id="g-board"${tn("board")}>
    <span class="dg-label">Board — board manufacturer</span>
    <div class="dg-row">
      <div class="dg-box" data-id="ddr"${st("ddr")}><b>DDR chips</b><small>${ex("ddr", "the gigabytes of RAM")}</small></div>
      <div class="dg-box" data-id="media"${st("media")}><b>Boot media</b><small>${ex("media", "SD · eMMC · SPI flash")}</small></div>
      <div class="dg-box" data-id="conn"${st("conn")}><b>Connectors</b><small>USB · Ethernet · GPIO</small></div>
      <div class="dg-box" data-id="pwr"${st("pwr")}><b>Power</b><small>regulators</small></div>
    </div>
    <div class="dg-group" data-id="g-soc"${tn("soc")}>
      <span class="dg-label">SoC — silicon vendor</span>
      <div class="dg-row">
        <div class="dg-box" data-id="cpu"${st("cpu")}><b>CPU cores</b><small>${ex("cpu", "Cortex-A")}</small></div>
        <div class="dg-box" data-id="sram"${st("sram")}><b>SRAM</b><small>${ex("sram", "small, on-chip")}</small></div>
        <div class="dg-box" data-id="rom"${st("rom")}><b>Boot ROM</b><small>${ex("rom", "permanent")}</small></div>
        <div class="dg-box" data-id="dramc"${st("dramc")}><b>DRAM controller</b><small>${ex("dramc", "talks to the DDR chips")}</small></div>
        <div class="dg-box" data-id="periph"${st("periph")}><b>Peripherals</b><small>UART · GPIO · I2C · …</small></div>
      </div>
    </div>
  </div>
</div>`;
  }

  // The five-stage chain. `lit` = ids with data-state="focus"; `done` = "on".
  function chain(lit = [], done = [], subs = {}) {
    const stages = [
      ["rbl", "ROM Bootloader", "in the silicon"],
      ["spl", "SPL", "unlocks DRAM"],
      ["uboot", "U-Boot", "finds the kernel"],
      ["kernel", "Kernel + Device Tree", "the OS takes over"],
      ["rootfs", "Root filesystem", "your application"],
    ];
    return `
<div class="dg">
  <div class="dg-row">
    ${stages.map(([id, name, sub], i) => `
      ${i ? '<div class="dg-arrow" data-dir="right"></div>' : ""}
      <div class="dg-box" data-id="${id}" data-state="${lit.includes(id) ? "focus" : done.includes(id) ? "on" : "ghost"}">
        <b>${name}</b><small>${subs[id] || sub}</small>
      </div>`).join("")}
  </div>
</div>`;
  }

  const ownerBox = (id, title, small, state) =>
    `<div class="dg-box" data-id="${id}"${state ? ` data-state="${state}"` : ""}><b>${title}</b><small>${small}</small></div>`;

  /* ---- rail presets ----------------------------------------------------- */
  const rail = {
    rbl:    { Memory: ["on-chip SRAM only", "blocked"], CPU: "executing from ROM",  Code: "immutable" },
    spl:    { Memory: ["SRAM → DRAM coming online", "ok"], CPU: "executing from SRAM", Code: "first stage you can change" },
    uboot:  { Memory: ["full DRAM", "ok"], CPU: "executing from DRAM", Code: "open source · configured by you" },
    kernel: { Memory: ["virtual — MMU on", "ok"], CPU: "kernel mode", Code: "community · vendors · your overlay" },
    rootfs: { Memory: ["virtual, per process", "ok"], CPU: "user mode", Code: ["yours", "you"] },
  };

  /* ---- the deck --------------------------------------------------------- */
  KSS.defineDeck({
    id: "session-01",
    title: "From power-on to a shell",
    plannedMinutes: 60,
    steps: [

      /* ===== Opening ===================================================== */
      {
        id: "open-question",
        section: "Session 1",
        title: "From power-on to a shell",
        caption: "What happened in that one second?",
        visual: { key: "intro", html: `
<div class="dg">
  <div class="dg-row dg-center">
    <div class="dg-box" data-grow="2" data-state="focus"><b>⏻ &nbsp;Power</b><small>5 V, one cable</small></div>
    <div class="dg-arrow" data-dir="right">about one second</div>
    <div class="dg-box" data-grow="3"><div class="dg-term"><span class="p">rpi4 login:</span> <span class="c">root</span>
<span class="p">~ #</span> <span class="c">_</span></div></div>
  </div>
</div>` },
        cues: [
          "Ask the room: what runs first when you power a board? (RTOS folks: reset vector. App folks: usually no idea.)",
          "Set the frame: today is the generic ARM Cortex-A story, not the Raspberry Pi — the Pi comes up at the end.",
        ],
      },
      {
        id: "open-relay",
        section: "Session 1",
        title: "Five stages, one relay race",
        caption: "Each runner exists because the previous one physically couldn't go further.",
        visual: { key: "chain", html: chain() },
        cues: [
          "Compare to what they know: bare-metal Cortex-M = power → reset vector → main(). RTOS = + scheduler. Linux = this relay.",
          "Promise: by the end they can look at any embedded Linux board and ask the right questions at each handoff.",
        ],
      },
      {
        id: "open-today",
        section: "Session 1",
        title: "Today: four parts",
        caption: "The mental model first, then the workflow, then our board.",
        visual: { key: "agenda", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · SoC &amp; board</b><small>what the hardware is, who builds what</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Five stages</b><small>ROM → SPL → U-Boot → kernel → rootfs</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>3 · Network boot</b><small>why we never re-flash the SD card</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>4 · Our RPi4</b><small>the generic story on real hardware</small></div>
  </div>
</div>` },
        cues: [
          "Set the time expectation (about an hour) and say questions are welcome at each stage boundary.",
          "Flag the live demo: serial console on the RPi4 near the end.",
        ],
      },
      {
        id: "open-series",
        section: "Session 1",
        title: "Where this fits: a three-session series",
        caption: "Each session peels back one layer between your code and the hardware.",
        visual: { key: "series", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · From power-on to a shell</b><small>today — what boots, in what order, who wrote it</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="ghost"><b>2 · Your code doesn't own the hardware</b><small>processes, virtual memory, syscalls</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="ghost"><b>3 · How Linux knows your hardware exists</b><small>Device Tree → driver → /dev</small></div>
  </div>
</div>` },
        cues: [
          "Tie it to the series question: what sits between your code and the hardware, and why? Today is the bottom of that stack.",
          "Tell RTOS and app folks what they get: sessions 2 and 3 are where their day-to-day code comes in.",
        ],
      },

      /* ===== SoC & board ================================================= */
      {
        id: "soc-chip",
        section: "Before the chain",
        title: "The chip: a System-on-Chip",
        caption: "A microcontroller, scaled up — and the RAM is not inside it.",
        visual: { key: "layers", html: socBoard(
          { cpu: "focus", sram: "focus", rom: "focus", dramc: "focus", periph: "focus" },
          { soc: "focus", board: "faded", sw: "faded" }) },
        cues: [
          "Name a few: BCM2711 (Pi 4), AM335x (BeagleBone), i.MX8, STM32MP1.",
          "Stress the one surprise: the DRAM controller is on the chip; the DRAM itself is not.",
        ],
      },
      {
        id: "soc-board",
        section: "Before the chain",
        title: "The board: built around the SoC",
        caption: "The board manufacturer picks the DDR chips, the boot media, the connectors.",
        visual: { key: "layers", html: socBoard(
          { ddr: "focus", media: "focus", conn: "focus", pwr: "focus" },
          { soc: "", board: "focus", sw: "faded" }) },
        cues: [
          "Raspberry Pi Foundation, BeagleBoard.org, Toradex, Variscite — all board makers buying chips from silicon vendors.",
        ],
      },
      {
        id: "soc-authors",
        section: "Before the chain",
        title: "Three layers, three authors",
        caption: "Silicon vendor · board manufacturer · open source + you.",
        visual: { key: "layers", html: socBoard(
          { "sw-spl": "focus", "sw-uboot": "focus", "sw-kernel": "focus", "sw-rootfs": "you" },
          { soc: "", board: "", sw: "focus" }) },
        cues: [
          "BRIDGE (verbal, not on screen): no single party knows everything about this board. Keep that thought — it is why there are five stages instead of one.",
        ],
      },

      /* ===== Stage 1: RBL ================================================ */
      {
        id: "rbl-reset",
        section: "1 · ROM Bootloader",
        title: "Power on: the CPU fetches from a fixed address",
        caption: "The reset vector points into ROM that was etched at the factory.",
        rail: rail.rbl,
        visual: { key: "soc", html: socBoard(
          { cpu: "focus", rom: "focus" },
          { soc: "focus", board: "faded", sw: "faded" },
          { cpu: "wakes up at the reset vector", rom: "RBL runs from here" }) },
        cues: [
          "Bare-metal people: this IS your reset vector — just that the vendor filled the address with their code, not yours.",
          "If it has bugs: errata document, not a patch. Chip selection matters.",
        ],
      },
      {
        id: "rbl-world",
        section: "1 · ROM Bootloader",
        title: "What the ROM can see",
        caption: "SRAM works. DRAM is dark. The board is mostly invisible.",
        rail: rail.rbl,
        visual: { key: "soc", html: socBoard(
          { rom: "focus", sram: "on", dramc: "off", ddr: "off", media: "", conn: "off", pwr: "off" },
          { soc: "focus", board: "faded", sw: "faded" },
          { sram: "~128–256 KB · usable now", dramc: "not initialised", ddr: "dark", media: "can read one small file" }) },
        cues: [
          "Ask: how big is a Linux kernel? (tens of MB). How big is SRAM? (a few hundred KB). So?",
        ],
      },
      {
        id: "rbl-minimum",
        section: "1 · ROM Bootloader",
        title: "The ROM does the minimum",
        caption: "The kernel is tens of MB. SRAM is a few hundred KB. There is nowhere to put it.",
        rail: rail.rbl,
        visual: { key: "rbl-steps", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · Read boot pins / eFuses</b><small>SD? SPI flash? eMMC? UART?</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Read a small binary</b><small>from that boot media</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>3 · Copy it into SRAM</b><small>the only memory that works</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>4 · Jump to it</b><small>that binary is the SPL</small></div>
  </div>
</div>` },
        cues: [
          "eFuses: one-time-programmable bits. On many boards the same choice is on DIP switches or solder jumpers — 'boot mode pins'.",
        ],
      },
      {
        id: "rbl-owner",
        section: "1 · ROM Bootloader",
        title: "Written by the SoC vendor. Shipped in the silicon.",
        caption: "You never compile it. You never flash it. It is just there, every power-on.",
        rail: rail.rbl,
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-row dg-center">
    ${ownerBox("o-rbl", "ROM Bootloader", "TI · NXP · ST · Broadcom · Qualcomm …", "focus")}
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">mask ROM</span><span class="dg-chip">immutable</span><span class="dg-chip">errata, not patches</span><span class="dg-chip">knows the chip, not your board</span>
  </div>
</div>` },
        cues: [
          "Transition: it knows the chip. It cannot know your board. Who does? → SPL.",
        ],
      },

      /* ===== Stage 2: SPL ================================================ */
      {
        id: "spl-intro",
        section: "2 · SPL",
        title: "SPL: the first code you can change",
        caption: "A stripped-down U-Boot, small enough to live in SRAM.",
        rail: rail.spl,
        visual: { key: "soc", html: socBoard(
          { sram: "on", media: "focus", dramc: "off", ddr: "off" },
          { soc: "focus", board: "", sw: "faded" },
          { sram: "SPL running here", media: "SPL was read from here", dramc: "not initialised", ddr: "dark" }) },
        cues: [
          "Names you'll meet: MLO (TI), u-boot-spl.bin, SPL. Same idea.",
        ],
      },
      {
        id: "spl-dram",
        section: "2 · SPL",
        title: "One job: initialise the DRAM controller",
        caption: "Parameters specific to the DDR chips the board vendor chose.",
        rail: rail.spl,
        visual: { key: "soc", html: socBoard(
          { sram: "on", dramc: "on", ddr: "on" },
          { soc: "focus", board: "on", sw: "faded" },
          { sram: "SPL running here", dramc: "configured ✓", ddr: "gigabytes, now usable" }) },
        cues: [
          "This is the moment of the stage — let the boxes turn green before you speak.",
          "Why the ROM can't do it: the ROM was designed before this board existed. The timing depends on chips the vendor never saw.",
          "If you designed your own board, this is the stage you would touch first.",
        ],
      },
      {
        id: "spl-handoff",
        section: "2 · SPL",
        title: "Then: load U-Boot into DRAM, and jump",
        caption: "From a few hundred KB to gigabytes — room for a real bootloader.",
        rail: rail.spl,
        visual: { key: "soc", html: socBoard(
          { sram: "on", dramc: "on", ddr: "focus", media: "focus", "sw-uboot": "focus" },
          { soc: "", board: "on", sw: "" },
          { ddr: "U-Boot copied in here", media: "U-Boot read from here", sram: "SPL hands off" }) },
        cues: [],
      },
      {
        id: "spl-owner",
        section: "2 · SPL",
        title: "Framework from U-Boot. DRAM config from the board vendor.",
        caption: "Falcon mode exists — normally you don't skip U-Boot.",
        rail: rail.spl,
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-row">
    ${ownerBox("o-splfw", "SPL framework", "U-Boot project · open source", "focus")}
    <div class="dg-arrow" data-dir="right">+</div>
    ${ownerBox("o-ddrcfg", "DRAM configuration", "SoC reference design → adapted by the board vendor", "")}
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">init DRAM</span><i>→</i><span class="dg-chip">load U-Boot</span><i>→</i><span class="dg-chip">hand off</span>
  </div>
</div>` },
        cues: [
          "Why not load the kernel from SPL? It can (Falcon mode) — but the kernel wants bootargs, a DTB at a known address, CPU in a known state. That's a bootloader's job.",
        ],
      },

      /* ===== Stage 3: U-Boot ============================================= */
      {
        id: "uboot-intro",
        section: "3 · U-Boot",
        title: "U-Boot: the first stage with room to breathe",
        caption: "Running in DRAM: a C runtime, drivers, networking, and a shell.",
        rail: rail.uboot,
        visual: { key: "uboot", html: `
<div class="dg">
  <div class="dg-group" data-tone="on">
    <span class="dg-label">DRAM — gigabytes</span>
    <div class="dg-row">
      <div class="dg-box" data-grow="2" data-state="focus"><b>U-Boot</b><small>"Das U-Boot" — the universal bootloader</small></div>
    </div>
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip" data-state="focus">C runtime</span><span class="dg-chip" data-state="focus">storage drivers</span><span class="dg-chip" data-state="focus">network</span><span class="dg-chip" data-state="focus">serial</span><span class="dg-chip" data-state="focus">interactive shell</span>
  </div>
</div>` },
        cues: [
          "Think of it as the BIOS of embedded Linux — same U-Boot on TI, NXP, ST, Allwinner; only the defconfig changes.",
        ],
      },
      {
        id: "uboot-load",
        section: "3 · U-Boot",
        title: "Load the kernel and Device Tree into DRAM",
        caption: "Two things, two places, not overlapping. Then booti — and U-Boot never runs again.",
        rail: rail.uboot,
        visual: { key: "mem", html: `
<div class="dg">
  <div class="dg-mem">
    <div class="dg-mem-addr">0x0200_0000</div>
    <div class="dg-mem-seg" data-state="focus"><b>Kernel <code>Image</code></b>tens of MB · from the boot source</div>
    <div class="dg-mem-addr"></div>
    <div class="dg-mem-seg" data-state="gap">gap — must not overlap</div>
    <div class="dg-mem-addr">0x0600_0000</div>
    <div class="dg-mem-seg" data-state="focus"><b>Device Tree Blob <code>.dtb</code></b>tens of KB · describes the board</div>
    <div class="dg-mem-addr">…</div>
    <div class="dg-mem-seg"><b>U-Boot itself</b>relocated near the top of RAM</div>
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">load Image</span><i>→</i><span class="dg-chip">load .dtb</span><i>→</i><span class="dg-chip">set bootargs</span><i>→</i><span class="dg-chip" data-state="focus">booti</span>
  </div>
</div>` },
        cues: [
          "Addresses are illustrative. The point: two things, two places.",
          "WAR STORY (optional, verbal): our DTB got overwritten when the kernel relocated over it — 'FDT image overlaps OS image'. Silent, confusing. That's why the gap.",
        ],
      },
      {
        id: "uboot-env",
        section: "3 · U-Boot",
        title: "Configuration = environment variables",
        caption: "printenv to read, setenv to change, saveenv to keep. A boot script is a saved sequence.",
        rail: rail.uboot,
        visual: { key: "term", html: `
<div class="dg">
  <div class="dg-term"><span class="p">U-Boot&gt;</span> <span class="c">printenv bootargs</span>
<span class="o">bootargs=console=ttyS0,115200 root=/dev/nfs rw nfsroot=192.168.1.220:/rootfs …</span>
<span class="p">U-Boot&gt;</span> <span class="c">setenv serverip 192.168.1.220</span>
<span class="p">U-Boot&gt;</span> <span class="c">saveenv</span>
<span class="o">Saving Environment to … OK</span>
<span class="p">U-Boot&gt;</span> <span class="c">tftp 0x02000000 Image</span>
<span class="o">Loading: ################  41.5 MiB</span></div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip" data-state="focus">bootargs</span><span class="dg-chip" data-state="focus">serverip</span><span class="dg-chip" data-state="focus">bootcmd</span><span class="dg-chip">bootdelay</span><span class="dg-chip">fdt_addr</span><span class="dg-chip">boot.scr</span>
  </div>
</div>` },
        cues: [
          "DEMO OPTION: interrupt autoboot on the Pi, type printenv. Let them see it's just key=value.",
          "saveenv only works if the board has somewhere to store the environment (flash, SD, eMMC). Some setups keep it in the boot script instead.",
        ],
      },
      {
        id: "uboot-why",
        section: "3 · U-Boot",
        title: "Generic bootloader, your boot flow",
        caption: "U-Boot cannot assume where your kernel lives or what your console is. You tell it.",
        rail: rail.uboot,
        visual: { key: "custom", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-grow="2"><b>Generic U-Boot</b><small>one codebase · hundreds of SoCs and boards</small></div>
    <div class="dg-arrow" data-dir="right">you supply</div>
    <div class="dg-col" style="flex:3">
      <div class="dg-box" data-state="you"><b>defconfig</b><small>which SoC and board → the right drivers and memory map</small></div>
      <div class="dg-box" data-state="you"><b>boot script</b><small>your load sequence</small></div>
      <div class="dg-box" data-state="you"><b>bootargs</b><small>your console, your root filesystem</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "Same shape as SPL: the generic thing can't know your specifics → you provide exactly that. Watch for it again with the Device Tree.",
        ],
      },
      {
        id: "uboot-source",
        section: "3 · U-Boot",
        title: "Where it loads from is up to you",
        caption: "TFTP is what makes the SD-card-free workflow possible.",
        rail: rail.uboot,
        visual: { key: "sources", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box"><b>SD card</b><small>first bring-up</small></div>
    <div class="dg-box"><b>eMMC</b><small>product</small></div>
    <div class="dg-box"><b>USB</b><small>recovery</small></div>
    <div class="dg-box"><b>SPI flash</b><small>small products</small></div>
    <div class="dg-box" data-state="focus"><b>TFTP (network)</b><small>development — covered in a minute</small></div>
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">open source · denx.de</span><span class="dg-chip">vendors add board configs</span><span class="dg-chip" data-state="you">you define the boot flow</span>
  </div>
</div>` },
        cues: [
          "Plant the seed: 'TFTP' is the word to remember for the workflow section.",
        ],
      },

      /* ===== Stage 4: Kernel + DT ======================================== */
      {
        id: "kernel-mmu",
        section: "4 · Kernel + Device Tree",
        title: "The kernel takes over — and turns on the MMU",
        caption: "From here on, addresses are virtual. Programs stop seeing the real memory bus.",
        rail: rail.kernel,
        visual: { key: "mmu", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-col">
      <div class="dg-box" data-state="you"><b>Program A</b><small>sees 0x0040_0000</small></div>
      <div class="dg-box" data-state="you"><b>Program B</b><small>sees 0x0040_0000 too</small></div>
    </div>
    <div class="dg-arrow" data-dir="right">virtual</div>
    <div class="dg-box" data-state="focus" style="align-self:center"><b>MMU</b><small>translates every access</small></div>
    <div class="dg-arrow" data-dir="right">physical</div>
    <div class="dg-col">
      <div class="dg-box" data-state="on"><b>DRAM 0x8A12_0000</b><small>A's page</small></div>
      <div class="dg-box" data-state="on"><b>DRAM 0x9F40_0000</b><small>B's page</small></div>
    </div>
  </div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip" data-state="focus">MMU on</span><i>→</i><span class="dg-chip">interrupt controller</span><i>→</i><span class="dg-chip">scheduler</span><i>→</i><span class="dg-chip">probe drivers</span>
  </div>
</div>` },
        cues: [
          "RTOS people: this is the wall. On your RTOS you own physical memory. Here you never see it again from userspace.",
          "Session 2 lives entirely on this slide. Don't go deep now.",
        ],
      },
      {
        id: "kernel-silent",
        section: "4 · Kernel + Device Tree",
        title: "How does the kernel know what hardware is here?",
        caption: "On a PC, devices announce themselves. On an SoC, nothing does.",
        rail: rail.kernel,
        visual: { key: "enum", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group" data-tone="">
      <span class="dg-label">Desktop PC</span>
      <div class="dg-box" data-state="on"><b>USB device</b><small>"hello — I'm a keyboard, vendor 0x046d"</small></div>
      <div class="dg-box" data-state="on"><b>PCI card</b><small>announces itself during enumeration</small></div>
    </div>
    <div class="dg-group" data-tone="focus">
      <span class="dg-label">ARM SoC</span>
      <div class="dg-row">
        <div class="dg-box" data-state="off"><b>UART</b><small>0xFE20_1000 · silent</small></div>
        <div class="dg-box" data-state="off"><b>GPIO</b><small>0xFE20_0000 · silent</small></div>
        <div class="dg-box" data-state="off"><b>I2C</b><small>0xFE80_4000 · silent</small></div>
      </div>
    </div>
  </div>
</div>` },
        cues: [
          "Pause here. Let them feel the problem before you show the answer.",
        ],
      },
      {
        id: "kernel-dt",
        section: "4 · Kernel + Device Tree",
        title: "The Device Tree is the announcement",
        caption: "Data, not code: 'there is a UART at this address'. The kernel pairs it with a driver.",
        rail: rail.kernel,
        visual: { key: "dt", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-grow="2" data-state="focus"><div class="dg-term">uart@fe201000 {
    compatible = <span class="hl">"arm,pl011"</span>;
    reg = &lt;0xfe201000 0x200&gt;;
    interrupts = &lt;57&gt;;
};</div></div>
    <div class="dg-arrow" data-dir="right">match<br><code>compatible</code></div>
    <div class="dg-box" data-state="focus"><b>pl011 driver</b><small><code>probe()</code> runs with that address</small></div>
    <div class="dg-arrow" data-dir="right">creates</div>
    <div class="dg-box" data-state="on"><b><code>/dev/ttyS0</code></b><small>your serial console</small></div>
  </div>
</div>` },
        cues: [
          "'.dts' is the readable source, '.dtb' the compiled blob U-Boot loaded two stages ago. Connect it back.",
          "Session 3 is this slide in depth — overlays, probe(), your own driver.",
        ],
      },
      {
        id: "kernel-layers",
        section: "4 · Kernel + Device Tree",
        title: "Layered, because different people know different parts",
        caption: "SoC vendor describes the chip. Board vendor describes the wiring. You describe what you added.",
        rail: rail.kernel,
        visual: { key: "dt-layers", html: `
<div class="dg">
  <div class="dg-box" data-state="you"><b>Your overlay</b><small>adds: a sensor on a GPIO, a relay for a safety system — hardware the board vendor never saw</small></div>
  <div class="dg-arrow">includes</div>
  <div class="dg-box"><b>Board <code>.dts</code> &nbsp;· board vendor</b><small>extends: which GPIO drives an LED, which I2C bus has a sensor — e.g. <code>bcm2711-rpi-4-b.dts</code></small></div>
  <div class="dg-arrow">includes</div>
  <div class="dg-box" data-state="focus"><b>SoC <code>.dtsi</code> &nbsp;· silicon vendor</b><small>base: every peripheral on the chip, shared by all boards using it — e.g. <code>bcm2711.dtsi</code></small></div>
</div>` },
        cues: [
          "Third time the shape appears: generic (vendor) → specific (board) → yours (overlay).",
          "Kernel itself: community + vendor drivers + board patches. You may write a driver later — that's a future session.",
        ],
      },

      /* ===== Stage 5: Rootfs ============================================ */
      {
        id: "rootfs-tree",
        section: "5 · Root filesystem",
        title: "A kernel alone is not a system",
        caption: "Mount /, run /sbin/init. Now you're in userspace.",
        rail: rail.rootfs,
        visual: { key: "tree", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-grow="2"><div class="dg-tree">/
├── <span class="hl">sbin/init</span>          <span class="dim">← first process (PID 1)</span>
├── bin/sh             <span class="dim">← a shell</span>
├── etc/init.d/rcS     <span class="dim">← startup script</span>
├── dev/               <span class="dim">← device nodes</span>
├── proc/              <span class="dim">← kernel state, as files</span>
└── <span class="hl">your-application</span>   <span class="dim">← your binary</span></div></div>
    <div class="dg-col">
      <div class="dg-box"><b>Where it comes from</b><small>SD partition · flash · or NFS over the network</small></div>
      <div class="dg-box" data-state="you"><b>Who builds it</b><small>you — the developer or integrator</small></div>
      <div class="dg-box"><b>Separate from the kernel</b><small>update your app without rebuilding the kernel, and vice versa</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "App developers: this is where your world starts. Everything above was to get here.",
        ],
      },
      {
        id: "rootfs-build",
        section: "5 · Root filesystem",
        title: "How a rootfs is built",
        caption: "Buildroot and Yocto build the whole system — U-Boot, kernel, DT and rootfs — not just this layer.",
        rail: rail.rootfs,
        visual: { key: "spectrum", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>BusyBox</b><small>one binary …</small></div>
    <div class="dg-arrow" data-dir="right">is</div>
    <div class="dg-box" data-grow="3"><b><code>ls cat sh mount ifconfig vi … </code></b><small>200+ Unix commands in ~2 MB — first bring-up, minimal appliances</small></div>
  </div>
  <div class="dg-row">
    <div class="dg-box" data-state="you"><b>BusyBox</b><small>~2 MB</small></div>
    <div class="dg-box" data-state="focus"><b>Buildroot</b><small>5–25 MB · you pick packages</small></div>
    <div class="dg-box" data-state="focus"><b>Yocto / OpenEmbedded</b><small>industrial, layer-based, reproducible</small></div>
    <div class="dg-box" data-state="off"><b>Full distribution</b><small>500 MB+ · rarely in products</small></div>
  </div>
</div>` },
        cues: [
          "Our lab rootfs is BusyBox over NFS; Buildroot shows up when we productise.",
        ],
      },

      /* ===== Summary ===================================================== */
      {
        id: "summary",
        section: "The whole chain",
        title: "Five stages, one picture",
        caption: "",
        visual: { key: "summary", html: `
<div class="dg">
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>ROM Bootloader</b></div><div class="dg-box" data-grow="3">Ran from on-chip ROM. Found the boot media. Loaded SPL into SRAM.</div></div>
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>SPL</b></div><div class="dg-box" data-grow="3">Ran from SRAM. Initialised DRAM. Loaded U-Boot into DRAM.</div></div>
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>U-Boot</b></div><div class="dg-box" data-grow="3">Ran from DRAM. Loaded kernel + Device Tree. Set boot arguments. Jumped to the kernel.</div></div>
  <div class="dg-row"><div class="dg-box" data-state="ghost"><b>Kernel + Device Tree</b></div><div class="dg-box" data-grow="3">Enabled the MMU. Probed drivers from the Device Tree. Mounted the rootfs. Launched <code>init</code>.</div></div>
  <div class="dg-row"><div class="dg-box" data-state="you"><b>Root filesystem</b></div><div class="dg-box" data-grow="3" data-state="you">Userspace. Shell. Your application. You're here.</div></div>
</div>` },
        cues: [
          "Read it top to bottom once, slowly. Then: 'questions on the chain before we talk about living with it every day?'",
        ],
      },

      /* ===== Workflow ==================================================== */
      {
        id: "flow-pain",
        section: "Development workflow",
        title: "The SD-card loop",
        caption: "Minutes per cycle. Dozens of cycles a day.",
        visual: { key: "loop", html: `
<div class="dg">
  <div class="dg-chips" style="justify-content:center; font-size:1.05em">
    <span class="dg-chip">Edit</span><i>→</i><span class="dg-chip">Compile</span><i>→</i>
    <span class="dg-chip" data-state="pain">Power off</span><i>→</i><span class="dg-chip" data-state="pain">Pull SD</span><i>→</i>
    <span class="dg-chip" data-state="pain">Mount on host</span><i>→</i><span class="dg-chip">Copy</span><i>→</i>
    <span class="dg-chip" data-state="pain">Unmount</span><i>→</i><span class="dg-chip" data-state="pain">Insert</span><i>→</i>
    <span class="dg-chip">Power on</span><i>→</i><span class="dg-chip">Test</span><i>→</i><span class="dg-chip">repeat</span>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): alternatives we considered — USB mass storage, rsync over SSH, serial/ymodem. Why TFTP+NFS: it covers the kernel and DT too, not just userspace, and the board needs no working OS to receive files.",
        ],
      },
      {
        id: "flow-network",
        section: "Development workflow",
        title: "Make U-Boot load over the network",
        caption: "Kernel and DTB over TFTP. Root filesystem over NFS. Files live on your machine.",
        visual: { key: "net", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-grow="2" data-state="you"><b>Your development machine</b><small>kernel <code>Image</code> · <code>.dtb</code> · the rootfs directory</small></div>
    <div class="dg-col" style="flex:2">
      <div class="dg-arrow" data-dir="right">TFTP — U-Boot fetches Image + DTB on every boot</div>
      <div class="dg-arrow" data-dir="right">NFS — the kernel mounts / from your machine</div>
    </div>
    <div class="dg-box" data-grow="2" data-state="focus"><b>Board</b><small>edit · reboot · the change is live</small></div>
  </div>
</div>` },
        cues: [
          "Same five stages. Only the SOURCE of stages 3–5 moved from the SD card to your desk.",
        ],
      },
      {
        id: "flow-lab",
        section: "Development workflow",
        title: "How it works in our lab",
        caption: "One Docker container, three services, one command: ./lab docker run",
        visual: { key: "lab", html: `
<div class="dg">
  <div class="dg-group" data-tone="you">
    <span class="dg-label">Your development machine</span>
    <div class="dg-group">
      <span class="dg-label">Docker container</span>
      <div class="dg-row">
        <div class="dg-box"><b>dnsmasq</b><small>DHCP — "here is your IP; TFTP is at …"</small></div>
        <div class="dg-box"><b>tftpd-hpa</b><small>TFTP — serves <code>Image</code>, <code>.dtb</code>, <code>boot.scr</code></small></div>
        <div class="dg-box"><b>nfs-kernel-server</b><small>NFS — exports the rootfs directory</small></div>
      </div>
    </div>
  </div>
  <div class="dg-arrow">Ethernet</div>
  <div class="dg-group" data-tone="focus">
    <span class="dg-label">Board</span>
    <div class="dg-row">
      <div class="dg-box" data-state="focus"><b>U-Boot</b><small>DHCP → IP · TFTP → kernel + DTB</small></div>
      <div class="dg-box" data-state="focus"><b>Kernel</b><small>NFS → mounts / from your machine</small></div>
      <div class="dg-box" data-state="you"><b>Your app</b><small>runs from the NFS rootfs</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "Why Docker: same on macOS / Linux / Windows. Honest caveat: host networking + firewall rules are a one-time per-machine setup.",
          "On the Pi the SD card can go entirely — the EEPROM fetches even the firmware over TFTP. Mention, don't explain.",
        ],
      },
      {
        id: "flow-demo",
        section: "Live demo",
        title: "Watch the serial console",
        caption: "Switching to the terminal — this is what to look for.",
        visual: { key: "demo", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · DHCP</b><small>board asks for an IP, is told where TFTP is</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · TFTP</b><small><code>Image</code> and <code>.dtb</code> stream in — watch the counter</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>3 · Starting kernel …</b><small>U-Boot hands off, never returns</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>4 · Kernel log</b><small>drivers probing · <code>NFS: Mounting …</code></small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="you"><b>5 · login:</b><small><code>VFS: Mounted root</code> → <code>init</code> → shell</small></div>
  </div>
</div>` },
        cues: [
          "Press B to blank this window, switch the Teams share to the terminal, power-cycle the Pi.",
          "Narrate each handoff as it scrolls. Pause at 'Starting kernel ...'.",
          "Come back here, un-blank, and point at the five boxes: 'that was the whole talk, in 20 seconds'.",
        ],
      },

      /* ===== Footnote & close =========================================== */
      {
        id: "rpi4",
        section: "Footnote",
        title: "How our RPi4 maps to this",
        caption: "A GPU does the RBL + SPL jobs with proprietary firmware. From U-Boot on, identical.",
        visual: { key: "rpi4", html: `
<div class="dg">
  <div class="dg-group">
    <span class="dg-label">Generic ARM SoC — TI · NXP · ST · Allwinner · Qualcomm</span>
    ${chain([], ["rbl", "spl", "uboot", "kernel", "rootfs"]).replace('<div class="dg">', "").replace(/<\/div>\s*$/, "")}
  </div>
  <div class="dg-group" data-tone="focus">
    <span class="dg-label">Raspberry Pi 4 — BCM2711</span>
    <div class="dg-row">
      <div class="dg-box" data-grow="2" data-state="focus"><b>VideoCore GPU + <code>start4.elf</code></b><small>proprietary firmware: initialises DRAM, loads U-Boot — the RBL and SPL roles in one</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-state="on"><b>U-Boot</b><small>same</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-state="on"><b>Kernel + Device Tree</b><small>same</small></div>
      <div class="dg-arrow" data-dir="right"></div>
      <div class="dg-box" data-state="on"><b>Root filesystem</b><small>same</small></div>
    </div>
  </div>
</div>` },
        cues: [
          "This is why the demo looked slightly different from the diagram. The concepts map 1:1.",
        ],
      },
      {
        id: "end",
        section: "Next",
        title: "Session 2: your code doesn't own the hardware anymore",
        caption: "The thread: what sits between your code and the hardware, and why?",
        visual: { key: "end", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="on"><b>1 · From power-on to a shell</b><small>today</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Your code doesn't own the hardware</b><small>processes, virtual memory, syscalls — what the OS does between you and the silicon</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="ghost"><b>3 · How Linux knows your hardware exists</b><small>Device Tree → driver → /dev</small></div>
  </div>
</div>` },
        cues: [
          "One sentence of pull for next time, then questions.",
        ],
      },
    ],
  });
})();
