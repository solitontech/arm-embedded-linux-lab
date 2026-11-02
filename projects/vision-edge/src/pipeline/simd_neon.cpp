#ifdef __aarch64__

#include "visiond/pipeline/simd_engine.hpp"
#include <arm_neon.h>
#include <cmath>

namespace visiond {

class NeonSIMDEngine : public ISIMDEngine {
public:
    std::string_view name() const override { return "NeonSIMDEngine"; }

    uint32_t pixel_diff_threshold(const uint8_t* __restrict current_frame,
                                  const uint8_t* __restrict baseline_frame,
                                  size_t num_pixels,
                                  uint8_t threshold) override {
        uint32_t anomaly_count = 0;
        const uint8x16_t v_thresh = vdupq_n_u8(threshold);
        const uint8x16_t v_one    = vdupq_n_u8(1);

        // Process 64 pixels per unrolled loop iteration (4 x 16-byte NEON registers)
        size_t i = 0;
        for (; i + 63 < num_pixels; i += 64) {
            // 1. Vector load: 16 bytes per register, 4 registers = 64 pixels
            uint8x16_t c0 = vld1q_u8(current_frame  + i);
            uint8x16_t c1 = vld1q_u8(current_frame  + i + 16);
            uint8x16_t c2 = vld1q_u8(current_frame  + i + 32);
            uint8x16_t c3 = vld1q_u8(current_frame  + i + 48);

            uint8x16_t b0 = vld1q_u8(baseline_frame + i);
            uint8x16_t b1 = vld1q_u8(baseline_frame + i + 16);
            uint8x16_t b2 = vld1q_u8(baseline_frame + i + 32);
            uint8x16_t b3 = vld1q_u8(baseline_frame + i + 48);

            // 2. Absolute difference: |current - baseline| per byte
            uint8x16_t diff0 = vabdq_u8(c0, b0);
            uint8x16_t diff1 = vabdq_u8(c1, b1);
            uint8x16_t diff2 = vabdq_u8(c2, b2);
            uint8x16_t diff3 = vabdq_u8(c3, b3);

            // 3. Compare greater than threshold: 0xFF if diff > threshold, else 0x00
            uint8x16_t mask0 = vcgtq_u8(diff0, v_thresh);
            uint8x16_t mask1 = vcgtq_u8(diff1, v_thresh);
            uint8x16_t mask2 = vcgtq_u8(diff2, v_thresh);
            uint8x16_t mask3 = vcgtq_u8(diff3, v_thresh);

            // 4. AND with 1 to convert 0xFF masks to integer 1 flags
            uint8x16_t cnt0 = vandq_u8(mask0, v_one);
            uint8x16_t cnt1 = vandq_u8(mask1, v_one);
            uint8x16_t cnt2 = vandq_u8(mask2, v_one);
            uint8x16_t cnt3 = vandq_u8(mask3, v_one);

            // 5. Horizontal accumulate across all 16 lanes per register
            anomaly_count += vaddlvq_u8(cnt0);
            anomaly_count += vaddlvq_u8(cnt1);
            anomaly_count += vaddlvq_u8(cnt2);
            anomaly_count += vaddlvq_u8(cnt3);
        }

        // Scalar tail for remaining pixels (num_pixels % 64)
        for (; i < num_pixels; ++i) {
            int diff = std::abs(static_cast<int>(current_frame[i]) -
                                static_cast<int>(baseline_frame[i]));
            if (diff > threshold) ++anomaly_count;
        }

        return anomaly_count;
    }
};

std::unique_ptr<ISIMDEngine> make_neon_simd_engine() {
    return std::make_unique<NeonSIMDEngine>();
}

} // namespace visiond

#endif // __aarch64__
