# KSS #1 — Resources

Everything referenced in *From power-on to a shell*, in one place.

## Recording

- [Meeting recording (SharePoint, Soliton access)](https://solitontech.sharepoint.com/:v:/r/sites/SLEDSolitonLaboratoryofEmbeddedDivision/Shared%20Documents/Embedded%20Linux/Recordings/Embedded%20Linux%20KSS%20_1%20%20From%20Power-On%20to%20a%20Shell,-20261120_170503-Meeting%20Recording.mp4?d=wb3fdf0d319174b6586c2e8202b9c0374&csf=1&web=1&e=lYJ00x)

## The session

| What | Where |
|---|---|
| Slide deck (runs on a local server, not a static file) | [launcher](index.html) · [how to run it](../README.md#running-a-session) |
| This lab repository (decks, lab tooling, board docs) | Repository root: [README](../../../README.md) |

To view the deck yourself:

```bash
git clone <this repository>
cd arm-embedded-linux-lab
python3 docs/kss/_shared/serve.py        # opens the session 1 launcher
```

Use `→` / `←` to move between steps.
## Repeat the demo yourself

The demo (network boot of a Raspberry Pi 4: DHCP → TFTP → kernel → NFS root) is repeatable from this repo.

- [U-Boot TFTP boot](../../raspi4/uboot_tftp_boot.md)
- [Network boot deep dive](../../raspi4/netboot_deep_dive.md)
- [BusyBox root filesystem](../../raspi4/rootfs_busybox.md)
- [EEPROM network boot](../../raspi4/eeprom_netboot.md)
- [Boot architecture](../../raspi4/boot_architecture.md)

Lab hardware (boards, sensors, actuators) is available to try ideas on. Details are on the community channel.

## Go deeper

- [Udemy: Embedded Linux step by step using BeagleBone](https://www.udemy.com/course/embedded-linux-step-by-step-using-beaglebone/) — a Cortex-A board, covering bootloaders through drivers. Extensive and long, but a good full-length course. Different board from the demo; the concepts are the same.
- **Official documentation** — the main source for details. Pick what you need rather than reading end to end:
  - [U-Boot documentation](https://docs.u-boot.org/) · [source](https://github.com/u-boot/u-boot)
  - [Linux kernel documentation](https://docs.kernel.org/)
  - [BusyBox](https://busybox.net/) · [command reference](https://busybox.net/downloads/BusyBox.html)
  - [Raspberry Pi boot sequence](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#boot-sequence) — the GPU-firmware-first flow on our demo board
- **Practice beats reading.** Try each step on a board; the concepts do not stick otherwise.

## Coming later

A terminology pre-read for newcomers, ahead of the next session, was requested. It will be linked here when ready.
