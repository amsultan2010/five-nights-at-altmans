"""Helpers for building new words in the game's own pixel font.

Most letters are cut from the game's existing text sprites (the title, the menu items),
so they match exactly. The few letters the game never uses are drawn with DejaVu Sans Mono,
which is close enough at this size.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from paths import EX, FONTS

ADV = 25.6                                   # glyph advance of the title/menu font, in px
DV = str(FONTS / 'DejaVuSansMono.ttf')

def A(k):
    """Alpha mask of game image k."""
    return np.asarray(Image.open(EX / f'{k}.webp').convert('RGBA'))[..., 3] > 128

T = A('444')                                 # the title sprite ("Five / Nights / at / Freddy's")

def cell(a, i):
    return a[:, int(round(i * ADV)):int(round((i + 1) * ADV))]

def bottom(a):
    return np.where(a.any(1))[0].max() + 1

def flat_base(sprite, i):
    """Baseline row of glyph i (use a letter with no descender)."""
    return bottom(cell(sprite, i))

def render(ch, font, size):
    """A glyph rendered with a TrueType font, cropped tight (bottom row = baseline)."""
    f = ImageFont.truetype(font, size)
    im = Image.new('L', (60, 80), 0)
    ImageDraw.Draw(im).text((10, 10), ch, font=f, fill=255)
    a = np.asarray(im) > 110
    rows = np.where(a.any(1))[0]; cols = np.where(a.any(0))[0]
    return a[rows.min():rows.max() + 1, cols.min():cols.max() + 1]

def build_line(spec, H=44, BASE=33, W=201):
    """Lay glyphs out one per cell. spec items: ('cut', sprite, cell, baseline) or ('font', ch, size, dx, dy)."""
    out = np.zeros((H, W + 10), bool)
    for i, s in enumerate(spec):
        x0 = int(round(i * ADV))
        if s[0] == 'cut':
            _, sp, ci, base = s
            g = cell(sp, ci)
            dy = BASE - base
            for y in range(g.shape[0]):
                ty = y + dy
                if 0 <= ty < H:
                    w = min(g.shape[1], out.shape[1] - x0)
                    out[ty, x0:x0 + w] |= g[y, :w]
        else:
            _, ch, size, xoff, yoff = s
            g = render(ch, DV, size)
            ty0 = BASE - g.shape[0] + yoff
            tx0 = x0 + xoff
            out[ty0:ty0 + g.shape[0], tx0:tx0 + g.shape[1]] |= g
    return out[:, :W]
