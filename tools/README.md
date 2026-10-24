# Asset tools

Python scripts that made every swapped image in the game: they relight each cut-out
photo to match the original frame (brightness, colour cast, light falloff, grain),
place it where the animatronic stood, and pack the results into `../packs/`.

You only need these to change the art. The game itself is just `../index.html` + `../packs/`.

## Setup

```bash
cd tools
pip install -r requirements.txt
python extract.py          # original images -> build/ex/  (run once)
```

## Rebuild

```bash
python build_all.py        # every swapped image -> build/out/   (about 2 minutes)
python repack.py           # build/out/ -> ../packs/
```

## Change one scene

1. Find the scene in `cams.py` (camera feeds and door views) or `seqs.py` (jumpscares,
   the hallway run, portraits, endings). Each entry names the photo and where it goes:
   `at=(x, y, height)`, plus brightness (`mean`), colour (`sat`, `tint`) and so on.
2. Preview it: `python preview.py 225` writes `build/preview/scenes.png`
   (original, new, and new at in-game brightness).
3. Run `build_all.py` and `repack.py`, then reload the game.

## Files

| File | What it does |
|---|---|
| `paths.py` | Every folder the tools use, relative to the repo |
| `extract.py` | Rebuilds the original image set from the game packs + `originals/` |
| `engine.py`, `layer.py` | Relighting and compositing a cut-out onto a frame |
| `cams.py` | Camera feeds and door views |
| `seqs.py` | Sequences, portraits, endings, game over, office wall poster |
| `posters.py` | Photos printed onto the CAM 2B wall poster in perspective |
| `title.py` | Title screen lineup, flickers and the credit line |
| `pixelfont.py`, `text_sprites.py` | New words in the game's pixel font |
| `newspaper.py` | The OpenAI "HELP WANTED" ad |
| `build_all.py`, `repack.py` | Build everything, then pack it into the game |
| `preview.py` | Before/after sheet for any camera or door scene |
| `photos/` | The cast cut-outs (see `photos/README.md`) |
| `originals/` | The 195 original frames that were replaced, used as references |
| `fonts/` | Fonts the text sprites need |

Images are referred to by their id in `../packs/manifest.json` (for example `225` is
the left door with The Zuck in it). `build/` is scratch space and is not committed.
