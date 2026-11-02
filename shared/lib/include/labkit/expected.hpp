#pragma once
#include <labkit/types.hpp>

// Use std::expected when available (C++23), otherwise fall back to tl::expected.
#if __cpp_lib_expected >= 202211L
    #include <expected>
    namespace labkit {
        template <typename T, typename E = Error>
        using expected = std::expected<T, E>;
        using std::unexpected;
    }
#else
    #include <tl/expected.hpp>
    namespace labkit {
        template <typename T, typename E = Error>
        using expected = tl::expected<T, E>;
        using tl::unexpected;
    }
#endif
