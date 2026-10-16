"""Fast ZIP/XML checks only. Never loads an office or executes a C++ test."""
from pathlib import Path, PurePosixPath
import posixpath
import unittest
import xml.etree.ElementTree as ET
import zipfile

import make_reproducers as handmade

HERE = Path(__file__).resolve().parent
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


class HandmadeFixtures(unittest.TestCase):
    def test_relationship_targets_and_xml_parts_are_self_contained(self):
        paths = list(HERE.rglob('*.xlsx'))
        self.assertEqual(len(paths), 95)
        for path in paths:
            with zipfile.ZipFile(path) as package:
                names = set(package.namelist())
                self.assertEqual(len(names), len(package.namelist()))
                for name in names:
                    data = package.read(name)
                    data.decode('ascii')  # All content and metadata was hand-written synthetic ASCII.
                    root = ET.fromstring(data)
                    if name.endswith('.rels'):
                        base = PurePosixPath(name).parent.parent
                        for rel in root:
                            self.assertNotEqual(rel.get('TargetMode'), 'External')
                            target = posixpath.normpath(str(base / rel.get('Target')))
                            self.assertIn(target, names, (path.name, name, target))

    def test_cached_values_and_grand_totals_are_hand_calculated(self):
        for path in HERE.rglob('*.xlsx'):
            with zipfile.ZipFile(path) as package:
                sheet = ET.fromstring(package.read('xl/worksheets/sheet2.xml'))
                cells = {e.get('r'): int(e.find(S + 'v').text) for e in sheet.iter(S + 'c')
                         if e.find(S + 'v') is not None}
                if path.stem == 'no-grand-totals':
                    self.assertNotIn('G4', cells)
                    self.assertNotIn('C8', cells)
                else:
                    self.assertEqual([cells['G%d' % row] for row in range(4, 8)], [46, 86, 126, 166])
                    self.assertEqual([cells[col + '8'] for col in 'CDEF'], [100, 104, 108, 112])
                    self.assertEqual(cells['G8'], 424)
                self.assertEqual(sum(cells['%s%d' % (col, row)] for col in 'CDEF' for row in range(4, 8)), 424)
                records = ET.fromstring(package.read('xl/pivotCache/pivotCacheRecords1.xml'))
                self.assertEqual(len(records), 16)
                self.assertEqual(sum(int(e.find(S + 'n').get('v')) for e in records), 424)

    def test_styles_axes_and_header_offsets_are_explicit(self):
        for name, style, rows, columns, *options in handmade.cases():
            with zipfile.ZipFile(HERE / (name + '.xlsx')) as package:
                root = ET.fromstring(package.read('xl/pivotTables/pivotTable1.xml'))
                info = root.find(S + 'pivotTableStyleInfo')
                self.assertEqual(tuple(info.get(key) for key in ('name', 'showRowStripes', 'showColStripes')),
                                 (style, str(rows), str(columns)))
                row_headers, col_headers, totals, offset = (options + [1, 1, True, 1][len(options):])
                self.assertEqual(info.get('showRowHeaders'), str(row_headers))
                self.assertEqual(info.get('showColHeaders'), str(col_headers))
                self.assertEqual(info.get('showLastColumn'), '1')
                self.assertEqual(root.get('rowGrandTotals'), '1' if totals else '0')
                self.assertEqual(root.get('colGrandTotals'), '1' if totals else '0')
                self.assertEqual(root.find(S + 'location').attrib,
                    dict(ref='B3:G8' if totals else 'B3:F7', firstHeaderRow='0', firstDataRow=str(offset), firstDataCol='1'))

    def test_all_builtin_styles_have_an_independent_fixture(self):
        expected = {'PivotStyle%s%d' % (family, number)
                    for family in ('Light', 'Medium', 'Dark') for number in range(1, 29)}
        self.assertEqual({path.stem for path in (HERE / 'presets').glob('*.xlsx')}, expected)
        for path in (HERE / 'presets').glob('*.xlsx'):
            with zipfile.ZipFile(path) as package:
                root = ET.fromstring(package.read('xl/pivotTables/pivotTable1.xml'))
                self.assertEqual(root.find(S + 'pivotTableStyleInfo').get('name'), path.stem)

    def test_archives_are_deterministic_from_hand_authored_sources(self):
        for name, *arguments in handmade.cases():
            with zipfile.ZipFile(HERE / (name + '.xlsx')) as package:
                expected = handmade.parts(*arguments)
                self.assertEqual(set(package.namelist()), set(expected))
                for member in package.infolist():
                    self.assertEqual(member.date_time, (2026, 1, 1, 0, 0, 0))
                    self.assertEqual(package.read(member.filename), expected[member.filename].encode('utf-8'))
