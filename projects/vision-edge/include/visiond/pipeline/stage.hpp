#pragma once
#include <labkit/types.hpp>
#include <labkit/expected.hpp>
#include "visiond/pipeline/frame.hpp"
#include <string_view>

namespace visiond {
using labkit::expected;
using labkit::Error;

class IPipelineStage {
public:
    virtual ~IPipelineStage() = default;
    virtual std::string_view      name() const                 = 0;
    virtual expected<void, Error> process(FrameDescriptor& fd) = 0;
};

} // namespace visiond
