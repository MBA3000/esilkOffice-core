/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4; fill-column: 100 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include <sfx2/AdditionsDialogHelper.hxx>
#include <i18nlangtag/languagetag.hxx>
#include <officecfg/Office/Common.hxx>
#include <openuriexternally.hxx>
#include <rtl/uri.hxx>
#include <unotools/configmgr.hxx>
#include <vcl/abstdlg.hxx>
#include <vcl/weld/Dialog.hxx>

void AdditionsDialogHelper::RunAdditionsDialog(weld::Window* pParent, const OUString& rAdditionsTag)
{
    // esilk: the Additions dialog lists LibreOffice extensions from
    // extensions.libreoffice.org. A derived product opens its own extensions
    // page (Office.Common/Menus/ExtensionsURL) instead, with the same query as
    // the Start Center Extensions button plus the requested category.
    if (utl::ConfigManager::getProductName() != "LibreOffice")
    {
        OUString sURL = officecfg::Office::Common::Menus::ExtensionsURL::get() + "?LOvers="
                        + utl::ConfigManager::getProductVersion() + "&LOlocale="
                        + LanguageTag(utl::ConfigManager::getUILocale()).getBcp47();
        if (!rAdditionsTag.isEmpty())
            sURL += "&tag="
                    + rtl::Uri::encode(rAdditionsTag, rtl_UriCharClassUricNoSlash,
                                       rtl_UriEncodeIgnoreEscapes, RTL_TEXTENCODING_UTF8);
        sfx2::openUriExternally(sURL, true, pParent);
        return;
    }

    VclAbstractDialogFactory* pFact = VclAbstractDialogFactory::Create();
    VclPtr<AbstractAdditionsDialog> pDialog = pFact->CreateAdditionsDialog(pParent, rAdditionsTag);
    pDialog->StartExecuteAsync(
        [pDialog](sal_Int32 /*nResult*/) -> void { pDialog->disposeOnce(); });
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab cinoptions=b1,g0,N-s cinkeys+=0=break: */
