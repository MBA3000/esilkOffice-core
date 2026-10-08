# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# esilk brand hook, included from Repository.mk (before every module makefile).
#
# ESILK_BRAND_DIR unset: upstream art. The icons come from sysui/desktop/icons, the MSI bitmaps from
# instsetoo_native/inc_common/windows/msi_templates/Binary, the icon themes are unchanged and the brand pack is the
# one configure found (--with-branding); the pack files reach instdir byte-identical, only via a workdir copy (below).
#
# ESILK_BRAND_DIR=<absolute path outside any LibreOffice tree, no spaces>: the private brand set
# (brand-manifest.json and the files below) supplies
#   * the icon resources of soffice.exe/.com/_safe.exe, soffice.bin, swriter, sweb, scalc, simpress, sdraw,
#     smath, sbase and quickstart: program icons, window/taskbar icons and file-type icons (DefaultIcon is
#     soffice.bin,N). The icons are staged under their upstream names in $(esilk_brand_STAGEDIR)/icons, and
#     gb_WinResTarget_use_esilk_brand_icons (desktop/WinResTarget_*.mk) puts that directory first on the rc
#     include path, so the unchanged .rc files resolve "icons/<name>.ico" to the brand file;
#   * Banner.bmp and Image.bmp of the MSI dialogs (instsetoo_native/CustomTarget_install.mk);
#   * the ARP icon (solenv/bin/modules/installer/windows/idtglobal.pm copies ESILK_BRAND_ARP_ICON);
#   * the brand pack (splash, About, Welcome dialog, Start Center logos): CUSTOM_BRAND_IMAGES and the PROGRESS*
#     splash settings are taken from the pack directory named in brand-manifest.json, so switching brand sets
#     needs no reconfigure;
#   * the product logo inside the PNG icon themes (res/mainapp_*.png: Help > About menu icon, Start Center
#     recent-document badge), as an extra pack_images.py custom path (esilk_brand_IMAGES_CUSTOM/_DEPS, used by
#     postprocess/CustomTarget_images.mk).
# The private files are only read from ESILK_BRAND_DIR and copied into WORKDIR/INSTDIR; nothing private is
# added to this tree.

esilk_brand_STAGEDIR := $(WORKDIR)/EsilkBrand
# Records where the staged files come from: ESILK_BRAND_DIR (empty: upstream art) and the brand pack directory.
# It changes only when one of them changes, so switching the brand on, off, to another directory or to another
# pack in an existing workdir restages everything and rebuilds the icon resources, the MSI bitmaps, the icon theme
# archives and the instdir pack files, while a no-op make rebuilds nothing. (The WinResTarget, msi_templates/%/Binary
# and images_%.zip recipes do not use $<, so the extra prerequisite is safe there.)
esilk_brand_STAMP := $(esilk_brand_STAGEDIR)/brand-dir.stamp

# Files of the brand set: upstream build name : path under ESILK_BRAND_DIR (see brand-manifest.json,
# "build_name"/"build_names"). The names on the left are the files the unchanged .rc files and MSI templates use.
esilk_brand_ICONS := \
	soffice.ico:icons/main.ico \
	writer_app.ico:icons/writer.ico \
	calc_app.ico:icons/calc.ico \
	impress_app.ico:icons/impress.ico \
	draw_app.ico:icons/draw.ico \
	math_app.ico:icons/math.ico \
	base_app.ico:icons/base.ico \
	oasis-text.ico:icons/doc-text.ico \
	oasis-text-template.ico:icons/doc-text-template.ico \
	oasis-spreadsheet.ico:icons/doc-spreadsheet.ico \
	oasis-spreadsheet-template.ico:icons/doc-spreadsheet-template.ico \
	oasis-drawing.ico:icons/doc-drawing.ico \
	oasis-drawing-template.ico:icons/doc-drawing-template.ico \
	oasis-presentation.ico:icons/doc-presentation.ico \
	oasis-presentation-template.ico:icons/doc-presentation-template.ico \
	oasis-master-document.ico:icons/doc-master-document.ico \
	oasis-web-template.ico:icons/doc-web-template.ico \
	oasis-database.ico:icons/doc-database.ico \
	oasis-formula.ico:icons/doc-formula.ico \
	oxt-extension.ico:icons/doc-extension.ico \

esilk_brand_MSI := \
	Banner.bmp:installer/banner.bmp \
	Image.bmp:installer/dialog.bmp \

# icon theme images that show the product logo, under ESILK_BRAND_DIR/icon-overlay (brand-manifest.json
# "theme_overlay"); cmd/sc_about.png is a links.txt alias of res/mainapp_16_8.png in every theme
esilk_brand_THEME_IMAGES := \
	res/mainapp_16.png \
	res/mainapp_16_8.png \
	res/mainapp_32.png \
	res/mainapp_32_8.png \
	res/mainapp_48_8.png \

esilk_brand_name = $(word 1,$(subst :, ,$(1)))
esilk_brand_file = $(word 2,$(subst :, ,$(1)))

# $(call esilk_brand_stage_rule,staged path under STAGEDIR,source file): copy without keeping the source time
# stamp, so a staged file is newer than everything built from an earlier one (gb_Deliver copies the staged time
# stamp on to instdir, so a no-op make stays a no-op).
define esilk_brand_stage_rule
$(esilk_brand_STAGEDIR)/$(1) : $(2) $(esilk_brand_STAMP)
	$$(call gb_Output_announce,EsilkBrand/$(1),$$(true),CPY,1)
	mkdir -p $$(dir $$@) && cp -f $$< $$@

endef

ifneq ($(strip $(ESILK_BRAND_DIR)),)

esilk_brand_DIR := $(patsubst %/,%,$(subst \,/,$(strip $(ESILK_BRAND_DIR))))

ifneq ($(words $(esilk_brand_DIR)),1)
$(error ESILK_BRAND_DIR must be a single path without spaces)
endif
ifeq ($(filter /% $(foreach d,A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z,$(d):/%),$(esilk_brand_DIR)),)
$(error ESILK_BRAND_DIR must be an absolute path: $(esilk_brand_DIR))
endif
# Outside the tree, whatever the spelling (case, 8.3 short names): no ancestor may be a LibreOffice source or
# build tree. $(call esilk_brand_ancestors,dir) = dir and its parents, up to the drive or filesystem root.
esilk_brand_parent = $(patsubst %/,%,$(dir $(1)))
esilk_brand_ancestors = $(1)$(if $(findstring /,$(call esilk_brand_parent,$(1))), $(call esilk_brand_ancestors,$(call esilk_brand_parent,$(1))))
esilk_brand_INSIDE := $(firstword \
	$(foreach d,$(call esilk_brand_ancestors,$(esilk_brand_DIR)),\
		$(if $(wildcard $(d)/config_host.mk $(d)/solenv/gbuild/gbuild.mk),$(d))) \
	$(foreach t,$(SRCDIR) $(BUILDDIR) $(patsubst %/workdir,%,$(WORKDIR)) $(patsubst %/instdir,%,$(INSTDIR)),\
		$(if $(filter $(t) $(t)/%,$(esilk_brand_DIR)),$(t))))
ifneq ($(esilk_brand_INSIDE),)
$(error ESILK_BRAND_DIR must stay outside the LibreOffice source/build tree $(esilk_brand_INSIDE))
endif

esilk_brand_MANIFEST := $(esilk_brand_DIR)/brand-manifest.json
ifeq ($(wildcard $(esilk_brand_MANIFEST)),)
$(error ESILK_BRAND_DIR: $(esilk_brand_MANIFEST) missing)
endif

# "pack": "<dir>" of the manifest (json.dumps layout: one key per line, ": " separator)
esilk_brand_PACK := $(patsubst "pack":"%"$(COMMA),%,$(filter "pack":%,$(subst ": ",":",$(file <$(esilk_brand_MANIFEST)))))
ifneq ($(words $(esilk_brand_PACK)),1)
$(error $(esilk_brand_MANIFEST): no "pack" entry)
endif
esilk_brand_PACK_SRC := $(esilk_brand_DIR)/$(esilk_brand_PACK)

# Brand pack: what configure would have set for --with-branding=$(esilk_brand_PACK_SRC).
export CUSTOM_BRAND_IMAGES := $(BRAND_INTRO_IMAGES) logo.svg logo_inverted.svg logo-sc.svg logo-sc_inverted.svg \
	about.svg donate1.png donate2.png
export DEFAULT_BRAND_IMAGES :=

esilk_brand_MISSING := $(filter-out $(wildcard \
		$(foreach pair,$(esilk_brand_ICONS) $(esilk_brand_MSI),$(esilk_brand_DIR)/$(call esilk_brand_file,$(pair))) \
		$(addprefix $(esilk_brand_DIR)/icon-overlay/,$(esilk_brand_THEME_IMAGES)) \
		$(addprefix $(esilk_brand_PACK_SRC)/,$(CUSTOM_BRAND_IMAGES) progress.conf)),\
	$(foreach pair,$(esilk_brand_ICONS) $(esilk_brand_MSI),$(esilk_brand_DIR)/$(call esilk_brand_file,$(pair))) \
	$(addprefix $(esilk_brand_DIR)/icon-overlay/,$(esilk_brand_THEME_IMAGES)) \
	$(addprefix $(esilk_brand_PACK_SRC)/,$(CUSTOM_BRAND_IMAGES) progress.conf))
ifneq ($(esilk_brand_MISSING),)
$(error ESILK_BRAND_DIR is incomplete, missing: $(esilk_brand_MISSING))
endif

# progress.conf is a shell fragment of KEY="value" lines without spaces (configure sources it).
esilk_brand_PROGRESS := $(file <$(esilk_brand_PACK_SRC)/progress.conf)
esilk_brand_progress = $(patsubst $(1)="%",%,$(filter $(1)=%,$(esilk_brand_PROGRESS)))
$(foreach key,PROGRESSBARCOLOR PROGRESSSIZE PROGRESSPOSITION PROGRESSFRAMECOLOR PROGRESSTEXTCOLOR PROGRESSTEXTBASELINE,\
	$(eval export $(key) := $(call esilk_brand_progress,$(key))))

# Icons and MSI bitmaps are staged under their upstream names, the theme images under their image names.
$(foreach pair,$(esilk_brand_ICONS),\
	$(eval $(call esilk_brand_stage_rule,icons/$(call esilk_brand_name,$(pair)),$(esilk_brand_DIR)/$(call esilk_brand_file,$(pair)))))
$(foreach pair,$(esilk_brand_MSI),\
	$(eval $(call esilk_brand_stage_rule,msi/$(call esilk_brand_name,$(pair)),$(esilk_brand_DIR)/$(call esilk_brand_file,$(pair)))))
$(foreach image,$(esilk_brand_THEME_IMAGES),\
	$(eval $(call esilk_brand_stage_rule,icon-overlay/$(image),$(esilk_brand_DIR)/icon-overlay/$(image))))

# $(call gb_WinResTarget_use_esilk_brand_icons,winrestarget,icon file names under sysui/desktop/icons)
define gb_WinResTarget_use_esilk_brand_icons
$(call gb_WinResTarget_get_target,$(1)) : INCLUDE := -I$(esilk_brand_STAGEDIR) $$(INCLUDE)
$(call gb_WinResTarget_get_target,$(1)) : $(addprefix $(esilk_brand_STAGEDIR)/icons/,$(2))
ifeq ($(gb_FULLDEPS),$(true))
$(call gb_WinResTarget_get_dep_target,$(1)) : INCLUDE := -I$(esilk_brand_STAGEDIR) $$(INCLUDE)
endif

endef

# instsetoo_native/CustomTarget_install.mk: prerequisites and copy commands of the msi_templates/*/Binary dirs
# (the staged ARP icon is listed so that it exists before make_installer runs).
esilk_brand_MSI_DEPS := $(esilk_brand_STAMP) $(esilk_brand_STAGEDIR)/icons/soffice.ico \
	$(foreach pair,$(esilk_brand_MSI),$(esilk_brand_STAGEDIR)/msi/$(call esilk_brand_name,$(pair)))
esilk_brand_MSI_COPY := $(foreach pair,$(esilk_brand_MSI),\
	&& cp -f $(esilk_brand_STAGEDIR)/msi/$(call esilk_brand_name,$(pair)) $(call esilk_brand_name,$(pair)))

# postprocess/CustomTarget_images.mk: pack_images.py takes the first custom path that has an image, so this
# directory goes before the theme's own (PNG themes only; the *_svg themes keep their .svg files).
esilk_brand_IMAGES_CUSTOM := -c $(esilk_brand_STAGEDIR)/icon-overlay
esilk_brand_IMAGES_DEPS := $(esilk_brand_STAMP) $(addprefix $(esilk_brand_STAGEDIR)/icon-overlay/,$(esilk_brand_THEME_IMAGES))

# read by solenv/bin/modules/installer/windows/idtglobal.pm (Icon table entry soffice.ico = ARPPRODUCTICON)
export ESILK_BRAND_ARP_ICON := $(esilk_brand_STAGEDIR)/icons/soffice.ico

else # ESILK_BRAND_DIR unset

# the pack configure found (empty without --with-branding: then desktop/Package_branding.mk delivers the
# default images and nothing is staged; never the staged copy itself, should a sub-make inherit it)
esilk_brand_PACK_SRC := $(filter-out $(esilk_brand_STAGEDIR)/pack,$(strip $(CUSTOM_BRAND_DIR)))

define gb_WinResTarget_use_esilk_brand_icons
$(call gb_WinResTarget_get_target,$(1)) : $(esilk_brand_STAMP)

endef

esilk_brand_MSI_DEPS := $(esilk_brand_STAMP)
esilk_brand_MSI_COPY :=
esilk_brand_IMAGES_CUSTOM :=
esilk_brand_IMAGES_DEPS := $(esilk_brand_STAMP)
ESILK_BRAND_ARP_ICON :=
unexport ESILK_BRAND_ARP_ICON

endif

# The brand pack reaches instdir through a staged copy (desktop/Package_branding_custom.mk reads
# CUSTOM_BRAND_DIR). gb_Deliver copies when the source is newer than the installed file; the staged copies are
# fresh whenever the stamp or a source changes, so instdir always gets the selected pack, also when that pack's
# files are older than the installed ones (another brand directory, back to the configured pack, ...).
ifneq ($(esilk_brand_PACK_SRC),)
$(foreach image,$(CUSTOM_BRAND_IMAGES),\
	$(eval $(call esilk_brand_stage_rule,pack/$(image),$(esilk_brand_PACK_SRC)/$(image))))
export CUSTOM_BRAND_DIR := $(esilk_brand_STAGEDIR)/pack
endif

# A restage starts from an empty overlay directory (pack_images.py reads the whole directory).
$(esilk_brand_STAMP) : $(gb_Helper_PHONY)
	mkdir -p $(dir $@) && \
	printf '%s\n' 'ESILK_BRAND_DIR=$(strip $(ESILK_BRAND_DIR))' 'pack=$(esilk_brand_PACK_SRC)' > $@.tmp && \
	if cmp -s $@.tmp $@; then rm $@.tmp; else rm -rf $(esilk_brand_STAGEDIR)/icon-overlay && mv $@.tmp $@; fi

# vim: set noet sw=4 ts=4:
