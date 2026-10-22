#include "visiond/safety/trip_controller.hpp"

namespace visiond {

TripController::TripController(ISafetyDriver& driver, ILogger& logger, TripPolicy policy)
    : driver_(driver)
    , logger_(logger)
    , policy_(policy)
{}

expected<bool, Error> TripController::evaluate(uint32_t anomaly_count)
{
    if (anomaly_count >= policy_.anomaly_threshold) {
        consecutive_count_++;
        logger_.log(LogLevel::DEBUG,
            "Anomaly threshold exceeded: " + std::to_string(anomaly_count) +
            " >= " + std::to_string(policy_.anomaly_threshold) +
            " (consecutive: " + std::to_string(consecutive_count_) +
            "/" + std::to_string(policy_.consecutive_frames) + ")");

        if (consecutive_count_ >= policy_.consecutive_frames) {
            logger_.log(LogLevel::WARN,
                "Trip threshold reached — issuing safety trip");
            auto result = driver_.trip();
            if (!result.has_value())
                return unexpected<Error>(result.error());
            consecutive_count_ = 0;
            return true;
        }
    } else {
        if (consecutive_count_ > 0) {
            logger_.log(LogLevel::DEBUG,
                "Anomaly count " + std::to_string(anomaly_count) +
                " below threshold — resetting consecutive counter");
        }
        consecutive_count_ = 0;
    }

    return false;
}

void TripController::reset()
{
    consecutive_count_ = 0;
    logger_.log(LogLevel::INFO, "TripController: consecutive counter reset");
}

} // namespace visiond
