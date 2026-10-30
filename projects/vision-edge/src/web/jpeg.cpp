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
    // stb wants contiguous rows — if stride == width, pass directly
    if (stride == width) {
        stbi_write_jpg_to_func(jpeg_write_cb, &out,
            static_cast<int>(width), static_cast<int>(height), 1, data, quality);
    } else {
        // Pack rows into contiguous buffer
        std::vector<uint8_t> packed(width * height);
        for (uint32_t y = 0; y < height; y++)
            std::memcpy(packed.data() + y * width, data + y * stride, width);
        stbi_write_jpg_to_func(jpeg_write_cb, &out,
            static_cast<int>(width), static_cast<int>(height), 1, packed.data(), quality);
    }
    return out;
}

} // namespace visiond
