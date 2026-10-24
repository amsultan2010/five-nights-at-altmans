from engine import *

def head_center(m, frac=.2):
    """x-centre of the top `frac` of the mask's height, plus top/bottom rows."""
    bb = bbox(m)
    if bb is None: return None
    x0, y0, x1, y1 = bb
    yh = int(y0 + (y1 - y0) * frac)
    ys, xs = np.where(m[y0:yh + 1])
    return float(xs.mean()), y0, y1

def layer(base, name, at, box=(0, 0, 1, 1), flip=False, rot=0, mean=.2, sat=.55, contrast=1.0,
          tint=None, tint_s=.8, clip=None, light=None, light_s=.7, blur=.7, noise=.015, seed=0,
          feather=1.0, gamma=1.0, opacity=1.0, anchor='top', ax=.5, fade=None):
    """at = (x, y, height). anchor: 'top' -> y is top of cutout, 'bottom' -> y is bottom, 'center'.
    ax = fraction of the cutout width that lands on x (default centre)."""
    c = cut(name, box, flip)
    x, y, hgt = at
    c = fit(c, h=hgt)
    if fade:
        ft, fb = fade
        hh = c.shape[0]; ramp = np.ones(hh, np.float32)
        if fb: n = max(1, int(hh * fb)); ramp[-n:] = np.linspace(1, 0, n)
        if ft: n = max(1, int(hh * ft)); ramp[:n] = np.minimum(ramp[:n], np.linspace(0, 1, n))
        c[..., 3] *= ramp[:, None]
    c = rotate(c, rot)
    h, w = c.shape[:2]
    if tint is None:
        bx0 = int(x - w / 2); by0 = int(y if anchor == 'top' else y - h)
        tint = ambient_tint(base[..., :3], (max(0, bx0), max(0, by0), min(base.shape[1], bx0 + w), min(base.shape[0], by0 + h)))
    c = grade(c, mean, sat=sat, contrast=contrast, tint=tint, tint_s=tint_s, gamma=gamma)
    px = x - w * ax
    py = y if anchor == 'top' else (y - h if anchor == 'bottom' else y - h / 2)
    return paste(base, c, px, py, clip=clip, light=light, light_s=light_s, blur=blur, noise=noise, feather=feather, opacity=opacity, seed=seed)
