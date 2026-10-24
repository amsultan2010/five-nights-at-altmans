"""Headless browser smoke test: loads the game and walks through the main screens.

    pip install playwright && playwright install chromium
    python tests/smoke_test.py            # from tools/

Fails (exit 1) on any page error or a screen that doesn't show up.
"""
import asyncio, functools, http.server, socketserver, sys, threading
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/'

async def desktop(browser, url, check):
    pg = await browser.new_page(viewport={'width': 1280, 'height': 720})
    errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    await pg.goto(url); await pg.wait_for_function('loaded === true', timeout=60000)
    await pg.wait_for_timeout(300)
    check('opens straight on the title screen', await pg.evaluate('scene === S_TITLE'))
    check('page title', await pg.title() == "Five Nights at Altman's")
    await pg.mouse.click(260, 421); await pg.wait_for_timeout(1200)           # New Game
    check('New Game shows the newspaper ad', await pg.evaluate('scene === S_AD'))
    await pg.evaluate('go(S_NIGHT, 1)'); await pg.wait_for_timeout(300)
    await pg.mouse.move(600, 700); await pg.wait_for_timeout(900)            # hover the bar: cameras up
    check('camera monitor opens', await pg.evaluate('N.mon === 2'))
    await pg.mouse.click(983 + 30, 643 + 20); await pg.wait_for_timeout(200)  # CAM 2B button
    check('camera switching', await pg.evaluate("N.cam === '2B'"))
    await pg.evaluate("SAVE.beat6 = 1; go(S_CUSTOM)"); await pg.wait_for_timeout(200)
    check('Custom Night screen', await pg.evaluate('scene === S_CUSTOM'))
    check('no page errors (desktop)', not errors)
    if errors: print('   ', errors[:3])

async def phone(browser, url, check):
    ctx = await browser.new_context(viewport={'width': 390, 'height': 844}, has_touch=True, is_mobile=True)
    pg = await ctx.new_page()
    errors = []; pg.on('pageerror', lambda e: errors.append(str(e)))
    await pg.goto(url); await pg.wait_for_function('loaded === true', timeout=60000)
    check('phone held upright: game turns sideways', await pg.evaluate('rotated === true'))
    s = min(844 / 1280, 390 / 720)                                          # game point -> screen point when rotated
    await pg.touchscreen.tap(195 - (421 - 360) * s, 422 + (260 - 640) * s); await pg.wait_for_timeout(800)
    check('tap New Game on a phone', await pg.evaluate('scene === S_AD'))
    check('no page errors (phone)', not errors)
    await ctx.close()

async def main():
    srv, url = serve()
    failed = []
    def check(name, ok):
        print(('PASS ' if ok else 'FAIL ') + name)
        if not ok: failed.append(name)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        await desktop(browser, url, check)
        await phone(browser, url, check)
        await browser.close()
    srv.shutdown()
    print(f'\n{len(failed)} failed' if failed else '\nall checks passed')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    asyncio.run(main())
