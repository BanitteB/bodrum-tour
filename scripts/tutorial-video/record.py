"""Records a fictional demo playthrough of the Bodrum Tour app as a tutorial video.

Everything shown is made up: a demo tour served via intercepted Supabase
requests, a procedurally drawn fictional town map, and simulated GPS walking.
Usage: python3 record.py <lang> <outdir>
"""
import asyncio, io, json, math, os, sys, time, random
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

from texts import TEXTS

LANG = sys.argv[1] if len(sys.argv) > 1 else 'de'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'out'
TX = TEXTS[LANG]
BASE = 'http://localhost:4173/bodrum-tour/'
TOUR_ID = '00000000-demo-0000-0000-000000000001'

# ── Fictional geography ──────────────────────────────────────────────
START = (37.03420, 27.42780)
STOPS = [
    (37.03395, 27.42930),
    (37.03300, 27.43040),
    (37.03210, 27.42930),
    (37.03250, 27.42760),
]

def tour_rows():
    s = TX['stops']
    stops = []
    for i, (lat, lng) in enumerate(STOPS):
        st = s[i]
        stops.append({
            'id': f'stop-{i+1}', 'tour_id': TOUR_ID, 'order_index': i + 1,
            'name': st['name'], 'location_name': st['place'], 'story': st['story'],
            'challenge_type': st['type'], 'challenge_prompt': st['prompt'],
            'challenge_answer': st.get('answer', ''), 'challenge_hint': st['hint'],
            'challenge_options': st.get('options', ''), 'lat': lat, 'lng': lng,
            'points': 100, 'translations': {}, 'show_photo': False,
            'photo_url': None, 'audio_url': None,
        })
    return [{
        'id': TOUR_ID, 'name': TX['tour_name'], 'subtitle': TX['tour_sub'],
        'description': TX['tour_sub'], 'tags': ['history', 'culture'],
        'gradient_from': '#1e3a8a', 'gradient_to': '#0e7490', 'accent_color': '#38bdf8',
        'duration_min': 1, 'duration_max': 1.5, 'difficulty': 'easy',
        'tour_type': 'sequential', 'price': 0, 'kid_friendly': True,
        'bypass_gps': False, 'published': True, 'sort_order': 0,
        'translations': {}, 'tour_stops': stops,
    }]

# ── Fictional map tiles ──────────────────────────────────────────────
def lat2py(lat, z):
    r = math.radians(lat)
    return (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 256 * 2 ** z

SEA_LAT = 37.0317
tile_cache = {}

def make_tile(z, x, y):
    key = (z, x, y)
    if key in tile_cache:
        return tile_cache[key]
    S = 256
    img = Image.new('RGB', (S, S), (242, 239, 233))
    d = ImageDraw.Draw(img)
    ox, oy = x * S, y * S
    sea_y = lat2py(SEA_LAT, z) - oy
    step = max(24, int(70 * 2 ** (z - 17)))
    # blocks: random parks / buildings
    for bx in range((ox // step) * step, ox + S + step, step):
        for by in range((oy // step) * step, oy + S + step, step):
            rnd = random.Random(bx * 7919 + by * 104729 + z)
            col = (205, 235, 190) if rnd.random() < 0.15 else (222, 214, 205)
            pad = step * 0.18
            d.rounded_rectangle([bx - ox + pad, by - oy + pad, bx - ox + step - pad, by - oy + step - pad],
                                radius=step * 0.08, fill=col)
    # streets
    w = max(3, step // 9)
    for sx in range((ox // step) * step, ox + S + step, step):
        d.line([(sx - ox, 0), (sx - ox, S)], fill=(255, 255, 255), width=w)
    for sy in range((oy // step) * step, oy + S + step, step):
        d.line([(0, sy - oy), (S, sy - oy)], fill=(255, 255, 255), width=w)
    # sea + beach
    if sea_y < S:
        top = max(0, sea_y)
        d.rectangle([0, top, S, S], fill=(170, 211, 223))
        if sea_y >= -8:
            d.rectangle([0, max(0, sea_y - 6), S, max(0, sea_y)], fill=(245, 228, 180))
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    tile_cache[key] = buf.getvalue()
    return tile_cache[key]

def demo_photo():
    W, H = 900, 680
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    for yy in range(H // 2):
        t = yy / (H / 2)
        d.line([(0, yy), (W, yy)], fill=(int(255 - 60 * t), int(190 + 20 * t), int(120 + 110 * t)))
    d.ellipse([620, 90, 740, 210], fill=(255, 236, 160))
    d.rectangle([0, H // 2, W, H], fill=(40, 120, 170))
    for i in range(8):
        d.line([(0, H // 2 + 20 + i * 38), (W, H // 2 + 14 + i * 38)], fill=(80, 160, 205), width=3)
    for bx, s in [(160, 1.0), (470, 0.75)]:
        d.polygon([(bx, 400), (bx + 230 * s, 400), (bx + 190 * s, 440), (bx + 30 * s, 440)], fill=(250, 250, 250))
        d.line([(bx + 110 * s, 400), (bx + 110 * s, 400 - 170 * s)], fill=(90, 60, 40), width=5)
        d.polygon([(bx + 115 * s, 240 * (2 - s) / 1 if s < 1 else 235), (bx + 115 * s, 390), (bx + 200 * s, 390)], fill=(255, 255, 255))
    d.rectangle([0, H - 90, W, H], fill=(233, 214, 170))
    buf = io.BytesIO(); img.save(buf, 'JPEG', quality=88)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'demo_photo.jpg')
    open(path, 'wb').write(buf.getvalue())
    return path

# ── Overlay helpers (captions + tap indicator) ───────────────────────
OVERLAY_JS = r"""
(() => {
  if (window.__ov) return;
  const st = document.createElement('style');
  st.textContent = `
  #__cap{position:fixed;left:12px;right:12px;bottom:max(18px, env(safe-area-inset-bottom));z-index:2147483647;
    background:rgba(5,12,28,.88);color:#fff;border:1px solid rgba(255,255,255,.18);border-radius:18px;
    padding:14px 16px;font:600 17px/1.35 system-ui,-apple-system,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.45);
    transition:opacity .35s, transform .35s;opacity:0;transform:translateY(10px);pointer-events:none}
  #__cap.top{bottom:auto;top:max(14px, env(safe-area-inset-top))}
  #__cap.on{opacity:1;transform:none}
  #__cap small{display:block;font-weight:500;font-size:13.5px;color:rgba(255,255,255,.72);margin-top:4px}
  .__tap{position:fixed;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;z-index:2147483647;
    background:rgba(255,255,255,.35);border:3px solid #fff;pointer-events:none;animation:__tap .7s ease-out forwards}
  @keyframes __tap{0%{transform:scale(.4);opacity:1}100%{transform:scale(1.6);opacity:0}}
  #__card{position:fixed;inset:0;z-index:2147483647;display:flex;flex-direction:column;align-items:center;justify-content:center;
    text-align:center;padding:30px;color:#fff;background:linear-gradient(160deg,#041a3d,#072b5c 55%,#0e7490);
    font-family:system-ui,-apple-system,sans-serif;transition:opacity .5s;opacity:0;pointer-events:none}
  #__card.on{opacity:1}
  #__card .e{font-size:64px;margin-bottom:16px}
  #__card h1{font-size:30px;font-weight:800;margin:0 0 10px;line-height:1.15}
  #__card p{font-size:17px;color:rgba(255,255,255,.75);margin:0;line-height:1.45}
  #__card .tag{margin-top:22px;font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#67e8f9}
  `;
  document.documentElement.appendChild(st);
  const cap = document.createElement('div'); cap.id='__cap'; document.documentElement.appendChild(cap);
  const card = document.createElement('div'); card.id='__card'; document.documentElement.appendChild(card);
  window.__ov = {
    cap(html, top){ cap.innerHTML = html; cap.classList.toggle('top', !!top); cap.classList.add('on'); },
    hide(){ cap.classList.remove('on'); },
    tap(x,y){ const t=document.createElement('div'); t.className='__tap'; t.style.left=x+'px'; t.style.top=y+'px';
      document.documentElement.appendChild(t); setTimeout(()=>t.remove(),800); },
    card(html){ card.innerHTML = html; card.classList.add('on'); },
    uncard(){ card.classList.remove('on'); },
  };
})();
"""

class Director:
    def __init__(self, page, ctx):
        self.page, self.ctx = page, ctx
        self.t0 = time.time()
        self.chimes = []
        self.taps = []

    async def ensure(self):
        await self.page.evaluate(OVERLAY_JS)

    async def cap(self, title, sub=None, top=False, wait=0):
        await self.ensure()
        html = title + (f'<small>{sub}</small>' if sub else '')
        await self.page.evaluate('([h,t]) => window.__ov.cap(h,t)', [html, top])
        if wait: await self.page.wait_for_timeout(wait)

    async def hide(self):
        await self.ensure(); await self.page.evaluate('window.__ov.hide()')

    async def card(self, emoji, title, text, tag='', wait=3500):
        await self.ensure()
        html = f'<div class="e">{emoji}</div><h1>{title}</h1><p>{text}</p>' + (f'<div class="tag">{tag}</div>' if tag else '')
        await self.page.evaluate('h => window.__ov.card(h)', html)
        await self.page.wait_for_timeout(wait)

    async def uncard(self):
        await self.page.evaluate('window.__ov.uncard()'); await self.page.wait_for_timeout(600)

    async def tap(self, loc, pause=700):
        await loc.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(250)
        box = await loc.bounding_box()
        await self.ensure()
        x, y = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
        await self.page.evaluate('([x,y]) => window.__ov.tap(x,y)', [x, y])
        self.taps.append(time.time() - self.t0)
        await self.page.wait_for_timeout(250)
        await loc.click()
        await self.page.wait_for_timeout(pause)

    async def type(self, loc, text):
        await self.tap(loc, pause=200)
        await loc.press_sequentially(text, delay=140)
        await self.page.wait_for_timeout(500)

    async def walk(self, a, b, seconds=7.0):
        steps = int(seconds / 0.25)
        chimed = False
        for i in range(steps + 1):
            t = i / steps
            lat = a[0] + (b[0] - a[0]) * t
            lng = a[1] + (b[1] - a[1]) * t
            await self.ctx.set_geolocation({'latitude': lat, 'longitude': lng, 'accuracy': 5})
            dy = (b[0] - lat) * 111320
            dx = (b[1] - lng) * 111320 * math.cos(math.radians(lat))
            if not chimed and math.hypot(dx, dy) <= 9:
                chimed = True
                self.chimes.append(time.time() - self.t0 + 0.4)  # arrival → chime in the soundtrack
            await self.page.wait_for_timeout(250)

    async def scroll_to(self, loc):
        await loc.evaluate("el => el.scrollIntoView({behavior:'smooth', block:'center'})")
        await self.page.wait_for_timeout(1100)


async def main():
    photo = demo_photo()
    rows = tour_rows()
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--no-sandbox', '--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(
            viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=False,
            locale={'de': 'de-DE', 'en': 'en-US', 'tr': 'tr-TR', 'fr': 'fr-FR'}[LANG],
            geolocation={'latitude': START[0], 'longitude': START[1], 'accuracy': 5},
            permissions=['geolocation'],
            record_video_dir=OUT, record_video_size={'width': 780, 'height': 1688},
        )
        await ctx.add_init_script(f"""
          try {{
            if (!sessionStorage.getItem('__init')) {{
              localStorage.clear();
              localStorage.setItem('bodrum-lang', '{LANG}');
              localStorage.setItem('bodrum-purchases-v2', JSON.stringify({{'{TOUR_ID}': true}}));
              sessionStorage.setItem('__init', '1');
            }}
          }} catch (e) {{}}
          // No service worker in the recording (keeps requests interceptable)
          try {{ Object.defineProperty(navigator, 'serviceWorker', {{ get: () => undefined }}) }} catch (e) {{}}
        """)

        async def supa(route):
            req = route.request
            url = req.url
            if '/rest/v1/tours' in url and req.method == 'GET':
                return await route.fulfill(status=200, content_type='application/json', body=json.dumps(rows))
            accept = req.headers.get('accept', '')
            if req.method == 'GET':
                body = 'null' if 'vnd.pgrst.object' in accept else '[]'
                return await route.fulfill(status=200, content_type='application/json', body=body)
            body = '{}' if 'vnd.pgrst.object' in accept else '[]'
            return await route.fulfill(status=201, content_type='application/json', body=body)

        async def tiles(route):
            parts = route.request.url.rstrip('.png').split('/')
            z, x, y = int(parts[-3]), int(parts[-2]), int(parts[-1])
            await route.fulfill(status=200, content_type='image/png', body=make_tile(z, x, y))

        await ctx.route('https://dummy.supabase.co/**', supa)
        await ctx.route('https://tile.openstreetmap.org/**', tiles)
        await ctx.route(lambda u: not (u.startswith('http://localhost') or 'dummy.supabase' in u or 'tile.openstreetmap' in u or u.startswith('data:') or u.startswith('blob:')),
                        lambda r: r.abort())

        page = await ctx.new_page()
        D = Director(page, ctx)
        await page.goto(BASE)
        await page.wait_for_timeout(1200)

        # ── Intro ───────────────────────────────────────────────
        await D.card('🧭', TX['intro_title'], TX['intro_text'], TX['intro_tag'], wait=4500)
        await D.uncard()

        # ── Welcome ─────────────────────────────────────────────
        await D.cap(*TX['c_welcome'], wait=2600)
        await D.type(page.locator('input[type=text]').first, TX['team'])
        await D.cap(*TX['c_begin'], wait=1500)
        await D.tap(page.locator('form button[type=submit]'), pause=1500)

        # ── Tour select ─────────────────────────────────────────
        await D.cap(*TX['c_pick'], wait=2600)
        await D.tap(page.get_by_text(TX['tour_name']).first, pause=1800)

        # ── Rules ───────────────────────────────────────────────
        await D.cap(*TX['c_rules'], top=True, wait=4200)
        await D.hide()
        rules_btn = page.locator('div.fixed button').last
        await D.tap(rules_btn, pause=1500)

        # ── Hub tour ────────────────────────────────────────────
        await D.cap(*TX['c_hub_steps'], wait=4200)
        await D.cap(*TX['c_hub_map'], wait=4200)

        challenge = page.locator('main, body')
        prev = START
        for i, st in enumerate(TX['stops']):
            # Walk to the stop
            await D.cap(*(TX['c_walk'] if i == 0 else TX['c_walk_next']), wait=600)
            await D.walk(prev, STOPS[i], seconds=7.0 if i == 0 else 5.0)
            prev = STOPS[i]
            await page.wait_for_timeout(500)
            await D.cap(*TX['c_arrived'], wait=3000)
            start_btn = page.locator('button.cta-pulse').filter(has_text=TX['ui_arrived']).first
            await D.hide()
            await D.tap(start_btn, pause=1500)

            # Mission screen
            if i == 0:
                await D.cap(*TX['c_story'], top=True, wait=4000)
            ctype = st['type']
            if ctype == 'riddle':
                inp = page.locator('input[type=text]').first
                await D.scroll_to(inp)
                await D.cap(*TX['c_riddle'], top=True, wait=4200)
                await D.type(inp, st['wrong'])
                await D.tap(page.locator('form button[type=submit]').first, pause=900)
                await D.cap(*TX['c_wrong'], top=True, wait=2600)
                await inp.fill('')
                await D.type(inp, st['answer_typed'])
                await D.tap(page.locator('form button[type=submit]').first, pause=2200)
            elif ctype == 'multiple_choice':
                opt = page.get_by_role('button', name=st['answer'], exact=True).first
                await D.scroll_to(opt)
                await D.cap(*TX['c_mc'], top=True, wait=3800)
                hint = page.get_by_text(TX['ui_hint_q']).first
                await D.tap(hint, pause=900)
                await D.cap(*TX['c_hint'], top=True, wait=3000)
                confirm = page.locator('div.fixed button').last
                await D.tap(confirm, pause=1600)
                await D.tap(opt, pause=700)
                submit = page.get_by_role('button', name=TX['ui_mc_submit']).first
                await D.tap(submit, pause=2200)
            elif ctype == 'code':
                inp = page.locator('input[type=text]').first
                await D.scroll_to(inp)
                await D.cap(*TX['c_code'], top=True, wait=4000)
                await D.type(inp, st['answer'])
                await D.tap(page.get_by_role('button', name=TX['ui_code_submit']).first, pause=2200)
            elif ctype == 'photo':
                btn = page.get_by_text(TX['ui_take_photo']).first
                await D.scroll_to(btn)
                await D.cap(*TX['c_photo'], top=True, wait=4000)
                await btn.scroll_into_view_if_needed()
                box = await btn.bounding_box()
                await D.ensure()
                await page.evaluate('([x,y]) => window.__ov.tap(x,y)', [box['x'] + box['width'] / 2, box['y'] + box['height'] / 2])
                await page.wait_for_timeout(500)
                await page.locator('input[type=file]').first.set_input_files(photo)
                await page.wait_for_timeout(1800)
                await D.tap(page.get_by_role('button', name=TX['ui_photo_submit']).first, pause=2200)

            # Success overlay
            await D.cap(*(TX['c_success'] if i < len(STOPS) - 1 else TX['c_final']), top=True, wait=3800)
            await D.hide()
            cont = page.locator('button.cta-pulse').last
            await D.tap(cont, pause=1800)
            if i == 0:
                await D.cap(*TX['c_back'], wait=4200)

        # ── Completion ──────────────────────────────────────────
        await D.cap(*TX['c_done'], wait=4500)
        await page.mouse.wheel(0, 500)
        await page.wait_for_timeout(2500)
        await D.hide()
        await D.card('🎉', TX['outro_title'], TX['outro_text'], '', wait=4500)

        dur = time.time() - D.t0
        await ctx.close()
        await b.close()
        json.dump({'chimes': D.chimes, 'taps': D.taps, 'dur': dur}, open(f'{OUT}/meta.json', 'w'))
        print('done', dur, D.chimes)

asyncio.run(main())
