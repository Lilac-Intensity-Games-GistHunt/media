"""Gist Hunt ad v2b (Millennials): one-line story + four short cards, hinge word "almost". Made-up example.
1080x1920, 30 fps, 16 s.  Usage: python3 mill2.py stills [t ...] | video
"""
import os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
import genz_cant_read as R
from genz_cant_read import (W, H, FPS, font, ease_out, ease_back, clamp01, rr, centered, paste_center, band_text, eyebrow,
                    layout, span_boxes, CREAM, CARD, LILAC, LILAC_SOFT, LILAC_DEEP, NAVY, MUTED, ROSE, ROSE_SOFT, BORDER,
                    tone, noise, add, kick, music, lowpass, SR)

T_BEG, T_BOARD, T_FAIL, T_REREAD, T_PUNCH, T_END, T_TOTAL = 1.8, 3.0, 7.0, 8.0, 11.2, 13.8, 16.0
TAP = 5.6
HL_S = (8.35, 8.9)
HL_B = (9.3, 9.9)
T_EQ = 10.15
T_PUNCH2 = 12.6

CHALLENGE = "One of these means the same as the story. The rest quietly don’t."
LABEL = "BRUNCH GROUP CHAT · 7:42 AM"
STORY = "“The avocado is almost ripe.”"
CARDS = [("A", "The avocado is ripe. Toast is go."),
         ("B", "The avocado isn’t ripe yet. Hold the toast."),
         ("C", "The avocado is past it. Toast is cancelled."),
         ("D", "The avocado was ripe at 3 a.m. You missed it.")]

X0, X1 = 80, W - 80
F_EYE = font("SemiBold", 28)
F_CH = font("Bold", 52)
F_LBL = font("SemiBold", 26)
F_ST = font("SemiBold", 54)
F_CD = font("Medium", 44)
F_LET = font("Bold", 36)

def geometry():
    g = {}; y = 395
    g["eye"] = y; y += 50
    g["ch"], h = layout(CHALLENGE, F_CH, X1 - X0, X0, y, 64); y += h + 24
    pad = 30
    g["lbl_y"] = y + pad
    g["st"], h = layout(STORY, F_ST, X1 - X0 - 2 * pad, X0 + pad, y + pad + 44, 70)
    g["panel"] = (X0, y, X1, y + pad + 44 + h + pad - 8); y = g["panel"][3] + 24
    cards = []
    for let, txt in CARDS:
        tx = X0 + 110
        ws, h = layout(txt, F_CD, X1 - tx - 30, tx, y + 22, 58)
        box = (X0, y, X1, y + h + 40); cards.append({"let": let, "w": ws, "box": box}); y = box[3] + 18
    g["cards"] = cards; g["bottom"] = y - 18
    return g

G = geometry()

def hl_boxes(d, words, phrase, k, lh_px, color=(255, 214, 102, 235)):
    for bx0, by, bx1 in span_boxes(words, phrase, 0, 0):
        ww = (bx1 - bx0 + 20) * ease_out(k)
        rr(d, (bx0 - 10, by + 4, bx0 - 10 + ww, by + lh_px), 10, fill=color)

def draw_board(img, picked=None, wrong=None, dim=0.0, hs=0.0, hb=0.0, shake=0.0, right=None):
    d = ImageDraw.Draw(img, "RGBA")
    x = X0
    for c in "QUICK ROUND · GIST HUNT":
        d.text((x, G["eye"]), c, font=F_EYE, fill=LILAC_DEEP); x += d.textlength(c, font=F_EYE) + 4
    for wd, x, y, w in G["ch"]:
        d.text((x, y), wd, font=F_CH, fill=NAVY)
    rr(d, G["panel"], 28, fill=LILAC_SOFT)
    x = X0 + 30
    for c in LABEL:
        d.text((x, G["lbl_y"]), c, font=F_LBL, fill=MUTED); x += d.textlength(c, font=F_LBL) + 3
    if hs > 0: hl_boxes(d, G["st"], ["almost"], hs, 74)
    for wd, x, y, w in G["st"]:
        d.text((x, y), wd, font=F_ST, fill=NAVY)
    for c in G["cards"]:
        x0, y0, x1, y1 = c["box"]
        dx = int(14 * np.sin(shake * 40) * (1 - shake)) if (wrong == c["let"] and shake > 0) else 0
        if wrong == c["let"]: fill, outl, wd_ = ROSE_SOFT, ROSE, 5
        elif right == c["let"]: fill, outl, wd_ = LILAC_SOFT, LILAC_DEEP, 5
        elif picked == c["let"]: fill, outl, wd_ = LILAC_SOFT, LILAC_DEEP, 5
        else: fill, outl, wd_ = CARD, BORDER, 3
        rr(d, (x0 + dx, y0, x1 + dx, y1), 26, fill=fill, outline=outl, width=wd_)
        cx, cy = x0 + 56 + dx, (y0 + y1) / 2
        on = c["let"] in (wrong, right, picked)
        d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=outl if on else LILAC_SOFT)
        lw = d.textlength(c["let"], font=F_LET)
        d.text((cx - lw / 2, cy - 26), c["let"], font=F_LET, fill=CARD if on else LILAC_DEEP)
        if c["let"] == "B" and hb > 0:
            for bx0, by, bx1 in span_boxes(c["w"], ["isn’t", "ripe", "yet"], 0, 0):
                ww = (bx1 - bx0 + 20) * ease_out(hb)
                rr(d, (bx0 - 10 + dx, by + 4, bx0 - 10 + dx + ww, by + 62), 10, fill=(255, 214, 102, 235))
        for wd, x, y, w in c["w"]:
            d.text((x + dx, y), wd, font=F_CD, fill=NAVY)
    if dim > 0:
        d.rectangle((0, 0, W, H), fill=(*CREAM, int(170 * dim)))

def card_center(let):
    for c in G["cards"]:
        if c["let"] == let:
            x0, y0, x1, y1 = c["box"]; return ((x0 + x1) / 2 + 200, (y0 + y1) / 2)

def frame(t):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    if t < T_BEG:
        fnt = font("Bold", 104)
        lines = [["Millennials", "keep"], ["saying", "Gen Z"], ["can’t", "read"]]
        ys = [700, 830, 960]; idx = 0
        for li, ln in enumerate(lines):
            tw = d.textlength(" ".join(ln), font=fnt); x = (W - tw) / 2
            for wd in ln:
                a = clamp01((t - (0.1 + idx * 0.12)) / 0.12)
                if a > 0:
                    col = LILAC_DEEP if wd in ("Millennials", "Gen Z") else NAVY
                    d.text((x, ys[li] + 18 * (1 - a)), wd, font=fnt, fill=(*col, int(255 * a)))
                x += d.textlength(wd + " ", font=fnt); idx += 1
        if t > 1.05:
            d.text((W / 2 - 60, 1150), "…", font=font("Bold", 120), fill=(*MUTED, int(255 * clamp01((t - 1.05) / 0.2))))
        eyebrow(d)
        return img
    if t < T_BOARD:
        k = t - T_BEG
        img = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(img, "RGBA")
        s = 1.25 - 0.25 * ease_out(k / 0.3)
        layer = Image.new("RGBA", (W, 600), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        f1 = font("Bold", 130)
        for i, ln in enumerate(["but can", "they?"]):
            tw = ld.textlength(ln, font=f1)
            ld.text(((W - tw) / 2, 140 + i * 160), ln, font=f1, fill=CREAM if i == 0 else LILAC)
        layer = layer.resize((int(W * s), int(600 * s)))
        img.paste(layer, (int((W - layer.width) / 2), int(960 - layer.height / 2)), layer)
        if k > 0.5:
            rr(d, (W / 2 - 260, 1215, W / 2 - 260 + 520 * ease_out((k - 0.5) / 0.3), 1229), 7, fill=LILAC)
        return img
    if t < T_FAIL:
        draw_board(img, picked="A" if t >= TAP + 0.05 else None)
        d = ImageDraw.Draw(img, "RGBA")
        if t < 4.9:
            paste_center(img, band_text(d, "easy.", T_BOARD + 0.25, t), 300)
        else:
            paste_center(img, band_text(d, "obviously A.", 4.9, t), 300)
        k = (t - TAP) / 0.35
        if -0.25 < k < 1.0:
            cx, cy = card_center("A")
            a = clamp01(1 + k / 0.25) if k < 0 else 1 - k
            r = 46 if k < 0 else 46 + 40 * k
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(31, 36, 64, int(70 * a)), outline=(31, 36, 64, int(160 * a)), width=5)
        return img
    if t < T_REREAD:
        k = t - T_FAIL
        draw_board(img, wrong="A", dim=0.5 * ease_out(k / 0.15), shake=clamp01(k / 0.5))
        d = ImageDraw.Draw(img, "RGBA")
        s = ease_back(k / 0.22)
        if s > 0:
            fq = font("Bold", 120); tw = d.textlength("Not quite.", font=fq)
            layer = Image.new("RGBA", (int(tw + 120), 230), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            rr(ld, (0, 0, layer.width, 230), 46, fill=(*CARD, 255), outline=(*ROSE, 255), width=8)
            ld.text((60, 30), "Not quite.", font=fq, fill=ROSE)
            layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))))
            paste_center(img, layer, (G["panel"][1] + G["panel"][3]) / 2)
        return img
    if t < T_PUNCH:
        hs = clamp01((t - HL_S[0]) / (HL_S[1] - HL_S[0])); hb = clamp01((t - HL_B[0]) / (HL_B[1] - HL_B[0]))
        draw_board(img, wrong="A", hs=hs, hb=hb, right="B" if t >= HL_B[0] else None)
        d = ImageDraw.Draw(img, "RGBA")
        if t < T_EQ:
            paste_center(img, band_text(d, "*reads it again*", T_REREAD + 0.05, t, fnt=font("SemiBold", 64), sticker=False), 300)
        else:
            paste_center(img, band_text(d, "almost = not yet", T_EQ, t, fnt=font("Bold", 72)), 300)
        return img
    if t < T_END:
        k1 = ease_out((t - T_PUNCH) / 0.25)
        centered(d, "ok.", font("Bold", 150), 700, (*NAVY, int(255 * k1)))
        centered(d, "Millennials can read.", font("Bold", 84), 880, (*NAVY, int(255 * k1)), maxw=1000)
        if t >= T_PUNCH2:
            k2 = ease_back((t - T_PUNCH2) / 0.25)
            layer = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            rr(ld, (90, 40, W - 90, 380), 40, fill=(*LILAC, 255))
            fb = font("Bold", 92)
            for i, ln in enumerate(["just not", "avocados."]):
                tw = ld.textlength(ln, font=fb); ld.text(((W - tw) / 2, 80 + i * 120), ln, font=fb, fill=NAVY)
            s = max(0.01, k2)
            layer = layer.resize((int(W * s), max(1, int(420 * s)))).rotate(-2, expand=True)
            paste_center(img, layer, 1190)
        eyebrow(d)
        return img
    return end_card(t)

def end_card(t):
    from PIL import ImageFont
    img = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(img, "RGBA")
    k = ease_out((t - T_END) / 0.3)
    fw = font("Bold", 110); star = ImageFont.truetype(R.SYM, 92)
    tw = d.textlength("Gist Hunt", font=fw); sw = d.textlength("✦", font=star); x = (W - tw - sw - 24) / 2
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
        for i, ln in enumerate(["Send this to the Millennial", "who said it first."]):
            lw = ld.textlength(ln, font=fs); ld.text(((W - lw) / 2, 52 + i * 70), ln, font=fs, fill=NAVY)
        layer = layer.resize((max(1, int(W * k2)), max(1, int(260 * k2))))
        paste_center(img, layer, 1300)
    return img

def build_audio(path):
    buf = np.zeros(int(SR * T_TOTAL) + SR)
    for i in range(6): add(buf, tone(900 + 60 * i, 0.06, 0.18, 60), 0.1 + i * 0.12)
    wh = noise(0.45, 0.35, 4, 7); add(buf, lowpass(wh * np.sin(np.linspace(0, np.pi, len(wh))), 0.08), T_BEG - 0.25)
    add(buf, kick() * 1.4, T_BEG + 0.05)
    seg = np.zeros_like(buf); music(seg, T_BOARD, T_FAIL)
    i0 = int(T_BOARD * SR); seg[i0:i0 + int(0.15 * SR)] *= np.linspace(0, 1, int(0.15 * SR)); buf += seg * 0.9
    add(buf, noise(0.03, 0.35, 160, 3), TAP); add(buf, tone(1800, 0.04, 0.15, 90), TAP)
    n = int(0.32 * SR); tt = np.arange(n) / SR
    f = 300 + 1400 * np.abs(np.sin(2 * np.pi * 3.2 * tt))
    scr = 0.30 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-5 * tt)
    add(buf, lowpass(scr + noise(n / SR, 0.12, 6, 9)[:n], 0.25), T_FAIL)
    add(buf, tone(659.25, 0.35, 0.22, 5), T_FAIL + 0.30); add(buf, tone(523.25, 0.55, 0.22, 4), T_FAIL + 0.55)
    tk, i = T_REREAD + 0.1, 0
    while tk < T_PUNCH - 0.05:
        add(buf, tone(2400 if i % 2 == 0 else 2000, 0.025, 0.10, 120), tk); add(buf, noise(0.02, 0.05, 200, i), tk); tk += 0.5; i += 1
    for a, b in (HL_S, HL_B): add(buf, lowpass(noise(b - a, 0.08, 1.5, 11), 0.3), a)
    add(buf, tone(1318.5, 0.4, 0.14, 7), T_EQ)
    add(buf, tone(880, 0.12, 0.12, 25), T_PUNCH)
    seg2 = np.zeros_like(buf); music(seg2, T_PUNCH2, T_TOTAL, seed=21); buf += seg2 * 0.75
    for i, fq in enumerate((523.25, 659.25, 783.99, 1046.5)): add(buf, tone(fq, 0.8, 0.12, 4), T_END + 0.05 + i * 0.07)
    buf = buf[:int(SR * T_TOTAL)]; fo = int(0.25 * SR); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = np.tanh(buf * 1.4) / np.tanh(1.4); buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.89
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
        os.makedirs(os.path.join(here, "m2_stills"), exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] or [4.5, 6.2, 7.6, 9.6, 10.8]
        frame(ts[0]).save(os.path.join(here, "m2_stills", "full.png"))
        ims = [frame(t).resize((360, 640)) for t in ts]; sh = Image.new("RGB", (360 * len(ims), 640))
        for i, im in enumerate(ims): sh.paste(im, (i * 360, 0))
        sh.save(os.path.join(here, "m2_stills", "sheet.png")); print("bottom", G["bottom"])
    else:
        outdir = os.path.join(here, "m2_out"); os.makedirs(outdir, exist_ok=True)
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
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(outdir, "gisthunt_millennials_cant_read.mp4")], check=True)
        frame(1.7).save(os.path.join(outdir, "cover.jpg"), quality=92); print("done")
