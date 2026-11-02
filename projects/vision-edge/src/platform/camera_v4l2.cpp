#ifdef __aarch64__

#include "visiond/platform/camera.hpp"
#include "visiond/platform/dma.hpp"
#include <linux/videodev2.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <vector>

namespace visiond {

class V4l2CameraSource : public ICameraSource {
public:
    explicit V4l2CameraSource(ILogger& logger) : logger_(logger) {}

    ~V4l2CameraSource() override {
        stop_streaming();
        for (auto& buf : buffers_) {
            if (buf.start) munmap(buf.start, buf.length);
        }
        if (fd_ >= 0) ::close(fd_);
    }

    expected<void, Error> open(const CameraConfig& cfg) override {
        fd_ = ::open("/dev/video0", O_RDWR | O_NONBLOCK, 0);
        if (fd_ < 0)
            return unexpected(Error{ErrorCode::DEVICE_NOT_FOUND, "Cannot open /dev/video0"});

        // Set pixel format
        v4l2_format fmt{};
        fmt.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        fmt.fmt.pix.width       = cfg.width;
        fmt.fmt.pix.height      = cfg.height;
        fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
        fmt.fmt.pix.field       = V4L2_FIELD_NONE;
        if (::ioctl(fd_, VIDIOC_S_FMT, &fmt) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "VIDIOC_S_FMT failed"});

        width_  = fmt.fmt.pix.width;
        height_ = fmt.fmt.pix.height;
        stride_ = fmt.fmt.pix.bytesperline;

        // Request MMAP buffers
        v4l2_requestbuffers req{};
        req.count  = cfg.buffer_count;
        req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        req.memory = V4L2_MEMORY_MMAP;
        if (::ioctl(fd_, VIDIOC_REQBUFS, &req) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "VIDIOC_REQBUFS failed"});

        buffers_.resize(req.count);
        for (uint32_t i = 0; i < req.count; ++i) {
            v4l2_buffer buf{};
            buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory = V4L2_MEMORY_MMAP;
            buf.index  = i;
            ::ioctl(fd_, VIDIOC_QUERYBUF, &buf);

            buffers_[i].length = buf.length;
            buffers_[i].start  = mmap(nullptr, buf.length,
                                      PROT_READ | PROT_WRITE, MAP_SHARED,
                                      fd_, buf.m.offset);

            // Export buffer as dma-buf for zero-copy sharing
            v4l2_exportbuffer exp{};
            exp.type  = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            exp.index = i;
            exp.flags = O_CLOEXEC | O_RDWR;
            if (::ioctl(fd_, VIDIOC_EXPBUF, &exp) < 0)
                return unexpected(Error{ErrorCode::IO_ERROR, "VIDIOC_EXPBUF failed"});
            buffers_[i].dma = DmaBufHandle(exp.fd);
        }

        logger_.log(LogLevel::INFO, "V4L2 camera opened: " +
                    std::to_string(width_) + "x" + std::to_string(height_));
        return {};
    }

    expected<void, Error> start_streaming() override {
        for (uint32_t i = 0; i < buffers_.size(); ++i) {
            v4l2_buffer buf{};
            buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory = V4L2_MEMORY_MMAP;
            buf.index  = i;
            ::ioctl(fd_, VIDIOC_QBUF, &buf);
        }
        int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        if (::ioctl(fd_, VIDIOC_STREAMON, &type) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "VIDIOC_STREAMON failed"});
        streaming_ = true;
        return {};
    }

    expected<FrameDescriptor, Error> dequeue_frame() override {
        v4l2_buffer buf{};
        buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        if (::ioctl(fd_, VIDIOC_DQBUF, &buf) < 0)
            return unexpected(Error{ErrorCode::IO_ERROR, "VIDIOC_DQBUF failed"});

        // Invalidate CPU caches — DMA wrote directly to DRAM
        buffers_[buf.index].dma.sync_for_cpu();

        FrameDescriptor fd{};
        fd.data      = static_cast<uint8_t*>(buffers_[buf.index].start);
        fd.width     = width_;
        fd.height    = height_;
        fd.stride    = stride_;
        fd.index     = buf.index;
        fd.sequence  = buf.sequence;
        fd.dma_fd    = buffers_[buf.index].dma.fd();
        return fd;
    }

    void return_frame(uint32_t index) override {
        buffers_[index].dma.sync_for_device();
        v4l2_buffer buf{};
        buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index  = index;
        ::ioctl(fd_, VIDIOC_QBUF, &buf);
    }

    void stop_streaming() override {
        if (!streaming_) return;
        int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        ::ioctl(fd_, VIDIOC_STREAMOFF, &type);
        streaming_ = false;
    }

private:
    struct MappedBuffer {
        void*        start{nullptr};
        size_t       length{0};
        DmaBufHandle dma{-1};
    };

    ILogger&                  logger_;
    int                       fd_{-1};
    bool                      streaming_{false};
    uint32_t                  width_{0}, height_{0}, stride_{0};
    std::vector<MappedBuffer> buffers_;
};

std::unique_ptr<ICameraSource> make_v4l2_camera(ILogger& logger) {
    return std::make_unique<V4l2CameraSource>(logger);
}

} // namespace visiond

#endif // __aarch64__
