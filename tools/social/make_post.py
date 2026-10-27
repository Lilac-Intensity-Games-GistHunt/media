#!/usr/bin/env python3
"""Make one "Yesterday's Gist Daily" post from the social feed's JSON (GET /api/social/yesterday).

Writes, into --out:
  reel.mp4      9:16 Reel for Instagram + TikTok (about 16 s): the question fills the first second, ~5 s on the cards,
                "Comment your pick", the answer and why, then "Today's Daily is live at playgisthunt.com".
  linkedin.jpg  4:5 still for LinkedIn: the question with the answer marked, and why.
  meta.json     what the post shows (season, art, letters, answer) plus alt texts, for the caption and the checks.

Usage: python3 make_post.py feed.json --out DIR [--expect-day YYYY-MM-DD]
It stops with an error (and writes nothing) if the feed has no question, the day isn't the one expected, or the answer
doesn't check out against the cards.
"""
import argparse, hashlib, json, math, os, subprocess, sys, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 16.0
CREAM = (255, 248, 237); NAVY = (23, 36, 61); LILAC = (200, 188, 255); BLUSH = (255, 188, 188); PLUM = (74, 30, 76)
WHITE = (255, 255, 255); PEACH = (255, 214, 190); LILAC_SOFT = (238, 233, 255); GREY = (150, 150, 160)

def font(weight, size): return ImageFont.truetype(os.path.join(HERE, 'fonts', f'Poppins-{weight}.ttf'), int(size))

# Which picture goes with which season (SOCIAL_FEED.md, December: holiday puzzles). Kwanzaa's picture is not used here:
# the Kwanzaa post stays a greeting.
ART = {'hanukkah': ['hanukkah_hedgehog'],
       'christmas': ['christmas_reindeer', 'christmas_gingerbread', 'christmas_tree_friends', 'christmas_gingerbread_tree'],
       'new year': ['newyear_toast'],
       None: ['winter_polarbear_cocoa', 'winter_owl', 'winter_fox', 'winter_polarbear_lantern']}
ART_WORDS = {'hanukkah_hedgehog': 'a smiling hedgehog in a lilac scarf beside a lit menorah and a plate of doughnuts',
             'christmas_reindeer': 'a small reindeer in a lilac hat and scarf beside a wrapped gift',
             'christmas_gingerbread': 'a smiling gingerbread friend with a mug of cocoa and a gift',
             'christmas_tree_friends': 'a fox, a hedgehog and a squirrel decorating a small Christmas tree',
             'christmas_gingerbread_tree': 'a gingerbread friend with cocoa beside a decorated tree',
             'newyear_toast': 'a fox and a hedgehog in party hats toasting beside a 2027 calendar',
             'winter_polarbear_cocoa': 'a polar bear in lilac earmuffs holding a mug of cocoa',
             'winter_owl': 'a snowy owl in a knit hat holding a magnifying glass to a snowflake',
             'winter_fox': 'a fox wrapped in a blanket with a warm mug by a snowy window',
             'winter_polarbear_lantern': 'a polar bear holding a glowing lantern under a crescent moon'}

def season_key(name):
    n = (name or '').lower()
    for k in ('hanukkah', 'christmas', 'new year'):
        if k in n: return k
    return None

def pick_art(season, day):
    choices = ART[season_key(season)]
    return choices[int(hashlib.sha256(('art:' + day).encode()).hexdigest(), 16) % len(choices)]

def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=f) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def spaced(draw, xy, text, f, fill, spacing=3, anchor_center=None):
    x, y = xy
    if anchor_center is not None:
        total = sum(draw.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
        x = anchor_center - total / 2
    for c in text:
        draw.text((x, y), c, font=f, fill=fill); x += draw.textlength(c, font=f) + spacing

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- checks
def load(feed_path, expect_day):
    d = json.load(open(feed_path))
    if 'error' in d: sys.exit('Feed answered an error (wrong key or feed switched off): ' + str(d.get('error')))
    q, r = d.get('question'), d.get('reveal')
    if not q or not r: sys.exit('No question to post for ' + str(d.get('day')) + ': ' + str(d.get('message', '')))
    if expect_day and d.get('day') != expect_day: sys.exit(f"Feed day {d.get('day')} is not the expected {expect_day}.")
    ids = [c['id'] for c in q['cards']]
    if not r['correct'] or any(c not in ids for c in r['correct']): sys.exit('Answer ids are not among the cards.')
    if len(r['correct']) != q.get('pick', len(r['correct'])): sys.exit('Answer size does not match the pick.')
    marked = {c['id'] for c in r.get('cards', []) if c.get('correct')}
    if marked and marked != set(r['correct']): sys.exit('Reveal cards disagree with the answer.')
    return d

# ---------------------------------------------------------------- shared drawing
def card_box(draw, x, y, w, letter, text, f, fl, state='plain', alpha=1.0):
    """Draw one card on an RGBA layer; return its height. state: plain | right | dim."""
    lines = wrap(draw, text, f, w - 130)
    lh = int(f.size * 1.32); h = max(len(lines) * lh + 44, 100)
    fill = {'plain': WHITE, 'right': PEACH, 'dim': (247, 244, 240)}[state]
    edge = {'plain': NAVY, 'right': NAVY, 'dim': (205, 200, 205)}[state]
    ink = NAVY if state != 'dim' else (165, 165, 175)
    a = int(255 * alpha)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=fill + (a,), outline=edge + (a,), width=3)
    cx, cy = x + 52, y + h / 2
    badge = LILAC if state == 'plain' else (NAVY if state == 'right' else (225, 222, 230))
    draw.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=badge + (a,))
    # A right card keeps its letter, white on navy, so "Answer: A, C" can be matched to the cards; the peach fill marks it.
    ink_l = WHITE if state == 'right' else (NAVY if state == 'plain' else (165, 165, 175))
    tw = draw.textlength(letter, font=fl)
    draw.text((cx - tw / 2, cy - fl.size * 0.62), letter, font=fl, fill=ink_l + (a,))
    ty = y + (h - len(lines) * lh) / 2 - 4
    for ln in lines:
        draw.text((x + 104, ty), ln, font=f, fill=ink + (a,)); ty += lh
    return h

def measure_cards(q, f, w):
    d = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    lh = int(f.size * 1.32)
    return [max(len(wrap(d, c['text'], f, w - 130)) * lh + 44, 100) for c in q['cards']]

# ---------------------------------------------------------------- the Reel
def reel_layout(d):
    q = d['question']
    for s in [1.0, 0.95, 0.9, 0.85, 0.8, 0.76, 0.72, 0.68, 0.64, 0.6]:
        F = dict(eye=font('Medium', 32 * s), ins=font('Bold', 58 * s), lab=font('Medium', 28 * s), body=font('Medium', 44 * s),
                 card=font('Medium', 42 * s), letter=font('Bold', 34 * s), pick=font('Medium', 34 * s))
        dr = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
        y = 300; L = {}
        L['eye'] = y; y += int(46 * s)
        L['ins'] = y; ins = wrap(dr, q['instruction'], F['ins'], 900); L['ins_lines'] = ins; y += len(ins) * int(F['ins'].size * 1.25) + int(22 * s)
        body = wrap(dr, (q.get('text') or {}).get('body') or '', F['body'], 840)
        if body:
            ph = (int(F['lab'].size * 1.6) if (q.get('text') or {}).get('label') else 0) + len(body) * int(F['body'].size * 1.35) + 48
            L['panel'] = (y, ph); L['body_lines'] = body; y += ph + int(22 * s)
        L['pick'] = y; y += int(F['pick'].size * 1.6)
        hs = measure_cards(q, F['card'], 900); L['cards'] = []
        for h in hs: L['cards'].append((y, h)); y += h + int(16 * s)
        if y <= 1560: L['end'] = y; return F, L, s
    return F, L, s

def render_reel(d, art_name, out_mp4, workdir):
    q, r = d['question'], d['reveal']
    F, L, s = reel_layout(d)
    art = Image.open(os.path.join(HERE, 'art', art_name + '.png')).convert('RGBA')
    art_small = art.resize((int(art.width * 200 / art.height), 200), Image.LANCZOS)
    big_h = 560; art_big = art.resize((min(940, int(art.width * big_h / art.height)), min(big_h, int(art.height * 940 / art.width))), Image.LANCZOS)
    letters = 'ABCDEFGHIJKL'
    season = (q.get('seasonName') or '').upper()
    eyebrow = "YESTERDAY'S DAILY · Q" + str(q['number']) + ' OF ' + str(q['of']) + (' · ' + season if season else '')
    right = set(r['correct'])

    def header(draw, a=1.0):
        A = int(255 * a)
        spaced(draw, (0, L['eye']), eyebrow, F['eye'], PLUM + (A,), 3, W / 2)
        y = L['ins']
        for ln in L['ins_lines']:
            tw = draw.textlength(ln, font=F['ins']); draw.text(((W - tw) / 2, y), ln, font=F['ins'], fill=NAVY + (A,)); y += int(F['ins'].size * 1.25)
        if 'panel' in L:
            py, ph = L['panel']; draw.rounded_rectangle((90, py, 990, py + ph), radius=26, fill=LILAC_SOFT + (A,))
            y = py + 24; lab = (q.get('text') or {}).get('label')
            if lab: spaced(draw, (120, y), lab.upper(), F['lab'], PLUM + (A,), 2); y += int(F['lab'].size * 1.6)
            for ln in L['body_lines']: draw.text((120, y), ln, font=F['body'], fill=NAVY + (A,)); y += int(F['body'].size * 1.35)
        pk = 'Pick ' + str(q['pick']) if q['pick'] != 1 else 'Pick 1'
        tw = draw.textlength(pk, font=F['pick']); draw.text(((W - tw) / 2, L['pick']), pk, font=F['pick'], fill=PLUM + (A,))

    def pill(draw, text, y, f, fill, ink, a=1.0, pad=36):
        tw = draw.textlength(text, font=f); A = int(255 * a)
        draw.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + f.size * 1.9), radius=int(f.size), fill=fill + (A,))
        draw.text(((W - tw) / 2, y + f.size * 0.38), text, font=f, fill=ink + (A,))

    frames = os.path.join(workdir, 'frames'); os.makedirs(frames, exist_ok=True)
    N = int(FPS * DUR)
    f_big = font('Bold', 76)
    exp_draw = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
    exp_text = r.get('explanation') or ''
    for es in [50, 47, 44, 41, 38, 35, 32, 30]:
        f_exp = font('Medium', es); exp_lines = wrap(exp_draw, exp_text, f_exp, 880)
        aha = r.get('aha'); aha_lines = wrap(exp_draw, aha, f_exp, 880) if aha else []
        if (len(exp_lines) + len(aha_lines)) * es * 1.4 <= 820: break
    title_lines = wrap(exp_draw, r.get('title') or 'The answer', f_big, 900)
    ans_letters = ', '.join(letters[i] for i, c in enumerate(q['cards']) if c['id'] in right)

    for i in range(N):
        t = i / FPS
        fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
        if t < 10.0:
            fr.alpha_composite(art_small, ((W - art_small.width) // 2, 70))
            header(dr)
            for k, (c, (cy, ch)) in enumerate(zip(q['cards'], L['cards'])):
                appear = ease((t - 0.5 - 0.12 * k) / 0.3)
                if appear <= 0: continue
                state = 'plain'
                if t >= 8.0: state = 'right' if c['id'] in right else 'dim'
                lay = Image.new('RGBA', (W, ch + 10), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                card_box(ld, 90, 0, 900, letters[k], c['text'], F['card'], F['letter'], state, appear)
                fr.alpha_composite(lay, (0, int(cy + 24 * (1 - appear))))
            if 1.2 <= t < 6.5:   # 5-s thinking bar
                p = min(1, (t - 1.2) / 5.0); y = 1600
                dr.rounded_rectangle((240, y, 840, y + 16), radius=8, fill=(232, 226, 245, 255))
                dr.rounded_rectangle((240, y, 240 + int(600 * p), y + 16), radius=8, fill=LILAC + (255,))
                tl = str(max(1, math.ceil(5 - (t - 1.2))))
                tw = dr.textlength(tl, font=F['pick']); dr.text(((W - tw) / 2, y + 30), tl, font=F['pick'], fill=PLUM + (255,))
            if 6.5 <= t < 8.0:
                a = ease((t - 6.5) / 0.3); pulse = 1 + 0.04 * math.sin((t - 6.5) * 2 * math.pi * 1.5)
                pill(dr, 'Comment your pick', 1590, font('Bold', int(44 * pulse)), NAVY, WHITE, a)
            if t >= 8.0:
                a = ease((t - 8.0) / 0.3)
                pill(dr, 'Answer: ' + ans_letters, 1590, font('Bold', 44), NAVY, WHITE, a)
            if t >= 9.6:   # fade out
                fade = ease((t - 9.6) / 0.4); fr = Image.blend(fr, Image.new('RGBA', (W, H), CREAM + (255,)), fade); dr = ImageDraw.Draw(fr)
        elif t < 13.6:   # why
            a = ease((t - 10.0) / 0.4)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); A = int(255 * a)
            spaced(ld, (0, 330), 'THE ANSWER · ' + ans_letters, font('Medium', 34), PLUM + (A,), 3, W / 2)
            y = 410
            for ln in title_lines:
                tw = ld.textlength(ln, font=f_big); ld.text(((W - tw) / 2, y), ln, font=f_big, fill=NAVY + (A,)); y += int(f_big.size * 1.2)
            y += 30
            ld.rounded_rectangle((70, y, 1010, y + int((len(exp_lines) + len(aha_lines) + (0.6 if aha_lines else 0)) * f_exp.size * 1.4) + 60), radius=30, fill=WHITE + (A,), outline=NAVY + (A,), width=3)
            y += 30
            for ln in exp_lines: ld.text((100, y), ln, font=f_exp, fill=NAVY + (A,)); y += int(f_exp.size * 1.4)
            if aha_lines:
                y += int(f_exp.size * 0.6)
                for ln in aha_lines: ld.text((100, y), ln, font=f_exp, fill=PLUM + (A,)); y += int(f_exp.size * 1.4)
            fr.alpha_composite(lay)
            fr.alpha_composite(art_small, ((W - art_small.width) // 2, 70))
            if t >= 13.2:
                fade = ease((t - 13.2) / 0.4); fr = Image.blend(fr, Image.new('RGBA', (W, H), CREAM + (255,)), fade); dr = ImageDraw.Draw(fr)
        else:   # end card
            a = ease((t - 13.6) / 0.4); z = 0.96 + 0.04 * ease((t - 13.6) / 2.4)
            ab = art_big.resize((int(art_big.width * z), int(art_big.height * z)), Image.LANCZOS)
            lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay); A = int(255 * a)
            wm = font('Bold', 96); tw = ld.textlength('Gist Hunt', font=wm); ld.text(((W - tw) / 2, 250), 'Gist Hunt', font=wm, fill=NAVY + (A,))
            lay.alpha_composite(ab, ((W - ab.width) // 2, 450 + (big_h - ab.height) // 2))
            l1 = "Today's Daily is live"; tw = ld.textlength(l1, font=font('Bold', 56)); ld.text(((W - tw) / 2, 1080), l1, font=font('Bold', 56), fill=NAVY + (A,))
            pill(ld, 'playgisthunt.com', 1190, font('Bold', 46), LILAC, NAVY, a)
            fr.alpha_composite(lay)
        fr.convert('RGB').save(os.path.join(frames, f'{i:04d}.png'))
    wav = os.path.join(workdir, 'audio.wav'); music(wav, d['day'])
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%04d.png'), '-i', wav,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-shortest',
                    '-movflags', '+faststart', out_mp4], check=True)
    shutil.rmtree(frames, ignore_errors=True); os.remove(wav)

def music(path, day):
    """Original synthesised music box (no licensed music): a soft pad, a pentatonic melody, a chime at the reveal."""
    sr = 44100; L = int(sr * DUR); tt = np.arange(L) / sr; audio = np.zeros(L)
    audio += sum(np.sin(2 * np.pi * f * tt) for f in [130.81, 196.0, 261.63]) * 0.02 * np.minimum(1, tt / 1.5) * np.minimum(1, (DUR - tt) / 1.0)
    rng = np.random.default_rng(int(hashlib.sha256(day.encode()).hexdigest(), 16) % 2**32)
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    for k in range(28):
        st = 0.2 + k * 0.55
        if st > DUR - 1: break
        f = scale[rng.integers(len(scale))]; s0 = int(st * sr); e = min(L, s0 + int(1.5 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += (np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn)) * np.exp(-tn * 3.4) * 0.07
    for f in (1046.5, 1318.5, 1568.0):   # reveal chime at 8 s
        s0 = int(8.0 * sr); e = min(L, s0 + int(2 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += np.sin(2 * np.pi * f * tn) * np.exp(-tn * 2.5) * 0.06
    audio *= np.minimum(1, (DUR - tt) / 0.8)
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- the LinkedIn still
def render_still(d, art_name, out_jpg):
    q, r = d['question'], d['reveal']; SW, SH = 1080, 1350
    art = Image.open(os.path.join(HERE, 'art', art_name + '.png')).convert('RGBA')
    letters = 'ABCDEFGHIJKL'; right = set(r['correct'])
    season = (q.get('seasonName') or '').upper()
    for s in [1.0, 0.92, 0.85, 0.78, 0.72, 0.66, 0.6]:
        img = Image.new('RGBA', (SW, SH), CREAM + (255,)); dr = ImageDraw.Draw(img)
        a2 = art.resize((int(art.width * 150 * s / art.height), int(150 * s)), Image.LANCZOS); img.alpha_composite(a2, ((SW - a2.width) // 2, 36))
        y = 36 + int(150 * s) + 18
        spaced(dr, (0, y), "YESTERDAY'S GIST DAILY" + (' · ' + season if season else ''), font('Medium', 24 * s), PLUM + (255,), 3, SW / 2); y += int(44 * s)
        fi = font('Bold', 38 * s)
        for ln in wrap(dr, q['instruction'], fi, 940): tw = dr.textlength(ln, font=fi); dr.text(((SW - tw) / 2, y), ln, font=fi, fill=NAVY); y += int(fi.size * 1.25)
        y += int(14 * s)
        body = (q.get('text') or {}).get('body') or ''
        if body:
            fb = font('Medium', 30 * s); bl = wrap(dr, body, fb, 880); ph = len(bl) * int(fb.size * 1.35) + 36
            dr.rounded_rectangle((70, y, 1010, y + ph), radius=22, fill=LILAC_SOFT); yy = y + 18
            for ln in bl: dr.text((100, yy), ln, font=fb, fill=NAVY); yy += int(fb.size * 1.35)
            y += ph + int(16 * s)
        fc, fl = font('Medium', 28 * s), font('Bold', 26 * s)
        for k, c in enumerate(q['cards']):
            h = card_box(dr, 70, y, 940, letters[k], c['text'], fc, fl, 'right' if c['id'] in right else 'dim'); y += h + int(12 * s)
        y += int(10 * s)
        ft, fe = font('Bold', 32 * s), font('Medium', 26 * s)
        dr.text((70, y), (r.get('title') or 'The answer') + ' · Answer: ' + ', '.join(letters[i] for i, c in enumerate(q['cards']) if c['id'] in right), font=ft, fill=NAVY); y += int(ft.size * 1.4)
        for ln in wrap(dr, r.get('explanation') or '', fe, 940): dr.text((70, y), ln, font=fe, fill=NAVY); y += int(fe.size * 1.38)
        y += int(14 * s)
        foot = "Today's Daily is live at playgisthunt.com"; ff = font('Bold', 28 * s); tw = dr.textlength(foot, font=ff)
        if y + ff.size * 1.9 <= SH - 24:
            yb = SH - 24 - int(ff.size * 1.9)
            dr.rounded_rectangle(((SW - tw) / 2 - 30, yb, (SW + tw) / 2 + 30, yb + ff.size * 1.9), radius=int(ff.size), fill=LILAC)
            dr.text(((SW - tw) / 2, yb + ff.size * 0.38), foot, font=ff, fill=NAVY)
            img.convert('RGB').save(out_jpg, quality=92); return s
    img.convert('RGB').save(out_jpg, quality=92); return s

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('feed'); ap.add_argument('--out', required=True); ap.add_argument('--expect-day')
    a = ap.parse_args(); d = load(a.feed, a.expect_day); os.makedirs(a.out, exist_ok=True)
    q, r = d['question'], d['reveal']; letters = 'ABCDEFGHIJKL'
    art_name = pick_art(q.get('seasonName'), d['day'])
    render_reel(d, art_name, os.path.join(a.out, 'reel.mp4'), a.out)
    render_still(d, art_name, os.path.join(a.out, 'linkedin.jpg'))
    cards = [{'letter': letters[i], 'text': c['text'], 'correct': c['id'] in r['correct']} for i, c in enumerate(q['cards'])]
    ans = ', '.join(c['letter'] for c in cards if c['correct'])
    body = (q.get('text') or {}).get('body') or ''
    card_list = ' '.join(f"{c['letter']}: {c['text']}" for c in cards)
    meta = {'day': d['day'], 'season': q.get('seasonName'), 'art': art_name, 'goal': q['goal'], 'goalName': q.get('goalName'), 'level': q.get('level'),
            'number': q['number'], 'of': q['of'], 'pick': q['pick'], 'instruction': q['instruction'], 'text': q.get('text'), 'cards': cards, 'answer': ans,
            'title': r.get('title'), 'explanation': r.get('explanation'), 'aha': r.get('aha'),
            'alt_reel': f"Gist Hunt puzzle video, yesterday's Daily question {q['number']}: {q['instruction']} {body} Cards: {card_list} The video pauses for "
                        f"your pick, then shows the answer, {ans}: {r.get('explanation') or ''} It ends on an illustration of {ART_WORDS[art_name]} and "
                        f"\"Today's Daily is live at playgisthunt.com\".",
            'alt_still': f"Gist Hunt puzzle with its answer: {q['instruction']} {body} Cards: {card_list} Answer {ans} ({r.get('title') or ''}): "
                         f"{r.get('explanation') or ''} Illustration: {ART_WORDS[art_name]}. Today's Daily is live at playgisthunt.com."}
    json.dump(meta, open(os.path.join(a.out, 'meta.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: meta[k] for k in ('day', 'season', 'art', 'goalName', 'number', 'answer', 'title')}, ensure_ascii=False))

if __name__ == '__main__': main()
