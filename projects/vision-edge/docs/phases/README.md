# VisionEdge: Implementation Roadmap

> **Target Platform:** Raspberry Pi 4 Model B (BCM2711 / Quad-Core Cortex-A72 / AArch64)  
> **Development Environment:** Docker Container (`arm-lab-dev`) via `./lab` CLI  
> **Target Access:** SD-Free Network Boot (U-Boot TFTP + NFS RootFS + Dropbear SSH)  
> **Architecture Reference:** [design/architecture.md](../design/architecture.md)

---

## 1. Monorepo Infrastructure Status

| Infrastructure Layer | Status | VisionEdge Role |
|---|---|---|
| **Toolchain & Container** | **Ready** | Dockerized `aarch64-linux-gnu-g++` (C++20) cross-compiles `visiond` and kernel modules |
| **Board Bootloader** | **Ready** | U-Boot 2024.07 AArch64 via TFTP + PXE boot |
| **Linux Kernel** | **Ready** | 64-bit kernel with V4L2 camera driver support, custom LKM loading |
| **Root Filesystem** | **Ready** | BusyBox NFS rootfs exported from Docker at `/workspace/nfs/rpi4-rootfs/` |
| **Device Communication** | **Ready** | Dropbear SSH (`./lab ssh`), Serial UART (`./lab console`), GDB (`./lab gdb`) |
| **Build & Deploy CLI** | **Ready** | `./lab build`, `./lab deploy`, `./lab run` |

---

## 2. System Architecture

See [design/architecture.md](../design/architecture.md) for the full specification. Summary:

```mermaid
graph TB
    subgraph Userspace ["Userspace (EL0) — visiond"]
        direction TB
        ORCH["DaemonOrchestrator\n(app/)"]
        PIPE["Zero-Copy Pipeline\n(pipeline/)"]
        SAFETY_U["Safety Client\n(safety/)"]
        TELEM["Heartbeat & Metrics\n(telemetry/)"]
        WEB["Web Dashboard :8080\n(web/)"]

        ORCH --> PIPE
        ORCH --> SAFETY_U
        ORCH --> TELEM
        ORCH --> WEB
    end

    subgraph Kernel ["Kernel Space (EL1)"]
        V4L2["V4L2 / DMA Subsystem"]
        DRIVER["vision_safety Platform Driver\n(/dev/vision_safety)"]
        GIC["GIC-400 Interrupt Controller"]
    end

    subgraph Hardware ["BCM2711 Hardware"]
        CAM["MIPI CSI-2 Camera"]
        GPIO["GPIO Peripherals\n(MMIO 0xFE200000)"]
        RELAY["Safety Interlock\n(Relay + Strobe)"]
    end

    PIPE <-->|"dma-buf zero-copy"| V4L2
    SAFETY_U -->|"ioctl / poll"| DRIVER
    CAM --> V4L2
    DRIVER -->|"iowrite32"| GPIO
    GIC -->|"IRQ"| DRIVER
    GPIO -->|"< 10 µs"| RELAY
```

---

## 3. End-to-End Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant Cam as MIPI Camera
    participant V4L2 as V4L2 / DMA
    participant Ring as LocklessTripleBuffer
    participant SIMD as ISIMDEngine (NEON)
    participant Trip as TripController
    participant Driver as ISafetyDriver
    participant Relay as GPIO Relay
    participant Web as WebServer :8080

    rect rgb(240, 248, 255)
    Note over Cam,Ring: Zero-Copy Ingestion (30-60 FPS)
    Cam->>V4L2: Raw YUV frame
    V4L2->>Ring: DMA into dma-buf slot (0 CPU copies)
    end

    rect rgb(255, 250, 240)
    Note over Ring,SIMD: NEON SIMD Vectorized Inspection
    Ring->>SIMD: Acquire frame pointer (atomic swap)
    SIMD->>Trip: Anomaly count (1.2 ms/frame)
    end

    alt Optical Boundary Breached
        rect rgb(255, 235, 235)
        Note over Trip,Relay: Deterministic Safety Trip
        Trip->>Driver: trip()
        Driver->>Relay: ioctl → top-half ISR → MMIO write (< 10 µs)
        end
    else Normal Flow
        rect rgb(245, 255, 245)
        Note over SIMD,Web: Telemetry & Streaming
        SIMD->>Web: Rendered frame + metrics via EventBus
        end
    end
```

---

## 4. Hardware Wiring (BCM2711 GPIO Pinout)

```
Raspberry Pi 4 40-Pin Header (J8)
Pin 01: 3.3V Power ------------> Logic VDD
Pin 02: 5.0V Power ------------> Relay Module VCC
Pin 06: Ground ----------------> Common GND
Pin 08: GPIO 14 (TXD0) --------> USB-UART RX (Serial Console: 115200 baud)
Pin 10: GPIO 15 (RXD0) --------> USB-UART TX (Serial Console: 115200 baud)
Pin 12: GPIO 18 (PWM0 / OUT) --> Hardware Interlock Relay Signal (Active LOW)
Pin 16: GPIO 23 (IN / IRQ) ----> Optical Safety Trigger Sensor (Falling Edge)
Pin 18: GPIO 24 (OUT) ---------> Emergency Strobe Warning LED
```

---

## 5. Phase-by-Phase Implementation

Each phase builds on the previous one's modules. See the [architecture doc](../design/architecture.md) for the full module map.

| Phase | Focus | Modules Built | Guide |
|---|---|---|---|
| **1** | **Foundation & Daemon Bringup** | `core/*`, `telemetry/*`, `app/` | [Phase 1](phase1_daemon_bringup.md) |
| **2** | **CPU Internals, Memory & GPIO HAL** | `platform/gpio*`, `platform/mmio`, `pipeline/ring_buffer`, `pipeline/frame` | [Phase 2](phase2_cpu_memory_mmio.md) |
| **3** | **Kernel Driver & Safety Subsystem** | `kernel/*`, `safety/*` | [Phase 3](phase3_kernel_safety_driver.md) |
| **4** | **Video Pipeline & NEON SIMD** | `platform/camera*`, `platform/dma`, `pipeline/simd*`, `pipeline/stage` | [Phase 4](phase4_video_dma_neon.md) |
| **5** | **Productization & Instant Boot** | `web/*`, Buildroot configs | [Phase 5](phase5_productization.md) |

### Phase Structure

Each phase document follows the same structure:

1. **Goal & Scope** — what this phase delivers and which architecture modules it builds
2. **Build Steps** — concrete implementation steps with file paths and code snippets (delegatable to AI)
3. **Exploration Exercises** — optional hands-on deep-dives for platform understanding
4. **Verification Gate** — pass/fail checklist

---

## 6. Verification Gates

```mermaid
flowchart TD
    G1["Gate 1: Daemon Bringup\nvisiond boots on RPi4, heartbeat runs,\nclean SIGINT/SIGTERM shutdown"]
    G2["Gate 2: Execution & Memory\nGDB crash analysis, GPIO toggle via /dev/mem,\nlockless buffer at 60 FPS"]
    G3["Gate 3: Platform Driver\n/dev/vision_safety active, DT overlay bound,\ntop-half IRQ < 10 µs"]
    G4["Gate 4: Data-Path & SIMD\nZero-copy dma-buf capture, NEON 1.2 ms/frame,\n24h soak test"]
    G5["Gate 5: Production Appliance\n< 2.5s cold boot, web UI at :8080,\npower-loss immune"]

    G1 --> G2 --> G3 --> G4 --> G5
```
