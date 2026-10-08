#!/usr/bin/env python3
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil -*-
#
# Check the esilk po overlays (see README.md) against the en-US sources:
# every entry must name an existing string of its source file, and its msgid
# must equal the current en-US text. l10ntools keys translations by file,
# group and id only, so a stale msgid would still be merged silently.
#
# usage: python esilk/l10n/check_overlays.py [--quiet]
#   --quiet: print nothing when all entries match. The build runs it this way
#   before every ulfex/xrmex merge that uses overlays (gb_POLOCATION_check_overlays
#   in solenv/gbuild/TargetLocations.mk), so a stale overlay fails the build.
# exit status: 0 = all entries match, 1 = problems found

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERLAYS = ROOT / 'esilk' / 'l10n' / 'translations' / 'source'


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


def en_us_xrm(path):
    text = path.read_text(encoding='utf-8')
    return {m.group(1): m.group(2) for m in
            re.finditer(r'<\w+ id="([^"]+)"[^>]*xml:lang="en-US"[^>]*>(.*?)</\w+>', text, re.S)}


def main(argv):
    quiet = '--quiet' in argv
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
