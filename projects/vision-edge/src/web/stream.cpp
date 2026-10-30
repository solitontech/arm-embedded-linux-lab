#include "visiond/web/stream.hpp"
#include "visiond/web/shared_state.hpp"
#include "visiond/web/jpeg.hpp"

namespace visiond {

void MjpegStream::register_events(EventBus& bus) {
    bus.subscribe<FrameEvent>([this](const FrameEvent& e) { on_frame(e); });
}

void MjpegStream::on_frame(const FrameEvent& event) {
    if (!event.frame || !state_) return;
    auto& f = *event.frame;
    auto jpeg = jpeg_encode_gray(f.data, f.width, f.height, f.stride);

    auto* s = static_cast<SharedState*>(state_);
    std::lock_guard<std::mutex> lock(s->frame_mtx);
    s->latest_jpeg = std::move(jpeg);
    s->frame_ready = true;
}

} // namespace visiond
