---
description: how to add or modify components in the shared labkit C++ library
---

# Shared C++ Library (`labkit::`)

## When to Use This Workflow

Use this workflow whenever you need to:
- Add a new reusable C++ component (interface, utility, type) to the monorepo
- Vendor a new third-party header-only library
- Update an existing `labkit::` component
- Determine whether code belongs in shared or in a project

## Decision: Shared vs Project-Local?

**Put it in `shared/lib/include/labkit/` if:**
- Two or more projects could use it (or one project uses it and it's clearly generic)
- It's an abstract interface, vocabulary type, or generic utility
- It has no project-specific or hardware-specific dependencies

**Keep it in the project if:**
- It's a concrete implementation tied to specific hardware (e.g., `/proc` parser, GPIO driver)
- It's application-specific configuration or orchestration
- It depends on project-specific types

## Directory Layout

```
shared/lib/
├── vendor/                          # Third-party headers (committed, version-pinned)
│   ├── README.md                    # Provenance: versions, licenses, sources
│   ├── spdlog/                      # spdlog v1.14.1 (header-only, includes bundled fmt)
│   └── tl/
│       └── expected.hpp             # tl::expected v1.1.0
│
└── include/labkit/                  # Shared monorepo foundation library
    ├── types.hpp                    # ErrorCode, Error
    ├── expected.hpp                 # tl::expected / std::expected wrapper
    ├── logger.hpp                   # ILogger interface + SpdlogLogger
    ├── term.hpp                     # Terminal formatting: banner, section, separator, kv, status
    ├── event.hpp                    # EventBus (typed pub/sub)
    ├── lifecycle.hpp                # ISubsystem interface, SubsystemState
    └── metrics.hpp                  # SystemMetrics struct + IMetricsSource interface
```

## Steps

### 1. Adding a New labkit Header

Create the header in `shared/lib/include/labkit/`:

```cpp
#pragma once
// Keep headers self-contained — include all dependencies.

namespace labkit {
    // Your interface, type, or utility here.
}
```

**Guidelines:**
- Header-only preferred (inline implementations). Use `.cpp` files only when compile time is a concern.
- Include guards via `#pragma once`.
- Everything in `namespace labkit {}`.
- No project-specific dependencies.

### 2. Consuming labkit from a Project

Create a **forwarding header** in the project so internal includes stay unchanged:

```cpp
// projects/<name>/include/<ns>/core/my_component.hpp
#pragma once
#include <labkit/my_component.hpp>

namespace my_project_ns {
    using labkit::MyInterface;
    using labkit::MyType;
}
```

This ensures:
- Existing project code (`#include "my_ns/core/my_component.hpp"`) keeps working
- The shared implementation is the single source of truth
- Project namespace (`visiond::`, etc.) stays consistent for downstream files

### 3. Vendoring a Third-Party Library

1. **Check it's header-only** and works with GCC 11 / aarch64 cross-compilation
2. **Pin to a specific release** at least 7 days old (supply-chain safety)
3. Download and extract to `shared/lib/vendor/<library_name>/`
4. **Update `shared/lib/vendor/README.md`** with version, license, and source URL
5. Include via `<library_name/header.h>` — the vendor path is on the compiler include path via `framework.mk`

### 4. Build System

`framework.mk` automatically adds both paths to all projects:

```makefile
-I$(REPO_ROOT)/shared/lib/include    # for labkit/ headers
-I$(REPO_ROOT)/shared/lib/vendor     # for vendored third-party headers
```

No per-project Makefile changes are needed.

### 5. Verify

```bash
# Cross-compile all projects that use the changed component
./lab docker exec -- make -C projects/<name> BOARD=rpi4 clean all

# Verify AArch64 binary
./lab docker exec -- aarch64-linux-gnu-readelf -h projects/<name>/build/rpi4/<binary> | grep Machine
```

## Files Touched

- `[CREATE/MODIFY]` `shared/lib/include/labkit/<component>.hpp`
- `[CREATE/MODIFY]` `shared/lib/vendor/<lib>/` (if vendoring)
- `[MODIFY]` `shared/lib/vendor/README.md` (if vendoring)
- `[CREATE/MODIFY]` `projects/<name>/include/<ns>/core/<forwarding_header>.hpp`
- `[MODIFY]` `shared/build_system/framework.mk` (only if new include paths needed)

## Current labkit Components

| Header | Contents | Used By |
|---|---|---|
| `types.hpp` | `ErrorCode`, `Error` | All projects |
| `expected.hpp` | `expected<T,E>`, `unexpected` (wraps tl::expected or std::expected) | All projects |
| `logger.hpp` | `ILogger`, `LogLevel` (lightweight — no spdlog) | All projects |
| `spdlog_logger.hpp` | `SpdlogLogger` (heavy — include only in `main.cpp`) | Composition roots only |
| `term.hpp` | `banner()`, `section()`, `separator()`, `kv()`, `status_ok/fail()`, `colored()` | All projects |
| `event.hpp` | `EventBus` (typed pub/sub) | Event-driven projects |
| `lifecycle.hpp` | `ISubsystem`, `SubsystemState` | Daemon projects |
| `metrics.hpp` | `SystemMetrics`, `IMetricsSource` | Telemetry projects |
