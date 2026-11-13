"""Gist Hunt ad batch 3 (Nov 12): multiplayer — the challenge, the bragging rights, the conversation.
  thetext   — a friend texts "got 3/3 on today's Gist. beat it?" → "bet." → 3/3 → "rematch."
  yourmove  — Sam played at 7:02 am. You've been thinking about it all day. Lunch: 3/3. "your move, Sam."
  groupchat — 7:01 pm, the Daily drops, the group chat erupts.
  rematch   — sequel to batch 2's "Sam wins.": you send a rematch in Gist Versus and win.
  house     — "who's the better reader in your house?" two phones, one question, one of you is wrong.
All questions are made up and labelled EXAMPLE. Same look and helpers as batch 2. Original synthesised audio, no AI art.
Usage: python3 batch3.py stills <ad> [t ...] | video <ad>
"""
import math, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
B2 = os.path.join(os.path.dirname(HERE), "batch2")
sys.path.insert(0, B2)
from genz2 import (gradient, sparkles, impulses, camera, text_layer, put, sticker, pop, wobble,
                   VIOLET, VIOLET_D, PINK, YELLOW, CREAM, NAVY, RED, MINT)
from render import font, ease_out, ease_back, clamp01, rr, tone, noise, add, kick, music, lowpass, SR, SYM
from batch import end_card, sticker_lines, slam_words, whoosh, fanfare, chime, finish

W, H, FPS = 1080, 1920, 30
SAMC = (200, 40, 120)
PAPER = (250, 246, 255)
GREY = (232, 226, 244)
MUTE = (120, 112, 150)

# ------------------------------------------------------------------ text helpers
_D = ImageDraw.Draw(Image.new("RGB", (1, 1)))
def wrap(text, fnt, maxw):
    lines, cur = [], ""
    for wd in text.split(" "):
        test = (cur + " " + wd).strip()
        if _D.textlength(test, font=fnt) > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = test
    lines.append(cur)
    return lines

def bubble(text, out, fnt=None, name=None, maxw=640, typing=None, card=None):
    """Chat bubble layer. out=True → right/violet. typing=phase → animated dots. card=(title, line) → a result chip."""
    fnt = fnt or font("SemiBold", 60)
    lh = int(fnt.size * 1.3)
    if typing is not None:
        lines, tw = [], 150
    elif card:
        lines, tw = [], 520
    else:
        lines = wrap(text, fnt, maxw); tw = max(_D.textlength(l, font=fnt) for l in lines)
    bw = int(tw + 70)
    bh = (len(lines) * lh + 44) if lines else (110 if typing is not None else 200)
    top = 54 if name else 0
    lay = Image.new("RGBA", (bw + 8, bh + top + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if name:
        d.text((14, 0), name, font=font("SemiBold", 38), fill=MUTE)
    fill = VIOLET if out else CREAM
    fg = CREAM if out else NAVY
    rr(d, (6, top + 8, bw + 6, top + bh + 8), 40, fill=(0, 0, 0, 40))
    rr(d, (0, top, bw, top + bh), 40, fill=(*fill, 255))
    if typing is not None:
        for i in range(3):
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(typing * 9 - i * 1.1))
            cx = 45 + i * 32; cy = top + bh / 2
            d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=(*(CREAM if out else MUTE), int(255 * a)))
    elif card:
        rr(d, (22, top + 20, bw - 22, top + bh - 20), 28, fill=(*(VIOLET_D if out else (244, 238, 255)), 255))
        d.text((54, top + 38), card[0], font=font("SemiBold", 38), fill=(YELLOW if out else VIOLET))
        d.text((54, top + 86), card[1], font=font("Bold", 70), fill=(CREAM if out else NAVY))
    else:
        for i, l in enumerate(lines):
            d.text((35, top + 20 + i * lh), l, font=fnt, fill=fg)
    return lay

PANEL = (100, 300, 980, 1660)

def chat(img, t, title, msgs, sub=None):
    """msgs: (t_in, out, text, name, kind)  kind: None | 'typing' (until next msg) | ('card', title, line)."""
    d = ImageDraw.Draw(img, "RGBA")
    x0, y0, x1, y1 = PANEL
    rr(d, (x0 + 10, y0 + 16, x1 + 10, y1 + 16), 64, fill=(0, 0, 0, 70))
    rr(d, (x0, y0, x1, y1), 64, fill=PAPER)
    rr(d, (x0, y0, x1, y0 + 150), 64, fill=NAVY); d.rectangle((x0, y0 + 90, x1, y0 + 150), fill=NAVY)
    ft = font("Bold", 46); tw = d.textlength(title, font=ft); d.text(((x0 + x1 - tw) / 2, y0 + 32 + (0 if sub else 18)), title, font=ft, fill=CREAM)
    if sub:
        fs = font("Medium", 30); sw = d.textlength(sub, font=fs); d.text(((x0 + x1 - sw) / 2, y0 + 92), sub, font=fs, fill=(200, 190, 230))
    shown = []
    for i, m in enumerate(msgs):
        t_in, out, text, name, kind = (list(m) + [None, None])[:5]
        if t < t_in: break
        if kind == "typing":
            nxt = msgs[i + 1][0] if i + 1 < len(msgs) else 1e9
            if t >= nxt: continue
            lay = bubble("", out, typing=t)
        elif isinstance(kind, tuple):
            lay = bubble("", out, name=name, card=kind[1:])
        else:
            lay = bubble(text, out, name=name)
        shown.append((t_in, out, lay))
    gap = 30; total = sum(l.height + gap for _, _, l in shown)
    cw, chh = x1 - x0, (y1 - 30) - (y0 + 150)
    content = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    y = 30 - max(0, total + 30 - chh)
    for t_in, out, lay in shown:
        s = pop(t, t_in, 0.22)
        cx = (cw - 36 - lay.width / 2) if out else (36 + lay.width / 2)
        if y + lay.height > -20:
            put(content, lay, cx, y + lay.height / 2, scale=max(0.02, s))
        y += lay.height + gap
    img.paste(content, (x0, y0 + 150), content)

def q_montage(img, t, qs, header=None, y0=660):
    if header:
        put(img, sticker(header, font("Bold", 60), bg=CREAM), W / 2, 420, rot=-2)
    for i, (t0, lab) in enumerate(qs):
        if t < t0: continue
        y = y0 + i * 250
        card = Image.new("RGBA", (900, 200), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        rr(cd, (8, 12, 900, 200), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, 890, 188), 40, fill=CREAM)
        cd.text((50, 54), lab, font=font("Bold", 72), fill=NAVY)
        put(img, card, W / 2 - 30, y, scale=pop(t, t0, 0.2), rot=(-1) ** i * 2.5)
        if t >= t0 + 0.4:
            stamp = Image.new("RGBA", (150, 150), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
            sd.ellipse((0, 0, 148, 148), fill=MINT); sf = ImageFont.truetype(SYM, 92)
            mw = sd.textlength("✓", font=sf); sd.text(((148 - mw) / 2, 16), "✓", font=sf, fill=CREAM)
            put(img, stamp, W - 150, y, scale=pop(t, t0 + 0.4, 0.2), rot=-10)

def question_card(t, quote, opts, picks, reveal, t_in, w=930, eyebrow="EXAMPLE QUESTION · SAME FOR BOTH"):
    """opts: [(letter, text)], picks: {letter: [(label, colour, t_pick)]}, reveal: (t_reveal, right_letter)."""
    h = 200 + 120 * len(opts) + 40
    card = Image.new("RGBA", (w + 10, h + 14), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    rr(cd, (10, 14, w + 10, h + 14), 40, fill=(0, 0, 0, 60)); rr(cd, (0, 0, w, h), 40, fill=CREAM)
    ew = font("SemiBold", 28); x = 50
    for c in eyebrow:
        cd.text((x, 36), c, font=ew, fill=VIOLET); x += cd.textlength(c, font=ew) + 3
    qf = font("Bold", 64 if _D.textlength(quote, font=font("Bold", 64)) < w - 100 else 52)
    cd.text((50, 82), quote, font=qf, fill=NAVY)
    cd.text((50, 172), "Same meaning?", font=font("SemiBold", 42), fill=(110, 100, 140))
    t_rev, right = reveal
    for i, (let, txt) in enumerate(opts):
        oy = 240 + i * 120
        who = [p for p in picks.get(let, []) if t >= p[2]]
        if t >= t_rev: fill = MINT if let == right else (RED if who else (240, 232, 252))
        elif who: fill = YELLOW
        else: fill = (240, 232, 252)
        rr(cd, (40, oy, w - 40, oy + 100), 30, fill=fill)
        cd.text((70, oy + 24), f"{let}   {txt}", font=font("SemiBold", 42), fill=CREAM if fill == RED else NAVY)
        xx = w - 70
        for lab, col, _ in who:
            lw = cd.textlength(lab, font=font("Bold", 34)); xx -= lw
            cd.text((xx, oy + 30), lab, font=font("Bold", 34), fill=CREAM if fill in (RED,) else col); xx -= 24
    return card

def ping(buf, at, amp=1.0):
    add(buf, tone(1567.98, 0.12, 0.2 * amp, 20), at); add(buf, tone(2093, 0.15, 0.18 * amp, 18), at + 0.08)

def sent(buf, at):
    add(buf, whoosh(0.12, 0.16, 9), at - 0.04); add(buf, tone(1174.7, 0.1, 0.14, 25), at)

def typing_ticks(buf, a, b, seed=3):
    tt = a; i = 0
    while tt < b:
        add(buf, noise(0.015, 0.12, 220, seed + i), tt); tt += 0.11 + 0.05 * (i % 3); i += 1

def checks(buf, qs):
    for t0, _ in qs:
        add(buf, whoosh(0.12, 0.15, 50), t0 - 0.05); add(buf, tone(988, 0.15, 0.16, 12), t0 + 0.4); add(buf, tone(1318.5, 0.2, 0.14, 10), t0 + 0.47)

# =====================================================================================
# 1. THE TEXT
# =====================================================================================
class TheText:
    T_CHAT, T_PLAY, T_SCORE, T_REM, T_END, T_TOTAL = 2.8, 5.6, 8.6, 11.0, 12.6, 15.4
    T_NOTE = 0.6
    QS = [(5.9, "Q1"), (6.6, "Q2 · lightning"), (7.3, "Q3")]
    MSG1 = "got 3/3 on today’s Gist. beat it?"
    def frame(self, t):
        T = self
        if t < T.T_CHAT:
            img = gradient(t, NAVY, VIOLET_D, 0.1); sparkles(img, t, 35)
            put(img, text_layer("Monday", font("Medium", 54), (210, 200, 240)), W / 2, 330)
            put(img, text_layer("8:14", font("Bold", 250), CREAM), W / 2, 500)
            if t >= T.T_NOTE:
                k = ease_out((t - T.T_NOTE) / 0.35)
                n = Image.new("RGBA", (920, 280), (0, 0, 0, 0)); nd = ImageDraw.Draw(n)
                rr(nd, (8, 14, 920, 280), 44, fill=(0, 0, 0, 70)); rr(nd, (0, 0, 910, 266), 44, fill=(*CREAM, 245))
                nd.text((44, 30), "MESSAGES", font=font("SemiBold", 30), fill=VIOLET)
                nd.text((790, 30), "now", font=font("Medium", 30), fill=MUTE)
                nd.text((44, 76), "Sam", font=font("Bold", 56), fill=NAVY)
                for i, l in enumerate(wrap(T.MSG1, font("SemiBold", 46), 820)):
                    nd.text((44, 150 + i * 58), l, font=font("SemiBold", 46), fill=NAVY)
                put(img, n, W / 2, 900 + (1 - k) * -500, alpha=clamp01(k * 2))
            if t >= 1.7:
                put(img, sticker("oh it’s on.", font("Bold", 74)), W / 2, 1250, scale=pop(t, 1.7), rot=wobble(t, 1.7, 6))
            sh = impulses(t, [T.T_NOTE + 0.2, 1.7], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, bg=NAVY)
        if t < T.T_PLAY:
            img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 50)
            msgs = [(T.T_CHAT, False, T.MSG1, "Sam"), (T.T_CHAT + 0.7, True, "", None, "typing"), (T.T_CHAT + 1.7, True, "bet.")]
            chat(img, t, "Sam", msgs)
            sh = impulses(t, [T.T_CHAT + 1.7], 20)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_SCORE:
            img = gradient(t, PINK, VIOLET, 0.9); sparkles(img, t, 70)
            q_montage(img, t, T.QS, header="today’s Daily, 8:15 am")
            if t >= 7.9:
                put(img, sticker("read. every. word.", font("Bold", 62)), W / 2, 1500, scale=pop(t, 7.9), rot=wobble(t, 7.9, 5) + 2)
            sh = impulses(t, [q[0] + 0.4 for q in T.QS], 12) + 2 * math.sin(t * 30)
            return camera(img, zoom=1.05, dx=sh, dy=sh * 0.7)
        if t < T.T_REM:
            img = gradient(t, VIOLET, PINK, 0.3); sparkles(img, t, 60)
            msgs = [(T.T_CHAT, False, T.MSG1, "Sam"), (T.T_CHAT + 1.7, True, "bet."),
                    (T.T_SCORE, True, "", None, ("card", "TODAY’S DAILY", "3/3")),
                    (T.T_SCORE + 0.6, True, "your move."),
                    (T.T_SCORE + 1.2, False, "", None, "typing"), (T.T_SCORE + 2.0, False, "rematch.", "Sam")]
            chat(img, t, "Sam", msgs)
            sh = impulses(t, [T.T_SCORE, T.T_SCORE + 2.0], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_END:
            img = gradient(t, PINK, VIOLET, 0.8); sparkles(img, t, 160, YELLOW)
            put(img, text_layer("rematch.", font("Bold", 190), YELLOW, stroke=8, stroke_fill=NAVY), W / 2, 820, scale=pop(t, T.T_REM, 0.22), rot=-4)
            if t >= T.T_REM + 0.6:
                put(img, sticker("same time tomorrow.", font("Bold", 66), bg=CREAM), W / 2, 1060, scale=pop(t, T.T_REM + 0.6), rot=wobble(t, T.T_REM + 0.6, 5) + 3)
            sh = impulses(t, [T.T_REM, T.T_REM + 0.6], 22)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.08, bg=PINK)
        return end_card(t, T.T_END, "Gist Hunt", "Your move.", ["Send this to the friend", "who’ll say “bet.”"],
                        small=["One free puzzle a day.", "Same puzzle for everyone."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        add(buf, tone(98, 2.4, 0.12, 0.8), 0.0)
        ping(buf, T.T_NOTE); add(buf, kick() * 1.1, 1.7); add(buf, whoosh(0.15, 0.18, 2), 1.62)
        typing_ticks(buf, T.T_CHAT + 0.7, T.T_CHAT + 1.6)
        sent(buf, T.T_CHAT + 1.7); add(buf, kick() * 1.3, T.T_CHAT + 1.7)
        seg = np.zeros_like(buf); music(seg, T.T_PLAY, T.T_SCORE, bpm=132); buf += seg
        checks(buf, T.QS)
        sent(buf, T.T_SCORE); fanfare(buf, T.T_SCORE); sent(buf, T.T_SCORE + 0.6)
        typing_ticks(buf, T.T_SCORE + 1.2, T.T_SCORE + 1.9, 7); ping(buf, T.T_SCORE + 2.0)
        add(buf, kick() * 1.4, T.T_REM); add(buf, noise(0.3, 0.15, 8, 4), T.T_REM)
        seg2 = np.zeros_like(buf); music(seg2, T.T_REM, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.8
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# 2. YOUR MOVE (the async slow-burn)
# =====================================================================================
class YourMove:
    T_MEET, T_STILL, T_LUNCH, T_SEND, T_END, T_TOTAL = 2.2, 4.8, 7.2, 10.4, 12.6, 15.4
    QS = [(7.9, "Q1"), (8.6, "Q2 · lightning"), (9.3, "Q3")]
    def frame(self, t):
        T = self
        if t < T.T_MEET:
            img = gradient(t, VIOLET, VIOLET_D); sparkles(img, t, 60)
            slam_words(img, t, [("Sam played", 760, font("Bold", 128), CREAM, 0.1, -2),
                                ("at 7:02 am.", 920, font("Bold", 128), YELLOW, 0.6, 2)])
            if t >= 1.2:
                n = bubble("got 3/3. your turn", False, name="Sam")
                put(img, n, W / 2, 1180, scale=pop(t, 1.2), rot=-2)
            sh = impulses(t, [0.1, 0.6, 1.2], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_STILL:
            img = gradient(t, NAVY, (50, 36, 110), 0.1); sparkles(img, t, 30)
            k = t - T.T_MEET
            cal = Image.new("RGBA", (860, 300), (0, 0, 0, 0)); cd = ImageDraw.Draw(cal)
            rr(cd, (8, 12, 860, 300), 40, fill=(0, 0, 0, 80)); rr(cd, (0, 0, 850, 288), 40, fill=CREAM)
            rr(cd, (0, 0, 24, 288), 12, fill=VIOLET)
            cd.text((60, 40), "9:00 – 10:30 am", font=font("SemiBold", 40), fill=MUTE)
            cd.text((60, 100), "Quarterly planning", font=font("Bold", 64), fill=NAVY)
            cd.text((60, 190), "(it’s been 40 minutes)", font=font("Medium", 40), fill=MUTE)
            put(img, cal, W / 2, 700, scale=pop(t, T.T_MEET, 0.3))
            put(img, text_layer("you’re in a meeting.", font("Bold", 88), CREAM), W / 2, 1000, alpha=clamp01((k - 0.4) / 0.3))
            if k > 1.3:
                put(img, sticker("thinking about it.", font("Bold", 68)), W / 2, 1200, scale=pop(t, T.T_MEET + 1.3), rot=wobble(t, T.T_MEET + 1.3, 5) - 2)
            return camera(img, zoom=1.04 + 0.03 * k / 2.6, bg=NAVY)
        if t < T.T_LUNCH:
            img = gradient(t, VIOLET_D, VIOLET, 0.2); sparkles(img, t, 50)
            k = t - T.T_STILL
            # a clock face spinning forward
            cx, cy, r = W / 2, 760, 230
            d = ImageDraw.Draw(img, "RGBA")
            d.ellipse((cx - r - 8, cy - r, cx + r + 8, cy + r + 16), fill=(0, 0, 0, 60))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=CREAM, outline=NAVY, width=12)
            for i in range(12):
                a = i * math.pi / 6; d.line((cx + 0.82 * r * math.sin(a), cy - 0.82 * r * math.cos(a), cx + 0.92 * r * math.sin(a), cy - 0.92 * r * math.cos(a)), fill=NAVY, width=8)
            hrs = 10.5 + 1.5 * ease_out(k / 2.2)
            am = (hrs % 1) * 2 * math.pi; ah = (hrs % 12) / 12 * 2 * math.pi
            d.line((cx, cy, cx + 0.75 * r * math.sin(am), cy - 0.75 * r * math.cos(am)), fill=VIOLET, width=12)
            d.line((cx, cy, cx + 0.5 * r * math.sin(ah), cy - 0.5 * r * math.cos(ah)), fill=NAVY, width=16)
            put(img, text_layer("still thinking", font("Bold", 96), CREAM), W / 2, 1110, scale=pop(t, T.T_STILL + 0.2, 0.25))
            put(img, text_layer("about it.", font("Bold", 96), YELLOW, stroke=5, stroke_fill=NAVY), W / 2, 1230, scale=pop(t, T.T_STILL + 0.5, 0.25), rot=-2)
            return camera(img, zoom=1.04, dx=3 * math.sin(t * 2), bg=VIOLET_D)
        if t < T.T_SEND:
            img = gradient(t, PINK, VIOLET, 0.9); sparkles(img, t, 70)
            q_montage(img, t, T.QS, header="12:31 pm. lunch.")
            sh = impulses(t, [q[0] + 0.4 for q in T.QS], 12) + 2 * math.sin(t * 30)
            return camera(img, zoom=1.05, dx=sh, dy=sh * 0.7)
        if t < T.T_END:
            img = gradient(t, VIOLET, PINK, 0.3); sparkles(img, t, 80, YELLOW)
            msgs = [(0, False, "got 3/3. your turn", "Sam"), (T.T_SEND, True, "", None, ("card", "TODAY’S DAILY", "3/3")),
                    (T.T_SEND + 0.6, True, "your move, Sam.")]
            chat(img, t, "Sam", msgs, sub="read 12:32 pm")
            sh = impulses(t, [T.T_SEND, T.T_SEND + 0.6], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        return end_card(t, T.T_END, "Gist Hunt", "Same puzzle. Play whenever.", ["Send this to the friend", "who plays at 7 am."],
                        small=["New puzzle every night at 7 pm ET."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        for tw in (0.1, 0.6): add(buf, kick() * 1.1, tw); add(buf, whoosh(0.15, 0.18, 1), tw - 0.08)
        ping(buf, 1.2)
        add(buf, tone(110, 2.6, 0.12, 0.6), T.T_MEET)  # meeting drone
        for i in range(5): add(buf, tone(2400 if i % 2 else 2000, 0.03, 0.1, 120), T.T_MEET + 0.3 + i * 0.5)
        tk = T.T_STILL
        while tk < T.T_LUNCH:  # clock racing
            add(buf, tone(2400, 0.025, 0.1, 140), tk); tk += max(0.07, 0.3 - 0.1 * (tk - T.T_STILL))
        seg = np.zeros_like(buf); music(seg, T.T_LUNCH, T.T_SEND, bpm=132); buf += seg
        checks(buf, T.QS)
        sent(buf, T.T_SEND); fanfare(buf, T.T_SEND); sent(buf, T.T_SEND + 0.6); add(buf, kick() * 1.3, T.T_SEND + 0.6)
        seg2 = np.zeros_like(buf); music(seg2, T.T_SEND + 0.6, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.75
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# 3. GROUP CHAT AT 7:01
# =====================================================================================
class GroupChat:
    T_CHAT, T_TALK, T_END, T_TOTAL = 1.9, 10.6, 12.8, 15.6
    MSGS = [(2.3, False, "2/3. the second one was rude", "Jo"),
            (3.3, False, "1/3. don’t talk to me", "Priya"),
            (4.4, False, "", "Sam", ("card", "TODAY’S DAILY", "3/3")),
            (5.4, False, "HOW", "Jo"),
            (6.2, False, "screenshot or it didn’t happen", "Priya"),
            (7.3, False, "that IS the screenshot", "Sam"),
            (8.3, True, "rematch. same time tomorrow."),
            (9.3, False, "bring snacks", "Jo")]
    def frame(self, t):
        T = self
        if t < T.T_CHAT:
            img = gradient(t, VIOLET, VIOLET_D); sparkles(img, t, 60)
            slam_words(img, t, [("7:01 pm.", 760, font("Bold", 170), YELLOW, 0.1, -3),
                                ("the Daily just dropped.", 960, font("Bold", 80), CREAM, 0.7, 1)])
            sh = impulses(t, [0.1, 0.7], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        if t < T.T_TALK:
            img = gradient(t, PINK, VIOLET, 0.25); sparkles(img, t, 50)
            chat(img, t, "book club (we don’t read)", T.MSGS, sub="Jo, Priya, Sam, you")
            sh = impulses(t, [m[0] for m in T.MSGS], 7)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.5)
        if t < T.T_END:
            img = gradient(t, PINK, VIOLET, 0.7); sparkles(img, t, 140, YELLOW)
            put(img, text_layer("same puzzle.", font("Bold", 120), CREAM), W / 2, 760, scale=pop(t, T.T_TALK, 0.22))
            put(img, text_layer("everyone.", font("Bold", 120), CREAM), W / 2, 900, scale=pop(t, T.T_TALK + 0.3, 0.22))
            if t >= T.T_TALK + 0.9:
                put(img, sticker("the trash talk is free.", font("Bold", 70)), W / 2, 1100, scale=pop(t, T.T_TALK + 0.9), rot=wobble(t, T.T_TALK + 0.9, 5) + 2)
            sh = impulses(t, [T.T_TALK, T.T_TALK + 0.9], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, bg=PINK)
        return end_card(t, T.T_END, "Gist Hunt", "New puzzle at 7 pm ET.", ["Send this to your group", "chat’s worst reader."],
                        small=["Same puzzle for everyone."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        add(buf, kick() * 1.3, 0.1); add(buf, whoosh(0.15, 0.18, 1), 0.02); add(buf, kick(), 0.7)
        seg = np.zeros_like(buf); music(seg, T.T_CHAT, T.T_TALK, bpm=118); buf += seg * 0.8
        for i, m in enumerate(T.MSGS):
            if m[1]: sent(buf, m[0])
            else: ping(buf, m[0], 0.8 + 0.1 * (i % 2))
        add(buf, kick() * 1.2, 5.4); add(buf, noise(0.2, 0.15, 10, 5), 5.4)  # HOW
        add(buf, tone(196, 0.3, 0.14, 6), 7.3); add(buf, tone(261.6, 0.3, 0.14, 6), 7.45)  # deadpan
        fanfare(buf, T.T_TALK); add(buf, kick() * 1.3, T.T_TALK + 0.9)
        seg2 = np.zeros_like(buf); music(seg2, T.T_TALK + 0.9, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.75
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# 4. THE REMATCH (sequel to batch 2 "Sam wins.")
# =====================================================================================
class Rematch:
    T_SENT, T_MATCH, T_WIN, T_RESTORE, T_END, T_TOTAL = 2.0, 3.5, 8.3, 10.0, 12.2, 15.2
    TAP_SAM, TAP_YOU, T_REV = 5.4, 6.1, 6.9
    def avatar(self, img, cx, cy, label, col, score, flash=0.0):
        d = ImageDraw.Draw(img, "RGBA"); r = 74
        d.ellipse((cx - r - 6, cy - r - 2, cx + r + 6, cy + r + 10), fill=(0, 0, 0, 60))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col, outline=CREAM, width=8)
        f = font("Bold", 50); tw = d.textlength(label, font=f); d.text((cx - tw / 2, cy - 34), label, font=f, fill=CREAM)
        put(img, text_layer(str(score), font("Bold", 64), YELLOW if flash > 0 else CREAM), cx, cy + 128, scale=1 + 0.35 * flash)
    def frame(self, t):
        T = self
        if t < T.T_SENT:
            img = gradient(t, NAVY, (50, 36, 110), 0.1); sparkles(img, t, 30)
            put(img, text_layer("previously:", font("SemiBold", 64), (200, 190, 230)), W / 2, 600, alpha=clamp01(t / 0.3))
            put(img, text_layer("Sam wins.", font("Bold", 170), YELLOW, stroke=8, stroke_fill=NAVY), W / 2, 780, scale=pop(t, 0.3, 0.22), rot=-4)
            if t >= 1.0:
                put(img, sticker("friendship status: under review", font("Bold", 50), bg=CREAM), W / 2, 1000, scale=pop(t, 1.0), rot=wobble(t, 1.0, 4))
            return camera(img, zoom=1.04, bg=NAVY)
        if t < T.T_MATCH:
            img = gradient(t, VIOLET, PINK, 0.3); sparkles(img, t, 70)
            slam_words(img, t, [("you sent", 780, font("Bold", 120), CREAM, T.T_SENT, 0),
                                ("a rematch.", 940, font("Bold", 140), YELLOW, T.T_SENT + 0.4, -3)])
            sh = impulses(t, [T.T_SENT, T.T_SENT + 0.4], 18)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.06)
        if t < T.T_WIN:
            img = gradient(t, VIOLET, PINK, 0.25); sparkles(img, t, 60)
            k = ease_back((t - T.T_MATCH) / 0.35)
            you_x = -200 + 500 * min(1, k); sam_x = W + 200 - 500 * min(1, k)
            fl = clamp01(1 - (t - T.T_REV) / 0.6) if t > T.T_REV else 0
            self.avatar(img, you_x, 470, "YOU", VIOLET_D, 175 if t > T.T_REV else 0, fl)
            self.avatar(img, sam_x, 470, "SAM", SAMC, 0, 0)
            put(img, text_layer("VS", font("Bold", 120), YELLOW, stroke=6, stroke_fill=NAVY), W / 2, 470, scale=pop(t, T.T_MATCH + 0.2, 0.25), rot=-6 + 3 * math.sin(t * 6))
            card = question_card(t, "“Almost every seat was taken.”",
                                 [("A", "Every seat was taken."), ("B", "Nearly every seat was taken.")],
                                 {"A": [("SAM", SAMC, T.TAP_SAM)], "B": [("YOU", VIOLET_D, T.TAP_YOU)]}, (T.T_REV, "B"), T.T_MATCH)
            ck = ease_back((t - T.T_MATCH - 0.4) / 0.4)
            put(img, card, W / 2, 1080 + (1 - min(1, ck)) * 700)
            if t >= T.T_MATCH + 0.9 and t < T.T_REV:
                put(img, sticker("same questions.", font("Bold", 60)), W / 2, 750, scale=pop(t, T.T_MATCH + 0.9), rot=wobble(t, T.T_MATCH + 0.9, 5) - 2)
            if t >= T.T_REV + 0.1:
                put(img, sticker("+175", font("Bold", 80), bg=MINT), 230, 300, scale=pop(t, T.T_REV + 0.1), rot=-8)
                put(img, sticker("“almost” isn’t “every.”", font("Bold", 54), bg=CREAM), W / 2, 750, scale=pop(t, T.T_REV + 0.3), rot=2)
            sh = impulses(t, [T.TAP_SAM, T.TAP_YOU, T.T_REV], 12)
            return camera(img, zoom=1.04, dx=6 * math.sin(t * 1.6) + sh, dy=sh)
        if t < T.T_RESTORE:
            img = gradient(t, PINK, VIOLET, 0.8); sparkles(img, t, 160, YELLOW)
            put(img, text_layer("you win.", font("Bold", 190), YELLOW, stroke=8, stroke_fill=NAVY), W / 2, 860, scale=pop(t, T.T_WIN, 0.22), rot=-4)
            sh = impulses(t, [T.T_WIN], 22)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, rot=sh * 0.1, bg=PINK)
        if t < T.T_END:
            img = gradient(t, VIOLET, VIOLET_D, 0.2); sparkles(img, t, 70)
            put(img, sticker("friendship status:", font("Bold", 62), bg=CREAM), W / 2, 760, scale=pop(t, T.T_RESTORE), rot=-2)
            if t >= T.T_RESTORE + 0.5:
                put(img, sticker("restored.", font("Bold", 96), bg=MINT), W / 2, 920, scale=pop(t, T.T_RESTORE + 0.5), rot=wobble(t, T.T_RESTORE + 0.5, 5) + 3)
            if t >= T.T_RESTORE + 1.3:
                put(img, text_layer("(for now)", font("SemiBold", 70), CREAM), W / 2, 1090, alpha=clamp01((t - T.T_RESTORE - 1.3) / 0.3))
            sh = impulses(t, [T.T_RESTORE + 0.5], 14)
            return camera(img, zoom=1.04, dx=sh, dy=sh)
        return end_card(t, T.T_END, "Gist Versus", "You vs a friend. Same questions.",
                        ["Send this to the friend", "who owes you a rematch."],
                        small=["Plus members start matches.", "Friends they invite play free."])
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        add(buf, tone(220, 0.5, 0.15, 5), 0.3); add(buf, tone(207.7, 0.6, 0.15, 4), 0.55)  # "uh oh" callback
        add(buf, tone(1318.5, 0.3, 0.1, 7), 1.0)
        sent(buf, T.T_SENT); add(buf, kick() * 1.1, T.T_SENT); add(buf, kick() * 1.4, T.T_SENT + 0.4)
        seg = np.zeros_like(buf); music(seg, T.T_MATCH, T.T_WIN, bpm=112); buf += seg
        add(buf, whoosh(0.3, 0.25, 30), T.T_MATCH); add(buf, kick() * 1.2, T.T_MATCH + 0.2)
        for tt in (T.TAP_SAM, T.TAP_YOU): add(buf, noise(0.03, 0.4, 160, 3), tt); add(buf, tone(1800, 0.05, 0.2, 80), tt)
        add(buf, tone(988, 0.3, 0.18, 7), T.T_REV); add(buf, tone(1318.5, 0.3, 0.15, 7), T.T_REV + 0.08)
        fanfare(buf, T.T_WIN); add(buf, kick() * 1.4, T.T_WIN); add(buf, noise(0.4, 0.12, 6, 8), T.T_WIN)
        for i, fq in enumerate((523.25, 659.25, 783.99)): add(buf, tone(fq, 0.25, 0.12, 8), T.T_RESTORE + 0.5 + i * 0.08)
        seg2 = np.zeros_like(buf); music(seg2, T.T_RESTORE, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.8
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

# =====================================================================================
# 5. WHO'S THE BETTER READER IN YOUR HOUSE?
# =====================================================================================
class House:
    T_PHONES, T_WRONG, T_REVEAL, T_END, T_TOTAL = 2.4, 6.6, 8.2, 11.4, 14.4
    TAP_L, TAP_R = 4.6, 5.3
    def phone(self, t, label, pick, reveal, flip=0.0):
        pw, ph = 470, 900
        lay = Image.new("RGBA", (pw + 16, ph + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        rr(d, (8, 14, pw + 16, ph + 20), 60, fill=(0, 0, 0, 70)); rr(d, (0, 0, pw, ph), 60, fill=NAVY)
        rr(d, (16, 16, pw - 16, ph - 16), 48, fill=PAPER)
        lw = d.textlength(label, font=font("Bold", 40)); d.text(((pw - lw) / 2, 50), label, font=font("Bold", 40), fill=VIOLET)
        ew = font("SemiBold", 22); x = 44
        for c in "EXAMPLE QUESTION":
            d.text((x, 130), c, font=ew, fill=MUTE); x += d.textlength(c, font=ew) + 2
        for i, l in enumerate(["“I’ll be there", "in five.”"]):
            d.text((44, 172 + i * 62), l, font=font("Bold", 50), fill=NAVY)
        d.text((44, 310), "Same meaning?", font=font("SemiBold", 34), fill=MUTE)
        for i, (let, txt) in enumerate((("A", "I’ll be there soon."), ("B", "I’m already there."))):
            oy = 380 + i * 170
            chosen = pick and t >= pick[1] and pick[0] == let
            if t >= reveal: fill = MINT if let == "A" else (RED if chosen else (240, 232, 252))
            elif chosen: fill = YELLOW
            else: fill = (240, 232, 252)
            rr(d, (36, oy, pw - 36, oy + 140), 30, fill=fill)
            d.text((64, oy + 18), let, font=font("Bold", 46), fill=CREAM if fill == RED else VIOLET)
            for j, l in enumerate(wrap(txt, font("SemiBold", 38), pw - 190)):
                d.text((130, oy + 22 + j * 46), l, font=font("SemiBold", 38), fill=CREAM if fill == RED else NAVY)
        if flip > 0:  # phone turned over: card-flip, then show the back
            if flip >= 0.5:
                back = Image.new("RGBA", lay.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(back)
                rr(bd, (8, 14, pw + 16, ph + 20), 60, fill=(0, 0, 0, 70)); rr(bd, (0, 0, pw, ph), 60, fill=(48, 40, 96))
                rr(bd, (40, 40, 170, 200), 40, fill=NAVY)
                for cx_, cy_ in ((80, 85), (130, 85), (80, 150)):
                    bd.ellipse((cx_ - 22, cy_ - 22, cx_ + 22, cy_ + 22), fill=(20, 18, 40), outline=(90, 80, 140), width=4)
                lay = back
            sx = abs(math.cos(math.pi * flip))
            lay = lay.resize((max(2, int(lay.width * sx)), lay.height), Image.BILINEAR)
        return lay
    def frame(self, t):
        T = self
        if t < T.T_PHONES:
            img = gradient(t, VIOLET, VIOLET_D); sparkles(img, t, 60)
            slam_words(img, t, [("who’s the", 680, font("Bold", 110), CREAM, 0.1, 0),
                                ("better reader", 850, font("Bold", 140), YELLOW, 0.5, -3),
                                ("in your house?", 1030, font("Bold", 104), CREAM, 1.0, 2)])
            sh = impulses(t, [0.1, 0.5, 1.0], 16)
            return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6)
        img = gradient(t, PINK, VIOLET, 0.3); sparkles(img, t, 60)
        k = ease_back((t - T.T_PHONES) / 0.4)
        flip = clamp01((t - T.T_REVEAL - 1.2) / 1.4)
        left = self.phone(t, "YOU", ("A", T.TAP_L), T.T_REVEAL)
        right = self.phone(t, "THEM", ("B", T.TAP_R), T.T_REVEAL, flip)
        put(img, left, 280 - (1 - min(1, k)) * 600, 1000, rot=3)
        put(img, right, 800 + (1 - min(1, k)) * 600, 1000, rot=-3)
        if T.T_WRONG <= t < T.T_REVEAL:
            d = ImageDraw.Draw(img, "RGBA"); d.rectangle((0, 0, W, H), fill=(24, 22, 58, int(110 * clamp01((t - T.T_WRONG) / 0.2))))
            put(img, sticker("one of you is wrong.", font("Bold", 74)), W / 2, 980, scale=pop(t, T.T_WRONG), rot=wobble(t, T.T_WRONG, 5) - 2)
        if t < T.T_WRONG:
            put(img, sticker("same question.", font("Bold", 60), bg=CREAM), W / 2, 400, scale=pop(t, T.T_PHONES + 0.5), rot=-2)
        if t >= T.T_REVEAL + 0.3:
            put(img, sticker("“in five” isn’t “here.”", font("Bold", 56), bg=CREAM), W / 2, 400, scale=pop(t, T.T_REVEAL + 0.3), rot=2)
        if t >= T.T_REVEAL + 2.2:
            put(img, sticker("(it was them)", font("Bold", 64)), W / 2, 1640, scale=pop(t, T.T_REVEAL + 2.2), rot=wobble(t, T.T_REVEAL + 2.2, 5) + 3)
        sh = impulses(t, [T.TAP_L, T.TAP_R, T.T_WRONG, T.T_REVEAL], 12)
        if t >= T.T_END:
            return end_card(t, T.T_END, "Gist Hunt", "Settle it.", ["Send this to whoever’s on", "the other end of the couch."],
                            small=["One free puzzle a day."])
        return camera(img, zoom=1.04, dx=sh, dy=sh * 0.6, bg=PINK)
    def audio(self, path):
        T = self; buf = np.zeros(int(SR * T.T_TOTAL) + SR)
        for i, tw in enumerate((0.1, 0.5, 1.0)): add(buf, kick() * (1.3 if i == 1 else 0.9), tw); add(buf, whoosh(0.15, 0.18, i), tw - 0.08)
        seg = np.zeros_like(buf); music(seg, T.T_PHONES, T.T_WRONG, bpm=104); buf += seg * 0.8
        for tt in (T.TAP_L, T.TAP_R): add(buf, noise(0.03, 0.4, 160, 3), tt); add(buf, tone(1800, 0.05, 0.2, 80), tt)
        add(buf, tone(98, 1.6, 0.16, 0.8), T.T_WRONG)
        for i in range(3): add(buf, kick() * 0.8, T.T_WRONG + 0.3 + i * 0.42); add(buf, kick() * 0.5, T.T_WRONG + 0.44 + i * 0.42)
        add(buf, tone(988, 0.3, 0.16, 7), T.T_REVEAL); add(buf, tone(196, 0.4, 0.18, 6), T.T_REVEAL + 0.15)
        for i, fq in enumerate((392, 349.2, 311.1, 261.6)): add(buf, tone(fq, 0.35, 0.12, 6), T.T_REVEAL + 1.2 + i * 0.3)  # sad trombone-ish
        seg2 = np.zeros_like(buf); music(seg2, T.T_REVEAL + 2.2, T.T_TOTAL, bpm=112, seed=21); buf += seg2 * 0.75
        chime(buf, T.T_END); finish(buf, T.T_TOTAL, path)

ADS = {"thetext": TheText, "yourmove": YourMove, "groupchat": GroupChat, "rematch": Rematch, "house": House}
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

COVER_T = {"thetext": 1.9, "yourmove": 1.6, "groupchat": 6.6, "rematch": 7.6, "house": 7.4}

if __name__ == "__main__":
    mode, name = sys.argv[1], sys.argv[2]
    ad = _get(name)
    if mode == "stills":
        ts = [float(x) for x in sys.argv[3:]]
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        ims = [ad.frame(t).resize((270, 480)) for t in ts]; sh = Image.new("RGB", (270 * len(ims), 480))
        for i, im in enumerate(ims): sh.paste(im, (i * 270, 0))
        sh.save(os.path.join(HERE, "stills", f"{name}_sheet.png"))
    else:
        outdir = os.path.join(HERE, "out", name); os.makedirs(outdir, exist_ok=True)
        total = ad.T_TOTAL; edges = [x * total / 8 for x in range(9)]
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
        ad.frame(COVER_T[name]).convert("RGB").save(os.path.join(outdir, "cover.jpg"), quality=92)
        print("done", name)
