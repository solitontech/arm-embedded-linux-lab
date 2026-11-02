#pragma once
// Concrete ILogger backed by spdlog. Heavy header — include only in
// composition roots (main.cpp) where the logger is constructed.
#include <labkit/logger.hpp>
#include <memory>
#include <string>

#ifndef SPDLOG_HEADER_ONLY
#define SPDLOG_HEADER_ONLY
#endif
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

namespace labkit {

class SpdlogLogger : public ILogger {
public:
    explicit SpdlogLogger(const std::string& name = "app") {
        auto sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
        logger_ = std::make_shared<spdlog::logger>(name, sink);
        logger_->set_pattern("%^[%L]%$ [%Y-%m-%d %H:%M:%S.%e] %v");
        logger_->set_level(spdlog::level::info);
    }

    void log(LogLevel level, std::string_view msg) override {
        switch (level) {
            case LogLevel::DEBUG: logger_->debug("{}", msg);   break;
            case LogLevel::INFO:  logger_->info("{}", msg);    break;
            case LogLevel::WARN:  logger_->warn("{}", msg);    break;
            case LogLevel::ERROR: logger_->error("{}", msg);   break;
        }
    }

    void set_level(LogLevel level) override {
        switch (level) {
            case LogLevel::DEBUG: logger_->set_level(spdlog::level::debug); break;
            case LogLevel::INFO:  logger_->set_level(spdlog::level::info);  break;
            case LogLevel::WARN:  logger_->set_level(spdlog::level::warn);  break;
            case LogLevel::ERROR: logger_->set_level(spdlog::level::err);   break;
        }
    }

    void add_file_sink(const std::string& path) {
        auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(path, true);
        file_sink->set_pattern("[%L] [%Y-%m-%d %H:%M:%S.%e] %v");
        logger_->sinks().push_back(file_sink);
    }

    spdlog::logger& raw() { return *logger_; }

private:
    std::shared_ptr<spdlog::logger> logger_;
};

} // namespace labkit
