#!/usr/bin/env python3
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil -*-
#
# Check the esilk po overlays (see README.md) against the en-US sources:
# every entry must name an existing string of its source file, and its msgid
# must equal the current en-US text. l10ntools keys translations by file,
# group and id only, so a stale msgid would still be merged silently.
# UI overlays (<module>/messages.po, merged into the .mo files) are keyed by
# msgctxt and msgid: an entry whose msgid no longer exists in the source would
# simply never be shown, so it is reported as well. Their header must keep the
# upstream Content-Type and Plural-Forms, because the overlay comes first in the
# msgcat merge and its header becomes the header of the .mo file.
#
# usage: python esilk/l10n/check_overlays.py [--quiet] [--translations DIR]
#   --quiet: print nothing when all entries match. The build runs it this way
#   before every ulfex/xrmex merge and every .mo build that uses overlays
#   (gb_POLOCATION_check_overlays in solenv/gbuild/TargetLocations.mk), so a
#   stale overlay fails the build.
# exit status: 0 = all entries match, 1 = problems found

import html
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERLAYS = ROOT / 'esilk' / 'l10n' / 'translations' / 'source'
# upstream po files (the translations submodule); --translations DIR overrides it
TRANSLATIONS = ROOT / 'translations' / 'source'


def unquote(lines):
    return ''.join(re.fullmatch(r'"(.*)"', l.strip()).group(1) for l in lines)


def unescape(s):
    return re.sub(r'\\(.)', lambda m: {'n': '\n', 't': '\t'}.get(m.group(1), m.group(1)), s)


def read_po(path):
    """Yield (reference, msgctxt, msgid, msgstr) for each non-header entry."""
    text = path.read_text(encoding='utf-8')
    for block in re.split(r'\n\s*\n', text):
        lines = [l for l in block.splitlines() if l.strip()]
        ref = next((l[3:].strip() for l in lines if l.startswith('#: ')), None)
        fields, cur = {}, None
        for l in lines:
            m = re.match(r'(msgctxt|msgid|msgstr) (".*")$', l)
            if m:
                cur = m.group(1)
                fields[cur] = [m.group(2)]
            elif l.startswith('"') and cur:
                fields[cur].append(l)
            elif l.startswith('#'):
                if cur:
                    raise ValueError(f'{path}: comment inside an entry: {l}')
        if 'msgid' not in fields or not unquote(fields['msgid']):
            continue  # header
        yield (ref, unescape(unquote(fields['msgctxt'])), unescape(unquote(fields['msgid'])),
               unescape(unquote(fields['msgstr'])))


def en_us_ulf(path):
    strings, key = {}, None
    for l in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\s*\[(\w+)\]\s*$', l)
        if m:
            key = m.group(1)
        m = re.match(r'\s*en-US\s*=\s*"(.*)"\s*$', l)
        if m and key:
            strings[key] = m.group(1).replace('\\"', '"')
    return strings


def en_us_xcu(path):
    """'<node>/<prop>' -> en-US value of a configuration fragment (merged by cfgex;
    the msgctxt is file, node, prop, value.text). Fragments have no root element,
    so they are read with a regular expression, not an XML parser."""
    strings = {}
    text = path.read_text(encoding='utf-8')
    for node in re.finditer(r'<node oor:name="([^"]+)"(.*?)</node>', text, re.S):
        for prop in re.finditer(r'<prop oor:name="([^"]+)"[^>]*>(.*?)</prop>', node.group(2), re.S):
            m = re.search(r'<value xml:lang="en-US">(.*?)</value>', prop.group(2), re.S)
            if m:
                strings[f'{html.unescape(node.group(1))}/{prop.group(1)}'] = html.unescape(m.group(1))
    return strings


def en_us_xrm(path):
    text = path.read_text(encoding='utf-8')
    return {m.group(1): m.group(2) for m in
            re.finditer(r'<\w+ id="([^"]+)"[^>]*xml:lang="en-US"[^>]*>(.*?)</\w+>', text, re.S)}


def c_strings(text):
    """Join adjacent C string literals and undo their escapes."""
    return unescape(''.join(re.findall(r'"((?:[^"\\\n]|\\.)*)"', text)))


def en_us_hrc(path):
    """msgctxt -> en-US texts of the NC_("ctxt", "text") entries of a .hrc file."""
    strings = {}
    # string literals may be split over lines, also with a backslash line continuation
    for m in re.finditer(r'\bNC_\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*((?:"(?:[^"\\]|\\.)*"(?:\s|\\\n)*)+)\)',
                         path.read_text(encoding='utf-8')):
        strings.setdefault(unescape(m.group(1)), []).append(c_strings(m.group(2)))
    return strings


def en_us_ui(path):
    """msgctxt -> en-US texts of the translatable elements of a .ui file."""
    strings = {}
    for el in ET.parse(path).iter():
        if el.get('translatable') == 'yes' and el.get('context'):
            strings.setdefault(el.get('context'), []).append(el.text or '')
    return strings


def po_header(path):
    """The header fields (name -> value) of a po file."""
    text = path.read_text(encoding='utf-8')
    m = re.search(r'^msgid ""\nmsgstr ((?:".*"\n?)+)', text, re.M)
    fields = {}
    if m:
        for line in unescape(unquote(m.group(1).splitlines())).splitlines():
            name, _, value = line.partition(':')
            fields[name.strip()] = value.strip()
    return fields


def check_messages(po, rel, lang, entries, problems):
    """Check a UI overlay (<module>/messages.po) against its sources and the upstream po."""
    upstream = TRANSLATIONS / rel
    if not upstream.is_file():
        problems.append(f'{rel.as_posix()}: upstream po {upstream} missing')
    else:
        mine, theirs = po_header(po), po_header(upstream)
        for field in ('Content-Type', 'Plural-Forms'):
            if mine.get(field) != theirs.get(field):
                problems.append(f'{rel.as_posix()}: header {field} differs from the upstream po\n'
                                f'    upstream: {theirs.get(field)}\n    overlay:  {mine.get(field)}')
    seen = set()
    for ref, ctxt, msgid, msgstr in entries:
        where = f'{rel.as_posix()}: {ctxt}'
        if (ctxt, msgid) in seen:
            problems.append(f'{where}: duplicate entry')
        seen.add((ctxt, msgid))
        if not ref:
            problems.append(f'{where}: entry has no "#: <source file>" reference')
            continue
        source = ROOT / ref.split()[0].rsplit(':', 1)[0]
        if not source.is_file():
            problems.append(f'{where}: source {source} missing')
            continue
        try:
            strings = en_us_ui(source) if source.suffix == '.ui' else en_us_hrc(source)
        except (ET.ParseError, UnicodeDecodeError) as e:
            problems.append(f'{where}: cannot read {source.name} ({e})')
            continue
        if ctxt not in strings:
            problems.append(f'{where}: no string with this context in {source.name}')
        elif msgid not in strings[ctxt]:
            problems.append(f'{where}: msgid differs from the en-US text\n'
                            f'    en-US: {" | ".join(strings[ctxt])}\n    msgid: {msgid}')
        if not msgstr:
            problems.append(f'{where}: empty msgstr')
        if lang not in ('kk', 'ru'):
            problems.append(f'{where}: unexpected language directory {lang}')


def main(argv):
    global TRANSLATIONS
    quiet = '--quiet' in argv
    if '--translations' in argv:
        TRANSLATIONS = pathlib.Path(argv[argv.index('--translations') + 1])
    # The build's console may not be UTF-8; never fail on printing a message.
    sys.stdout.reconfigure(errors='backslashreplace')
    problems, count = [], 0
    for po in sorted(OVERLAYS.rglob('*.po')):
        rel = po.relative_to(OVERLAYS)
        lang, module = rel.parts[0], pathlib.Path(*rel.parts[1:]).with_suffix('')
        try:
            entries = list(read_po(po))
        except (ValueError, AttributeError, KeyError, UnicodeDecodeError) as e:
            problems.append(f'{rel.as_posix()}: cannot parse ({type(e).__name__}: {e})')
            continue
        if rel.name == 'messages.po':
            count += len(entries)
            check_messages(po, rel, lang, entries, problems)
            continue
        for ref, ctxt, msgid, msgstr in entries:
            count += 1
            parts = ctxt.split('\n')
            where = f'{rel.as_posix()}: {"/".join(parts[:-1])}'
            if not ref:
                problems.append(f'{where}: entry has no "#: <source file>" reference')
                continue
            source = ROOT / module / ref
            if not source.is_file():
                problems.append(f'{where}: source {source} missing')
                continue
            if source.suffix == '.xcu':
                strings = en_us_xcu(source)
                key = '/'.join(parts[-3:-1]) if len(parts) >= 3 else ''
            else:
                strings = en_us_xrm(source) if source.suffix == '.xrm' else en_us_ulf(source)
                key = parts[-2] if len(parts) >= 2 else ''
            if key not in strings:
                problems.append(f'{where}: no en-US string "{key}" in {source.name}')
            elif strings[key] != msgid:
                problems.append(f'{where}: msgid differs from the en-US text\n'
                                f'    en-US: {strings[key]}\n    msgid: {msgid}')
            if not msgstr:
                problems.append(f'{where}: empty msgstr')
            if lang not in ('kk', 'ru'):
                problems.append(f'{where}: unexpected language directory {lang}')
    for p in problems:
        print('check_overlays.py: PROBLEM', p)
    if problems or not quiet:
        print(f'check_overlays.py: {count} overlay entries checked, {len(problems)} problem(s)'
              + (' - fix the overlay or the en-US string (esilk/l10n/README.md)' if problems else ''))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
