# ==============================================================================
# ARM Embedded Linux Lab — Development Docker Image
# Base: Ubuntu 22.04 LTS
# Contains: native compilers, ARM64 cross-compiler, serial/debug/deploy tools
# ==============================================================================

FROM ubuntu:22.04

# Suppress interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive

# Install all required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core build tools
    build-essential \
    git \
    cmake \
    python3 \
    python3-pip \
    # Host compilers
    gcc \
    g++ \
    clang \
    # ARM64 cross-compiler (RPi4, RPi3, QEMU — currently used targets)
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    # Debug & serial tools
    gdb-multiarch \
    picocom \
    minicom \
    # Deploy / network tools
    ssh \
    rsync \
    scp \
    iputils-ping \
    # Utilities
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user matching the host UID/GID to avoid permission issues
# Pass --build-arg UID=$(id -u) GID=$(id -g) when building
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} labuser \
    && useradd -m -u ${UID} -g ${GID} -s /bin/bash labuser

# Set working directory — the repo is bind-mounted here at runtime
WORKDIR /workspace

# Ensure lab CLI is executable when mounted
# (The actual ./lab symlink is provided via the bind mount)

USER labuser

# Default: open an interactive bash shell
CMD ["/bin/bash"]
