#!/usr/bin/env python3
# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil -*-
#
# Merge an esilk UI po overlay into an upstream po file for msgfmt (see README.md).
#
# usage: python esilk/l10n/merge_po.py <overlay.po> <upstream.po> <out.po>
#
# The output keeps the upstream header (Plural-Forms), then every overlay entry,
# then the upstream entries that the overlay does not replace. An upstream entry
# is replaced when the overlay has an entry with the same msgctxt and msgid, or
# when an overlay entry names it in a comment
#     #. esilk-replaces: "<old msgid, po-escaped>"
# (an en-US string esilk rewrote: the old entry would otherwise stay in the .mo
# with its old text, unused but visible to string scans). Entries are copied as
# text, so plural entries and comments pass through unchanged.

import re
import sys


def blocks(text):
    return [b for b in re.split(r'\n\s*\n', text.strip('\n')) if b.strip()]


def field(block, key):
    """The po-escaped value of msgctxt/msgid in a block, or None."""
    out, cur = None, None
    for line in block.splitlines():
        m = re.match(r'(msgctxt|msgid|msgid_plural|msgstr(?:\[\d+\])?) "(.*)"$', line)
        if m:
            cur = m.group(1)
            if cur == key:
                out = [m.group(2)]
        elif line.startswith('"') and cur == key and out is not None:
            out.append(line[1:-1])
    return None if out is None else ''.join(out)


def key(block):
    return (field(block, 'msgctxt') or '', field(block, 'msgid'))


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    with open(argv[0], encoding='utf-8') as f:
        overlay = blocks(f.read())
    with open(argv[1], encoding='utf-8') as f:
        upstream = blocks(f.read())
    replaced = set()
    entries = []
    for b in overlay:
        k = key(b)
        if not k[1]:
            continue  # header
        entries.append(b)
        replaced.add(k)
        for m in re.finditer(r'^#\. esilk-replaces: "(.*)"$', b, re.M):
            replaced.add((k[0], m.group(1)))
    header = [b for b in upstream if not key(b)[1]][:1]
    rest = [b for b in upstream if key(b)[1] and key(b) not in replaced]
    with open(argv[2], 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n\n'.join(header + entries + rest) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
