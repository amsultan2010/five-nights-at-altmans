"""Animated sequences, full-screen faces, title/menu art."""
from layer import *
import math

# eye data per face source: (mid_x_frac, mid_y_frac, eye_dist_frac_of_width)
EYES = {
    'bonnie_title': (.585, .37, .23),
    'chica_title': (.49, .35, .14),
    'foxy_title': (.50, .48, .26),
    'freddy_title': (.50, .40, .14),
    'freddy_image1': (.50, .37, .14),
    'golden_freddy_image1': (.628, .183, .156),
    'foxy_image9': (.634, .168, .131),
    'goldenfred': (.415, .20, .17),
    'foxy_image2': (.51, .13, .04),
    'fred1022': (.454, .23, .1375),
    'chica12041': (.547, .164, .106),
    'fred67': (.5075, .133, .135),
    'chica_flick': (.500, .473, .188),
    'foxy_flick': (.286, .519, .183),
    'freddy_flick': (.382, .455, .143),
    'bonnie_flick': (.522, .241, .194),
}

def by_eyes(base, name, mid, dist, rot=0, mean=.2, sat=.55, contrast=1.0, tint=None, tint_s=.8, blur=.7,
            noise=.015, seed=0, light=None, light_s=.7, fade=None, opacity=1.0, clip=None, box=None):
    """Place a face so that its eye midpoint lands on `mid` with eye spacing `dist` px."""
    ex, ey, ed = EYES[name]
    c = src(name)
    if box:
        h0, w0 = c.shape[:2]
        x0, y0, x1, y1 = box
        c = c[int(y0 * h0):int(y1 * h0), int(x0 * w0):int(x1 * w0)]
        ex = (ex - x0) / (x1 - x0); ey = (ey - y0) / (y1 - y0); ed = ed / (x1 - x0)
    h0, w0 = c.shape[:2]
    s = dist / (ed * w0)
    # crop the source to what can land on the canvas (keeps huge zooms cheap)
    H, W = base.shape[:2]
    exp_ = ex * w0, ey * h0
    mg = .35 * max(W, H) / s
    sx0 = max(0, int(exp_[0] - mid[0] / s - mg)); sx1 = min(w0, int(exp_[0] + (W - mid[0]) / s + mg))
    sy0 = max(0, int(exp_[1] - mid[1] / s - mg)); sy1 = min(h0, int(exp_[1] + (H - mid[1]) / s + mg))
    if sx1 - sx0 < 2 or sy1 - sy0 < 2: return base
    c = c[sy0:sy1, sx0:sx1]
    ex = (exp_[0] - sx0) / (sx1 - sx0); ey = (exp_[1] - sy0) / (sy1 - sy0)
    h0, w0 = c.shape[:2]
    c = resize(c, w0 * s, h0 * s)
    if fade:
        ft, fb = fade
        hh = c.shape[0]; ramp = np.ones(hh, np.float32)
        if fb: n = max(1, int(hh * fb)); ramp[-n:] = np.linspace(1, 0, n)
        if ft: n = max(1, int(hh * ft)); ramp[:n] = np.minimum(ramp[:n], np.linspace(0, 1, n))
        c[..., 3] *= ramp[:, None]
    px, py = ex * c.shape[1], ey * c.shape[0]
    c, M = rotate(c, rot, ret_M=True)
    qx = M[0, 0] * px + M[0, 1] * py + M[0, 2]
    qy = M[1, 0] * px + M[1, 1] * py + M[1, 2]
    if tint is None:
        tint = ambient_tint(base[..., :3], (0, 0, base.shape[1], base.shape[0]))
    c = grade(c, mean, sat=sat, contrast=contrast, tint=tint, tint_s=tint_s)
    return paste(base, c, mid[0] - qx, mid[1] - qy, clip=clip, light=light, light_s=light_s,
                 blur=blur, noise=noise, opacity=opacity, seed=seed)

def black(w=1280, h=720, alpha=False):
    a = np.zeros((h, w, 4), np.float32); a[..., 3] = 1
    return a

def vignette(arr, strength=.6, cx=None, cy=None, r=None):
    H, W = arr.shape[:2]
    cx = W / 2 if cx is None else cx; cy = H / 2 if cy is None else cy; r = r or max(W, H) * .6
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    v = np.clip(1 - strength * d ** 2, 0, 1)
    out = arr.copy(); out[..., :3] *= v[..., None]
    return out

def selflight(k, th=.03, sig=50):
    o = img(k)[..., :3]
    m = lum(o) > th
    return lightmap(o, m, sig)

# ------------------------------------------------------------------ Foxy run down CAM 2A
RUN = [241, 244, 245, 246, 247, 248, 250, 280, 282, 283, 284, 285, 286, 287, 288, 289, 290, 292, 302, 306,
       327, 329, 330, 331, 332, 333, 334, 335, 336, 337]

def run_frames():
    out = {}
    n = len(RUN)
    for i, k in enumerate(RUN):
        base = img('44')
        bob = (8 if i % 2 else -8)
        tilt = (3 if i % 2 else -3)
        if i <= 6:      # far end of the hall, starting to run
            h = 270 + i * 8; top = 160 + bob * .5; x = 1030; mean = .05 + i * .002
        elif i <= 16:   # charging closer
            u = (i - 6) / 10
            h = 330 * (3.6 ** u); top = 160 - 90 * u + bob; x = 1030 - 40 * u; mean = .065 + .09 * u
        elif i <= 20:   # right in the lens
            u = (i - 16) / 4
            h = 1190 + 330 * u; top = 70 - 45 * u + bob; x = 990 - 60 * u; mean = .16
        elif i <= 25:   # swerving out of frame to the left, past the camera
            u = (i - 20) / 5
            h = 1520 + 150 * u; top = 25 + 10 * u; x = 930 - 1250 * u ** 1.3; mean = .16 - .05 * u; tilt = -5 - 9 * u
        else:
            out[k] = base; continue
        out[k] = layer(base, 'foxy_image1', at=(x, top, h), ax=.4, rot=tilt, mean=mean, sat=.5,
                       blur=.7 + (.8 if i > 15 else 0) + (1.6 if i > 20 else 0), seed=100 + i)
    return out

# ------------------------------------------------------------------ office jumpscares (1600x720, base 126)
def js_bonnie():
    ids = [291, 293, 294, 295, 296, 297, 298, 299, 300, 301, 303]
    hx = [894, 853, 944, 1011, 1024, 960, 862, 893, 913, 885, 907]
    rot = [0, -6, -12, -15, -11, -5, 2, 0, 4, -2, 1]
    dist = [205, 215, 228, 236, 230, 220, 210, 205, 208, 202, 206]
    ey = [300, 310, 330, 345, 340, 320, 305, 300, 302, 298, 300]
    out = {}
    for i, k in enumerate(ids):
        b = img('126')
        out[k] = by_eyes(b, 'bonnie_title', (hx[i] - 250, ey[i] + 20), dist[i] * 1.4, rot=rot[i], mean=.22, sat=.75,
                         contrast=1.3, tint_s=.35, seed=200 + i, blur=.9)
    return out

def js_chica():
    ids = [65, 69, 216, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 239, 279, 281]
    hx = [563, 592, 640, 663, 674, 685, 687, 670, 617, 575, 619, 524, 549, 560, 565, 569]
    rot = [-8, -4, 0, 4, 6, 4, 0, -4, -8, -10, -6, -2, 2, 6, 4, 0]
    out = {}
    for i, k in enumerate(ids):
        b = img('126')
        d = 205 + 8 * math.sin(i * 1.3)
        out[k] = by_eyes(b, 'chica_title', (hx[i] + 40, 270 + 10 * math.sin(i * 2.1)), d, rot=rot[i], mean=.26,
                         sat=.75, contrast=1.3, tint_s=.35, seed=300 + i, blur=.9)
    return out

def js_foxy():
    """Elon's face (his title photo): rushes in from the left door, then lunges and shakes in the lens.
    The game centres the view (scroll 160) when he strikes, so the screen centre is x = 800 here."""
    ids = [413, 415, 242, 243, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412]
    out = {}
    for i, k in enumerate(ids):
        b = img('126')
        if i < 4:          # coming through the left doorway
            u = i / 3
            mid = (200 + 450 * u, 340 - 20 * u); d = 130 + 90 * u; rot = 14 - 10 * u; bl = 2.2 - .9 * u
        else:              # lunge, then violent shake right in your face
            j = i - 4; u = min(1, j / 4)
            sh = (22 * math.sin(j * 2.1), 14 * math.cos(j * 2.9))
            mid = (650 + 150 * u + sh[0] * u, 285 + sh[1] * u); d = 225 + 60 * u + 8 * math.sin(j * 1.7) * u
            rot = 5 * math.sin(j * 1.3) * u; bl = .9
        out[k] = by_eyes(b, 'foxy_title', mid, d, rot=rot, mean=.24, sat=.75, contrast=1.3, tint_s=.35,
                         seed=400 + i, blur=bl, fade=(0, .17))
    return out

def js_freddy():
    ids = [489, 490, 491, 493, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510,
           511, 512, 513, 514, 515, 516, 517, 518]
    out = {}
    for i, k in enumerate(ids):
        b = img('126')
        if i < 5:   # rising up from the bottom-right
            u = i / 4
            mid = (1400 - 330 * u, 820 - 520 * u); d = 150 + 90 * u; rot = 25 - 20 * u
        else:       # filling the screen, head jerking
            j = i - 5
            mid = (820 + 70 * math.sin(j * .9) - 4 * j, 300 + 25 * math.sin(j * 1.7)); d = 320 + 30 * math.sin(j * .6)
            rot = 8 * math.sin(j * 1.1)
        out[k] = by_eyes(b, 'freddy_title', mid, d, rot=rot, mean=.13, sat=1, contrast=1.1,
                         tint=(1.25, .95, .7), tint_s=1, seed=500 + i, blur=.9)
    return out

def js_freddy_dark():
    ids = [326, 307, 348, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325]
    out = {}
    warm = (1.3, .95, .65)
    for i, k in enumerate(ids):
        b = black()
        if i == 0:
            out[k] = b; continue
        if i <= 5:    # rising from below
            u = (i - 1) / 4
            mid = (640, 1080 - 600 * u); d = 150; rot = 0
        elif i <= 13:  # face swaying in the dark
            j = i - 6
            mid = (640 + 40 * math.sin(j * .8), 300 + 10 * math.sin(j * 1.3)); d = 150 + 8 * j; rot = 4 * math.sin(j * .7)
        else:          # zoom into one eye
            j = (i - 13) / 7
            z = 1.0 + 7 * j ** 1.6
            d = 214 * z
            # keep his left eye (screen-left) drifting to the centre
            mid = (640 + d / 2 * min(1, j * 1.4), 330 + 20 * j); rot = 0
        f = by_eyes(b, 'freddy_image1', mid, d, rot=rot, mean=.2, sat=1, contrast=1.25, tint=warm, tint_s=1,
                    seed=600 + i, blur=.8, noise=.02)
        out[k] = vignette(f, .9, 640, 330, 700)
    return out

# ------------------------------------------------------------------ title screen + creepy faces
def title_faces():
    out = {}
    L = selflight('431', .02, 60)
    out['431'] = by_eyes(black(), 'freddy_title', (930, 290), 235, mean=.07, sat=.5, contrast=1.45,
                         tint=(.9, 1.05, .85), tint_s=1, light=L, light_s=.9, seed=700, fade=(0, .15))
    out['440'] = by_eyes(black(), 'freddy_title', (960, 320), 260, rot=7, mean=.085, sat=.5, contrast=1.5,
                         tint=(.9, 1.05, .85), tint_s=1, light=L, light_s=.9, seed=701, fade=(0, .15))
    out['441'] = by_eyes(black(), 'freddy_title', (900, 280), 225, rot=-6, mean=.08, sat=.5, contrast=1.5,
                         tint=(.9, 1.05, .85), tint_s=1, light=L, light_s=.9, seed=702, fade=(0, .15))
    out['442'] = by_eyes(black(), 'freddy_image1', (1000, 300), 120, mean=.16, sat=0, contrast=1.6,
                         tint=(1, 1, 1), tint_s=1, seed=703, fade=(0, .2))
    purple = (1.05, .9, 1.35)
    z = by_eyes(black(), 'bonnie_title', (650, 300), 300, mean=.13, sat=.4, contrast=1.2, tint=purple, tint_s=1,
                seed=704, fade=(0, .1))
    out['520'] = vignette(z, .7)
    # eyeless variant (also used as a hallucination flash)
    e = z.copy()
    ex, ey, ed = EYES['bonnie_title']
    yy, xx = np.mgrid[0:720, 0:1280]
    m = np.zeros((720, 1280), np.float32)
    for dx in (-150, 150):
        cx, cy = 650 + dx, 300
        m = np.maximum(m, np.clip(1.6 - np.sqrt(((xx - cx) / 78) ** 2 + ((yy - cy) / 52) ** 2) * 1.2, 0, 1))
    m = cv2.GaussianBlur(m, (0, 0), 6)
    e[..., :3] *= (1 - m[..., None])
    out['545'] = vignette(e, .7)
    out['525'] = vignette(by_eyes(black(), 'freddy_flick', (640, 330), 300, rot=0, mean=.3, sat=.7, contrast=1.1,
                                  tint=(1.25, .95, .7), tint_s=1, seed=705), .5)
    out['548'] = vignette(by_eyes(black(), 'golden_freddy_image1', (660, 300), 360, mean=.35, sat=.8, contrast=1.5,
                                  tint=(1.45, 1.15, .35), tint_s=1, seed=706), .5)
    return out

def golden_office():
    """573: Golden Freddy slumped in the office (541x521 RGBA sprite)."""
    spr = np.zeros((521, 541, 4), np.float32)
    spr = layer(spr, 'goldenfred', at=(270, 30, 560), rot=-10, mean=.12, sat=.6, contrast=1.15,
                tint=(1.5, 1.2, .3), tint_s=1, seed=707, fade=(0, .12), noise=.01)
    return {'573': spr}

def portraits():
    out = {}
    for k, name, d, mid in [('527', 'fred1022', 50, (100, 90)), ('528', 'bonnie_title', 70, (100, 88)),
                            ('529', 'chica12041', 50, (100, 90)), ('536', 'foxy_image9', 62, (100, 88))]:
        o = img(k)
        bg = o.copy()
        bg[..., :3] = cv2.GaussianBlur(o[..., :3], (0, 0), 14) * .75
        out[k] = by_eyes(bg, name, mid, d, mean=.42, sat=.9, contrast=1.05, tint=(1, 1, 1), tint_s=0,
                         seed=710, blur=.4, noise=.008)
    return out

def ending(k):
    """Paycheck / pink-slip screens: keep paper + text, swap the faded crew behind."""
    o = img(k)
    Y = lum(o[..., :3])
    ui = Y > .42
    lab, n = nd.label(nd.binary_dilation(ui, iterations=2))
    keep = np.zeros_like(ui)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() > 30: keep |= comp
    keep = nd.binary_fill_holes(nd.binary_closing(keep, iterations=4))
    keep = nd.binary_dilation(keep, iterations=3)
    km = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.5)[..., None]
    bg = o.copy()
    bg[..., :3] = cv2.GaussianBlur(o[..., :3], (0, 0), 30)
    t = ambient_tint(o[..., :3], (0, 0, 1280, 720), 0)
    bg = layer(bg, 'bonnie_image4', at=(200, 50, 960), mean=.2, sat=.3, contrast=.7, tint=t, tint_s=1, seed=730, blur=3.5, opacity=.8)
    bg = layer(bg, 'chica_image3', at=(1080, 70, 900), ax=.55, mean=.22, sat=.3, contrast=.7, tint=t, tint_s=1, seed=731, blur=3.5, opacity=.8)
    bg = layer(bg, 'fred69', at=(640, 40, 1150), mean=.2, sat=.3, contrast=.7, tint=t, tint_s=1, seed=732, blur=3.5, opacity=.8)
    out = o.copy()
    out[..., :3] = bg[..., :3] * (1 - km) + o[..., :3] * km
    return out

def endings():
    return {k: ending(k) for k in ['210', '522', '523']}

def gameover():
    o = img('358')
    out = o.copy()
    # smother the stuffed suit into shadow, then stand Altman there
    yy, xx = np.mgrid[0:720, 0:1280]
    m = np.clip(1.5 - np.sqrt(((xx - 330) / 330) ** 2 + ((yy - 380) / 460) ** 2), 0, 1)
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 25)[..., None]
    dark = cv2.GaussianBlur(o[..., :3], (0, 0), 25) * .25
    out[..., :3] = o[..., :3] * (1 - m) + dark * m
    out = layer(out, 'fred1022', at=(300, 40, 1150), ax=.454, mean=.05, sat=.4, seed=740, blur=1.0)
    return {'358': out}

# ------------------------------------------------------------------ the CELEBRATE! poster on the office wall
PR = (522, 190, 790, 420)   # x0, y0, x1, y1 (office 1600x720 space)

def _poster_patch():
    o = img('126')
    x0, y0, x1, y1 = PR
    reg = o[y0:y1, x0:x1].copy()
    bg = reg.copy()
    bg[..., :3] = cv2.GaussianBlur(reg[..., :3], (0, 0), 40, borderType=cv2.BORDER_REFLECT) * .9
    bg[..., :3] += np.random.default_rng(5).normal(0, .012, bg.shape[:2])[..., None]
    t = ambient_tint(reg[..., :3], (0, 0, x1 - x0, y1 - y0), 0)
    bg = layer(bg, 'fred67', at=(138, 14, 300), mean=.2, sat=.9, tint=t, tint_s=.6, seed=750, blur=.8, noise=.01)
    bg = layer(bg, 'bonnie_image2', at=(60, 18, 200), ax=.52, mean=.2, sat=.9, tint=t, tint_s=.6, seed=751, blur=.8, noise=.01)
    bg = layer(bg, 'chica_image4', at=(222, 24, 215), ax=.55, mean=.22, sat=.9, tint=t, tint_s=.6, seed=752, blur=.8, noise=.01)
    H, W = y1 - y0, x1 - x0
    m = np.ones((H, W), np.float32)
    m = cv2.GaussianBlur(np.pad(m[6:-6, 6:-6], 6), (0, 0), 3)
    # keep the dark desk / monitor that sits in front of the poster's bottom edge
    front = np.zeros((H, W), np.float32)
    for fx0, fy0, fx1, fy1 in [(606, 345, 690, 430), (486, 386, 582, 430)]:
        front[max(0, fy0 - y0):fy1 - y0, max(0, fx0 - x0):fx1 - x0] = 1
    m = m * (1 - cv2.GaussianBlur(front, (0, 0), 1))
    return bg, m

_PP = None
def poster(arr, ref_k):
    """Swap the animatronics on the wall poster; relight to match image `ref_k`."""
    global _PP
    if _PP is None: _PP = _poster_patch()
    patch, m = _PP
    x0, y0, x1, y1 = PR
    a126 = img('126')[y0:y1, x0:x1, :3].reshape(-1, 3).mean(0)
    ak = img(ref_k)[y0:y1, x0:x1, :3].reshape(-1, 3).mean(0)
    ratio = ak / np.maximum(a126, 1e-4)
    out = arr.copy()
    reg = out[y0:y1, x0:x1, :3]
    out[y0:y1, x0:x1, :3] = reg * (1 - m[..., None]) + np.clip(patch[..., :3] * ratio, 0, 1) * m[..., None]
    return out
