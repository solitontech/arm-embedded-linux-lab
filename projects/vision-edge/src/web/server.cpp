#include "visiond/web/server.hpp"
#include "visiond/web/shared_state.hpp"
#include <mongoose/mongoose.h>
#include <cstdio>
#include <cstring>
#include "dashboard_html.h"

namespace visiond {

namespace {

// CORS headers — allows dashboard.html to connect from any origin
const char* CORS = "Access-Control-Allow-Origin: *\r\n"
                   "Access-Control-Allow-Methods: GET\r\n"
                   "Access-Control-Allow-Headers: *\r\n";

// Connection tag stored in mg_connection::data[0]
constexpr char TAG_MJPEG = 1;
constexpr char TAG_WS    = 2;

// Mongoose event handler — called from mg_mgr_poll()
void http_handler(struct mg_connection* c, int ev, void* ev_data) {
    auto* state = static_cast<SharedState*>(c->fn_data);

    if (ev == MG_EV_HTTP_MSG) {
        auto* hm = static_cast<struct mg_http_message*>(ev_data);

        if (mg_match(hm->uri, mg_str("/stream.mjpg"), nullptr)) {
            mg_printf(c,
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: multipart/x-mixed-replace; boundary=visiond-frame\r\n"
                "Cache-Control: no-cache, no-store, must-revalidate\r\n"
                "Pragma: no-cache\r\n"
                "Expires: 0\r\n"
                "%s"
                "Connection: keep-alive\r\n\r\n", CORS);
            c->data[0] = TAG_MJPEG;
            uint64_t zero = 0;
            std::memcpy(&c->data[8], &zero, sizeof(zero));

        } else if (mg_match(hm->uri, mg_str("/ws/telemetry"), nullptr)) {
            mg_ws_upgrade(c, hm, nullptr);
            c->data[0] = TAG_WS;
            uint64_t zero = 0;
            std::memcpy(&c->data[8], &zero, sizeof(zero));

        } else if (mg_match(hm->uri, mg_str("/api/info"), nullptr)) {
            mg_http_reply(c, 200,
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n",
                "{\"name\":\"visiond\",\"version\":\"" VISIOND_VERSION "\","
                "\"endpoints\":[\"/stream.mjpg\",\"/snapshot.jpg\",\"/ws/telemetry\",\"/api/info\"]}");

        } else if (mg_match(hm->uri, mg_str("/snapshot.jpg"), nullptr) ||
                   mg_match(hm->uri, mg_str("/api/snapshot.jpg"), nullptr)) {
            std::lock_guard<std::mutex> lock(state->frame_mtx);
            if (!state->latest_jpeg.empty()) {
                mg_printf(c,
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: image/jpeg\r\n"
                    "Content-Length: %lu\r\n"
                    "Cache-Control: no-cache, no-store, must-revalidate\r\n"
                    "%s"
                    "Connection: close\r\n\r\n",
                    static_cast<unsigned long>(state->latest_jpeg.size()), CORS);
                mg_send(c, state->latest_jpeg.data(), state->latest_jpeg.size());
            } else {
                mg_http_reply(c, 503, CORS, "No frame available\r\n");
            }
            c->is_draining = 1;

        } else {
            // Serve embedded dashboard HTML for all other routes
            mg_printf(c,
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                "Content-Length: %u\r\n"
                "Cache-Control: no-cache\r\n\r\n",
                dashboard_html_len);
            mg_send(c, dashboard_html, dashboard_html_len);
        }

    } else if (ev == MG_EV_POLL) {
        // Push MJPEG frames to tagged clients
        if (c->data[0] == TAG_MJPEG) {
            std::lock_guard<std::mutex> lock(state->frame_mtx);
            uint64_t client_seq = 0;
            std::memcpy(&client_seq, &c->data[8], sizeof(client_seq));

            if (client_seq < state->frame_seq && !state->latest_jpeg.empty()) {
                auto& jpeg = state->latest_jpeg;
                mg_printf(c,
                    "--visiond-frame\r\n"
                    "Content-Type: image/jpeg\r\n"
                    "Content-Length: %lu\r\n\r\n",
                    static_cast<unsigned long>(jpeg.size()));
                mg_send(c, jpeg.data(), jpeg.size());
                mg_send(c, "\r\n", 2);

                client_seq = state->frame_seq;
                std::memcpy(&c->data[8], &client_seq, sizeof(client_seq));
            }
        }
        // Push telemetry JSON to WebSocket clients
        if (c->data[0] == TAG_WS) {
            std::lock_guard<std::mutex> lock(state->metrics_mtx);
            uint64_t client_seq = 0;
            std::memcpy(&client_seq, &c->data[8], sizeof(client_seq));

            if (client_seq < state->metrics_seq && !state->latest_json.empty()) {
                mg_ws_send(c, state->latest_json.data(),
                           state->latest_json.size(), WEBSOCKET_OP_TEXT);
                client_seq = state->metrics_seq;
                std::memcpy(&c->data[8], &client_seq, sizeof(client_seq));
            }
        }
    }
}

} // anonymous namespace

// ---------------------------------------------------------------------------
// WebServer — mongoose event loop as an ISubsystem
// ---------------------------------------------------------------------------

WebServer::WebServer(ILogger& logger, EventBus& bus, const DaemonConfig& config)
    : logger_(logger), bus_(bus), port_(config.web_port) {}

WebServer::~WebServer() { stop(); }

expected<void, Error> WebServer::init() {
    state_data_ = std::make_unique<SharedState>();
    mjpeg_.state_ = state_data_.get();
    ws_telemetry_.state_ = state_data_.get();

    mjpeg_.register_events(bus_);
    ws_telemetry_.register_events(bus_);

    state_ = SubsystemState::INITIALIZED;
    logger_.log(LogLevel::INFO, "WebServer initialized on :" + std::to_string(port_));
    return {};
}

expected<void, Error> WebServer::start() {
    running_ = true;
    accept_thread_ = std::thread([this]() {
        struct mg_mgr mgr;
        mg_mgr_init(&mgr);

        char url[64];
        std::snprintf(url, sizeof(url), "http://0.0.0.0:%u", port_);
        mg_http_listen(&mgr, url, http_handler, state_data_.get());

        logger_.log(LogLevel::INFO, "WebServer listening on :" + std::to_string(port_));

        while (running_) {
            mg_mgr_poll(&mgr, 50);
        }

        mg_mgr_free(&mgr);
    });

    state_ = SubsystemState::RUNNING;
    return {};
}

void WebServer::stop() {
    if (!running_.exchange(false)) return;

    if (accept_thread_.joinable())
        accept_thread_.join();

    state_ = SubsystemState::STOPPED;
    logger_.log(LogLevel::INFO, "WebServer stopped");
}

} // namespace visiond
