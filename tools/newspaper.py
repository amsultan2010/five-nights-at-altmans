"""The "HELP WANTED" newspaper ad (image 574): OpenAI logo in the photo box and new ad copy.

The page is tilted in perspective, so the ad is flattened first (rectify), edited flat, then
warped back (unrectify). The red marker circle is kept on top.

    python newspaper.py        # preview -> build/preview/newspaper.png
"""
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from paths import EX, PHOTOS, FONTS, PREVIEW

# ---- perspective of the ad on screen
PB = np.float32([[250, 282], [668, 227], [720, 612], [302, 667]])     # photo box corners on screen
S = 1.5                                                                # rectified pixels per plane unit
X0, Y0, X1, Y1 = -90, -230, 830, 560                                   # plane window (photo box = 0..420 x 0..400)
def H_plane_to_screen():
    src = np.float32([[0, 0], [420, 0], [420, 400], [0, 400]])
    return cv2.getPerspectiveTransform(src, PB)
def H_rect_to_screen():
    T = np.array([[1 / S, 0, X0], [0, 1 / S, Y0], [0, 0, 1]], np.float64)
    return H_plane_to_screen() @ T
RW, RH = int((X1 - X0) * S), int((Y1 - Y0) * S)
def rectify(img):
    Hr = H_rect_to_screen()
    return cv2.warpPerspective(img, np.linalg.inv(Hr), (RW, RH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def unrectify(rimg, size=(1280, 720)):
    return cv2.warpPerspective(rimg, H_rect_to_screen(), size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
def p2r(x, y):  # plane -> rectified px
    return (x - X0) * S, (y - Y0) * S

# ---- the ad

FONT = str(FONTS / 'FreeMonoBold.ttf')
LOGO = PHOTOS / 'openai_logo.png'
RIGHT = 1273                      # right edge of the text column (rectified px)
LINES = [                          # (baseline y, text)
    (365, "OpenAI is looking for"), (407.5, "a new MTS to work from"), (450, "6 a.m. to 7 p.m."),
    (535, "Vibecode B2B SaaS, larp"), (577.5, "being technical, drop"), (620, "usage resets."),
    (705, "Prerequisites: 10 years"), (747.5, "of Claude Code"), (790, "experience, YC-backed."),
    (875, "$67,000 a day."), (917.5, "To apply call:"), (960, "1-555-CHATGPT"),
]
TXT = (782, 328, 1292, 978)       # text column region to clean
BOX = (135, 345, 765, 945)        # photo box
HEAD = (196, 232, 1232, 312)      # heading line

def lum(a): return a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114

def build():
    o = np.asarray(Image.open(EX / '574.webp').convert('RGB')).astype(np.float32) / 255
    r = rectify(o)
    out = r.copy()
    x0, y0, x1, y1 = TXT
    reg = r[y0:y1, x0:x1]
    Y = lum(reg)
    bg = cv2.medianBlur((Y * 255).astype(np.uint8), 31).astype(np.float32) / 255
    rowsY = np.arange(y0, y1)[:, None]
    ink = (bg - Y) > np.where(rowsY > 840, .045, .12)      # bottom lines are blurrier / lower contrast
    ink = cv2.dilate(ink.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2)
    paper_ink_l = float(np.percentile(Y[ink > 0], 5))
    clean = cv2.inpaint((np.clip(reg, 0, 1) * 255).astype(np.uint8), ink, 9, cv2.INPAINT_TELEA).astype(np.float32) / 255
    clean = cv2.GaussianBlur(clean, (0, 0), 1.2) * .6 + clean * .4
    # ---- new text (rendered at 4x then downsampled for smooth edges)
    K = 4
    canvas = Image.new('L', ((x1 - x0) * K, (y1 - y0) * K), 0)
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT, int(34.3 * K))
    asc = f.getmetrics()[0]
    for base, t in LINES:
        w = d.textlength(t, font=f)
        d.text(((RIGHT - x0) * K - w, (base - y0) * K - asc), t, font=f, fill=255)
    a = np.asarray(canvas.resize((x1 - x0, y1 - y0), Image.LANCZOS)).astype(np.float32) / 255
    # depth-of-field: crisp in the middle, softer toward the bottom lines
    ys = np.arange(y0, y1)
    sig = np.clip(.7 + (ys - 800) / 160 * 1.9, .7, 2.6)
    blurred = np.zeros_like(a)
    for s in np.unique(np.round(sig, 1)):
        rows = np.where(np.round(sig, 1) == s)[0]
        b = cv2.GaussianBlur(a, (0, 0), float(s))
        blurred[rows] = b[rows]
    a = np.clip(blurred * 1.15, 0, 1)[..., None]
    inkc = np.array([paper_ink_l] * 3, np.float32) * np.array([1.0, 1.0, 1.02])
    clean = clean * (1 - a) + inkc * a
    out[y0:y1, x0:x1] = clean
    # ---- heading: "Technical Role at OpenAI" in place of the pizzeria name
    hx0, hy0, hx1, hy1 = HEAD
    hreg = r[hy0:hy1, hx0:hx1]
    hY = lum(hreg)
    hbg = cv2.medianBlur((hY * 255).astype(np.uint8), 41).astype(np.float32) / 255
    hink = cv2.dilate(((hbg - hY) > .08).astype(np.uint8), np.ones((5, 5), np.uint8), iterations=2)
    hclean = cv2.inpaint((np.clip(hreg, 0, 1) * 255).astype(np.uint8), hink, 11, cv2.INPAINT_TELEA).astype(np.float32) / 255
    hclean = cv2.GaussianBlur(hclean, (0, 0), 1.5) * .6 + hclean * .4
    K = 4
    hc = Image.new('L', ((hx1 - hx0) * K, (hy1 - hy0) * K), 0); hd = ImageDraw.Draw(hc)
    hf = ImageFont.truetype(FONT, int(68.3 * K)); hasc = hf.getmetrics()[0]
    ht = "Technical Role at OpenAI"; hw = hd.textlength(ht, font=hf)
    hd.text(((711.5 - hx0) * K - hw / 2, (287 - hy0) * K - hasc), ht, font=hf, fill=255)
    ha = np.asarray(hc.resize((hx1 - hx0, hy1 - hy0), Image.LANCZOS)).astype(np.float32) / 255
    ha = np.clip(cv2.GaussianBlur(ha, (0, 0), 1.4) * 1.15, 0, 1)[..., None]
    out[hy0:hy1, hx0:hx1] = hclean * (1 - ha) + inkc * ha
    # ---- photo box: OpenAI logo printed on paper
    bx0, by0, bx1, by1 = BOX
    paper = float(np.median(lum(r[by0 - 40:by0 - 10, bx0:bx1])))
    lg = Image.open(LOGO).convert('RGBA'); wb = Image.new('RGBA', lg.size, (255, 255, 255, 255)); wb.alpha_composite(lg)
    L = np.asarray(wb.convert('L')).astype(np.float32) / 255
    rows = np.where((L < .5).any(1))[0]; cols = np.where((L < .5).any(0))[0]
    L = L[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
    bw, bh = bx1 - bx0, by1 - by0
    tw = int(bw * .84); th = int(L.shape[0] * tw / L.shape[1])
    Ls = cv2.resize(L, (tw, th), interpolation=cv2.INTER_AREA)
    box = np.ones((bh, bw), np.float32)
    box[(bh - th) // 2:(bh - th) // 2 + th, (bw - tw) // 2:(bw - tw) // 2 + tw] = Ls
    box = cv2.GaussianBlur(box, (0, 0), .9)
    rng = np.random.default_rng(3)
    tone = paper * 1.04 * box + paper_ink_l * (1 - box)            # white -> paper, black -> ink
    tone += rng.normal(0, .012, tone.shape).astype(np.float32)
    frame = np.zeros((bh, bw), np.float32); frame[:5] = frame[-5:] = 1; frame[:, :5] = frame[:, -5:] = 1
    tone = tone * (1 - frame) + paper_ink_l * frame
    out[by0:by1, bx0:bx1] = np.repeat(np.clip(tone, 0, 1)[..., None], 3, 2)
    # ---- warp back and composite (red marker circle stays on top)
    m = np.zeros(r.shape[:2], np.float32)
    m[y0:y1, x0:x1] = 1; m[by0 - 2:by1 + 2, bx0 - 2:bx1 + 2] = 1; m[HEAD[1]:HEAD[3], HEAD[0]:HEAD[2]] = 1
    m = cv2.GaussianBlur(m, (0, 0), 2)
    W = unrectify(out); M = unrectify(m)[..., None]
    res = o * (1 - M) + W * M
    red = (o[..., 0] - np.maximum(o[..., 1], o[..., 2])) > .18
    red = cv2.GaussianBlur(cv2.dilate(red.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), .8)[..., None]
    res = res * (1 - red) + o * red
    return np.clip(res, 0, 1), out

def newspaper():
    """574: the job ad shown before night 1."""
    res, _ = build()
    return {'574': res}

if __name__ == '__main__':
    PREVIEW.mkdir(parents=True, exist_ok=True)
    res, rect = build()
    Image.fromarray((res * 255 + .5).astype(np.uint8)).save(PREVIEW / 'newspaper.png')
    Image.fromarray((np.clip(rect, 0, 1) * 255).astype(np.uint8)).save(PREVIEW / 'newspaper_flat.png')
    print('wrote', PREVIEW / 'newspaper.png')
