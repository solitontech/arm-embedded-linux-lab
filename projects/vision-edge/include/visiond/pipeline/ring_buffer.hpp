#pragma once
#include <array>
#include <atomic>
#include <cstdint>

namespace visiond {

/// Lockless triple buffer for single-producer / single-consumer exchange.
///
/// The producer writes to one slot while the consumer reads from another.
/// A third "shared" slot holds the most recently published frame. Publishing
/// and acquiring swap atomic indices — no mutexes, no allocations.
///
/// Memory ordering:
///   - publish() uses acquire-release on the shared index exchange to ensure
///     the producer's writes to the buffer are visible to the consumer.
///   - acquire() uses acquire-release on the shared index exchange to ensure
///     the consumer sees the producer's writes before reading the buffer.
template <typename T>
class LocklessTripleBuffer {
public:
    LocklessTripleBuffer() {
        write_idx_.store(0, std::memory_order_relaxed);
        read_idx_.store(1, std::memory_order_relaxed);
        shared_idx_.store(2, std::memory_order_relaxed);
    }

    // -- Producer API --

    /// Get a reference to the current write buffer.
    /// The producer fills this buffer with new data.
    T& get_write_buffer() {
        return buffers_[write_idx_.load(std::memory_order_relaxed)];
    }

    /// Publish the completed write buffer, making it available to the consumer.
    /// Swaps the write index with the shared index atomically.
    void publish() {
        uint32_t old_write = write_idx_.load(std::memory_order_relaxed);
        uint32_t new_write = shared_idx_.exchange(old_write,
                                                  std::memory_order_acq_rel);
        write_idx_.store(new_write, std::memory_order_release);
    }

    // -- Consumer API --

    /// Acquire the most recently published buffer for reading.
    /// Swaps the read index with the shared index atomically.
    T& acquire_read_buffer() {
        uint32_t old_read = read_idx_.load(std::memory_order_relaxed);
        uint32_t new_read = shared_idx_.exchange(old_read,
                                                 std::memory_order_acq_rel);
        read_idx_.store(new_read, std::memory_order_relaxed);
        return buffers_[new_read];
    }

private:
    std::array<T, 3>       buffers_{};
    std::atomic<uint32_t>  write_idx_;
    std::atomic<uint32_t>  read_idx_;
    std::atomic<uint32_t>  shared_idx_;
};

} // namespace visiond
