"""'Have you played your Gist Hunt today?' checklist posts. 1080x1350. python3 make.py"""
import json, math
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
GF = '/usr/share/fonts/truetype/google-fonts/'
PB = lambda s: ImageFont.truetype(GF + 'Poppins-Bold.ttf', s)
PM = lambda s: ImageFont.truetype(GF + 'Poppins-Medium.ttf', s)
INK = (24, 18, 36); CREAM = (255, 248, 238); GREEN = (40, 170, 110)
FIELDS = [(183, 155, 255), (255, 210, 31), (255, 111, 174), (61, 220, 151), (69, 193, 255), (255, 154, 46)]

MORNING = [  # (date, item1, item2)
    ("2026-11-16", "snoozed 3 times", "got up anyway"),
    ("2026-11-17", "coffee", "pretended to read the email"),
    ("2026-11-18", "Wordle", "Connections"),
    ("2026-11-19", "missed the bus", "caught the next one"),
    ("2026-11-20", "made the bed (kind of)", "found one sock"),
    ("2026-11-21", "slept in", "slept in more"),
    ("2026-11-22", "Sunday reset", "reset nothing"),
    ("2026-11-23", "replied “haha”", "did not haha"),
    ("2026-11-24", "texted “on my way”", "was not on my way"),
    ("2026-11-25", "bought the pie", "ate a slice of the pie"),
    ("2026-11-26", "“so… seeing anyone?”", "changed the subject"),
    ("2026-11-27", "added to cart", "removed from cart"),
    ("2026-11-28", "laundry in", "laundry still in"),
    ("2026-11-29", "walked the dog", "the dog walked me"),
]
EVENING = [
    ("2026-11-16", "dinner", "dishes (tomorrow)"),
    ("2026-11-17", "3 meetings", "1 of them needed"),
    ("2026-11-18", "opened the fridge", "closed the fridge"),
    ("2026-11-19", "said “you too” to the waiter", "replayed it 9 times"),
    ("2026-11-20", "answered the group chat", "muted the group chat"),
    ("2026-11-21", "made Saturday plans", "cancelled Saturday plans"),
    ("2026-11-22", "Sunday scaries", "ignored them"),
    ("2026-11-23", "accepted the terms", "did not read the terms"),
    ("2026-11-24", "phone at 3%", "found a charger"),
    ("2026-11-25", "packed for the trip", "packed again"),
    ("2026-11-26", "seconds", "thirds"),
    ("2026-11-27", "checked the deals", "bought socks"),
    ("2026-11-28", "leftovers", "leftovers again"),
    ("2026-11-29", "watered the plant", "apologised to the plant"),
]

def star(d, cx, cy, r, fill):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.32
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)

def centered(d, y, text, f, fill):
    d.text((W / 2, y), text, font=f, fill=fill, anchor='ma')

def checkbox(d, x, y, s, checked):
    d.rounded_rectangle([x, y, x + s, y + s], 12, outline=INK, width=7, fill=CREAM)
    if checked:
        d.line([(x + s * .22, y + s * .52), (x + s * .43, y + s * .74), (x + s * .80, y + s * .28)], fill=GREEN, width=12, joint='curve')

def fit(text, maxw, size):
    while PB(size).getlength(text) > maxw and size > 34: size -= 2
    return PB(size)

def render(i, slot, item1, item2, out):
    S = 2  # supersample
    im = Image.new('RGB', (W * S, H * S), FIELDS[i % len(FIELDS)])
    d = ImageDraw.Draw(im)
    sc = lambda v: int(v * S)
    if slot == 'am':
        lines = ["have you played", "your Gist Hunt today?"]
        foot = "3 questions · same puzzle for everyone"
    else:
        lines = ["did you do", "today's Gist yet?"]
        foot = "a new puzzle every day"
    f = PB(sc(78))
    y = sc(120)
    for ln in lines:
        d.text((W * S / 2, y), ln, font=f, fill=INK, anchor='ma'); y += sc(96)
    # card
    cx0, cy0, cx1, cy1 = sc(90), sc(400), sc(990), sc(1060)
    d.rounded_rectangle([cx0 + sc(14), cy0 + sc(16), cx1 + sc(14), cy1 + sc(16)], sc(40), fill=INK)
    d.rounded_rectangle([cx0, cy0, cx1, cy1], sc(40), fill=CREAM, outline=INK, width=sc(7))
    d.text((cx0 + sc(70), cy0 + sc(58)), "today:", font=PB(sc(46)), fill=(120, 100, 160))
    rows = [(item1, True), (item2, True), ("Gist Hunt", False)]
    ry = cy0 + sc(170)
    for k, (txt, ck) in enumerate(rows):
        bs = sc(84)
        checkbox(d, cx0 + sc(70), ry, bs, ck)
        maxw = cx1 - (cx0 + sc(190)) - sc(50)
        fnt = fit(txt, maxw, sc(60) if k < 2 else sc(70))
        col = (90, 80, 110) if ck else INK
        d.text((cx0 + sc(190), ry + bs / 2), txt, font=fnt, fill=col, anchor='lm')
        if ck:  # strike-through for done items
            tw = fnt.getlength(txt)
            d.line([(cx0 + sc(190), ry + bs / 2 + sc(4)), (cx0 + sc(190) + tw, ry + bs / 2 + sc(4))], fill=(90, 80, 110), width=sc(5))
        ry += sc(150)
    # footer
    d.text((W * S / 2, sc(1130)), foot, font=PM(sc(40)), fill=INK, anchor='ma')
    url = "playgisthunt.com"
    uf = PB(sc(48)); uw = uf.getlength(url)
    star(d, W * S / 2 - uw / 2 - sc(40), sc(1225), sc(22), INK)
    d.text((W * S / 2 + sc(10), sc(1196)), url, font=uf, fill=INK, anchor='ma')
    im.resize((W, H), Image.LANCZOS).save(out, quality=92)

if __name__ == '__main__':
    import os
    os.makedirs('out', exist_ok=True)
    meta = []
    for i, (dt, a, b) in enumerate(MORNING):
        fn = f"pt_{dt}_am.jpg"; render(i, 'am', a, b, 'out/' + fn); meta.append(dict(date=dt, slot='am', items=[a, b], file=fn))
    for i, (dt, a, b) in enumerate(EVENING):
        fn = f"pt_{dt}_pm2.jpg"; render(i + 3, 'pm', a, b, 'out/' + fn); meta.append(dict(date=dt, slot='pm', items=[a, b], file=fn))
    json.dump(meta, open('out/meta.json', 'w'), indent=1, ensure_ascii=False)
    print(len(meta))
