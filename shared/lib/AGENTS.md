# labkit Shared Library — Coding Rules

These rules apply to every header and source file under `shared/lib/`.
Any agent modifying or adding labkit components **must** follow them.

## 1. Separate Interface from Implementation

**Interface headers are lightweight. Concrete implementations are separate.**

- An interface header (e.g. `logger.hpp`) contains only the abstract class, enums, and vocabulary types. It must **never** include heavy third-party headers like spdlog, fmt, or Boost.
- A concrete implementation header (e.g. `spdlog_logger.hpp`) includes the heavy dependency and provides the class that implements the interface. It is marked with a comment: `// heavy — include only in composition roots (main.cpp)`.
- Only the composition root (`main.cpp`) includes the heavy header to construct the concrete object. All other code depends on the interface via `IFoo&`.

**Why:** Including spdlog in every translation unit costs ~7 seconds each. Separating interface from implementation reduced total build time from ~37s to ~5.7s across 5 files. This scales linearly — at 20 files the difference would be ~144s vs ~10s.

### Example — correct:

```
labkit/logger.hpp           ← ILogger + LogLevel (lightweight, ~15 lines)
labkit/spdlog_logger.hpp    ← SpdlogLogger : ILogger (heavy, includes spdlog)
```

```cpp
// heartbeat.cpp — only needs the interface
#include <labkit/logger.hpp>       // ~174ms compile time
void HeartbeatWorker::init(labkit::ILogger& logger) { ... }

// main.cpp — composition root, constructs the concrete type
#include <labkit/spdlog_logger.hpp> // ~3400ms compile time (paid once)
labkit::SpdlogLogger logger("app");
daemon.run(logger);                 // passed as ILogger&
```

### Example — wrong:

```cpp
// logger.hpp — DO NOT put SpdlogLogger here
#include <spdlog/spdlog.h>  // ← every file that includes logger.hpp pays ~7s
class SpdlogLogger : public ILogger { ... };
```

## 2. Headers Must Be Self-Contained

Every header must compile on its own — include everything you use, never rely on transitive includes from other headers.

```cpp
// CORRECT: config.hpp includes what it needs
#include <cstdint>    // for uint32_t
#include <string>     // for std::string

// WRONG: config.hpp relies on spdlog pulling in <cstdint>
#include "logger.hpp" // happened to bring <cstdint> transitively
```

**Why:** When you clean up transitive includes (like splitting logger.hpp), files that relied on accidental transitive includes break. Self-contained headers prevent this.

## 3. No Project-Specific Dependencies

labkit headers must **never** include project headers (`visiond/`, etc.) or depend on project-specific types. Dependency direction is strictly: `projects → labkit`, never the reverse.

## 4. Namespace

Everything in `namespace labkit {}`. Sub-namespaces are allowed (e.g. `labkit::term`).

## 5. Prefer Header-Only for Small Components

Small interfaces, enums, structs, and template code should be header-only (inline). Split into a separate `.cpp` only when:
- The implementation pulls in a heavy third-party header (spdlog, fmt, etc.)
- The implementation is large and non-template (>100 lines of non-trivial logic)

## 6. Vendored Libraries

Third-party headers live in `shared/lib/vendor/` and are version-pinned.

- **Never** include vendored headers directly from project code. Wrap them in a labkit header (e.g. `labkit/expected.hpp` wraps `tl/expected.hpp`).
- **Never** vendor a library newer than 7 days old.
- **Always** update `shared/lib/vendor/README.md` when adding or updating a vendored library.

## 7. Checklist for Adding a New Component

- [ ] Interface in `labkit/foo.hpp` — lightweight, no heavy includes
- [ ] Concrete impl in `labkit/foo_impl.hpp` (or `.cpp`) — if it needs heavy deps
- [ ] Comment on heavy header: `// heavy — include only in composition roots`
- [ ] Header is self-contained (`#include` everything it uses)
- [ ] No project-specific dependencies
- [ ] Cross-compiles with GCC 11 / aarch64: `make -C projects/vision-edge BOARD=rpi4`
- [ ] Update `.agents/workflows/shared_library.md` component table
