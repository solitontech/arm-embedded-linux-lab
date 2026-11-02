# Phase 1: Foundation & Daemon Bringup

> **Goal:** Wire the shared library (`labkit::`), build the first subsystem (`telemetry/`), and the daemon orchestrator (`app/`). Cross-compile inside Docker and deploy to the live RPi4 over NFS.  
> **Modules Built:** `telemetry/*`, `app/*` (core interfaces come from `labkit::`)  
> **Interfaces Introduced:** `ISubsystem`, `ILogger`, `IMetricsSource`, `EventBus`, `expected<T,E>`  
> **Shared Library:** `shared/lib/include/labkit/` (types, logger, lifecycle, event, metrics, expected)  
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

This phase wires the shared `labkit::` library and implements two project modules:

| Source | Header | Source | Purpose |
|---|---|---|---|
| `labkit` | `shared/lib/include/labkit/types.hpp` | -- | `ErrorCode`, `Error` |
| `labkit` | `shared/lib/include/labkit/expected.hpp` | -- | `expected<T,E>` via `tl::expected` / `std::expected` |
| `labkit` | `shared/lib/include/labkit/logger.hpp` | -- | `ILogger` interface, `LogLevel` (header-only) |
| `labkit` | `shared/lib/include/labkit/spdlog_logger.hpp` | -- | `SpdlogLogger` concrete implementation (header-only) |
| `labkit` | `shared/lib/include/labkit/lifecycle.hpp` | -- | `ISubsystem`, `SubsystemState` (header-only) |
| `labkit` | `shared/lib/include/labkit/event.hpp` | -- | `EventBus` typed pub/sub (header-only) |
| `labkit` | `shared/lib/include/labkit/metrics.hpp` | -- | `SystemMetrics`, `IMetricsSource` (header-only) |
| `app` | `include/visiond/app/config.hpp` | `src/app/config.cpp` | `DaemonConfig` (CLI parsing) |
| `app` | `include/visiond/app/daemon.hpp` | `src/app/daemon.cpp` | `DaemonOrchestrator` |
| `telemetry` | `include/visiond/telemetry/metrics.hpp` | `src/telemetry/metrics_procfs.cpp` | `ProcfsMetricsSource` (uses `labkit::IMetricsSource`) |
| `telemetry` | `include/visiond/telemetry/heartbeat.hpp` | `src/telemetry/heartbeat.cpp` | `HeartbeatWorker` (periodic `ISubsystem`) |
| -- | -- | `src/main.cpp` | Composition root |

---

## 3. Build Steps

### Step 1: Create the directory scaffold

```
projects/vision-edge/
├── include/visiond/
│   ├── app/
│   └── telemetry/
├── src/
│   ├── app/
│   └── telemetry/
├── tests/
│   ├── unit/
│   └── integration/
├── design/
│   └── architecture.md
└── phases/
```

> **Note:** `platform/` and `pipeline/` directories are created later in Phase 2. Empty placeholder directories are not used -- directories appear only when they contain code. Core interfaces (`ILogger`, `ISubsystem`, `EventBus`, etc.) live in the shared library at `shared/lib/include/labkit/` and are consumed via `#include <labkit/...>`.

### Step 2: `labkit/types.hpp` + `labkit/expected.hpp` — Error type and `expected`

These are vocabulary headers every other file depends on. They live in the shared library (`shared/lib/include/labkit/`) and provide:
- `Error` struct (error code + context string)
- `expected<T, Error>` alias that forwards to `std::expected` on C++23 or falls back to `tl::expected` (vendored at `shared/lib/vendor/tl/expected.hpp`)

```cpp
// shared/lib/include/labkit/types.hpp
#pragma once
#include <cstdint>
#include <string>

namespace labkit {

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

} // namespace labkit
```

```cpp
// shared/lib/include/labkit/expected.hpp
#pragma once
#include <labkit/types.hpp>

#if __cpp_lib_expected >= 202211L
    #include <expected>
    namespace labkit {
        template <typename T, typename E = Error>
        using expected = std::expected<T, E>;
        using std::unexpected;
    }
#else
    #include <tl/expected.hpp>
    namespace labkit {
        template <typename T, typename E = Error>
        using expected = tl::expected<T, E>;
        using tl::unexpected;
    }
#endif
```

### Step 3: `labkit/logger.hpp` — `ILogger` interface + `SpdlogLogger`

Every component receives an `ILogger&` via constructor -- no singletons. The interface is a lightweight header-only abstract class in `labkit::`. The concrete implementation (`SpdlogLogger`) is in a separate heavy header, included only in the composition root (`main.cpp`).

```cpp
// shared/lib/include/labkit/logger.hpp  (lightweight — safe to include everywhere)
#pragma once
#include <string_view>

namespace labkit {

enum class LogLevel { DEBUG, INFO, WARN, ERROR };

class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(LogLevel level, std::string_view msg) = 0;
    virtual void set_level(LogLevel level) = 0;
};

} // namespace labkit
```

The concrete `labkit::SpdlogLogger` lives in `shared/lib/include/labkit/spdlog_logger.hpp` (header-only, backed by vendored spdlog at `shared/lib/vendor/spdlog/`). It provides:
- Thread-safe colored console output via spdlog
- ISO 8601 timestamps with millisecond precision
- Optional file sink via `add_file_sink(path)`
- Only `main.cpp` includes this heavy header; all other code depends on `ILogger&`

### Step 4: `labkit/lifecycle.hpp` — `ISubsystem` contract

```cpp
// shared/lib/include/labkit/lifecycle.hpp
#pragma once
#include <labkit/expected.hpp>
#include <string_view>

namespace labkit {

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

} // namespace labkit
```

### Step 5: Implement `app/config.hpp` + `src/app/config.cpp` — CLI parsing

`DaemonConfig` is project-specific (not shared) and lives under `app/`. It holds all runtime configuration with layered resolution: compiled defaults -> CLI args. (Config file support can be added later.)

```cpp
// include/visiond/app/config.hpp
#pragma once
#include <labkit/logger.hpp>
#include <cstdint>
#include <string>

namespace visiond {
using labkit::LogLevel;

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

### Step 6: `labkit/event.hpp` — Typed EventBus (header-only)

A lightweight publish/subscribe dispatcher for control events (safety trips, metrics broadcasts, state changes). Not used for frame data. This is fully header-only in `labkit::` -- there is no corresponding `.cpp` file.

```cpp
// shared/lib/include/labkit/event.hpp
#pragma once
#include <any>
#include <functional>
#include <mutex>
#include <typeindex>
#include <unordered_map>
#include <vector>

namespace labkit {

class EventBus {
public:
    template <typename EventT>
    void subscribe(std::function<void(const EventT&)> handler) {
        std::lock_guard<std::mutex> lock(mtx_);
        auto key = std::type_index(typeid(EventT));
        handlers_[key].emplace_back(
            [h = std::move(handler)](const std::any& a) {
                h(std::any_cast<const EventT&>(a));
            });
    }

    template <typename EventT>
    void publish(const EventT& event) {
        std::vector<std::function<void(const std::any&)>> snapshot;
        {
            std::lock_guard<std::mutex> lock(mtx_);
            auto it = handlers_.find(std::type_index(typeid(EventT)));
            if (it == handlers_.end()) return;
            snapshot = it->second;
        }
        std::any wrapped = event;
        for (auto& fn : snapshot) fn(wrapped);
    }

private:
    std::mutex mtx_;
    std::unordered_map<std::type_index,
                       std::vector<std::function<void(const std::any&)>>> handlers_;
};

} // namespace labkit
```

### Step 7: Implement `telemetry/metrics.hpp` + `src/telemetry/metrics_procfs.cpp`

The metrics data structure and `IMetricsSource` interface live in `labkit::`. The project header re-exports them and adds the concrete `ProcfsMetricsSource` implementation.

```cpp
// include/visiond/telemetry/metrics.hpp
#pragma once
#include <labkit/metrics.hpp>
#include <labkit/logger.hpp>

namespace visiond {
using labkit::SystemMetrics;
using labkit::IMetricsSource;
using labkit::ILogger;

// Real implementation: parses /proc/stat, /proc/meminfo, /proc/uptime
class ProcfsMetricsSource : public IMetricsSource {
public:
    explicit ProcfsMetricsSource(ILogger& logger);
    SystemMetrics sample() override;

private:
    ILogger& logger_;
    uint64_t prev_idle_{0};
    uint64_t prev_total_{0};
    bool first_sample_{true};
};

} // namespace visiond
```

### Step 8: Implement `telemetry/heartbeat.hpp` + `src/telemetry/heartbeat.cpp`

`HeartbeatWorker` is the first `ISubsystem`. It periodically calls `IMetricsSource::sample()` and publishes a `MetricsEvent` via `EventBus`. It does NOT format or log — that's the subscriber's job.

```cpp
// include/visiond/telemetry/heartbeat.hpp
#pragma once
#include <labkit/lifecycle.hpp>
#include <labkit/event.hpp>
#include "visiond/telemetry/metrics.hpp"
#include <atomic>
#include <condition_variable>
#include <mutex>
#include <thread>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;
using labkit::LogLevel;
using labkit::ILogger;
using labkit::SubsystemState;
using labkit::ISubsystem;
using labkit::EventBus;

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

Note how `using` declarations bring `labkit::` types into the `visiond` namespace. This pattern keeps project code concise while making the shared library origin explicit at the top of each header.

### Step 9: Implement `app/daemon.hpp` + `src/app/daemon.cpp` — DaemonOrchestrator

Owns all subsystems. Handles ordered `init()` → `start()`, reverse-ordered `stop()`, POSIX signal handling, and the main wait loop.

```cpp
// include/visiond/app/daemon.hpp
#pragma once
#include <labkit/lifecycle.hpp>
#include <labkit/logger.hpp>
#include "visiond/app/config.hpp"
#include <memory>
#include <vector>

namespace visiond {
using labkit::ILogger;
using labkit::ISubsystem;
using labkit::SubsystemState;
using labkit::LogLevel;

class DaemonOrchestrator {
public:
    DaemonOrchestrator(ILogger& logger, const DaemonConfig& config);

    void add(std::unique_ptr<ISubsystem> subsystem);

    // init all -> start all -> wait for signal -> stop all (reverse order)
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

### Step 10: Implement `src/main.cpp` — Composition root

This is the only file that includes the heavy `<labkit/spdlog_logger.hpp>` header. Everything else depends on `ILogger&`.

```cpp
#include "visiond/app/config.hpp"
#include "visiond/telemetry/metrics.hpp"
#include "visiond/telemetry/heartbeat.hpp"
#include "visiond/app/daemon.hpp"
#include <labkit/spdlog_logger.hpp>   // heavy -- only in composition root
#include <iomanip>
#include <iostream>
#include <sstream>

int main(int argc, char* argv[]) {
    auto config = visiond::DaemonConfig::parse(argc, argv);
    if (config.show_help)    { visiond::DaemonConfig::print_usage(argv[0]); return 0; }
    if (config.show_version) { std::cout << "visiond 0.1.0\n"; return 0; }

    // Composition root: create shared dependencies
    labkit::SpdlogLogger logger("visiond");
    logger.set_level(config.log_level);
    if (!config.log_file.empty())
        logger.add_file_sink(config.log_file);

    labkit::EventBus event_bus;
    visiond::ProcfsMetricsSource metrics_source(logger);

    // Subscribe to MetricsEvents for logging (temporary -- replaced by WebServer in Phase 5)
    event_bus.subscribe<visiond::MetricsEvent>(
        [&logger](const visiond::MetricsEvent& e) {
            std::ostringstream ss;
            ss << std::fixed << std::setprecision(1)
               << "[event] MetricsEvent: CPU " << e.metrics.cpu_usage_percent
               << "%, Mem " << (e.metrics.mem_available_kb / 1024)
               << "/" << (e.metrics.mem_total_kb / 1024) << " MB";
            logger.log(labkit::LogLevel::DEBUG, ss.str());
        });

    // Build orchestrator and register subsystems
    visiond::DaemonOrchestrator daemon(logger, config);
    daemon.add(std::make_unique<visiond::HeartbeatWorker>(
        logger, metrics_source, event_bus, config.heartbeat_interval_ms));

    return daemon.run();
}
```

### Step 11: Update Makefile

```makefile
PROJECT_NAME    := vision-edge
PROJECT_TYPE    := app
DEFAULT_BOARD   := rpi4

CXXFLAGS_EXTRA  += -std=c++20 -O2 -Wall -Wextra
INCLUDES_EXTRA  += -I./include
LDFLAGS_EXTRA   += -static
LDLIBS_EXTRA    += -pthread

include ../../shared/build_system/framework.mk
```

The build framework handles recursive source discovery automatically -- no overrides needed.

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
- [ ] No singletons -- every component receives deps via constructor (`ILogger&`, `EventBus&`, etc.)
