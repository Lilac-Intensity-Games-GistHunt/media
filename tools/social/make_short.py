#!/usr/bin/env python3
"""Make a short "Same meaning?" Reel (8 s) from a small JSON spec: two near-identical lines, a reveal, a call to play.

Built for the pillar posts in CONTENT_PILLARS.md (Same story, different spin / The daily hunt) and the short-hook idea in
GROWTH_READOUT P1. Reuses make_post.py's palette, fonts, art and safe zones (y 250-1570).

Writes into --out: reel.mp4 (1080x1920, 8 s, original synthesised audio), cover.jpg (text inside the 3:4 grid crop).

Spec fields: eyebrow, label (optional, small caps above the lines), question, a, b, tag_a, tag_b, verdict, why,
end1, end2, art, seed.
Usage: python3 -I make_short.py spec.json --out DIR
"""
import argparse, json, math, os, shutil, subprocess, sys, wave, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_post import (font, wrap_balanced, wrap, spaced, ease, W, H, FPS, SAFE_TOP, SAFE_BOTTOM,
                       CREAM, NAVY, LILAC, PLUM, WHITE, LILAC_SOFT, BLUSH)

DUR, T_REVEAL, T_END = 8.0, 3.4, 5.9
MINT = (214, 240, 222)


def line_card(dr, y, letter, text, f, tag=None, ftag=None, state='plain', a=1.0):
    """One sentence on a white card; after the reveal a small tag says what it means. Returns the card height."""
    lines = wrap_balanced(dr, text, f, 760)
    lh = int(f.size * 1.25); h = len(lines) * lh + 70 + (int(ftag.size * 1.9) if tag else 0)
    fill = WHITE if state == 'plain' else (LILAC_SOFT if state == 'a' else (255, 236, 232))
    dr.rounded_rectangle((90, y, 990, y + h), radius=30, fill=fill + (255,), outline=NAVY + (255,), width=3)
    dr.ellipse((120, y + 35, 190, y + 105), fill=NAVY + (255,))
    fl = font('Bold', 40); tw = dr.textlength(letter, font=fl)
    dr.text((155 - tw / 2, y + 44), letter, font=fl, fill=WHITE + (255,))
    yy = y + 35
    for ln in lines:
        dr.text((215, yy), ln, font=f, fill=NAVY + (255,)); yy += lh
    if tag:
        A = int(255 * a); ttw = dr.textlength(tag, font=ftag)
        dr.rounded_rectangle((215, yy + 12, 215 + ttw + 44, yy + 12 + int(ftag.size * 1.6)), radius=int(ftag.size * 0.8),
                             fill=(PLUM if state == 'a' else NAVY) + (A,))
        dr.text((237, yy + 12 + ftag.size * 0.25), tag, font=ftag, fill=WHITE + (A,))
    return h


def pill(dr, text, y, f, fill, ink, a=1.0, pad=36):
    tw = dr.textlength(text, font=f); A = int(255 * a)
    dr.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + f.size * 1.9), radius=int(f.size), fill=fill + (A,))
    dr.text(((W - tw) / 2, y + f.size * 0.38), text, font=f, fill=ink + (A,))


def frame(s, art_small, state, tag_alpha=0.0):
    fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
    fr.alpha_composite(art_small, ((W - art_small.width) // 2, SAFE_TOP - 10))
    y = SAFE_TOP + art_small.height + 10
    spaced(dr, (0, y), s['eyebrow'], font('Medium', 34), PLUM + (255,), 3, W / 2); y += 70
    size = 110
    while dr.textlength(s['question'], font=font('Bold', size)) > 940: size -= 4
    fq = font('Bold', size); tw = dr.textlength(s['question'], font=fq)
    dr.text(((W - tw) / 2, y), s['question'], font=fq, fill=NAVY + (255,)); y += 160
    if s.get('label'):
        spaced(dr, (0, y), s['label'], font('Medium', 28), (120, 110, 140, 255), 3, W / 2); y += 55
    f = font('Bold', 52); ft = font('Medium', 34)
    show = state != 'plain'
    ha = line_card(dr, y, 'A', s['a'], f, s['tag_a'] if show else None, ft, 'a' if show else 'plain', tag_alpha)
    y += ha + 30
    hb = line_card(dr, y, 'B', s['b'], f, s['tag_b'] if show else None, ft, 'b' if show else 'plain', tag_alpha)
    return fr, y + hb + 40


def end_frame(s, art_small):
    fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
    fr.alpha_composite(art_small, ((W - art_small.width) // 2, SAFE_TOP - 10))
    y = SAFE_TOP + art_small.height + 40
    fv = font('Bold', 96); tw = dr.textlength(s['verdict'], font=fv)
    dr.text(((W - tw) / 2, y), s['verdict'], font=fv, fill=NAVY + (255,)); y += 150
    fw = font('Medium', 46)
    lines = wrap_balanced(dr, s['why'], fw, 860); bh = len(lines) * int(46 * 1.4) + 70
    dr.rounded_rectangle((90, y, 990, y + bh), radius=30, fill=WHITE + (255,), outline=NAVY + (255,), width=3)
    yy = y + 35
    for ln in lines:
        lw = dr.textlength(ln, font=fw); dr.text(((W - lw) / 2, yy), ln, font=fw, fill=NAVY + (255,)); yy += int(46 * 1.4)
    y += bh + 50
    fe = font('Bold', 48); el = wrap_balanced(dr, s['end1'], fe, 820); eh = len(el) * int(48 * 1.3) + 60
    dr.rounded_rectangle((110, y, 970, y + eh), radius=34, fill=LILAC + (255,))
    yy = y + 30
    for ln in el:
        lw = dr.textlength(ln, font=fe); dr.text(((W - lw) / 2, yy), ln, font=fe, fill=NAVY + (255,)); yy += int(48 * 1.3)
    y += eh + 40
    pill(dr, s['end2'], y, font('Bold', 40), NAVY, WHITE)
    return fr, y + int(40 * 1.9)


def shift(img, top, bottom, dy):
    """Move the content band [top, bottom] down by dy on a fresh cream canvas (the background is flat)."""
    out = Image.new('RGBA', (W, H), CREAM + (255,))
    out.alpha_composite(img.crop((0, top, W, bottom)), (0, top + dy))
    return out


def centre_dy(top, bottom):
    return max(0, int((SAFE_TOP + SAFE_BOTTOM) / 2 - (top + bottom) / 2))


def music(path, seed):
    sr = 44100; L = int(sr * DUR); tt = np.arange(L) / sr; audio = np.zeros(L)
    audio += sum(np.sin(2 * np.pi * f * tt) for f in [130.81, 196.0, 261.63]) * 0.02 * np.minimum(1, tt / 0.3) * np.minimum(1, (DUR - tt) / 0.3)
    rng = np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 2**32)
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    for k in range(16):
        st = 0.05 + k * 0.5
        if st > DUR - 1: break
        f = scale[rng.integers(len(scale))]; s0 = int(st * sr); e = min(L, s0 + int(1.4 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += (np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn)) * np.exp(-tn * 3.4) * 0.07
    for f in (1046.5, 1318.5, 1568.0):
        s0 = int(T_REVEAL * sr); e = min(L, s0 + int(2 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += np.sin(2 * np.pi * f * tn) * np.exp(-tn * 2.5) * 0.06
    audio *= np.minimum(1, (DUR - tt) / 0.3)
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


def cover(s, art, out):
    img = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(img)
    spaced(dr, (0, 330), s['eyebrow'], font('Medium', 36), PLUM + (255,), 4, W / 2)
    size = 130
    while dr.textlength(s['question'], font=font('Bold', size)) > 940: size -= 4
    fq = font('Bold', size); tw = dr.textlength(s['question'], font=fq); dr.text(((W - tw) / 2, 400), s['question'], font=fq, fill=NAVY + (255,))
    y = 600; f = font('Bold', 54)
    if s.get('label'):
        spaced(dr, (0, y - 10), s['label'], font('Medium', 30), (120, 110, 140, 255), 3, W / 2); y += 45
    for letter, txt in (('A', s['a']), ('B', s['b'])):
        y += line_card(dr, y, letter, txt, f) + 30
    room = 1440 - y
    if room > 200:
        ah = min(room - 40, 520); a2 = art.resize((int(art.width * ah / art.height), ah), Image.LANCZOS)
        img.alpha_composite(a2, ((W - a2.width) // 2, y + (room - ah) // 2))
    img.convert('RGB').save(out, quality=92)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('--out', required=True); a = ap.parse_args()
    s = json.load(open(a.spec)); os.makedirs(a.out, exist_ok=True)
    art = Image.open(os.path.join(HERE, 'art', s['art'] + '.png')).convert('RGBA')
    art_small = art.resize((int(art.width * 250 / art.height), 250), Image.LANCZOS)
    top = SAFE_TOP - 10
    plain, bottom = frame(s, art_small, 'plain')
    revealed, bottom2 = frame(s, art_small, 'revealed', 1.0)
    dy = centre_dy(top, bottom2 + 30)
    if bottom2 + 30 + dy > SAFE_BOTTOM: sys.exit('Lines too long for the safe zone.')
    plain = shift(plain, top, bottom2 + 30, dy); revealed = shift(revealed, top, bottom2 + 30, dy); bottom += dy
    end, eb = end_frame(s, art_small)
    edy = centre_dy(top, eb)
    if eb + edy > SAFE_BOTTOM: sys.exit('End screen too long for the safe zone; shorten end1/why.')
    end = shift(end, top, eb, edy)
    frames = os.path.join(a.out, 'frames'); os.makedirs(frames, exist_ok=True)
    fbar = None
    for i in range(int(FPS * DUR)):
        t = i / FPS
        if t < T_REVEAL:
            fr = plain.copy(); dr = ImageDraw.Draw(fr)
            p = t / T_REVEAL; by = bottom + 10
            dr.rounded_rectangle((290, by, 790, by + 10), radius=5, fill=(232, 226, 245, 255))
            if p > 0.02: dr.rounded_rectangle((290, by, 290 + int(500 * p), by + 10), radius=5, fill=PLUM + (255,))
        elif t < T_END:
            fr = Image.blend(plain, revealed, ease((t - T_REVEAL) / 0.3))
            if t >= T_END - 0.3: fr = Image.blend(fr, end, ease((t - (T_END - 0.3)) / 0.3))
        else:
            fr = end.copy()
            if t >= DUR - 0.35: fr = Image.blend(fr, plain, ease((t - (DUR - 0.35)) / 0.35))
        fr.convert('RGB').save(os.path.join(frames, f'{i:04d}.png'))
    wav = os.path.join(a.out, 'audio.wav'); music(wav, s.get('seed', s['a']))
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%04d.png'),
                    '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    '-b:a', '128k', '-shortest', '-movflags', '+faststart', os.path.join(a.out, 'reel.mp4')], check=True)
    shutil.rmtree(frames, ignore_errors=True); os.remove(wav)
    cover(s, art, os.path.join(a.out, 'cover.jpg'))
    print('ok', a.out)


if __name__ == '__main__':
    main()
