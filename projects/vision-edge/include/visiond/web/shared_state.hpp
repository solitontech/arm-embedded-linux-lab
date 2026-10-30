#pragma once
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

namespace visiond {

// Thread-safe bridge: EventBus callbacks (any thread) → mongoose poll loop (server thread)
struct SharedState {
    std::mutex frame_mtx;
    std::vector<uint8_t> latest_jpeg;
    bool frame_ready{false};

    std::mutex metrics_mtx;
    std::string latest_json;
    bool metrics_ready{false};
};

} // namespace visiond
