"""Gist Hunt ad: "They keep saying Gen Z can't read. I beg to differ."
No-face, text-led, 1080x1920, 30 fps. Board = real Oct 29 Gist Daily Q1 (already public on Oct 30).
Usage: python3 render.py stills   -> key frames to ./stills
       python3 render.py video    -> ./out/ad.mp4 (+ cover.jpg)
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "fonts")
GF = "/usr/share/fonts/truetype/google-fonts"

def font(w, size):
    p = os.path.join(F, f"Poppins-{w}.ttf")
    if not os.path.exists(p):
        p = os.path.join(GF, f"Poppins-{w}.ttf")
    return ImageFont.truetype(p, size)

SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CREAM = (251, 246, 238)
CARD = (255, 255, 255)
LILAC = (185, 166, 224)
LILAC_SOFT = (236, 229, 248)
LILAC_DEEP = (122, 92, 196)
NAVY = (31, 36, 64)
MUTED = (110, 108, 128)
ROSE = (226, 110, 128)
ROSE_SOFT = (250, 222, 226)
BORDER = (226, 219, 238)

# ---------- timeline (seconds) ----------
T_HOOK, T_BEG, T_BOARD, T_FAIL, T_REREAD, T_PUNCH, T_END, T_TOTAL = 0.0, 2.0, 3.4, 7.4, 8.6, 12.0, 14.8, 17.0
TAP_A, TAP_D = 4.6, 5.8
HL_STORY = (8.95, 9.65)   # marker sweep on "ideally"
HL_CARD = (10.15, 10.75)  # marker sweep on "must have a lid"
T_NEQ = 10.95
T_PUNCH2 = 13.2

# ---------- the real board (Gist Daily, Oct 29, Q1) ----------
CHALLENGE = "Two of these mean the same as the story. The rest quietly don’t."
STORY = ("Tomorrow we grow crystals. Each student should bring one clean jar, ideally with a lid. "
         "Please do not send the good jam jar again. Mrs. Okoro has asked about it twice.")
CARDS = [
    ("A", "Every student brings one clean jar tomorrow, and it must have a lid. Not the jam jar."),
    ("B", "Tomorrow each student brings a couple of clean jars, ideally with lids. Spare the jam jar."),
    ("C", "Every student brings a single clean jar tomorrow. A lid is nice but not required."),
    ("D", "For tomorrow’s crystals, one clean jar each, lid if possible. Not the good jam jar."),
    ("E", "One clean jar per table tomorrow, lid if you have one. The good jam jar stays home."),
]

def ease_out(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

def ease_back(x):
    x = max(0.0, min(1.0, x)); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def clamp01(x): return max(0.0, min(1.0, x))

# ---------- text layout ----------
def layout(text, fnt, maxw, x0, y0, lh):
    """Greedy wrap; returns (words list of (word, x, y, w), height)."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    space = d.textlength(" ", font=fnt)
    out, x, y = [], x0, y0
    for wd in text.split(" "):
        w = d.textlength(wd, font=fnt)
        if x > x0 and x + w > x0 + maxw:
            x, y = x0, y + lh
        out.append((wd, x, y, w)); x += w + space
    return out, (y - y0) + lh

def draw_words(d, words, fnt, fill):
    for wd, x, y, w in words:
        d.text((x, y), wd, font=fnt, fill=fill)

def span_boxes(words, phrase_words, fnt_size, lh):
    """Boxes (per line) covering the consecutive words starting where phrase matches."""
    toks = [w[0].strip(".,’'") for w in words]
    n = len(phrase_words)
    for i in range(len(toks) - n + 1):
        if [t.lower() for t in toks[i:i + n]] == [p.lower() for p in phrase_words]:
            seg = words[i:i + n]; boxes = []
            for wd, x, y, w in seg:
                if boxes and abs(boxes[-1][1] - y) < 2:
                    boxes[-1][2] = x + w
                else:
                    boxes.append([x, y, x + w])
            return [(bx0, by, bx1) for bx0, by, bx1 in boxes]
    raise ValueError(phrase_words)

def centered(d, text, fnt, cy, fill, maxw=900, lh=None):
    lh = lh or int(fnt.size * 1.18)
    lines, cur = [], ""
    for wd in text.split(" "):
        test = (cur + " " + wd).strip()
        if d.textlength(test, font=fnt) > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = test
    lines.append(cur)
    top = cy - lh * len(lines) / 2
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=fnt)
        d.text(((W - w) / 2, top + i * lh), ln, font=fnt, fill=fill)
    return top, top + lh * len(lines)

def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

# ---------- board geometry (computed once) ----------
BX0, BX1 = 70, W - 70
F_EYE = font("SemiBold", 26)
F_CH = font("Bold", 44)
F_STORY = font("Regular", 33)
F_CARD = font("Medium", 31)
F_LET = font("Bold", 30)

def board_geometry():
    g = {}
    y = 440
    g["eye_y"] = y; y += 50
    ch, h = layout(CHALLENGE, F_CH, BX1 - BX0, BX0, y, 56); g["ch"] = ch; y += h + 22
    pad = 26
    st, h = layout(STORY, F_STORY, BX1 - BX0 - 2 * pad, BX0 + pad, y + pad, 44)
    g["story_box"] = (BX0, y, BX1, y + h + 2 * pad - 6); g["story"] = st; y = g["story_box"][3] + 22
    cards = []
    for let, txt in CARDS:
        tx = BX0 + 92
        ws, h = layout(txt, F_CARD, BX1 - tx - 26, tx, y + 18, 41)
        box = (BX0, y, BX1, y + h + 32)
        cards.append({"let": let, "words": ws, "box": box}); y = box[3] + 14
    g["cards"] = cards; g["bottom"] = y - 14
    return g

G = board_geometry()

def draw_board(img, t, selected, wrong=None, dim=0.0, hl_story=0.0, hl_card=0.0, shake=0.0):
    d = ImageDraw.Draw(img, "RGBA")
    # eyebrow (letter-spaced small caps)
    eye = "DAILY WORD PUZZLE · GIST HUNT"
    x = BX0
    for ch in eye:
        d.text((x, G["eye_y"]), ch, font=F_EYE, fill=LILAC_DEEP); x += d.textlength(ch, font=F_EYE) + 3
    draw_words(d, G["ch"], F_CH, NAVY)
    # story panel
    rr(d, G["story_box"], 26, fill=LILAC_SOFT)
    if hl_story > 0:
        for bx0, by, bx1 in span_boxes(G["story"], ["ideally"], 33, 44):
            ww = (bx1 - bx0 + 16) * ease_out(hl_story)
            rr(d, (bx0 - 8, by + 2, bx0 - 8 + ww, by + 46), 8, fill=(255, 214, 102, 230))
    draw_words(d, G["story"], F_STORY, NAVY)
    # cards
    for c in G["cards"]:
        x0, y0, x1, y1 = c["box"]
        dx = 0
        if wrong == c["let"] and shake > 0:
            dx = int(14 * math.sin(shake * 40) * (1 - shake))
        sel = c["let"] in selected
        is_wrong = wrong == c["let"]
        fill = ROSE_SOFT if is_wrong else (LILAC_SOFT if sel else CARD)
        outl = ROSE if is_wrong else (LILAC_DEEP if sel else BORDER)
        rr(d, (x0 + dx, y0, x1 + dx, y1), 22, fill=fill, outline=outl, width=4 if (sel or is_wrong) else 2)
        cx, cy = x0 + 46 + dx, y0 + 18 + 22
        d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=(outl if (sel or is_wrong) else LILAC_SOFT))
        lt = c["let"]; lw = d.textlength(lt, font=F_LET)
        d.text((cx - lw / 2, cy - 22), lt, font=F_LET, fill=(CARD if (sel or is_wrong) else LILAC_DEEP))
        if c["let"] == "A" and hl_card > 0:
            for bx0, by, bx1 in span_boxes(c["words"], ["must", "have", "a", "lid"], 31, 41):
                total = bx1 - bx0 + 16
                ww = total * ease_out(hl_card)
                rr(d, (bx0 - 8 + dx, by + 2, bx0 - 8 + dx + ww, by + 44), 8, fill=(255, 214, 102, 230))
        for wd, x, y, w in c["words"]:
            d.text((x + dx, y), wd, font=F_CARD, fill=NAVY)
    if dim > 0:
        d.rectangle((0, 0, W, H), fill=(251, 246, 238, int(170 * dim)))
    return d

def card_center(let):
    for c in G["cards"]:
        if c["let"] == let:
            x0, y0, x1, y1 = c["box"]; return ((x0 + x1) / 2 + 180, (y0 + y1) / 2)

def draw_tap(d, t, t_tap, let):
    k = (t - t_tap) / 0.35
    if -0.25 < k < 1.0:
        cx, cy = card_center(let)
        if k < 0:  # finger arriving
            a = clamp01(1 + k / 0.25); r = 46
        else:
            a = 1 - k; r = 46 + 40 * k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(31, 36, 64, int(70 * a)), outline=(31, 36, 64, int(160 * a)), width=5)

def band_text(d, text, t_in, t, fnt=None, fill=NAVY, sticker=True, italic=False):
    """Meme caption in the top band (y 270-410)."""
    fnt = fnt or font("Bold", 76)
    k = ease_back((t - t_in) / 0.25)
    if k <= 0: return
    tw = d.textlength(text, font=fnt)
    s = max(0.01, k)
    layer = Image.new("RGBA", (int(tw + 90), 150), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    if sticker:
        rr(ld, (0, 15, layer.width, 135), 30, fill=(*LILAC, 255))
    ld.text((45, 20), text, font=fnt, fill=fill)
    if s != 1:
        layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
    layer = layer.rotate(-3, expand=True, resample=Image.BICUBIC)
    return layer

def paste_center(img, layer, cy):
    if layer is None: return
    img.paste(layer, (int((W - layer.width) / 2), int(cy - layer.height / 2)), layer)

# ---------- frames ----------
def frame(t):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")

    if t < T_BEG:  # HOOK: words pop in
        words = ["they", "keep", "saying", "Gen Z", "can’t", "read"]
        fnt = font("Bold", 104)
        lines = [["they", "keep", "saying"], ["Gen Z", "can’t", "read"]]
        idx = 0; ys = [760, 900]
        for li, ln in enumerate(lines):
            full = " ".join(ln); tw = d.textlength(full, font=fnt); x = (W - tw) / 2
            for wd in ln:
                ti = 0.12 + idx * 0.14
                a = clamp01((t - ti) / 0.12)
                if a > 0:
                    yy = ys[li] + 18 * (1 - a)
                    col = LILAC_DEEP if wd in ("Gen Z",) else NAVY
                    d.text((x, yy), wd, font=fnt, fill=(*col, int(255 * a)))
                x += d.textlength(wd + " ", font=fnt); idx += 1
        # side-eye marks
        if t > 1.15:
            a = clamp01((t - 1.15) / 0.2)
            d.text((W / 2 - 60, 1110), "…", font=font("Bold", 120), fill=(*MUTED, int(255 * a)))
        eyebrow(d)
        return img

    if t < T_BOARD:  # I BEG TO DIFFER
        k = (t - T_BEG)
        img = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(img, "RGBA")
        s = 1.25 - 0.25 * ease_out(k / 0.35)
        layer = Image.new("RGBA", (W, 600), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        f1 = font("Bold", 130)
        for i, ln in enumerate(["I beg to", "differ."]):
            tw = ld.textlength(ln, font=f1)
            ld.text(((W - tw) / 2, 140 + i * 160), ln, font=f1, fill=CREAM if i == 0 else LILAC)
        layer = layer.resize((int(W * s), int(600 * s)), Image.LANCZOS)
        img.paste(layer, (int((W - layer.width) / 2), int(960 - layer.height / 2)), layer)
        # tiny "sets coffee down" beat: a lilac underline that draws in
        if k > 0.55:
            ww = 520 * ease_out((k - 0.55) / 0.3)
            rr(d, (W / 2 - 260, 1215, W / 2 - 260 + ww, 1229), 7, fill=LILAC)
        return img

    if t < T_FAIL:  # BOARD, rushing
        selected = set()
        if t >= TAP_A + 0.05: selected.add("A")
        if t >= TAP_D + 0.05: selected.add("D")
        draw_board(img, t, selected)
        d = ImageDraw.Draw(img, "RGBA")
        draw_tap(d, t, TAP_A, "A"); draw_tap(d, t, TAP_D, "D")
        if t < 5.2:
            paste_center(img, band_text(d, "easy.", 3.65, t), 340)
        else:
            paste_center(img, band_text(d, "obviously.", 5.2, t), 340)
        # speed lines while rushing
        if 4.3 < t < 6.3:
            for i in range(6):
                yy = 300 + i * 260 + int((t * 900) % 260)
                d.line((30, yy, 30, yy + 90), fill=(*LILAC, 140), width=6)
                d.line((W - 30, yy + 120, W - 30, yy + 210), fill=(*LILAC, 140), width=6)
        return img

    if t < T_REREAD:  # NOT QUITE
        k = t - T_FAIL
        draw_board(img, t, {"A", "D"}, wrong="A", dim=0.55 * ease_out(k / 0.15), shake=clamp01(k / 0.5))
        d = ImageDraw.Draw(img, "RGBA")
        s = ease_back(k / 0.22)
        if s > 0:
            fq = font("Bold", 120)
            tw = d.textlength("Not quite.", font=fq)
            layer = Image.new("RGBA", (int(tw + 120), 230), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            rr(ld, (0, 0, layer.width, 230), 46, fill=(*CARD, 255), outline=(*ROSE, 255), width=8)
            ld.text((60, 30), "Not quite.", font=fq, fill=ROSE)
            layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
            paste_center(img, layer, 735)
        return img

    if t < T_PUNCH:  # READ IT AGAIN
        hs = clamp01((t - HL_STORY[0]) / (HL_STORY[1] - HL_STORY[0]))
        hc = clamp01((t - HL_CARD[0]) / (HL_CARD[1] - HL_CARD[0]))
        draw_board(img, t, set(), wrong="A" if t >= HL_CARD[0] else None, hl_story=hs, hl_card=hc)
        d = ImageDraw.Draw(img, "RGBA")
        if t < T_NEQ:
            paste_center(img, band_text(d, "*reads it again*", T_REREAD + 0.05, t,
                                        fnt=font("SemiBold", 64), sticker=False, fill=NAVY), 340)
        else:
            lay = band_text(d, "ideally  ≠  must", T_NEQ, t, fnt=font("Bold", 72))
            paste_center(img, lay, 340)
        # slow-reading cursor under story text
        if t < HL_STORY[0]:
            k = clamp01((t - T_REREAD) / (HL_STORY[0] - T_REREAD))
            wds = G["story"]; i = min(len(wds) - 1, int(k * 14))
            wd, x, y, w = wds[i]
            rr(d, (x, y + 44, x + w, y + 50), 3, fill=LILAC_DEEP)
        return img

    if t < T_END:  # PUNCHLINE
        f1 = font("Bold", 96)
        k1 = ease_out((t - T_PUNCH) / 0.25)
        d.text((0, 0), "", font=f1)
        centered(d, "ok.", font("Bold", 150), 700, (*NAVY, int(255 * k1)))
        centered(d, "we can read.", f1, 880, (*NAVY, int(255 * k1)))
        if t >= T_PUNCH2:
            k2 = ease_back((t - T_PUNCH2) / 0.25)
            layer = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            rr(ld, (90, 40, W - 90, 380), 40, fill=(*LILAC, 255))
            fb = font("Bold", 92)
            for i, ln in enumerate(["we just read", "at 2x speed."]):
                tw = ld.textlength(ln, font=fb)
                ld.text(((W - tw) / 2, 80 + i * 120), ln, font=fb, fill=NAVY)
            s = max(0.01, k2)
            layer = layer.resize((int(W * s), max(1, int(420 * s))), Image.LANCZOS).rotate(-2, expand=True, resample=Image.BICUBIC)
            paste_center(img, layer, 1190)
        eyebrow(d)
        return img

    # END CARD
    k = ease_out((t - T_END) / 0.3)
    fw = font("Bold", 110)
    d.text((0, 0), "", font=fw)
    star = ImageFont.truetype(SYM, 92)
    tw = d.textlength("Gist Hunt", font=fw); sw = d.textlength("✦", font=star)
    x = (W - tw - sw - 24) / 2
    d.text((x, 560 + 30 * (1 - k)), "✦", font=star, fill=(*LILAC_DEEP, int(255 * k)))
    d.text((x + sw + 24, 540 + 30 * (1 - k)), "Gist Hunt", font=fw, fill=(*NAVY, int(255 * k)))
    centered(d, "One free puzzle a day.", font("SemiBold", 56), 790, (*NAVY, int(255 * k)))
    centered(d, "Every word counts.", font("Regular", 50), 870, (*MUTED, int(255 * k)))
    rr(d, (190, 960, W - 190, 1070), 55, fill=(*NAVY, int(255 * k)))
    centered(d, "playgisthunt.com", font("Bold", 56), 1012, (*CREAM, int(255 * k)))
    k2 = ease_back((t - T_END - 0.45) / 0.3)
    if k2 > 0:
        layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        rr(ld, (110, 20, W - 110, 240), 34, fill=(*LILAC_SOFT, 255), outline=(*LILAC, 255), width=4)
        fs = font("SemiBold", 50)
        for i, ln in enumerate(["Send this to the friend", "who reads too fast."]):
            lw = ld.textlength(ln, font=fs); ld.text(((W - lw) / 2, 52 + i * 70), ln, font=fs, fill=NAVY)
        layer = layer.resize((max(1, int(W * k2)), max(1, int(260 * k2))), Image.LANCZOS)
        paste_center(img, layer, 1300)
    return img

def eyebrow(d):
    f = F_EYE; txt = "✦ GIST HUNT"
    x = (W - 230) / 2
    star = ImageFont.truetype(SYM, 26)
    d.text((x, 300), "✦", font=star, fill=LILAC_DEEP)
    x += 40
    for ch in "GIST HUNT":
        d.text((x, 300), ch, font=f, fill=LILAC_DEEP); x += d.textlength(ch, font=f) + 4

# ---------- audio ----------
SR = 44100

def tone(f, dur, amp=0.3, decay=6.0, kind="sine"):
    t = np.arange(int(SR * dur)) / SR
    if kind == "sine": w = np.sin(2 * np.pi * f * t)
    elif kind == "tri": w = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))
    else: w = np.sign(np.sin(2 * np.pi * f * t)) * 0.5
    env = np.exp(-decay * t) * np.minimum(1, t / 0.004)
    return amp * w * env

def noise(dur, amp=0.3, decay=30.0, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(int(SR * dur)) / SR
    return amp * rng.standard_normal(len(t)) * np.exp(-decay * t)

def lowpass(x, a):
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc); y[i] = acc
    return y

def add(buf, sig, at):
    i = int(at * SR); j = min(len(buf), i + len(sig))
    if i < len(buf): buf[i:j] += sig[:j - i]

def kick():
    t = np.arange(int(SR * 0.25)) / SR
    f = 120 * np.exp(-18 * t) + 45
    return 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)

def music(buf, start, end, bpm=104, seed=1):
    beat = 60 / bpm
    bass = [55.0, 55.0, 65.41, 73.42, 55.0, 55.0, 82.41, 73.42]  # A1 C2 D2 E2
    pluck = [440, 523.25, 659.25, 587.33, 523.25, 659.25, 783.99, 659.25]
    n = 0; t = start
    hat = noise(0.05, 0.06, 90, seed)
    while t < end - 0.01:
        if n % 2 == 0: add(buf, kick(), t)
        if n % 4 == 2: add(buf, noise(0.12, 0.10, 35, seed + n), t)  # snare-ish
        add(buf, hat, t + beat / 2)
        add(buf, tone(bass[n % 8], beat * 0.9, 0.22, 4, "tri"), t)
        add(buf, tone(pluck[n % 8], 0.22, 0.07, 14, "tri"), t + beat / 2)
        t += beat; n += 1

def build_audio(path):
    buf = np.zeros(int(SR * T_TOTAL) + SR)
    # hook: soft pops per word
    for i in range(6):
        add(buf, tone(900 + 60 * i, 0.06, 0.18, 60), 0.12 + i * 0.14)
    # whoosh + boom on "I beg to differ"
    wh = noise(0.45, 0.35, 4, 7)
    env = np.sin(np.linspace(0, np.pi, len(wh)))
    add(buf, lowpass(wh * env, 0.08), T_BEG - 0.25)
    add(buf, kick() * 1.4, T_BEG + 0.05)
    # music bed while rushing
    seg = np.zeros_like(buf); music(seg, T_BOARD, T_FAIL)
    fade_i = int(T_BOARD * SR); seg[fade_i:fade_i + int(0.15 * SR)] *= np.linspace(0, 1, int(0.15 * SR))
    buf += seg * 0.9
    # taps
    for tt in (TAP_A, TAP_D):
        add(buf, noise(0.03, 0.35, 160, 3), tt); add(buf, tone(1800, 0.04, 0.15, 90), tt)
    # record scratch at the fail (music cut is the hard stop at T_FAIL)
    n = int(0.32 * SR); t = np.arange(n) / SR
    f = 300 + 1400 * np.abs(np.sin(2 * np.pi * 3.2 * t))
    scr = 0.30 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-5 * t)
    add(buf, lowpass(scr + noise(n / SR, 0.12, 6, 9)[:n], 0.25), T_FAIL)
    # "not quite" two-note fall
    add(buf, tone(659.25, 0.35, 0.22, 5), T_FAIL + 0.30)
    add(buf, tone(523.25, 0.55, 0.22, 4), T_FAIL + 0.55)
    # clock tick while re-reading
    tt = T_REREAD + 0.1
    i = 0
    while tt < T_PUNCH - 0.05:
        add(buf, tone(2400 if i % 2 == 0 else 2000, 0.025, 0.10, 120), tt); add(buf, noise(0.02, 0.05, 200, i), tt)
        tt += 0.5; i += 1
    # marker swishes
    for a, b in (HL_STORY, HL_CARD):
        sw = noise(b - a, 0.08, 1.5, 11); add(buf, lowpass(sw, 0.3), a)
    add(buf, tone(1318.5, 0.4, 0.14, 7), T_NEQ)  # ding
    # punchline: music returns on line 2
    add(buf, tone(880, 0.12, 0.12, 25), T_PUNCH)
    seg2 = np.zeros_like(buf); music(seg2, T_PUNCH2, T_TOTAL, seed=21)
    buf += seg2 * 0.75
    # end chime
    for i, fq in enumerate((523.25, 659.25, 783.99, 1046.5)):
        add(buf, tone(fq, 0.8, 0.12, 4), T_END + 0.05 + i * 0.07)
    buf = buf[:int(SR * T_TOTAL)]
    # fade last 0.25 s, soft clip, normalize to -1 dBFS
    fo = int(0.25 * SR); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = np.tanh(buf * 1.4) / np.tanh(1.4)
    buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.89
    pcm = (buf * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

# ---------- render ----------
SCENES = [(T_HOOK, T_BEG), (T_BEG, T_BOARD), (T_BOARD, T_FAIL), (T_FAIL, T_REREAD),
          (T_REREAD, T_PUNCH), (T_PUNCH, T_END), (T_END, T_TOTAL)]

def render_scene(i, a, b, outdir):
    out = os.path.join(outdir, f"s{i}.mp4"); tmp = os.path.join(outdir, f"s{i}.tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    n0, n1 = round(a * FPS), round(b * FPS)
    for n in range(n0, n1):
        p.stdin.write(frame(n / FPS).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0
    os.replace(tmp, out); return out

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    if mode == "stills":
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        for t in [float(x) for x in (sys.argv[2:] or ["1.5", "3.2", "5.5", "7.9", "11.5", "14.0", "16.5"])]:
            frame(t).convert("RGB").save(os.path.join(HERE, "stills", f"t{t:05.2f}.png"))
        print("board bottom y =", G["bottom"])
    else:
        outdir = os.path.join(HERE, "out"); os.makedirs(outdir, exist_ok=True)
        import concurrent.futures as cf
        with cf.ProcessPoolExecutor() as ex:
            files = list(ex.map(render_scene, range(len(SCENES)), [s[0] for s in SCENES], [s[1] for s in SCENES], [outdir] * len(SCENES)))
        with open(os.path.join(outdir, "list.txt"), "w") as f:
            for fn in files: f.write(f"file '{fn}'\n")
        build_audio(os.path.join(outdir, "audio.wav"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"),
                        "-c", "copy", os.path.join(outdir, "video.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "video.mp4"), "-i", os.path.join(outdir, "audio.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", os.path.join(outdir, "gisthunt_genz_cant_read.mp4")], check=True)
        # cover: hook + punch, 1080x1920 (Instagram crops 3:4 from centre)
        c = frame(1.9).convert("RGB"); c.save(os.path.join(outdir, "cover.jpg"), quality=92)
        print("done")
