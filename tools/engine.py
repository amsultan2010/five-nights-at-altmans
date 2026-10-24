"""Compositing engine: put real-person cutouts into FNAF scenes."""
import numpy as np, cv2, os
from PIL import Image
from scipy import ndimage as nd

from paths import EX, PHOTOS as SRC
_cache = {}

def img(k):
    """Original game image as float RGB 0..1 (or RGBA if it has alpha)."""
    key = ('img', k)
    if key not in _cache:
        im = Image.open(f'{EX}/{k}.webp')
        _cache[key] = (np.asarray(im.convert('RGBA')).astype(np.float32) / 255, im.mode)
    a, mode = _cache[key]
    return a.copy()

def src(name):
    key = ('src', name)
    if key not in _cache:
        c = np.asarray(Image.open(f'{SRC}/{name}.png').convert('RGBA')).astype(np.float32) / 255
        # edge decontamination: replace fringe colours with colour pulled from the interior
        h, w = c.shape[:2]
        k = max(2, int(min(h, w) / 250))
        a = c[..., 3]
        inner = nd.binary_erosion(a > .98, iterations=k)
        wgt = inner.astype(np.float32)
        s = 2.5 * k
        num = cv2.GaussianBlur(c[..., :3] * wgt[..., None], (0, 0), s)
        den = cv2.GaussianBlur(wgt, (0, 0), s)
        fill = num / np.maximum(den, 1e-4)[..., None]
        band = (a > 0) & ~inner & (den > 1e-3)
        c[..., :3][band] = fill[band]
        c[..., 3] = np.clip((a - .2) / .8, 0, 1)   # slight choke
        _cache[key] = c
    return _cache[key].copy()

def lum(rgb):
    return rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114

def diffmask(a, b, th=18 / 255, dil=0):
    A, B = img(a)[..., :3], img(b)[..., :3]
    d = np.abs(A - B).max(2)
    m = d > th
    m = nd.binary_opening(m, iterations=2)
    m = nd.binary_closing(m, iterations=6)
    lab, n = nd.label(m)
    if n:
        sizes = nd.sum(m, lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > max(400, .05 * sizes.max())])
        m = keep
    if dil: m = nd.binary_dilation(m, iterations=dil)
    return m

def bbox(m):
    ys, xs = np.where(m)
    if len(xs) == 0: return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1

def cut(name, box=(0, 0, 1, 1), flip=False):
    """Crop a cutout by fractional box (x0,y0,x1,y1) of its content bbox."""
    c = src(name)
    h, w = c.shape[:2]
    x0, y0, x1, y1 = box
    c = c[int(y0 * h):int(round(y1 * h)), int(x0 * w):int(round(x1 * w))]
    if flip: c = c[:, ::-1]
    return np.ascontiguousarray(c)

def grade(c, mean, sat=.6, contrast=1.0, tint=(1, 1, 1), tint_s=1.0, gamma=1.0):
    """Relight cutout: set mean luminance (over opaque px), contrast, desaturate, tint."""
    rgb, a = c[..., :3], c[..., 3]
    Y = lum(rgb)
    w = a > .5
    mY = max(1e-4, (Y[w]).mean()) if w.any() else max(1e-4, Y.mean())
    Yn = np.clip(Y / mY, 0, 50) ** contrast
    Yn = Yn / max(1e-4, Yn[w].mean() if w.any() else Yn.mean())
    Y2 = mean * Yn
    if gamma != 1.0: Y2 = np.clip(Y2, 0, 1) ** gamma
    ratio = Y2 / np.maximum(Y, 1e-4)
    col = rgb * ratio[..., None]
    grey = np.repeat(Y2[..., None], 3, 2)
    out = grey + (col - grey) * sat
    t = np.array(tint, np.float32)
    t = 1 + (t - 1) * tint_s
    out = out * t
    c = c.copy(); c[..., :3] = np.clip(out, 0, 1)
    return c

def ambient_tint(base_rgb, box, pad=60):
    """Normalised colour of the base image around a region (for tinting)."""
    H, W = base_rgb.shape[:2]
    x0, y0, x1, y1 = box
    r = base_rgb[max(0, y0 - pad):min(H, y1 + pad), max(0, x0 - pad):min(W, x1 + pad)].reshape(-1, 3)
    m = r.mean(0) + 1e-3
    return tuple(m / lum(m[None])[0])

def resize(c, w, h):
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    interp = cv2.INTER_AREA if w < c.shape[1] else cv2.INTER_CUBIC
    # premultiply to avoid fringe
    p = c.copy(); p[..., :3] *= p[..., 3:4]
    r = cv2.resize(p, (w, h), interpolation=interp)
    r = np.clip(r, 0, 1)
    a = r[..., 3:4]
    r[..., :3] = np.where(a > 1e-4, r[..., :3] / np.maximum(a, 1e-4), 0)
    return np.clip(r, 0, 1)

def rotate(c, deg, ret_M=False):
    if not deg:
        return (c, np.array([[1, 0, 0], [0, 1, 0]], np.float64)) if ret_M else c
    h, w = c.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    M[0, 2] += nw / 2 - w / 2; M[1, 2] += nh / 2 - h / 2
    p = c.copy(); p[..., :3] *= p[..., 3:4]
    r = cv2.warpAffine(p, M, (nw, nh), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    r = np.clip(r, 0, 1); a = r[..., 3:4]
    r[..., :3] = np.where(a > 1e-4, r[..., :3] / np.maximum(a, 1e-4), 0)
    return (r, M) if ret_M else r

def lightmap(orig_rgb, mask, sigma=40):
    """Spatial light falloff of the original character region, normalised to mean 1."""
    Y = lum(orig_rgb)
    m = mask.astype(np.float32)
    num = cv2.GaussianBlur(Y * m, (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)
    L = np.where(den > 1e-3, num / np.maximum(den, 1e-3), np.nan)
    mean = np.nanmean(L[mask]) if mask.any() else 1
    L = np.where(np.isnan(L), mean, L) / max(mean, 1e-4)
    return L

def paste(base, c, x, y, clip=None, light=None, light_s=1.0, blur=0.6, noise=0.0, feather=1.0, opacity=1.0, seed=0):
    """Alpha-composite cutout c (RGBA) onto base (RGB/RGBA float) with top-left at (x, y)."""
    H, W = base.shape[:2]
    h, w = c.shape[:2]
    x, y = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x), max(0, -y)
    dx0, dy0 = max(0, x), max(0, y)
    dx1, dy1 = min(W, x + w), min(H, y + h)
    if dx1 <= dx0 or dy1 <= dy0: return base
    cc = c[sy0:sy0 + (dy1 - dy0), sx0:sx0 + (dx1 - dx0)].copy()
    rgb, a = cc[..., :3], cc[..., 3]
    if blur: rgb = cv2.GaussianBlur(rgb, (0, 0), blur)
    if feather: a = cv2.GaussianBlur(a, (0, 0), feather)
    if light is not None:
        L = light[dy0:dy1, dx0:dx1]
        rgb = rgb * (1 + (L[..., None] - 1) * light_s)
    if noise:
        rng = np.random.default_rng(seed)
        rgb = rgb + rng.normal(0, noise, rgb.shape[:2])[..., None].astype(np.float32)
    rgb = np.clip(rgb, 0, 1)
    if clip is not None:
        a = a * clip[dy0:dy1, dx0:dx1]
    a = a * opacity
    region = base[dy0:dy1, dx0:dx1]
    region[..., :3] = region[..., :3] * (1 - a[..., None]) + rgb * a[..., None]
    if base.shape[2] == 4:
        region[..., 3] = region[..., 3] * (1 - a) + a
    base[dy0:dy1, dx0:dx1] = region
    return base

def fit(c, h=None, w=None):
    ch, cw = c.shape[:2]
    if h is not None: s = h / ch
    else: s = w / cw
    return resize(c, cw * s, ch * s)

def save(arr, k, outdir, q=82):
    os.makedirs(outdir, exist_ok=True)
    a = np.clip(arr * 255 + .5, 0, 255).astype(np.uint8)
    mode = 'RGBA' if a.shape[2] == 4 and (a[..., 3] < 255).any() else 'RGB'
    im = Image.fromarray(a if mode == 'RGBA' else a[..., :3], mode)
    im.save(f'{outdir}/{k}.webp', 'WEBP', quality=q, method=6)
    return im

def region_mean(k, mask):
    Y = lum(img(k)[..., :3])
    return float(Y[mask].mean())
