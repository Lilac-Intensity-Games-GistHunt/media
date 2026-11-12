"""Gist Hunt ad 3: "They say Gen Z can't read." Fast version: less text, saturated colour, lots of motion.
Made-up example round, hinge words "about to". 1080x1920, 30 fps, 13 s.
Usage: python3 genz2.py stills [t ...] | video
"""
import math, os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from render import (font, ease_out, ease_back, clamp01, rr, tone, noise, add, kick, music, lowpass, SR, SYM)

W, H, FPS = 1080, 1920, 30
T_BEG, T_BOARD, T_FAIL, T_REREAD, T_PUNCH, T_END, T_TOTAL = 2.1, 3.4, 7.6, 8.8, 12.0, 14.8, 17.0
WORD_T = [0.1, 0.42, 0.82, 1.3, 1.6]   # they / say / Gen Z / can't / read
TAP = 6.1
HL_S, HL_B = (9.2, 9.8), (10.2, 10.8)
T_BED = 11.0
T_P1, T_P2 = 12.4, 13.2

VIOLET = (112, 56, 232); VIOLET_D = (60, 24, 150); PINK = (240, 64, 150); YELLOW = (255, 212, 56)
CREAM = (255, 248, 236); NAVY = (24, 22, 58); RED = (255, 64, 96); RED_SOFT = (255, 222, 228); MINT = (64, 214, 160)

LABEL = "GROUP CHAT · 11:58 PM"
STORY = "“I’m about to leave.”"
CARDS = [("A", "I’m on my way."), ("B", "I haven’t left yet."), ("C", "I’m already there.")]

# ---------- background ----------
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)

def gradient(t, c1, c2, speed=0.35):
    a = 0.9 + 0.25 * math.sin(t * 0.7)
    s = 0.5 + 0.5 * np.sin(((_xx * math.cos(a) + _yy * math.sin(a)) / 1400.0 + t * speed) * 2 * math.pi)
    s = s[..., None]
    arr = np.array(c1, np.float32) * (1 - s) + np.array(c2, np.float32) * s
    return Image.fromarray(arr.astype(np.uint8), "RGB")

rng = np.random.default_rng(4)
SPARKS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(24, 60), rng.uniform(40, 110), rng.uniform(0, 6.28)) for _ in range(22)]

def sparkles(img, t, alpha=110, col=CREAM):
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, size, sp, ph in SPARKS:
        yy = (y - t * sp) % H
        a = int(alpha * (0.5 + 0.5 * math.sin(t * 3 + ph)))
        d.text((x, yy), "✦", font=ImageFont.truetype(SYM, int(size)), fill=(*col, a))

# ---------- camera ----------
def impulses(t, times, amp, k=9.0, f=55.0):
    v = 0.0
    for ti in times:
        if t >= ti:
            dt = t - ti; v += amp * math.exp(-k * dt) * math.sin(dt * f)
    return v

def camera(img, zoom=1.04, dx=0.0, dy=0.0, rot=0.0, cy=None, bg=VIOLET):
    if rot:
        img = img.rotate(rot, resample=Image.BILINEAR, fillcolor=bg)
    cw, ch = W / zoom, H / zoom
    cx = W / 2 + dx; cyy = (cy if cy is not None else H / 2) + dy
    x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cyy - ch / 2, 0), H - ch)
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

# ---------- drawing helpers ----------
def text_layer(text, fnt, fill, stroke=0, stroke_fill=None, pad=30):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    l, tp, r, b = d.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    lay = Image.new("RGBA", (r - l + 2 * pad, b - tp + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((pad - l, pad - tp), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return lay

def put(img, lay, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if lay is None or scale <= 0.01 or alpha <= 0: return
    if scale != 1:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
    if rot:
        lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha)); lay.putalpha(a)
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)

def sticker(text, fnt, bg=YELLOW, fg=NAVY):
    tl = text_layer(text, fnt, fg, pad=0)
    lay = Image.new("RGBA", (tl.width + 80, tl.height + 56), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rr(d, (6, 10, lay.width, lay.height), 28, fill=(0, 0, 0, 70))  # drop shadow
    rr(d, (0, 0, lay.width - 6, lay.height - 10), 28, fill=(*bg, 255))
    lay.paste(tl, (37, 23), tl)
    return lay

def pop(t, t0, dur=0.28):
    return ease_back((t - t0) / dur)

def wobble(t, t0, amp=4.0):
    return amp * math.sin((t - t0) * 9) * math.exp(-(t - t0) * 1.2) - 3

# ---------- board ----------
F_CH = font("Bold", 58); F_LBL = font("SemiBold", 30); F_ST = font("Bold", 74); F_CD = font("SemiBold", 62); F_LET = font("Bold", 44)
PANEL = (70, 600, W - 70, 840)
CARD_Y = [880, 1040, 1200]; CARD_H = 136

def card_slide(t, i):
    k = ease_back((t - (T_BOARD + 0.1 + i * 0.16)) / 0.45)
    return (1 - k) * 700 if k < 1 else 0.0

def draw_board(img, t, picked=None, wrong=None, right=None, hs=0.0, hb=0.0, shake_card=0.0, entering=True):
    d = ImageDraw.Draw(img, "RGBA")
    # challenge line
    k = clamp01((t - T_BOARD) / 0.2) if entering else 1
    ch = text_layer("Which one means the same?", F_CH, CREAM, stroke=0)
    put(img, ch, W / 2, 530, scale=0.9 + 0.1 * ease_out(k) if k < 1 else 1, alpha=k)
    # story panel
    off = card_slide(t, -1) if entering else 0
    x0, y0, x1, y1 = PANEL
    rr(d, (x0 + 8, y0 + 12 + off, x1 + 8, y1 + 12 + off), 40, fill=(0, 0, 0, 60))
    rr(d, (x0, y0 + off, x1, y1 + off), 40, fill=CREAM)
    lx = x0 + 44
    for c in LABEL:
        d.text((lx, y0 + 34 + off), c, font=F_LBL, fill=VIOLET); lx += d.textlength(c, font=F_LBL) + 4
    # story text with highlight on "about to"
    sx, sy = x0 + 44, y0 + 98 + off
    pre, hlw, post = "“I’m ", "about to", " leave.”"
    w_pre = d.textlength(pre, font=F_ST); w_hl = d.textlength(hlw, font=F_ST)
    if hs > 0:
        rr(d, (sx + w_pre - 12, sy + 2, sx + w_pre - 12 + (w_hl + 24) * ease_out(hs), sy + 98), 16, fill=(*YELLOW, 255))
    d.text((sx, sy), pre + hlw + post, font=F_ST, fill=NAVY)
    # cards
    for i, (let, txt) in enumerate(CARDS):
        off = card_slide(t, i) if entering else 0
        y = CARD_Y[i] + off
        dx = int(18 * math.sin(shake_card * 45) * (1 - shake_card)) if (wrong == let and shake_card > 0) else 0
        bounce = 0
        if picked == let and t < TAP + 0.4:
            bounce = -14 * math.sin(clamp01((t - TAP) / 0.3) * math.pi)
        y += bounce
        if wrong == let: fill, ring, txtc, badge = RED, RED, CREAM, CREAM
        elif right == let: fill, ring, txtc, badge = MINT, MINT, NAVY, NAVY
        elif picked == let: fill, ring, txtc, badge = YELLOW, YELLOW, NAVY, NAVY
        else: fill, ring, txtc, badge = CREAM, CREAM, NAVY, VIOLET
        rr(d, (70 + dx + 8, y + 12, W - 70 + dx + 8, y + CARD_H + 12), 36, fill=(0, 0, 0, 60))
        rr(d, (70 + dx, y, W - 70 + dx, y + CARD_H), 36, fill=fill)
        cx, cy = 70 + 64 + dx, y + CARD_H / 2
        d.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), outline=badge, width=5)
        lw = d.textlength(let, font=F_LET); d.text((cx - lw / 2, cy - 31), let, font=F_LET, fill=badge)
        tx = 70 + 130 + dx
        if let == "B" and hb > 0:
            wb = d.textlength("I haven’t left yet", font=F_CD)
            rr(d, (tx - 10, y + 26, tx - 10 + (wb + 20) * ease_out(hb), y + CARD_H - 22), 14, fill=(*YELLOW, 255))
        d.text((tx, y + 28), txt, font=F_CD, fill=txtc)

def tap_ripple(img, t):
    k = (t - TAP) / 0.4
    if -0.2 < k < 1:
        d = ImageDraw.Draw(img, "RGBA")
        cx, cy = 760, CARD_Y[0] + CARD_H / 2
        a = clamp01(1 + k / 0.2) if k < 0 else 1 - k
        r = 50 if k < 0 else 50 + 70 * k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, int(90 * a)), outline=(255, 255, 255, int(220 * a)), width=6)

# ---------- frames ----------
def frame(t):
    if t < T_BEG:  # HOOK
        bg = PINK if t >= WORD_T[2] and t < WORD_T[3] else VIOLET
        img = gradient(t, bg, VIOLET_D if bg == VIOLET else (200, 40, 120)); sparkles(img, t, 70)
        f_big = font("Bold", 132); f_gz = font("Bold", 210)
        rows = [("they say", 640, f_big, CREAM, [0, 1]), ("Gen Z", 860, f_gz, YELLOW, [2]), ("can’t read", 1080, f_big, CREAM, [3, 4])]
        # draw word by word with slam
        for text, cy, fnt, col, idxs in rows:
            words = text.split(" ") if len(idxs) > 1 else [text]
            d = ImageDraw.Draw(img)
            total = d.textlength(text, font=fnt); x = (W - total) / 2
            for wi, wd in enumerate(words):
                ww = d.textlength(wd, font=fnt)
                t0 = WORD_T[idxs[wi]]
                if t >= t0:
                    s = 1.0 + 0.7 * (1 - ease_out((t - t0) / 0.18))
                    lay = text_layer(wd, fnt, col, stroke=6 if col == YELLOW else 0, stroke_fill=NAVY)
                    put(img, lay, x + ww / 2, cy, scale=s, rot=(-4 if idxs[wi] == 2 else 0), alpha=clamp01((t - t0) / 0.08))
                x += ww + d.textlength(" ", font=fnt)
        sh = impulses(t, WORD_T, 16)
        return camera(img, zoom=1.04 + 0.04 * t / T_BEG, dx=sh, dy=sh * 0.6, rot=sh * 0.08)

    if t < T_BOARD:  # I BEG TO DIFFER
        k = t - T_BEG
        img = gradient(t, YELLOW, (255, 170, 40), 0.6); sparkles(img, t, 90, NAVY)
        f1 = font("Bold", 150)
        put(img, text_layer("I beg to", f1, NAVY), W / 2, 840, scale=pop(t, T_BEG, 0.22), rot=-3)
        put(img, text_layer("differ.", f1, VIOLET, stroke=0), W / 2, 1010, scale=pop(t, T_BEG + 0.18, 0.22), rot=3)
        sh = impulses(t, [T_BEG, T_BEG + 0.18], 22)
        return camera(img, zoom=1.2 - 0.14 * ease_out(k / 0.3), dx=sh, dy=-sh * 0.5, rot=sh * 0.1, bg=YELLOW)

    if t < T_FAIL:  # BOARD
        img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 60)
        draw_board(img, t, picked="A" if t >= TAP + 0.03 else None)
        tap_ripple(img, t)
        if T_BOARD + 0.8 <= t < TAP - 0.8:
            put(img, sticker("easy.", font("Bold", 84)), W / 2, 360, scale=pop(t, T_BOARD + 0.8), rot=wobble(t, T_BOARD + 0.8, 6))
        if t >= TAP - 0.8:
            put(img, sticker("obviously A.", font("Bold", 76)), W / 2, 360, scale=pop(t, TAP - 0.8), rot=wobble(t, TAP - 0.8, 6) + 3)
        sway = 6 * math.sin(t * 1.6)
        sh = impulses(t, [TAP], 10)
        return camera(img, zoom=1.04, dx=sway + sh, dy=sh)

    if t < T_REREAD:  # FAIL
        k = t - T_FAIL
        img = gradient(t, (200, 30, 80), VIOLET_D, 0.9)
        draw_board(img, t, wrong="A", shake_card=clamp01(k / 0.6), entering=False)
        d = ImageDraw.Draw(img, "RGBA")
        flash = max(0.0, 1 - k / 0.25)
        if flash > 0: d.rectangle((0, 0, W, H), fill=(255, 64, 96, int(150 * flash)))
        put(img, sticker("Not quite.", font("Bold", 132), bg=CREAM, fg=RED), W / 2, 730, scale=pop(t, T_FAIL + 0.04, 0.22), rot=wobble(t, T_FAIL, 8))
        sh = impulses([t][0], [T_FAIL], 34, k=6, f=60)
        return camera(img, zoom=1.06, dx=sh, dy=sh * 0.7, rot=sh * 0.12, bg=VIOLET_D)

    if t < T_PUNCH:  # RE-READ
        hs = clamp01((t - HL_S[0]) / (HL_S[1] - HL_S[0])); hb = clamp01((t - HL_B[0]) / (HL_B[1] - HL_B[0]))
        img = gradient(t, VIOLET, VIOLET_D, 0.15); sparkles(img, t, 40)
        draw_board(img, t, wrong="A", right="B" if t >= HL_B[0] else None, hs=hs, hb=hb, entering=False)
        if t < T_BED:
            put(img, text_layer("*reads it again*", font("SemiBold", 70), CREAM), W / 2, 360, scale=pop(t, T_REREAD + 0.05), rot=-2)
        else:
            put(img, sticker("about to = still in bed", font("Bold", 62)), W / 2, 360, scale=pop(t, T_BED), rot=wobble(t, T_BED, 6))
        z = 1.04 + 0.06 * ease_out((t - T_REREAD) / 3.0)
        sh = impulses(t, [T_BED], 12)
        return camera(img, zoom=z, cy=920, dx=sh, dy=sh)

    if t < T_END:  # PUNCHLINE
        img = gradient(t, PINK, VIOLET, 0.7); sparkles(img, t, 120)
        put(img, text_layer("ok.", font("Bold", 190), CREAM), W / 2, 640, scale=pop(t, T_PUNCH, 0.2), rot=-4)
        if t >= T_P1:
            put(img, text_layer("Gen Z can read.", font("Bold", 100), CREAM), W / 2, 850, scale=pop(t, T_P1, 0.22))
        if t >= T_P2:
            lay = Image.new("RGBA", (920, 380), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            rr(ld, (10, 14, 920, 380), 44, fill=(0, 0, 0, 70)); rr(ld, (0, 0, 910, 366), 44, fill=(*YELLOW, 255))
            fb = font("Bold", 96)
            for i, ln in enumerate(["we just can’t", "leave on time."]):
                tw = ld.textlength(ln, font=fb); ld.text(((910 - tw) / 2, 50 + i * 128), ln, font=fb, fill=NAVY)
            put(img, lay, W / 2, 1150, scale=pop(t, T_P2, 0.26), rot=wobble(t, T_P2, 5))
        sh = impulses(t, [T_PUNCH, T_P1, T_P2], 14)
        return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.06, bg=PINK)

    # END CARD
    img = gradient(t, VIOLET, VIOLET_D, 0.3); sparkles(img, t, 140, YELLOW)
    k = t - T_END
    star = ImageFont.truetype(SYM, 110)
    gh = text_layer("Gist Hunt", font("Bold", 120), CREAM); st = text_layer("✦", star, YELLOW)
    combo = Image.new("RGBA", (st.width + gh.width - 20, max(st.height, gh.height)), (0, 0, 0, 0))
    combo.paste(st, (0, (combo.height - st.height) // 2 + 6), st); combo.paste(gh, (st.width - 20, (combo.height - gh.height) // 2), gh)
    put(img, combo, W / 2, 600, scale=pop(t, T_END, 0.25), rot=2 * math.sin(k * 3))
    put(img, text_layer("One free puzzle a day.", font("SemiBold", 60), CREAM), W / 2, 760, scale=pop(t, T_END + 0.12, 0.25))
    pulse = 1 + 0.04 * math.sin(k * 7)
    pill = Image.new("RGBA", (700, 130), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    rr(pd, (0, 0, 700, 130), 65, fill=(*YELLOW, 255))
    fw = font("Bold", 62); tw = pd.textlength("playgisthunt.com", font=fw); pd.text(((700 - tw) / 2, 26), "playgisthunt.com", font=fw, fill=NAVY)
    put(img, pill, W / 2, 920, scale=pop(t, T_END + 0.24, 0.25) * pulse)
    box = Image.new("RGBA", (900, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    rr(bd, (0, 0, 900, 230), 36, fill=(*CREAM, 255))
    fs = font("SemiBold", 52)
    for i, ln in enumerate(["Send this to the friend who’s", "“about to leave.”"]):
        lw = bd.textlength(ln, font=fs); bd.text(((900 - lw) / 2, 42 + i * 76), ln, font=fs, fill=NAVY)
    put(img, box, W / 2, 1210, scale=pop(t, T_END + 0.5, 0.28), rot=wobble(t, T_END + 0.5, 3) + 3)
    sh = impulses(t, [T_END], 10)
    return camera(img, zoom=1.04, dx=sh, dy=sh)

# ---------- audio ----------
def whoosh(dur=0.25, amp=0.25, seed=5):
    w = noise(dur, amp, 3, seed); return lowpass(w * np.sin(np.linspace(0, np.pi, len(w))), 0.12)

def build_audio(path):
    buf = np.zeros(int(SR * T_TOTAL) + SR)
    for i, tw in enumerate(WORD_T):
        add(buf, kick() * (1.3 if i == 2 else 0.9), tw); add(buf, whoosh(0.15, 0.18, i), tw - 0.08)
    add(buf, whoosh(0.35, 0.3, 9), T_BEG - 0.2); add(buf, kick() * 1.5, T_BEG); add(buf, kick() * 1.2, T_BEG + 0.18)
    seg = np.zeros_like(buf); music(seg, T_BOARD, T_FAIL, bpm=112)
    i0 = int(T_BOARD * SR); seg[i0:i0 + int(0.1 * SR)] *= np.linspace(0, 1, int(0.1 * SR)); buf += seg
    for i in range(4): add(buf, whoosh(0.12, 0.12, 20 + i), T_BOARD + 0.07 + i * 0.16)
    add(buf, noise(0.03, 0.4, 160, 3), TAP); add(buf, tone(1800, 0.05, 0.2, 80), TAP)
    n = int(0.32 * SR); tt = np.arange(n) / SR
    f = 300 + 1400 * np.abs(np.sin(2 * np.pi * 3.2 * tt))
    scr = 0.32 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-5 * tt)
    add(buf, lowpass(scr + noise(n / SR, 0.12, 6, 9)[:n], 0.25), T_FAIL); add(buf, kick() * 1.4, T_FAIL)
    add(buf, tone(659.25, 0.3, 0.22, 6), T_FAIL + 0.28); add(buf, tone(523.25, 0.5, 0.22, 4), T_FAIL + 0.5)
    tk, i = T_REREAD + 0.1, 0
    while tk < T_PUNCH - 0.05:
        add(buf, tone(2400 if i % 2 == 0 else 2000, 0.025, 0.10, 120), tk); tk += 0.5; i += 1
    for a, b in (HL_S, HL_B): add(buf, lowpass(noise(b - a, 0.09, 1.5, 11), 0.3), a)
    add(buf, tone(1318.5, 0.35, 0.16, 7), T_BED); add(buf, kick(), T_BED)
    for tp in (T_PUNCH, T_P1, T_P2): add(buf, kick() * 1.1, tp)
    seg2 = np.zeros_like(buf); music(seg2, T_P2, T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.85
    for i, fq in enumerate((523.25, 659.25, 783.99, 1046.5)): add(buf, tone(fq, 0.7, 0.13, 4), T_END + 0.05 + i * 0.06)
    buf = buf[:int(SR * T_TOTAL)]; fo = int(0.2 * SR); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = np.tanh(buf * 1.5) / np.tanh(1.5); buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())

SCENES = [(0.0, T_BEG), (T_BEG, T_BOARD), (T_BOARD, T_FAIL), (T_FAIL, T_REREAD), (T_REREAD, T_PUNCH), (T_PUNCH, T_END), (T_END, T_TOTAL)]

def render_scene(i, a, b, outdir):
    out = os.path.join(outdir, f"s{i}.mp4"); tmp = os.path.join(outdir, f"s{i}.tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for n in range(round(a * FPS), round(b * FPS)): p.stdin.write(frame(n / FPS).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.replace(tmp, out); return out

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if sys.argv[1] == "stills":
        os.makedirs(os.path.join(here, "g2_stills"), exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] or [1.5, 2.2, 4.2, 5.8, 8.6, 10.5, 12.5]
        frame(ts[2]).save(os.path.join(here, "g2_stills", "full.png"))
        ims = [frame(t).resize((300, 533)) for t in ts]; sh = Image.new("RGB", (300 * len(ims), 533))
        for i, im in enumerate(ims): sh.paste(im, (i * 300, 0))
        sh.save(os.path.join(here, "g2_stills", "sheet.png"))
    else:
        outdir = os.path.join(here, "g2_out"); os.makedirs(outdir, exist_ok=True)
        import concurrent.futures as cf
        with cf.ProcessPoolExecutor() as ex:
            files = list(ex.map(render_scene, range(len(SCENES)), [s[0] for s in SCENES], [s[1] for s in SCENES], [outdir] * len(SCENES)))
        with open(os.path.join(outdir, "list.txt"), "w") as f:
            for fn in files: f.write(f"file '{fn}'\n")
        build_audio(os.path.join(outdir, "audio.wav"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"), "-c", "copy",
                        os.path.join(outdir, "video.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "video.mp4"), "-i", os.path.join(outdir, "audio.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(outdir, "gisthunt_genz_fast.mp4")], check=True)
        frame(2.0).save(os.path.join(outdir, "cover.jpg"), quality=92); print("done")
