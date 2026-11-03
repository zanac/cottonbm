"""Build the English cartridge region of Cotton Boomerang. Python 3
standard library only.

The stage result screen lines are sprites of CHR_RS.MF (frames 80-137, two
frames per line: the left part ends at the frame anchor, the right part
starts there). Each English line is drawn with the font of tools/font.py,
packed with LZ00 and put in the free space after the cartridge file chain;
the two frames point at the new sprites (an offset from the start of the
sprite table, past its end) and get the new size and position."""
import os
import struct

import cblib
import font
import lz

HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN_END = 0x185b360        # after the last file of the cartridge chain
REGION_END = cblib.REGION_SIZE


class Cart:
    def __init__(self, reg):
        self.reg = bytearray(reg)
        self.free = (CHAIN_END + 0xfff) & ~0xfff
        assert all(b == 0xff for b in self.reg[self.free:REGION_END]) or \
            all(b == 0 for b in self.reg[self.free:self.free + 0x1000]), 'free area not empty'
        self.files = {n: o for o, n, s in cblib.cart_files(self.reg)}
        self.log = []

    def alloc(self, size, align=0x20):
        at = (self.free + align - 1) & ~(align - 1)
        assert at + size <= REGION_END, 'cartridge full'
        self.free = at + size
        return at

    def subfiles(self, name):
        """{subfile name: data offset in the region} of a file of the chain"""
        n, s2, d = cblib.fs_entry(self.reg, self.files[name])
        assert n == name
        out = {}
        o = d
        while o < d + s2:
            sz = struct.unpack('>I', self.reg[o:o + 4])[0]
            if sz in (0, 0xffffffff):
                break
            out[self.reg[o + 4:o + 20].split(b'\0')[0].decode()] = o + 0x20
            o += sz
        return out


def load_lines(path=os.path.join(HERE, '..', 'text', 'result_lines.txt')):
    out = []
    for l in open(path, encoding='utf-8'):
        if l.startswith('#') or not l.strip():
            continue
        frames, jp, en = l.rstrip('\n').split('\t')
        a, b = (int(x) for x in frames.split(','))
        out.append((a, b, jp, en.split(' / ')))
    return out


def pack4(rows, w, h):
    out = bytearray()
    for y in range(h):
        r = rows[y]
        for x in range(0, w, 2):
            out.append((r[x] << 4) | r[x + 1])
    return bytes(out)


def result_lines(cart):
    sub = cart.subfiles('CHR_RS.MF')
    sch_at, spt_at = sub['CHR_RS.SCH'], sub['CHR_RS.SPT']
    first = struct.unpack('>I', cart.reg[sch_at:sch_at + 4])[0]
    ptr = [struct.unpack('>I', cart.reg[sch_at + i:sch_at + i + 4])[0] for i in range(0, first, 4)]

    def frame(k):
        p = sch_at + ptr[k]
        off, = struct.unpack('>I', cart.reg[p:p + 4])
        x, y = struct.unpack('>hh', cart.reg[p + 8:p + 12])
        h = cart.reg[spt_at + off:spt_at + off + 0x20]
        w, hh = struct.unpack('>HH', h[4:8])
        return p, off, x, y, w, hh, bytes(h)

    for a, b, jp, lines in load_lines():
        pa, oa, xa, ya, wa, ha, hdr = frame(a)
        pb, ob, xb, yb, wb, hb, _ = frame(b)
        # the original line: left part [-wa, 0], right part [0, wb] around the anchor
        center2 = wb - wa                 # twice the centre of the line
        rows, W, H = font.render(lines)
        if len(lines) == 1:
            rows, H = rows[:32], 32       # the last 1x row is empty
        Wp = (W + 7) & ~7
        pad = (Wp - W) // 2
        rows = [[0] * pad + r + [0] * (Wp - W - pad) for r in rows]
        if H % 2:
            rows.append([0] * Wp)
            H += 1
        wl = ((Wp - center2) // 2 + 4) & ~7
        wl = max(8, min(Wp - 8, wl))
        for k, p, x0, x1, oldy, oldh in ((a, pa, 0, wl, ya, ha), (b, pb, wl, Wp, yb, hb)):
            w = x1 - x0
            part = [r[x0:x1] for r in rows]
            data = lz.lz(pack4(part, w, H))
            assert cblib.unlz(data) == pack4(part, w, H)
            h2 = bytearray(hdr)
            h2[4:8] = struct.pack('>HH', w, H)
            h2[8:12] = struct.pack('>I', len(data))
            blob = bytes(h2) + data + b'\0' * ((-len(data)) & 3)
            at = cart.alloc(len(blob))
            cart.reg[at:at + len(blob)] = blob
            # x: the centre of the part from the anchor; y: keep the bottom edge
            x = -(w // 2) if k == a else w // 2
            y = oldy + oldh // 2 - H // 2
            cart.reg[p:p + 4] = struct.pack('>I', at - spt_at)
            cart.reg[p + 8:p + 12] = struct.pack('>hh', x, y)
        cart.log.append('RS %3d,%3d %3dx%-2d %s' % (a, b, Wp, H, ' / '.join(lines)))


# --- shared helpers ---------------------------------------------------------

def frame_table(cart, mf):
    """(SCH offset, SPT offset, frame record offsets) of a container"""
    sub = cart.subfiles(mf)
    base = mf[:-3]
    sch_at, spt_at = sub[base + '.SCH'], sub[base + '.SPT']
    first = struct.unpack('>I', cart.reg[sch_at:sch_at + 4])[0]
    recs = [sch_at + struct.unpack('>I', cart.reg[sch_at + i:sch_at + i + 4])[0] for i in range(0, first, 4)]
    return sch_at, spt_at, recs


def sprite(cart, spt_at, rec):
    """(width, height, pixel list, header) of the sprite of a frame record"""
    off, = struct.unpack('>I', cart.reg[rec:rec + 4])
    a = spt_at + off
    h = bytes(cart.reg[a:a + 0x20])
    w, hh = struct.unpack('>HH', h[4:8])
    size, = struct.unpack('>I', h[8:12])
    data = bytes(cart.reg[a + 0x20:a + 0x20 + size])
    raw = cblib.unlz(data) if data[:4] == b'LZ00' else data
    return w, hh, [v for c in raw[:w * hh // 2] for v in (c >> 4, c & 15)], h


def new_sprite(cart, spt_at, header, w, h, px):
    """a new LZ00 sprite in the free area: its offset from the SPT"""
    data = lz.lz(bytes((px[i] << 4) | px[i + 1] for i in range(0, w * h, 2)))
    hdr = bytearray(header)
    hdr[4:8] = struct.pack('>HH', w, h)
    hdr[8:12] = struct.pack('>I', len(data))
    blob = bytes(hdr) + data + b'\0' * ((-len(data)) & 3)
    at = cart.alloc(len(blob))
    cart.reg[at:at + len(blob)] = blob
    return at - spt_at


# --- character select ---------------------------------------------------------

# CHR_SEL.MF has the shot/weapon panels in Japanese (frames 56-59, 64-67) and
# in English (frames 72-79), in the same order:
#   Fire/Twist, Wind/Focus, Ice/Sector, Light/Search,
#   Ice/Wing, Wind/Homing, Fire/Pierce, Light/Spread ("Spred" in the ROM)
SEL_JP = (56, 57, 58, 59, 64, 65, 66, 67)
SEL_EN = (72, 73, 74, 75, 76, 77, 78, 79)
# with a Japanese BIOS the game shows panel SEL_JP[k]; with any other BIOS
# it shows frame SEL_EN[k] for the character that should get panel
# (k + 4) % 8 (Cotton gets "Ice / Wing" instead of "Fire / Twist")
SEL_OTHER_SHIFT = 4


def spread_panel(w, h, px):
    """the "Light / Spred" panel with "Spread": an "a" taken from "Weapon"
    in the same line, put between the "e" and the "d" of "Spred". Text is
    colour 1; the background is a 0/2 checkerboard"""
    y0, y1 = 34, 50                      # the sub weapon line
    cols = [any(px[y * w + x] == 1 for y in range(y0, y1)) for x in range(w)]
    glyphs, x = [], 0
    while x < w:
        if cols[x]:
            x0 = x
            while x < w and cols[x]:
                x += 1
            glyphs.append((x0, x))
        x += 1
    # S u b W e a p o n : S p r e d
    assert len(glyphs) == 15, len(glyphs)
    ax0, ax1 = glyphs[5]
    ex0, ex1 = glyphs[13]
    dx0, dx1 = glyphs[14]
    gap = dx0 - ex1
    a = [[px[y * w + x] == 1 for x in range(ax0, ax1)] for y in range(y0, y1)]
    d = [[px[y * w + x] == 1 for x in range(dx0, dx1)] for y in range(y0, y1)]
    out = list(px)
    for y in range(y0, y1):                # clear from the d on
        for x in range(dx0, w):
            if out[y * w + x] == 1:
                out[y * w + x] = 2 if (x + y) % 2 == 0 else 0
    for glyph, at in ((a, ex1 + gap), (d, ex1 + gap + (ax1 - ax0) + gap)):
        for yy, row in enumerate(glyph):
            for xx, on in enumerate(row):
                if on:
                    assert at + xx < w
                    out[(y0 + yy) * w + at + xx] = 1
    return out


def select_panels(cart):
    """the Japanese panel frames show the English sprites; the frames the
    other regions use are pointed so that every character gets its own
    panel; Spred becomes Spread"""
    sch_at, spt_at, recs = frame_table(cart, 'CHR_SEL.MF')
    for jp, en in zip(SEL_JP, SEL_EN):
        assert cart.reg[recs[jp] + 4:recs[jp] + 12] == cart.reg[recs[en] + 4:recs[en] + 12], (jp, en)
    spr = [bytes(cart.reg[recs[en]:recs[en] + 4]) for en in SEL_EN]
    w, h, px, hdr = sprite(cart, spt_at, recs[SEL_EN[7]])
    spr[7] = struct.pack('>I', new_sprite(cart, spt_at, hdr, w, h, spread_panel(w, h, px)))
    for k, jp in enumerate(SEL_JP):
        cart.reg[recs[jp]:recs[jp] + 4] = spr[k]
    for m, en in enumerate(SEL_EN):
        cart.reg[recs[en]:recs[en] + 4] = spr[(m + SEL_OTHER_SHIFT) % 8]
    cart.log.append('SEL panels: Japanese and other regions, "Spread"')


# --- title and character profiles (attract) -----------------------------------

def katakana_title(cart):
    """"コットン ブーメラン" under the logo (frame 6 of CHR_STT.MF and of
    CHR_TTLB.MF, the same sprite): the title in Japanese, already in the
    logo; it becomes an empty sprite"""
    for mf in ('CHR_STT.MF', 'CHR_TTLB.MF'):
        sch_at, spt_at, recs = frame_table(cart, mf)
        w, h, px, hdr = sprite(cart, spt_at, recs[6])
        off = new_sprite(cart, spt_at, hdr, w, h, [0] * (w * h))
        cart.reg[recs[6]:recs[6] + 4] = struct.pack('>I', off)
    cart.log.append('title katakana removed')


# frame of CHR_TTLA.MF, English lines (one per katakana line of the sprite)
PROFILE_NAMES = (
    (18, ['Nata de Cotton']),
    (26, ['Appli Ke', 'Pumpkin']),      # the "&" below the name is kept
    (27, ['Needle Work', 'III']),
    (38, ['Silk']),
)


def text_blocks(px, w, h):
    """row ranges of the text lines of a sprite (separated by empty rows)"""
    rows = [any(px[y * w:(y + 1) * w]) for y in range(h)]
    out, y = [], 0
    while y < h:
        if rows[y]:
            y0 = y
            while y < h and rows[y]:
                y += 1
            out.append((y0, y))
        y += 1
    return out


def profile_names(cart):
    """the full names in katakana under the English names of the profiles
    are drawn in English with the font at 1x: outline in colour 15 as the
    katakana, the fill of every row in the colour the katakana have in that
    row (a gradient), left aligned as they were"""
    sch_at, spt_at, recs = frame_table(cart, 'CHR_TTLA.MF')
    for k, lines in PROFILE_NAMES:
        w, h, px, hdr = sprite(cart, spt_at, recs[k])
        blocks = text_blocks(px, w, h)[:len(lines)]
        assert len(blocks) == len(lines), (k, blocks)
        out = list(px)
        for (y0, y1), text in zip(blocks, lines):
            x0 = min(x for y in range(y0, y1) for x in range(w) if px[y * w + x])
            fill = []
            for y in range(y0, y1):
                c = [px[y * w + x] for x in range(w) if px[y * w + x] not in (0, 15)]
                fill.append(max(set(c), key=c.count) if c else None)
            fill = [f if f is not None else next(g for g in fill if g is not None) for f in fill]
            for y in range(y0, y1):
                for x in range(w):
                    out[y * w + x] = 0
            rows, tw, th = font.render_1x(text)
            assert tw <= w - x0, (text, tw, w - x0)
            top = max(0, y0 + (y1 - y0 - th) // 2)
            for yy in range(th):
                y = top + yy
                if y >= h:
                    break
                f = fill[min(max(y - y0, 0), len(fill) - 1)]
                for xx in range(tw):
                    v = rows[yy][xx]
                    if v:
                        out[y * w + x0 + xx] = 15 if v == 1 else f
        off = new_sprite(cart, spt_at, hdr, w, h, out)
        cart.reg[recs[k]:recs[k] + 4] = struct.pack('>I', off)
    cart.log.append('profile names: ' + ', '.join(' '.join(l) for k, l in PROFILE_NAMES))


def build(reg):
    cart = Cart(reg)
    result_lines(cart)
    select_panels(cart)
    katakana_title(cart)
    profile_names(cart)
    return bytes(cart.reg), cart.log
