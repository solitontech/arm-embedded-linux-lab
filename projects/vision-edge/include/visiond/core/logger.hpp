#pragma once
// Forwarding header — logger interface lives in shared labkit.
#include <labkit/logger.hpp>

namespace visiond {
    using labkit::LogLevel;
    using labkit::ILogger;
    using labkit::SpdlogLogger;
} // namespace visiond
