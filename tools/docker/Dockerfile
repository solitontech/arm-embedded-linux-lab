# ==============================================================================
# ARM Embedded Linux Lab — Development Docker Image
# Base: Ubuntu 22.04 LTS
# Contains: native compilers, ARM64 cross-compiler, serial/debug/deploy tools
# ==============================================================================

FROM ubuntu:22.04

# Suppress interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive

# Layer 1: Core build tools & host compilers (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    cmake \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    gcc \
    g++ \
    clang \
    curl \
    wget \
    bison \
    flex \
    bc \
    libssl-dev \
    swig \
    device-tree-compiler \
    lld \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Heavy cross-compiler toolchains (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc-aarch64-linux-gnu \
    g++-aarch64-linux-gnu \
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Layer 3: Serial, debug, deploy & network tools (easier to add/modify without invalidating compiler cache)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdb-multiarch \
    picocom \
    minicom \
    socat \
    nano \
    sudo \
    openssh-client \
    rsync \
    iputils-ping \
    iproute2 \
    net-tools \
    ufw \
    tftp-hpa \
    tftpd-hpa \
    nfs-kernel-server \
    rpcbind \
    u-boot-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pre-configure /etc/default/tftpd-hpa to serve /workspace/tftp
RUN echo 'TFTP_USERNAME="tftp"' > /etc/default/tftpd-hpa && \
    echo 'TFTP_DIRECTORY="/workspace/tftp"' >> /etc/default/tftpd-hpa && \
    echo 'TFTP_ADDRESS=":69"' >> /etc/default/tftpd-hpa && \
    echo 'TFTP_OPTIONS="--secure"' >> /etc/default/tftpd-hpa

# Create a non-root user matching the host UID/GID to avoid permission issues
# Pass --build-arg UID=$(id -u) GID=$(id -g) when building
ARG UID=1000
ARG GID=1000
RUN TARGET_UID="${UID}"; TARGET_GID="${GID}"; \
    if [ "${TARGET_UID}" -eq 0 ]; then TARGET_UID=1000; TARGET_GID=1000; fi; \
    (getent group ${TARGET_GID} || groupadd -g ${TARGET_GID} labuser) \
    && (id -u labuser >/dev/null 2>&1 || useradd -m -u ${TARGET_UID} -g ${TARGET_GID} -s /bin/bash labuser) \
    && usermod -aG dialout labuser \
    && echo "labuser ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/labuser \
    && chmod 0440 /etc/sudoers.d/labuser

# Copy container entrypoint script
COPY tools/docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set working directory — the repo is bind-mounted here at runtime
WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
