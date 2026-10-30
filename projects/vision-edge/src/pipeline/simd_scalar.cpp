#include "visiond/pipeline/simd_engine.hpp"
#include <cmath>

namespace visiond {

class ScalarSIMDEngine : public ISIMDEngine {
public:
    std::string_view name() const override { return "ScalarSIMDEngine"; }

    uint32_t pixel_diff_threshold(const uint8_t* current_frame,
                                  const uint8_t* baseline_frame,
                                  size_t num_pixels,
                                  uint8_t threshold) override {
        uint32_t anomaly_count = 0;
        for (size_t i = 0; i < num_pixels; ++i) {
            int diff = std::abs(static_cast<int>(current_frame[i]) -
                                static_cast<int>(baseline_frame[i]));
            if (diff > threshold) ++anomaly_count;
        }
        return anomaly_count;
    }
};

std::unique_ptr<ISIMDEngine> make_scalar_simd_engine() {
    return std::make_unique<ScalarSIMDEngine>();
}

} // namespace visiond
