#!/usr/bin/env python3
"""Cotton Boomerang English (ST-V) - full build. Python 3 standard library only.

usage: build.py ROMDIR [OUTDIR]

ROMDIR  folder with the arcade cottonbm.zip
OUTDIR  output folder (default: ./out)

Writes OUTDIR/cottonbme.zip and patch/cottonbme.dat. The English text is in
text/, the font in font/ (rebuilt from Cotton 2 with tools/make_font.py).

Users who only want the ROM set do not need this: patch/make_cottonbme.py
rebuilds it from cottonbm.zip alone.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import cblib, romset, translate


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 1
    romdir = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) == 3 else 'out'
    os.makedirs(out, exist_ok=True)
    reg, orig_chips = cblib.load_cart(romdir)
    eng, log = translate.build(bytes(reg))
    for line in log:
        print('  ' + line)
    for name, crc, data in romset.write_zip(eng, os.path.join(out, romset.SET + '.zip')):
        print('  %-12s %08x' % (name, crc))
    dat = os.path.join(HERE, 'patch', romset.SET + '.dat')
    open(dat, 'wb').write(romset.make_patch(orig_chips, eng))
    print('  written %s and %s' % (os.path.join(out, romset.SET + '.zip'), dat))
    return 0


if __name__ == '__main__':
    sys.exit(main())
