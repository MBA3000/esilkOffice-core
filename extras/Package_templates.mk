# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

$(eval $(call gb_Package_Package,extras_templates,$(gb_CustomTarget_workdir)/extras/source/templates))

$(eval $(call gb_Package_add_files_with_dir,extras_templates,$(LIBO_SHARE_FOLDER)/template/common,\
	offimisc/Businesscard-with-logo.ott \
	styles/Default.ott \
	styles/Modern.ott \
	styles/Simple.ott \
	draw/bpmn.otg \
))

# esilk: no l10n/zh_CN_ott_normal.ott and l10n/ja_ott_normal.ott. esilkOffice ships
# kk/ru/en only; the template manager listed them as "Japanese normal" and
# "Simplified Chinese normal" (pilot-readiness audit Q07).
# esilk: no officorr/Modern_business_letter_*.ott, personal/CV.ott and
# personal/Resume1page.ott either. The KZ templates (kzdocs) carry the business
# letter and the resume, so the stock ones only duplicated them in the template
# manager (pilot-readiness audit R2-20).

# vim: set noet sw=4 ts=4:
