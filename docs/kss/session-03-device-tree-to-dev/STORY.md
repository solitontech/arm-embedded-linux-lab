# Session 03 — How Linux knows your hardware exists

> **Status:** Draft for review. Not yet approved; the deck is built from this file after approval.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py session-03-device-tree-to-dev`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** How a peripheral at a fixed address becomes a device you can open from user space, and who wrote each link in that chain.
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live demo. Launcher: [index.html](index.html).

## Planning notes

**Where this sits in the series:** continues [session 2](../session-02-userspace-kernel-boundary/STORY.md), where your program reaches the kernel through system calls and cannot touch hardware. [Session 1](../session-01-boot-flow/STORY.md) introduced the Device Tree in one beat; this session expands that beat into the whole story and closes the series.

**Single question:** how does a peripheral at a fixed address become something you can open from user space, and who wrote each link in that chain?

**How the audience form shaped this draft:**
- *How the kernel talks to hardware* and *writing or debugging device drivers* were top asks. This session is the payoff for both.
- Newcomers dominate, so the opening is one command on the Pi (an LED turning on from a file write), and the three-link chain (describe, bind, expose) is the spine. Kernel internals stay at one idea per step.
- *Real mistakes and how they were fixed*: the `breaks` beat maps symptoms to links (missing node, silent `compatible` typo, failed or deferred probe, no `/dev` entry).
- The "generic → your specifics" pattern appears here for the third time (SPL, U-Boot, Device Tree). `dt-layers` says so out loud.
- The close ties the whole series together and carries the *later* topics for the audience to pick from.

**Demo prep (verify before presenting; nothing below is confirmed on the board yet):**
- Confirm which LED the lab kernel exposes under `/sys/class/leds/` and its name, and that a write to `brightness` visibly changes it.
- Confirm `/proc/device-tree` is present and readable on the lab rootfs, and that the UART or LED node exists with the properties we read out.
- Confirm `/sys/bus/platform/drivers/` shows the expected driver and that device→driver links can be followed over SSH.
- Optional second demo, not built yet: a small platform driver (a variant of the hello-world module) bound to a node added by an overlay, so the audience sees `probe()` print on `dmesg`. This needs a new project; start from the new-kernel-module workflow if you want it.

**Cue seeds (go into `deck.js` when the deck is built, not on screen):**
- `open-question`: ask the room how they'd turn on an LED from a program on this board.
- `open-chain`: BRIDGE (verbal) — name sessions 1 and 2 as the two ends of this road.
- `ctx-where`: pause on the question mark; the next beat answers it.
- `dt-layers`: CONTEXT (verbal) — "third time we've seen generic → your specifics"; ask the room to say the pattern with you.
- `dt-owner`: only explain the `0x7e…` vs `0xFE…` difference if someone opens the real file.
- `bind-sees`: WAR STORY (optional) — a real `compatible` typo or overlapping DTB overlay from the lab.
- `breaks`: ask the room which of these they have already stared at.
- `demo`: press `B`, switch the share to the terminal, narrate each link, come back.
- `end`: ask which *later* topic they want first.

## How this file drives the deck

- `<!-- step: id -->` marks the start of one beat. The prose that follows, up to the next marker or the next `##` heading, becomes the **presenter's notes** for that beat.
- The matching entry in [`deck.js`](deck.js) (same `id`) defines what the **audience** sees: title, visual, caption, hardware-state chips — and the presenter's **cues** (things to say that are *not* on screen).
- Paragraphs starting with `**Visual:**` or `**Rail state:**` are authoring notes; the generator drops them.
- Prose outside any marker (this header, the review log) is not shown anywhere.

## Who says what

| Speaker (verbal — lives in `deck.js` cues) | Audience sees (`deck.js` visuals) | Presenter reads (this file) |
|---|---|---|
| Why we're looking at this today; the alternatives; why this approach | One title, one visual, one caption per beat | What each thing *is*, why it exists, who writes it |
| Bridges between sections | Hardware-state chips | Terms defined on first use |
| War stories, "we learned the hard way" | — | — |
| Live demo narration | A frame of what to watch for | Demo checklist |

The audience never sees paragraphs. The page never carries anecdotes. Those are the speaker's.

---

## 0. Opening

<!-- step: open-question -->
On the Pi, you can type one line into the shell:

`echo 1 > /sys/class/leds/<led>/brightness`

and a light turns on. You wrote a character into a file. There is no register, no address, no pointer anywhere in sight. So which file is that? Who created it? And how did a write to a file become a voltage on a pin?

**Visual:** a one-line terminal command → an arrow → a lit LED.

<!-- step: open-chain -->
In session 1 the kernel found out the board's hardware from a Device Tree. In session 2 we saw that your program can't touch hardware, and can only knock on the kernel's door. Today is the stretch of road between those two facts. It has three links, and each has a different author:

1. **Describe:** the hardware is written down in a Device Tree.
2. **Bind:** a driver that recognises that description takes charge of the hardware.
3. **Expose:** the driver publishes a file your program can open.

**Visual:** three boxes in a row — Describe → Bind → Expose — then an arrow out to "your `open()`". Boxes dim.

<!-- step: open-today -->
Here is what today covers: what a driver actually needs to know, then the three links in order — the Device Tree node, the match that wakes a driver up, and the interface the driver publishes. Then how things go wrong at each link, and a live look at all three on the Pi.

**Visual:** four agenda chips — what a driver needs → describe → bind → expose.

<!-- step: open-series -->
This is the last of the three sessions, and it closes the loop. Session 1 got the board to a shell. Session 2 explained the wall between your code and the hardware. Today we find the other end of the door, the part of the kernel that actually does the work. After this, the topics you asked for in the form — bringing up a new board, building an image, cross-compiling, networking — all build on this foundation.

**Visual:** three session boxes — 1 and 2 done, 3 highlighted — and a dim *later* group.

---

## 1. Before the chain — what a driver knows, and what it can't

<!-- step: ctx-driver -->
A **driver** is the code that knows how to operate one kind of hardware: which register starts a transfer, which bit means "busy", in what order to program it. It is the datasheet, written in C.

The same piece of silicon design is often reused across many chips. A common UART block, for instance, appears in SoCs from several vendors. One driver can run all of them.

**Visual:** one driver box (`pl011` driver) with three different chips below it, all marked "same UART design".

<!-- step: ctx-where -->
What a driver cannot know is where its hardware lives on this particular board: at which address, on which interrupt line, driven by which clock, wired to which pins. Those facts change from chip to chip and from board to board, even though the UART design is identical.

So there has to be another source for them. The kernel needs the *how* from the driver and the *where* from something else.

**Visual:** two columns — "driver knows: registers, bits, sequences" and "driver can't know: address, interrupt, clock, pins". The second column has a question mark over it.

---

## 2. Link 1 — Describe: "the hardware announces itself, in a file"

<!-- step: dt-what -->
That something else is the **Device Tree**. You met it in session 1; now we open it. It's a data file, not code. Each piece of hardware is a **node**, and a node is a handful of **properties**:

- `compatible` — a name that says what this hardware is, for example `"arm,pl011"`
- `reg` — where its registers live: address and size
- `interrupts` — which interrupt line it raises
- `clocks` — which clock feeds it
- `status` — whether it is enabled (`"okay"`) or switched off (`"disabled"`)

**Visual:** a five-line DT node with `compatible` highlighted and the other properties labelled by what they answer: *what · where · which interrupt · which clock · on or off*.

**Rail state:** Described by: a DT node · Bound to: nothing yet · Visible as: nothing yet

<!-- step: dt-why -->
Why a data file, and not C code inside the kernel? Years ago, ARM Linux carried a board file written in C for every board it supported. There were hundreds of them, and it did not scale: every new board meant changing the kernel. Moving the board facts out into data means **one kernel image can run on many boards**, and a new board needs a new description, not a new kernel.

And why can't the kernel just look for the hardware? Because, as we saw in session 1, a fixed peripheral on a SoC doesn't announce itself. Somebody has to write it down.

**Visual:** left — "board file in C × hundreds of boards" (red); right — "one kernel + a small data file per board" (green).

<!-- step: dt-layers -->
### Generic → your specifics, a third time

By now this shape should feel familiar. SPL was generic until you supplied your DRAM parameters. U-Boot was generic until you supplied your boot flow. The Device Tree is layered the same way:

- The **SoC `.dtsi`**, written by the silicon vendor, describes every peripheral on the chip.
- The **board `.dts`**, written by the board manufacturer, includes it and says which peripherals are actually wired up and how.
- An **overlay**, written by you, adds or changes a node for the hardware you attached.

Typical edits at the board or overlay level are flipping a node's `status` to `"okay"`, or adding a new node for the sensor you wired in.

**Visual:** a vertical stack: SoC `.dtsi` (silicon vendor) → board `.dts` (board manufacturer) → overlay (you, in yellow), with an arrow "includes" between layers.

<!-- step: dt-handoff -->
The `.dts` text is compiled by the **device tree compiler** (`dtc`) into a compact binary, the `.dtb`. Then, as in session 1: U-Boot, or on the Pi the GPU firmware, loads the `.dtb` into DRAM and hands the kernel its address. The kernel unpacks the blob into a tree in memory that it can walk.

You can see that tree from the shell: it is exposed under `/proc/device-tree` (also reachable at `/sys/firmware/devicetree/base`). That folder structure is the board's description, as the kernel received it.

**Visual:** `.dts` → `dtc` → `.dtb` → (U-Boot / firmware) → DRAM → kernel tree → `/proc/device-tree`.

<!-- step: dt-owner -->
**Who writes it:** three authors, as in the layers above — silicon vendor, board manufacturer, and you. A mistake in any layer is a mistake the kernel will faithfully believe, because the Device Tree is the only source of truth the kernel has.

**Presenter note on addresses:** in the real file for the Pi, the UART appears at `0x7e201000`. That is its address on the chip's internal bus. The parent node's `ranges` property translates it to `0xFE201000`, the address the CPU uses and the one we've used in these sessions. Mention it only if someone opens the file and asks.

**Visual:** three boxes tagged *silicon vendor*, *board manufacturer*, *you*, each with one example line.

---

## 3. Link 2 — Bind: "the driver says what it can drive"

<!-- step: bind-what -->
Each driver declares a list of `compatible` names it knows how to drive. When the kernel walks the Device Tree, it creates a **device** for each hardware node, then looks for a driver whose list contains that node's `compatible`. When it finds a match, it **binds** the two and calls the driver's **`probe()`** function.

This was the one-line summary in session 1. Now you can see both halves: the node on one side, the driver's list on the other, and the `compatible` string as the handshake.

**Visual:** a DT node on the left, a driver's match list on the right, the matching `compatible` highlighted in both, an arrow to a `probe()` box.

**Rail state:** Described by: a DT node · Bound to: a driver `probe()` · Visible as: nothing yet

<!-- step: bind-probe -->
`probe()` is the driver's hello. It reads the node and sets the hardware up:

1. Get the register address from `reg`, and map it into the kernel's address space. This is the deliberate mapping session 2 said only the kernel has.
2. Get the interrupt from `interrupts` and attach a handler.
3. Get the clock from `clocks` and switch it on.
4. Initialise the hardware, then register with the kernel (the next link).

If a resource isn't ready yet, such as a clock whose own driver hasn't loaded, `probe()` asks to be retried later. The kernel calls this **deferred probe**, and it is a common reason a device appears late.

**Visual:** four chips in a row: map registers → attach interrupt → enable clock → register.

<!-- step: bind-why -->
Why this design? Because it separates the two kinds of knowledge. The driver holds the *how*, written once. The Device Tree holds the *where*, written per board. A new board that reuses a known UART needs no new driver code, only a new node.

Why can't the kernel just load drivers by address? Because an address says nothing about what's at it. The `compatible` string is the only thing that says "this is a PL011".

**Visual:** a driver box feeding three boards, each with its own small DT node.

<!-- step: bind-sees -->
Binding is something you can look at. Under `/sys/bus/platform/devices/` is one entry per device the kernel created from the tree. Under `/sys/bus/platform/drivers/` is one folder per driver, and a bound device appears there as a link.

This gives you a debugging model with two simple states: a device with no driver bound to it, and a driver with no device to probe. Most "my hardware doesn't work" problems are one of these.

**Visual:** two columns, *devices* and *drivers*, with lines for bound pairs, one orphan device and one idle driver, each marked.

<!-- step: bind-owner -->
**Who writes it:** the drivers for the SoC's built-in peripherals come mostly from the silicon vendor and the kernel community. If you design custom hardware, or attach a part nobody has written a driver for, the driver is yours. The matching mechanism itself is part of the kernel.

**Visual:** one box "match + probe" tagged *kernel*, with two boxes under it: *drivers for the SoC* (vendor / community) and *your own driver* (you).

---

## 4. Link 3 — Expose: "the driver publishes an interface"

<!-- step: expose-what -->
A driver that only initialises hardware is no use to your program. So `probe()` ends by registering the device with a **subsystem**: the kernel's framework for one class of hardware, such as serial ports (tty), LEDs, GPIO, I2C or input devices. The subsystem gives the device a standard interface to user space: a file in `/dev`, and often a set of attributes under `/sys`.

When `/dev` is managed by the kernel (the `devtmpfs` filesystem, which our rootfs mounts at boot), the file appears the moment the driver registers.

**Visual:** driver → subsystem box → two outputs: `/dev/…` and `/sys/class/…`.

**Rail state:** Described by: a DT node · Bound to: a driver · Visible as: `/dev` and `/sys` entries

<!-- step: expose-why -->
Why a subsystem layer in the middle? So your program doesn't have to know the chip. Twenty different UART chips with twenty different drivers all show up as serial ports with the same behaviour, so the same program works on all of them. The standard interface is what makes software portable across boards.

**Visual:** several different chip boxes at the bottom, one common interface box at the top.

<!-- step: expose-door -->
Now connect it back to session 2. Your program opens a device file and calls `write()`. That is a system call: it goes through the door into the kernel. The kernel finds which driver owns that file, and calls the **handler the driver registered for `write`**. The driver then does the register access using the mapping it made in `probe()`.

So the door from session 2 and the driver from today are two ends of the same path.

**Visual:** `write()` → syscall door → kernel finds the driver → driver's `write` handler → register. The same visual language as the session 2 `printf` chain, with the driver highlighted.

<!-- step: expose-led -->
That is the answer to the opening question. The LED driver bound to the LED node, registered with the LED subsystem, and the subsystem created a `brightness` file for it. When you write `1` to that file, the subsystem calls the driver, and the driver sets the pin.

No part of your command touched a register. Every link in the chain did its job so that you wouldn't have to.

**Visual:** the opening command again, now annotated link by link: file write → LED subsystem → LED driver → GPIO pin → LED.

<!-- step: expose-owner -->
**Who writes it:** the subsystem, and the shape of the interface it presents, is the kernel community's work. The driver fills it in for its hardware. Your application consumes it. That split is why an application that toggles an LED or reads a serial port keeps working when the board underneath it changes.

**Visual:** three boxes: *subsystem interface* (kernel community), *driver* (vendor / you), *your application* (you).

---

## 5. The whole chain — one picture

<!-- step: summary -->
| Link | What happens | Who wrote it |
|---|---|---|
| **Describe** | A Device Tree node says what hardware exists and where. | Silicon vendor, board manufacturer, you |
| **Bind** | The kernel matches `compatible` to a driver and calls `probe()`. | Kernel community, vendors |
| **Expose** | The driver registers with a subsystem; `/dev` and `/sys` entries appear. | Kernel community, vendors, you |
| **Use** | Your program opens the file and uses system calls. | You |

**Visual:** the four rows build in one after another, with the opening chain's three boxes as the left column.

<!-- step: breaks -->
Each link fails in its own way, and the symptom tells you which link to check first:

- **Nothing under `/sys/bus/platform/devices/`** for your hardware — the *describe* link: the node is missing, its `status` is `"disabled"`, or the overlay wasn't applied.
- **The device is listed but has no driver** — the *bind* link: a typo in `compatible`, or the driver wasn't built into the kernel or loaded as a module. Nothing complains. A typo here fails silently.
- **`dmesg` shows `probe` failing with an error** — the *bind* link, inside `probe()`: a missing resource (address, clock, regulator) or a deferred probe that never completes.
- **Bound, but no file in `/dev`** — the *expose* link: the driver didn't register, or `/dev` isn't being populated.

**Visual:** one row per symptom — what you see → which link → what to check first.

---

## 6. Live demo — "see the three links on the board"

<!-- step: demo -->
### What to watch on the serial console or SSH session

1. **Describe:** list `/proc/device-tree` and open one node, such as the UART or the LED. Read its `compatible`, `reg` and `status` the way the kernel did.
2. **Bind:** look in `/sys/bus/platform/drivers/` for the driver that claimed that node, and follow the link from the device to its driver.
3. **Expose:** find the file the driver published, and use it. Write to the LED's `brightness` file, and watch the light respond.

**Visual:** the three things to watch, as a checklist the audience keeps in view while the terminal is shared.

<!-- step: demo-repeat -->
You can repeat all of this on your own board. The Raspberry Pi 4 docs cover how the Device Tree is built and loaded: [boot architecture](../../raspi4/boot_architecture.md) and [kernel and Device Tree build](../../raspi4/kernel_build.md).

**Visual:** two chips — "boot architecture" and "kernel + Device Tree build".

---

## 7. Footnote — how our RPi4 maps to this

<!-- step: rpi4 -->
On the Raspberry Pi 4, the GPU firmware loads the base Device Tree (`bcm2711-rpi-4-b.dtb`) and applies any overlays named in `config.txt` before the kernel starts. So the tree the kernel sees may differ from the plain `.dtb` file on disk. When something doesn't match what you edited, check which Device Tree your boot path actually passes to the kernel.

Everything else on the way from node to `/dev` is identical to any other ARM Cortex-A board.

**Visual:** generic path above, Pi path below; "firmware merges overlays" on the Pi's loading step.

---

## 8. Close

<!-- step: end -->
Put the three sessions together and you have an answer to the series' question, *what sits between your code and the hardware, and why?* A chain of firmware that gets the board running. A wall that protects everyone from everyone else. And a layer of descriptions and drivers that turns raw silicon into files you can open.

The topics you asked for next, such as bringing up a new board, building an image with Yocto or Buildroot, cross-compiling and deploying your own application, and networking, each work on one of these layers. Tell us which one you want first.

**Visual:** the three sessions all done, and the *later* group of topics highlighted for choosing.

<!-- /steps -->

---

## Review log

Changes made during story review, kept so future sessions can learn from them:

| Feedback | Change |
|---|---|
| First draft written from the audience form, session 1 and the storytelling skill. Awaiting review. | — |
