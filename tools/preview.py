"""Before/after preview of camera and office scenes, for tweaking placements in cams.py.

    python preview.py 2 225 451        # writes build/preview/scenes.png

Each row shows the original frame (brightened), the new frame (brightened) and the
new frame at true in-game brightness.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw
import cams, posters
from engine import img
from paths import PREVIEW

def enh(a, g=1.8):
    return np.clip((np.clip(a[..., :3], 0, 1) ** (1 / g)) * 1.1, 0, 1)

def to_im(a, w):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return im.resize((w, int(w * im.height / im.width)))

def main(ids, w=480):
    if any(cams.SPEC[t]['base'] == '0' for t in ids):           # CAM 2B scenes sit on the new wall poster
        cams.BASE_OVERRIDE['0'] = posters.make(img('0'), 'altman')
    rows = []
    for t in ids:
        o, n = img(t), cams.build(t)
        tiles = [to_im(enh(o), w), to_im(enh(n), w), to_im(n[..., :3], w)]
        r = Image.new('RGB', (3 * w + 8, tiles[0].height + 16), '#222')
        for i, tile in enumerate(tiles): r.paste(tile, (i * (w + 4), 16))
        ImageDraw.Draw(r).text((4, 2), f'{t}   original | new | new (in-game brightness)', fill='#ff0')
        rows.append(r)
    sheet = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height
    PREVIEW.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW / 'scenes.png'); print('wrote', PREVIEW / 'scenes.png')

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1:])
