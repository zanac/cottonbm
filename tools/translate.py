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


# character select: the Japanese panels (main shot type, sub weapon) and the
# English ones of the other regions, same order (Cotton, ...)
SEL_JP = (56, 57, 58, 59, 64, 65, 66, 67)
SEL_EN = (72, 73, 74, 75, 76, 77, 78, 79)


def select_panels(cart):
    """the Japanese panel frames show the English sprites. The game has them
    for the other regions, but there it shows them for the wrong characters
    (Cotton gets "Ice / Wing"), so the frames are pointed at them here"""
    sub = cart.subfiles('CHR_SEL.MF')
    sch_at = sub['CHR_SEL.SCH']
    first = struct.unpack('>I', cart.reg[sch_at:sch_at + 4])[0]
    ptr = [struct.unpack('>I', cart.reg[sch_at + i:sch_at + i + 4])[0] for i in range(0, first, 4)]
    for jp, en in zip(SEL_JP, SEL_EN):
        pj, pe = sch_at + ptr[jp], sch_at + ptr[en]
        assert cart.reg[pj + 4:pj + 12] == cart.reg[pe + 4:pe + 12], (jp, en)   # palette, position
        cart.reg[pj:pj + 4] = cart.reg[pe:pe + 4]
    cart.log.append('SEL panels %s -> %s' % (SEL_JP, SEL_EN))


def build(reg):
    cart = Cart(reg)
    result_lines(cart)
    select_panels(cart)
    return bytes(cart.reg), cart.log
