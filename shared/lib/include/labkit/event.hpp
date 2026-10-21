#pragma once
#include <any>
#include <functional>
#include <mutex>
#include <typeindex>
#include <unordered_map>
#include <vector>

namespace labkit {

class EventBus {
public:
    template <typename EventT>
    void subscribe(std::function<void(const EventT&)> handler) {
        std::lock_guard<std::mutex> lock(mtx_);
        auto key = std::type_index(typeid(EventT));
        handlers_[key].emplace_back(
            [h = std::move(handler)](const std::any& a) {
                h(std::any_cast<const EventT&>(a));
            });
    }

    template <typename EventT>
    void publish(const EventT& event) {
        std::vector<std::function<void(const std::any&)>> snapshot;
        {
            std::lock_guard<std::mutex> lock(mtx_);
            auto it = handlers_.find(std::type_index(typeid(EventT)));
            if (it == handlers_.end()) return;
            snapshot = it->second;
        }
        std::any wrapped = event;
        for (auto& fn : snapshot) fn(wrapped);
    }

private:
    std::mutex mtx_;
    std::unordered_map<std::type_index,
                       std::vector<std::function<void(const std::any&)>>> handlers_;
};

} // namespace labkit
