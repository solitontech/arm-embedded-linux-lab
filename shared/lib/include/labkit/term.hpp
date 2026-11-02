#pragma once
#include <initializer_list>
#include <iostream>
#include <string>
#include <string_view>

namespace labkit::term {

enum class Color {
    Default, Black, Red, Green, Yellow, Blue, Magenta, Cyan, White,
    BrightRed, BrightGreen, BrightYellow, BrightBlue, BrightMagenta, BrightCyan, BrightWhite
};

// --- ANSI escape helpers ---

inline const char* color_code(Color c) {
    switch (c) {
        case Color::Default:       return "\033[0m";
        case Color::Black:         return "\033[30m";
        case Color::Red:           return "\033[31m";
        case Color::Green:         return "\033[32m";
        case Color::Yellow:        return "\033[33m";
        case Color::Blue:          return "\033[34m";
        case Color::Magenta:       return "\033[35m";
        case Color::Cyan:          return "\033[36m";
        case Color::White:         return "\033[37m";
        case Color::BrightRed:     return "\033[91m";
        case Color::BrightGreen:   return "\033[92m";
        case Color::BrightYellow:  return "\033[93m";
        case Color::BrightBlue:    return "\033[94m";
        case Color::BrightMagenta: return "\033[95m";
        case Color::BrightCyan:    return "\033[96m";
        case Color::BrightWhite:   return "\033[97m";
    }
    return "\033[0m";
}

inline std::string colored(Color c, std::string_view text) {
    std::string result;
    result.reserve(text.size() + 16);
    result += color_code(c);
    result += text;
    result += "\033[0m";
    return result;
}

// --- Unicode box-drawing banner ---
//
// ╔══════════════════════════════════════════════════════════════════════╗
// ║  Line 1 text                                                         ║
// ║  Line 2 text                                                         ║
// ╚══════════════════════════════════════════════════════════════════════╝

inline void banner(std::ostream& os,
                   std::initializer_list<std::string_view> lines,
                   Color border_color = Color::BrightCyan,
                   int width = 70) {
    const char* c = color_code(border_color);
    const char* r = "\033[0m";
    int inner = width - 2; // space between ║...║

    // Top border: ╔══...══╗
    os << c << "\xe2\x95\x94";
    for (int i = 0; i < inner; ++i) os << "\xe2\x95\x90";
    os << "\xe2\x95\x97" << r << '\n';

    // Content lines: ║  text ...  ║
    for (auto& line : lines) {
        os << c << "\xe2\x95\x91" << r << "  ";
        os << line;
        int pad = inner - 2 - static_cast<int>(line.size());
        if (pad > 0) for (int i = 0; i < pad; ++i) os << ' ';
        os << c << "\xe2\x95\x91" << r << '\n';
    }

    // Bottom border: ╚══...══╝
    os << c << "\xe2\x95\x9a";
    for (int i = 0; i < inner; ++i) os << "\xe2\x95\x90";
    os << "\xe2\x95\x9d" << r << '\n';

    os << std::flush;
}

// --- Section header ---
// ── Title text ────────────────────────────────────────────────

inline void section(std::ostream& os,
                    std::string_view text,
                    Color color = Color::BrightCyan,
                    int width = 70) {
    const char* c = color_code(color);
    const char* r = "\033[0m";

    os << c << "\xe2\x94\x80\xe2\x94\x80 " << r;
    os << text;
    int remaining = width - 3 - static_cast<int>(text.size()) - 1;
    if (remaining > 0) {
        os << ' ' << c;
        for (int i = 0; i < remaining; ++i) os << "\xe2\x94\x80";
        os << r;
    }
    os << '\n' << std::flush;
}

// --- Horizontal separator ---
// ──────────────────────────────────────────────────────────────

inline void separator(std::ostream& os,
                      Color color = Color::Default,
                      int width = 70) {
    const char* c = (color == Color::Default) ? "" : color_code(color);
    const char* r = (color == Color::Default) ? "" : "\033[0m";

    os << c;
    for (int i = 0; i < width; ++i) os << "\xe2\x94\x80";
    os << r << '\n' << std::flush;
}

// --- Key-value pair ---
//   Board           Raspberry Pi 4

inline void kv(std::ostream& os,
               std::string_view key,
               std::string_view value,
               int key_width = 16) {
    os << "  " << key;
    int pad = key_width - static_cast<int>(key.size());
    if (pad > 0) for (int i = 0; i < pad; ++i) os << ' ';
    os << value << '\n';
}

// --- Status indicators ---

inline void status_ok(std::ostream& os, std::string_view msg) {
    os << "  " << color_code(Color::Green) << "\xe2\x9c\x94" << "\033[0m " << msg << '\n';
}

inline void status_fail(std::ostream& os, std::string_view msg) {
    os << "  " << color_code(Color::Red) << "\xe2\x9c\x96" << "\033[0m " << msg << '\n';
}

} // namespace labkit::term
