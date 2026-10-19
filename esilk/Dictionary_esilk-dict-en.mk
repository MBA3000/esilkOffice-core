# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# esilkOffice: English (USA) spelling dictionary, hyphenation patterns and
# thesaurus as a bundled extension (share/extensions/esilk-dict-en).
#
# Upstream leaves the whole dict-en out of an MPL subset build on Windows
# (dictionaries/Module_dictionaries.mk) because the package mixes licences.
# This package takes only the permissively licensed parts:
# - en_US.aff/.dic: SCOWL (Kevin Atkinson, permissive) + Ispell affix (BSD),
#   README_en_US.txt;
# - hyph_en_US.dic: BSD-style, README_hyph_en_US.txt;
# - th_en_US_v2.dat: WordNet 2.1 licence, WordNet_license.txt.
# Not shipped: en_GB/en_AU/en_CA/en_ZA spelling (en_GB is LGPL), the package
# licence.txt (GPL) and the Lightproof grammar checker.
# The data comes unmodified from the dictionaries submodule.

ifeq ($(wildcard $(SRCDIR)/dictionaries/en/en_US.dic),)
$(error esilk: the dictionaries submodule is not checked out (git submodule update --init dictionaries))
endif

$(eval $(call gb_Dictionary_Dictionary,esilk-dict-en,esilk/dictionaries/en))

$(eval $(call gb_Dictionary_add_root_files,esilk-dict-en,\
	dictionaries/en/README_en_US.txt \
	dictionaries/en/README_hyph_en_US.txt \
	dictionaries/en/WordNet_license.txt \
	dictionaries/en/en_US.aff \
	dictionaries/en/en_US.dic \
	dictionaries/en/hyph_en_US.dic \
))

$(eval $(call gb_Dictionary_add_thesaurus,esilk-dict-en,dictionaries/en/th_en_US_v2.dat))

# vim: set noet sw=4 ts=4:
