"""Fast ZIP/XML checks only. Never loads an office or executes a C++ test."""
from pathlib import Path, PurePosixPath
import posixpath
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


class HandmadeFixtures(unittest.TestCase):
    def test_relationship_targets_and_xml_parts_are_self_contained(self):
        paths = list(HERE.glob('*.xlsx'))
        self.assertEqual(len(paths), 7)
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
        for path in HERE.glob('*.xlsx'):
            with zipfile.ZipFile(path) as package:
                sheet = ET.fromstring(package.read('xl/worksheets/sheet2.xml'))
                cells = {e.get('r'): int(e.find(S + 'v').text) for e in sheet.iter(S + 'c')
                         if e.find(S + 'v') is not None}
                self.assertEqual([cells['G%d' % row] for row in range(4, 8)], [46, 86, 126, 166])
                self.assertEqual([cells[col + '8'] for col in 'CDEF'], [100, 104, 108, 112])
                self.assertEqual(cells['G8'], 424)
                self.assertEqual(sum(cells['%s%d' % (col, row)] for col in 'CDEF' for row in range(4, 8)), 424)
                records = ET.fromstring(package.read('xl/pivotCache/pivotCacheRecords1.xml'))
                self.assertEqual(len(records), 16)
                self.assertEqual(sum(int(e.find(S + 'n').get('v')) for e in records), 424)

    def test_styles_axes_and_header_offsets_are_explicit(self):
        expected = {
            'light16-rows': ('PivotStyleLight16', '1', '0'),
            'light23-columns': ('PivotStyleLight23', '0', '1'),
            'medium23-rows': ('PivotStyleMedium23', '1', '0'),
            'medium24-columns': ('PivotStyleMedium24', '0', '1'),
            'disabled-control': ('PivotStyleLight16', '0', '0'),
            'both-axes-control': ('PivotStyleLight16', '1', '1'),
            'dark-control': ('PivotStyleDark1', '1', '0'),
        }
        for name, values in expected.items():
            with zipfile.ZipFile(HERE / (name + '.xlsx')) as package:
                root = ET.fromstring(package.read('xl/pivotTables/pivotTable1.xml'))
                info = root.find(S + 'pivotTableStyleInfo')
                self.assertEqual(tuple(info.get(key) for key in ('name', 'showRowStripes', 'showColStripes')), values)
                self.assertEqual(root.find(S + 'location').attrib,
                    dict(ref='B3:G8', firstHeaderRow='0', firstDataRow='1', firstDataCol='1'))
