# Session 02 — Your code doesn't own the hardware anymore

> **Status:** Draft for review. Not yet approved; the deck is built from this file after approval.
> If the story changes, update this file first, then run `python3 docs/kss/_shared/build_deck.py session-02-userspace-kernel-boundary`.

**Audience:** Mixed — students, RTOS/firmware engineers, application developers, driver developers.
**Goal:** What the OS does between your code and the silicon, and why your program can no longer touch hardware directly.
**Format:** Two windows — [audience view](show.html) shared on the call, [presenter view](present.html) on the speaker's screen — plus a live demo. Launcher: [index.html](index.html).

## Planning notes

**Where this sits in the series:** continues [session 1](../session-01-boot-flow/STORY.md), which ended with the kernel up, the MMU on and a shell running. Session 1 showed *that* the kernel takes over; this session explains what that changes for your code. It leads into [session 3](../session-03-device-tree-to-dev/STORY.md), which is the other end of the system-call door.

**Single question:** what does the OS actually do between your code and the silicon, and why can't your code simply touch the hardware?

**How the audience form shaped this draft:**
- Mostly newcomers, so every term (exception level, page table, system call, interrupt) is defined inline on first use, and the depth stays at mental-model level.
- *How the kernel talks to hardware* was a top ask. This session sets up the wall and the door; session 3 delivers the driver side. The close hands off explicitly.
- Firmware/RTOS engineers are the second-largest group, so there is a dedicated RTOS contrast (`ctx-owner`, `vm-noskip`, `cpu-rtos`) built on what they already know.
- *Real mistakes and how they were fixed* and *why it breaks* were asked for: the `breaks` beat maps symptoms (segfault, EPERM, Killed, hang) to mechanisms.
- *A map of what to learn next*: the close carries the series map with the *later* topics.

**Demo prep (verify before presenting; nothing below is confirmed on the board yet):**
- A system-call tracer (such as `strace`) is not in the BusyBox rootfs by default. Either add one to the rootfs build or replace demo part 1 with a different visible syscall.
- A tiny C program that writes to the UART's physical address needs to be written and cross-compiled for the board. Confirm it faults on the lab kernel.
- The kernel module part uses the existing hello-world module. Confirm `insmod` and `dmesg` work over the lab's SSH, and that `dmesg` prints `hello: loaded`.
- Optional extra: show `/proc/<pid>/maps` of a running process to make the virtual address space visible.

**Cue seeds (go into `deck.js` when the deck is built, not on screen):**
- `open-question`: ask the room who has written a register address in firmware. Let the RTOS folks answer first.
- `open-carry`: BRIDGE (verbal) — remind them of the rail chips from session 1: CPU mode went from ROM to kernel to user.
- `ctx-modes`: if asked, the CPU starts at the highest level at reset and firmware drops it down. Don't expand.
- `vm-peripherals`: pause after "not mapped" and let the opening question land before reading the answer.
- `sys-printf`: ask where they think the bytes go next at each arrow.
- `cpu-rtos`: invite the RTOS folks to correct or extend. Don't claim Linux can't be real-time.
- `breaks`: WAR STORY (optional) — a real segfault or hang from the lab.
- `demo`: press `B`, switch the share to the terminal, narrate, come back.
- `end`: BRIDGE (verbal) — "we said only the kernel can touch the UART; but how does it know where it is?"

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
On a Cortex-M, this works. You write a character to the UART's data register and it comes out of the pin:

`*(volatile unsigned int *)0xFE201000 = 'A';`

Now take the board from session 1, the one that just gave you a shell. Compile the same line into a normal Linux program and run it. You get `Segmentation fault`. Same CPU. Same board. Same address. Who said no, and how?

**Visual:** left — "bare metal": the line of C → a UART with an *A* coming out. Right — "Linux": the same line → `Segmentation fault`.

<!-- step: open-carry -->
Session 1 ended with a shell. If you looked at the status chips along the way, the CPU went from *executing from ROM*, to *kernel mode*, to *user mode*. That last change is today. At the end of session 1 the kernel handed you a process, and between you and the hardware it left a wall.

**Visual:** the five-stage chain from session 1, dimmed. A wall appears between *Kernel + Device Tree* and *Root filesystem*, with "user mode" on the right of it.

<!-- step: open-today -->
Here is what today covers. First, the wall itself: what you are no longer allowed to do, and where that is enforced. Then your own private memory, which is the answer to the opening question. Then the one door through the wall, the system call. Then how the kernel takes the CPU back from a program that won't give it up.

We finish with a live demo on the Pi: watch a system call happen, hit the wall on purpose, and then load a piece of code that is on the other side of it.

**Visual:** four agenda chips in order — the wall → your own memory → the only door → taking the CPU back.

<!-- step: open-series -->
This is the second of three sessions. Session 1 was how the board gets to a shell. Today is what the OS does between your code and the hardware. Session 3 is the other end of the door: how Linux learns the hardware exists, and how a driver turns a peripheral into a file you can open.

**Visual:** three session boxes in a row — 1 done, 2 highlighted, 3 dim.

---

## 1. Before the wall — what you had without an OS

<!-- step: ctx-owner -->
### Bare metal: you own everything

On a microcontroller the reset vector leads to your `main()`. Your code is the only code. You read and write any register, touch any byte of RAM, enable or mask any interrupt. Nothing stands between your code and the silicon.

Most RTOSes add tasks and a scheduler to that picture, but usually keep its shape: one program image, one shared address space, every task allowed to do everything.

**Visual:** two stacks. Left: "your firmware" sitting directly on "hardware". Right: "tasks" on "RTOS" on the same "hardware", with one shared memory block beneath all of them.

<!-- step: ctx-cost -->
### The price of owning everything

When everything shares one address space, a bug anywhere is a bug everywhere. A stray pointer in the logging task overwrites the motor controller's state, and the symptom shows up somewhere else, much later.

That is acceptable when one team writes all the code and tests it as one unit. It is not acceptable when a board runs many programs, written by many people, some of them updated after the board shipped. Linux is built for that second case.

**Visual:** three task boxes on one memory strip; a red arrow from one task into another's slice.

<!-- step: ctx-modes -->
### The CPU itself has a privilege level

A Cortex-A core is not all-powerful at every moment. It always runs at a **privilege level**. On 64-bit ARM these are called **exception levels**: **EL0** is the least privileged, where ordinary programs run, and **EL1** is where the kernel runs. At EL0 the CPU refuses certain instructions and refuses to touch certain registers, such as the ones that control memory translation and interrupts.

This is a property of the silicon, not a rule the kernel merely asks programs to follow.

**Visual:** two stacked boxes: *EL1 — kernel* above *EL0 — your program*. A line between them labelled "page tables · interrupt control · privileged registers", locked.

**Rail state:** Privilege: EL1 (kernel) / EL0 (program) · Address space: physical · Owner: the kernel

---

## 2. Part 1 — The wall: "the one the silicon enforces"

<!-- step: wall-what -->
When your program runs, the CPU is at the user privilege level. If it tries something only the kernel may do — write to a peripheral register, change the memory map, mask interrupts — the CPU does not carry it out. It raises an **exception**, which jumps into the kernel at an address the kernel chose. The kernel looks at what happened and, usually, ends the process. That is what you see as a segmentation fault.

**Visual:** the user box attempts an arrow down to "hardware"; the arrow bounces and an exception arrow goes up to the kernel box.

**Rail state:** Privilege: user mode · Address space: virtual · Owner: you, within limits

<!-- step: wall-why -->
Why does the wall exist? Because the kernel has to stay alive no matter what any program does. If any program could write any register, one buggy or hostile program could take down every other program, or the whole board. A shared system needs one party that is always in charge, and it needs something stopping everyone else from taking that role.

**Visual:** same picture as `ctx-cost`, redrawn with the wall between each task and the kernel; the red arrow now stops at the wall.

<!-- step: wall-noskip -->
Why doesn't the kernel simply ask programs to behave, or check their code at build time? Because a rule that the program itself can bypass is not a rule. Only a check made by the hardware, on every instruction, is something a program cannot talk its way around.

The honest alternative is to give up isolation for speed and run everything privileged, which is what the bare-metal and RTOS designs above do. Linux chooses isolation.

**Visual:** two columns — "software promise" (a cracked box) and "hardware check" (a solid box).

<!-- step: wall-owner -->
**Who writes it:** the privilege levels are part of the ARM architecture, built into the core design the silicon vendor licenses. The kernel sets everything up in its first moments, as we saw in session 1. Your program starts on the user side of the wall, and stays there.

**Visual:** one box "privilege levels", tagged *ARM architecture → in the SoC*, with the chips "enforced by hardware" and "configured by the kernel".

---

## 3. Part 2 — Virtual memory: "everyone sees their own memory"

<!-- step: vm-what -->
A **process** is a running program plus its own private view of memory, its **virtual address space**. Two different programs can each believe their code starts at the same address, and neither is wrong. The **MMU** (the memory-translation hardware you met in session 1) turns each program's virtual addresses into physical RAM locations using a **page table**, a lookup table the kernel builds for each process. When the kernel switches from one process to another, it switches the page table.

**Visual:** two processes on the left, each with the same address column (0x0 … 0xFFFF…); an MMU box in the middle; a single physical RAM strip on the right, with each process mapped to a different slice.

**Rail state:** Privilege: user mode · Address space: virtual, one per process · Owner: the kernel builds it, the MMU applies it

<!-- step: vm-why -->
There are two payoffs. **Isolation:** process A has no address that leads into process B's memory, because its page table never mentions it, so there's nothing to attack. **Freedom from placement:** a program doesn't care where in physical RAM it landed, or whether its memory is contiguous.

A third payoff matters to anyone who has debugged a crash: an address with no mapping is an error. A null-pointer dereference becomes a clean, loud fault, instead of silently reading some other part of RAM.

**Visual:** same picture, one arrow from process A aimed at an address with no mapping → "fault".

<!-- step: vm-noskip -->
Why not simply give each program its own fixed physical region and trust the linker? Programs would have to be built for a specific place in RAM, memory would fragment as programs start and stop, and one program's bad pointer could still reach another's region.

Some Cortex-M parts have a simpler hardware option, a **Memory Protection Unit (MPU)**, which guards a small, fixed number of regions. The MMU is the scaled-up version: a full per-process table, so any number of programs.

**Visual:** a row of three options — "fixed regions", "MPU", "MMU + page tables" — with the last one in focus.

<!-- step: vm-peripherals -->
Now the opening question has an answer. A peripheral's registers are just physical addresses, like `0xFE201000` for the UART. Your process's page table does not map them, so when your program writes to that address it is writing to an address that doesn't exist in its world, and the MMU raises a fault. Only the kernel has a mapping for the hardware, and it builds that mapping deliberately, driver by driver. Session 3 is about how.

One caveat: root can sometimes map physical memory through `/dev/mem`, if the kernel was built to allow it. That is a deliberate hole used for debugging, not the normal path.

**Visual:** two page tables side by side. Process: code, heap, stack, and a row for the UART marked "not mapped". Kernel: the same plus the UART row in focus.

<!-- step: vm-owner -->
**Who writes it:** the MMU hardware comes with the core, from ARM through the silicon vendor. The kernel builds and switches the page tables. Your program just uses addresses and never sees the machinery.

**Visual:** one box "MMU", tagged *in the SoC*, plus one box "page tables", tagged *kernel*.

---

## 4. Part 3 — System calls: "the only door through the wall"

<!-- step: sys-what -->
Your program still needs to do things that live outside its own memory: print, read a file, open a socket, allocate more memory. For all of these it asks the kernel, using a **system call**.

A system call is a special instruction (`svc` on 64-bit ARM). It does not jump to an address of the program's choosing. The CPU switches to the kernel privilege level and jumps to **one entry point the kernel set up**. The kernel looks at which call was requested, does the work on the program's behalf, and returns, dropping the CPU back to user level.

**Visual:** user box → a narrow door labelled `svc` → kernel box; a return arrow back, with the privilege chip flipping kernel → user.

**Rail state:** Privilege: user → kernel → user · Address space: virtual · Owner: the kernel, on your behalf

<!-- step: sys-printf -->
Follow one `printf("hello\n")` down to the serial console:

1. `printf` is a library function in your program's **libc**. It formats and buffers the text.
2. libc calls `write(1, …)`, which executes the `svc` instruction. Now you are in the kernel.
3. The kernel finds out what file descriptor 1 is: the console, a terminal device.
4. The terminal layer hands the bytes to the UART **driver**.
5. The driver writes them into the UART's registers. That is the very write your program wasn't allowed to make.

The kernel does for you the exact thing the wall stopped you from doing yourself, with its own checks in the middle.

**Visual:** a chain of boxes, `printf` → libc → `write()` → kernel → driver → UART. Boxes before the door are in the user group, after it in the kernel group.

<!-- step: sys-why -->
Why a door, and not just letting programs call kernel functions? Because if a program could jump to any kernel address it would sidestep the wall. A single, narrow entry point is something the kernel can guard. At that entry point the kernel treats everything coming from user space as untrusted: it checks the arguments, and it checks that any memory address you pass really belongs to your process.

**Visual:** a wide-open door (red) vs a narrow door with a gatekeeper (green).

<!-- step: sys-cost -->
The wall has a price. A system call costs noticeably more than a plain function call, because the CPU switches level, and the kernel checks and does real work. For most programs this is invisible. It is why high-rate code batches its work (one `write` of a big buffer instead of many small ones) and why some interfaces let a program map memory directly instead of copying it through calls.

**Visual:** two small timelines: many tiny syscalls vs one batched syscall.

<!-- step: sys-owner -->
**Who writes it:** the list of system calls, and what each one means, is the kernel's contract with user space, and it is kept stable on purpose so old programs keep working. libc wraps those calls in ordinary C functions, so you almost never write `svc` yourself. Your own code, written in C with libc, sits entirely on the user side.

**Visual:** three boxes: "your code" (you), "libc" (a library), "system-call interface" (kernel), with arrows down.

---

## 5. Part 4 — The scheduler: "taking the CPU back"

<!-- step: cpu-what -->
The wall protects memory and hardware. But what about time? What if a program enters an infinite loop and never gives the CPU back?

The kernel arms a **hardware timer** that fires an **interrupt** every few milliseconds. An interrupt forces the CPU into the kernel no matter what the program is doing. The kernel's **scheduler** then decides who runs next: the same program for another slice, or a different one.

**Visual:** a timeline strip: *A runs* | tick | *scheduler* | *B runs* | tick | *scheduler* | *A runs*. Colour the kernel slots blue.

**Rail state:** Privilege: kernel on each tick · Address space: switches with the process · Owner: the kernel

<!-- step: cpu-why -->
This is why the timer and the privilege wall fit together. A program cannot disable the timer or mask the interrupt, because those are privileged operations. So no program can keep the CPU for itself. Without that guarantee, the kernel would depend on every program being polite.

**Visual:** same strip, with one program trying to stop the tick and the wall blocking it.

<!-- step: cpu-rtos -->
### For the RTOS folks

An RTOS preempts on a timer tick too. The difference is the goal. An RTOS is designed around priorities and a bounded, predictable response time. Linux's default scheduler is designed around fairness and throughput across many programs. Linux can be tuned toward real-time behaviour, but that is a whole topic of its own and not a given.

**Visual:** two lanes — "RTOS: highest priority always first, bounded latency" and "Linux default: share the CPU fairly".

<!-- step: cpu-owner -->
**Who writes it:** the timer is a peripheral in the SoC; ARM cores include a generic one. The scheduler is part of the kernel and is written by the kernel community. How the kernel finds that timer on this particular board is the same question as how it finds the UART, and that is session 3.

**Visual:** two boxes, "timer" (*SoC*) and "scheduler" (*kernel community*), with an arrow from the first to the second.

---

## 6. The whole wall — one picture

<!-- step: summary -->
| Mechanism | What it enforces | What it means for your code |
|---|---|---|
| **Privilege levels** | Only the kernel can touch privileged registers and hardware. | You can't poke a peripheral directly. |
| **Virtual memory** | Each process sees only its own memory. | A stray pointer faults instead of corrupting a neighbour. |
| **System calls** | One guarded entry into the kernel. | Anything outside your memory is a request, not a right. |
| **Timer + scheduler** | The kernel always gets the CPU back. | No program can hog the board. |

**Visual:** the four rows build in one after another; the last row carries a "you are here" tag on the user side.

<!-- step: breaks -->
Each mechanism fails in a recognisable way, and the symptom tells you which one you hit:

- **`Segmentation fault`** — you used an address with no mapping: a null or stray pointer, a freed buffer, or an attempt to reach hardware directly.
- **`Operation not permitted`** — a system call was refused because you lack the privilege for it, such as a device or a setting only root may use.
- **`Killed`** — the kernel ended the process, often because the board ran out of memory.
- **The program hangs and uses no CPU** — it is blocked inside a system call, waiting for something. Tracing the system calls, as we'll do in the demo, shows which one.

**Visual:** one row per symptom — what you see → which mechanism → where to look first.

---

## 7. Live demo — "see the wall on the board"

<!-- step: demo -->
### What to watch on the serial console or SSH session

1. **Watch a system call happen.** Trace a trivial command such as `echo hi`. Among the lines you'll see the `write` call that carries your text to the console.
2. **Hit the wall on purpose.** Run a tiny program that writes to the UART's physical address. It dies with a segmentation fault: the same line that worked on the Cortex-M.
3. **Go to the other side.** Load the small kernel module, and read its message with `dmesg`. This code runs at the kernel privilege level on the same board, with no wall. A bug here would not be a segfault but a kernel crash.

**Visual:** the three things to watch, as a checklist the audience keeps in view while the terminal is shared.

<!-- step: demo-repeat -->
You can repeat the third part yourself. The workflow for adding and loading an out-of-tree kernel module is in [new kernel module](../../../.agents/workflows/new_kernel_module.md), and the BusyBox rootfs the board runs is described in [BusyBox rootfs](../../raspi4/rootfs_busybox.md).

**Visual:** two chips — "new kernel module workflow" and "BusyBox rootfs".

---

## 8. Footnote — how our RPi4 maps to this

<!-- step: rpi4 -->
The Raspberry Pi 4 runs Linux in 64-bit mode (AArch64), so the privilege levels here are the exception levels we used: your programs at EL0, the kernel at EL1. ARM defines EL2 for hypervisors and EL3 for the secure firmware layer. A 32-bit ARM core has the same idea under different names (user mode and supervisor mode).

The concepts transfer to any ARM Cortex-A board running Linux.

**Visual:** a vertical stack EL3 / EL2 / EL1 / EL0, with EL1 and EL0 highlighted and labelled "Linux" and "your programs".

---

## 9. Close

<!-- step: end -->
The wall explains a lot, and it leaves one question open. We said only the kernel can touch the UART. But how does the kernel know that there is a UART, and at which address? And how does a peripheral become a file your program can `open`? That is the other end of the door, and it is session 3.

**Visual:** the series as a map: sessions 1 and 2 done, session 3 highlighted, and a *later* group (bring up a new board · build an image · cross-compile and deploy · networking).

<!-- /steps -->

---

## Review log

Changes made during story review, kept so future sessions can learn from them:

| Feedback | Change |
|---|---|
| First draft written from the audience form, session 1 and the storytelling skill. Awaiting review. | — |
