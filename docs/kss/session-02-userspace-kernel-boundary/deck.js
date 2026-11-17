/* ==========================================================================
   Session 2 — Your code doesn't own the hardware anymore — deck definition
   What the AUDIENCE sees (title, visual, caption, hardware-state chips) and
   what the PRESENTER says but does not show (cues).
   Presenter prose comes from STORY.md via deck-content.js (generated).

   Visual rules (see _shared/COMPONENTS.md and the kss-deck-builder skill):
   - Build visuals from dg-* primitives only.
   - Consecutive steps that share visual.key MORPH: give boxes a stable
     data-id and change only data-state; the engine animates the change.
   - One thing to notice per step. Title = the claim, caption = the consequence.

   CUES ARE THE PRESENTER'S TO EDIT — they're seeded from the story's planning notes.
   ========================================================================== */
(() => {
  /* ---- reusable fragments --------------------------------------------- */

  // The wall: program / wall / kernel / hardware as a vertical stack.
  // `s` maps data-id → data-state; `ex` overrides the small text under a box.
  function wallPic(s = {}, ex = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const t = (id, dflt) => (ex[id] !== undefined ? ex[id] : dflt);
    return `
<div class="dg">
  <div class="dg-box" data-id="prog"${st("prog")}><b>Your program</b><small>${t("prog", "user mode · EL0")}</small></div>
  <div class="dg-arrow" data-id="ar-direct">${t("ar-direct", "write a peripheral register")}</div>
  <div class="dg-box" data-id="wall"${st("wall")}><b>The wall</b><small>${t("wall", "enforced by the CPU")}</small></div>
  <div class="dg-arrow" data-id="ar-kernel">${t("ar-kernel", "only the kernel goes through")}</div>
  <div class="dg-box" data-id="kernel"${st("kernel")}><b>Kernel</b><small>${t("kernel", "kernel mode · EL1")}</small></div>
  <div class="dg-arrow" data-id="ar-hw"></div>
  <div class="dg-box" data-id="hw"${st("hw")}><b>Hardware</b><small>${t("hw", "registers · peripherals")}</small></div>
</div>`;
  }

  // Virtual memory: two processes → MMU → one physical RAM. `uart` adds the UART row.
  function vmPic(s = {}, ex = {}, uart = false) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const t = (id, dflt) => (ex[id] !== undefined ? ex[id] : dflt);
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-col" data-grow="2">
      <div class="dg-box" data-id="pa"${st("pa")}><b>Process A</b><small>${t("pa", "its code starts at 0x400000")}</small></div>
      <div class="dg-box" data-id="pb"${st("pb")}><b>Process B</b><small>${t("pb", "its code starts at 0x400000")}</small></div>
    </div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="mmu"${st("mmu")}><b>MMU</b><small>${t("mmu", "one page table per process")}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-col" data-grow="2">
      <div class="dg-box" data-id="ram-a"${st("ram-a")}><b>Physical RAM</b><small>${t("ram-a", "A's slice")}</small></div>
      <div class="dg-box" data-id="ram-b"${st("ram-b")}><b>Physical RAM</b><small>${t("ram-b", "B's slice")}</small></div>
      ${uart ? `<div class="dg-box" data-id="ram-uart"${st("ram-uart")}><b>UART registers</b><small>${t("ram-uart", "0xFE201000")}</small></div>` : ""}
    </div>
  </div>
</div>`;
  }

  // System-call path. `full` adds libc, the driver and the UART.
  function doorPic(full, s = {}, ex = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    const t = (id, dflt) => (ex[id] !== undefined ? ex[id] : dflt);
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group" data-id="g-user" data-tone="you">
      <span class="dg-label">User side</span>
      <div class="dg-row">
        <div class="dg-box" data-id="prog"${st("prog")}><b>${full ? "printf(…)" : "Your code"}</b><small>${t("prog", full ? "your program" : "needs something done")}</small></div>
        ${full ? `<div class="dg-arrow" data-dir="right"></div>
        <div class="dg-box" data-id="libc"${st("libc")}><b>libc</b><small>${t("libc", "formats, buffers")}</small></div>` : ""}
      </div>
    </div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="door"${st("door")}><b>${full ? "write()" : "svc"}</b><small>${t("door", full ? "the system call" : "one entry point")}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-group" data-id="g-kernel" data-tone="focus">
      <span class="dg-label">Kernel side</span>
      <div class="dg-row">
        <div class="dg-box" data-id="kernel"${st("kernel")}><b>Kernel</b><small>${t("kernel", full ? "console → terminal layer" : "does the work")}</small></div>
        ${full ? `<div class="dg-arrow" data-dir="right"></div>
        <div class="dg-box" data-id="drv"${st("drv")}><b>UART driver</b><small>${t("drv", "writes the registers")}</small></div>` : ""}
      </div>
    </div>
    ${full ? `<div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-id="uart"${st("uart")}><b>UART</b><small>${t("uart", "serial console")}</small></div>` : ""}
  </div>
</div>`;
  }

  // The scheduler timeline. `tryStop` adds the program's failed attempt to stop the tick.
  function cpuPic(tryStop = false, s = {}) {
    const st = (id) => (s[id] ? ` data-state="${s[id]}"` : "");
    return `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-id="a1" data-state="you"><b>A runs</b><small>user mode</small></div>
    <div class="dg-box" data-id="t1" data-state="focus"><b>tick</b><small>scheduler</small></div>
    <div class="dg-box" data-id="b1" data-state="you"><b>B runs</b><small>user mode</small></div>
    <div class="dg-box" data-id="t2" data-state="focus"><b>tick</b><small>scheduler</small></div>
    <div class="dg-box" data-id="a2" data-state="you"><b>A runs</b><small>user mode</small></div>
  </div>
  ${tryStop ? `<div class="dg-row dg-center" data-id="row-try">
    <div class="dg-box" data-id="try" data-state="pain"><b>Program: mask the timer interrupt</b><small>privileged operation</small></div>
    <div class="dg-arrow" data-dir="right">refused</div>
    <div class="dg-box" data-id="try-wall" data-state="focus"><b>The wall</b><small>the tick still fires</small></div>
  </div>` : ""}
</div>`;
  }

  // Summary / symptom rows: narrow label box + wide text box.
  const row = (label, text, state = "ghost", wide = "") =>
    `<div class="dg-row"><div class="dg-box" data-state="${state}"><b>${label}</b></div><div class="dg-box" data-grow="3"${wide}>${text}</div></div>`;

  // The series map used by the opening and the close.
  const seriesBoxes = (a, b, c, subs = {}) => `
  <div class="dg-row">
    <div class="dg-box" data-state="${a}"><b>1 · From power-on to a shell</b><small>${subs[1] || "what boots, in what order"}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="${b}"><b>2 · Your code doesn't own the hardware</b><small>${subs[2] || "the wall, memory, syscalls"}</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="${c}"><b>3 · How Linux knows your hardware exists</b><small>${subs[3] || "Device Tree → driver → /dev"}</small></div>
  </div>`;

  /* ---- rail presets ----------------------------------------------------- */
  const rail = {
    modes: { "Privilege": "EL1 kernel · EL0 programs", "Address space": "physical", "Owner": "the kernel" },
    wall:  { "Privilege": "user mode", "Address space": "virtual", "Owner": ["you, within limits", "you"] },
    vm:    { "Privilege": "user mode", "Address space": ["virtual, one per process", "ok"], "Owner": "the kernel builds it, the MMU applies it" },
    sys:   { "Privilege": ["user → kernel → user", "ok"], "Address space": "virtual", "Owner": "the kernel, on your behalf" },
    cpu:   { "Privilege": "kernel on each tick", "Address space": "switches with the process", "Owner": "the kernel" },
  };

  /* ---- the deck --------------------------------------------------------- */
  KSS.defineDeck({
    id: "session-02",
    title: "Your code doesn't own the hardware anymore",
    plannedMinutes: 60,
    steps: [

      /* ===== Opening ===================================================== */
      {
        id: "open-question",
        section: "Session 2",
        title: "Same line of C, different result",
        caption: "Who said no, and how?",
        visual: { key: "intro", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group" data-grow="2">
      <span class="dg-label">Bare metal · Cortex-M</span>
      <div class="dg-term"><span class="c">*(volatile unsigned int *)0xFE201000 = 'A';</span></div>
      <div class="dg-arrow"></div>
      <div class="dg-box" data-state="on"><b>UART prints A</b></div>
    </div>
    <div class="dg-group" data-grow="2" data-tone="focus">
      <span class="dg-label">Linux · same board</span>
      <div class="dg-term"><span class="c">*(volatile unsigned int *)0xFE201000 = 'A';</span></div>
      <div class="dg-arrow"></div>
      <div class="dg-box" data-state="pain"><b>Segmentation fault</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "Ask the room: who has written a register address in firmware? Let the RTOS folks answer first.",
          "Don't explain yet. Leave the question open; it's answered at 'Your page table has no row for the UART'.",
        ],
      },
      {
        id: "open-carry",
        section: "Session 2",
        title: "Session 1 ended on the far side of a wall",
        caption: "The kernel handed you a process, and left a wall.",
        visual: { key: "carry", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="ghost"><b>ROM Bootloader</b></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="ghost"><b>SPL</b></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="ghost"><b>U-Boot</b></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>Kernel + Device Tree</b><small>kernel mode</small></div>
    <div class="dg-box" data-state="focus" data-grow="0"><b>THE WALL</b></div>
    <div class="dg-box" data-state="you"><b>Root filesystem</b><small>user mode</small></div>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): remember the status chips from session 1? The CPU line went from 'executing from ROM' to 'kernel mode' to 'user mode'. That last change is today.",
        ],
      },
      {
        id: "open-today",
        section: "Session 2",
        title: "Today: the wall, and the door through it",
        caption: "Then a live demo on the Pi.",
        visual: { key: "agenda", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · The wall</b><small>what you can no longer do</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>2 · Your own memory</b><small>the answer to the opening question</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>3 · The only door</b><small>system calls</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="focus"><b>4 · Taking the CPU back</b><small>timer and scheduler</small></div>
  </div>
</div>` },
        cues: [
          "Set the time expectation (about an hour) and say questions are welcome at each part boundary.",
          "Flag the live demo near the end: a system call, the wall, and a kernel module.",
        ],
      },
      {
        id: "open-series",
        section: "Session 2",
        title: "Where this fits: session 2 of 3",
        caption: "Session 3 is the other end of the door.",
        visual: { key: "series", html: `<div class="dg">${seriesBoxes("on", "focus", "ghost", { 1: "done" , 2: "today", 3: "next" })}</div>` },
        cues: [
          "Tie it to the series question: what sits between your code and the hardware, and why? Session 1 was the bottom of the stack; today is the boundary.",
        ],
      },

      /* ===== Before the wall ============================================= */
      {
        id: "ctx-owner",
        section: "Before the wall",
        title: "On bare metal, you own everything",
        caption: "Most RTOSes keep that shape: one shared address space.",
        visual: { key: "ctx", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-group">
      <span class="dg-label">Bare metal</span>
      <div class="dg-col">
        <div class="dg-box" data-state="you"><b>Your firmware</b><small>the only code</small></div>
        <div class="dg-box"><b>Hardware</b><small>every register, every byte</small></div>
      </div>
    </div>
    <div class="dg-group">
      <span class="dg-label">RTOS</span>
      <div class="dg-col">
        <div class="dg-box" data-state="you"><b>Tasks</b><small>all allowed to do everything</small></div>
        <div class="dg-box"><b>RTOS</b><small>scheduler</small></div>
        <div class="dg-box"><b>Hardware</b><small>one shared memory</small></div>
      </div>
    </div>
  </div>
</div>` },
        cues: [
          "Compare to what they know: reset vector → main() → you own the chip. RTOS adds tasks, not walls.",
        ],
      },
      {
        id: "ctx-cost",
        section: "Before the wall",
        title: "In one address space, every bug is everyone's",
        caption: "The symptom shows up somewhere else, much later.",
        visual: { key: "ctx-mem", html: `
<div class="dg">
  <div class="dg-group">
    <span class="dg-label">One shared address space</span>
    <div class="dg-row">
      <div class="dg-box" data-state="you"><b>Logging task</b><small>has a stray pointer</small></div>
      <div class="dg-arrow" data-dir="right">overwrites</div>
      <div class="dg-box" data-state="pain"><b>Motor controller state</b><small>corrupted</small></div>
      <div class="dg-box"><b>Sensor task</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "Ask the room: has anyone chased a corruption that turned out to be a different task's bug?",
          "Say plainly: that's fine when one team tests everything as one unit. Linux is built for the other case.",
        ],
      },
      {
        id: "ctx-modes",
        section: "Before the wall",
        title: "The CPU itself has a privilege level",
        caption: "A property of the silicon, not a rule programs are asked to follow.",
        rail: rail.modes,
        visual: { key: "levels", html: `
<div class="dg">
  <div class="dg-box" data-state="focus"><b>EL1 — kernel</b><small>runs privileged code</small></div>
  <div class="dg-arrow">page tables · interrupt control · privileged registers — locked to EL0</div>
  <div class="dg-box" data-state="you"><b>EL0 — your program</b><small>ordinary programs</small></div>
</div>` },
        cues: [
          "CONTEXT (verbal): if asked, the CPU starts at the highest level at reset and firmware drops it down. Don't expand.",
        ],
      },

      /* ===== Part 1 — The wall ========================================== */
      {
        id: "wall-what",
        section: "Part 1 · The wall",
        title: "Touch hardware from user mode: the CPU says no",
        caption: "The kernel usually ends the process: a segmentation fault.",
        rail: rail.wall,
        visual: { key: "wall", html: wallPic(
          { prog: "you", wall: "focus", kernel: "on" },
          { wall: "CPU raises an exception into the kernel" }) },
        cues: [
          "Let the picture sit: the arrow from the program never reaches the hardware box.",
        ],
      },
      {
        id: "wall-why",
        section: "Part 1 · The wall",
        title: "The kernel must stay alive whatever runs",
        caption: "A shared system needs one party always in charge.",
        rail: rail.wall,
        visual: { key: "wall", html: wallPic(
          { prog: "pain", wall: "focus", kernel: "on" },
          { prog: "buggy or hostile", ["ar-direct"]: "any program, any bug", kernel: "must keep running" }) },
        cues: [
          "BRIDGE (verbal): back to the logging task. With the wall, that red arrow stops at the wall.",
        ],
      },
      {
        id: "wall-noskip",
        section: "Part 1 · The wall",
        title: "Only hardware can enforce an unbypassable rule",
        caption: "Linux chooses isolation over the speed of running everything privileged.",
        visual: { key: "wall-skip", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="off"><b>A software promise</b><small>asked to behave · checked at build time</small></div>
    <div class="dg-box" data-state="on"><b>A hardware check</b><small>on every instruction, no way round it</small></div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): the alternative is real, and it's what bare-metal and RTOS designs do. Fast, simple, no isolation.",
        ],
      },
      {
        id: "wall-owner",
        section: "Part 1 · The wall",
        title: "The privilege levels come with the ARM core",
        caption: "The kernel sets them up; your program starts on the user side.",
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-box" data-state="focus"><b>Privilege levels</b><small>ARM architecture → in the SoC</small></div>
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">enforced by hardware</span>
    <span class="dg-chip" data-state="focus">configured by the kernel</span>
    <span class="dg-chip" data-state="you">your program starts at the user level</span>
  </div>
</div>` },
        cues: [
          "Transition: that was the wall for the CPU. Now the wall for memory.",
        ],
      },

      /* ===== Part 2 — Virtual memory ==================================== */
      {
        id: "vm-what",
        section: "Part 2 · Virtual memory",
        title: "Every process gets its own view of memory",
        caption: "Two programs, same addresses, different RAM.",
        rail: rail.vm,
        visual: { key: "vm", html: vmPic(
          { pa: "you", pb: "you", mmu: "focus", "ram-a": "on", "ram-b": "on" }) },
        cues: [
          "BRIDGE (verbal): this is the MMU from session 1. Then it was 'addresses become virtual'; now you see why.",
        ],
      },
      {
        id: "vm-why",
        section: "Part 2 · Virtual memory",
        title: "Isolation, free placement, loud faults",
        caption: "An address with no mapping is an error, not a silent read.",
        rail: rail.vm,
        visual: { key: "vm", html: vmPic(
          { pa: "pain", pb: "you", mmu: "focus", "ram-a": "on", "ram-b": "on" },
          { pa: "a stray address → fault", "ram-b": "A can't name this" }) },
        cues: [
          "Ask the room: what does a null-pointer dereference do on a Cortex-M with no MMU?",
        ],
      },
      {
        id: "vm-noskip",
        section: "Part 2 · Virtual memory",
        title: "Fixed regions don't scale; page tables do",
        caption: "The MMU is the scaled-up version of the MPU.",
        visual: { key: "vm-opts", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="off"><b>Fixed regions</b><small>one program per place in RAM</small></div>
    <div class="dg-box" data-state="ghost"><b>MPU</b><small>a small, fixed number of regions</small></div>
    <div class="dg-box" data-state="focus"><b>MMU + page tables</b><small>a full table per process</small></div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): RTOS folks with an MPU know a slice of this already; invite them to say what it protects.",
        ],
      },
      {
        id: "vm-peripherals",
        section: "Part 2 · Virtual memory",
        title: "Your page table has no row for the UART",
        caption: "Only the kernel maps hardware, deliberately, driver by driver.",
        rail: rail.vm,
        visual: { key: "vm", html: vmPic(
          { pa: "pain", pb: "you", mmu: "focus", "ram-a": "on", "ram-b": "on", "ram-uart": "off" },
          { pa: "writes 0xFE201000", "ram-uart": "not mapped for your process" }, true) },
        cues: [
          "Pause after 'not mapped' and let the opening question land before you say the answer out loud.",
          "BRIDGE (verbal): session 3 is how the kernel builds that mapping for the hardware.",
        ],
      },
      {
        id: "vm-owner",
        section: "Part 2 · Virtual memory",
        title: "MMU in silicon, page tables in the kernel",
        caption: "",
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>MMU</b><small>hardware · ARM core in the SoC</small></div>
    <div class="dg-box" data-state="focus"><b>Page tables</b><small>built and switched by the kernel</small></div>
  </div>
  <div class="dg-chips" style="justify-content:center"><span class="dg-chip" data-state="you">your program just uses addresses</span></div>
</div>` },
        cues: [
          "Transition: the program is boxed in. It still needs to get things done. How?",
        ],
      },

      /* ===== Part 3 — System calls ====================================== */
      {
        id: "sys-what",
        section: "Part 3 · System calls",
        title: "A system call is the only door into the kernel",
        caption: "The CPU jumps to one entry point the kernel chose.",
        rail: rail.sys,
        visual: { key: "door", html: doorPic(false, { prog: "you", door: "focus", kernel: "on" }) },
        cues: [
          "Say the return trip out loud: the kernel does the work, then drops the CPU back to user mode.",
        ],
      },
      {
        id: "sys-printf",
        section: "Part 3 · System calls",
        title: "One printf, all the way down to the UART",
        caption: "The kernel makes the register write you weren't allowed to.",
        rail: rail.sys,
        visual: { key: "door", html: doorPic(true, { prog: "you", libc: "you", door: "focus", kernel: "on", drv: "on", uart: "on" }) },
        cues: [
          "Ask the room: at each arrow, where do the bytes go next?",
          "Note: this path is for the serial console. Over SSH the last hops differ.",
        ],
      },
      {
        id: "sys-why",
        section: "Part 3 · System calls",
        title: "A narrow door is a door the kernel can guard",
        caption: "Everything from user space is untrusted until checked.",
        visual: { key: "door-why", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="pain"><b>Wide-open door</b><small>jump to any kernel address</small></div>
    <div class="dg-box" data-state="on"><b>One narrow door</b><small>arguments and addresses checked at the gate</small></div>
  </div>
</div>` },
        cues: [
          "CONTEXT (verbal): one sentence on why a wide door defeats the wall; don't go into how the checks work.",
        ],
      },
      {
        id: "sys-cost",
        section: "Part 3 · System calls",
        title: "A system call costs more than a function call",
        caption: "So high-rate code batches its work.",
        visual: { key: "cost", html: `
<div class="dg">
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip" data-state="pain">write</span><span class="dg-chip" data-state="pain">write</span><span class="dg-chip" data-state="pain">write</span><span class="dg-chip" data-state="pain">write</span><span class="dg-chip" data-state="pain">write</span><span class="dg-chip" data-state="pain">write</span>
  </div>
  <div class="dg-arrow">batch</div>
  <div class="dg-chips" style="justify-content:center"><span class="dg-chip" data-state="on">one write of a big buffer</span></div>
</div>` },
        cues: [
          "Keep it qualitative: noticeably more than a function call. No numbers.",
        ],
      },
      {
        id: "sys-owner",
        section: "Part 3 · System calls",
        title: "libc wraps the kernel's stable contract",
        caption: "You almost never write svc yourself.",
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-box" data-state="you"><b>Your code</b><small>you</small></div>
  <div class="dg-arrow"></div>
  <div class="dg-box"><b>libc</b><small>a library that wraps the calls in C functions</small></div>
  <div class="dg-arrow"></div>
  <div class="dg-box" data-state="focus"><b>System-call interface</b><small>the kernel's contract with user space, kept stable on purpose</small></div>
</div>` },
        cues: [
          "Transition: the wall protects memory and hardware. But what about time?",
        ],
      },

      /* ===== Part 4 — The scheduler ===================================== */
      {
        id: "cpu-what",
        section: "Part 4 · The scheduler",
        title: "A timer forces the CPU back into the kernel",
        caption: "Then the scheduler picks who runs next.",
        rail: rail.cpu,
        visual: { key: "cpu", html: cpuPic(false) },
        cues: [
          "Ask the room: what if a program enters an infinite loop? Let them say 'the kernel must take the CPU back'.",
        ],
      },
      {
        id: "cpu-why",
        section: "Part 4 · The scheduler",
        title: "A program can't stop the tick",
        caption: "Masking interrupts is privileged, so no program can keep the CPU.",
        rail: rail.cpu,
        visual: { key: "cpu", html: cpuPic(true) },
        cues: [
          "BRIDGE (verbal): this is the first wall again, now protecting time instead of memory.",
        ],
      },
      {
        id: "cpu-rtos",
        section: "Part 4 · The scheduler",
        title: "Same tick, different goal",
        caption: "Linux can be tuned toward real-time, but that's another topic.",
        visual: { key: "rtos", html: `
<div class="dg">
  <div class="dg-group">
    <span class="dg-label">RTOS</span>
    <div class="dg-row">
      <div class="dg-box" data-state="focus"><b>Highest priority first</b></div>
      <div class="dg-box" data-state="focus"><b>Bounded latency</b></div>
    </div>
  </div>
  <div class="dg-group">
    <span class="dg-label">Linux default</span>
    <div class="dg-row">
      <div class="dg-box" data-state="on"><b>Share the CPU fairly</b></div>
      <div class="dg-box" data-state="on"><b>Throughput across many programs</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "Invite the RTOS folks to correct or extend this. Do not claim Linux can't be real-time.",
        ],
      },
      {
        id: "cpu-owner",
        section: "Part 4 · The scheduler",
        title: "Timer in silicon, scheduler in the kernel",
        caption: "How the kernel finds this timer is session 3.",
        visual: { key: "owner", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>Timer</b><small>a peripheral in the SoC</small></div>
    <div class="dg-arrow" data-dir="right">interrupt</div>
    <div class="dg-box" data-state="focus"><b>Scheduler</b><small>kernel community</small></div>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): same question as the UART: how does the kernel know this timer exists, and where? That's session 3.",
        ],
      },

      /* ===== Summary ===================================================== */
      {
        id: "summary",
        section: "The whole wall",
        title: "Four mechanisms, one wall",
        caption: "",
        visual: { key: "summary", html: `
<div class="dg">
  ${row("Privilege levels", "Only the kernel touches hardware. You can't poke a peripheral.")}
  ${row("Virtual memory", "Each process sees only its own memory. A stray pointer faults.")}
  ${row("System calls", "One guarded entry into the kernel. Everything else is a request.")}
  ${row("Timer + scheduler", "The kernel always gets the CPU back. No program hogs the board.")}
  ${row("Your code", "Runs on the user side. You are here.", "you", ' data-state="you"')}
</div>` },
        cues: [
          "Read it top to bottom once, slowly. Then: 'questions before we look at what goes wrong?'",
        ],
      },
      {
        id: "breaks",
        section: "The whole wall",
        title: "The symptom tells you which mechanism you hit",
        caption: "Read the message, then pick the mechanism.",
        visual: { key: "breaks", html: `
<div class="dg">
  ${row("Segmentation fault", "An address with no mapping: a stray pointer, or reaching for hardware.")}
  ${row("Operation not permitted", "A system call refused for lack of privilege.")}
  ${row("Killed", "The kernel ended the process, often because the board ran out of memory.")}
  ${row("Hangs, no CPU use", "Blocked inside a system call. Tracing the calls shows which one.")}
</div>` },
        cues: [
          "WAR STORY (optional): one real segfault or hang from the lab, and which of these four it was.",
          "Ask the room: which of these have you stared at without knowing where to look?",
        ],
      },

      /* ===== Live demo =================================================== */
      {
        id: "demo",
        section: "Live demo",
        title: "Watch a call, hit the wall, cross it",
        caption: "Switching to the terminal — this is what to look for.",
        visual: { key: "demo", html: `
<div class="dg">
  <div class="dg-row">
    <div class="dg-box" data-state="focus"><b>1 · A system call</b><small>trace <code>echo hi</code>: the <code>write</code> carries your text</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="pain"><b>2 · The wall</b><small>write to the UART's physical address: segmentation fault</small></div>
    <div class="dg-arrow" data-dir="right"></div>
    <div class="dg-box" data-state="on"><b>3 · The other side</b><small>load a kernel module, read it in <code>dmesg</code></small></div>
  </div>
</div>` },
        cues: [
          "DEMO: press B to blank this window, switch the Teams share to the terminal.",
          "DEMO: narrate each of the three. For 3, say a bug here is a kernel crash, not a segfault.",
          "Transition: come back, un-blank, and point at the three boxes: 'that was the whole wall, in a few minutes'.",
        ],
      },
      {
        id: "demo-repeat",
        section: "Live demo",
        title: "You can repeat the module demo yourself",
        caption: "",
        visual: { key: "repeat", html: `
<div class="dg">
  <div class="dg-chips" style="justify-content:center">
    <span class="dg-chip">New kernel module workflow</span><span class="dg-chip">BusyBox rootfs</span>
  </div>
</div>` },
        cues: [
          "Point them at the new-kernel-module workflow and the BusyBox rootfs doc; share the links in the call chat.",
        ],
      },

      /* ===== Footnote & close =========================================== */
      {
        id: "rpi4",
        section: "Footnote",
        title: "On our Pi 4: programs at EL0, kernel at EL1",
        caption: "32-bit ARM has the same idea: user and supervisor mode.",
        visual: { key: "rpi4", html: `
<div class="dg">
  <div class="dg-box" data-state="ghost"><b>EL3</b><small>secure firmware layer</small></div>
  <div class="dg-box" data-state="ghost"><b>EL2</b><small>hypervisors</small></div>
  <div class="dg-box" data-state="focus"><b>EL1</b><small>the Linux kernel</small></div>
  <div class="dg-box" data-state="you"><b>EL0</b><small>your programs</small></div>
</div>` },
        cues: [
          "This is the concepts-transfer slide: any ARM Cortex-A board running Linux works the same way.",
        ],
      },
      {
        id: "end",
        section: "Next",
        title: "Session 3: how Linux knows your hardware exists",
        caption: "How does the kernel know there is a UART, and where?",
        visual: { key: "end", html: `
<div class="dg">
  ${seriesBoxes("on", "on", "focus", { 1: "done", 2: "today", 3: "Device Tree → driver → /dev" })}
  <div class="dg-group">
    <span class="dg-label">Later — not scheduled, shaped by your votes</span>
    <div class="dg-row">
      <div class="dg-box" data-state="ghost"><b>Bring up a new board</b></div>
      <div class="dg-box" data-state="ghost"><b>Build an image</b><small>Yocto · Buildroot</small></div>
      <div class="dg-box" data-state="ghost"><b>Cross-compile &amp; deploy your app</b></div>
      <div class="dg-box" data-state="ghost"><b>Networking</b></div>
    </div>
  </div>
</div>` },
        cues: [
          "BRIDGE (verbal): we said only the kernel can touch the UART. But how does it know where the UART is?",
          "One sentence of pull for session 3, then questions.",
        ],
      },
    ],
  });
})();
