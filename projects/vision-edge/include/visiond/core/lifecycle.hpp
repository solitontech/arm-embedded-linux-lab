#pragma once
// Forwarding header — subsystem lifecycle lives in shared labkit.
// Include types.hpp to bring expected/Error into visiond:: for downstream headers.
#include "visiond/core/types.hpp"
#include <labkit/lifecycle.hpp>

namespace visiond {
    using labkit::SubsystemState;
    using labkit::ISubsystem;
} // namespace visiond
