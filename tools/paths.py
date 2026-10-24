"""Every folder the asset tools read from or write to, relative to this repo."""
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
GAME_PACKS = ROOT / 'packs'          # the packs the game loads
PHOTOS = TOOLS / 'photos'            # cut-out photos of the cast (transparent PNGs)
ORIGINALS = TOOLS / 'originals'      # the original FNAF frames that were replaced (used as references)
FONTS = TOOLS / 'fonts'
BUILD = TOOLS / 'build'              # scratch, git-ignored
EX = BUILD / 'ex'                    # every original game image, rebuilt by extract.py
OUT = BUILD / 'out'                  # every rebuilt image, written by build_all.py
PREVIEW = BUILD / 'preview'
