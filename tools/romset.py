"""The cottonbme ROM set and the patch that rebuilds it from cottonbm.

cottonbme is a clone of cottonbm: the chips the translation changes get new
names (mpr -> cbe) and are the only files of cottonbme.zip; the others are
loaded from the parent set, cottonbm.zip."""
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
    changed = [(dst, data) for src, dst, data in chips(orig_chips, reg) if dst]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for dst, data in changed:
            z.writestr(dst, data)
    return [(dst, zlib.crc32(data), data) for dst, data in changed]


def make_patch(orig_chips, reg):
    """XOR of every changed chip against the original, lzma compressed"""
    blob = MAGIC
    for src, dst, data in chips(orig_chips, reg):
        if not dst:
            continue
        old = orig_chips[src]
        x = lzma.compress(bytes(p ^ q for p, q in zip(data, old)), preset=9)
        for s in (src.encode(), dst.encode()):
            blob += struct.pack('B', len(s)) + s
        blob += struct.pack('>III', zlib.crc32(old), zlib.crc32(data), len(x)) + x
    return blob
