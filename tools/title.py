"""fnaa title screen: four monochrome heads in a row + new copyright line."""
import numpy as np, cv2
from PIL import Image
from engine import src, resize, rotate, img
from paths import EX

def lum(rgb):
    """Red-weighted mono mix (like a red filter in B&W film): smoother skin, lips do not go black."""
    return rgb[..., 0] * .55 + rgb[..., 1] * .38 + rgb[..., 2] * .07
from scipy import ndimage as nd
from seqs import EYES

ORDER = ['chica_flick', 'bonnie_title', 'foxy_title', 'freddy_image1']   # left -> right; Freddy's swap is right-most
REF = 'freddy_image1'     # tonal reference face
D = 125           # eye distance of the right-most (largest) head
STEP = .78        # each head is this much smaller than the one on its right (depth / spacing effect)
DIM = .1          # each step back is also this much dimmer, so the row recedes into the dark
EYE_Y = 318       # shared eye line (camera at eye level, so eyes sit on the horizon)
FADE = (2.0, 3.6)     # neck/shoulder fade start/end, in eye-distances below the eye line
FADES = {'golden_freddy_image1': (4.2, 6.6)}     # Jensen: keep his jacket, fade only near the bottom
TOPFADE = {'foxy_title': .38, 'bonnie_title': .15}
OVERLAP = .42     # how far each head covers the one on its left, in that left head's eye-distances
X_RANGE = (376, 1240)
NUDGE = {1: -20, 2: -40, 3: -60}     # per-head x shift after spacing: tighter overlaps (1 Zuck, 2 Elon, 3 Altman)

# per-face size trim so faces read the same size before the depth scaling (Chica's swap has a wider face, Zuck's photo a narrower one)
K = {'freddy_image1': .98, 'chica_title': .94, 'bonnie_title': 1.057, 'foxy_title': 1.037,
     # flicker photos (3/4-view heads get a boost so the head, not the eye gap, matches)
     'chica_flick': .92, 'bonnie_flick': 1.0, 'foxy_flick': 1.0, 'freddy_flick': .92}
FLICK = {'chica_flick': 'chica_title', 'bonnie_title': 'bonnie_flick', 'foxy_title': 'foxy_flick', 'freddy_image1': 'freddy_flick'}

def depth(i):
    return STEP ** (len(ORDER) - 1 - i)

def Dof(i):
    return D * K[ORDER[i]] * depth(i)

def _head(name, Dn, rot=0.0):
    """Scaled, rotated cutout + eye midpoint in its own pixel space."""
    ex, ey, ed = EYES[name]
    c = src(name)
    h0, w0 = c.shape[:2]
    s = Dn / (ed * w0)
    c = resize(c, w0 * s, h0 * s)
    px, py = ex * c.shape[1], ey * c.shape[0]
    if name == 'chica_title':    # drop the hazy halo above his hair (before any fades)
        c[..., 3] = np.clip((c[..., 3] - .6) / .4, 0, 1)
    fa, fb = FADES.get(name, FADE)
    f0, f1 = py + fa * Dn, py + fb * Dn
    need = int(np.ceil(f1 - c.shape[0])) + 2
    if need > 0:
        c = _extend(c, need, Dn)
    yy = np.arange(c.shape[0])[:, None].astype(np.float32)
    t = np.clip((f1 - yy) / (f1 - f0), 0, 1); c[..., 3] *= t * t * (3 - 2 * t)          # smooth neck fade
    xx = np.arange(c.shape[1])[None, :].astype(np.float32)
    w = .75 * Dn
    if c[:, 0, 3].mean() > .05:              # photo was cropped through the left shoulder
        t = np.clip(xx / w, 0, 1); c[..., 3] *= t * t * (3 - 2 * t)
    if c[:, -1, 3].mean() > .05:             # ... or the right one
        t = np.clip((c.shape[1] - 1 - xx) / w, 0, 1); c[..., 3] *= t * t * (3 - 2 * t)
    if name in TOPFADE:          # photo cuts flat through the top of the hair: let it melt into the dark instead
        t = np.clip(yy / (TOPFADE[name] * Dn), 0, 1); c[..., 3] *= t * t * (3 - 2 * t)
    c, M = rotate(c, rot, ret_M=True)
    qx = M[0, 0] * px + M[0, 1] * py + M[0, 2]
    qy = M[1, 0] * px + M[1, 1] * py + M[1, 2]
    return c, qx, qy

def _extend(c, n, Dn):
    """Photo stops short (just under the chin): carry the bottom rows down into shadow so the neck can fade out."""
    k = 6
    a = c[-k:, :, 3:4]
    prem = (c[-k:, :, :3] * a).sum(0) / np.maximum(a.sum(0), 1e-4)
    al = a.mean(0)[:, 0]
    rows = []
    for i in range(1, n + 1):
        sig = 1 + i * .12
        rgb = cv2.GaussianBlur(prem[None], (0, 0), sigmaX=sig, sigmaY=.1)[0]
        aa = cv2.GaussianBlur(al[None], (0, 0), sigmaX=sig, sigmaY=.1)[0]
        rgb = rgb * np.exp(-i / (.55 * Dn))          # under-chin shadow deepens with distance
        rows.append(np.concatenate([rgb, aa[:, None]], 1))
    return np.concatenate([c, np.stack(rows, 0).astype(np.float32)], 0)

def _positions():
    """Centre x of each head: every head covers its left neighbour by OVERLAP of that neighbour's eye distance."""
    edges = []
    for i, n in enumerate(ORDER):
        c, qx, qy = _head(n, Dof(i))
        a = c[..., 3] > .5
        L, R = {}, {}
        for y in range(c.shape[0]):
            dy = y - int(qy)
            if a[y].any() and dy < 1.3 * Dof(i):
                L[dy] = np.where(a[y])[0].min() - qx; R[dy] = np.where(a[y])[0].max() - qx
        edges.append((L, R))
    xs = [0.0]
    for i in range(1, len(ORDER)):
        Rp = edges[i - 1][1]; Ln = edges[i][0]
        need = max(xs[-1] + Rp[y] - Ln[y] for y in Rp if y in Ln)
        xs.append(need - OVERLAP * Dof(i - 1))
    left = xs[0] + min(edges[0][0].values())
    right = xs[-1] + max(edges[-1][1].values())
    shift = (X_RANGE[0] + X_RANGE[1]) / 2 - (left + right) / 2
    return [x + shift for x in xs], (left + shift, right + shift)

_POS = None

def _face_mask(c, qx, qy, Dn):
    hh, ww = c.shape[:2]
    yy, xx = np.mgrid[0:hh, 0:ww]
    e = ((xx - qx) / (.95 * Dn)) ** 2 + ((yy - qy - .35 * Dn) / (1.05 * Dn)) ** 2 < 1
    return e & (c[..., 3] > .9)

def _ref_cdf():
    Dn = D * K[REF]
    c, qx, qy = _head(REF, Dn)
    L = lum(c[..., :3])
    return np.sort(L[_face_mask(c, qx, qy, Dn)])

def _match(c, ref, qx, qy, Dn):
    """Map the head's tones so its face (skin, eyes, mouth) has the same tonal spread as the reference face."""
    L = lum(c[..., :3])
    v = np.sort(L[_face_mask(c, qx, qy, Dn)])
    q = np.interp(L, v, np.linspace(0, 1, len(v)))
    return np.interp(q, np.linspace(0, 1, len(ref)), ref)

def _tone(L):
    """Map matched luminance onto the dim title look."""
    return np.clip(.012 + .62 * np.clip(L, 0, 1) ** 1.55, 0, 1)

# Jensen stands at the far left edge, mostly off screen, dim enough that the menu reads over him
JENSEN = dict(name='golden_freddy_image1', mid=(100, 300), D=64, dim=.5, alpha=.5, lift=.7)   # smaller, see-through: fainter than the main four

def _paint_jensen(canvas, ref):
    n, Dj = JENSEN['name'], JENSEN['D']
    c, qx, qy = _head(n, Dj)
    L = (_tone(_match(c, ref, qx, qy, Dj)) ** JENSEN['lift']) * JENSEN['dim']   # lift shadows so the jacket reads
    hh, ww = L.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    r = np.sqrt(((xx - qx) / (1.9 * Dj)) ** 2 + ((yy - qy + .2 * Dj) / (2.4 * Dj)) ** 2)
    L = L * np.clip(1.15 - .45 * r ** 2, .35, 1)
    a = cv2.GaussianBlur(c[..., 3], (0, 0), .9)
    cx, cy = JENSEN['mid']
    x0, y0 = int(round(cx - qx)), int(round(cy - qy))
    xs0, ys0 = max(0, -x0), max(0, -y0)
    xd0, yd0 = max(0, x0), max(0, y0)
    xd1, yd1 = min(1280, x0 + ww), min(720, y0 + hh)
    sub_a = a[ys0:ys0 + yd1 - yd0, xs0:xs0 + xd1 - xd0][..., None] * JENSEN['alpha']
    sub_L = L[ys0:ys0 + yd1 - yd0, xs0:xs0 + xd1 - xd0][..., None]
    canvas[yd0:yd1, xd0:xd1] = canvas[yd0:yd1, xd0:xd1] * (1 - sub_a) + sub_L * sub_a

def lineup(twitch=None, hollow=False, seed=0, swap=None):
    """twitch = (index, dx, dy, rot) to jerk one head; hollow = black out every pair of eyes."""
    global _POS
    if _POS is None: _POS = _positions()
    ref = _ref_cdf()
    canvas = np.zeros((720, 1280, 3), np.float32)
    _paint_jensen(canvas, ref)
    eyes = []
    for i, name in enumerate(ORDER):          # painted left -> right, so each head covers the one on its left
        Dn = Dof(i)
        if swap is not None and swap == i:     # this head flickers to its alternate photo
            name = FLICK[name]; Dn = D * K[name] * depth(i)
        cx, cy = _POS[0][i] + NUDGE.get(i, 0), EYE_Y
        rot = 0.0
        if twitch and twitch[0] == i:
            cx += twitch[1]; cy += twitch[2]; rot = twitch[3]
        c, qx, qy = _head(name, Dn, rot)
        L = _tone(_match(c, ref, qx, qy, Dn)) * (1 - DIM * (len(ORDER) - 1 - i))
        hh, ww = L.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        r = np.sqrt(((xx - qx) / (1.9 * Dn)) ** 2 + ((yy - qy + .2 * Dn) / (2.4 * Dn)) ** 2)
        L = L * np.clip(1.15 - .45 * r ** 2, .35, 1)
        er = 3 if name in ('chica_title', 'chica_flick') else 1          # his cutout carries a light fringe from the white backdrop
        a = cv2.GaussianBlur(cv2.erode(c[..., 3], np.ones((2 * er + 1, 2 * er + 1), np.uint8)), (0, 0), .9)
        x0, y0 = int(round(cx - qx)), int(round(cy - qy))
        xs0, ys0 = max(0, -x0), max(0, -y0)
        xd0, yd0 = max(0, x0), max(0, y0)
        xd1, yd1 = min(1280, x0 + ww), min(720, y0 + hh)
        sub_a = a[ys0:ys0 + yd1 - yd0, xs0:xs0 + xd1 - xd0][..., None]
        sub_L = L[ys0:ys0 + yd1 - yd0, xs0:xs0 + xd1 - xd0][..., None]
        reg = canvas[yd0:yd1, xd0:xd1]
        canvas[yd0:yd1, xd0:xd1] = reg * (1 - sub_a) + sub_L * sub_a
        eyes.append((cx, cy, Dn))
    if hollow:
        yy, xx = np.mgrid[0:720, 0:1280]
        m = np.zeros((720, 1280), np.float32)
        for cx, cy, Dn in eyes:
            for sgn in (-1, 1):
                ex, ey = cx + sgn * Dn / 2, cy
                m = np.maximum(m, np.clip(1.5 - np.sqrt(((xx - ex) / (.30 * Dn)) ** 2 + ((yy - ey) / (.19 * Dn)) ** 2), 0, 1))
        m = cv2.GaussianBlur(m, (0, 0), 3)
        canvas *= (1 - .97 * m[..., None])
    rng = np.random.default_rng(seed)
    canvas += rng.normal(0, .008, canvas.shape[:2])[..., None]
    out = np.zeros((720, 1280, 4), np.float32)
    out[..., :3] = np.clip(canvas, 0, 1); out[..., 3] = 1
    return out

def title_frames():
    # ORDER = chica, bonnie, foxy, freddy (left -> right)
    return {
        '431': lineup(seed=1),
        '440': lineup(swap=0, seed=2),     # Chica flicker
        '441': lineup(swap=1, seed=3),     # Bonnie flicker
        '442': lineup(swap=2, seed=4),     # Foxy flicker
        '900': lineup(swap=3, seed=5),     # Freddy flicker (new frame id)
    }

# ------------------------------------------------------------------ copyright sprite (226x14, white pixel font, 12 px cells)
NEW = {
    '6': ["............", ".....####...", "...######...", "..###.......", "..##........", ".##.........", ".##.####....",
          ".########...", ".###...###..", ".##.....##..", ".##.....##..", ".###...###..", "..#######...", "...#####...."],
    'A': ["............", ".....##.....", ".....##.....", "....####....", "....####....", "...##..##...", "...##..##...",
          "..##....##..", "..########..", "..########..", ".##......##.", ".##......##.", ".##......##.", ".##......##."],
    'M': ["............", ".##......##.", ".###....###.", ".####..####.", ".##.####.##.", ".##..##..##.", ".##..##..##.",
          ".##......##.", ".##......##.", ".##......##.", ".##......##.", ".##......##.", ".##......##.", ".##......##."],
    'u': ["............", "............", "............", "............", "..##....##..", "..##....##..", "..##....##..",
          "..##....##..", "..##....##..", "..##....##..", "..##....##..", "..##...###..", "..########..", "...####.##.."],
    'b': ["..##........", "..##........", "..##........", "..##........", "..##.####...", "..########..", "..###...###.",
          "..##.....##.", "..##.....##.", "..##.....##.", "..##.....##.", "..###...###.", "..########..", "..##.####..."],
    'd': ["........##..", "........##..", "........##..", "........##..", "...####.##..", "..########..", ".###...###..",
          ".##.....##..", ".##.....##..", ".##.....##..", ".##.....##..", ".###...###..", "..########..", "...####.##.."],
    'l': ["..#####.....", "..#####.....", ".....##.....", ".....##.....", ".....##.....", ".....##.....", ".....##.....",
          ".....##.....", ".....##.....", ".....##.....", ".....##.....", ".....##.....", "..########..", "..########.."],
}

def copyright_sprite(text='©2026 Abdullah Sultan'):
    o = np.asarray(Image.open(EX / '433.webp').convert('RGBA'))[..., 3] > 128
    o = np.pad(o, ((0, 0), (0, 12)))
    old = '©2014 Scott Cawthon'
    cells = {}
    for i, ch in enumerate(old):
        if ch not in cells: cells[ch] = o[:, 12 * i:12 * i + 12]
    for ch, rows in NEW.items():
        cells[ch] = np.array([[c == '#' for c in r] for r in rows])
    cells[' '] = np.zeros((14, 12), bool)
    strip = np.concatenate([cells[ch] for ch in text], 1)
    cols = np.where(strip.any(0))[0]
    strip = strip[:, :cols.max() + 1]
    Wd = max(226, strip.shape[1])                   # widened for the longer name; the game right-aligns it
    out = np.zeros((14, Wd), bool)
    out[:, Wd - strip.shape[1]:] = strip
    rgba = np.zeros((14, Wd, 4), np.float32)
    rgba[out] = 1
    return {'433': rgba}
