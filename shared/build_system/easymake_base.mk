# ==============================================================================
# easymake_base.mk
# Core compilation engine for the ARM Embedded Linux Lab monorepo.
#
# Provides:
# - Automatic discovery of C/C++/Assembly source files
# - Per-board isolated build trees (build/$(BOARD)/obj/...)
# - Automatic header dependency tracking (-MMD -MP)
# - Support for executables, static libraries (.a), and shared libraries (.so)
# ==============================================================================

# Directories to search for sources (defaults to src)
SRCDIRS ?= src

# Find all source files unless explicitly provided by the project
ifeq ($(strip $(SRCS)),)
  C_SRCS   := $(shell find $(SRCDIRS) -name '*.c' 2>/dev/null)
  CXX_SRCS := $(shell find $(SRCDIRS) \( -name '*.cpp' -o -name '*.cc' -o -name '*.cxx' \) 2>/dev/null)
  ASM_SRCS := $(shell find $(SRCDIRS) \( -name '*.s' -o -name '*.S' \) 2>/dev/null)
  SRCS     := $(C_SRCS) $(CXX_SRCS) $(ASM_SRCS) $(SRCS_EXTRA)
endif

# Compute object files inside build/$(BOARD)/obj/
OBJS := $(patsubst %.c,$(BUILD_DIR)/obj/%.o,$(filter %.c,$(SRCS))) \
        $(patsubst %.cpp,$(BUILD_DIR)/obj/%.o,$(filter %.cpp,$(SRCS))) \
        $(patsubst %.cc,$(BUILD_DIR)/obj/%.o,$(filter %.cc,$(SRCS))) \
        $(patsubst %.cxx,$(BUILD_DIR)/obj/%.o,$(filter %.cxx,$(SRCS))) \
        $(patsubst %.s,$(BUILD_DIR)/obj/%.o,$(filter %.s,$(SRCS))) \
        $(patsubst %.S,$(BUILD_DIR)/obj/%.o,$(filter %.S,$(SRCS)))

# Dependency files
DEPS := $(OBJS:.o=.d)

# Adjust flags for shared library if requested
ifeq ($(PROJECT_TYPE),lib_shared)
  CFLAGS   += -fPIC
  CXXFLAGS += -fPIC
endif

# ------------------------------------------------------------------------------
# Target Compilation Rules
# ------------------------------------------------------------------------------

# Pattern rule for C source files
$(BUILD_DIR)/obj/%.o: %.c
	@mkdir -p $(dir $@)
	@echo "  [CC]  $< -> $@"
	@$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

# Pattern rule for C++ source files
$(BUILD_DIR)/obj/%.o: %.cpp
	@mkdir -p $(dir $@)
	@echo "  [CXX] $< -> $@"
	@$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR)/obj/%.o: %.cc
	@mkdir -p $(dir $@)
	@echo "  [CXX] $< -> $@"
	@$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR)/obj/%.o: %.cxx
	@mkdir -p $(dir $@)
	@echo "  [CXX] $< -> $@"
	@$(CXX) $(CXXFLAGS) -MMD -MP -c $< -o $@

# Pattern rule for Assembly source files
$(BUILD_DIR)/obj/%.o: %.s
	@mkdir -p $(dir $@)
	@echo "  [AS]  $< -> $@"
	@$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/obj/%.o: %.S
	@mkdir -p $(dir $@)
	@echo "  [AS]  $< -> $@"
	@$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

# ------------------------------------------------------------------------------
# Final Linking Rules based on PROJECT_TYPE
# ------------------------------------------------------------------------------

ifeq ($(PROJECT_TYPE),lib_static)
$(TARGET): $(OBJS)
	@mkdir -p $(dir $@)
	@echo "  [AR]  $@"
	@$(AR) rcs $@ $^
else ifeq ($(PROJECT_TYPE),lib_shared)
$(TARGET): $(OBJS)
	@mkdir -p $(dir $@)
	@echo "  [LD]  $@ (Shared Library)"
	@$(CXX) -shared $(LDFLAGS) -o $@ $^ $(LDLIBS)
else ifeq ($(PROJECT_TYPE),raw)
$(TARGET):
	@mkdir -p $(dir $@)
	@echo "  [RAW] Target ready: $@"
else
# Default: Executable application
$(TARGET): $(OBJS)
	@mkdir -p $(dir $@)
	@echo "  [LD]  $@"
	@$(CXX) $(LDFLAGS) -o $@ $^ $(LDLIBS)
endif

# Include dependency files if they exist
-include $(DEPS)
