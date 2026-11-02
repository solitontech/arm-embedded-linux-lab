#pragma once
#include "visiond/platform/gpio.hpp"
#include <labkit/lifecycle.hpp>
#include <memory>
#include <string_view>
#include <utility>

namespace visiond {
using labkit::SubsystemState;
using labkit::ISubsystem;

// Adapter: wraps IGpioController into ISubsystem for the orchestrator
class GpioSubsystem : public ISubsystem {
public:
    explicit GpioSubsystem(std::unique_ptr<IGpioController> ctrl)
        : ctrl_(std::move(ctrl)) {}

    expected<void, Error> init() override {
        state_ = SubsystemState::INITIALIZED;
        return ctrl_->init();
    }
    expected<void, Error> start() override {
        state_ = SubsystemState::RUNNING;
        return {};
    }
    void stop() override {
        state_ = SubsystemState::STOPPED;
    }
    std::string_view   name()  const override { return "gpio"; }
    SubsystemState     state() const override { return state_; }

private:
    std::unique_ptr<IGpioController> ctrl_;
    SubsystemState state_{SubsystemState::CREATED};
};

} // namespace visiond
