"""Write the game's asset packs, swapping in every image from build/out/.

    python repack.py

Reads ../packs/ (images + audio), replaces any image that has a file in build/out/,
appends brand-new ids, and writes ../packs/ back (p0.wasm, p1.wasm, ... + manifest.json).
Packs are split at ~9 MB. They are plain byte blobs; the .wasm name is just a container.
"""
import json
from paths import GAME_PACKS, OUT

LIMIT = 9_000_000

def main(src=GAME_PACKS, dst=GAME_PACKS, reps_dir=OUT, prefix='p'):
    reps = {f.stem: f for f in reps_dir.glob('*.webp')}
    m = json.loads((src / 'manifest.json').read_text())
    packs = [(src / name).read_bytes() for name, _ in m['packs']]
    entries = [('img', k, v) for k, v in m['img'].items()] + [('aud', k, v) for k, v in m['aud'].items()]
    entries.sort(key=lambda e: (e[2][0], e[2][1]))                 # keep the original order
    out, cur, new = [], bytearray(), {'img': {}, 'aud': {}}

    def add(kind, k, data, mime):
        nonlocal cur
        if len(cur) + len(data) > LIMIT and cur:
            out.append(bytes(cur)); cur = bytearray()
        new[kind][k] = [len(out), len(cur), len(data), mime]; cur += data

    for kind, k, (p, o, l, mime) in entries:
        data = packs[p][o:o + l]
        if kind == 'img' and k in reps: data = reps[k].read_bytes()
        add(kind, k, data, mime)
    for k in sorted(set(reps) - set(m['img']), key=int):           # ids the original game never had
        add('img', k, reps[k].read_bytes(), 'image/webp')
    if cur: out.append(bytes(cur))

    for f in list(dst.glob('*.wasm')): f.unlink()
    names = []
    for i, b in enumerate(out):
        name = f'{prefix}{i}.wasm'; (dst / name).write_bytes(b); names.append([name, len(b)])
    (dst / 'manifest.json').write_text(json.dumps({'packs': names, 'img': new['img'], 'aud': new['aud']}, separators=(',', ':')))
    print(f'{sum(k in m["img"] for k in reps)} images replaced, {len(set(reps) - set(m["img"]))} added -> {names}')

if __name__ == '__main__':
    main()
