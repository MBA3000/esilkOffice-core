# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# This file incorporates work covered by the following license notice:
#
#   Licensed to the Apache Software Foundation (ASF) under one or more
#   contributor license agreements. See the NOTICE file distributed
#   with this work for additional information regarding copyright
#   ownership. The ASF licenses this file to you under the Apache
#   License, Version 2.0 (the "License"); you may not use this file
#   except in compliance with the License. You may obtain a copy of
#   the License at http://www.apache.org/licenses/LICENSE-2.0 .
#

# Overview of dependencies and tasks of AllLangMoTarget
#
# target                task                depends on
# AllLangMoTarget      nothing              MoTarget for all active langs
# MoTarget             running msgfmt

# MoTarget

$(call gb_MoTarget_get_clean_target,%) :
	$(call gb_Output_announce,$*,$(false),RES,2)
	$(call gb_Helper_abbreviate_dirs,\
		rm -f \
			$(call gb_MoTarget_get_target,$*) \
			$(call gb_MoTarget_get_install_target,$*))

# esilk: UI po overlays (esilk/l10n/README.md). When
# esilk/l10n/translations/source/<lang>/<polocation>/messages.po exists,
# esilk/l10n/merge_po.py (run by the build's python after check_overlays.py)
# writes <target>.po: the upstream header, the overlay entries, and the upstream
# entries the overlay does not replace (same msgctxt + msgid, or named by an
# "esilk-replaces" comment). msgfmt then compiles that file instead of the
# upstream po: the overlay translation wins, an untranslated upstream message
# gets the overlay translation, and the old entry of a rewritten en-US string
# leaves the .mo.
# $(call gb_MoTarget_get_po,lang,polocation): the upstream po file
gb_MoTarget_get_po = $(gb_POLOCATION)/$(1)/$(2)/messages.po
# $(call gb_MoTarget_get_overlay,lang,polocation): its overlay, if one exists
gb_MoTarget_get_overlay = $(call gb_POLOCATION_get_overlays,$(call gb_MoTarget_get_po,$(1),$(2)))

# wsl1 seems to have issues with writing to stdout/pipes when running with high parallelism
# so as a workaround run the two statements in a single command run by a shell
$(call gb_MoTarget_get_target,%) : $(gb_Helper_MISCDUMMY)
	$(call gb_Output_announce,$*,$(true),MO ,2)
	$(call gb_Trace_StartRange,$*,MO )
	$(call gb_POLOCATION_check_overlays,$(call gb_MoTarget_get_po,$(LANGUAGE),$(POLOCATION)))
	$(call gb_Helper_abbreviate_dirs,mkdir -p $(dir $@)) && \
	$(if $(call gb_MoTarget_get_overlay,$(LANGUAGE),$(POLOCATION)),\
		$(call gb_ExternalExecutable_get_command,python) $(SRCDIR)/esilk/l10n/merge_po.py \
			$(call gb_MoTarget_get_overlay,$(LANGUAGE),$(POLOCATION)) \
			$(call gb_MoTarget_get_po,$(LANGUAGE),$(POLOCATION)) $@.po && \
		$(call gb_Helper_wsl_path,$(WSL) /bin/sh -c "$(MSGUNIQ) --force-po $@.po | $(MSGFMT) - -o $@") && \
		rm -f $@.po,\
		$(call gb_Helper_wsl_path,$(WSL) /bin/sh -c "$(MSGUNIQ) --force-po $(call gb_MoTarget_get_po,$(LANGUAGE),$(POLOCATION)) | $(MSGFMT) - -o $@"))
	$(call gb_Trace_EndRange,$*,MO )

# $(call gb_MoTarget__add_overlay_deps,motarget,polocation,lang): rebuild the .mo
# when its overlay changes; the overlay check needs the build's python first.
define gb_MoTarget__add_overlay_deps
$(call gb_MoTarget_get_target,$(1)) : $(call gb_MoTarget_get_overlay,$(3),$(2)) \
	$(if $(call gb_MoTarget_get_overlay,$(3),$(2)),$(SRCDIR)/esilk/l10n/merge_po.py) \
	| $(call gb_POLOCATION_get_overlay_check_deps,$(call gb_MoTarget_get_po,$(3),$(2)))

endef

#$(info $(call gb_MoTarget_get_target,$(1)))
define gb_MoTarget_MoTarget
$(call gb_MoTarget_get_target,$(1)) : LIBRARY = $(2)
$(call gb_MoTarget_get_target,$(1)) : LANGUAGE = $(3)
$(call gb_MoTarget_get_target,$(1)) : POLOCATION = $(2)
$(call gb_AllLangMoTarget_get_clean_target,$(2)) : $(call gb_MoTarget_get_clean_target,$(1))
$(call gb_MoTarget__add_overlay_deps,$(1),$(2),$(3))

endef

# $(call gb_MoTarget_set_polocation,motarget,polocation,lang)
define gb_MoTarget_set_polocation
$(call gb_MoTarget_get_target,$(1)) : POLOCATION = $(2)
$(call gb_MoTarget__add_overlay_deps,$(1),$(2),$(3))

endef

# AllLangMoTarget

gb_AllLangMoTarget_LANGS := $(filter-out qtz,$(filter-out en-US,$(gb_WITH_LANG)))

define gb_AllLangMoTarget_set_langs
gb_AllLangMoTarget_LANGS := $(1)
endef

$(call gb_AllLangMoTarget_get_clean_target,%) :
	$(call gb_Helper_abbreviate_dirs,\
		rm -f $(call gb_AllLangMoTarget_get_target,$*))

$(call gb_AllLangMoTarget_get_target,%) :
	$(call gb_Helper_abbreviate_dirs,\
		mkdir -p $(dir $@) && touch $@)

gb_MoTarget_get_install_target = $(INSTROOT)/$(LIBO_SHARE_RESOURCE_FOLDER)/$(1).mo

define gb_AllLangMoTarget_AllLangMoTarget
ifeq (,$$(filter $(1),$$(gb_AllLangMoTarget_REGISTERED)))
$$(eval $$(call gb_Output_info,Currently known AllLangMoTargets are: $(sort $(gb_AllLangMoTarget_REGISTERED)),ALL))
$$(eval $$(call gb_Output_error,AllLangMoTarget $(1) must be registered in Repository.mk))
endif
$(foreach lang,$(gb_AllLangMoTarget_LANGS),\
	$(call gb_MoTarget_MoTarget,$(1)$(lang),$(1),$(lang)))

$(foreach lang,$(gb_AllLangMoTarget_LANGS),\
$(call gb_Helper_install,$(call gb_AllLangMoTarget_get_target,$(1)), \
	$(call gb_MoTarget_get_install_target,$(shell $(SRCDIR)/solenv/bin/localestr $(lang))/LC_MESSAGES/$(1)), \
	$(call gb_MoTarget_get_target,$(1)$(lang))))

$$(eval $$(call gb_Module_register_target,$(call gb_AllLangMoTarget_get_target,$(1)),$(call gb_AllLangMoTarget_get_clean_target,$(1))))
$(call gb_Helper_make_userfriendly_targets,$(1),AllLangMoTarget)
$(call gb_Postprocess_register_target,AllResources,AllLangMoTarget,$(1))

endef

define gb_AllLangMoTarget_set_polocation
$(foreach lang,$(gb_AllLangMoTarget_LANGS),\
        $(call gb_MoTarget_set_polocation,$(1)$(lang),$(2),$(lang)))

endef

# vim: set noet sw=4: 
