# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# The proprietary extension is supplied externally, never from this repository.
esilk_kz_calc_oxt := $(patsubst %/,%,$(strip $(ESILK_OXT_DIR)))/esilk-kz-calc.oxt

ifeq ($(wildcard $(esilk_kz_calc_oxt)),)
$(error ESILK_OXT_DIR must contain the external esilk-kz-calc.oxt artifact)
endif

$(eval $(call gb_ExtensionPackage_ExtensionPackage,esilk-kz-calc,$(esilk_kz_calc_oxt)))

# vim: set noet sw=4 ts=4:
