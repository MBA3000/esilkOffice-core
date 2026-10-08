# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_WinResTarget_WinResTarget,sofficebin/officeloader))

$(eval $(call gb_WinResTarget_set_include,sofficebin/officeloader,\
    $$(INCLUDE) \
    -I$(SRCDIR)/sysui/desktop \
))

# esilk: the icons come from ESILK_BRAND_DIR when it is set (esilk/Brand.mk)
$(eval $(call gb_WinResTarget_use_esilk_brand_icons,sofficebin/officeloader,\
    soffice.ico \
    oasis-text.ico \
    oasis-text-template.ico \
    oasis-spreadsheet.ico \
    oasis-spreadsheet-template.ico \
    oasis-drawing.ico \
    oasis-drawing-template.ico \
    oasis-presentation.ico \
    oasis-presentation-template.ico \
    oasis-master-document.ico \
    oasis-web-template.ico \
    oasis-database.ico \
    oasis-formula.ico \
    oxt-extension.ico \
))

$(eval $(call gb_WinResTarget_add_defs,sofficebin/officeloader,\
    -DRES_APP_ICON=icons/soffice.ico \
))

$(eval $(call gb_WinResTarget_add_dependencies,sofficebin/officeloader,\
    sysui/desktop/icons/soffice.ico \
	sysui/desktop/icons/oasis-database.ico \
	sysui/desktop/icons/oasis-drawing-template.ico \
	sysui/desktop/icons/oasis-drawing.ico \
	sysui/desktop/icons/oasis-formula.ico \
	sysui/desktop/icons/oasis-master-document.ico \
	sysui/desktop/icons/oasis-presentation-template.ico \
	sysui/desktop/icons/oasis-presentation.ico \
	sysui/desktop/icons/oasis-spreadsheet-template.ico \
	sysui/desktop/icons/oasis-spreadsheet.ico \
	sysui/desktop/icons/oasis-text-template.ico \
	sysui/desktop/icons/oasis-text.ico \
	sysui/desktop/icons/oasis-web-template.ico \
	sysui/desktop/icons/database.ico \
	sysui/desktop/icons/drawing-template.ico \
	sysui/desktop/icons/drawing.ico \
	sysui/desktop/icons/formula.ico \
	sysui/desktop/icons/master-document.ico \
	sysui/desktop/icons/presentation-template.ico \
	sysui/desktop/icons/presentation.ico \
	sysui/desktop/icons/spreadsheet-template.ico \
	sysui/desktop/icons/spreadsheet.ico \
	sysui/desktop/icons/text-template.ico \
	sysui/desktop/icons/text.ico \
	sysui/desktop/icons/oxt-extension.ico \
))

$(eval $(call gb_WinResTarget_set_rcfile,sofficebin/officeloader,desktop/util/officeloader))

# vim: set ts=4 sw=4 et:
