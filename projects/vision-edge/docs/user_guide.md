# VisionEdge User Guide

> Build, deploy, and operate the VisionEdge industrial inspection gateway.

---

## Prerequisites

- Docker running: `./lab docker run`
- RPi4 connected via Ethernet (for dev mode) or SD card prepared (for prod mode)
- Serial console available: `./lab console --board=rpi4`

---

## 1. Build

### Host build (x86, for development/testing)

```bash
cd projects/vision-edge
make clean && make -j$(nproc)
./build/host/vision-edge --help
```

### Cross-compile for RPi4 (inside Docker)

```bash
./lab docker exec -- bash -c "cd projects/vision-edge && make BOARD=rpi4 -j\$(nproc)"
```

Output: `projects/vision-edge/build/rpi4/vision-edge`

---

## 2. Deploy

### Development mode (EEPROM netboot + NFS)

No SD card required. The RPi4 boots entirely over the network.

```bash
# 1. Ensure Docker is running (serves TFTP + NFS)
./lab docker run

# 2. Deploy visiond binary to NFS rootfs
cp projects/vision-edge/build/rpi4/vision-edge \
   shared/nfs/rpi4-rootfs/usr/local/bin/visiond

# 3. Power on the RPi4 (no SD card inserted)
#    EEPROM → TFTP firmware → U-Boot → TFTP kernel → NFS rootfs
```

### Production mode (SD card, standalone)

Self-contained boot from SD card. No network dependency.

```bash
# 1. Cross-compile visiond
./lab docker exec -- bash -c "cd projects/vision-edge && make BOARD=rpi4 -j\$(nproc)"

# 2. Copy binary to Buildroot overlay
cp projects/vision-edge/build/rpi4/vision-edge \
   projects/vision-edge/buildroot/overlay/usr/local/bin/visiond
aarch64-linux-gnu-strip projects/vision-edge/buildroot/overlay/usr/local/bin/visiond

# 3. Build SquashFS rootfs image
./lab docker exec -- bash -c "
  export FORCE_UNSAFE_CONFIGURE=1
  cd shared/buildroot/buildroot
  make BR2_EXTERNAL=/workspace/projects/vision-edge/buildroot visiond_rpi4_defconfig
  make -j\$(nproc)
"

# 4. Flash SD card (insert SD card into host)
make -C shared/boot deploy-sd BOARD=rpi4 MODE=prod
```

The SD card now contains:
- **Partition 1 (FAT32):** GPU firmware, U-Boot, boot.scr, kernel Image
- **Partition 2 (SquashFS):** Read-only rootfs with visiond (2.8 MB)

Insert the SD card into the RPi4 and power on.

---

## 3. Boot modes

U-Boot auto-detects the boot mode at startup:

| Condition | Mode | Kernel source | Root filesystem |
|---|---|---|---|
| SD card with partition 2 | **Production** | SD card | SquashFS (read-only) |
| No SD card | **Development** | TFTP (Docker) | NFS (Docker) |

No manual configuration needed — `boot.scr` handles the detection.

---

## 4. Access the dashboard

The dashboard is a standalone HTML file at `projects/vision-edge/web/dashboard.html`.

### Option A: Open directly in browser

Open `web/dashboard.html` in any browser. Edit the `host` variable at the top of the `<script>` block to point to your RPi4's IP:

```
var host = '192.168.1.150:8080';
```

### Option B: Serve locally

```bash
cd projects/vision-edge/web
python3 -m http.server 3000
# Open http://localhost:3000/dashboard.html
```

The dashboard connects to visiond's API endpoints:

| Endpoint | Protocol | Data |
|---|---|---|
| `/stream.mjpg` | HTTP (MJPEG) | Live camera video stream |
| `/ws/telemetry` | WebSocket | JSON metrics (CPU, memory, safety state) |
| `/` | HTTP GET | JSON API descriptor |

---

## 5. API reference

### `GET /`

Returns a JSON descriptor of available endpoints.

```json
{"name": "visiond", "version": "0.5.0", "endpoints": ["/stream.mjpg", "/ws/telemetry"]}
```

### `GET /stream.mjpg`

MJPEG video stream. Use in an `<img>` tag:

```html
<img src="http://192.168.1.150:8080/stream.mjpg" alt="Camera Stream">
```

### `WebSocket /ws/telemetry`

Real-time JSON metrics pushed at heartbeat interval (1 Hz):

```json
{
  "cpu": 12.5,
  "mem_pct": 34.2,
  "anomaly": 0,
  "armed": true,
  "tripped": false,
  "trips": 0
}
```

---

## 6. Runtime behavior

### Development mode

```bash
# SSH into the RPi4
./lab ssh --board=rpi4

# Run visiond manually
/usr/local/bin/visiond

# Or with options
/usr/local/bin/visiond --log-level debug --port 8080
```

Stop with `Ctrl+C` (SIGINT) or `kill <pid>` (SIGTERM). visiond handles both signals for clean shutdown.

### Production mode

visiond starts automatically via `/etc/init.d/S99visiond` on boot. Manage it with:

```bash
/etc/init.d/S99visiond stop
/etc/init.d/S99visiond start
/etc/init.d/S99visiond restart
```

Logs go to stdout (serial console). The rootfs is read-only — `/tmp`, `/var`, `/run` are RAM-backed tmpfs.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Dashboard shows "Connecting" | visiond not running or wrong IP | Verify visiond is running, check IP/port |
| No video stream | Camera not connected or V4L2 driver missing | Check `ls /dev/video*`, verify camera module |
| Boot hangs at U-Boot | TFTP server not running (dev mode) | Start Docker: `./lab docker run` |
| `fsck` errors on boot | Writable rootfs was corrupted | Use production mode (SquashFS, read-only) |
| Binary not found on NFS | Forgot to copy to NFS rootfs | `cp build/rpi4/vision-edge shared/nfs/rpi4-rootfs/usr/local/bin/visiond` |

---

## 8. Project structure

```
projects/vision-edge/
├── docs/
│   ├── user_guide.md              ← this file
│   ├── design/
│   │   └── architecture.md        ← software architecture spec
│   └── phases/                    ← implementation guides (Phases 1-5)
├── include/visiond/               ← C++ headers
├── src/                           ← C++ sources
├── web/
│   └── dashboard.html             ← standalone web dashboard
├── buildroot/
│   ├── configs/visiond_rpi4_defconfig
│   ├── overlay/                   ← rootfs overlay (init script, fstab, binary)
│   └── package/visiond/           ← Buildroot package definition
├── kernel/                        ← vision_safety kernel module (Phase 3)
└── Makefile
```
