"""Rebuild every original game image into build/ex/ (the tools composite on top of these).

Untouched images come straight out of the game packs. The frames that were replaced by
photos are restored from originals/, so the result is the full, original image set.

    python extract.py
"""
import json
from paths import GAME_PACKS, ORIGINALS, EX

def main():
    EX.mkdir(parents=True, exist_ok=True)
    m = json.loads((GAME_PACKS / 'manifest.json').read_text())
    packs = [(GAME_PACKS / name).read_bytes() for name, _ in m['packs']]
    for k, (p, off, length, _mime) in m['img'].items():
        (EX / f'{k}.webp').write_bytes(packs[p][off:off + length])
    restored = 0
    for f in ORIGINALS.glob('*.webp'):
        (EX / f.name).write_bytes(f.read_bytes()); restored += 1
    print(f'{len(m["img"])} images extracted, {restored} originals restored -> {EX}')

if __name__ == '__main__':
    main()
