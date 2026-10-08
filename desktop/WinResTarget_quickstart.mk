# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_WinResTarget_WinResTarget,quickstart/QuickStart))

$(eval $(call gb_WinResTarget_set_include,quickstart/QuickStart,\
    $$(INCLUDE) \
    -I$(SRCDIR)/desktop/win32/source/QuickStart \
    -I$(SRCDIR)/sysui/desktop \
))

# esilk: the icons come from ESILK_BRAND_DIR when it is set (esilk/Brand.mk)
$(eval $(call gb_WinResTarget_use_esilk_brand_icons,quickstart/QuickStart,soffice.ico))

$(eval $(call gb_WinResTarget_add_dependencies,quickstart/QuickStart,\
    sysui/desktop/icons/soffice.ico \
))

$(eval $(call gb_WinResTarget_set_rcfile,quickstart/QuickStart,desktop/win32/source/QuickStart/QuickStart))

# vim: set ts=4 sw=4 et:
