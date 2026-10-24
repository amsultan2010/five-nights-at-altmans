"""Rebuild every swapped image into build/out/.

    python extract.py      # once: original images -> build/ex/
    python build_all.py    # all swapped images   -> build/out/   (a few minutes)
    python repack.py       # build/out/ -> ../packs/ (what the game loads)
"""
import json, time
import numpy as np
from PIL import Image
import engine
from engine import img, save, lum
from paths import OUT
import cams, seqs, posters, title, text_sprites, newspaper

OUT.mkdir(parents=True, exist_ok=True)
done = set()
t0 = time.time()

def put(k, arr, q=80):
    """Save a float RGB/RGBA image (same size as the original frame it replaces)."""
    k = str(k)
    if k in engine._cache or (engine.EX / f'{k}.webp').exists():
        assert arr.shape[:2] == img(k).shape[:2], (k, arr.shape, img(k).shape)
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones(arr.shape[:2] + (1,), np.float32)], 2)
    save(arr, k, OUT, q=q)
    done.add(k)

def put_lossless(k, rgba):
    """Save a uint8 RGBA sprite losslessly (pixel-font text)."""
    Image.fromarray(rgba, 'RGBA').save(OUT / f'{k}.webp', 'WEBP', lossless=True)
    done.add(k)

def step(name):
    print(f'{name:<28} {len(done):>4} images  {time.time() - t0:5.0f}s')

# 0) CAM 2B wall poster: Altman instead of the original Freddy (also the base for every 2B frame)
new0 = posters.make(img('0'), 'altman'); put('0', new0); cams.BASE_OVERRIDE['0'] = new0

# 1) camera feeds + office door views
for tid in cams.SPEC:
    put(tid, cams.build(tid))
step('cameras')

# 2) the CELEBRATE! poster on every office view
for k in ['225', '227', '305']:
    put(k, seqs.poster(cams.build(k), k))
for k in ['126', '39', '58', '127', '304', '519', '521', '485']:
    put(k, seqs.poster(img(k), k))
step('office poster')

# 3) sequences (jumpscares sit on the poster-swapped office)
engine._cache[('img', '126')] = (seqs.poster(img('126'), '126'), 'RGB')
for fn in ['run_frames', 'js_bonnie', 'js_chica', 'js_foxy', 'js_freddy', 'js_freddy_dark', 'title_faces',
           'golden_office', 'portraits', 'endings', 'gameover']:
    for k, v in getattr(seqs, fn)().items():
        put(k, v)
    step(fn)

# 4) title screen, text and the newspaper (these replace some step-3 frames)
for k, v in title.title_frames().items():
    put(k, v, q=82)
put_lossless('433', (title.copyright_sprite()['433'] * 255).astype(np.uint8))
for k in ['520', '545']:                         # rare creepy title faces, in black and white like the lineup
    a = np.asarray(Image.open(OUT / f'{k}.webp').convert('RGBA')).astype(np.float32) / 255
    a[..., :3] = np.repeat(lum(a[..., :3])[..., None], 3, 2)
    put(k, a, q=82)
for k, v in {**text_sprites.title_logo(), **text_sprites.name_labels()}.items():
    put_lossless(k, v)
res = newspaper.newspaper()['574']
Image.fromarray((res * 255 + .5).astype(np.uint8)).save(OUT / '574.webp', 'WEBP', quality=88, method=6); done.add('574')
step('title, text, newspaper')

(OUT / '_ids.json').write_text(json.dumps(sorted(done, key=int)))
print(f'done: {len(done)} images in {OUT}')
