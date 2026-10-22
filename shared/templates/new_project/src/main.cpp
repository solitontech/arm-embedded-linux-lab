#include <labkit/spdlog_logger.hpp>    // heavy — only in composition root (main.cpp)
#include <labkit/term.hpp>
#include <iostream>

// Entry point for the embedded daemon.
// Replace this with your project's initialization logic.
// See shared/lib/include/labkit/ for available utilities:
//   labkit::ILogger (lightweight), labkit::SpdlogLogger (heavy, main.cpp only),
//   labkit::term::banner(), labkit::EventBus, etc.
int main() {
    labkit::term::banner(std::cout, {
        "ARM Embedded Linux Lab — New Project",
    });

    labkit::SpdlogLogger logger("app");
    logger.log(labkit::LogLevel::INFO, "Hello from ARM Embedded Linux Lab project!");

    return 0;
}
