#include "visiond/safety/driver_client.hpp"

#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <poll.h>
#include <cerrno>
#include <cstring>

// Shared UAPI header — same definitions as the kernel module
#include "../../kernel/include/uapi/vision_safety_uapi.h"

namespace visiond {

DriverClient::DriverClient(ILogger& logger, const std::string& device_path)
    : logger_(logger)
    , device_path_(device_path)
{}

DriverClient::~DriverClient()
{
    if (fd_ >= 0) {
        ::close(fd_);
        fd_ = -1;
    }
}

expected<void, Error> DriverClient::open_device()
{
    fd_ = ::open(device_path_.c_str(), O_RDWR);
    if (fd_ < 0) {
        return unexpected<Error>(Error{
            ErrorCode::DEVICE_NOT_FOUND,
            "Failed to open " + device_path_ + ": " + std::strerror(errno)
        });
    }
    logger_.log(LogLevel::INFO,
                "Opened " + device_path_ + " (fd=" + std::to_string(fd_) + ")");
    return {};
}

expected<void, Error> DriverClient::arm()
{
    if (::ioctl(fd_, VISION_IOCTL_ARM) < 0) {
        return unexpected<Error>(Error{ErrorCode::IO_ERROR,
            "VISION_IOCTL_ARM failed: " + std::string(std::strerror(errno))});
    }
    logger_.log(LogLevel::INFO, "Safety system ARMED");
    return {};
}

expected<void, Error> DriverClient::disarm()
{
    if (::ioctl(fd_, VISION_IOCTL_DISARM) < 0) {
        return unexpected<Error>(Error{ErrorCode::IO_ERROR,
            "VISION_IOCTL_DISARM failed: " + std::string(std::strerror(errno))});
    }
    logger_.log(LogLevel::INFO, "Safety system DISARMED");
    return {};
}

expected<void, Error> DriverClient::trip()
{
    if (::ioctl(fd_, VISION_IOCTL_TRIP) < 0) {
        return unexpected<Error>(Error{ErrorCode::IO_ERROR,
            "VISION_IOCTL_TRIP failed: " + std::string(std::strerror(errno))});
    }
    logger_.log(LogLevel::WARN, "Safety TRIP issued (software)");
    return {};
}

expected<bool, Error> DriverClient::poll_event(int timeout_ms)
{
    struct pollfd pfd{};
    pfd.fd     = fd_;
    pfd.events = POLLIN | POLLPRI;

    int ret = ::poll(&pfd, 1, timeout_ms);
    if (ret < 0) {
        return unexpected<Error>(Error{ErrorCode::IO_ERROR,
            "poll() failed: " + std::string(std::strerror(errno))});
    }
    if (ret == 0)
        return false;  // Timeout — no event

    return (pfd.revents & (POLLIN | POLLPRI)) != 0;
}

expected<SafetyStatus, Error> DriverClient::status()
{
    struct vision_safety_status kstatus{};
    if (::ioctl(fd_, VISION_IOCTL_STATUS, &kstatus) < 0) {
        return unexpected<Error>(Error{ErrorCode::IO_ERROR,
            "VISION_IOCTL_STATUS failed: " + std::string(std::strerror(errno))});
    }

    SafetyStatus result;
    result.armed             = kstatus.armed != 0;
    result.tripped           = kstatus.tripped != 0;
    result.trip_timestamp_ns = kstatus.trip_timestamp_ns;
    result.trip_count        = kstatus.trip_count;
    return result;
}

} // namespace visiond
