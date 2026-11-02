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
    uint64_t frame_seq{0};

    std::mutex metrics_mtx;
    std::string latest_json;
    uint64_t metrics_seq{0};
};

} // namespace visiond
