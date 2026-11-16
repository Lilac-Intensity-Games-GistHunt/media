"""Table-flip memes. python3 flip.py"""
import os, math
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 1350, 2
CJK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
GF = '/usr/share/fonts/truetype/google-fonts/'
K = lambda z: ImageFont.truetype(CJK, int(z * S), index=0)
PB = lambda z: ImageFont.truetype(GF + 'Poppins-Bold.ttf', int(z * S))
PM = lambda z: ImageFont.truetype(GF + 'Poppins-Medium.ttf', int(z * S))
INK = (24, 18, 36); CREAM = (255, 248, 238)
FLIP = '(╯°□°)╯︵ ┻━┻'
TABLE = '┬─┬'
PUTBACK = '┬─┬ノ( º _ ºノ)'
ICON = Image.open('../left_on_read/icon512.png').convert('RGB')

def s(v): return int(round(v * S))

DJ = lambda z: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(z * S))
CJK_CH = set('\u30ce\ufe35')
WOOD = (196, 140, 96); WOOD_L = (222, 172, 126)

def mixed(d, cx, y, text, size, fill=INK):
    parts = [(ch, K(size) if ch in CJK_CH else DJ(size)) for ch in text]
    total = sum(f.getlength(ch) for ch, f in parts)
    x = s(cx) - total / 2
    for ch, f in parts:
        d.text((x, s(y)), ch, font=f, fill=fill, anchor='ls'); x += f.getlength(ch)
    return total / S

def table(w, h, with_icon=False):
    """Upright wooden table sprite (RGBA, supersampled)."""
    pad = 20
    im = Image.new('RGBA', (s(w + 2 * pad), s(h + 2 * pad + (w * 0.3 if with_icon else 0))), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    top = pad + (w * 0.3 if with_icon else 0)
    lw = w * 0.07
    for lx in (pad + w * 0.12, pad + w * 0.88 - lw):
        d.rectangle([s(lx), s(top + 30), s(lx + lw), s(top + h)], fill=WOOD, outline=INK, width=s(6))
    d.rounded_rectangle([s(pad), s(top), s(pad + w), s(top + 40)], s(10), fill=WOOD_L, outline=INK, width=s(7))
    if with_icon:
        ic = icon(w * 0.26)
        im.alpha_composite(ic, (int(s(pad + w / 2) - ic.width / 2), int(s(top) - ic.height + s(4))))
    return im

def flipped_table(w, h, rot=160):
    return table(w, h).rotate(rot, resample=Image.BICUBIC, expand=True)

def motion(d, x, y, n=3, ln=60):
    for j in range(n):
        d.arc([s(x - ln - j * 22), s(y - ln - j * 22), s(x + ln + j * 22), s(y + ln + j * 22)], 200, 250, fill=INK, width=s(5))


def icon(size, rot=0):
    a = ICON.resize((s(size), s(size)), Image.LANCZOS).convert('RGBA')
    m = Image.new('L', a.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, a.size[0] - 1, a.size[1] - 1], s(size * 0.22), fill=255)
    a.putalpha(m)
    return a.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else a

def fit(text, maxw, size, fnt=K):
    while fnt(size).getlength(text) / S > maxw and size > 20: size -= 2
    return fnt(size)

def ctext(d, y, text, f, fill=INK):
    d.text((s(W / 2), s(y)), text, font=f, fill=fill, anchor='ma')

def paste(im, spr, cx, cy):
    im.alpha_composite(spr, (int(s(cx) - spr.width / 2), int(s(cy) - spr.height / 2)))

def footer(d, y=1262, fill=INK):
    url = 'playgisthunt.com'; uf = PB(46); uw = uf.getlength(url) / S
    cx, cy, r = W / 2 - uw / 2 - 34, y + 2, 19
    pts = [(s(cx + (r if i % 2 == 0 else r * .32) * math.cos(math.pi / 4 * i - math.pi / 2)),
            s(cy + (r if i % 2 == 0 else r * .32) * math.sin(math.pi / 4 * i - math.pi / 2))) for i in range(8)]
    d.polygon(pts, fill=fill)
    d.text((s(W / 2 + 10), s(y)), url, font=uf, fill=fill, anchor='mm')

def save(im, name):
    os.makedirs('out', exist_ok=True)
    im.convert('RGB').resize((W, H), Image.LANCZOS).save(f'out/{name}.jpg', quality=92)

def card1():  # gist hunt is on the table -> flipped
    im = Image.new('RGBA', (s(W), s(H)), (255, 210, 31, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, s(620), s(W), s(H)], fill=(255, 111, 174))
    d.line([(0, s(620)), (s(W), s(620))], fill=INK, width=s(8))
    ctext(d, 70, 'gist hunt is on the table.', PB(64))
    paste(im, table(430, 210, with_icon=True), W / 2, 410); d = ImageDraw.Draw(im)
    ctext(d, 665, '*misses one word*', PM(52))
    mixed(d, 300, 1010, '(\u256f\u00b0\u25a1\u00b0)\u256f', 120)
    paste(im, flipped_table(330, 170, rot=150), 780, 900)
    paste(im, icon(110, rot=-40), 960, 770); d = ImageDraw.Draw(im)
    motion(d, 690, 900)
    footer(d); save(im, 'flip01_onthetable')

def card2():  # flip, then put it back
    im = Image.new('RGBA', (s(W), s(H)), (69, 193, 255, 255)); d = ImageDraw.Draw(im)
    ctext(d, 70, "me when \u201calmost\u201d", PB(62)); ctext(d, 150, "meant \u201cnot yet\u201d:", PB(62))
    mixed(d, 330, 440, '(\u256f\u00b0\u25a1\u00b0)\u256f', 110)
    paste(im, flipped_table(290, 150, rot=150), 780, 360); d = ImageDraw.Draw(im)
    motion(d, 690, 370)
    d.line([(s(140), s(560)), (s(940), s(560))], fill=INK, width=s(6))
    ctext(d, 610, 'me 10 seconds later:', PB(62))
    paste(im, table(330, 170, with_icon=True), 330, 860); d = ImageDraw.Draw(im)
    mixed(d, 770, 960, '\u30ce( \u00ba _ \u00ba\u30ce)', 100)
    ctext(d, 1090, 'ok. one more.', PM(56))
    footer(d); save(im, 'flip02_putback')

def card3():  # same meaning? not even close
    im = Image.new('RGBA', (s(W), s(H)), (183, 155, 255, 255)); d = ImageDraw.Draw(im)
    ctext(d, 70, 'same meaning?', PB(84))
    for k, (txt, y) in enumerate([('\u201cI\u2019ll be there in five.\u201d', 230), ('\u201cI\u2019m already there.\u201d', 380)]):
        d.rounded_rectangle([s(130 + 12), s(y + 12), s(950 + 12), s(y + 120 + 12)], s(30), fill=INK)
        d.rounded_rectangle([s(130), s(y), s(950), s(y + 120)], s(30), fill=CREAM, outline=INK, width=s(6))
        d.text((s(540), s(y + 60)), txt, font=PB(48), fill=INK, anchor='mm')
    ctext(d, 570, 'me, who said yes:', PM(54))
    mixed(d, 300, 900, '(\u256f\u00b0\u25a1\u00b0)\u256f', 120)
    paste(im, flipped_table(330, 170, rot=150), 780, 790); d = ImageDraw.Draw(im)
    motion(d, 690, 800)
    ctext(d, 1030, 'not even close.', PB(64))
    d.text((s(W - 40), s(1335)), 'example', font=PM(24), fill=INK, anchor='rd')
    footer(d); save(im, 'flip03_samemeaning')

if __name__ == '__main__':
    card1(); card2(); card3()
    g = Image.new('RGB', (480 * 3, 600))
    for i, n in enumerate(['flip01_onthetable', 'flip02_putback', 'flip03_samemeaning']):
        g.paste(Image.open(f'out/{n}.jpg').resize((480, 600)), (i * 480, 0))
    g.save('grid.jpg', quality=88)
