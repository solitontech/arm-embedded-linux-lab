# Phase 1: Foundation & Daemon Bringup

> **Goal:** Build the architectural foundation (`core/`), the first subsystem (`telemetry/`), and the daemon orchestrator (`app/`). Cross-compile inside Docker and deploy to the live RPi4 over NFS.  
> **Modules Built:** `core/*`, `telemetry/*`, `app/`  
> **Interfaces Introduced:** `ISubsystem`, `ILogger`, `IMetricsSource`, `EventBus`, `expected<T,E>`  
> **Architecture Reference:** [design/architecture.md](../design/architecture.md)  
> **Milestone:** Gate 1 (Daemon Bringup)

---

## 1. Prerequisites

Verify the lab infrastructure is active before starting:

```bash
./lab docker status                              # Docker container running
./lab ssh --board=rpi4 "uname -a; free -h"       # RPi4 reachable over NFS
```

---

## 2. Files Created

This phase establishes the directory scaffold and implements three modules:

| Module | Header | Source | Purpose |
|---|---|---|---|
| `core` | `include/visiond/core/types.hpp` | — | `Error` type, `expected<T,E>` polyfill |
| `core` | `include/visiond/core/logger.hpp` | `src/core/logger.cpp` | `ILogger` interface, `ConsoleLogger` |
| `core` | `include/visiond/core/lifecycle.hpp` | — | `ISubsystem` interface, `SubsystemState` |
| `core` | `include/visiond/core/config.hpp` | `src/core/config.cpp` | `DaemonConfig` (CLI parsing) |
| `core` | `include/visiond/core/event.hpp` | `src/core/event.cpp` | `EventBus` (typed pub/sub) |
| `telemetry` | `include/visiond/telemetry/metrics.hpp` | `src/telemetry/metrics_procfs.cpp` | `IMetricsSource`, `ProcfsMetricsSource` |
| `telemetry` | `include/visiond/telemetry/heartbeat.hpp` | `src/telemetry/heartbeat.cpp` | `HeartbeatWorker` (periodic `ISubsystem`) |
| `app` | `include/visiond/app/daemon.hpp` | `src/app/daemon.cpp` | `DaemonOrchestrator` |
| — | — | `src/main.cpp` | Minimal entry point |

---

## 3. Build Steps

### Step 1: Create the directory scaffold

```
projects/vision-edge/
├── include/visiond/
│   ├── core/
│   ├── platform/        # empty — Phase 2
│   ├── pipeline/        # empty — Phase 2
│   ├── safety/          # empty — Phase 3
│   ├── telemetry/
│   ├── web/             # empty — Phase 5
│   └── app/
├── src/
│   ├── core/
│   ├── platform/        # empty — Phase 2
│   ├── pipeline/        # empty — Phase 2
│   ├── safety/          # empty — Phase 3
│   ├── telemetry/
│   ├── web/             # empty — Phase 5
│   └── app/
├── kernel/              # empty — Phase 3
├── tests/
│   ├── unit/
│   └── integration/
├── design/
│   └── architecture.md
└── phases/
```

### Step 2: Implement `core/types.hpp` — Error type and `expected` polyfill

This is the vocabulary header every other file depends on. It provides:
- `Error` struct (error code + context string)
- `expected<T, Error>` alias that forwards to `std::expected` on C++23 or falls back to a minimal polyfill on GCC 11

```cpp
// include/visiond/core/types.hpp
#pragma once
#include <cstdint>
#include <string>

namespace visiond {

enum class ErrorCode : uint16_t {
    OK = 0,
    INVALID_ARG,
    IO_ERROR,
    DEVICE_NOT_FOUND,
    PERMISSION_DENIED,
    ALREADY_RUNNING,
    NOT_INITIALIZED,
    TIMEOUT,
};

struct Error {
    ErrorCode   code;
    std::string context;
};

// --- expected<T, E> polyfill ---
#if __cpp_lib_expected >= 202211L
    #include <expected>
    template <typename T, typename E = Error>
    using expected = std::expected<T, E>;
    using std::unexpected;
#else
    // Provide a minimal polyfill (~80 lines):
    // - Discriminated union with has_value(), value(), error()
    // - Move-constructible, supports void specialization
    // See architecture doc §3.1 for design rationale
    template <typename E> class unexpected { /* ... */ };
    template <typename T, typename E = Error> class expected { /* ... */ };
#endif

} // namespace visiond
```

### Step 3: Implement `core/logger.hpp` — `ILogger` interface + `ConsoleLogger`

Every component receives an `ILogger&` via constructor — no singletons.

```cpp
// include/visiond/core/logger.hpp
#pragma once
#include <string_view>

namespace visiond {

enum class LogLevel { DEBUG, INFO, WARN, ERROR };

class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(LogLevel level, std::string_view msg) = 0;
    virtual void set_level(LogLevel level) = 0;
};

// Default implementation: ANSI-colored output to stdout, optional file output
class ConsoleLogger : public ILogger {
public:
    void log(LogLevel level, std::string_view msg) override;
    void set_level(LogLevel level) override;
    bool set_log_file(const std::string& path);

private:
    LogLevel current_level_{LogLevel::INFO};
    std::mutex mtx_;
    std::ofstream file_stream_;
};

} // namespace visiond
```

The `ConsoleLogger` implementation in `src/core/logger.cpp` handles:
- Thread-safe mutex-guarded output
- ISO 8601 timestamps with millisecond precision
- ANSI color codes per log level (cyan/green/yellow/red)
- Optional file logging (plaintext, no ANSI codes)

### Step 4: Implement `core/lifecycle.hpp` — `ISubsystem` contract

```cpp
// include/visiond/core/lifecycle.hpp
#pragma once
#include "visiond/core/types.hpp"
#include <string_view>

namespace visiond {

enum class SubsystemState { CREATED, INITIALIZED, RUNNING, STOPPED, FAILED };

class ISubsystem {
public:
    virtual ~ISubsystem() = default;
    virtual expected<void, Error> init()  = 0;
    virtual expected<void, Error> start() = 0;
    virtual void                  stop()  = 0;
    virtual std::string_view  name()  const = 0;
    virtual SubsystemState    state() const = 0;
};

} // namespace visiond
```

### Step 5: Implement `core/config.hpp` + `src/core/config.cpp` — CLI parsing

`DaemonConfig` holds all runtime configuration with layered resolution: compiled defaults → CLI args. (Config file support can be added later.)

```cpp
// include/visiond/core/config.hpp
#pragma once
#include "visiond/core/logger.hpp"
#include <string>

namespace visiond {

struct DaemonConfig {
    LogLevel    log_level{LogLevel::INFO};
    uint32_t    heartbeat_interval_ms{1000};
    uint16_t    web_port{8080};
    std::string log_file;
    bool        daemon_mode{false};
    bool        show_version{false};
    bool        show_help{false};

    static DaemonConfig parse(int argc, char* argv[]);
    static void print_usage(const char* prog_name);
};

} // namespace visiond
```

CLI flags: `-h/--help`, `-v/--version`, `-d/--daemon`, `-i/--interval <ms>`, `-p/--port <port>`, `-l/--log-level <level>`, `-f/--log-file <path>`.

### Step 6: Implement `core/event.hpp` + `src/core/event.cpp` — Typed EventBus

A lightweight publish/subscribe dispatcher for control events (safety trips, metrics broadcasts, state changes). Not used for frame data.

```cpp
// include/visiond/core/event.hpp
#pragma once
#include <any>
#include <functional>
#include <mutex>
#include <typeindex>
#include <unordered_map>
#include <vector>

namespace visiond {

class EventBus {
public:
    template <typename EventT>
    void subscribe(std::function<void(const EventT&)> handler);

    template <typename EventT>
    void publish(const EventT& event);

private:
    std::mutex mtx_;
    std::unordered_map<std::type_index,
                       std::vector<std::function<void(const std::any&)>>> handlers_;
};

} // namespace visiond
```

### Step 7: Implement `telemetry/metrics.hpp` + `src/telemetry/metrics_procfs.cpp`

Separate the metrics data structure from the collection strategy via `IMetricsSource`.

```cpp
// include/visiond/telemetry/metrics.hpp
#pragma once
#include "visiond/core/logger.hpp"
#include <cstdint>

namespace visiond {

struct SystemMetrics {
    float    cpu_usage_percent{0.0f};
    double   uptime_seconds{0.0};
    uint64_t mem_total_kb{0};
    uint64_t mem_free_kb{0};
    uint64_t mem_available_kb{0};
};

class IMetricsSource {
public:
    virtual ~IMetricsSource() = default;
    virtual SystemMetrics sample() = 0;
};

// Real implementation: parses /proc/stat, /proc/meminfo, /proc/uptime
class ProcfsMetricsSource : public IMetricsSource {
public:
    explicit ProcfsMetricsSource(ILogger& logger);
    SystemMetrics sample() override;

private:
    ILogger& logger_;
    // CPU delta tracking state
    uint64_t prev_idle_{0}, prev_total_{0};
    bool first_sample_{true};
};

} // namespace visiond
```

### Step 8: Implement `telemetry/heartbeat.hpp` + `src/telemetry/heartbeat.cpp`

`HeartbeatWorker` is the first `ISubsystem`. It periodically calls `IMetricsSource::sample()` and publishes a `MetricsEvent` via `EventBus`. It does NOT format or log — that's the subscriber's job.

```cpp
// include/visiond/telemetry/heartbeat.hpp
#pragma once
#include "visiond/core/lifecycle.hpp"
#include "visiond/core/event.hpp"
#include "visiond/telemetry/metrics.hpp"
#include <thread>
#include <atomic>
#include <condition_variable>

namespace visiond {

struct MetricsEvent {
    SystemMetrics metrics;
};

class HeartbeatWorker : public ISubsystem {
public:
    HeartbeatWorker(ILogger& logger, IMetricsSource& source,
                    EventBus& bus, uint32_t interval_ms);
    ~HeartbeatWorker() override;

    expected<void, Error> init()  override;
    expected<void, Error> start() override;
    void                  stop()  override;
    std::string_view  name()  const override { return "heartbeat"; }
    SubsystemState    state() const override { return state_; }

private:
    void worker_loop();

    ILogger&        logger_;
    IMetricsSource& source_;
    EventBus&       bus_;
    uint32_t        interval_ms_;
    SubsystemState  state_{SubsystemState::CREATED};
    std::atomic<bool> running_{false};
    std::thread       thread_;
    std::condition_variable cv_;
    std::mutex              cv_mtx_;
};

} // namespace visiond
```

### Step 9: Implement `app/daemon.hpp` + `src/app/daemon.cpp` — DaemonOrchestrator

Owns all subsystems. Handles ordered `init()` → `start()`, reverse-ordered `stop()`, POSIX signal handling, and the main wait loop.

```cpp
// include/visiond/app/daemon.hpp
#pragma once
#include "visiond/core/lifecycle.hpp"
#include "visiond/core/logger.hpp"
#include "visiond/core/config.hpp"
#include <memory>
#include <vector>

namespace visiond {

class DaemonOrchestrator {
public:
    DaemonOrchestrator(ILogger& logger, const DaemonConfig& config);

    void add(std::unique_ptr<ISubsystem> subsystem);

    // init all → start all → wait for signal → stop all (reverse order)
    int run();

private:
    void setup_signal_handlers();
    void wait_for_shutdown();

    ILogger& logger_;
    DaemonConfig config_;
    std::vector<std::unique_ptr<ISubsystem>> subsystems_;
};

} // namespace visiond
```

### Step 10: Implement `src/main.cpp` — Minimal entry point

```cpp
#include "visiond/core/config.hpp"
#include "visiond/core/logger.hpp"
#include "visiond/core/event.hpp"
#include "visiond/telemetry/metrics.hpp"
#include "visiond/telemetry/heartbeat.hpp"
#include "visiond/app/daemon.hpp"
#include <iostream>

int main(int argc, char* argv[]) {
    auto config = visiond::DaemonConfig::parse(argc, argv);
    if (config.show_help)    { visiond::DaemonConfig::print_usage(argv[0]); return 0; }
    if (config.show_version) { std::cout << "visiond 0.1.0\n"; return 0; }

    // Composition root: create shared dependencies
    visiond::ConsoleLogger logger;
    logger.set_level(config.log_level);

    visiond::EventBus event_bus;
    visiond::ProcfsMetricsSource metrics_source(logger);

    // Build orchestrator and register subsystems
    visiond::DaemonOrchestrator daemon(logger, config);
    daemon.add(std::make_unique<visiond::HeartbeatWorker>(
        logger, metrics_source, event_bus, config.heartbeat_interval_ms));

    // Subscribe to MetricsEvents for logging (temporary — replaced by WebServer in Phase 5)
    event_bus.subscribe<visiond::MetricsEvent>([&logger](const visiond::MetricsEvent& e) {
        // format and log metrics
    });

    return daemon.run();
}
```

### Step 11: Update Makefile for recursive source discovery

```makefile
PROJECT_NAME    := vision-edge
PROJECT_TYPE    := app
DEFAULT_BOARD   := rpi4

CXXFLAGS_EXTRA  += -std=c++20 -O2 -Wall -Wextra
INCLUDES_EXTRA  += -I./include
LDFLAGS_EXTRA   += -static
LDLIBS_EXTRA    += -pthread

# Override flat SRCS glob with recursive discovery
SRCS_OVERRIDE   := $(shell find src -name '*.cpp')

include ../../shared/build_system/framework.mk
```

> **Note:** `framework.mk` may need a small patch to respect `SRCS_OVERRIDE`. Check `shared/build_system/easymake_base.mk` for where `SRCS` is defined and add a conditional.

### Step 12: Build and deploy

```bash
# Cross-compile inside Docker
./lab docker exec -- ./lab build vision-edge --board rpi4

# Deploy to RPi4 NFS rootfs
./lab docker exec -- ./lab deploy vision-edge --board rpi4

# Run on target
./lab docker exec -- ./lab run vision-edge --board rpi4
```

---

## 4. Exploration Exercises

These are optional deep-dives for building platform understanding. They don't produce code that ships — they build your mental model.

### Exercise 1: ELF Binary Inspection

After cross-compilation, inspect the binary:

```bash
aarch64-linux-gnu-readelf -h build/rpi4/vision-edge   # Verify AArch64
aarch64-linux-gnu-readelf -S build/rpi4/vision-edge   # Section headers
aarch64-linux-gnu-objdump -d build/rpi4/vision-edge | head -100  # Disassembly
```

**What to observe:** Machine type is AArch64, `.text` section contains ARM64 instructions, `-O2` enables branch optimization and loop unrolling.

### Exercise 2: ARM64 Calling Convention

Compile a simple function with `-O0` and `-O2`, then compare the assembly:

```bash
aarch64-linux-gnu-g++ -S -O0 -o /tmp/func_O0.s test_func.cpp
aarch64-linux-gnu-g++ -S -O2 -o /tmp/func_O2.s test_func.cpp
diff /tmp/func_O0.s /tmp/func_O2.s
```

**What to observe:** Arguments in `x0-x7`, return value in `x0`, link register in `x30`, stack pointer in `sp`. `-O2` eliminates redundant loads/stores.

---

## 5. Verification Gate

- [ ] Binary cross-compiles cleanly with `aarch64-linux-gnu-g++ -std=c++20`
- [ ] `readelf -h` confirms Machine: AArch64
- [ ] `visiond --help` prints usage and exits 0
- [ ] `visiond --version` prints version and exits 0
- [ ] Daemon boots on RPi4, logs `INITIALIZING → RUNNING` state transitions
- [ ] HeartbeatWorker publishes `MetricsEvent` every N ms (default 1000)
- [ ] Metrics log shows CPU%, memory, and uptime (not zeros)
- [ ] `Ctrl+C` (SIGINT) triggers clean shutdown: `STOPPING → TERMINATED`, all threads joined, exit 0
- [ ] `kill -TERM <pid>` also triggers clean shutdown
- [ ] No singletons anywhere — every component receives deps via constructor
