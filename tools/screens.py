#!/usr/bin/env python3
"""Sheets for the README: the stage result lines, Japanese (from the
cartridge) and English (as built), in screenshots/result_lines.png, and the
letters of the font in screenshots/font.png.
Needs Pillow (only this script).

usage: screens.py ROMDIR"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cblib, font, translate
from PIL import Image

BG, PAL = (32, 48, 96), {1: (0, 0, 0), 2: (248, 248, 248)}


def jp_line(reg, a, b):
    files = {n: o for o, n, s in cblib.cart_files(reg)}
    n, s2, d = cblib.fs_entry(reg, files['CHR_RS.MF'])
    subs = {k: x for k, x, z in cblib.mf_parse(reg[d:d + s2])}
    ents = cblib.spt_entries(subs['CHR_RS.SPT'])
    parts = []
    for k in (a, b):
        o, h, data = ents[k]
        w, hh = struct.unpack('>HH', h[4:8])
        px = [v for c in cblib.unlz(data)[:w * hh // 2] for v in (c >> 4, c & 15)]
        im = Image.new('RGB', (w, hh), BG)
        im.putdata([PAL.get(v, BG) for v in px])
        parts.append(im)
    out = Image.new('RGB', (sum(p.width for p in parts), max(p.height for p in parts)), BG)
    out.paste(parts[0], (0, 0))
    out.paste(parts[1], (parts[0].width, 0))
    return out


def en_line(lines):
    rows, w, h = font.render(lines)
    im = Image.new('RGB', (w, h), BG)
    im.putdata([PAL.get(v, BG) for r in rows for v in r])
    return im


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    reg, chips = cblib.load_cart(sys.argv[1])
    pairs = [(jp_line(bytes(reg), a, b), en_line(en)) for a, b, jp, en in translate.load_lines()]
    wj = max(j.width for j, e in pairs)
    we = max(e.width for j, e in pairs)
    H = sum(max(j.height, e.height) + 8 for j, e in pairs) + 8
    out = Image.new('RGB', (wj + we + 40, H), BG)
    y = 8
    for j, e in pairs:
        out.paste(j, (12, y))
        out.paste(e, (wj + 28, y))
        y += max(j.height, e.height) + 8
    path = os.path.join(HERE, '..', 'screenshots', 'result_lines.png')
    out.save(path)
    print('written ' + path)
    font_sheet(os.path.join(HERE, '..', 'screenshots', 'font.png'))
    return 0


def font_sheet(path):
    """every letter of the font at 2x: from Cotton 2 on top, drawn below"""
    import font_extra
    drawn = ''.join(sorted(c for c in font.FONT if c in font_extra.X))
    c2 = ''.join(sorted(c for c in font.FONT if c not in font_extra.X))
    ims = [en_line([' '.join(c2[i:i + 21]) for i in range(0, len(c2), 21)]),
           en_line([' '.join(drawn[i:i + 21]) for i in range(0, len(drawn), 21)])]
    out = Image.new('RGB', (max(i.width for i in ims) + 24, sum(i.height for i in ims) + 36), BG)
    out.paste(ims[0], (12, 12))
    out.paste(ims[1], (12, ims[0].height + 24))
    out.save(path)
    print('written ' + path)


if __name__ == '__main__':
    sys.exit(main())
