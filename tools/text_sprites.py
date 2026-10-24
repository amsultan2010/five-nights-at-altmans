"""Text sprites in the game's pixel font: the 'Five Nights at Altman's' title and the
Custom Night name labels. Returns uint8 RGBA arrays (white text on transparent)."""
import numpy as np
from pixelfont import T, A, ADV, flat_base, build_line

L1 = T[0:34]; L2 = T[56:100]; L4 = T[168:212]          # "Five", "Nights", "Freddy's"
G448 = A('448'); G449 = A('449'); G533 = A('533')        # "New Game", "Continue", "Chica"
B = {'L1': flat_base(L1, 0), 'L2': flat_base(L2, 0), 'L4': flat_base(L4, 0), '448': flat_base(G448, 0),
     '449': flat_base(G449, 2), '533': flat_base(G533, 1)}
GLYPH = {
    't': ('cut', L2, 4, B['L2']), 'h': ('cut', L2, 3, B['L2']), 'e': ('cut', L1, 3, B['L1']), 'i': ('cut', L1, 1, B['L1']),
    'm': ('cut', G448, 6, B['448']), 'a': ('cut', G448, 5, B['448']), 'n': ('cut', G449, 2, B['449']),
    'o': ('cut', G449, 1, B['449']), 'u': ('cut', G449, 6, B['449']), 'r': ('cut', L4, 1, B['L4']),
    'c': ('cut', G533, 3, B['533']), "'": ('cut', L4, 6, B['L4']), 's': ('cut', L4, 7, B['L4']),
    'A': ('font', 'A', 42, 1, 0), 'l': ('font', 'l', 42, 3, 0), 'T': ('font', 'T', 42, 1, 0), 'Z': ('font', 'Z', 42, 2, 0),
    'k': ('font', 'k', 42, 2, 0), 'E': ('font', 'E', 42, 3, 0), 'D': ('font', 'D', 42, 2, 0),
}
NAMES = {'531': 'Altman', '535': 'The Zuck', '533': 'Dario', '534': 'Elon'}   # Custom Night labels

def _rgba(mask):
    out = np.zeros(mask.shape + (4,), np.uint8); out[mask] = 255
    return out

def title_logo():
    """444: the title, with the last line rewritten from "Freddy's" to "Altman's"."""
    spec = [GLYPH[c] for c in "Altman's"]
    line = build_line(spec, BASE=B['L4'])
    mask = T.copy()
    mask[168:212] = False
    mask[168:212, :line.shape[1]] = line
    return {'444': _rgba(mask)}

def name_sprite(text):
    W = int(round(len(text) * ADV)) + 4
    line = np.zeros((50, W), bool)
    for i, ch in enumerate(text):
        if ch == ' ': continue
        g = build_line([GLYPH[ch]], H=50, BASE=36, W=W)
        x0 = int(round(i * ADV)); line[:, x0:] |= g[:, :W - x0]
    rows = np.where(line.any(1))[0]; cols = np.where(line.any(0))[0]
    return _rgba(line[rows.min():rows.max() + 1, cols.min():cols.max() + 1])

def name_labels():
    return {k: name_sprite(t) for k, t in NAMES.items()}
