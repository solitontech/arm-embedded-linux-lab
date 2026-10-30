#pragma once
#include "visiond/safety/driver_client.hpp"
#include <cstdint>

namespace visiond {

class TripController {
public:
    TripController(ISafetyDriver& driver, ILogger& logger, TripPolicy policy = {});

    // Called by the pipeline stage after SIMD diff computation.
    // Returns true if a trip was issued this call.
    expected<bool, Error> evaluate(uint32_t anomaly_count);

    // Reset the consecutive-frame counter (e.g., after re-arm)
    void reset();

    const TripPolicy& policy() const { return policy_; }

private:
    ISafetyDriver& driver_;
    ILogger&       logger_;
    TripPolicy     policy_;
    uint32_t       consecutive_count_{0};
};

} // namespace visiond
