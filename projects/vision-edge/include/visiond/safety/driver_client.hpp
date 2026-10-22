#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include <labkit/logger.hpp>
#include <cstdint>
#include <string>

namespace visiond {
using labkit::expected;
using labkit::unexpected;
using labkit::Error;
using labkit::ErrorCode;
using labkit::ILogger;
using labkit::LogLevel;

struct SafetyStatus {
    bool     armed{false};
    bool     tripped{false};
    uint64_t trip_timestamp_ns{0};
    uint32_t trip_count{0};
};

// Abstract interface — enables test mocks without hardware
class ISafetyDriver {
public:
    virtual ~ISafetyDriver() = default;
    virtual expected<void, Error>         arm()                      = 0;
    virtual expected<void, Error>         disarm()                   = 0;
    virtual expected<void, Error>         trip()                     = 0;
    virtual expected<bool, Error>         poll_event(int timeout_ms) = 0;
    virtual expected<SafetyStatus, Error> status()                   = 0;
};

// Real implementation: ioctl client for /dev/vision_safety
class DriverClient : public ISafetyDriver {
public:
    explicit DriverClient(ILogger& logger,
                          const std::string& device_path = "/dev/vision_safety");
    ~DriverClient() override;

    DriverClient(const DriverClient&) = delete;
    DriverClient& operator=(const DriverClient&) = delete;

    expected<void, Error> open_device();

    expected<void, Error>         arm()                      override;
    expected<void, Error>         disarm()                   override;
    expected<void, Error>         trip()                     override;
    expected<bool, Error>         poll_event(int timeout_ms) override;
    expected<SafetyStatus, Error> status()                   override;

private:
    ILogger&    logger_;
    std::string device_path_;
    int         fd_{-1};
};

} // namespace visiond
