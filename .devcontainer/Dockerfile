FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Update and install dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        build-essential \
        gcc-aarch64-linux-gnu \
        g++-aarch64-linux-gnu \
        gdb-multiarch \
        libssl-dev \
        bc \
        bison \
        flex \
        device-tree-compiler \
        liblz4-tool \
        python3 \
        git \
        rsync \
        expect \
        openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Easymake
RUN git clone https://github.com/roxma/easymake.git /opt/easymake \
    && ln -s /opt/easymake/easymake /usr/local/bin/easymake

# Add a non-root user (already created by the base devcontainer image)
USER vscode

# Ensure the workspace directory is set correctly
WORKDIR /workspace
