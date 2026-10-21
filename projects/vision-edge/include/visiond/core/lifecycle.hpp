#pragma once
#include "visiond/core/types.hpp"
#include <string_view>

namespace visiond {

enum class SubsystemState { CREATED, INITIALIZED, RUNNING, STOPPED, FAILED };

class ISubsystem {
public:
    virtual ~ISubsystem() = default;
    virtual expected<void, Error> init()  = 0;
    virtual expected<void, Error> start() = 0;
    virtual void                  stop()  = 0;
    virtual std::string_view  name()  const = 0;
    virtual SubsystemState    state() const = 0;
};

} // namespace visiond
