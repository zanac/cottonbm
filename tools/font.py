"""The English font: the hint font of the Cotton 2 English patch (Saturn,
by nanashi, CC BY-NC-SA 4.0), taken from the cotton2e cartridge, plus the
glyphs Cotton Boomerang needs that Cotton 2 does not use, drawn in the same
style. Glyphs are 1-pixel strokes on a 16-row cell (caps from row 1,
baseline row 11, descenders to row 14); the outline is added around them.

render() returns a 2x pixel map with 0 = transparent, 1 = outline, 2 = fill,
the two colours of the Cotton Boomerang result screen text."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = json.load(open(os.path.join(HERE, '..', 'font', 'cotton2_hint_font.json'), encoding='utf-8'))
GAP = 3        # stroke to stroke between letters (as in Cotton 2)
SPACE = 9      # stroke to stroke across a space
ROWS = 16


def line_1x(text):
    """one line at 1x: list of rows of 0/2 (stroke), width"""
    cols = []
    first = True
    pending = 0
    for ch in text:
        if ch == ' ':
            pending = SPACE
            continue
        g = FONT[ch]
        if not first:
            pending = pending or GAP
            cols += [[0] * ROWS for _ in range(pending - 1)]
        pending = 0
        first = False
        w = len(g[0])
        # trim empty columns of the glyph
        used = [x for x in range(w) if any(g[y][x] != '.' for y in range(ROWS))]
        x0, x1 = (used[0], used[-1]) if used else (0, w - 1)
        for x in range(x0, x1 + 1):
            cols.append([2 if g[y][x] != '.' else 0 for y in range(ROWS)])
    w = len(cols)
    return [[cols[x][y] for x in range(w)] for y in range(ROWS)], w


def outline(px, w, h):
    out = [row[:] for row in px]
    for y in range(h):
        for x in range(w):
            if px[y][x] == 0 and any(0 <= y + dy < h and 0 <= x + dx < w and px[y + dy][x + dx] == 2
                                     for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                out[y][x] = 1
    return out


def render_1x(text):
    """one line at 1x with the outline: (rows of 0/1/2, width, 18 rows)"""
    r, w = line_1x(text)
    W, H = w + 2, ROWS + 2
    px = [[0] * W for _ in range(H)]
    for y in range(ROWS):
        for x in range(w):
            if r[y][x]:
                px[y + 1][x + 1] = 2
    return outline(px, W, H), W, H


def render(lines, pitch=14):
    """lines of text, centered; 2x scaled with the outline drawn at 1x then
    scaled (as the Cotton 2 font looks at 2x). Returns (rows, width, height)
    at 2x; height = 2 * (16 + pitch * (n - 1)) + 2"""
    rendered = [line_1x(t) for t in lines]
    W = max(w for r, w in rendered) + 2
    H = ROWS + pitch * (len(lines) - 1) + 1
    px = [[0] * W for _ in range(H)]
    for i, (r, w) in enumerate(rendered):
        x0 = 1 + (W - 2 - w) // 2
        for y in range(ROWS):
            for x in range(w):
                if r[y][x]:
                    px[i * pitch + y][x0 + x] = 2
    px = outline(px, W, H)
    big = []
    for row in px:
        r2 = []
        for v in row:
            r2 += [v, v]
        big.append(r2)
        big.append(r2[:])
    return big, W * 2, H * 2
