# Vendored Third-Party Libraries

Header-only C++ libraries committed directly into the repository.
All projects automatically have these on the include path via `framework.mk`.

| Library | Version | License | Source |
|---|---|---|---|
| **spdlog** | v1.14.1 (2024-04-22) | MIT | https://github.com/gabime/spdlog/releases/tag/v1.14.1 |
| **fmtlib** | bundled with spdlog | MIT | (bundled in `spdlog/fmt/`) |
| **tl::expected** | v1.1.0 (2023-07-09) | CC0 1.0 | https://github.com/TartanLlama/expected/releases/tag/v1.1.0 |

## Usage

```cpp
// spdlog (used internally by labkit::SpdlogLogger — prefer labkit/logger.hpp)
#include <spdlog/spdlog.h>

// tl::expected (used internally by labkit/expected.hpp — prefer labkit/expected.hpp)
#include <tl/expected.hpp>
```

## Updating a Vendored Library

1. Download the new release archive
2. Replace the contents of the corresponding directory under `vendor/`
3. Update the version in this table
4. Cross-compile all projects to verify: `./lab docker exec -- ./lab build <project> --board rpi4`
5. Commit with message: `chore(vendor): update <lib> to v<version>`
