#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <pthread.h>
#include <sched.h>
#include <string>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;

inline expected<void, Error> pin_thread_to_core(pthread_t thread, int core_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);
    int rc = pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
    if (rc != 0)
        return unexpected(Error{ErrorCode::IO_ERROR,
                                "Failed to pin thread to core " + std::to_string(core_id)});
    return {};
}

} // namespace visiond
