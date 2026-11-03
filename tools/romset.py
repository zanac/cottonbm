"""The cottonbme ROM set and the patch that rebuilds it from cottonbm.

cottonbme is a clone of cottonbm. cottonbme.zip holds all the chips, so it
runs on its own: the ones the translation changes get new names
(mpr -> cbe), the others keep their names and data."""
import lzma, struct, zipfile, zlib

import cblib

SET = 'cottonbme'
MAGIC = b'CBE1\0'


def new_name(name):
    """mpr21073.5 -> cbe21073.5"""
    return 'cbe' + name[3:]


def chips(orig_chips, reg):
    """[(original name, new name or None when unchanged, data)]"""
    out = []
    for name, data in cblib.save_chips(reg):
        out.append((name, new_name(name) if data != orig_chips[name] else None, data))
    return out


def write_zip(orig_chips, reg, path):
    files = [(dst or src, data) for src, dst, data in chips(orig_chips, reg)]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            z.writestr(name, data)
    return [(name, zlib.crc32(data), data) for name, data in files]


def make_patch(orig_chips, reg):
    """one entry per chip: names, CRC32 of the original and of the result,
    then the XOR against the original, lzma compressed (empty for the chips
    copied as they are)"""
    blob = MAGIC
    for src, dst, data in chips(orig_chips, reg):
        old = orig_chips[src]
        if dst:
            x = lzma.compress(bytes(p ^ q for p, q in zip(data, old)), preset=9)
        else:
            dst, x = src, b''
        for s in (src.encode(), dst.encode()):
            blob += struct.pack('B', len(s)) + s
        blob += struct.pack('>III', zlib.crc32(old), zlib.crc32(data), len(x)) + x
    return blob
