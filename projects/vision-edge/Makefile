# ==============================================================================
# Project Makefile Template
# Copy to projects/<your-project>/ and customize variables below.
# ==============================================================================

# Project identity
PROJECT_NAME    := vision-edge
PROJECT_TYPE    := app            # app | lib_static | lib_shared | raw
DEFAULT_BOARD   := rpi4

# Version — single source of truth, injected as preprocessor macro
VISIOND_VERSION := 0.5.0

# Custom build flags
CXXFLAGS_EXTRA  += -std=c++20 -g -O2 -Wall -Wextra -DVISIOND_VERSION=\"$(VISIOND_VERSION)\"
INCLUDES_EXTRA  += -I./include -I./$(BUILD_DIR)/generated
LDFLAGS_EXTRA   += -static
LDLIBS_EXTRA    += -pthread

# Deployment configuration
DEPLOY_METHOD   := ssh
TARGET_DEST_DIR := /usr/bin

# Include the centralized monorepo framework
include ../../shared/build_system/framework.mk

# --- Embed dashboard.html as C header (generated before compilation) ---
DASHBOARD_HDR := $(BUILD_DIR)/generated/dashboard_html.h

$(DASHBOARD_HDR): web/dashboard.html tools/embed_html.py
	@mkdir -p $(dir $@)
	@echo "  [GEN] dashboard_html.h"
	@python3 tools/embed_html.py $< $@

# server.cpp includes dashboard_html.h — ensure it exists before compilation
$(BUILD_DIR)/obj/src/web/server.o: $(DASHBOARD_HDR)
