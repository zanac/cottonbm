#!/usr/bin/env python3
"""Rebuild font/cotton2_hint_font.json from the Cotton 2 English cartridge.
Python 3 standard library only.

usage: make_font.py COTTON2E_ZIP

COTTON2E_ZIP is cotton2e.zip, made with github.com/zanac/Cotton2
(patch/make_cotton2e.py). The continue screen hints of that cartridge are
English sentences drawn with the font of the Cotton 2 Saturn English patch
(nanashi, CC BY-NC-SA 4.0); with their text (font_hints.py) every letter is
cut out (the strokes, pixel values 3 and 4; the outline is redrawn). The
letters Cotton 2 does not use come from font_extra.py."""
import collections, json, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cblib
from font_hints import T
from font_extra import X

# cotton2e chips (ROM_LOAD16_WORD_SWAP)
C2E = [('c2e20122.7', 0x0200000), ('c2e20117.2', 0x0400000), ('c2e20118.3', 0x0800000),
       ('c2e20119.4', 0x0c00000), ('c2e20120.5', 0x1000000), ('c2e20121.6', 0x1400000),
       ('c2e20116.1', 0x1800000), ('c2e20123.8', 0x1c00000)]


def hint_sprites(reg):
    files = {n: (o, s) for o, n, s in cblib.cart_files(reg)}
    out = []
    for st in range(1, 8):
        o, s = files['CHR_ST%d.MF' % st]
        base = o + 0x20
        subs = cblib.mf_parse(reg[base:base + s])
        sch = [d for n, d, z in subs if n.endswith('.SCH')][0]
        spt = [d for n, d, z in subs if n.endswith('.SPT')][0]
        spt_at = reg.find(spt[:256], base)
        first = struct.unpack('>I', sch[:4])[0]
        ptr = [struct.unpack('>I', sch[i:i + 4])[0] for i in range(0, first, 4)]
        for f in range(8):
            so = struct.unpack('>I', sch[ptr[f]:ptr[f] + 4])[0]
            a = spt_at + so
            w, h = struct.unpack('>HH', reg[a + 4:a + 8])
            # the English hint lines: raw sprites 100-400 pixels wide
            if not 100 <= w <= 400 or h > 100 or reg[a + 0x20:a + 0x24] == b'LZ00':
                continue
            px = []
            for b in reg[a + 0x20:a + 0x20 + w * h // 2]:
                px += [b >> 4, b & 15]
            out.append((w, h, px))
    return out


def letters(px, w, y0):
    """the letters of a 16-row text line: fill pixels joined in 8 directions,
    pieces that overlap in x (the dot of i) merged, left to right"""
    fill = lambda x, y: px[(y0 + y) * w + x] in (3, 4)
    seen, comps = set(), []
    for x in range(w):
        for y in range(16):
            if (x, y) in seen or not fill(x, y):
                continue
            st, pts = [(x, y)], []
            seen.add((x, y))
            while st:
                a, b = st.pop()
                pts.append((a, b))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        c, d = a + dx, b + dy
                        if 0 <= c < w and 0 <= d < 16 and (c, d) not in seen and fill(c, d):
                            seen.add((c, d))
                            st.append((c, d))
            comps.append(pts)
    comps = sorted([min(p[0] for p in c), max(p[0] for p in c)] for c in comps)
    merged = []
    for c in comps:
        if merged and c[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], c[1])
        else:
            merged.append(c)
    return merged


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    z = zipfile.ZipFile(sys.argv[1])
    reg = bytearray(b'\xff' * 0x2000000)
    for name, off in C2E:
        d = z.read(name)
        reg[off:off + len(d)] = cblib.swap16(d)
    var = collections.defaultdict(collections.Counter)
    for (w, h, px), text in zip(hint_sprites(bytes(reg)), T):
        for li, line in enumerate(text):
            ls = letters(px, w, li * 16)
            chars = [c for c in line if c != ' ']
            assert len(ls) == len(chars), (line, len(ls), len(chars))
            for c, (x0, x1) in zip(chars, ls):
                var[c][tuple(''.join(str(px[(li * 16 + y) * w + x]) if px[(li * 16 + y) * w + x] in (3, 4) else '.'
                                     for x in range(x0, x1 + 1)) for y in range(16))] += 1
    font = {c: list(v.most_common(1)[0][0]) for c, v in var.items()}
    for c, rows in X.items():
        w = max(len(r) for r in rows)
        font[c] = [r.replace(' ', '.').replace('#', '4').ljust(w, '.') for r in rows] + ['.' * w] * (16 - len(rows))
    out = os.path.join(HERE, '..', 'font', 'cotton2_hint_font.json')
    json.dump(font, open(out, 'w', encoding='utf-8'), indent=0, ensure_ascii=False, sort_keys=True)
    print('%d letters from Cotton 2, %d drawn: %s' % (len(var), len(X), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
