# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_ExternalPackage_ExternalPackage,fonts_roboto,font_roboto))

# unhinted/static is the full-glyph set (it has the tenge sign U+20B8; web/static does not).
# esilkOffice: Regular, Bold, Italic, BoldItalic plus Light and Medium (stat.gov.kz and Office
# cloud documents name "Roboto Light" / "Roboto Medium" as separate families).
$(eval $(call gb_ExternalPackage_add_unpacked_files,fonts_roboto,$(LIBO_SHARE_FOLDER)/fonts/truetype,\
	unhinted/static/Roboto-Bold.ttf \
	unhinted/static/Roboto-BoldItalic.ttf \
	unhinted/static/Roboto-Italic.ttf \
	unhinted/static/Roboto-Light.ttf \
	unhinted/static/Roboto-Medium.ttf \
	unhinted/static/Roboto-Regular.ttf \
))

# vim: set noet sw=4 ts=4:
