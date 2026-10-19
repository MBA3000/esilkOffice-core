# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_Module_Module,esilk))

$(eval $(call gb_Module_add_targets,esilk,\
	ExtensionPackage_esilk-kz-calc \
	Package_esilk-defaults \
))

# Bundled spelling dictionaries (ru, en-US); the dictionaries submodule must be
# checked out. Never a Kazakh dictionary: the 2009 kk_KZ dictionary is banned
# (owner decision), and tools/build/check-msi-branding.ps1 in the private repo
# fails an MSI that contains one.
$(eval $(call gb_Module_add_l10n_targets,esilk,\
	Dictionary_esilk-dict-en \
	Dictionary_esilk-dict-ru \
))

# vim: set noet sw=4 ts=4:
