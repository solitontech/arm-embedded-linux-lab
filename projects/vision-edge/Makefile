# ==============================================================================
# Project Makefile Template
# Copy to projects/<your-project>/ and customize variables below.
# ==============================================================================

# Project identity
PROJECT_NAME    := vision-edge
PROJECT_TYPE    := app            # app | lib_static | lib_shared | raw
DEFAULT_BOARD   := rpi4

# Custom build flags
CXXFLAGS_EXTRA  += -std=c++20 -O2 -Wall -Wextra
INCLUDES_EXTRA  += -I./include
LDFLAGS_EXTRA   += -static
LDLIBS_EXTRA    += -pthread

# Deployment configuration
DEPLOY_METHOD   := ssh
TARGET_DEST_DIR := /usr/bin

# Lifecycle hooks (optional)
# PRE_BUILD_HOOK   := 
# POST_BUILD_HOOK  := 
# PRE_DEPLOY_HOOK  := 
# POST_DEPLOY_HOOK := 

# Include the centralized monorepo framework
include ../../shared/build_system/framework.mk
