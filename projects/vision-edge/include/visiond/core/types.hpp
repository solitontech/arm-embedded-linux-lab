#pragma once
// Forwarding header — types and expected polyfill live in shared labkit.
#include <labkit/types.hpp>
#include <labkit/expected.hpp>

namespace visiond {
    using labkit::ErrorCode;
    using labkit::Error;
    using labkit::expected;
    using labkit::unexpected;
} // namespace visiond
