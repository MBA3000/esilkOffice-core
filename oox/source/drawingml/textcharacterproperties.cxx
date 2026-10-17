/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following license notice:
 *
 *   Licensed to the Apache Software Foundation (ASF) under one or more
 *   contributor license agreements. See the NOTICE file distributed
 *   with this work for additional information regarding copyright
 *   ownership. The ASF licenses this file to you under the Apache
 *   License, Version 2.0 (the "License"); you may not use this file
 *   except in compliance with the License. You may obtain a copy of
 *   the License at http://www.apache.org/licenses/LICENSE-2.0 .
 */

#include <drawingml/textcharacterproperties.hxx>
#include <com/sun/star/lang/Locale.hpp>
#include <com/sun/star/awt/FontFamily.hpp>
#include <com/sun/star/awt/FontPitch.hpp>
#include <com/sun/star/awt/FontSlant.hpp>
#include <com/sun/star/awt/FontWeight.hpp>
#include <com/sun/star/i18n/ScriptType.hpp>
#include <comphelper/sequence.hxx>
#include <i18nlangtag/languagetag.hxx>
#include <i18nlangtag/mslangid.hxx>
#include <editeng/escapementitem.hxx>
#include <docmodel/uno/UnoComplexColor.hxx>
#include <oox/helper/helper.hxx>
#include <oox/helper/propertyset.hxx>
#include <oox/helper/graphichelper.hxx>
#include <oox/core/xmlfilterbase.hxx>
#include <oox/drawingml/drawingmltypes.hxx>
#include <oox/drawingml/theme.hxx>
#include <oox/token/properties.hxx>
#include <oox/token/tokens.hxx>

using ::oox::core::XmlFilterBase;
using namespace ::com::sun::star;
using namespace ::com::sun::star::uno;
using namespace ::com::sun::star::beans;

namespace oox::drawingml {

namespace {

/** esilk: ISO 15924 script tag of the Office supplemental theme font list for a run language,
    limited to scripts that LibreOffice draws with the Western ("Latin") font. Same language
    list as writerfilter::dmapper fromLCIDToScriptTag() for "Cyrl". */
std::u16string_view lclGetLatinSupplementalScript( const OUString& rLang )
{
    LanguageTag aTag(rLang);
    // A tag with an explicit script, e.g. "sr-Cyrl" or "kk-Cyrl-KZ".
    if (aTag.getScript() == u"Cyrl")
        return u"Cyrl";
    switch (static_cast<sal_uInt16>(aTag.getLanguageType()))
    {
        case 0x6c1a: // Serbian Cyrillic (script-only tag sr-Cyrl)
        case 0x641a: // Bosnian Cyrillic (bs-Cyrl)
        case 0x783f: // Kazakh Cyrillic (kk-Cyrl)
        case 0x742c: // Azerbaijani Cyrillic (az-Cyrl)
        case 0x7843: // Uzbek Cyrillic (uz-Cyrl)
        case 0x7850: // Mongolian Cyrillic (mn-Cyrl)
        case 0x419: // Russian
        case 0x402: // Bulgarian
        case 0x281a: // Serbian Cyrillic
        case 0x422: // Ukrainian
        case 0x819: // Russian (Moldova)
        case 0xc1a: // Serbian Cyrillic (Serbia and Montenegro)
        case 0x1c1a: // Serbian Cyrillic (Bosnia and Herzegovina)
        case 0x201a: // Bosnian Cyrillic
        case 0x301a: // Serbian Cyrillic (Montenegro)
        case 0x423: // Belarusian
        case 0x428: // Tajik
        case 0x82c: // Azerbaijani Cyrillic
        case 0x42f: // Macedonian
        case 0x43f: // Kazakh
        case 0x440: // Kyrgyz
        case 0x843: // Uzbek Cyrillic
        case 0x444: // Tatar
        case 0x450: // Mongolian Cyrillic
        case 0x46d: // Bashkir
        case 0x485: // Sakha
            return u"Cyrl";
        default:
            return {};
    }
}

/** esilk: PowerPoint draws a run whose latin font is the theme font (+mj-lt / +mn-lt) in the
    theme's supplemental font for the script of the run language (<a:font script="Cyrl"
    typeface="..."/>), e.g. Cyrillic text of a localized theme in Calibri although the theme's
    latin font (Tw Cen MT) has no Cyrillic glyphs. Returns that typeface, or an empty string. */
OUString lclResolveLatinSupplementalFont( const OUString& rTypeface, const std::optional<OUString>& roLang,
                                          const XmlFilterBase& rFilter )
{
    if (!roLang.has_value() || roLang->isEmpty())
        return OUString();
    sal_Int32 nScheme = 0;
    if (rTypeface == u"+mj-lt")
        nScheme = XML_major;
    else if (rTypeface == u"+mn-lt")
        nScheme = XML_minor;
    else
        return OUString();
    const Theme* pTheme = rFilter.getCurrentTheme();
    if (!pTheme)
        return OUString();
    std::u16string_view aScript = lclGetLatinSupplementalScript(*roLang);
    if (aScript.empty())
        return OUString();
    const auto& rSupplementalFontMap = pTheme->getSupplementalFontMap();
    auto it = rSupplementalFontMap.find(nScheme);
    if (it == rSupplementalFontMap.end())
        return OUString();
    for (const auto& [rScript, rSupplementalTypeface] : it->second)
        if (rScript == aScript && !rSupplementalTypeface.isEmpty())
            return rSupplementalTypeface;
    return OUString();
}

} // namespace

void TextCharacterProperties::assignUsed( const TextCharacterProperties& rSourceProps )
{
    // overwrite all properties existing in rSourceProps
    maHyperlinkPropertyMap.assignUsed( rSourceProps.maHyperlinkPropertyMap );
    maLatinFont.assignIfUsed( rSourceProps.maLatinFont );
    maLatinThemeFont.assignIfUsed( rSourceProps.maLatinThemeFont );
    maAsianFont.assignIfUsed( rSourceProps.maAsianFont );
    maAsianThemeFont.assignIfUsed( rSourceProps.maAsianThemeFont );
    maComplexFont.assignIfUsed( rSourceProps.maComplexFont );
    maComplexThemeFont.assignIfUsed( rSourceProps.maComplexThemeFont );
    maSymbolFont.assignIfUsed( rSourceProps.maSymbolFont );
    maHighlightColor.assignIfUsed( rSourceProps.maHighlightColor );
    maHighlightOOXColor.assignIfUsed( rSourceProps.maHighlightOOXColor );
    maUnderlineColor.assignIfUsed( rSourceProps.maUnderlineColor );
    assignIfUsed( moLang, rSourceProps.moLang );
    assignIfUsed( moHeight, rSourceProps.moHeight );
    assignIfUsed( moFontScale, rSourceProps.moFontScale);
    assignIfUsed( moSpacing, rSourceProps.moSpacing );
    assignIfUsed( moUnderline, rSourceProps.moUnderline );
    assignIfUsed( moBaseline, rSourceProps.moBaseline );
    assignIfUsed( moStrikeout, rSourceProps.moStrikeout );
    assignIfUsed( moCaseMap, rSourceProps.moCaseMap );
    assignIfUsed( moBold, rSourceProps.moBold );
    assignIfUsed( moItalic, rSourceProps.moItalic );
    assignIfUsed( moUnderlineLineFollowText, rSourceProps.moUnderlineLineFollowText );
    assignIfUsed( moUnderlineFillFollowText, rSourceProps.moUnderlineFillFollowText );
    assignIfUsed( moTextOutlineProperties, rSourceProps.moTextOutlineProperties);

    maTextEffectsProperties = rSourceProps.maTextEffectsProperties;
    mpEffectPropertiesPtr->assignUsed(*rSourceProps.mpEffectPropertiesPtr);
    maFillProperties.assignUsed( rSourceProps.maFillProperties );
}

bool TextCharacterProperties::getLatinFontData( OUString& rFontName, sal_Int16& rnFontPitch,
                                                sal_Int16& rnFontFamily, const XmlFilterBase& rFilter ) const
{
    bool bRet = maLatinFont.getFontData( rFontName, rnFontPitch, rnFontFamily, nullptr, rFilter );
    if (!bRet)
        // In case there is no direct font, try to look it up as a theme reference.
        bRet = maLatinThemeFont.getFontData( rFontName, rnFontPitch, rnFontFamily, nullptr, rFilter );
    if (bRet)
    {
        OUString aSupplementalFontName = lclResolveLatinSupplementalFont(
            maLatinFont.getTypeface(), moLang, rFilter);
        if (!aSupplementalFontName.isEmpty())
        {
            rFontName = aSupplementalFontName;
            rnFontPitch = awt::FontPitch::DONTKNOW;
            rnFontFamily = awt::FontFamily::DONTKNOW;
        }
    }
    return bRet;
}

void TextCharacterProperties::pushToPropMap( PropertyMap& rPropMap, const XmlFilterBase& rFilter ) const
{
    OUString aFontName;
    sal_Int16 nFontPitch = 0;
    sal_Int16 nFontFamily = 0;

    bool bRet = getLatinFontData( aFontName, nFontPitch, nFontFamily, rFilter );
    if (bRet)
    {
        rPropMap.setProperty( PROP_CharFontName, aFontName);
        rPropMap.setProperty( PROP_CharFontPitch, nFontPitch);
        rPropMap.setProperty( PROP_CharFontFamily, nFontFamily);
    }

    bRet = maAsianFont.getFontData( aFontName, nFontPitch, nFontFamily, nullptr, rFilter );
    if (!bRet)
        bRet = maAsianThemeFont.getFontData( aFontName, nFontPitch, nFontFamily, nullptr, rFilter );
    if (bRet)
    {
        rPropMap.setProperty( PROP_CharFontNameAsian, aFontName);
        rPropMap.setProperty( PROP_CharFontPitchAsian, nFontFamily);
        rPropMap.setProperty( PROP_CharFontFamilyAsian, nFontPitch);
    }

    bRet = maComplexFont.getFontData( aFontName, nFontPitch, nFontFamily, nullptr, rFilter );
    if (!bRet)
        bRet = maComplexThemeFont.getFontData( aFontName, nFontPitch, nFontFamily, nullptr, rFilter );
    if (bRet)
    {
        rPropMap.setProperty( PROP_CharFontNameComplex, aFontName);
        rPropMap.setProperty( PROP_CharFontPitchComplex, nFontPitch);
        rPropMap.setProperty( PROP_CharFontFamilyComplex, nFontFamily);
    }

    if ( maFillProperties.moFillType.has_value() )
    {
        Color aOOXColor = maFillProperties.getBestSolidColor();
        bool bContoured = false;

        // noFill doesn't exist for characters. Map noFill to 99% transparency
        if (maFillProperties.moFillType.value() == XML_noFill)
            aOOXColor.addTransformation(XML_alpha, 1000);

        // tdf#137438 Emulate text outline color/transparency.
        // If the outline color dominates, then use it as the text color.
        if (moTextOutlineProperties.has_value()
            && moTextOutlineProperties.value().maLineFill.moFillType.has_value()
            && moTextOutlineProperties.value().maLineFill.moFillType.value() != XML_noFill)
        {
            Color aLineColor = moTextOutlineProperties.value().maLineFill.getBestSolidColor();
            sal_Int16 nLineTransparency = aLineColor.getTransparency();

            // tdf#127696 If the text color is white (and the outline color doesn't dominate),
            //            then this is contoured text in LO.
            if (nLineTransparency < aOOXColor.getTransparency()
                || (bContoured = aOOXColor.getColor(rFilter.getGraphicHelper()) == COL_WHITE))
                aOOXColor = std::move(aLineColor);
        }
        rPropMap.setProperty(PROP_CharColor, aOOXColor.getColor(rFilter.getGraphicHelper()));

        // set theme color
        model::ComplexColor aComplexColor = aOOXColor.getComplexColor();
        sal_Int32 nToken = Color::getColorMapToken(aOOXColor.getSchemeColorName());
        if (nToken != -1)
        {
            rFilter.getGraphicHelper().getSchemeColorToken(nToken);
            model::ThemeColorType eThemeColorType = schemeTokenToThemeColorType(nToken);
            aComplexColor.setThemeColor(eThemeColorType);
        }
        rPropMap.setProperty(PROP_CharComplexColor, model::color::createXComplexColor(aComplexColor));
        rPropMap.setProperty(PROP_CharContoured, bContoured);

        if (aOOXColor.hasTransparency())
        {
            const auto nTransparency = aOOXColor.getTransparency();
            rPropMap.setProperty(PROP_CharTransparence, nTransparency);

            // WORKAROUND: Fully transparent white has the same value as COL_AUTO, avoid collision
            if (nTransparency == 100
                && aOOXColor.getColor(rFilter.getGraphicHelper()).GetRGBColor() == COL_AUTO.GetRGBColor())
                rPropMap.setProperty(PROP_CharColor, ::Color(ColorTransparency, 0xFFFFFFFE));
        }
    }

    if( moLang.has_value() && !moLang.value().isEmpty() )
    {
        LanguageTag aTag(moLang.value());
        lang::Locale aLocale(aTag.getLocale());
        switch(MsLangId::getScriptType(aTag.getLanguageType()))
        {
            case css::i18n::ScriptType::LATIN:
                rPropMap.setProperty( PROP_CharLocale, aLocale);break;
            case css::i18n::ScriptType::ASIAN:
                rPropMap.setProperty( PROP_CharLocaleAsian, aLocale);break;
            case css::i18n::ScriptType::COMPLEX:
                rPropMap.setProperty( PROP_CharLocaleComplex, aLocale);break;
        }
    }

    if( moHeight.has_value() )
    {
        float fHeight = GetFontHeight( moHeight.value() );
        if (moFontScale.has_value())
            fHeight *= (moFontScale.value() / 100000);
        rPropMap.setProperty( PROP_CharHeight, fHeight);
        rPropMap.setProperty( PROP_CharHeightAsian, fHeight);
        rPropMap.setProperty( PROP_CharHeightComplex, fHeight);
    }

    rPropMap.setProperty( PROP_CharKerning, static_cast<sal_Int16>(GetTextSpacingPoint( moSpacing.value_or( 0 ) )));

    rPropMap.setProperty( PROP_CharUnderline, GetFontUnderline( moUnderline.value_or( XML_none ) ));
    rPropMap.setProperty( PROP_CharStrikeout, GetFontStrikeout( moStrikeout.value_or( XML_noStrike ) ));
    rPropMap.setProperty( PROP_CharCaseMap, GetCaseMap( moCaseMap.value_or( XML_none ) ));

    if( moBaseline.has_value() ) {
        rPropMap.setProperty( PROP_CharEscapement, sal_Int16(moBaseline.value_or( 0 ) / 1000));
        rPropMap.setProperty( PROP_CharEscapementHeight, sal_Int8(DFLT_ESC_PROP));
    } else {
        rPropMap.setProperty( PROP_CharEscapement, sal_Int16(0));
        rPropMap.setProperty( PROP_CharEscapementHeight, sal_Int8(100)); // 100%
    }

    float fWeight = moBold.value_or( false ) ? awt::FontWeight::BOLD : awt::FontWeight::NORMAL;
    rPropMap.setProperty( PROP_CharWeight, fWeight);
    rPropMap.setProperty( PROP_CharWeightAsian, fWeight);
    rPropMap.setProperty( PROP_CharWeightComplex, fWeight);

    awt::FontSlant eSlant = moItalic.value_or( false ) ? awt::FontSlant_ITALIC : awt::FontSlant_NONE;
    rPropMap.setProperty( PROP_CharPosture, eSlant);
    rPropMap.setProperty( PROP_CharPostureAsian, eSlant);
    rPropMap.setProperty( PROP_CharPostureComplex, eSlant);

    bool bUnderlineFillFollowText = moUnderlineFillFollowText.value_or( false );
    if( moUnderline.has_value() && maUnderlineColor.isUsed() && !bUnderlineFillFollowText )
    {
        rPropMap.setProperty( PROP_CharUnderlineHasColor, true);
        rPropMap.setProperty( PROP_CharUnderlineColor, maUnderlineColor.getRGBColor());
        rPropMap.setProperty( PROP_CharUnderlineComplexColor, model::color::createXComplexColor(maUnderlineColor));
    }
    else
    {
        rPropMap.setProperty( PROP_CharUnderlineHasColor, false);
        rPropMap.setProperty( PROP_CharUnderlineColor, sal_Int32(-1));
    }

    if (maHighlightColor.isUsed() && !maHighlightColor.isTransparent())
    {
        rPropMap.setProperty(PROP_CharBackColor, maHighlightOOXColor.getColor( rFilter.getGraphicHelper() ));
        rPropMap.setProperty(PROP_CharBackgroundComplexColor, model::color::createXComplexColor(maHighlightColor));
    }
    else
        rPropMap.setProperty( PROP_CharBackColor, sal_Int32(-1));
}

static void pushToGrabBag( PropertySet& rPropSet, const std::vector<PropertyValue>& aVectorOfPropertyValues )
{
    if (!rPropSet.hasProperty(PROP_CharInteropGrabBag) || aVectorOfPropertyValues.empty())
        return;
    Sequence<PropertyValue> aGrabBag;
    Any aAnyGrabBag = rPropSet.getAnyProperty(PROP_CharInteropGrabBag);
    aAnyGrabBag >>= aGrabBag;

    rPropSet.setAnyProperty(PROP_CharInteropGrabBag, Any(comphelper::concatSequences(aGrabBag, aVectorOfPropertyValues)));
}

void TextCharacterProperties::pushToPropSet( PropertySet& rPropSet, const XmlFilterBase& rFilter ) const
{
    PropertyMap aPropMap;
    pushToPropMap( aPropMap, rFilter );
    rPropSet.setProperties( aPropMap );
    pushToGrabBag(rPropSet, maTextEffectsProperties);
}

float TextCharacterProperties::getCharHeightPoints( float fDefault ) const
{
    return moHeight.has_value() ? GetFontHeight( moHeight.value() ) : fDefault;
}

} // namespace oox::drawingml

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
