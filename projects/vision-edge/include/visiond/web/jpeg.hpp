#pragma once
#include <cstdint>
#include <vector>

namespace visiond {

std::vector<uint8_t> jpeg_encode_gray(const uint8_t* data,
                                       uint32_t width, uint32_t height,
                                       uint32_t stride, int quality = 75);

} // namespace visiond
