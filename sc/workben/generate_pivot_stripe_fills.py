#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Extract all 84 built-in pivot fill definitions from ECMA-376 presetTableStyles.xml.

Input: OfficeOpenXML-SpreadsheetMLStyles.zip inside the ECMA-376 Part1 download.
Output: data only, including unimplemented complex-layout regions for design review.
No Office, document import, network or native test. Missing fill means inherit, not white.
Usage: python generate_pivot_stripe_fills.py INPUT OUTPUT [INVENTORY.md]
"""
import math
import pathlib
import sys
import xml.etree.ElementTree as ET


ELEMENTS = (
    "wholeTable", "pageFieldLabels", "pageFieldValues", "firstColumnStripe", "secondColumnStripe",
    "firstRowStripe", "secondRowStripe", "firstColumn", "headerRow", "firstHeaderCell",
    "firstSubtotalColumn", "secondSubtotalColumn", "thirdSubtotalColumn", "blankRow",
    "firstSubtotalRow", "secondSubtotalRow", "thirdSubtotalRow", "firstColumnSubheading",
    "secondColumnSubheading", "thirdColumnSubheading", "firstRowSubheading", "secondRowSubheading",
    "thirdRowSubheading", "lastColumn", "totalRow", "lastHeaderCell", "firstTotalCell", "lastTotalCell",
)
FAMILIES = ("Light", "Medium", "Dark")
EXPECTED = tuple("PivotStyle%s%d" % (family, number) for family in FAMILIES for number in range(1, 29))
NONE = (-1, 0.0)


def presets(path):
    styles = {}
    for style in ET.parse(path).getroot():
        if not style.tag.startswith("PivotStyle"):
            continue
        if style.tag not in EXPECTED or style.tag in styles:
            raise ValueError("unknown or duplicate pivot preset: " + style.tag)
        dxfs = list(style.find("dxfs"))
        table = style.find("tableStyles/tableStyle")
        if table is None or table.get("name") != style.tag:
            raise ValueError("preset name mismatch")
        fills, seen = {}, set()
        for element in table:
            kind = element.get("type")
            if kind not in ELEMENTS or kind in seen:
                raise ValueError("unknown or duplicate preset region")
            seen.add(kind)
            if kind.endswith("Stripe") and element.get("size", "1") != "1":
                raise ValueError("non-unit preset stripe size")
            index = int(element.get("dxfId"))
            if not 0 <= index < len(dxfs):
                raise ValueError("invalid preset dxf index")
            fill = dxfs[index].find("fill")
            if fill is None:
                continue  # Differential formatting: absence must not erase a lower layer.
            pattern = fill.find("patternFill")
            if pattern is None or pattern.get("patternType") != "solid":
                raise ValueError("unsupported preset fill pattern")
            color = pattern.find("fgColor")
            if color is None or set(color.attrib) - {"theme", "tint"} or "theme" not in color.attrib:
                raise ValueError("unsupported preset fill color")
            theme, tint = int(color.get("theme")), float(color.get("tint", "0"))
            if not 0 <= theme <= 11 or not math.isfinite(tint) or not -1 <= tint <= 1:
                raise ValueError("invalid preset theme/tint")
            fills[kind] = theme, tint
        styles[style.tag] = fills
    if set(styles) != set(EXPECTED):
        raise ValueError("expected all 84 Light/Medium/Dark pivot presets")
    return [(name, styles[name]) for name in EXPECTED]


def generate(path):
    out = ['// Generated from ECMA-376 Part1 presetTableStyles.xml; see generate_pivot_stripe_fills.py.',
           '// This Source Code Form is subject to the Mozilla Public License, v. 2.0.',
           '// https://mozilla.org/MPL/2.0/', '#pragma once', '#include <string_view>',
           'namespace oox::xls {',
           '// PivotTable precedence; the last three elements are ignored for pivots.',
           'enum class PivotFillElement {']
    out.extend('    ' + name[0].upper() + name[1:] + ',' for name in ELEMENTS)
    out += ['    Count', '};', 'struct PivotSolidFill { int theme; double tint; };',
            'struct PivotStyleFills { std::u16string_view name;',
            '    PivotSolidFill fills[static_cast<int>(PivotFillElement::Count)];',
            '    constexpr const PivotSolidFill& get(PivotFillElement e) const',
            '    { return fills[static_cast<int>(e)]; }', '};',
            'constexpr PivotStyleFills aBuiltinPivotFills[] = {']
    for name, fills in presets(path):
        out.append('    { u"%s", {' % name)
        for kind in ELEMENTS:
            theme, tint = fills.get(kind, NONE)
            out.append('        { %d, %.17g }, // %s' % (theme, tint, kind))
        out.append('    } },')
    return '\n'.join(out + ['};', '} // namespace oox::xls', ''])


def inventory(path):
    columns = ('wholeTable', 'firstRowStripe', 'secondRowStripe', 'firstColumnStripe',
               'secondColumnStripe', 'headerRow', 'firstColumn', 'firstHeaderCell', 'lastColumn', 'totalRow')
    lines = ['# Built-in pivot solid-fill inventory', '',
             'Generated numeric data from ECMA-376 Part1 presetTableStyles.xml. `-` means inherit,',
             'not white/transparent. `Tn@tint` uses the workbook theme. All84presets are present;',
             'the C++ header also records page/subtotal/subheading regions for later design.', '',
             '| Preset | ' + ' | '.join(columns) + ' |',
             '|---|' + '---|' * len(columns)]
    for name, fills in presets(path):
        cells = ['T%d@%.17g' % fills[kind] if kind in fills else '-' for kind in columns]
        lines.append('| ' + name + ' | ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines) + '\n'


if __name__ == "__main__":
    pathlib.Path(sys.argv[2]).write_text(generate(sys.argv[1]), encoding="utf-8", newline="\n")
    if len(sys.argv) == 4:
        pathlib.Path(sys.argv[3]).write_text(inventory(sys.argv[1]), encoding="utf-8", newline="\n")
