"""L♡iter "Which is it?" — recurring split-opinion segment.
Real Loiter cards (from /api/loiter/deck), drawn in Loiter's own look: bright field, yellow card with a black outline and hard
shadow, Georgia-style bold italic (Gelasio), Arial-style UI (Liberation Sans), white buttons.
Each card → a 10 s vertical video (IG Reels / TikTok) and a 1080x1350 still (Bluesky / LinkedIn / IG feed).
Usage: python3 loiter_ads.py stills <n> [t...] | video <n> | image <n> | all
"""
import math, os, sys, subprocess, wave, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
SERIF = os.path.join(HERE, "fonts", "Gelasio-Italic-VF.ttf")
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

def serif(size):
    f = ImageFont.truetype(SERIF, size); f.set_variation_by_name("Bold Italic"); return f
def sans(size, bold=True): return ImageFont.truetype(SANS_B if bold else SANS, size)

INK = (28, 28, 28); PAPER = (255, 255, 255); PINK = (255, 111, 174); YEL = (255, 210, 31); LAMP = (255, 215, 106)
WALL = (43, 33, 64); MINT = (64, 214, 150); LILAC = (184, 160, 255)

# ---- the week's cards (real Loiter cards; ids from the live deck, 12 Nov 2026) ----
CARDS = [
    dict(id="lc-0db7b9661950dcac6cf4", q="Compliment or insult?", t="You drive like you’re carrying a wedding cake.", l="Insult", r="Compliment", field=PINK),
    dict(id="lc-739d0f9ebd65adf57999", q="Whose side are you on?", t="You held the door. She’s still 40 feet away and now has to jog. You both hate this.", l="The holder", r="The jogger", field=YEL, card=PAPER),
    dict(id="mad-thumbs", q="Are they mad at you?", t="A single thumbs-up, four hours later.", l="Mad", r="Not mad", field=LILAC),
    dict(id="lc-b79c5d91f101d329fa3c", q="Compliment or insult?", t="You have the energy of someone who owns a lot of lamps.", l="Insult", r="Compliment", field=PINK),
    dict(id="yes-pencil", q="Is this a yes?", t="I’ll put it on my calendar, in pencil.", l="That’s a no", r="That’s a yes", field=MINT),
    dict(id="crime-milk", q="Bigger crime?", t=None, l="Putting the empty milk back in the fridge.", r="Leaving one bite so it isn’t technically gone.", ls="Empty milk", rs="One bite", field=YEL, card=PAPER),
    dict(id="threat-fence", q="Friendly or a threat?", t="Lovely fence. Is that where you want it?", l="A threat", r="Friendly", field=LILAC),
]

def ease_out(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_back(x):
    x = max(0.0, min(1.0, x)); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def clamp01(x): return max(0.0, min(1.0, x))

def wrap(d, text, fnt, maxw):
    lines, cur = [], ""
    for w in text.split(" "):
        tst = (cur + " " + w).strip()
        if d.textlength(tst, font=fnt) > maxw and cur: lines.append(cur); cur = w
        else: cur = tst
    lines.append(cur); return lines

def fit_text(d, text, maxw, maxh, start=96, minsize=52, lh=1.12):
    s = start
    while s >= minsize:
        f = serif(s); ls = wrap(d, text, f, maxw)
        if len(ls) * s * lh <= maxh: return f, ls, int(s * lh)
        s -= 4
    f = serif(minsize); return f, wrap(d, text, f, maxw), int(minsize * lh)

def heart(d, cx, cy, s, fill):
    r = s * 0.28
    d.ellipse((cx - s * 0.5, cy - s * 0.42, cx - s * 0.5 + 2 * r, cy - s * 0.42 + 2 * r), fill=fill)
    d.ellipse((cx + s * 0.5 - 2 * r, cy - s * 0.42, cx + s * 0.5, cy - s * 0.42 + 2 * r), fill=fill)
    d.polygon([(cx - s * 0.5 + 2, cy - s * 0.16), (cx + s * 0.5 - 2, cy - s * 0.16), (cx, cy + s * 0.48)], fill=fill)

def wordmark(size=80, col=INK):
    f = serif(size); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    wl = d0.textlength("L", font=f); wi = d0.textlength("iter", font=f); hs = size * 0.62
    w = int(wl + hs + wi + 30); h = int(size * 1.35)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.text((6, 0), "L", font=f, fill=col)
    hx = 6 + wl + hs / 2 + 2; heart(d, hx, size * 0.62, hs, None)
    # outlined heart like the site: draw filled ink then smaller field? keep simple: ink outline via two passes
    heart(d, hx, size * 0.62, hs, col); heart(d, hx, size * 0.63, hs * 0.62, (0, 0, 0, 0))
    d.text((6 + wl + hs + 4, 0), "iter", font=f, fill=col)
    return lay

def put(img, lay, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if lay is None or scale <= 0.01 or alpha <= 0: return
    if scale != 1: lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BILINEAR)
    if rot: lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = lay.getchannel("A").point(lambda v: int(v * alpha)); lay.putalpha(a)
    img.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)

def pill(text, fnt, fill=PAPER, fg=INK, padx=44, h=None, arrow=None, border=6, shadow=12):
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    tw = d0.textlength(text, font=fnt); h = h or int(fnt.size * 2.2)
    w = int(tw + 2 * padx)
    lay = Image.new("RGBA", (w + border, h + shadow + border), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, shadow, w, h + shadow - 2), 34, fill=INK)
    d.rounded_rectangle((0, 0, w, h), 34, fill=fill, outline=INK, width=border)
    d.text(((w - tw) / 2, (h - fnt.size * 1.15) / 2), text, font=fnt, fill=fg)
    return lay

def card_layer(c, w=880, h=880, glow=0.0):
    lay = Image.new("RGBA", (w + 8, h + 26), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 18, w, h + 18), 48, fill=INK)
    d.rounded_rectangle((0, 0, w, h), 48, fill=c.get("card", YEL), outline=INK, width=7)
    ef = sans(34); x = 56
    for ch in c["q"].upper():
        d.text((x, 54), ch, font=ef, fill=INK); x += d.textlength(ch, font=ef) + 4
    heart(d, w - 80, 76, 44, INK); heart(d, w - 80, 77, 28, c.get("card", YEL))
    if c["t"]:
        f, ls, lh = fit_text(d, c["t"], w - 140, h - 220, start=92)
        y0 = 140 + (h - 160 - len(ls) * lh) / 2
        for i, l in enumerate(ls):
            lw = d.textlength(l, font=f); d.text(((w - lw) / 2, y0 + i * lh), l, font=f, fill=INK)
    else:  # "pick" card: two options
        f, la, lh = fit_text(d, c["l"], w - 160, 250, start=70)
        _, lb, _ = fit_text(d, c["r"], w - 160, 250, start=f.size, minsize=f.size)
        y = 190
        for i, l in enumerate(la):
            lw = d.textlength(l, font=f); d.text(((w - lw) / 2, y + i * lh), l, font=f, fill=INK)
        y += len(la) * lh + 30
        vf = sans(46); vw = d.textlength("or", font=vf); d.text(((w - vw) / 2, y), "or", font=vf, fill=(90, 90, 100))
        y += 90
        for i, l in enumerate(lb):
            lw = d.textlength(l, font=f); d.text(((w - lw) / 2, y + i * lh), l, font=f, fill=INK)
    return lay

def short(label):  # button text: pick cards use short A/B labels
    return label if len(label) <= 14 else None

def buttons(img, c, lean, t):
    lab_l = c.get("ls") or short(c["l"]) or "This one"; lab_r = c.get("rs") or short(c["r"]) or "That one"
    f = sans(46)
    for side, lab, cx in (("l", "← " + lab_l, 290), ("r", lab_r + " →", 790)):
        active = (lean < -0.45 and side == "l") or (lean > 0.45 and side == "r")
        p = pill(lab, f, fill=INK if active else PAPER, fg=PAPER if active else INK, h=118, padx=36)
        if p.width > 470: p = p.resize((470, int(p.height * 470 / p.width)))
        put(img, p, cx, 1395, scale=1.06 if active else 1.0)

def background(c, t, w=W, h=H):
    img = Image.new("RGB", (w, h), c["field"]); d = ImageDraw.Draw(img, "RGBA")
    rng = np.random.default_rng(3)
    for j in range(26):
        x = rng.uniform(0, w); y = (rng.uniform(0, h) - t * rng.uniform(15, 45)) % h; r = rng.uniform(6, 16)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 70))
    return img

def topbar(img, t):
    put(img, wordmark(84), 300, 300)
    put(img, pill("WHICH IS IT?", sans(36), fill=INK, fg=PAPER, h=84, padx=30), 760, 300, rot=-3 + 1.5 * math.sin(t * 2))

# ---------- video timeline ----------
T_IN, T_SWAY, T_ASK, T_END, T_TOTAL = 0.0, 0.7, 5.6, 7.4, 10.0

def lean_at(t):
    if t < T_SWAY: return 0.0
    if t < T_ASK:
        k = (t - T_SWAY) / (T_ASK - T_SWAY)
        freq = 0.9 + 1.6 * k  # indecision speeds up
        ph = 2 * math.pi * (0.9 * (t - T_SWAY) + 0.8 * (t - T_SWAY) ** 2 / (T_ASK - T_SWAY))
        return math.sin(ph) * (0.6 + 0.4 * k)
    return math.sin(2 * math.pi * 0.9 * (T_ASK - T_SWAY)) * max(0.0, 1 - (t - T_ASK) / 0.35)

def swing_times():
    """times the lean crosses an extreme (for notes)."""
    ts, prev, prevd = [], 0, 0
    for n in range(int(T_SWAY * 100), int(T_ASK * 100)):
        t = n / 100; v = lean_at(t); dv = v - prev
        if prevd > 0 and dv <= 0 or prevd < 0 and dv >= 0: ts.append(t)
        prev, prevd = v, dv
    return ts

def frame(c, t):
    img = background(c, t)
    topbar(img, t)
    lean = lean_at(t)
    k_in = ease_back((t - T_IN) / 0.55)
    cl = card_layer(c)
    cy = 860 + (1 - min(1, k_in)) * 900
    put(img, cl, W / 2 + lean * 90, cy, rot=-lean * 9)
    buttons(img, c, lean, t)
    if t >= T_SWAY + 0.4 and t < T_ASK:
        put(img, pill("can’t decide.", sans(40), fill=PAPER, h=90, padx=30), 300 + 30 * math.sin(t), 1525, rot=4, alpha=clamp01((t - T_SWAY - 0.4) / 0.3))
    if t >= T_ASK:
        s = ease_back((t - T_ASK) / 0.3)
        ask = pill("which is it?", serif(96), fill=INK, fg=PAPER, h=170, padx=56, shadow=14)
        put(img, ask, W / 2, 440, scale=s, rot=-3)
        if t >= T_ASK + 0.6:
            put(img, pill("argue in the comments ↓", sans(48), fill=LAMP, h=110, padx=40), W / 2, 1525, scale=ease_back((t - T_ASK - 0.6) / 0.3), rot=2)
    if t >= T_END:
        k = ease_out((t - T_END) / 0.4)
        d = ImageDraw.Draw(img, "RGBA"); d.rectangle((0, 0, W, H), fill=(*c["field"], int(150 * k)))
        box = Image.new("RGBA", (900, 470), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((0, 16, 892, 466), 48, fill=INK); bd.rounded_rectangle((0, 0, 892, 450), 48, fill=PAPER, outline=INK, width=7)
        f1 = sans(46, False); l1 = "Vote anonymously on"; bd.text(((892 - bd.textlength(l1, font=f1)) / 2, 56), l1, font=f1, fill=INK)
        wm = wordmark(120); box.paste(wm, (int((892 - wm.width) / 2), 120), wm)
        f2 = sans(40, False); l2 = "We don’t keep which way you answered."; bd.text(((892 - bd.textlength(l2, font=f2)) / 2, 290), l2, font=f2, fill=(90, 90, 100))
        f3 = sans(50); l3 = "playgisthunt.com"; bd.text(((892 - bd.textlength(l3, font=f3)) / 2, 360), l3, font=f3, fill=INK)
        put(img, box, W / 2, 960 + (1 - k) * 80, alpha=k)
    return img

# ---------- still image (1080x1350) ----------
def still(c):
    w, h = 1080, 1350
    img = background(c, 0, w, h)
    put(img, wordmark(78), 290, 110)
    put(img, pill("WHICH IS IT?", sans(34), fill=INK, fg=PAPER, h=80, padx=28), 780, 110, rot=-3)
    cl = card_layer(c, 880, 800)
    put(img, cl, w / 2, 620)
    f = sans(46)
    lab_l = c.get("ls") or short(c["l"]) or "This one"; lab_r = c.get("rs") or short(c["r"]) or "That one"
    put(img, pill("← " + lab_l, f, h=112, padx=34), 290, 1110)
    put(img, pill(lab_r + " →", f, h=112, padx=34), 790, 1110)
    d = ImageDraw.Draw(img)
    l = "Argue below. Vote anonymously on Loiter · playgisthunt.com"; fs = sans(34, False)
    d.text(((w - d.textlength(l, font=fs)) / 2, 1250), l, font=fs, fill=INK)
    return img

# ---------- audio: every swing plays a note (like Loiter) ----------
SR = 44100
def tone(f, dur, amp=0.2, decay=5.0):
    t = np.arange(int(SR * dur)) / SR
    return amp * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.exp(-decay * t) * np.minimum(1, t / 0.005)
def add(buf, s, at):
    i = int(at * SR); j = min(len(buf), i + len(s))
    if i < len(buf): buf[i:j] += s[:j - i]
def build_audio(path, seed):
    buf = np.zeros(int(SR * T_TOTAL) + SR)
    # soft pad
    for t0, ch in ((0, (261.63, 329.63, 392.0)), (2.5, (220.0, 261.63, 329.63)), (5.0, (174.61, 220.0, 261.63)), (7.5, (196.0, 246.94, 293.66))):
        for f in ch:
            n = int(SR * 3.2); tt = np.arange(n) / SR
            add(buf, 0.035 * np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.6) * np.exp(-0.35 * tt), t0)
    add(buf, tone(196, 0.3, 0.25, 9), 0.05)  # card lands
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    rng = np.random.default_rng(seed)
    melody = [scale[i] for i in rng.integers(0, len(scale), 40)]
    for i, ts in enumerate(swing_times()): add(buf, tone(melody[i], 0.45, 0.16, 6), ts)
    for f in (392.0, 493.88, 587.33, 783.99): add(buf, tone(f, 0.9, 0.11, 3), T_ASK)
    for i, f in enumerate((523.25, 659.25, 783.99, 1046.5)): add(buf, tone(f, 0.8, 0.1, 4), T_END + 0.1 + i * 0.07)
    buf = buf[:int(SR * T_TOTAL)]; fo = int(0.3 * SR); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())

def render_chunk(args):
    n, i, a, b, outdir = args; c = CARDS[n]
    out = os.path.join(outdir, f"s{i}.mp4"); tmp = os.path.join(outdir, f"s{i}.tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(round(a * FPS), round(b * FPS)): p.stdin.write(frame(c, f / FPS).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.replace(tmp, out); return out

def video(n):
    outdir = os.path.join(HERE, "out", f"card{n + 1}"); os.makedirs(outdir, exist_ok=True)
    edges = [x * T_TOTAL / 6 for x in range(7)]
    import concurrent.futures as cf
    with cf.ProcessPoolExecutor() as ex:
        files = list(ex.map(render_chunk, [(n, i, edges[i], edges[i + 1], outdir) for i in range(6)]))
    with open(os.path.join(outdir, "list.txt"), "w") as f:
        for fn in files: f.write(f"file '{fn}'\n")
    build_audio(os.path.join(outdir, "audio.wav"), seed=n + 1)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"), "-c", "copy", os.path.join(outdir, "video.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "video.mp4"), "-i", os.path.join(outdir, "audio.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    os.path.join(outdir, f"loiter_which_is_it_{n + 1}.mp4")], check=True)
    frame(CARDS[n], 6.6).convert("RGB").save(os.path.join(outdir, "cover.jpg"), quality=92)
    still(CARDS[n]).convert("RGB").save(os.path.join(outdir, f"loiter_which_is_it_{n + 1}.jpg"), quality=93)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "stills":
        n = int(sys.argv[2]); ts = [float(x) for x in sys.argv[3:]] or [0.3, 1.5, 3.0, 4.6, 6.2, 8.4]
        ims = [frame(CARDS[n], t).resize((270, 480)) for t in ts]
        sh = Image.new("RGB", (270 * len(ims) + 270, 480), "white")
        for i, im in enumerate(ims): sh.paste(im, (i * 270, 0))
        sh.paste(still(CARDS[n]).resize((270, 338)), (270 * len(ims), 0))
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True); sh.save(os.path.join(HERE, "stills", f"card{n + 1}.png"))
    elif mode == "video": video(int(sys.argv[2]))
    elif mode == "all":
        for n in range(len(CARDS)): video(n); print("done", n + 1, flush=True)
