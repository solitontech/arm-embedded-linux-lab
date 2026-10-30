#pragma once
#include <cstdint>
#include <memory>
#include <string_view>

namespace visiond {

class ISIMDEngine {
public:
    virtual ~ISIMDEngine() = default;
    virtual std::string_view name() const = 0;

    // Returns the count of pixels where |current[i] - baseline[i]| > threshold
    virtual uint32_t pixel_diff_threshold(const uint8_t* current_frame,
                                          const uint8_t* baseline_frame,
                                          size_t num_pixels,
                                          uint8_t threshold) = 0;
};

// Factory functions — architecture selects the implementation
#ifdef __aarch64__
std::unique_ptr<ISIMDEngine> make_neon_simd_engine();
#endif
std::unique_ptr<ISIMDEngine> make_scalar_simd_engine();

} // namespace visiond
