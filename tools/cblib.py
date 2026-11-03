"""Cotton Boomerang (Sega ST-V) English translation: shared helpers.

Adapted from the Cotton 2 English project (github.com/zanac/Cotton2).

Python 3 standard library only.

Formats handled here:
  * the ST-V cartridge region of cotton2 and its chained file system
  * the Saturn disc image (ISO 9660 data track, raw 2352 or cooked 2048)
  * the "MF" graphics containers (SCH/SPT/SPL/SAN/SIF/SCP subfiles)
  * the LZ00 sprite compression used by the Saturn port
"""
import os, struct, zipfile

# ---------------------------------------------------------------- arcade

# (name, crc, region offset, size) - ROM_LOAD16_WORD_SWAP in src/drivers/stv.c
CART = [
    ('mpr21075.7', 0x200b58ba, 0x0200000, 0x200000),
    ('mpr21070.2', 0x56c0bf1d, 0x0400000, 0x400000),
    ('mpr21071.3', 0x2bb18df2, 0x0800000, 0x400000),
    ('mpr21072.4', 0x7c7cb977, 0x0c00000, 0x400000),
    ('mpr21073.5', 0xf2e5a5b7, 0x1000000, 0x400000),
    ('mpr21074.6', 0x6a7e7a7b, 0x1400000, 0x400000),
    ('mpr21069.1', 0x6a28e3c5, 0x1800000, 0x400000),
]
REGION_SIZE = 0x1c00000
SET_IN = 'cottonbm'


def swap16(b):
    a = bytearray(b)
    a[0::2], a[1::2] = b[1::2], b[0::2]
    return bytes(a)


def find_member(zips, name, crc):
    for z in zips:
        for i in z.infolist():
            if i.CRC == crc:
                return z.read(i)
    return None


def load_cart(romdir):
    """the cart region (big endian, as the SH-2 sees it) and the raw chips"""
    zips = [zipfile.ZipFile(os.path.join(romdir, n))
            for n in (SET_IN + '.zip',) if os.path.exists(os.path.join(romdir, n))]
    if not zips:
        raise SystemExit(SET_IN + '.zip not found in ' + romdir)
    reg = bytearray(b'\xff' * REGION_SIZE)
    chips = {}
    for name, crc, off, size in CART:
        d = find_member(zips, name, crc)
        if d is None or len(d) != size:
            raise SystemExit('%s (CRC %08x) not found in %s.zip' % (name, crc, SET_IN))
        chips[name] = d
        reg[off:off + size] = swap16(d)
    return reg, chips


def save_chips(reg):
    """split a region back into chips"""
    return [(name, swap16(bytes(reg[off:off + size]))) for name, crc, off, size in CART]


def fs_entry(reg, off):
    """(name, size2, data offset) of the cart file at off"""
    name = reg[off + 4:off + 20].split(b'\0')[0].decode('latin1')
    s2 = struct.unpack('>I', reg[off + 0x14:off + 0x18])[0]
    return name, s2, off + 0x20



def mf_parse(b):
    """list of [name, data, stamp(8 bytes)] of an MF container"""
    o = 0
    out = []
    while o + 0x20 <= len(b):
        sz = struct.unpack('>I', b[o:o + 4])[0]
        if sz == 0:
            break
        name = b[o + 4:o + 20].split(b'\0')[0].decode('latin1')
        s2 = struct.unpack('>I', b[o + 0x14:o + 0x18])[0]
        out.append([name, b[o + 0x20:o + 0x20 + s2], b[o + 0x18:o + 0x20]])
        o += sz
    return out


def mf_build(subs, end=b'\0' * 4):
    out = bytearray()
    for name, data, stamp in subs:
        pad = (-len(data)) & 3
        hdr = struct.pack('>I', 0x20 + len(data) + pad) + name.encode().ljust(16, b'\0')
        hdr += struct.pack('>I', len(data)) + stamp
        out += hdr + data + b'\0' * pad
    out += end
    return bytes(out)


def unlz(c):
    """LZ00: byte b < 0x10 -> b+1 literals; else copy (next byte + 3) bytes
    from distance b - 0x0f (bytes before the start read as zero)"""
    assert c[:4] == b'LZ00'
    n = struct.unpack('>I', c[4:8])[0]
    i = 8
    o = bytearray()
    while len(o) < n and i < len(c):
        b = c[i]
        i += 1
        if b < 0x10:
            o += c[i:i + b + 1]
            i += b + 1
        else:
            d = b - 0x0f
            ln = c[i] + 3
            i += 1
            for _ in range(ln):
                s = len(o) - d
                o.append(o[s] if s >= 0 else 0)
    return bytes(o[:n])


def spt_entries(spt):
    """list of (offset, header, data) of a sprite pattern table"""
    out = []
    o = 0
    while o + 0x20 <= len(spt):
        h = spt[o:o + 0x20]
        sz = struct.unpack('>I', h[8:12])[0]
        out.append((o, h, spt[o + 0x20:o + 0x20 + sz]))
        o += 0x20 + ((sz + 3) & ~3)
    return out


def sch_offsets(sch):
    first = struct.unpack('>I', sch[:4])[0]
    n = (len(sch) - first) // 20
    return first, n


def cart_files(reg):
    """[(header offset, name, size2)] of every file entry found in the cart"""
    import re
    out = []
    for m in re.finditer(rb'[A-Z0-9_]{1,8}\.[A-Z0-9_]{1,3}\0', reg):
        o = m.start() - 4
        if o < 0 or o % 4:
            continue
        sz = struct.unpack('>I', reg[o:o + 4])[0]
        s2 = struct.unpack('>I', reg[o + 0x14:o + 0x18])[0]
        if s2 <= sz <= s2 + 0x40 and sz < 0x400000:
            out.append((o, m.group()[:-1].decode(), s2))
    return out
