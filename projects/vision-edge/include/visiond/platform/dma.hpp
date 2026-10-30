#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <cstdint>

#ifdef __linux__
#include <linux/dma-buf.h>
#include <sys/ioctl.h>
#include <unistd.h>
#endif

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;

class DmaBufHandle {
public:
    explicit DmaBufHandle(int fd = -1) : fd_(fd) {}
    ~DmaBufHandle() { if (fd_ >= 0) ::close(fd_); }

    // Move-only
    DmaBufHandle(DmaBufHandle&& other) noexcept : fd_(other.fd_) { other.fd_ = -1; }
    DmaBufHandle& operator=(DmaBufHandle&& other) noexcept {
        if (this != &other) { if (fd_ >= 0) ::close(fd_); fd_ = other.fd_; other.fd_ = -1; }
        return *this;
    }
    DmaBufHandle(const DmaBufHandle&) = delete;
    DmaBufHandle& operator=(const DmaBufHandle&) = delete;

    int fd() const { return fd_; }

    // Invalidate CPU caches before reading DMA-written data
    expected<void, Error> sync_for_cpu() {
#ifdef __linux__
        dma_buf_sync sync{};
        sync.flags = DMA_BUF_SYNC_START | DMA_BUF_SYNC_READ;
        if (::ioctl(fd_, DMA_BUF_IOCTL_SYNC, &sync) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "DMA_BUF_SYNC_START failed"});
#endif
        return {};
    }

    // Release CPU cache ownership back to device
    expected<void, Error> sync_for_device() {
#ifdef __linux__
        dma_buf_sync sync{};
        sync.flags = DMA_BUF_SYNC_END | DMA_BUF_SYNC_READ;
        if (::ioctl(fd_, DMA_BUF_IOCTL_SYNC, &sync) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "DMA_BUF_SYNC_END failed"});
#endif
        return {};
    }

private:
    int fd_{-1};
};

} // namespace visiond
