#!/usr/bin/env python3
"""Short playstyle Reels (8-10 s) for every Gist / Headline playstyle, in the make_short.py look.

One spec → reel.mp4 (1080x1920, original synthesised audio) + cover.jpg. Generalises make_short.py from two lines to
2-4 option cards plus an optional context box (clues, a condition, a headline brief).

Spec fields:
  eyebrow, question, label (optional small caps above the cards),
  context (optional): {"title": "MATCHING CONDITION", "lines": ["...", "..."]}
  options: [{"text": "...", "tag": "...", "mark": "right"|"wrong"|"plain"}]   (tag/mark shown after the reveal)
  verdict, why, end1, end2, art, seed
Usage: python3 -I playstyle_short.py spec.json --out DIR      (or a list of specs: --all specs.json --root DIR)
"""
import argparse, json, os, shutil, subprocess, sys, wave, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SOCIAL = os.path.dirname(HERE)
sys.path.insert(0, SOCIAL)
from make_post import (font, wrap_balanced, spaced, ease, W, H, FPS, SAFE_TOP, SAFE_BOTTOM,
                       CREAM, NAVY, LILAC, PLUM, WHITE, LILAC_SOFT)

WRONG = (255, 236, 232)
MUTE = (120, 110, 140)
LETTERS = "ABCD"


def card(dr, y, letter, text, f, ftag, tag=None, state='plain', a=1.0, width=760):
    lines = wrap_balanced(dr, text, f, width)
    lh = int(f.size * 1.25); pad = int(f.size * 0.62)
    h = len(lines) * lh + 2 * pad + (int(ftag.size * 1.9) if tag else 0)
    fill = {'plain': WHITE, 'right': LILAC_SOFT, 'wrong': WRONG, 'dim': (246, 243, 250)}[state]
    dr.rounded_rectangle((90, y, 990, y + h), radius=28, fill=fill + (255,), outline=NAVY + (255,), width=3)
    r = int(f.size * 0.62); cx, cy = 152, y + pad + lh // 2
    dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=NAVY + (255,))
    fl = font('Bold', int(f.size * 0.75)); tw = dr.textlength(letter, font=fl)
    dr.text((cx - tw / 2, cy - fl.size * 0.62), letter, font=fl, fill=WHITE + (255,))
    yy = y + pad
    ink = NAVY if state != 'dim' else (150, 145, 165)
    for ln in lines:
        dr.text((215, yy), ln, font=f, fill=ink + (255,)); yy += lh
    if tag:
        A = int(255 * a); ttw = dr.textlength(tag, font=ftag)
        dr.rounded_rectangle((215, yy + 10, 215 + ttw + 40, yy + 10 + int(ftag.size * 1.6)), radius=int(ftag.size * 0.8),
                             fill=(PLUM if state == 'right' else NAVY) + (A,))
        dr.text((235, yy + 10 + ftag.size * 0.25), tag, font=ftag, fill=WHITE + (A,))
    return h


def context_box(dr, y, ctx, f):
    ft = font('Medium', 28)
    lines = []
    for ln in ctx['lines']:
        lines += [('•' if len(ctx['lines']) > 1 else '', l) for l in wrap_balanced(dr, ln, f, 780)]
    lh = int(f.size * 1.32); h = 70 + len(lines) * lh + 30
    dr.rounded_rectangle((90, y, 990, y + h), radius=28, fill=LILAC + (255,))
    spaced(dr, (130, y + 24), ctx['title'], ft, PLUM + (255,), 3)
    yy = y + 70; prev = None
    for bullet, l in lines:
        x = 130
        if bullet and l is not None:
            dr.text((x, yy), bullet, font=f, fill=NAVY + (255,))
        dr.text((x + (36 if bullet else 0), yy), l, font=f, fill=NAVY + (255,)); yy += lh
    return h


def board(s, art_small, revealed, sizes, tag_alpha=1.0):
    fq_max, f_opt, f_ctx = sizes
    fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
    y = SAFE_TOP - 10
    if art_small is not None:
        fr.alpha_composite(art_small, ((W - art_small.width) // 2, y)); y += art_small.height + 14
    spaced(dr, (0, y), s['eyebrow'], font('Medium', 32), PLUM + (255,), 3, W / 2); y += 60
    size = fq_max
    while dr.textlength(s['question'], font=font('Bold', size)) > 940: size -= 4
    fq = font('Bold', size); tw = dr.textlength(s['question'], font=fq)
    dr.text(((W - tw) / 2, y), s['question'], font=fq, fill=NAVY + (255,)); y += int(size * 1.35)
    if s.get('context'):
        y += context_box(dr, y, s['context'], font('SemiBold' if False else 'Medium', f_ctx)) + 26
    if s.get('label'):
        spaced(dr, (0, y), s['label'], font('Medium', 26), MUTE + (255,), 3, W / 2); y += 48
    f = font('Bold', f_opt); ft = font('Medium', max(28, int(f_opt * 0.66)))
    for i, o in enumerate(s['options']):
        st = o.get('mark', 'plain') if revealed else 'plain'
        tag = o.get('tag') if revealed else None
        y += card(dr, y, LETTERS[i], o['text'], f, ft, tag, st, tag_alpha) + 22
    return fr, y


def end_screen(s, art_small):
    fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
    y = SAFE_TOP - 10
    if art_small is not None:
        fr.alpha_composite(art_small, ((W - art_small.width) // 2, y)); y += art_small.height + 40
    fv = font('Bold', 96)
    while dr.textlength(s['verdict'], font=fv) > 940: fv = font('Bold', fv.size - 4)
    tw = dr.textlength(s['verdict'], font=fv); dr.text(((W - tw) / 2, y), s['verdict'], font=fv, fill=NAVY + (255,)); y += int(fv.size * 1.5)
    fw = font('Medium', 46); lines = wrap_balanced(dr, s['why'], fw, 860); bh = len(lines) * int(46 * 1.4) + 70
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
    fp = font('Bold', 40); tw = dr.textlength(s['end2'], font=fp)
    dr.rounded_rectangle(((W - tw) / 2 - 36, y, (W + tw) / 2 + 36, y + 76), radius=40, fill=NAVY + (255,))
    dr.text(((W - tw) / 2, y + 15), s['end2'], font=fp, fill=WHITE + (255,))
    return fr, y + 76


def shift(img, top, bottom, dy):
    out = Image.new('RGBA', (W, H), CREAM + (255,)); out.alpha_composite(img.crop((0, top, W, bottom)), (0, top + dy)); return out


def centre_dy(top, bottom):
    return max(0, int((SAFE_TOP + SAFE_BOTTOM) / 2 - (top + bottom) / 2))


def timing(s):
    words = sum(len(o['text'].split()) for o in s['options']) + sum(len(l.split()) for l in (s.get('context') or {}).get('lines', []))
    t_rev = min(5.2, max(3.4, 1.4 + words * 0.14))
    return t_rev, t_rev + 2.5, t_rev + 5.2   # reveal, end screen, total


def music(path, seed, dur, t_rev):
    sr = 44100; L = int(sr * dur); tt = np.arange(L) / sr; audio = np.zeros(L)
    audio += sum(np.sin(2 * np.pi * f * tt) for f in [130.81, 196.0, 261.63]) * 0.02 * np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.3)
    rng = np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 2**32)
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    for k in range(30):
        st = 0.05 + k * 0.5
        if st > dur - 1: break
        f = scale[rng.integers(len(scale))]; s0 = int(st * sr); e = min(L, s0 + int(1.4 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += (np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn)) * np.exp(-tn * 3.4) * 0.07
    for f in (1046.5, 1318.5, 1568.0):
        s0 = int(t_rev * sr); e = min(L, s0 + int(2 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += np.sin(2 * np.pi * f * tn) * np.exp(-tn * 2.5) * 0.06
    audio *= np.minimum(1, (dur - tt) / 0.3)
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


def fit(s, art):
    """Largest art + type sizes whose revealed board fits the safe zone."""
    for art_h, sizes in [(250, (110, 52, 44)), (200, (104, 48, 42)), (170, (96, 44, 40)), (0, (96, 44, 40)), (0, (90, 40, 36))]:
        art_small = art.resize((int(art.width * art_h / art.height), art_h), Image.LANCZOS) if art_h else None
        rev, b2 = board(s, art_small, True, sizes)
        if b2 + 30 <= SAFE_BOTTOM - 20 or art_h == 0 and sizes[1] == 40:
            return art_small, sizes
    sys.exit('Board too long for the safe zone.')


def cover(s, art, out, art_small, sizes):
    img, b = board(s, art_small, False, sizes)
    top = SAFE_TOP - 10; img = shift(img, top, b + 10, centre_dy(top, b + 10))
    img.convert('RGB').save(out, quality=92)


def render(s, outdir):
    os.makedirs(outdir, exist_ok=True)
    art = Image.open(os.path.join(SOCIAL, 'art', s['art'] + '.png')).convert('RGBA')
    art_small, sizes = fit(s, art)
    t_rev, t_end, dur = timing(s)
    top = SAFE_TOP - 10
    plain, b1 = board(s, art_small, False, sizes)
    rev, b2 = board(s, art_small, True, sizes)
    if b2 + 30 > SAFE_BOTTOM: sys.exit(f'{outdir}: board overflows the safe zone ({b2}).')
    dy = centre_dy(top, b2 + 30)
    plain = shift(plain, top, b2 + 30, dy); rev = shift(rev, top, b2 + 30, dy); b1 += dy
    end_art = art.resize((int(art.width * 250 / art.height), 250), Image.LANCZOS)
    end, eb = end_screen(s, end_art)
    if eb > SAFE_BOTTOM: sys.exit(f'{outdir}: end screen too long.')
    end = shift(end, top, eb, centre_dy(top, eb))
    frames = os.path.join(outdir, 'frames'); os.makedirs(frames, exist_ok=True)
    for i in range(int(FPS * dur)):
        t = i / FPS
        if t < t_rev:
            fr = plain.copy(); dr = ImageDraw.Draw(fr); p = t / t_rev; by = min(b1 + 12, SAFE_BOTTOM - 12)
            dr.rounded_rectangle((290, by, 790, by + 10), radius=5, fill=(232, 226, 245, 255))
            if p > 0.02: dr.rounded_rectangle((290, by, 290 + int(500 * p), by + 10), radius=5, fill=PLUM + (255,))
        elif t < t_end:
            fr = Image.blend(plain, rev, ease((t - t_rev) / 0.3))
            if t >= t_end - 0.3: fr = Image.blend(fr, end, ease((t - (t_end - 0.3)) / 0.3))
        else:
            fr = end.copy()
            if t >= dur - 0.35: fr = Image.blend(fr, plain, ease((t - (dur - 0.35)) / 0.35))
        fr.convert('RGB').save(os.path.join(frames, f'{i:04d}.png'))
    wav = os.path.join(outdir, 'audio.wav'); music(wav, s.get('seed', s['question']), dur, t_rev)
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%04d.png'),
                    '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                    '-b:a', '128k', '-shortest', '-movflags', '+faststart', os.path.join(outdir, 'reel.mp4')], check=True)
    shutil.rmtree(frames, ignore_errors=True); os.remove(wav)
    cover(s, art, os.path.join(outdir, 'cover.jpg'), art_small, sizes)
    return dur


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec', nargs='?'); ap.add_argument('--out')
    ap.add_argument('--all'); ap.add_argument('--root'); ap.add_argument('--only'); ap.add_argument('--still', action='store_true')
    a = ap.parse_args()
    if a.all:
        specs = json.load(open(a.all))
        for s in specs:
            if a.only and s['id'] not in a.only.split(','): continue
            if a.still:
                art = Image.open(os.path.join(SOCIAL, 'art', s['art'] + '.png')).convert('RGBA'); asm, sz = fit(s, art)
                img, b = board(s, asm, True, sz); os.makedirs(a.root, exist_ok=True)
                img.convert('RGB').resize((360, 640)).save(os.path.join(a.root, s['id'] + '_rev.png'))
                e, _ = end_screen(s, asm); e.convert('RGB').resize((360, 640)).save(os.path.join(a.root, s['id'] + '_end.png'))
            else:
                print(s['id'], round(render(s, os.path.join(a.root, s['id'])), 1), 's')
    else:
        print(render(json.load(open(a.spec)), a.out))


if __name__ == '__main__':
    main()
