#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <cstddef>
#include <cstdint>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;

class MmioRegion {
public:
    static expected<MmioRegion, Error> create(off_t phys_addr, size_t length) {
        int fd = ::open("/dev/mem", O_RDWR | O_SYNC);
        if (fd < 0)
            return unexpected<Error>(Error{ErrorCode::PERMISSION_DENIED,
                    "Failed to open /dev/mem (requires root or CAP_SYS_RAWIO)"});

        void* ptr = ::mmap(nullptr, length, PROT_READ | PROT_WRITE,
                           MAP_SHARED, fd, phys_addr);
        ::close(fd);

        if (ptr == MAP_FAILED)
            return unexpected<Error>(Error{ErrorCode::IO_ERROR,
                    "mmap failed for physical address"});

        return MmioRegion(ptr, length);
    }

    ~MmioRegion() {
        if (base_) ::munmap(base_, length_);
    }

    MmioRegion(MmioRegion&& o) noexcept : base_(o.base_), length_(o.length_) {
        o.base_ = nullptr;
        o.length_ = 0;
    }
    MmioRegion& operator=(MmioRegion&& o) noexcept {
        if (this != &o) {
            if (base_) ::munmap(base_, length_);
            base_ = o.base_;
            length_ = o.length_;
            o.base_ = nullptr;
            o.length_ = 0;
        }
        return *this;
    }
    MmioRegion(const MmioRegion&) = delete;
    MmioRegion& operator=(const MmioRegion&) = delete;

    volatile uint32_t* as_u32() const {
        return static_cast<volatile uint32_t*>(base_);
    }

private:
    MmioRegion(void* base, size_t length) : base_(base), length_(length) {}

    void*  base_{nullptr};
    size_t length_{0};
};

} // namespace visiond
