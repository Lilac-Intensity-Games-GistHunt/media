"""'Have you played your Gist Hunt today?' as a chat thread from Gist Hunt, left on read.  python3 thread.py"""
import os, math
from PIL import Image, ImageDraw, ImageFont

W, H, S = 1080, 1350, 2
IF = '/usr/share/fonts/opentype/inter/'
F = lambda name, size: ImageFont.truetype(IF + name, int(size * S))
REG = lambda z: F('Inter-Regular.otf', z); MED = lambda z: F('Inter-Medium.otf', z); SB = lambda z: F('Inter-SemiBold.otf', z)
BG_FIELDS = [(200, 188, 255), (255, 210, 31), (255, 111, 174), (61, 220, 151), (69, 193, 255), (255, 154, 46)]
SCREEN = (16, 16, 18); BAR = (28, 28, 30); LILAC = (200, 188, 255); INK = (28, 28, 30)
ME = (60, 60, 64); GREY = (142, 142, 147); WHITE = (255, 255, 255)
ICON = Image.open('icon512.png').convert('RGB')

def s(v): return int(round(v * S))

EMOJI_FONT = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
def is_emoji(ch): return ord(ch) >= 0x1F000 or ch in '\u2764\u2728\u2615'
def _emoji_img(ch, px):
    im = Image.new('RGBA', (136, 128), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), ch, font=EMOJI_FONT, embedded_color=True)
    im = im.crop(im.getbbox() or (0, 0, 1, 1))
    k = px / max(im.height, 1)
    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
_EC = {}
def emoji_img(c, px):
    k = (c, px)
    if k not in _EC: _EC[k] = _emoji_img(c, px)
    return _EC[k]
def text_w(t, f):
    """width in final (supersampled) px"""
    em = int(f.size * 1.05)
    return sum((emoji_img(c, em).width + f.size * 0.1) if is_emoji(c) else f.getlength(c) for c in t if c != '\ufe0f')
def draw_line(im, x, y, t, f, fill):
    d = ImageDraw.Draw(im); em = int(f.size * 1.05)
    for c in t:
        if c == '\ufe0f': continue
        if is_emoji(c):
            e = emoji_img(c, em); im.alpha_composite(e, (int(x), int(y + f.size * 0.1))); x += e.width + f.size * 0.1
        else:
            d.text((x, y), c, font=f, fill=fill); x += f.getlength(c)


def avatar(size):
    a = ICON.resize((s(size), s(size)), Image.LANCZOS)
    m = Image.new('L', a.size, 0); ImageDraw.Draw(m).ellipse([0, 0, a.size[0] - 1, a.size[1] - 1], fill=255)
    out = Image.new('RGBA', a.size, (0, 0, 0, 0)); out.paste(a, (0, 0), m); return out

def wrap(text, f, maxw):
    words, out, cur = text.split(' '), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if text_w(t, f) <= maxw * S or not cur: cur = t
        else: out.append(cur); cur = w
    out.append(cur); return out

def render(name, bg, time_label, msgs, receipt, typing=False):
    """msgs: list of ('them'|'me', text). 'them' = Gist Hunt (left, lilac, with the g. avatar)."""
    im = Image.new('RGBA', (s(W), s(H)), bg + (255,))
    d = ImageDraw.Draw(im)
    # phone screen
    x0, y0, x1, y1 = 70, 60, 1010, 1205
    d.rounded_rectangle([s(x0 + 12), s(y0 + 16), s(x1 + 12), s(y1 + 16)], s(60), fill=INK)
    d.rounded_rectangle([s(x0), s(y0), s(x1), s(y1)], s(60), fill=SCREEN, outline=INK, width=s(8))
    # header
    d.rounded_rectangle([s(x0 + 4), s(y0 + 4), s(x1 - 4), s(y0 + 230)], s(56), fill=BAR)
    d.rectangle([s(x0 + 4), s(y0 + 150), s(x1 - 4), s(y0 + 230)], fill=BAR)
    d.text((s(x0 + 48), s(y0 + 112)), '‹', font=REG(80), fill=(10, 132, 255), anchor='lm')
    av = avatar(96); im.alpha_composite(av, (s((x0 + x1) / 2 - 48), s(y0 + 34)))
    d = ImageDraw.Draw(im)
    d.text((s((x0 + x1) / 2), s(y0 + 160)), 'Gist Hunt ›', font=SB(30), fill=WHITE, anchor='ma')
    d.line([(s(x0 + 4), s(y0 + 230)), (s(x1 - 4), s(y0 + 230))], fill=(48, 48, 52), width=s(2))
    # time label
    y = y0 + 270
    d.text((s((x0 + x1) / 2), s(y)), time_label, font=MED(30), fill=GREY, anchor='ma'); y += 70
    f = REG(52); maxw = 690; pad_x, pad_y, lh = 36, 24, 64
    last_them_y = None
    for i, (who, text) in enumerate(msgs):
        if all(is_emoji(c) for c in text if c != '\ufe0f'):
            big = s(118); x = s(x0 + 130) if who == 'them' else None
            ems = [emoji_img(c, big) for c in text if c != '\ufe0f']
            tw_e = sum(e.width for e in ems) + s(10) * (len(ems) - 1)
            if x is None: x = s(x1 - 40) - tw_e
            for e in ems:
                im.alpha_composite(e, (int(x), s(y))); x += e.width + s(10)
            d = ImageDraw.Draw(im)
            nxt = msgs[i + 1][0] if i + 1 < len(msgs) else None
            if who == 'them' and nxt != 'them' and not typing:
                im.alpha_composite(avatar(76), (s(x0 + 36), s(y + 118 - 76))); d = ImageDraw.Draw(im)
            y += 118 + (14 if nxt == who else 34)
            continue
        ls = wrap(text, f, maxw)
        tw = max(text_w(l, f) for l in ls) / S
        bw, bh = tw + 2 * pad_x, len(ls) * lh + 2 * pad_y - 8
        if who == 'them':
            bx = x0 + 130
            col, tc = LILAC, INK
        else:
            bx = x1 - 40 - bw
            col, tc = ME, WHITE
        d.rounded_rectangle([s(bx), s(y), s(bx + bw), s(y + bh)], s(min(46, bh / 2)), fill=col)
        for k, l in enumerate(ls):
            draw_line(im, s(bx + pad_x), s(y + pad_y + k * lh), l, f, tc)
        d = ImageDraw.Draw(im)
        nxt = msgs[i + 1][0] if i + 1 < len(msgs) else None
        if who == 'them' and nxt != 'them' and not typing:
            im.alpha_composite(avatar(76), (s(x0 + 36), s(y + bh - 76))); d = ImageDraw.Draw(im)
        last_them_y = y + bh
        y += bh + (14 if nxt == who else 34)
    if typing:
        bx = x0 + 130; bw, bh = 160, 92
        d.rounded_rectangle([s(bx), s(y), s(bx + bw), s(y + bh)], s(39), fill=LILAC)
        for j in range(3):
            cx = bx + 44 + j * 36; d.ellipse([s(cx - 11), s(y + 35), s(cx + 11), s(y + 57)], fill=(110, 96, 170))
        im.alpha_composite(avatar(76), (s(x0 + 36), s(y + bh - 76))); d = ImageDraw.Draw(im)
        y += bh + 34
    if receipt:
        d.text((s(x1 - 44), s(y - 14)), receipt, font=MED(30), fill=GREY, anchor='ra')
    # footer
    url = 'playgisthunt.com'; uf = SB(40); uw = uf.getlength(url) / S
    cx, cy, r = W / 2 - uw / 2 - 30, 1281, 17
    pts = [(s(cx + (r if i % 2 == 0 else r * .32) * math.cos(math.pi / 4 * i - math.pi / 2)),
            s(cy + (r if i % 2 == 0 else r * .32) * math.sin(math.pi / 4 * i - math.pi / 2))) for i in range(8)]
    d.polygon(pts, fill=INK)
    d.text((s(W / 2 + 8), s(1281)), url, font=uf, fill=INK, anchor='mm')
    os.makedirs('out', exist_ok=True)
    im.convert('RGB').resize((W, H), Image.LANCZOS).save(f'out/{name}.jpg', quality=92)

POSTS = [
    ('th01_qq', 'Today 9:02 AM', [('them', 'have you played your gist hunt today'), ('them', '?'), ('them', '??')], 'Read 9:14 AM', False),
    ('th02_hours', 'Today 1:12 PM', [('them', 'hey'), ('them', 'hey'), ('them', 'it’s 3 questions'), ('them', 'it takes like 3 minutes')], 'Read 1:12 PM', False),
    ('th03_online', 'Today 4:40 PM', [('them', 'have you played your gist hunt today'), ('them', 'i can see you’re online')], 'Read 4:41 PM', True),
    ('th04_k', 'Today 10:20 AM', [('them', 'have you played your gist hunt today'), ('me', 'k'), ('them', 'k?'), ('them', 'k with no period or k.'), ('them', 'because those mean different things')], None, False),
    ('th05_notmad', 'Today 6:03 PM', [('them', 'i’m not mad'), ('them', 'i’m just asking'), ('them', 'have you played your gist hunt today')], 'Read 6:03 PM', True),
    ('th06_late', 'Today 11:58 PM', [('them', 'u up?'), ('them', 'have you played your gist hunt today')], 'Read 11:58 PM', False),
    ('th07_eyes', 'Today 8:30 AM', [('them', 'good morning'), ('them', 'have you played your gist hunt today'), ('them', '…'), ('them', '……')], 'Read 8:31 AM', True),
    ('th08_played', 'Today 7:46 PM', [('them', 'have you played your gist hunt today'), ('me', 'played. 3/3'), ('them', 'proud of u'), ('them', 'same time tomorrow?')], None, False),
]

if __name__ == '__main__':
    for i, (n, t, m, r, ty) in enumerate(POSTS):
        render(n, BG_FIELDS[i % len(BG_FIELDS)], t, m, r, ty)
    fs = [p[0] for p in POSTS]
    g = Image.new('RGB', (360 * 4, 450 * 2))
    for i, n in enumerate(fs):
        g.paste(Image.open(f'out/{n}.jpg').resize((360, 450)), ((i % 4) * 360, (i // 4) * 450))
    g.save('grid.jpg', quality=88)
