#include "visiond/web/jpeg.hpp"
#include <stb/stb_image_write.h>
#include <cstring>

namespace visiond {

namespace {

void jpeg_write_cb(void* ctx, void* data, int size) {
    auto* out = static_cast<std::vector<uint8_t>*>(ctx);
    auto* bytes = static_cast<const uint8_t*>(data);
    out->insert(out->end(), bytes, bytes + size);
}

} // anonymous namespace

std::vector<uint8_t> jpeg_encode_gray(const uint8_t* data,
                                       uint32_t width, uint32_t height,
                                       uint32_t stride, int quality) {
    std::vector<uint8_t> out;
    out.reserve(width * height / 4);

    // YUYV: 2 bytes per pixel — extract Y (luminance) at every even byte offset.
    // packed[] holds one contiguous grayscale byte per pixel, row-major.
    std::vector<uint8_t> packed(width * height);
    for (uint32_t y = 0; y < height; ++y)
        for (uint32_t x = 0; x < width; ++x)
            packed[y * width + x] = data[y * stride + x * 2];  // Y channel only

    stbi_write_jpg_to_func(jpeg_write_cb, &out,
        static_cast<int>(width), static_cast<int>(height), 1,
        packed.data(), quality);
    return out;
}

} // namespace visiond
