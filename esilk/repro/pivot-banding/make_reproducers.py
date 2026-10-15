#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Hand-authored, deterministic SpreadsheetML pivot fixtures. No Office/openpyxl/network.

Source records are synthetic A-D, Q1-Q4 and integers 10-43. No document or metadata was copied
from a user file. Writes ZIPs beside this script; XML is checked, files are never opened in an office.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import zipfile

S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"
HEADER = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def xml(root, body, **attrs):
    attributes = ''.join(' %s="%s"' % (k, escape(str(v))) for k, v in attrs.items())
    return HEADER + '<%s xmlns="%s" xmlns:r="%s"%s>%s</%s>' % (root, S, R, attributes, body, root)


def rels(items):
    return HEADER + '<Relationships xmlns="%s">%s</Relationships>' % (P, ''.join(
        '<Relationship Id="rId%d" Type="%s/%s" Target="%s"/>' % (i, R, kind, target)
        for i, kind, target in items))


def cell(address, value):
    if isinstance(value, str):
        return '<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (address, escape(value))
    return '<c r="%s"><v>%d</v></c>' % (address, value)


def worksheet(rows, pivot=False):
    body = '<sheetData>' + ''.join('<row r="%d">%s</row>' % (i, row) for i, row in rows) + '</sheetData>'
    if pivot:
        body += '<pivotTableParts count="1"><pivotTablePart r:id="rId1"/></pivotTableParts>'
    return xml('worksheet', body)


def parts(style, rows, columns):
    records = [(g, q, 10 * (i + 1) + j) for i, g in enumerate('ABCD') for j, q in enumerate(('Q1', 'Q2', 'Q3', 'Q4'))]
    source = [(1, ''.join(cell('%s1' % c, value) for c, value in zip('ABC', ('Group', 'Quarter', 'Value'))))]
    source += [(i, cell('A%d' % i, g) + cell('B%d' % i, q) + cell('C%d' % i, value))
               for i, (g, q, value) in enumerate(records, 2)]
    pivot = [(3, ''.join(cell('%s3' % c, value) for c, value in zip('BCDEFG', ('Group', 'Q1', 'Q2', 'Q3', 'Q4', 'Grand Total'))))]
    for i, g in enumerate('ABCD', 4):
        values = [v for group, _, v in records if group == g]
        pivot.append((i, cell('B%d' % i, g) + ''.join(cell('%s%d' % (c, i), v)
                     for c, v in zip('CDEFG', values + [sum(values)]))))
    totals = [sum(v for _, quarter, v in records if quarter == q) for q in ('Q1', 'Q2', 'Q3', 'Q4')]
    pivot.append((8, cell('B8', 'Grand Total') + ''.join(cell('%s8' % c, v)
                  for c, v in zip('CDEFG', totals + [sum(totals)]))))
    data = {
        '_rels/.rels': rels([(1, 'officeDocument', 'xl/workbook.xml')]),
        'xl/workbook.xml': xml('workbook', '<sheets><sheet name="Source" sheetId="1" r:id="rId1"/>'
            '<sheet name="Pivot" sheetId="2" r:id="rId2"/></sheets>'
            '<pivotCaches><pivotCache cacheId="1" r:id="rId4"/></pivotCaches>'),
        'xl/_rels/workbook.xml.rels': rels([(1, 'worksheet', 'worksheets/sheet1.xml'),
            (2, 'worksheet', 'worksheets/sheet2.xml'), (3, 'styles', 'styles.xml'),
            (4, 'pivotCacheDefinition', 'pivotCache/pivotCacheDefinition1.xml'), (5, 'theme', 'theme/theme1.xml')]),
        'xl/worksheets/sheet1.xml': worksheet(source),
        'xl/worksheets/sheet2.xml': worksheet(pivot, True),
        'xl/worksheets/_rels/sheet2.xml.rels': rels([(1, 'pivotTable', '../pivotTables/pivotTable1.xml')]),
        'xl/pivotTables/_rels/pivotTable1.xml.rels': rels([(1, 'pivotCacheDefinition', '../pivotCache/pivotCacheDefinition1.xml')]),
        'xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels': rels([(1, 'pivotCacheRecords', 'pivotCacheRecords1.xml')]),
    }
    fields = ''.join('<cacheField name="%s"><sharedItems count="4">%s</sharedItems></cacheField>' %
        (name, ''.join('<s v="%s"/>' % value for value in values))
        for name, values in (('Group', 'ABCD'), ('Quarter', ('Q1', 'Q2', 'Q3', 'Q4'))))
    fields += '<cacheField name="Value"><sharedItems containsString="0" containsNumber="1" count="0"/></cacheField>'
    data['xl/pivotCache/pivotCacheDefinition1.xml'] = xml('pivotCacheDefinition',
        '<cacheSource type="worksheet"><worksheetSource ref="A1:C17" sheet="Source"/></cacheSource>'
        '<cacheFields count="3">%s</cacheFields>' % fields, **{'r:id': 'rId1', 'recordCount': '16',
        'refreshOnLoad': '0', 'createdVersion': '6', 'refreshedVersion': '6', 'minRefreshableVersion': '3'})
    data['xl/pivotCache/pivotCacheRecords1.xml'] = xml('pivotCacheRecords', ''.join(
        '<r><x v="%d"/><x v="%d"/><n v="%d"/></r>' % ('ABCD'.index(g), int(q[1]) - 1, v)
        for g, q, v in records), count='16')
    pivot_fields = ''.join('<pivotField axis="%s" showAll="0" defaultSubtotal="0">'
        '<items count="5">%s<item t="default"/></items></pivotField>' %
        (axis, ''.join('<item x="%d"/>' % i for i in range(4))) for axis in ('axisRow', 'axisCol'))
    pivot_fields += '<pivotField dataField="1" showAll="0"/>'
    items = ''.join('<i><x v="%d"/></i>' % i for i in range(4)) + '<i t="grand"><x v="0"/></i>'
    data['xl/pivotTables/pivotTable1.xml'] = xml('pivotTableDefinition',
        '<location ref="B3:G8" firstHeaderRow="0" firstDataRow="1" firstDataCol="1"/>'
        '<pivotFields count="3">%s</pivotFields><rowFields count="1"><field x="0"/></rowFields>'
        '<rowItems count="5">%s</rowItems><colFields count="1"><field x="1"/></colFields>'
        '<colItems count="5">%s</colItems><dataFields count="1"><dataField name="Sum of Value" fld="2" subtotal="sum"/></dataFields>'
        '<pivotTableStyleInfo name="%s" showRowHeaders="1" showColHeaders="1" showRowStripes="%d" showColStripes="%d"/>'
        % (pivot_fields, items, items, style, rows, columns), name='HandmadePivot', cacheId='1',
        dataCaption='Values', rowGrandTotals='1', colGrandTotals='1', compact='0', compactData='0',
        outline='0', outlineData='0', gridDropZones='1')
    data['xl/styles.xml'] = xml('styleSheet', '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs><cellXfs count="1"><xf xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>')
    colors = [('dk1', '000000'), ('lt1', 'FFFFFF'), ('dk2', '44546A'), ('lt2', 'E7E6E6'),
        ('accent1', '4472C4'), ('accent2', 'ED7D31'), ('accent3', 'A5A5A5'), ('accent4', 'FFC000'),
        ('accent5', '5B9BD5'), ('accent6', '70AD47'), ('hlink', '0563C1'), ('folHlink', '954F72')]
    data['xl/theme/theme1.xml'] = HEADER + '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Handmade">'
    data['xl/theme/theme1.xml'] += '<a:themeElements><a:clrScheme name="Handmade">' + ''.join(
        '<a:%s><a:srgbClr val="%s"/></a:%s>' % (name, value, name) for name, value in colors)
    data['xl/theme/theme1.xml'] += ('</a:clrScheme><a:fontScheme name="Handmade"><a:majorFont><a:latin typeface="Calibri"/>'
        '<a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/>'
        '<a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Handmade">')
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = '<a:ln w="12700">%s<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln>' % fill
    data['xl/theme/theme1.xml'] += ('<a:fillStyleLst>' + fill * 3 + '</a:fillStyleLst>'
        '<a:lnStyleLst>' + line * 3 + '</a:lnStyleLst><a:effectStyleLst>'
        + '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3 + '</a:effectStyleLst>'
        '<a:bgFillStyleLst>' + fill * 3 + '</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')
    types = {'workbook': 'sheet.main', 'worksheets': 'worksheet', 'styles': 'styles',
             'pivotTables': 'pivotTable', 'pivotCacheDefinition1': 'pivotCacheDefinition',
             'pivotCacheRecords1': 'pivotCacheRecords'}
    overrides = []
    for name in data:
        if not name.endswith('.xml'):
            continue
        if '/theme/' in name:
            content_type = 'application/vnd.openxmlformats-officedocument.theme+xml'
        else:
            key = next(key for key in types if key in name)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.%s+xml' % types[key]
        overrides.append('<Override PartName="/%s" ContentType="%s"/>' % (name, content_type))
    data['[Content_Types].xml'] = HEADER + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    data['[Content_Types].xml'] += ('<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>' + ''.join(overrides) + '</Types>')
    return data


if __name__ == '__main__':
    cases = [('light16-rows', 'PivotStyleLight16', 1, 0), ('light23-columns', 'PivotStyleLight23', 0, 1),
             ('medium23-rows', 'PivotStyleMedium23', 1, 0), ('medium24-columns', 'PivotStyleMedium24', 0, 1),
             ('disabled-control', 'PivotStyleLight16', 0, 0), ('both-axes-control', 'PivotStyleLight16', 1, 1),
             ('dark-control', 'PivotStyleDark1', 1, 0)]
    for name, style, rows, columns in cases:
        path = Path(__file__).resolve().parent / (name + '.xlsx')
        with zipfile.ZipFile(path, 'w') as package:
            for name, text in sorted(parts(style, rows, columns).items()):
                ET.fromstring(text)
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.create_system = 0
                info.compress_type = zipfile.ZIP_STORED
                package.writestr(info, text.encode('utf-8'))
        print(path.name)
