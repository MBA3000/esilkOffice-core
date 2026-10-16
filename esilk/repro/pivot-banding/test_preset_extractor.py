"""Fast data-extractor checks with synthetic XML. No Office/C++/network execution."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('pivot_preset_generator', ROOT / 'sc/workben/generate_pivot_stripe_fills.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def synthetic():
    root = ET.Element('presets')
    for family in ('Light', 'Medium', 'Dark'):
        for number in range(1, 29):
            name = 'PivotStyle%s%d' % (family, number)
            style = ET.SubElement(root, name)
            dxfs = ET.SubElement(style, 'dxfs', count='2')
            pattern = ET.SubElement(ET.SubElement(ET.SubElement(dxfs, 'dxf'), 'fill'), 'patternFill', patternType='solid')
            ET.SubElement(pattern, 'fgColor', theme='4', tint='0.5')
            ET.SubElement(dxfs, 'dxf')  # Border/font-only region: no fill is intentional.
            table = ET.SubElement(ET.SubElement(style, 'tableStyles'), 'tableStyle', name=name)
            ET.SubElement(table, 'tableStyleElement', type='firstRowStripe', dxfId='0', size='1')
            ET.SubElement(table, 'tableStyleElement', type='secondColumnStripe', dxfId='1')
    return root


class PresetExtractor(unittest.TestCase):
    def read(self, root):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.xml'
            path.write_bytes(ET.tostring(root))
            return generator.presets(path)

    def test_all_families_and_independent_axes_preserve_missing_fill(self):
        styles = self.read(synthetic())
        self.assertEqual(len(styles), 84)
        for name, fills in styles:
            self.assertEqual(fills, {'firstRowStripe': (4, 0.5)}, name)
            self.assertNotIn('secondColumnStripe', fills)
        self.assertEqual(styles[0][0], 'PivotStyleLight1')
        self.assertEqual(styles[-1][0], 'PivotStyleDark28')

    def test_unknown_duplicate_and_missing_styles_are_rejected(self):
        for operation in ('unknown', 'duplicate', 'missing'):
            root = synthetic()
            if operation == 'unknown':
                root[0].tag = 'PivotStyleDark29'
            elif operation == 'duplicate':
                root.append(root[0])
            else:
                root.remove(root[0])
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                self.read(root)

    def test_bad_dxf_indices_regions_and_stripe_sizes_are_rejected(self):
        for key, value in (('dxfId', '-1'), ('dxfId', '2'), ('size', '2'), ('type', 'unknownRegion')):
            root = synthetic()
            root[0].find('tableStyles/tableStyle/tableStyleElement').set(key, value)
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.read(root)
        root = synthetic()
        table = root[0].find('tableStyles/tableStyle')
        table.append(table[0])
        with self.assertRaises(ValueError):
            self.read(root)

    def test_unsupported_or_nonfinite_colors_are_rejected(self):
        for attributes in ({'rgb': 'FF000000'}, {'theme': '12'}, {'theme': '4', 'tint': 'nan'},
                           {'theme': '-1'}, {'theme': '1', 'tint': '1.1'}, {'theme': '1', 'tint': '-1.1'}):
            root = synthetic()
            color = root[0].find('dxfs/dxf/fill/patternFill/fgColor')
            color.attrib = attributes
            with self.subTest(attributes=attributes), self.assertRaises(ValueError):
                self.read(root)

    def test_generated_data_has_84_presets_and_known_asymmetric_dark_fills(self):
        source = (ROOT / 'sc/source/filter/inc/pivotstripefills.hxx').read_text(encoding='utf-8')
        styles = re.findall(r'\{ u"(PivotStyle\w+)", \{(.*?)\n    \} \},', source, re.S)
        self.assertEqual(len(styles), 84)
        data = {}
        for name, body in styles:
            data[name] = {kind: (int(theme), float(tint)) for theme, tint, kind in re.findall(
                r'\{ (-?\d+), ([-+\d.eE]+) \}, // (\w+)', body)}
            self.assertEqual(len(data[name]), 28)
        self.assertEqual(data['PivotStyleLight16']['headerRow'], (4, 0.79998168889431442))
        self.assertEqual(data['PivotStyleLight16']['totalRow'], (4, 0.79998168889431442))
        self.assertEqual(data['PivotStyleMedium23']['secondRowStripe'], (4, 0.59999389629810485))
        self.assertEqual(data['PivotStyleDark1']['secondRowStripe'], (0, -0.34998626667073579))
        self.assertEqual(data['PivotStyleDark1']['secondColumnStripe'], (-1, 0))
        self.assertEqual(data['PivotStyleDark28']['headerRow'], (9, -0.249977111117893))
        self.assertEqual(data['PivotStyleDark28']['wholeTable'], (9, 0))
        self.assertTrue(all(fills['lastColumn'] == (-1, 0) for fills in data.values()))

    def test_inventory_has_every_preset_without_claiming_white_for_no_fill(self):
        inventory = (Path(__file__).parent / 'preset-fill-inventory.md').read_text(encoding='utf-8')
        rows = re.findall(r'^\| (PivotStyle\w+) \|', inventory, re.M)
        self.assertEqual(set(rows), set(generator.EXPECTED))
        self.assertEqual(len(rows), 84)
        self.assertIn('not white/transparent', inventory)
