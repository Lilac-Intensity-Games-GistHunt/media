"""Gist Hunt ad batch 2 (Nov 12): three short, low-text ads for IG Reels + TikTok.
  versus  — "think you're a better reader than your friends?" (Gist Versus, saturated, unhinged)
  comfort — "reading can be hard." (real Settings screens: OpenDyslexic 'Steady' font, text size, Take your time; soft, low-key)
  whosays — "Gen Z can't read? who says." (saturated, unhinged-uplifting)
Usage: python3 batch.py stills <ad> [t ...] | video <ad>
"""
import math, os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, "/home/claude/ad")
from genz2 import (gradient, sparkles, impulses, camera, text_layer, put, sticker, pop, wobble,
                   VIOLET, VIOLET_D, PINK, YELLOW, CREAM, NAVY, RED, MINT)
from render import font, ease_out, ease_back, clamp01, rr, tone, noise, add, kick, music, lowpass, SR, SYM

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
DYS = os.path.join(HERE, "fonts", "opendyslexic-latin-700-normal.otf")
DYS_R = os.path.join(HERE, "fonts", "opendyslexic-latin-400-normal.otf")
def dys(size, bold=True): return ImageFont.truetype(DYS if bold else DYS_R, size)

LILAC = (206, 190, 244); PEACH = (255, 218, 196); BLUSH = (247, 204, 226); DUSK = (120, 96, 190)

def end_card(t, t0, title, sub, send, small=None, bg=(VIOLET, VIOLET_D), spark=YELLOW):
    img = gradient(t, *bg, 0.3); sparkles(img, t, 140, spark)
    k = t - t0
    star = ImageFont.truetype(SYM, 110)
    gh = text_layer(title, font("Bold", 116), CREAM); st = text_layer("✦", star, YELLOW)
    combo = Image.new("RGBA", (st.width + gh.width - 20, max(st.height, gh.height)), (0, 0, 0, 0))
    combo.paste(st, (0, (combo.height - st.height) // 2 + 6), st); combo.paste(gh, (st.width - 20, (combo.height - gh.height) // 2), gh)
    put(img, combo, W / 2, 560, scale=pop(t, t0, 0.25), rot=2 * math.sin(k * 3))
    put(img, text_layer(sub, font("SemiBold", 60), CREAM), W / 2, 720, scale=pop(t, t0 + 0.12, 0.25))
    pill = Image.new("RGBA", (700, 130), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    rr(pd, (0, 0, 700, 130), 65, fill=(*YELLOW, 255))
    fw = font("Bold", 62); tw = pd.textlength("playgisthunt.com", font=fw); pd.text(((700 - tw) / 2, 26), "playgisthunt.com", font=fw, fill=NAVY)
    put(img, pill, W / 2, 880, scale=pop(t, t0 + 0.24, 0.25) * (1 + 0.04 * math.sin(k * 7)))
    lines = send
    box = Image.new("RGBA", (920, 90 + 76 * len(lines)), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    rr(bd, (0, 0, box.width, box.height), 36, fill=(*CREAM, 255))
    fs = font("SemiBold", 52)
    for i, ln in enumerate(lines):
        lw = bd.textlength(ln, font=fs); bd.text(((box.width - lw) / 2, 40 + i * 76), ln, font=fs, fill=NAVY)
    put(img, box, W / 2, 1150, scale=pop(t, t0 + 0.5, 0.28), rot=wobble(t, t0 + 0.5, 3) + 2)
    if small:
        small_lines(img, t, t0, small, 1350)
    sh = impulses(t, [t0], 10)
    return camera(img, zoom=1.04, dx=sh, dy=sh)

def sticker_lines(lines, fnt, bg=YELLOW, fg=NAVY, gap=1.25):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    ws = [d.textlength(l, font=fnt) for l in lines]; lh = int(fnt.size * gap)
    w = int(max(ws)) + 90; h = lh * len(lines) + 60
    lay = Image.new("RGBA", (w + 6, h + 10), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rr(ld, (6, 10, w + 6, h + 10), 30, fill=(0, 0, 0, 70)); rr(ld, (0, 0, w, h), 30, fill=(*bg, 255))
    for i, l in enumerate(lines):
        ld.text(((w - ws[i]) / 2, 26 + i * lh), l, font=fnt, fill=fg)
    return lay

def small_lines(img, t, t0, lines, y):
    for i, l in enumerate(lines):
        put(img, text_layer(l, font("Medium", 38), CREAM), W / 2, y + i * 52, alpha=clamp01((t - t0 - 0.7) / 0.3))

def slam_words(img, t, rows):
    """rows: list of (text, cy, font, colour, t0, rot)"""
    for text, cy, fnt, col, t0, rot in rows:
        if t >= t0:
            s = 1.0 + 0.7 * (1 - ease_out((t - t0) / 0.18))
            put(img, text_layer(text, fnt, col, stroke=6 if col == YELLOW else 0, stroke_fill=NAVY), W / 2, cy,
                scale=s, rot=rot, alpha=clamp01((t - t0) / 0.08))

# =====================================================================================
# AD A: VERSUS
# =====================================================================================
class Versus:
    T_MATCH, T_WIN, T_SURV, T_END, T_TOTAL = 2.6, 7.6, 9.8, 12.0, 15.0
    HOOK = [0.1, 0.55, 1.15]
    TAP_YOU, TAP_SAM = 5.0, 5.6
    def avatar(self, img, cx, cy, label, col, score, flash=0.0):
        d = ImageDraw.Draw(img, "RGBA")
        r = 74
        d.ellipse((cx - r - 6, cy - r - 2, cx + r + 6, cy + r + 10), fill=(0, 0, 0, 60))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col, outline=CREAM, width=8)
        f = font("Bold", 50); tw = d.textlength(label, font=f); d.text((cx - tw / 2, cy - 34), label, font=f, fill=CREAM)
        sc = text_layer(str(score), font("Bold", 64), YELLOW if flash > 0 else CREAM)
        put(img, sc, cx, cy + 128, scale=1 + 0.35 * flash)
    def frame(self, t):
        T = self
        if t < T.T_MATCH:
            img = gradient(t, VIOLET, PINK if t > T.HOOK[2] else VIOLET_D); sparkles(img, t, 70)
            slam_words(img, t, [("think you’re a", 700, font("Bold", 110), CREAM, T.HOOK[0], 0),
                                ("better reader", 870, font("Bold", 140), YELLOW, T.HOOK[1], -3),
                                ("than your friends?", 1050, font("Bold", 94), CREAM, T.HOOK[2], 2)])
            sh = impulses(t, T.HOOK, 16)
            return camera(img, zoom=1.04 + 0.04 * t / T.T_MATCH, dx=sh, dy=sh * 0.6, rot=sh * 0.08)
        if t < T.T_WIN:
            img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 60)
            d = ImageDraw.Draw(img, "RGBA")
            # VS header
            k = ease_back((t - T.T_MATCH) / 0.35)
            you_x = -200 + (300 + 200) * min(1, k); sam_x = W + 200 - (W + 200 - (W - 300)) * min(1, k)
            sam_flash = clamp01(1 - (t - T.TAP_SAM - 0.5) / 0.6) if t > T.TAP_SAM + 0.5 else 0
            self.avatar(img, you_x, 470, "YOU", VIOLET_D, 0, 0)
            self.avatar(img, sam_x, 470, "SAM", (200, 40, 120), 175 if t > T.TAP_SAM + 0.5 else 0, sam_flash)
            put(img, text_layer("VS", font("Bold", 120), YELLOW, stroke=6, stroke_fill=NAVY), W / 2, 470,
                scale=pop(t, T.T_MATCH + 0.2, 0.25), rot=-6 + 3 * math.sin(t * 6))
            # the question card (same for both)
            ck = ease_back((t - T.T_MATCH - 0.4) / 0.4)
            card = Image.new("RGBA", (940, 560), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
            rr(cd, (10, 14, 940, 560), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 930, 546), 40, fill=CREAM)
            ew = font("SemiBold", 30); x = 50
            for c in "SAME QUESTION, BOTH OF YOU":
                cd.text((x, 40), c, font=ew, fill=VIOLET); x += cd.textlength(c, font=ew) + 3
            cd.text((50, 92), "“Mostly done.”", font=font("Bold", 76), fill=NAVY)
            cd.text((50, 200), "Same meaning?", font=font("SemiBold", 46), fill=(110, 100, 140))
            opts = [("A", "Done.", 290), ("B", "Nearly done.", 410)]
            for let, txt, oy in opts:
                you_pick = let == "A" and t >= T.TAP_YOU
                sam_pick = let == "B" and t >= T.TAP_SAM
                if t >= T.TAP_SAM + 0.5:
                    fill = RED if let == "A" else MINT
                elif you_pick or sam_pick:
                    fill = YELLOW
                else:
                    fill = (240, 232, 252)
                rr(cd, (40, oy, 890, oy + 100), 30, fill=fill)
                cd.text((80, oy + 18), f"{let}   {txt}", font=font("SemiBold", 56), fill=CREAM if (fill == RED) else NAVY)
                if you_pick: cd.text((700, oy + 24), "YOU", font=font("Bold", 44), fill=VIOLET_D if fill != RED else CREAM)
                if sam_pick: cd.text((720, oy + 24), "SAM", font=font("Bold", 44), fill=(200, 40, 120))
            put(img, card, W / 2, 1060 + (1 - min(1, ck)) * 600, scale=1)
            if t >= T.T_MATCH + 0.8:
                put(img, sticker("same questions.", font("Bold", 64)), W / 2, 760, scale=pop(t, T.T_MATCH + 0.8), rot=wobble(t, T.T_MATCH + 0.8, 5) - 2)
            if t >= T.TAP_SAM + 0.6:
                put(img, sticker("+175", font("Bold", 80), bg=MINT), W - 230, 300, scale=pop(t, T.TAP_SAM + 0.6), rot=8)
            sh = impulses(t, [T.TAP_YOU, T.TAP_SAM, T.TAP_SAM + 0.5], 12)
            return camera(img, zoom=1.04, dx=6 * math.sin(t * 1.6) + sh, dy=sh)
        if t < T.T_SURV:
            img = gradient(t, PINK, VIOLET, 0.8); sparkles(img, t, 160, YELLOW)
            put(img, text_layer("Sam wins.", font("Bold", 170), YELLOW, stroke=8, stroke_fill=NAVY), W / 2, 760, scale=pop(t, T.T_WIN, 0.22), rot=-4)
            if t >= T.T_WIN + 0.7:
                put(img, sticker("friendship status:", font("Bold", 58), bg=CREAM), W / 2, 1000, scale=pop(t, T.T_WIN + 0.7), rot=wobble(t, T.T_WIN + 0.7, 4))
            if t >= T.T_WIN + 1.2:
                put(img, sticker("under review", font("Bold", 76)), W / 2, 1140, scale=pop(t, T.T_WIN + 1.2), rot=wobble(t, T.T_WIN + 1.2, 6) + 3)
            sh = impulses(t, [T.T_WIN, T.T_WIN + 1.2], 22)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.1, bg=PINK)
        if t < T.T_END:
            img = gradient(t, VIOLET, VIOLET_D, 0.2); sparkles(img, t, 70)
            put(img, text_layer("Friendships have", font("Bold", 96), CREAM), W / 2, 820, scale=pop(t, T.T_SURV, 0.25))
            put(img, text_layer("survived worse.", font("Bold", 96), CREAM), W / 2, 950, scale=pop(t, T.T_SURV + 0.2, 0.25))
            if t >= T.T_SURV + 1.1:
                put(img, sticker("probably.", font("Bold", 70)), W / 2, 1130, scale=pop(t, T.T_SURV + 1.1), rot=wobble(t, T.T_SURV + 1.1, 6) - 3)
            sh = impulses(t, [T.T_SURV + 1.1], 12)
            return camera(img, zoom=1.04 + 0.03 * (t - T.T_SURV) / 2.2, dx=sh, dy=sh)
        return end_card(t, T.T_END, "Gist Versus", "You vs a friend. Same questions.",
                        ["Send this to the friend", "who thinks they’d win."],
                        small=["Plus members start matches.", "Friends they invite play free."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        for i, tw in enumerate(T.HOOK): add(buf, kick() * (1.3 if i == 1 else 0.9), tw); add(buf, whoosh(0.15, 0.18, i), tw - 0.08)
        seg = np.zeros_like(buf); music(seg, T.T_MATCH, T.T_WIN, bpm=112); buf += seg
        add(buf, whoosh(0.3, 0.25, 30), T.T_MATCH); add(buf, kick() * 1.2, T.T_MATCH + 0.2)
        for tt in (T.TAP_YOU, T.TAP_SAM): add(buf, noise(0.03, 0.4, 160, 3), tt); add(buf, tone(1800, 0.05, 0.2, 80), tt)
        add(buf, tone(392, 0.25, 0.2, 8), T.TAP_SAM + 0.5); add(buf, tone(988, 0.3, 0.18, 7), T.TAP_SAM + 0.6)
        fanfare(buf, T.T_WIN); add(buf, kick() * 1.4, T.T_WIN)
        add(buf, tone(220, 0.5, 0.2, 5), T.T_WIN + 1.2); add(buf, tone(207.7, 0.6, 0.2, 4), T.T_WIN + 1.45)  # "uh oh"
        add(buf, tone(1318.5, 0.35, 0.13, 7), T.T_SURV + 1.1)
        seg2 = np.zeros_like(buf); music(seg2, T.T_SURV + 1.1, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.8
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# AD B: COMFORT (reading can be hard) — real Settings screenshots
# =====================================================================================
class Comfort:
    T_LETTERS, T_PHONE, T_ASK, T_END, T_TOTAL = 3.2, 6.4, 12.6, 15.6, 18.5
    SHOT1 = os.path.join(HERE, "shots", "s1_standard.png")
    SHOT2 = os.path.join(HERE, "shots", "s2_steady.png")
    SHOT3 = os.path.join(HERE, "shots", "s5_home_steady.png")
    T_TAP_STEADY = 7.9
    T_HOME = 10.4
    def __init__(self):
        self.shots = [Image.open(p).convert("RGB") for p in (self.SHOT1, self.SHOT2, self.SHOT3)]
    def soft_bg(self, t):
        img = gradient(t, LILAC, PEACH, 0.08); sparkles(img, t, 55, CREAM)
        return img
    SCALE = 0.56
    def phone(self, shot, scale=None):
        scale = scale or self.SCALE
        w, h = int(shot.width * scale), int(shot.height * scale)
        ph = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
        rr(d, (8, 16, w + 40, h + 40), 70, fill=(40, 20, 80, 70))
        rr(d, (0, 0, w + 32, h + 32), 70, fill=NAVY)
        sc = shot.resize((w, h), Image.LANCZOS)
        mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), 56, fill=255)
        ph.paste(sc, (16, 16), mask)
        return ph
    def frame(self, t):
        T = self
        if t < T.T_LETTERS:
            img = self.soft_bg(t)
            words = ["reading", "can", "be", "hard."]
            f = font("SemiBold", 120)
            for i, wd in enumerate(words):
                t0 = 0.3 + i * 0.45
                a = clamp01((t - t0) / 0.5)
                if a > 0:
                    y = [760, 900, 900, 1060][i]; xoff = {1: -110, 2: 120}.get(i, 0)
                    put(img, text_layer(wd, f, NAVY), W / 2 + xoff, y + 20 * (1 - ease_out(a)), alpha=a)
            return camera(img, zoom=1.03 + 0.02 * t / T.T_LETTERS, bg=LILAC)
        if t < T.T_PHONE:
            img = self.soft_bg(t); d = ImageDraw.Draw(img, "RGBA")
            k = t - T.T_LETTERS
            put(img, text_layer("some days the letters", font("SemiBold", 70), NAVY), W / 2, 700, alpha=clamp01(k / 0.4))
            put(img, text_layer("won’t sit still.", font("SemiBold", 70), NAVY), W / 2, 790, alpha=clamp01((k - 0.3) / 0.4))
            # a jittery word that slowly settles near the end of the scene
            word = "bedtime story"
            f = font("Bold", 120)
            settle = clamp01((k - 1.9) / 0.9)
            amp = 16 * (1 - settle)
            x = (W - d.textlength(word, font=f)) / 2; y0 = 1010
            rng = np.random.default_rng(int(t * 12))
            for i, ch in enumerate(word):
                cw = d.textlength(ch, font=f)
                dx, dy, rot = rng.normal(0, amp * 0.5), rng.normal(0, amp * 0.4), rng.normal(0, amp * 0.5)
                put(img, text_layer(ch, f, DUSK), x + cw / 2 + dx, y0 + dy, rot=rot, alpha=clamp01(k / 0.5))
                x += cw
            return camera(img, zoom=1.04, bg=LILAC)
        if t < T.T_ASK:
            img = self.soft_bg(t)
            k = t - T.T_PHONE
            # phone with real screenshots: standard -> Steady -> home in Steady
            if t < T.T_TAP_STEADY: shot = self.shots[0]
            elif t < T.T_HOME: shot = self.shots[1]
            else: shot = self.shots[2]
            ph = self.phone(shot)
            y = 1000 + (1 - ease_out(min(1, k / 0.6))) * 900
            put(img, ph, W / 2, y)
            d = ImageDraw.Draw(img, "RGBA")
            # cross-fade flash on change
            for tc in (T.T_TAP_STEADY, T.T_HOME):
                if 0 <= t - tc < 0.25:
                    d.rectangle((0, 0, W, H), fill=(255, 255, 255, int(120 * (1 - (t - tc) / 0.25))))
            # tap ring on the real "Steady" button (s1 screenshot coords ~ (897, 998) at 1170x1992)
            if T.T_TAP_STEADY - 0.4 < t < T.T_TAP_STEADY + 0.5:
                kk = (t - T.T_TAP_STEADY) / 0.5
                bx = W / 2 - ph.width / 2 + 16 + 897 * self.SCALE
                by = y - ph.height / 2 + 16 + 998 * self.SCALE
                a = clamp01(1 + kk / 0.8) if kk < 0 else 1 - kk
                r = 46 + (50 * kk if kk > 0 else 0)
                d.ellipse((bx - r, by - r, bx + r, by + r), outline=(122, 92, 196, int(255 * a)), width=8, fill=(185, 166, 224, int(90 * a)))
            # captions (few words), in the Steady font once it is on
            cap = None
            if 6.9 <= t < T.T_TAP_STEADY: cap, t0 = ["so we made room."], 6.9
            elif T.T_TAP_STEADY <= t < 9.2: cap, t0 = ["a font made for", "dyslexic readers."], T.T_TAP_STEADY + 0.15
            elif 9.2 <= t < T.T_HOME: cap, t0 = ["bigger text.", "more time."], 9.2
            elif t >= T.T_HOME: cap, t0 = ["the whole game,", "your way."], T.T_HOME + 0.15
            if cap:
                fnt = dys(46) if t >= T.T_TAP_STEADY else font("Bold", 58)
                lay = sticker_lines(cap, fnt, bg=CREAM, fg=NAVY, gap=1.45 if t >= T.T_TAP_STEADY else 1.2)
                put(img, lay, W / 2, 320 if len(cap) == 1 else 300, scale=pop(t, t0, 0.3), rot=-2 + math.sin(t * 2))
            return camera(img, zoom=1.03, bg=LILAC)
        if t < T.T_END:
            img = gradient(t, BLUSH, LILAC, 0.08); sparkles(img, t, 70, CREAM)
            k = t - T.T_ASK
            put(img, text_layer("what else", dys(84), NAVY), W / 2, 760, alpha=clamp01(k / 0.6))
            put(img, text_layer("would help?", dys(84), NAVY), W / 2, 880, alpha=clamp01((k - 0.3) / 0.6))
            if k > 1.2:
                put(img, sticker_lines(["tell us.", "we’re listening."], dys(54), bg=CREAM, gap=1.45), W / 2, 1110, scale=pop(t, T.T_ASK + 1.2, 0.3), rot=-2)
            return camera(img, zoom=1.03 + 0.02 * k / 3, bg=BLUSH)
        return end_card(t, T.T_END, "Gist Hunt", "Play it your way.",
                        ["Comment what would", "make reading easier."],
                        small=["In Settings. Saved on your device.", "No account needed."],
                        bg=(DUSK, (90, 60, 160)), spark=CREAM)
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        # warm pad: slow chords
        chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 329.63), (174.61, 220.0, 293.66), (196.0, 246.94, 293.66)]
        dur = 4.0; t0 = 0.0; i = 0
        while t0 < T.T_TOTAL:
            for fq in chords[i % 4]:
                n = int(SR * (dur + 1.0)); tt = np.arange(n) / SR
                env = np.minimum(1, tt / 1.2) * np.exp(-0.25 * tt)
                add(buf, 0.05 * env * (np.sin(2 * np.pi * fq * tt) + 0.3 * np.sin(2 * np.pi * fq * 2 * tt)), t0)
            t0 += dur; i += 1
        notes = [659.25, 587.33, 523.25, 493.88, 523.25, 587.33]
        for j, tt in enumerate(np.arange(0.3, T.T_TOTAL - 1, 1.1)):
            add(buf, tone(notes[j % len(notes)], 0.9, 0.06, 3), tt)
        for tc in (T.T_TAP_STEADY, T.T_HOME): add(buf, tone(1046.5, 0.6, 0.1, 5), tc); add(buf, tone(1318.5, 0.6, 0.07, 5), tc + 0.08)
        add(buf, noise(0.02, 0.2, 160, 3), T.T_TAP_STEADY - 0.05)
        chime(buf, T.T_END, amp=0.09); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# AD C: WHO SAYS
# =====================================================================================
class WhoSays:
    T_WHO, T_LIST, T_CARD, T_PUNCH, T_END, T_TOTAL = 1.4, 3.0, 8.4, 10.6, 12.8, 15.5
    HOOK = [0.1, 0.5]
    ITEMS = [("the room", True), ("the subtext in “k.”", True), ("a 2am group chat", True), ("terms & conditions", False)]
    def frame(self, t):
        T = self
        if t < T.T_WHO:
            img = gradient(t, VIOLET, VIOLET_D); sparkles(img, t, 70)
            slam_words(img, t, [("Gen Z", 800, font("Bold", 220), YELLOW, T.HOOK[0], -4), ("can’t read?", 1010, font("Bold", 130), CREAM, T.HOOK[1], 2)])
            sh = impulses(t, T.HOOK, 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.08)
        if t < T.T_LIST:
            img = gradient(t, NAVY, (40, 30, 90), 0.1); sparkles(img, t, 40)
            k = t - T.T_WHO
            put(img, text_layer("who says.", font("Bold", 150), CREAM), W / 2, 960, scale=1.0 + 0.06 * k, alpha=clamp01(k / 0.25))
            return camera(img, zoom=1.04 + 0.05 * k / 1.6, bg=NAVY)
        if t < T.T_CARD:
            img = gradient(t, PINK, VIOLET, 0.3); sparkles(img, t, 80)
            put(img, text_layer("we read:", font("Bold", 110), CREAM), W / 2, 420, scale=pop(t, T.T_LIST, 0.22), rot=-2)
            for i, (txt, ok) in enumerate(T.ITEMS):
                t0 = T.T_LIST + 0.6 + i * 1.0
                if t < t0: continue
                y = 640 + i * 200
                card = Image.new("RGBA", (920, 160), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                rr(cd, (8, 12, 920, 160), 36, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 910, 148), 36, fill=CREAM)
                cd.text((50, 36), txt, font=font("SemiBold", 62), fill=NAVY)
                put(img, card, W / 2, y, scale=pop(t, t0, 0.25), rot=(-1) ** i * 1.5)
                if t >= t0 + 0.35:
                    mark = "✓" if ok else "✗"
                    col = MINT if ok else RED
                    stamp = Image.new("RGBA", (130, 130), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
                    sd.ellipse((0, 0, 128, 128), fill=col); sf = ImageFont.truetype(SYM, 80)
                    mw = sd.textlength(mark, font=sf); sd.text(((128 - mw) / 2, 14), mark, font=sf, fill=CREAM)
                    put(img, stamp, W - 150, y, scale=pop(t, t0 + 0.35, 0.2) * 1.0, rot=-10)
                if not ok and t >= t0 + 0.7:
                    put(img, sticker("ok not those.", font("Bold", 60)), W / 2 + 120, y + 130, scale=pop(t, t0 + 0.7), rot=wobble(t, t0 + 0.7, 6) + 4)
            sh = impulses(t, [T.T_LIST + 0.6 + i * 1.0 + 0.35 for i in range(4)], 9)
            return camera(img, zoom=1.04, dx=sh, dy=sh)
        if t < T.T_PUNCH:
            img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 60)
            k = t - T.T_CARD
            put(img, text_layer("Same meaning?", font("Bold", 84), CREAM), W / 2, 520, scale=pop(t, T.T_CARD, 0.25))
            for i, (lab, txt) in enumerate((("A", "k."), ("B", "okay!!"))):
                t0 = T.T_CARD + 0.3 + i * 0.3
                card = Image.new("RGBA", (860, 220), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                rr(cd, (8, 12, 860, 220), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 850, 206), 40, fill=CREAM)
                cd.text((50, 50), lab, font=font("Bold", 80), fill=VIOLET); cd.text((180, 40), txt, font=font("Bold", 110), fill=NAVY)
                put(img, card, W / 2, 760 + i * 270, scale=pop(t, t0, 0.25), rot=(-1) ** i * 2)
            if t >= T.T_CARD + 1.2:
                put(img, sticker("not even close.", font("Bold", 80), bg=YELLOW), W / 2, 1320, scale=pop(t, T.T_CARD + 1.2), rot=wobble(t, T.T_CARD + 1.2, 6) - 3)
            sh = impulses(t, [T.T_CARD + 1.2], 18)
            return camera(img, zoom=1.04, dx=sh, dy=sh, rot=sh * 0.08)
        if t < T.T_END:
            img = gradient(t, PINK, VIOLET, 0.7); sparkles(img, t, 140, YELLOW)
            put(img, text_layer("Gen Z can read.", font("Bold", 110), CREAM), W / 2, 820, scale=pop(t, T.T_PUNCH, 0.22))
            if t >= T.T_PUNCH + 0.8:
                lay = sticker("we read everything.", font("Bold", 84))
                put(img, lay, W / 2, 1010, scale=pop(t, T.T_PUNCH + 0.8, 0.26), rot=wobble(t, T.T_PUNCH + 0.8, 5))
            sh = impulses(t, [T.T_PUNCH, T.T_PUNCH + 0.8], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, bg=PINK)
        return end_card(t, T.T_END, "Gist Hunt", "Read every word.",
                        ["Send this to whoever", "replied “k.”"])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        for i, tw in enumerate(T.HOOK): add(buf, kick() * 1.2, tw); add(buf, whoosh(0.15, 0.18, i), tw - 0.08)
        add(buf, tone(110, 1.4, 0.18, 1.5), T.T_WHO)  # low drone for "who says."
        seg = np.zeros_like(buf); music(seg, T.T_LIST, T.T_PUNCH - 0.1, bpm=112); buf += seg
        for i in range(4):
            t0 = T.T_LIST + 0.6 + i * 1.0
            add(buf, whoosh(0.12, 0.15, 40 + i), t0 - 0.05)
            if i < 3: add(buf, tone(988, 0.2, 0.16, 12), t0 + 0.35); add(buf, tone(1318.5, 0.25, 0.14, 10), t0 + 0.42)
            else: add(buf, tone(196, 0.4, 0.22, 6), t0 + 0.35); add(buf, tone(185, 0.5, 0.22, 5), t0 + 0.55)
        add(buf, kick() * 1.3, T.T_CARD + 1.2); add(buf, noise(0.2, 0.2, 10, 5), T.T_CARD + 1.2)
        fanfare(buf, T.T_PUNCH)
        seg2 = np.zeros_like(buf); music(seg2, T.T_PUNCH + 0.8, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.8
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# AD D: CALL ME.
# =====================================================================================
class CallMe:
    T_PERIOD, T_CARD, T_DOT, T_WIFI, T_END, T_TOTAL = 1.8, 3.8, 7.4, 9.6, 12.0, 14.8
    def frame(self, t):
        T = self
        if t < T.T_PERIOD:
            img = gradient(t, VIOLET, VIOLET_D); sparkles(img, t, 60)
            slam_words(img, t, [("your mom texts:", 720, font("Bold", 92), CREAM, 0.1, 0)])
            if t >= 0.7:
                # phone bubble
                s = pop(t, 0.7, 0.25)
                b = Image.new("RGBA", (720, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
                rr(bd, (8, 12, 720, 230), 60, fill=(0, 0, 0, 70)); rr(bd, (0, 0, 712, 218), 60, fill=CREAM)
                f = font("Bold", 120); tw = bd.textlength("call me.", font=f); bd.text(((712 - tw) / 2, 30), "call me.", font=f, fill=NAVY)
                put(img, b, W / 2, 960, scale=s, rot=-2)
            sh = impulses(t, [0.1, 0.7], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_CARD:
            k = t - T.T_PERIOD
            img = gradient(t, NAVY, (40, 30, 90), 0.1); sparkles(img, t, 30)
            # zoom into the period: keep the dot at a fixed screen point while the line grows
            z = 1.0 + 1.6 * ease_out(k / 1.4)
            f = font("Bold", 200)
            lay = text_layer("call me.", f, CREAM)
            dd = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            l0, t0_, r0, b0 = dd.textbbox((0, 0), "call me.", font=f)
            pl, pt, pr, pb = dd.textbbox((0, 0), "call me", font=f)
            dot_x = 30 + (pr - l0) + ((r0 - l0) - (pr - l0)) / 2      # dot centre inside the layer (pad 30)
            dot_y = 30 + (b0 - t0_) - 22
            tx, ty = W / 2, 980                                          # where the dot should sit on screen
            cx = tx - z * (dot_x - lay.width / 2); cy = ty - z * (dot_y - lay.height / 2)
            put(img, lay, cx, cy, scale=z)
            d = ImageDraw.Draw(img, "RGBA")
            if k > 0.9:
                r = 70 + 14 * math.sin(k * 12)
                d.ellipse((tx - r, ty - r, tx + r, ty + r), outline=(*YELLOW, 255), width=12)
                put(img, sticker("the period.", font("Bold", 80)), W / 2, 1300, scale=pop(t, T.T_PERIOD + 1.0), rot=wobble(t, T.T_PERIOD + 1.0, 6) - 3)
            sh = impulses(t, [T.T_PERIOD + 0.9], 20) + 4 * math.sin(k * 30) * clamp01(k - 0.9)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.5, bg=NAVY)
        if t < T.T_DOT:
            img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 60)
            put(img, text_layer("Same meaning?", font("Bold", 88), CREAM), W / 2, 520, scale=pop(t, T.T_CARD, 0.25))
            for i, (lab, txt) in enumerate((("A", "call me."), ("B", "call me when you can :)"))):
                t0 = T.T_CARD + 0.35 + i * 0.35
                card = Image.new("RGBA", (920, 200), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                rr(cd, (8, 12, 920, 200), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 910, 188), 40, fill=CREAM)
                cd.text((50, 50), lab, font=font("Bold", 74), fill=VIOLET)
                cd.text((150, 48), txt, font=font("Bold", 76 if i == 0 else 60), fill=NAVY)
                put(img, card, W / 2, 770 + i * 250, scale=pop(t, t0, 0.25), rot=(-1) ** i * 2)
            if t >= T.T_CARD + 1.6:
                put(img, sticker("not even close.", font("Bold", 86)), W / 2, 1320, scale=pop(t, T.T_CARD + 1.6), rot=wobble(t, T.T_CARD + 1.6, 6) - 3)
            sh = impulses(t, [T.T_CARD + 1.6], 18)
            return camera(img, zoom=1.04, dx=sh, dy=sh, rot=sh * 0.08)
        if t < T.T_WIFI:
            img = gradient(t, VIOLET, VIOLET_D, 0.2); sparkles(img, t, 70)
            put(img, text_layer("one dot.", font("Bold", 130), CREAM), W / 2, 820, scale=pop(t, T.T_DOT, 0.22))
            if t >= T.T_DOT + 0.7:
                put(img, sticker("whole new meaning.", font("Bold", 80)), W / 2, 1000, scale=pop(t, T.T_DOT + 0.7), rot=wobble(t, T.T_DOT + 0.7, 5) + 2)
            sh = impulses(t, [T.T_DOT, T.T_DOT + 0.7], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh)
        if t < T.T_END:
            img = gradient(t, PINK, VIOLET, 0.6); sparkles(img, t, 140, YELLOW)
            put(img, text_layer("(she just wanted", font("Bold", 92), CREAM), W / 2, 840, scale=pop(t, T.T_WIFI, 0.22))
            put(img, text_layer("the wifi password)", font("Bold", 92), YELLOW, stroke=5, stroke_fill=NAVY), W / 2, 960, scale=pop(t, T.T_WIFI + 0.35, 0.22), rot=-2)
            sh = impulses(t, [T.T_WIFI + 0.35], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh, bg=PINK)
        return end_card(t, T.T_END, "Gist Hunt", "Read every word.", ["Send this to whoever", "texts “call me.”"])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        add(buf, kick(), 0.1); add(buf, whoosh(0.15, 0.18, 1), 0.02)
        add(buf, tone(1567.98, 0.12, 0.2, 20), 0.7); add(buf, tone(2093, 0.15, 0.18, 18), 0.78)  # message ping
        # suspense: low drone + heartbeat
        add(buf, tone(98, 2.0, 0.16, 0.8), T.T_PERIOD)
        for i in range(4):
            tb = T.T_PERIOD + 0.5 + i * 0.42
            add(buf, kick() * 0.8, tb); add(buf, kick() * 0.5, tb + 0.14)
        seg = np.zeros_like(buf); music(seg, T.T_CARD, T.T_WIFI - 0.05, bpm=112); buf += seg
        add(buf, kick() * 1.3, T.T_CARD + 1.6); add(buf, noise(0.2, 0.2, 10, 5), T.T_CARD + 1.6)
        add(buf, tone(1318.5, 0.3, 0.14, 7), T.T_DOT + 0.7)
        # the reveal: record scratch then silly bounce
        n = int(0.3 * SR); tt = np.arange(n) / SR
        f = 300 + 1400 * np.abs(np.sin(2 * np.pi * 3.2 * tt))
        add(buf, lowpass(0.3 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-5 * tt), 0.25), T.T_WIFI - 0.05)
        for i, fq in enumerate((392, 523.25, 392, 659.25)): add(buf, tone(fq, 0.18, 0.15, 10), T.T_WIFI + 0.35 + i * 0.13)
        seg2 = np.zeros_like(buf); music(seg2, T.T_WIFI + 0.9, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.8
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# AD E: STREAK (POV: the Daily resets in 2 minutes)
# =====================================================================================
class Streak:
    T_RUN, T_SAVED, T_TOMORROW, T_END, T_TOTAL = 2.2, 6.6, 9.2, 11.4, 14.2
    QS = [(2.6, "Q1"), (3.8, "Q2 · lightning"), (5.0, "Q3")]
    def clock(self, t):
        # 1:59 at start, races down to 0:04 at T_SAVED
        if t < self.T_RUN: secs = 119 - int(t)
        else: secs = int(117 - (113) * ease_out(clamp01((t - self.T_RUN) / (self.T_SAVED - self.T_RUN))))
        secs = max(4, secs); return f"{secs // 60}:{secs % 60:02d}"
    def streak_chip(self, n, col=YELLOW):
        return sticker_lines([f"streak: {n} days"], font("Bold", 58), bg=col)
    def frame(self, t):
        T = self
        if t < T.T_RUN:
            img = gradient(t, VIOLET_D, VIOLET); sparkles(img, t, 60)
            slam_words(img, t, [("POV:", 600, font("Bold", 110), CREAM, 0.1, -3),
                                ("the Daily resets in", 780, font("Bold", 84), CREAM, 0.5, 0)])
            if t >= 1.0:
                put(img, text_layer(self.clock(t), font("Bold", 260), YELLOW, stroke=8, stroke_fill=NAVY), W / 2, 1040,
                    scale=pop(t, 1.0, 0.2) * (1 + 0.03 * math.sin(t * 20)))
            sh = impulses(t, [0.1, 0.5, 1.0], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_SAVED:
            img = gradient(t, PINK, VIOLET, 0.9); sparkles(img, t, 80)
            d = ImageDraw.Draw(img, "RGBA")
            put(img, self.streak_chip(46, CREAM), W / 2 - 200, 330, rot=-3)
            put(img, text_layer(self.clock(t), font("Bold", 110), YELLOW, stroke=6, stroke_fill=NAVY), W / 2 + 260, 330,
                scale=1 + 0.05 * math.sin(t * 25))
            # question cards flying in, each stamped ✓
            for i, (t0, lab) in enumerate(T.QS):
                if t < t0: continue
                y = 660 + i * 260
                card = Image.new("RGBA", (900, 200), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                rr(cd, (8, 12, 900, 200), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 890, 188), 40, fill=CREAM)
                cd.text((50, 54), lab, font=font("Bold", 72), fill=NAVY)
                put(img, card, W / 2 - 30, y, scale=pop(t, t0, 0.2), rot=(-1) ** i * 2.5)
                if t >= t0 + 0.45:
                    stamp = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
                    sd.ellipse((0, 0, 148, 148), fill=MINT); sf = ImageFont.truetype(SYM, 92)
                    mw = sd.textlength("✓", font=sf); sd.text(((148 - mw) / 2, 16), "✓", font=sf, fill=CREAM)
                    put(img, stamp, W - 150, y, scale=pop(t, t0 + 0.45, 0.2), rot=-10)
            if t >= 3.0:
                put(img, sticker("read. every. word.", font("Bold", 64)), W / 2, 1470, scale=pop(t, 3.0), rot=wobble(t, 3.0, 5) + 2)
            # panic speed lines
            for i in range(8):
                yy = 250 + i * 200 + int((t * 1400) % 200)
                d.line((24, yy, 24, yy + 100), fill=(*CREAM, 120), width=7); d.line((W - 24, yy + 80, W - 24, yy + 180), fill=(*CREAM, 120), width=7)
            sh = impulses(t, [q[0] + 0.45 for q in T.QS], 12) + 3 * math.sin(t * 40)
            return camera(img, zoom=1.05, dx=sh, dy=sh * 0.7, rot=sh * 0.05)
        if t < T.T_TOMORROW:
            img = gradient(t, YELLOW, (255, 170, 40), 0.6); sparkles(img, t, 160, VIOLET)
            put(img, text_layer("0:04", font("Bold", 90), NAVY), W / 2, 480, alpha=0.6)
            put(img, sticker_lines(["streak: 47 days"], font("Bold", 110), bg=CREAM), W / 2, 820, scale=pop(t, T.T_SAVED, 0.25), rot=-3)
            if t >= T.T_SAVED + 0.8:
                put(img, text_layer("phew.", font("Bold", 150), VIOLET_D), W / 2, 1100, scale=pop(t, T.T_SAVED + 0.8, 0.22), rot=3)
            # confetti
            d = ImageDraw.Draw(img, "RGBA"); rng = np.random.default_rng(7)
            for j in range(70):
                x0 = rng.uniform(0, W); v = rng.uniform(500, 1100); ph = rng.uniform(0, 6)
                y = -50 + (t - T.T_SAVED) * v - rng.uniform(0, 300)
                if 0 < y < H:
                    c = [VIOLET, PINK, MINT, CREAM, RED][j % 5]; x = x0 + 30 * math.sin(t * 5 + ph)
                    d.rectangle((x, y, x + 16, y + 28), fill=c)
            sh = impulses(t, [T.T_SAVED, T.T_SAVED + 0.8], 20)
            return camera(img, zoom=1.04, dx=sh, dy=sh, bg=YELLOW)
        if t < T.T_END:
            img = gradient(t, VIOLET, VIOLET_D, 0.2); sparkles(img, t, 80)
            put(img, text_layer("same time", font("Bold", 120), CREAM), W / 2, 840, scale=pop(t, T.T_TOMORROW, 0.25))
            put(img, text_layer("tomorrow?", font("Bold", 120), YELLOW, stroke=6, stroke_fill=NAVY), W / 2, 990, scale=pop(t, T.T_TOMORROW + 0.3, 0.25), rot=-2)
            sh = impulses(t, [T.T_TOMORROW + 0.3], 12)
            return camera(img, zoom=1.04, dx=sh, dy=sh)
        return end_card(t, T.T_END, "Gist Hunt", "One free puzzle a day.", ["Send this to", "your streak buddy."],
                        small=["Same puzzle for everyone."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        for tw in (0.1, 0.5, 1.0): add(buf, kick() * 1.1, tw); add(buf, whoosh(0.15, 0.18, 2), tw - 0.08)
        tk = 1.0
        while tk < T.T_SAVED:   # clock ticks speeding up
            add(buf, tone(2400, 0.03, 0.12, 120), tk); tk += max(0.12, 0.5 - 0.09 * (tk - 1.0))
        seg = np.zeros_like(buf); music(seg, T.T_RUN, T.T_SAVED, bpm=140); buf += seg
        for t0, _ in T.QS: add(buf, whoosh(0.12, 0.15, 50), t0 - 0.05); add(buf, tone(988, 0.15, 0.16, 12), t0 + 0.45); add(buf, tone(1318.5, 0.2, 0.14, 10), t0 + 0.52)
        fanfare(buf, T.T_SAVED); add(buf, kick() * 1.4, T.T_SAVED); add(buf, noise(0.4, 0.12, 6, 8), T.T_SAVED)
        add(buf, tone(196, 0.6, 0.15, 3), T.T_SAVED + 0.8)  # "phew" sigh
        seg2 = np.zeros_like(buf); music(seg2, T.T_TOMORROW, T.T_TOTAL, bpm=104, seed=21); buf += seg2 * 0.75
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# ---------- shared audio bits ----------
def whoosh(dur=0.25, amp=0.25, seed=5):
    w = noise(dur, amp, 3, seed); return lowpass(w * np.sin(np.linspace(0, np.pi, len(w))), 0.12)

def fanfare(buf, t0):
    for i, fq in enumerate((523.25, 659.25, 783.99, 1046.5)): add(buf, tone(fq, 0.5, 0.15, 5), t0 + i * 0.07)

def chime(buf, t0, amp=0.13):
    for i, fq in enumerate((523.25, 659.25, 783.99, 1046.5)): add(buf, tone(fq, 0.7, amp, 4), t0 + 0.05 + i * 0.06)

def finish(buf, total, path):
    buf = buf[:int(SR * total)]; fo = int(0.3 * SR); buf[-fo:] *= np.linspace(1, 0, fo)
    buf = np.tanh(buf * 1.5) / np.tanh(1.5); buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.89
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes())

ADS = {"versus": Versus, "comfort": Comfort, "whosays": WhoSays, "callme": CallMe, "streak": Streak}
_AD = None
def _get(name):
    global _AD
    if _AD is None or _AD.__class__ is not ADS[name]: _AD = ADS[name]()
    return _AD

def render_scene(args):
    name, i, a, b, outdir = args
    ad = _get(name)
    out = os.path.join(outdir, f"s{i}.mp4"); tmp = os.path.join(outdir, f"s{i}.tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for n in range(round(a * FPS), round(b * FPS)): p.stdin.write(ad.frame(n / FPS).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.replace(tmp, out); return out

if __name__ == "__main__":
    mode, name = sys.argv[1], sys.argv[2]
    ad = _get(name)
    if mode == "stills":
        ts = [float(x) for x in sys.argv[3:]]
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        ims = [ad.frame(t).resize((270, 480)) for t in ts]; sh = Image.new("RGB", (270 * len(ims), 480))
        for i, im in enumerate(ims): sh.paste(im, (i * 270, 0))
        sh.save(os.path.join(HERE, "stills", f"{name}_sheet.png"))
        ad.frame(ts[len(ts) // 2]).save(os.path.join(HERE, "stills", f"{name}_full.png"))
    else:
        outdir = os.path.join(HERE, "out", name); os.makedirs(outdir, exist_ok=True)
        total = ad.T_TOTAL; edges = [x * total / 8 for x in range(9)]  # 8 equal chunks, rendered in parallel
        import concurrent.futures as cf
        with cf.ProcessPoolExecutor() as ex:
            files = list(ex.map(render_scene, [(name, i, edges[i], edges[i + 1], outdir) for i in range(8)]))
        with open(os.path.join(outdir, "list.txt"), "w") as f:
            for fn in files: f.write(f"file '{fn}'\n")
        ad.audio(os.path.join(outdir, "audio.wav"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"), "-c", "copy",
                        os.path.join(outdir, "video.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "video.mp4"), "-i", os.path.join(outdir, "audio.wav"),
                        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac",
                        "-b:a", "192k", "-shortest", "-movflags", "+faststart", os.path.join(outdir, f"gisthunt_{name}.mp4")], check=True)
        ad.frame(1.9 if name != "comfort" else 2.8).convert("RGB").save(os.path.join(outdir, "cover.jpg"), quality=92)
        print("done", name)
