from layer import *

SPEC = {}
BASE_OVERRIDE = {}     # base id -> replacement image (e.g. CAM 2B with the new wall poster)

def S(tid, base, *layers, lightref=None, over=None, post=None, lsig=40):
    SPEC[tid] = dict(base=base, layers=list(layers), lightref=lightref, over=over, post=post, lsig=lsig)

# clip='mask' -> clip to dilated diff mask of (tid, base); clipfree=y -> everything above row y is free
# ---------------- CAM 1B dining area (empty 48)
S('215', '48', dict(name='chica_image2', at=(606, 22, 470), mean=.15, sat=.5, seed=1, clip='mask', clipfree=200))
S('90', '48', dict(name='bonnie_image6', at=(1088, 150, 330), mean=.14, sat=.5, seed=2, clip='mask', clipfree=300))
S('222', '48', dict(name='chica_image4', at=(600, 92, 760), mean=.004, sat=.1, contrast=.3, seed=3, noise=.004))
S('120', '48', dict(name='bonnie_image2', box=(0, 0, 1, 1), at=(880, 250, 600), mean=.004, sat=.1, contrast=.3, seed=4, noise=.004))
S('492', '48', dict(name='fred69', at=(772, 8, 175), mean=.055, sat=.4, seed=5, blur=1.0, fade=(0, .3)))
# ---------------- CAM 3 supply closet (empty 62)
S('190', '62', dict(name='bonnie_title', at=(560, 60, 540), rot=-18, mean=.25, sat=.6, seed=6, fade=(0, .25)),
  lightref=('190', '62'), over=((250, 300, 650, 560), .8))
# ---------------- CAM 4A east hall (empty 67)
S('221', '67', dict(name='chica29321', at=(712, 165, 545), ax=.4, mean=.3, sat=.35, contrast=.8, seed=7, opacity=.85))
S('226', '67', dict(name='chica_image4', at=(862, 40, 1000), mean=.25, sat=.6, seed=8), lightref=('226', '67'))
S('487', '67', dict(name='freddy_image2', at=(600, 172, 300), mean=.09, sat=.3, contrast=.8, seed=9, fade=(0, .15)))

def glow(points, r=4, halo=22, s=1.0, col=(1, 1, 1)):
    def f(base):
        H, W = base.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.zeros((H, W), np.float32)
        for (px, py) in points:
            d2 = (xx - px) ** 2 + (yy - py) ** 2
            g = np.maximum(g, np.clip(1.4 - np.sqrt(d2) / r, 0, 1) + .55 * np.exp(-d2 / (2 * halo ** 2)))
        g = np.clip(g * s, 0, 1)[..., None]
        out = base.copy()
        out[..., :3] = out[..., :3] * (1 - g) + np.array(col, np.float32) * g
        return out
    return f

# ---------------- CAM 1A show stage (empty 484): Zuck left, Chica-guy middle, Altman right
ZS = dict(name='bonnie_image3', at=(305, 28, 1560), ax=.5, sat=.6, tint_s=.5, seed=11)
CS = dict(name='chica_image4', at=(790, 40, 760), ax=.5, sat=.6, tint_s=.5, seed=12)
FS = dict(name='fred67', at=(1255, 30, 1100), sat=.6, contrast=1.2, tint_s=.5, seed=13)
S('2', '484', dict(FS, mean=.16), dict(CS, mean=.17), dict(ZS, mean=.16))
S('68', '484', dict(FS, mean=.1), dict(CS, mean=.11))
S('223', '484', dict(FS, mean=.09), dict(ZS, mean=.1))
S('224', '484', dict(FS, mean=.05))
S('355', '484', dict(name='fred69', at=(1220, 20, 980), mean=.035, sat=.3, seed=14, fade=(0, .2)))
# ---------------- CAM 1C pirate cove
S('211', '66', dict(name='foxy_image3', at=(942, 66, 690), mean=.09, sat=.5, seed=15, clip=(866, 0, 1024, 720)))
S('338', '240', dict(name='foxy_image5', at=(545, 270, 1350), ax=.45, mean=.04, sat=.45, seed=16))
# ---------------- CAM 2A west hall (lit empty 44)
S('206', '44', dict(name='bonnie_image6', at=(1040, 182, 245), mean=.02, sat=.2, contrast=.5, seed=17))
S('340', '44', dict(name='bonnie_image3', at=(1000, 162, 312), mean=.03, sat=.3, contrast=.6, seed=18))
# ---------------- CAM 2B west hall corner (empty 0)
B2 = dict(name='bonnie_image4', box=(0, 0, 1, .5), at=(590, 20, 1000), sat=.5, seed=19, mean=.09, light_s=.45)
S('188', '0', dict(B2), lightref=('188', '0'), lsig=90)
S('478', '0', dict(B2, rot=9, at=(605, 10, 1040)), lightref=('478', '0'), lsig=90)
S('479', '0', dict(B2, rot=-7, at=(575, 30, 1090), contrast=1.25), lightref=('479', '0'), lsig=90)
import posters
S('540', '0', post=lambda b: posters.make(b, 'jensen'))
S('571', '0', post=lambda b: posters.make(b, 'altman_rare'))
# ---------------- CAM 4B east hall corner (empty 49)
C4 = dict(name='chica_image3', at=(1090, 20, 1150), ax=.55, sat=.55, seed=23, mean=.13)
S('220', '49', dict(C4))
S('476', '49', dict(C4, rot=-8, at=(1110, 0, 1200)))
S('451', '49', dict(name='chica_flick', at=(1080, -40, 860), rot=7, sat=.45, contrast=1.2, mean=.12, seed=24))
S('486', '49', dict(name='freddy_title', at=(17 + 750, -132, 997), rot=-7, mean=.012, sat=.2, contrast=.6, seed=25),
  post=glow([(662, 267), (872, 240)], r=5, halo=14))
# ---------------- CAM 5 backstage (empty 83)
S('205', '83', dict(name='bonnie_image5', at=(1070, 90, 1100), mean=.02, sat=.3, contrast=.6, seed=26))
S('555', '83', dict(name='bonnie_title', at=(870, -20, 840), mean=.1, sat=.35, contrast=1.3, seed=27))
# ---------------- CAM 7 restrooms (empty 41)
S('217', '41', dict(name='chica29321', at=(1165, 63, 240), mean=.1, sat=.45, seed=28))
S('219', '41', dict(name='chica12041', at=(690, 60, 1080), mean=.1, sat=.5, seed=29))
S('494', '41', dict(name='fred1022', at=(360.5, 30, 476), ax=.454, mean=.022, sat=.3, seed=30, fade=(0, .45), clip=(302, 0, 640, 720)),
  post=glow([(337, 139), (384, 139)], r=2.5, halo=6, s=.8))
# ---------------- Office door lights / power out
S('225', '58', dict(name='bonnie_image5', at=(195, 175, 1150), mean=.11, sat=.55, seed=31, clip=(86, 0, 292, 720)), lightref=('225', '58'))
S('227', '127', dict(name='chica_image2', box=(0, 0, 1, .5), at=(1180, 190, 360), ax=.5, mean=.17, sat=.55, seed=32, clip='hull', dil=2))
S('305', '304', dict(name='freddy_title', box=(.2, 0, .8, .85), at=(188, 212, 150), mean=.13, sat=.6, seed=33, fade=(0, .3)),
  post=glow([(170, 280), (207, 280)], r=2.5, halo=5, s=.5))

def build(tid):
    sp = SPEC[tid]
    base = BASE_OVERRIDE[sp['base']].copy() if sp['base'] in BASE_OVERRIDE else img(sp['base'])
    orig = img(tid)
    L = None
    if sp['lightref']:
        m = diffmask(*sp['lightref'])
        L = lightmap(img(sp['lightref'][0])[..., :3], m, sp['lsig'])
    for kw in sp['layers']:
        kw = dict(kw)
        if L is not None and 'light' not in kw: kw['light'] = L
        if isinstance(kw.get('clip'), tuple):
            x0, y0, x1, y1 = kw['clip']; m = np.zeros(base.shape[:2], np.float32); m[y0:y1, x0:x1] = 1
            kw['clip'] = cv2.GaussianBlur(m, (0, 0), 2)
        if isinstance(kw.get('clip'), str) and kw['clip'] == 'hull':
            from skimage.morphology import convex_hull_image
            m = convex_hull_image(diffmask(tid, sp['base'], dil=kw.pop('dil', 2))).astype(np.float32)
            kw.pop('clipfree', None)
            kw['clip'] = cv2.GaussianBlur(m, (0, 0), 1.5)
        if isinstance(kw.get('clip'), str) and kw['clip'] == 'mask':
            m = nd.binary_fill_holes(diffmask(tid, sp['base'], dil=kw.pop('dil', 10))).astype(np.float32)
            fr = kw.pop('clipfree', None)
            if fr: m[:fr] = 1
            kw['clip'] = cv2.GaussianBlur(m, (0, 0), 2)
        else:
            kw.pop('clipfree', None); kw.pop('dil', None)
        base = layer(base, **kw)
    overs = sp['over'] or []
    if overs and not isinstance(overs, list): overs = [overs]
    for ov in overs:
        if len(ov) == 2: (x0, y0, x1, y1), th = ov; srcid = sp['base']
        else: srcid, (x0, y0, x1, y1), th = ov
        b = img(srcid)
        sel = np.zeros(base.shape[:2], bool); sel[y0:y1, x0:x1] = True
        Y = lum(b[..., :3])
        mm = (sel & (Y > th)).astype(np.float32)
        mm = cv2.GaussianBlur(nd.binary_dilation(mm > 0, iterations=3).astype(np.float32), (0, 0), 3)[..., None]
        base = base * (1 - mm) + b * mm
    if sp['post']: base = sp['post'](base)
    return base
