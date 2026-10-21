#pragma once

#include <atomic>
#include <string_view>

namespace visiond {

enum class DaemonState {
    UNINITIALIZED,
    INITIALIZING,
    RUNNING,
    PAUSED,
    STOPPING,
    TERMINATED
};

inline std::string_view state_to_string(DaemonState state) {
    switch (state) {
        case DaemonState::UNINITIALIZED: return "UNINITIALIZED";
        case DaemonState::INITIALIZING:  return "INITIALIZING";
        case DaemonState::RUNNING:       return "RUNNING";
        case DaemonState::PAUSED:        return "PAUSED";
        case DaemonState::STOPPING:      return "STOPPING";
        case DaemonState::TERMINATED:    return "TERMINATED";
        default:                         return "UNKNOWN";
    }
}

class StateManager {
public:
    static StateManager& instance() {
        static StateManager sm;
        return sm;
    }

    void set_state(DaemonState new_state) {
        state_.store(new_state, std::memory_order_release);
    }

    DaemonState get_state() const {
        return state_.load(std::memory_order_acquire);
    }

    bool is_running() const {
        return state_.load(std::memory_order_acquire) == DaemonState::RUNNING;
    }

private:
    StateManager() : state_(DaemonState::UNINITIALIZED) {}
    std::atomic<DaemonState> state_;
};

} // namespace visiond
