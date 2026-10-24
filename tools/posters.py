import numpy as np, cv2, zlib
from engine import img, lum
Q = np.float32([[485, 78], [724, 20], [765, 288], [580, 385]])   # poster corners on CAM 2B (TL, TR, BR, BL)
PW, PH = 492, 642                                                # flat poster, 2x
def Hm():
    return cv2.getPerspectiveTransform(np.float32([[0, 0], [PW, 0], [PW, PH], [0, PH]]), Q)
def flat(arr):
    return cv2.warpPerspective(arr, np.linalg.inv(Hm()), (PW, PH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def unflat(f, size=(1600, 720)):
    return cv2.warpPerspective(f, Hm(), size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)

from layer import layer
PIC = (8, 106, 440, 634)      # picture area inside the flat poster (header "LET'S PARTY!" stays)

PHOTOS = {
    'altman': dict(name='freddy_image2', box=(0, 0, 1, .4), at=(226, 116, 540), mean=.2, sat=.45, contrast=1.1),
    'jensen': dict(name='goldenfred', box=(.05, 0, .8, .5), at=(222, 112, 560), mean=.2, sat=.85, contrast=1.1,
                   tint=(1.4, 1.12, .42), tint_s=1),
    'altman_rare': dict(name='freddy_title', box=(.12, 0, .88, .95), at=(222, 96, 600), mean=.16, sat=.7, contrast=1.45,
                        tint=(1.25, .9, .8), tint_s=1),
}

def make(base, who):
    """Print `who` onto the CAM 2B wall poster, in the poster's own perspective and lighting."""
    o = img('0')[..., :3]
    f0 = flat(o)                                        # original poster, flattened (for lighting reference)
    x0, y0, x1, y1 = PIC
    Y = lum(f0)
    pic = np.zeros((PH, PW), bool); pic[y0:y1, x0:x1] = True
    L = cv2.GaussianBlur(Y, (0, 0), 45); L = L / max(1e-4, L[pic].mean())
    canvas = np.zeros((PH, PW, 4), np.float32); canvas[..., 3] = 1
    canvas[..., :3] = (cv2.GaussianBlur(f0, (0, 0), 25) * .3)          # dark poster backdrop
    kw = dict(PHOTOS[who]); kw.setdefault('tint', (1, 1, 1)); kw.setdefault('tint_s', 0)
    canvas = layer(canvas, **kw, blur=.8, noise=.012, seed=zlib.crc32(who.encode()) % 997, clip=pic.astype(np.float32))
    canvas[..., :3] *= np.clip(1 + (L[..., None] - 1) * .7, .3, 1.8)      # same flashlight falloff as the wall
    m = np.zeros((PH, PW), np.float32); m[y0:y1, x0:x1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 2)
    W = unflat(canvas[..., :3]); M = unflat(m)[..., None]
    out = base.copy()
    out[..., :3] = base[..., :3] * (1 - M) + W * M
    return out
