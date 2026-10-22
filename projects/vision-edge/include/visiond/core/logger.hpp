#pragma once
// Forwarding header — lightweight logger interface only.
// SpdlogLogger is in <labkit/spdlog_logger.hpp> — include only in main.cpp.
#include <labkit/logger.hpp>

namespace visiond {
    using labkit::LogLevel;
    using labkit::ILogger;
} // namespace visiond
