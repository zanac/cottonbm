# Cotton Boomerang English (Sega ST-V)

An English translation of the ST-V arcade game *Cotton Boomerang*
(Success, 1998, MAME set `cottonbm`), as a bootleg clone set `cottonbme`
for [mame2003-plus](https://github.com/zanac/mame2003-plus-libretro)
(branch `stv-cottonbm-english`).

Most of the arcade game is already in English: menus, in-game messages,
ranking, staff roll and ending. What is Japanese is the line one of the
characters says on the stage result screen and the shot/weapon panel of
the character select screen. There is no fan translation of this game, so
the lines are translated here and drawn with the English font of the
Cotton 2 Saturn fan translation, the same one the
[Cotton 2 English](https://github.com/zanac/Cotton2) arcade set uses.

## Support
Hey dude! Help me out for a couple of :beers: or a :coffee:!<br/>
[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://bmc.link/zanac)

## Status

| Part | State |
|---|---|
| Stage result screen: the 25 lines | English; stage 1 checked in the emulator, all lines checked as sprites (sheet below) |
| Character select: main shot and sub weapon panels | English, checked in the emulator |
| Katakana under the title logo and the character names (attract) | not changed yet |
| ROM set `cottonbme`, patch, driver entry | done |

Known limits:

- The game has English select panels for the other regions, but with a
  non-Japanese BIOS it shows them for the wrong characters (Cotton gets
  "Ice / Wing" instead of "Fire / Twist"). Here the Japanese panels are
  pointed at the right English ones, so the set runs with the Japanese
  BIOS as before.
- The result line is on screen for a short time; the lines were checked
  in the emulator for stage 1 only. The other 24 are built the same way
  and shown below as the cartridge holds them.

## Screenshots

![Cotton Boomerang English, stage 2](screenshots/gameplay.png)

*Stage 2 in `cottonbme`.*

Translated screens: Japanese arcade original on the left, `cottonbme` on
the right (mame2003-plus).

| | |
|---|---|
| Stage result screen | ![result screen](screenshots/result_stage1.png) |
| Character select | ![character select](screenshots/select.png) |

All the result lines, Japanese sprites of the cartridge on the left,
English sprites of `cottonbme` on the right:

![result lines](screenshots/result_lines.png)

The font, at the size used on the result screen: the letters of the
Cotton 2 English patch on top, the ones drawn for this game below.

![font](screenshots/font.png)

## Getting the ROM set

You need `cottonbm.zip` (the MAME set) and `stvbios.zip`.

```
python3 patch/make_cottonbme.py ROMDIR [OUTDIR]
```

This writes `cottonbme.zip`. Python 3, standard library only. The script
checks every file it writes against the CRC32 in the patch.

`cottonbme` is a clone of `cottonbm`: `cottonbme.zip` holds only the two
chips the translation changes, the others are loaded from `cottonbm.zip`,
which must stay next to it.

Input, from `cottonbm.zip` (found by CRC, the names inside the zip do not
matter):

| File | Size | CRC32 | SHA1 |
|---|---|---|---|
| mpr21073.5 | 4194304 | f2e5a5b7 | 9258d508ef6f6529efc4ad172fd29e69877a99eb |
| mpr21069.1 | 4194304 | 6a28e3c5 | 60454b71db49b872e0cb89fae2259fed601588bd |

Output, the files of `cottonbme.zip`:

| File | Size | CRC32 | SHA1 | Replaces |
|---|---|---|---|---|
| cbe21073.5 | 4194304 | edf2e030 | 5f6c87723a6a84d03237e083f9b0dbf7a9beb9ab | mpr21073.5 |
| cbe21069.1 | 4194304 | 3d516717 | 403af91838fc7a6f9d98a6d6861d19b33130991b | mpr21069.1 |

The `cbe` names are the ones the `cottonbme` driver entry in mame2003-plus
expects.

## Rebuilding everything

`build.py` redoes the whole job from the original ROM set and writes both
the ROM set and `patch/cottonbme.dat`:

```
python3 build.py ROMDIR [OUTDIR]
```

- `ROMDIR`: folder with `cottonbm.zip`
- `OUTDIR`: output folder (default `./out`)

The English text is `text/result_lines.txt`, the font
`font/cotton2_hint_font.json`. The result is reproducible byte for byte.

| File | Purpose |
|---|---|
| `build.py` | the whole build |
| `patch/make_cottonbme.py` | ROM set from `cottonbm.zip` and `cottonbme.dat` |
| `text/result_lines.txt` | frames, Japanese and English of every result line |
| `font/cotton2_hint_font.json` | the font: one 16-row bitmap per letter |
| `tools/translate.py` | the English cartridge: result lines, select panels |
| `tools/font.py` | draws a line with the font (outline, 2x) |
| `tools/lz.py` | LZ00 compressor |
| `tools/romset.py` | ROM names and patch format |
| `tools/cblib.py` | cartridge, file chain, MF containers, LZ00 decoder |
| `tools/make_font.py` | rebuilds the font from `cotton2e.zip` |
| `tools/font_hints.py` | the text of the Cotton 2 hints the font is cut from |
| `tools/font_extra.py` | the letters drawn for this game |
| `tools/screens.py` | the line and font sheets of this README (needs Pillow) |

The font file is versioned, so the build does not need Cotton 2. To make
it again, build `cotton2e.zip` with
[zanac/Cotton2](https://github.com/zanac/Cotton2) and run
`python3 tools/make_font.py cotton2e.zip`.

## Technical notes

### Cartridge

`mpr21075.7` is loaded at 0x200000 (2 MB); `mpr21070.2` … `mpr21069.1`
follow at 4 MB steps (`ROM_LOAD16_WORD_SWAP`), up to 0x1c00000. The file
system is the one of Cotton 2: chained entries of size (4), name (16),
size2 at +0x14, an 8-byte stamp and the data from +0x20. The chain ends at
0x185b348; the rest of the region is zeros and is used for the new
sprites (from 0x185c000).

### MF containers and sprites

As in Cotton 2: an MF file is a chain of subfiles (`SCH` frames, `SPT`
sprite patterns, `SPL` palettes, `SAN` animations, `SIF` counts, `SCP`
cells). A frame record is 20 bytes: the sprite offset from the start of
the `SPT` (32-bit), the palette bank (16-bit), then x and y (signed
16-bit). A sprite is a 0x20-byte header (width at +4, height at +6, data
size at +8) and the data.

Unlike Cotton 2, the arcade sprites of this game are compressed with
LZ00: `LZ00`, the 32-bit unpacked size, then

- byte `b < 0x10`: copy the next `b + 1` bytes
- byte `b >= 0x10`: copy `next + 3` bytes from `b - 0x0f` bytes back

The size field of the header is the size of the compressed data.
`tools/lz.py` compresses the new sprites in the same format.

### Stage result lines

The lines are frames 80–137 of `CHR_RS.MF`, two frames per line (the line
is wider than one sprite). The first frame is the left part and ends at
the frame anchor, the second one starts there: the x of a frame is the
offset of its centre from the anchor. One-line sprites are 32 pixels high,
the three two-line exchanges 56. The text uses two colours, 1 (outline)
and 2 (fill), in palette banks 6, 7 or 8 (black on white or white on
black, by character).

The result screen runs in the high resolution mode (704 pixels wide), so
the Cotton 2 font, made for 352 pixels, is drawn at twice its size: a
letter is a 1-pixel stroke on a 16-row cell, the outline is added around
it and the line is scaled 2x, which gives 32-pixel lines like the
Japanese ones. Two-line exchanges have a 14-row line pitch (60 pixels).

For every line, `tools/translate.py` draws the English text, centres it
where the Japanese line was centred, cuts it in two at a multiple of 8,
compresses both parts and puts them in the free space after the file
chain. The two frames point there (an offset past the end of the `SPT`)
and get the new x, and a y that keeps the bottom edge of the line. The
container itself does not change size and nothing else moves.

### Character select panels

`CHR_SEL.MF` has the shot/weapon panels twice: Japanese in frames 56–59
and 64–67, English in frames 72–79, in the same character order and at
the same position. The game shows the English ones with a non-Japanese
BIOS, but for the wrong characters. Here the Japanese frames point at the
English sprites.

### Font

The English letters of Cotton 2 come from the continue screen hints of
`cotton2e`, sentences drawn with the font of the Saturn patch. With their
text (`tools/font_hints.py`) every line is cut into letters: the stroke
pixels (values 3 and 4) joined in 8 directions, pieces that overlap in x
merged (the dot of i, j); the count of pieces matches the letters of every
line. The most common drawing of each letter is kept; letters are 3
pixels apart, a space is 9. The hints have no E, F, K, M, N, O, P, Q, R,
S, V, X, Z, q, x, z, digits and some punctuation: those are drawn in the
same style (`tools/font_extra.py`), with the ♥ and ♪ of the Japanese
lines.

## Credits and license

- Translation and the arcade port: Zanac (Vanni Brutto).
- English font: from the
  [Cotton 2 Saturn English patch](https://segaxtreme.net/resources/cotton-2-english-patch.84/)
  (translation and hacking: nanashi; proofreading and editing: Katrin,
  Danthrax). The patch is distributed under CC BY-NC-SA 4.0
  (`font/LICENSE-CC-BY-NC-SA-4.0.txt`); the font here, its derived
  letters and the patch of this project follow the same license: credit
  the authors, no commercial use, share alike.
- Cartridge tools: from [zanac/Cotton2](https://github.com/zanac/Cotton2).
- *Cotton Boomerang* © Success 1998. This project distributes no game
  data: the patch only holds the differences from the original chips.
