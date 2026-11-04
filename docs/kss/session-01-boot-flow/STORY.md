# Session 1 — From Power-On to a Shell

> **Status:** Reviewed and approved. The deck is built from this file.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py session-01-boot-flow`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** An intuitive mental model of how a generic ARM Cortex-A Linux system boots, and why developers boot over the network during development.
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live RPi4 serial-console demo. Launcher: [index.html](index.html).

## How this file drives the deck

- `<!-- step: id -->` marks the start of one beat. The prose that follows, up to the next marker or the next `##` heading, becomes the **presenter's notes** for that beat.
- The matching entry in [`deck.js`](deck.js) (same `id`) defines what the **audience** sees: title, visual, caption, hardware-state chips — and the presenter's **cues** (things to say that are *not* on screen).
- Paragraphs starting with `**Visual:**` or `**Rail state:**` are authoring notes; the generator drops them.
- Prose outside any marker (this header, the review log) is not shown anywhere.

## Who says what

| Speaker (verbal — lives in `deck.js` cues) | Audience sees (`deck.js` visuals) | Presenter reads (this file) |
|---|---|---|
| Why we're looking at this today; the alternatives; why this approach | One title, one visual, one caption per beat | What each thing *is*, why it exists, who writes it |
| Bridges between sections ("remember the SoC/board split?") | Hardware-state chips | Terms defined on first use |
| Lab war stories, "we learned the hard way" | — | — |
| Live demo narration | A frame of what to watch for | Demo checklist |

The audience never sees paragraphs. The page never carries anecdotes. Those are the speaker's.

---

## 0. Opening

<!-- step: open-question -->
Imagine you plug a power cable into an embedded board. A second later, you see a blinking cursor on a serial terminal. Linux is running. A shell is waiting for your command.

But what happened in that one second? What ran first? Who decided what to run? And where was all of this code sitting before power existed?

<!-- step: open-relay -->
This is the story of how an ARM Cortex-A system boots — told in five stages, each handing off to the next, like a relay race where every runner exists because the previous one physically couldn't go any further.

**Visual:** the five stages as an outline chain, all dim. Nothing lit yet.

<!-- step: open-today -->
Here is what today covers. First the hardware you need to picture: what an SoC is, and who builds what around it. Then the five stages in order — ROM bootloader, SPL, U-Boot, kernel with Device Tree, root filesystem — each with what it is, why it exists, and who writes it.

After the chain, the practical half: how developers boot over the network during development instead of re-flashing an SD card, and how our Raspberry Pi 4 maps onto the generic story.

**Visual:** four agenda chips in order — SoC & board → five stages → network-boot workflow → our RPi4.

<!-- step: open-series -->
This is the first of a series. Each session peels back one layer between your code and the hardware.

Today: **what boots, in what order, and who wrote each stage.** Next: **session 2, your code doesn't own the hardware anymore** — what the OS does between your code and the silicon: processes, virtual memory, system calls. Then: **session 3, how Linux knows your hardware exists** — how a peripheral at a fixed address becomes a device you can open from user space.

**Visual:** three session boxes in a row, session 1 highlighted, 2 and 3 dim.

---

## 1. Before the chain — what is an SoC, and who builds what?

<!-- step: soc-chip -->
### The chip: System-on-Chip

A microcontroller like the STM32 or ATmega has a processor, some flash, some RAM, and a few peripherals — all in one package. An **SoC** (System-on-Chip) is the same idea, scaled up dramatically.

An SoC packs all of this onto a single piece of silicon:

- **CPU cores** — one or more ARM Cortex-A processors
- **On-chip SRAM** — a small, fast memory (tens to hundreds of KB) built into the chip, available immediately at power-on
- **DRAM controller** — the interface to the large external RAM. The RAM chips themselves are *not* on the SoC — they're separate chips on the board
- **Peripheral controllers** — UART, SPI, I2C, GPIO, USB, Ethernet, DMA, interrupt controller, timers… all on-chip
- **Boot ROM** — a small, permanent program burned into the chip during manufacturing
- Sometimes a **GPU**, **DSP**, or **NPU**

The SoC is designed and manufactured by a **silicon vendor** — Texas Instruments, NXP, STMicroelectronics, Broadcom, Qualcomm, MediaTek, Allwinner, and others.

**Visual:** the SoC die builds in — CPU, SRAM, Boot ROM, DRAM controller, peripherals.

<!-- step: soc-board -->
### The board: built around the SoC

The SoC alone can't do anything. It's a bare chip with hundreds of tiny pins. A **board manufacturer** takes that SoC and builds a complete circuit board (PCB) around it:

- **DDR memory chips** soldered next to the SoC, wired to the DRAM controller
- **Boot media** — an SD card slot, an eMMC flash chip, or SPI NOR flash
- **Connectors** — USB, Ethernet, GPIO header, camera, HDMI
- **Power regulation** — converting your 5 V input into the several voltages the SoC and memory need

The Raspberry Pi Foundation is a board manufacturer. So are BeagleBoard.org, Toradex, and Variscite. They all buy SoCs from silicon vendors and design boards around them.

**Visual:** the board builds in around the SoC — DDR chips, boot media, connectors, power.

<!-- step: soc-authors -->
### Three layers, three authors

The silicon vendor makes the chip. The board manufacturer builds the board. The software — SPL, U-Boot, the kernel, your application — is open source plus whatever you write.

**Visual:** the software layer builds in on top; each layer carries its author label.

---

## 2. Stage 1 — ROM Bootloader (RBL): "the one you can't change"

<!-- step: rbl-reset -->
When you apply power to an ARM SoC, the processor cores wake up and do exactly one thing: fetch an instruction from a fixed address. This address is the **reset vector** — a hardwired "start here" sign that the silicon itself enforces.

At that address, the SoC vendor has placed a small program in **mask ROM** — memory etched into the chip during fabrication. This is the ROM Bootloader. You cannot modify it, update it, or patch it. If it has bugs, the vendor publishes an *errata* document and you work around it.

**Visual:** reset vector → Boot ROM, inside the SoC. Everything else neutral.

**Rail state:** Memory: on-chip SRAM only · CPU: executing from ROM · Code: immutable

<!-- step: rbl-world -->
The RBL has a very limited world to work with. The only memory available is the on-chip **SRAM** — a few hundred kilobytes at most. The large external **DRAM** — the gigabytes on the board's spec sheet — is not usable yet. DRAM needs a configuration sequence before it can store a single byte, and the ROM doesn't know how to do that for your specific board.

**Visual:** SRAM lit; DRAM controller and the DDR chips on the board dark. The RBL can see inside the chip and just enough of the boot media to pull in one small binary.

<!-- step: rbl-minimum -->
So the RBL does the minimum:

1. Reads boot-configuration pins or **eFuses** (one-time-programmable bits inside the chip) to decide where to look for the next piece of software — SD card? SPI flash? eMMC? UART?
2. Reads a small binary from that boot media
3. Copies it into SRAM
4. Jumps to it

That small binary is the SPL. The RBL loads *it* rather than the Linux kernel for a simple reason: **the kernel is tens of megabytes and SRAM is a few hundred kilobytes. There is nowhere to put it.** The DRAM that could hold it doesn't work yet.

**Visual:** four boxes in a row: read boot pins → read a small binary → copy into SRAM → jump.

<!-- step: rbl-owner -->
**Who writes it:** the SoC vendor. It ships with the silicon. You never compile it, never flash it. It's just there, waiting for every power-on.

**Visual:** one box, "ROM Bootloader", tagged *SoC vendor*, with "immutable" and "errata, not patches".

---

## 3. Stage 2 — SPL (Secondary Program Loader): "the one that unlocks the big memory"

<!-- step: spl-intro -->
The SPL is the first piece of software that *you* — or your board vendor — can change. It's typically a stripped-down build of U-Boot, compiled small enough to fit in the chip's SRAM.

The RBL loaded it from boot media and placed it in SRAM. Now it runs.

**Visual:** same SoC diagram; SRAM now shows "SPL" inside, arrow from boot media. DRAM still dark.

**Rail state:** Memory: SRAM → DRAM coming online · CPU: executing from SRAM · Code: first stage you can change

<!-- step: spl-dram -->
The SPL has one critical job that nothing before it could do: **initialise the DRAM controller.**

Every board has different DDR memory chips soldered to its PCB. The DRAM controller inside the SoC must be configured with parameters specific to those chips before DRAM will work. The SoC vendor's ROM can't contain those parameters — they depend on which memory the board manufacturer chose. So the ROM hands this job to the SPL.

**Visual:** the DRAM controller and the DDR chips transition from dark to lit. This is the moment of the stage.

<!-- step: spl-handoff -->
Once the SPL has configured the controller, the full DRAM lights up. Instead of a few hundred KB of SRAM you now have gigabytes. The SPL then:

1. Reads the full U-Boot binary from boot media
2. Copies it into DRAM
3. Jumps to it

**Visual:** DRAM now contains "U-Boot"; arrow from boot media into DRAM.

<!-- step: spl-owner -->
*Why doesn't the SPL load the kernel directly?* It technically can — U-Boot calls this "Falcon mode" and it's used for fast-boot products. But normally the kernel expects a prepared environment: boot arguments, a Device Tree at a known address, the CPU in a particular state. Setting that up is the job of a full bootloader. The SPL stays small and focused: **init DRAM, load U-Boot, hand off.**

**Who writes it:** the SPL framework comes from the U-Boot project. The DRAM configuration comes from the SoC vendor's reference design, adapted by the board manufacturer for their board.

**Visual:** two boxes — "SPL framework · U-Boot project" and "DRAM config · SoC reference → board vendor".

---

## 4. Stage 3 — U-Boot: "the one that finds your kernel"

<!-- step: uboot-intro -->
U-Boot — "Das U-Boot", the Universal Bootloader — is now running in DRAM. After two stages of constrained bootstrap in tiny SRAM, this is the first stage with room to breathe. It has a full C runtime, drivers for storage, networking and serial, and an interactive command shell.

Its job: **load the Linux kernel and its hardware description (the Device Tree) into DRAM, then hand control to the kernel.**

**Visual:** DRAM as a large box with U-Boot inside; capability chips: C runtime · storage · network · serial · shell.

**Rail state:** Memory: full DRAM · CPU: executing from DRAM · Code: open source, configured by you

<!-- step: uboot-load -->
On a typical boot, U-Boot:

1. Loads the kernel image (`Image` on ARM64, `zImage` on ARM32) into a DRAM address
2. Loads the Device Tree Blob (`.dtb`) into a separate, non-overlapping DRAM address
3. Prepares **boot arguments** (`bootargs`) — a string telling the kernel which console to use, where the root filesystem is, and other options
4. Hands off — `booti` jumps to the kernel's entry point. U-Boot never runs again until the next reboot

**Visual:** DRAM address map — kernel `Image`, a labelled gap, the DTB, U-Boot near the top. Addresses are illustrative.

<!-- step: uboot-env -->
### Environment variables

U-Boot keeps its configuration as **environment variables** — key/value pairs such as `bootargs`, `serverip`, `bootcmd`. They control where it loads files from, what it passes to the kernel, and what it does automatically on power-on. You read them with `printenv`, change them with `setenv`, and persist them with `saveenv` (when the board provides storage for the environment). A boot script (`boot.scr`) is essentially a saved sequence of these commands, so you don't retype them every boot.

### The serial shell

Connect a serial cable and press a key during the boot countdown, and you get a `U-Boot>` prompt. From there you can run load commands by hand, inspect memory, and change variables. During early bring-up of a new board, this shell is invaluable.

**Visual:** a terminal block — `printenv`, `setenv`, `saveenv`, `tftp` — and three chips: `bootargs` · `serverip` · `bootcmd`.

<!-- step: uboot-why -->
### Why you customise U-Boot

U-Boot is generic — one codebase supports hundreds of SoCs and boards. But every product boots differently: where the kernel is stored (SD? eMMC? network?), which console device, which root filesystem, how long to wait before autobooting.

- The **defconfig** selects your SoC and board, so U-Boot includes the right drivers and memory map
- The **boot script** defines your load sequence
- **bootargs** tell the kernel about your board's console and rootfs

You customise these because U-Boot can't assume any of them. Your product's boot flow is yours to define.

**Visual:** "Generic U-Boot" → three boxes you supply: defconfig · boot script · bootargs.

<!-- step: uboot-source -->
The key flexibility is *where it loads from*: SD card, eMMC, USB, SPI flash — or, critically for development, **over the network via TFTP**. That's what makes the SD-card-free workflow possible.

**Who writes it:** an open-source project maintained at denx.de. SoC and board vendors contribute board configurations and drivers. You customise the boot flow.

**Visual:** boot sources side by side — SD · eMMC · USB · SPI · TFTP, with TFTP highlighted.

---

## 5. Stage 4 — Linux kernel + Device Tree: "the operating system takes over"

<!-- step: kernel-mmu -->
U-Boot has placed the kernel and Device Tree in DRAM and jumped to the kernel. From this moment the kernel owns the CPU and never gives control back.

### What the kernel does first

It enables the **MMU** (Memory Management Unit) — a hardware block in the CPU that translates memory addresses. Before this point, an address meant a physical location on the memory bus. After the MMU is on, addresses are **virtual** — a program sees one address, and the MMU translates it to wherever the physical memory actually is. This is what lets many programs run without stepping on each other's memory.

The kernel then sets up the interrupt controller, starts its scheduler, and begins probing hardware drivers.

**Visual:** physical addresses → MMU → virtual addresses; two programs each seeing their own address space.

**Rail state:** Memory: virtual (MMU on) · CPU: kernel mode · Code: open source + vendor drivers + your overlay

<!-- step: kernel-silent -->
### But how does the kernel know what hardware is on this board?

On a desktop PC, hardware announces itself: plug in a USB device and the USB controller detects it and reads its descriptor; PCI cards announce themselves during bus enumeration.

ARM SoCs don't work that way. The UART, GPIO controller, SPI bus, I2C controller, DMA engine — they're fixed peripherals at fixed addresses. Nobody announces them. They just sit there, silent, until something accesses them.

**Visual:** left — PC: "USB device: *hello, I'm a keyboard*". Right — SoC: UART, GPIO, I2C boxes, each marked "silent".

<!-- step: kernel-dt -->
The **Device Tree** is the announcement.

It's a data file, not code. Written in a readable source format (`.dts`), compiled to a compact binary (`.dtb`). It says things like: *"there is a UART at address 0xFE201000, on interrupt 57, clocked at 48 MHz."*

The kernel reads the Device Tree, walks its nodes, and for each one looks for a driver whose `compatible` string matches. When it finds one, it calls that driver's `probe()` function. That's how `/dev/ttyS0` appears: a Device Tree entry described the UART, the kernel matched it to a driver, and the driver created the device node.

**Visual:** a three-line DT node → "match `compatible`" → driver `probe()` → `/dev/ttyS0`.

<!-- step: kernel-layers -->
### The Device Tree is layered, because different people know different parts

- **SoC `.dtsi`** (e.g. `bcm2711.dtsi`) — written by the **SoC vendor**. Describes every peripheral on the chip. Shared by all boards using that SoC.
- **Board `.dts`** (e.g. `bcm2711-rpi-4-b.dts`) — written by the **board vendor**. Includes the SoC file and adds the board's wiring: which GPIO drives an LED, which I2C bus has a sensor.
- **Your overlay** — written by **you**, for hardware the board vendor didn't know about: a sensor on a GPIO, a relay for a safety system.

The kernel itself is written by the open-source Linux community, with SoC vendors contributing drivers and board vendors submitting board-specific patches.

After probing drivers, the kernel mounts a **root filesystem** and launches the first userspace process.

**Visual:** three stacked layers — SoC `.dtsi` (base), board `.dts` (extends), your overlay (adds) — each with its author.

---

## 6. Stage 5 — Root filesystem: "your application starts here"

<!-- step: rootfs-tree -->
The kernel is running and drivers are loaded. But a kernel on its own is not a usable system. It needs a **root filesystem** (rootfs) — the "disk" it mounts as `/` — to provide a shell, utilities, configuration, and your application.

The kernel's last act during boot is to mount this filesystem — from an SD card partition, a flash chip, or over the network via NFS — and execute `/sbin/init`. From then on you're in userspace.

**Visual:** a minimal directory tree with `/sbin/init` highlighted.

**Rail state:** Memory: virtual, per process · CPU: user mode · Code: yours

<!-- step: rootfs-build -->
### How is a rootfs built?

- **BusyBox** (~2 MB) — a single binary containing small implementations of 200+ Unix commands. Used for first bring-up and minimal appliances.
- **Buildroot** — compiles a complete custom rootfs from source; you choose the packages. Typically 5–25 MB.
- **Yocto / OpenEmbedded** — industrial-grade, layer-based build system. Maximum flexibility and reproducibility; used across automotive, industrial and consumer electronics.

Buildroot and Yocto are actually **full system build tools** — they can compile everything: U-Boot, the kernel, the Device Tree *and* the rootfs, from source, in one build. They appear here because the rootfs is where their output is most visible.

The rootfs is separate from the kernel: you can update your application without rebuilding the kernel, and vice versa.

**Who builds it:** you — the developer or system integrator.

**Visual:** BusyBox → "200+ commands"; size spectrum BusyBox · Buildroot · Yocto · full distro.

---

## 7. The complete chain — one picture

<!-- step: summary -->
| Stage | What it achieved |
|---|---|
| **ROM Bootloader** | Ran from on-chip ROM. Found the boot media. Loaded SPL into SRAM. |
| **SPL** | Ran from SRAM. Initialised DRAM. Loaded U-Boot into DRAM. |
| **U-Boot** | Ran from DRAM. Loaded kernel + Device Tree. Set boot arguments. Jumped to the kernel. |
| **Kernel + Device Tree** | Enabled the MMU. Probed drivers from the Device Tree. Mounted the rootfs. Launched `init`. |
| **Root filesystem** | Userspace. Shell. Your application. You're here. |

**Visual:** the five rows build in one after another.

---

## 8. Development workflow — "throw away the SD card"

<!-- step: flow-pain -->
Every time you change code during development, the SD-card workflow is:

> Edit → Compile → Power off → Pull SD → Mount on host → Copy → Unmount → Insert → Power on → Test → repeat

Minutes per cycle, dozens of cycles a day.

**Visual:** the loop as a row of pills, the card-handling steps marked in red.

<!-- step: flow-network -->
### The solution: make U-Boot load over the network

- **U-Boot fetches the kernel and DTB via TFTP** from your development machine on every boot
- **The kernel mounts the rootfs via NFS** from your development machine
- Files live on your host. Edit, reboot, the change is live. No card handling.

**Visual:** host ⇄ board with two labelled arrows: TFTP (kernel + DTB) and NFS (rootfs).

<!-- step: lab-map -->
### Our lab at a glance

Two machines and one Ethernet cable. The **development host** (here `192.168.1.220`, on interface `enp2s0`) holds everything the board boots from. The **Raspberry Pi 4** (`192.168.1.150`) holds nothing of its own: once its EEPROM is set to network boot it needs no SD card, and fetches its firmware, kernel and root filesystem from the host on every power-on.

**Visual:** host box and Pi box, one Ethernet arrow between them; the Pi's stages are dim outlines.

<!-- step: lab-docker -->
### One container runs every service the Pi needs

On the host, one Docker container (`./lab docker run`) runs the three network services. It uses **host networking**, so the services answer on the host's own IP — the Pi just talks to `192.168.1.220`, with no separate Docker address to route to. The repository is mounted into the container at `/workspace`, so a file edited on the host is the same file the services hand out.

| Service | Port | Role |
|---|---|---|
| **dnsmasq** | 67 | DHCP — gives the board an IP address and tells it where the TFTP server is |
| **tftpd-hpa** | 69 | TFTP — serves the boot files from `/workspace/tftp` |
| **nfs-kernel-server** | 2049 | NFS — exports `/workspace/nfs/rpi4-rootfs` to the lab subnet |

Why Docker: the same container works on macOS, Linux and Windows. Host networking and firewall rules still need a one-time setup per machine — see the lab docs.

**Visual:** the three services appear inside a Docker group on the host.

<!-- step: lab-dhcp -->
### 1 · DHCP — an address and a pointer

Power on. The Pi's EEPROM broadcasts a DHCP request. dnsmasq answers with an address from its pool (`192.168.1.150`–`.160`) and tells the Pi where boot files live: the TFTP server at `192.168.1.220`. dnsmasq does DHCP only; TFTP is a separate service so the two never contend for port 69.

**Visual:** the DHCP arrow builds in from the host to the Pi; dnsmasq lights up.

<!-- step: lab-tftp -->
### 2 · TFTP — the boot files arrive in order

The Pi now fetches its boot files from the host's `tftp/` folder, one after another:

1. `start4.elf` (+ `fixup4.dat`) — the GPU firmware, which on the Pi plays the ROM bootloader and SPL roles
2. `config.txt` — tells the firmware to run `u-boot.bin` instead of Linux
3. `u-boot.bin` — U-Boot
4. `boot.scr` — the boot script U-Boot runs; it sets the IP addresses and fetches the kernel
5. `Image` — the Linux kernel

The device tree is not a separate download in this setup: the GPU firmware hands U-Boot its DTB with the `config.txt` overlays (for example the camera) already applied.

**Visual:** the TFTP arrow builds in; the file chain appears under the diagram; the Pi's GPU firmware, U-Boot and kernel light up as their files arrive.

<!-- step: lab-nfs -->
### 3 · NFS — the root filesystem stays on the host

The boot script gives the kernel a command line with `root=/dev/nfs` and `nfsroot=192.168.1.220:/workspace/nfs/rpi4-rootfs`. The kernel brings up the network, mounts that exported directory as `/`, and runs `init` from it. The directory is an ordinary folder on the host: put a new binary in it and it is on the board's `/` immediately — no reboot, no SD card.

**Visual:** the NFS arrow builds in; the `nfsroot=` command-line line replaces the file chain; the Pi's rootfs lights up.

<!-- step: flow-demo -->
### Live demo — what to watch on the serial console

1. Power on — DHCP: the board asks for an IP and is told where TFTP is
2. TFTP: `Image` and the `.dtb` stream in (watch the byte counter)
3. `Starting kernel ...` — U-Boot hands off and never returns
4. Kernel log: MMU, drivers probing, `NFS: Mounting …`
5. `VFS: Mounted root (nfs filesystem)` → `init` → the login prompt

**Visual:** the five things to watch, as a checklist the audience keeps in view while the terminal is shared.

---

## 9. Footnote — how our RPi4 maps to this

<!-- step: rpi4 -->
The Raspberry Pi 4 has a non-standard early boot. Instead of an ARM-side ROM Bootloader loading an SPL, a **VideoCore GPU** loads proprietary firmware (`start4.elf`) that initialises DRAM and loads U-Boot. The GPU firmware combines the RBL and SPL roles.

From U-Boot onward, everything is identical to the flow above. Most production ARM SoCs — TI, NXP, ST, Allwinner, Qualcomm — follow the conventional RBL → SPL → U-Boot pattern described in this session.

**Visual:** generic chain above, RPi4 chain below; "GPU firmware" spans the RBL + SPL slots.

---

## 10. Close

<!-- step: end -->
The thread through this series: *what sits between your code and the hardware, and why?*

Next time: **your code doesn't own the hardware anymore** — what the OS actually does between your code and the silicon.

**Visual:** the series question, three session boxes, session 2 highlighted.

<!-- /steps -->

---

## Review log

Changes made during story review, kept so future sessions can learn from them:

| Feedback | Change |
|---|---|
| "Add an intuition of what an SoC is and how people build boards around it" | Added Section 1 before the chain |
| "The 'why this split matters for booting' bridge is not needed — I'll connect it vocally" | Removed; it is a presenter cue in `deck.js` |
| "Too much DDR detail (row activation, ranks, banks)" | Reduced to one sentence: parameters depend on the chips the board vendor chose |
| "Don't add lab learnings here" (DTB overlap war story) | Removed; war stories are presenter cues |
| "Talk about env variables" | Added *Environment variables* sub-section to U-Boot |
| "Rationale for customising U-Boot is missing — mirror the SPL pattern" | Added *Why you customise U-Boot*: generic tool → your specifics |
| "Buildroot/Yocto build kernel and DTS too, right?" | Clarified they are full-system build tools |
| "The page is too text-heavy to present; segregate presenter and viewer" | Split into audience view (visual per beat) and presenter view (this prose + cues); story gained `<!-- step -->` markers; one beat per screen |
