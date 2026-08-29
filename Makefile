# ==============================================================================
# Top-level Makefile — ARM Embedded Linux Lab Monorepo
# Orchestrates multi-project builds, hardware targets, and scaffolding.
# ==============================================================================

REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BOARD     ?= rpi4

# Discover all projects under projects/ that contain a Makefile
PROJECTS := $(sort $(patsubst $(REPO_ROOT)/projects/%/Makefile,%,$(wildcard $(REPO_ROOT)/projects/*/Makefile)))
BOARDS   := $(sort $(patsubst $(REPO_ROOT)/shared/build_system/boards/%.mk,%,$(wildcard $(REPO_ROOT)/shared/build_system/boards/*.mk)))

.PHONY: all build clean distclean deploy-all list-boards list-projects new-project help

# Default target: build all projects
all: build

build:
	@echo "======================================================================"
	@echo " Building all projects for board: $(BOARD)"
	@echo "======================================================================"
	@if [ -z "$(PROJECTS)" ]; then \
		echo "  [INFO] No projects found in projects/."; \
	else \
		for p in $(PROJECTS); do \
			echo "--> Building $$p for $(BOARD)..."; \
			$(MAKE) -C projects/$$p BOARD=$(BOARD) || exit 1; \
		done; \
	fi

clean:
	@for p in $(PROJECTS); do \
		$(MAKE) -C projects/$$p BOARD=$(BOARD) clean; \
	done

distclean:
	@for p in $(PROJECTS); do \
		$(MAKE) -C projects/$$p distclean; \
	done
	@rm -rf build/ output/ scratchpad/build/

deploy-all:
	@for p in $(PROJECTS); do \
		$(MAKE) -C projects/$$p BOARD=$(BOARD) deploy; \
	done

list-boards:
	@echo "======================================================================"
	@echo " Supported Hardware Board Profiles:"
	@echo "======================================================================"
	@for b in $(BOARDS); do \
		desc=$$(grep -E "^BOARD_DESC" shared/build_system/boards/$$b.mk 2>/dev/null | sed -e 's/^BOARD_DESC[[:space:]]*:=[[:space:]]*//' -e 's/"//g'); \
		arch=$$(grep -E "^ARCH" shared/build_system/boards/$$b.mk 2>/dev/null | sed -e 's/^ARCH[[:space:]]*:=[[:space:]]*//' -e 's/"//g'); \
		printf "  %-15s [%-6s] %s\n" "$$b" "$$arch" "$$desc"; \
	done
	@echo "======================================================================"

list-projects:
	@echo "======================================================================"
	@echo " Active Monorepo Projects:"
	@echo "======================================================================"
	@if [ -z "$(PROJECTS)" ]; then \
		echo "  (No projects created yet. Use 'make new-project NAME=<name>' to create one)"; \
	else \
		for p in $(PROJECTS); do \
			echo "  - $$p"; \
		done; \
	fi
	@echo "======================================================================"

new-project:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: Please specify NAME=<project-name>"; \
		exit 1; \
	fi
	@if [ -d "projects/$(NAME)" ]; then \
		echo "Error: projects/$(NAME) already exists."; \
		exit 1; \
	fi
	@echo "Scaffolding new project: projects/$(NAME)..."
	@cp -r shared/templates/new_project projects/$(NAME)
	@sed -i.bak "s/my-project/$(NAME)/g" projects/$(NAME)/Makefile && rm -f projects/$(NAME)/Makefile.bak
	@echo "Created projects/$(NAME) successfully. Run 'make -C projects/$(NAME) info' to inspect."

help:
	@echo "ARM Embedded Linux Lab — Monorepo Commands:"
	@echo "  make [BOARD=<name>]            - Build all projects in projects/ for board (default: rpi4)"
	@echo "  make clean [BOARD=<name>]      - Clean build artifacts for given board across all projects"
	@echo "  make distclean                 - Clean all build outputs"
	@echo "  make deploy-all [BOARD=<name>] - Deploy all projects to target board"
	@echo "  make list-boards               - List all supported hardware boards"
	@echo "  make list-projects             - List all active projects"
	@echo "  make new-project NAME=<name>   - Scaffold a new project under projects/<name>"
