################################################################################
#
# visiond — VisionEdge industrial inspection daemon
#
################################################################################

VISIOND_VERSION = 0.5.0
VISIOND_SITE = $(BR2_EXTERNAL_VISIOND_PATH)/../../..
VISIOND_SITE_METHOD = local
VISIOND_INSTALL_TARGET = YES

VISIOND_BUILD_OPTS = \
	CROSS_COMPILE=$(TARGET_CROSS) \
	BOARD=rpi4 \
	CXXFLAGS_EXTRA="$(TARGET_CXXFLAGS)" \
	LDFLAGS_EXTRA="$(TARGET_LDFLAGS)"

define VISIOND_BUILD_CMDS
	$(MAKE) -C $(@D)/projects/vision-edge $(VISIOND_BUILD_OPTS) clean
	$(MAKE) -C $(@D)/projects/vision-edge $(VISIOND_BUILD_OPTS)
endef

define VISIOND_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/projects/vision-edge/build/rpi4/vision-edge \
		$(TARGET_DIR)/usr/local/bin/visiond
endef

$(eval $(generic-package))
