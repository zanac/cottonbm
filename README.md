# Cotton Boomerang English (Sega ST-V)

Work in progress: an English translation of the ST-V arcade game *Cotton
Boomerang* (Success, 1998, MAME set `cottonbm`), as a bootleg clone set
`cottonbme` for [mame2003-plus](https://github.com/zanac/mame2003-plus-libretro).

Done so far: the 25 lines of the stage result screen, in the English font of
Cotton 2 (see below). Still to do: the character select panels, the
katakana under the title and the character names, screenshots.

## Getting the ROM set

```
python3 patch/make_cottonbme.py ROMDIR [OUTDIR]
```

ROMDIR holds `cottonbm.zip` (the MAME set); the result is `cottonbme.zip`.
Python 3, standard library only.

## Rebuilding

```
python3 build.py ROMDIR [OUTDIR]
```

rebuilds `cottonbme.zip` and `patch/cottonbme.dat` from `cottonbm.zip`,
`text/` and `font/`.

## Font and credits

The English font is the one of the [Cotton 2 Saturn English
patch](https://segaxtreme.net/resources/cotton-2-english-patch.84/)
(translation and hacking: nanashi; proofreading: Katrin, Danthrax),
taken from the English Cotton 2 arcade cartridge built by
[zanac/Cotton2](https://github.com/zanac/Cotton2) and shown at twice its
size; `tools/make_font.py` rebuilds it. The letters Cotton 2 does not use
were drawn in the same style (`tools/font_extra.py`). The patch is
distributed under CC BY-NC-SA 4.0 (`font/LICENSE-CC-BY-NC-SA-4.0.txt`),
and so is the font here: no commercial use.

The cartridge tools come from zanac/Cotton2.
