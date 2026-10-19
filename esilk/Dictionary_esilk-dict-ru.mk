# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# esilkOffice: Russian spelling dictionary as a bundled extension
# (share/extensions/esilk-dict-ru), independent of --with-myspell-dicts.
#
# Only parts whose licence is compatible with the MPL subset build ship:
# ru_RU.aff/.dic (BSD-style, Alexander I. Lebedev; README_ru_RU.txt carries the
# notice). Not shipped: hyph_ru_RU.dic (upstream license.xml: licence
# "unknown"), the thesaurus (LGPL) and the Lightproof grammar checker.
# The data comes unmodified from the dictionaries submodule.

ifeq ($(wildcard $(SRCDIR)/dictionaries/ru_RU/ru_RU.dic),)
$(error esilk: the dictionaries submodule is not checked out (git submodule update --init dictionaries))
endif

$(eval $(call gb_Dictionary_Dictionary,esilk-dict-ru,esilk/dictionaries/ru))

$(eval $(call gb_Dictionary_add_root_files,esilk-dict-ru,\
	dictionaries/ru_RU/README_ru_RU.txt \
	dictionaries/ru_RU/ru_RU.aff \
	dictionaries/ru_RU/ru_RU.dic \
))

# vim: set noet sw=4 ts=4:
