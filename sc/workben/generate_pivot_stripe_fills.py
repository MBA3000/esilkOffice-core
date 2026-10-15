#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Extract only built-in Light/Medium pivot solid stripe fills from ECMA-376 presetTableStyles.xml.

The source is in OfficeOpenXML-SpreadsheetMLStyles.zip inside the ECMA-376 Part1 download.
No office, document imports, network or tests. Usage: python generate_pivot_stripe_fills.py INPUT OUTPUT
"""
import pathlib
import sys
import xml.etree.ElementTree as ET


def presets(path):
    rows = []
    for style in ET.parse(path).getroot():
        if not style.tag.startswith(("PivotStyleLight", "PivotStyleMedium")):
            continue
        dxfs = list(style.find("dxfs"))
        table = style.find("tableStyles/tableStyle")
        fills = {}
        for element in table:
            kind = element.get("type")
            if kind not in ("wholeTable", "firstRowStripe", "secondRowStripe",
                            "firstColumnStripe", "secondColumnStripe"):
                continue
            pattern = dxfs[int(element.get("dxfId"))].find("fill/patternFill")
            if pattern is None or pattern.get("patternType") != "solid":
                continue
            color = pattern.find("fgColor")
            if color is None:
                continue
            if "theme" not in color.attrib or element.get("size", "1") != "1":
                raise ValueError("unsupported preset fill/stripe size")
            fills[kind] = int(color.get("theme")), float(color.get("tint", "0"))
        row_fill = fills.get("firstRowStripe") or fills.get("secondRowStripe")
        if row_fill is None:
            continue  # Border/font-only banding is outside this fill-only draft.
        col_fill = fills.get("firstColumnStripe") or fills.get("secondColumnStripe")
        if row_fill != col_fill or (("firstRowStripe" in fills) != ("firstColumnStripe" in fills)):
            raise ValueError("preset requires separate row/column fill definitions")
        phase = 0 if "firstRowStripe" in fills else 1
        rows.append((table.get("name"), *row_fill, phase, *fills.get("wholeTable", (-1, 0.0))))
    return sorted(rows, key=lambda row: ("Medium" in row[0], int("".join(c for c in row[0] if c.isdigit()))))


def generate(path):
    out = ['// Generated from ECMA-376 Part1 presetTableStyles.xml; see generate_pivot_stripe_fills.py.',
           '// This Source Code Form is subject to the Mozilla Public License, v. 2.0.',
           '// https://mozilla.org/MPL/2.0/', '#pragma once', '#include <string_view>',
           'namespace oox::xls {',
           'struct PivotStripeFill { std::u16string_view name; int theme; double tint;',
           '    int phase; int baseTheme; double baseTint; };',
           'constexpr PivotStripeFill aBuiltinPivotStripeFills[] = {']
    for name, theme, tint, phase, base_theme, base_tint in presets(path):
        out.append('    { u"%s", %d, %.17g, %d, %d, %.17g },' %
                   (name, theme, tint, phase, base_theme, base_tint))
    return '\n'.join(out + ['};', '} // namespace oox::xls', ''])


if __name__ == "__main__":
    pathlib.Path(sys.argv[2]).write_text(generate(sys.argv[1]), encoding="utf-8", newline="\n")
