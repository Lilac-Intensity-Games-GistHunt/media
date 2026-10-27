#!/usr/bin/env python3
"""Make one "Yesterday's Gist Daily" post from the social feed's JSON (GET /api/social/yesterday).

Writes, into --out:
  reel.mp4      9:16 Reel for Instagram + TikTok (14 s, reel-2): the challenge line and the whole board are on screen from the
                first frame; "Pause to solve", then "Comment your pick"; the reveal at 7 s; the answer, why, and a line to send it on;
                then the board again with "Today's Daily is live · playgisthunt.com", so the last frame loops into the first.
                Everything that matters sits between y=250 and y=1570, clear of Instagram's and TikTok's buttons and caption.
  cover.jpg     1080x1920 cover for the Reel (Metricool videoThumbnailUrl): the art and the challenge line, inside the 3:4 grid crop.
  linkedin.jpg  4:5 still for LinkedIn: the question with the answer marked, and why.
  meta.json     what the post shows (season, art, letters, answer, hook, send line) plus alt texts, for the caption and the checks.

Usage: python3 make_post.py feed.json --out DIR [--expect-day YYYY-MM-DD] [--send "Send this to ..."]
--send is the line on the "why" screen that invites a share, written from the question's own little world (max 90 characters).
It stops with an error (and writes nothing) if the feed has no question, the day isn't the one expected, or the answer
doesn't check out against the cards.
"""
import argparse, hashlib, json, math, os, subprocess, sys, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 14.0
SAFE_TOP, SAFE_BOTTOM = 250, 1570          # Reels/TikTok UI: username on top, caption and buttons on the bottom ~350 px
T_COMMENT, T_REVEAL, T_WHY, T_END = 5.5, 7.0, 9.0, 12.4
NUM = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 6: 'Six'}
DEFAULT_SEND = 'Send this to the friend who reads too fast.'
CREAM = (255, 248, 237); NAVY = (23, 36, 61); LILAC = (200, 188, 255); BLUSH = (255, 188, 188); PLUM = (74, 30, 76)
WHITE = (255, 255, 255); PEACH = (255, 214, 190); LILAC_SOFT = (238, 233, 255); GREY = (150, 150, 160)

def font(weight, size): return ImageFont.truetype(os.path.join(HERE, 'fonts', f'Poppins-{weight}.ttf'), int(size))

# Which picture goes with which season (SOCIAL_FEED.md, December: holiday puzzles). Kwanzaa's picture is not used here:
# the Kwanzaa post stays a greeting.
ART = {'halloween': ['autumn_pumpkin', 'autumn_scarecrow', 'autumn_mushroom'],
       'clocks': ['autumn_sleepy_fox'],
       'thanksgiving': ['autumn_harvest_friends'],
       'black friday': ['autumn_squirrel'],
       'hanukkah': ['hanukkah_hedgehog'],
       'christmas': ['christmas_reindeer', 'christmas_gingerbread', 'christmas_tree_friends', 'christmas_gingerbread_tree'],
       'new year': ['newyear_toast'],
       # No season: autumn animals in September to November, winter animals in December to February.
       'autumn': ['autumn_fox_path', 'autumn_hedgehog_tea', 'autumn_pumpkin', 'autumn_squirrel', 'autumn_sleepy_fox'],
       'winter': ['winter_polarbear_cocoa', 'winter_owl', 'winter_fox', 'winter_polarbear_lantern']}
ART_WORDS = {'hanukkah_hedgehog': 'a smiling hedgehog in a lilac scarf beside a lit menorah and a plate of doughnuts',
             'christmas_reindeer': 'a small reindeer in a lilac hat and scarf beside a wrapped gift',
             'christmas_gingerbread': 'a smiling gingerbread friend with a mug of cocoa and a gift',
             'christmas_tree_friends': 'a fox, a hedgehog and a squirrel decorating a small Christmas tree',
             'christmas_gingerbread_tree': 'a gingerbread friend with cocoa beside a decorated tree',
             'newyear_toast': 'a fox and a hedgehog in party hats toasting beside a 2027 calendar',
             'winter_polarbear_cocoa': 'a polar bear in lilac earmuffs holding a mug of cocoa',
             'winter_owl': 'a snowy owl in a knit hat holding a magnifying glass to a snowflake',
             'autumn_pumpkin': 'a smiling pumpkin in a lilac scarf with a warm mug',
             'autumn_scarecrow': 'a friendly scarecrow in a lilac hat holding a magnifying glass beside a pumpkin',
             'autumn_mushroom': 'a little mushroom in a lilac scarf sitting on a pumpkin',
             'autumn_sleepy_fox': 'a sleepy fox curled up beside a warm mug and autumn leaves',
             'autumn_harvest_friends': 'a fox, a hedgehog and a squirrel sharing a little harvest table with a pumpkin',
             'autumn_squirrel': 'a squirrel in a lilac scarf holding an acorn beside a basket of acorns',
             'autumn_fox_path': 'a fox with a magnifying glass at a fork in an autumn woodland path',
             'autumn_hedgehog_tea': 'a hedgehog in a lilac blanket with a mug of tea and a book',
             'winter_fox': 'a fox wrapped in a blanket with a warm mug by a snowy window',
             'winter_polarbear_lantern': 'a polar bear holding a glowing lantern under a crescent moon'}

def season_key(name, day):
    n = (name or '').lower()
    for k in ('halloween', 'clocks', 'thanksgiving', 'black friday', 'cyber', 'hanukkah', 'christmas', 'new year'):
        if k in n: return 'black friday' if k == 'cyber' else k
    return 'autumn' if int(day[5:7]) in (9, 10, 11) else 'winter'

def pick_art(season, day):
    choices = ART[season_key(season, day)]
    return choices[int(hashlib.sha256(('art:' + day).encode()).hexdigest(), 16) % len(choices)]

def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=f) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def wrap_balanced(draw, text, f, width):
    """Same number of lines as wrap(), but evened out, so a short last line ("it?") doesn't hang on its own."""
    n = len(wrap(draw, text, f, width)); lo, hi = 1, width
    while lo < hi:
        mid = (lo + hi) // 2
        if len(wrap(draw, text, f, mid)) <= n: hi = mid
        else: lo = mid + 1
    return wrap(draw, text, f, lo)

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
def hook_line(q):
    """The challenge on the first frame. Built from the playstyle and the pick, so it is always true to the question."""
    n = q.get('pick') or 1; word = NUM.get(n, str(n))
    goal = q.get('goal')
    if goal == 'odd': return 'One of these doesn’t belong. Can you spot it?'
    if goal == 'subject': return (word + ' of these clues point to the same thing. Which?') if n > 1 else 'One of these clues is the odd thing out. Which?'
    if goal == 'meaning': return (word + (' of these mean' if n > 1 else ' of these means') + ' the same as the story. The rest quietly don’t.')
    if goal == 'fit': return (word + (' of these match' if n > 1 else ' of these matches') + ' every detail. The rest slip somewhere.')
    return q.get('instruction') or 'Can you spot it?'

EYEBROW = "DAILY WORD PUZZLE · YESTERDAY'S GIST DAILY"

def reel_layout(d, hook):
    q = d['question']
    for s in [1.0, 0.95, 0.9, 0.85, 0.8, 0.76, 0.72, 0.68, 0.64, 0.6, 0.56, 0.52]:
        F = dict(eye=font('Medium', 28 * max(s, 0.8)), hook=font('Bold', 64 * max(s, 0.85)), lab=font('Medium', 28 * s), body=font('Medium', 42 * s),
                 card=font('Medium', 42 * s), letter=font('Bold', 34 * s))
        dr = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
        y = SAFE_TOP + 4; L = {}
        L['eye'] = y; y += int(F['eye'].size * 1.7)
        L['hook'] = y; hl = wrap_balanced(dr, hook, F['hook'], 940); L['hook_lines'] = hl; y += len(hl) * int(F['hook'].size * 1.18) + int(20 * s)
        body = wrap(dr, (q.get('text') or {}).get('body') or '', F['body'], 840)
        if body:
            ph = (int(F['lab'].size * 1.6) if (q.get('text') or {}).get('label') else 0) + len(body) * int(F['body'].size * 1.35) + 44
            L['panel'] = (y, ph); L['body_lines'] = body; y += ph + int(20 * s)
        hs = measure_cards(q, F['card'], 900); L['cards'] = []
        for h in hs: L['cards'].append((y, h)); y += h + int(14 * s)
        L['status'] = y + 10            # the "Pause to solve" / "Comment your pick" / "Answer" pill, then a thin bar
        if L['status'] + 120 <= SAFE_BOTTOM: return F, L, s
    return F, L, s

def render_reel(d, art_name, out_mp4, workdir, hook, send):
    q, r = d['question'], d['reveal']
    F, L, s = reel_layout(d, hook)
    if L['status'] + 120 > SAFE_BOTTOM: sys.exit('The board is too long to fit the Reel safely; post it as a still instead.')
    art = Image.open(os.path.join(HERE, 'art', art_name + '.png')).convert('RGBA')
    art_small = art.resize((int(art.width * 170 / art.height), 170), Image.LANCZOS)
    letters = 'ABCDEFGHIJKL'
    right = set(r['correct'])
    ans_letters = ', '.join(letters[i] for i, c in enumerate(q['cards']) if c['id'] in right)

    def pill(draw, text, y, f, fill, ink, a=1.0, pad=36):
        tw = draw.textlength(text, font=f); A = int(255 * a)
        draw.rounded_rectangle(((W - tw) / 2 - pad, y, (W + tw) / 2 + pad, y + f.size * 1.9), radius=int(f.size), fill=fill + (A,))
        draw.text(((W - tw) / 2, y + f.size * 0.38), text, font=f, fill=ink + (A,))

    def board(state_of):
        """The art, eyebrow, challenge line, story and cards. state_of(card) -> plain | right | dim."""
        fr = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(fr)
        fr.alpha_composite(art_small, ((W - art_small.width) // 2, SAFE_TOP - 175))
        spaced(dr, (0, L['eye']), EYEBROW, F['eye'], PLUM + (255,), 3, W / 2)
        y = L['hook']
        for ln in L['hook_lines']:
            tw = dr.textlength(ln, font=F['hook']); dr.text(((W - tw) / 2, y), ln, font=F['hook'], fill=NAVY + (255,)); y += int(F['hook'].size * 1.18)
        if 'panel' in L:
            py, ph = L['panel']; dr.rounded_rectangle((90, py, 990, py + ph), radius=26, fill=LILAC_SOFT + (255,))
            y = py + 22; lab = (q.get('text') or {}).get('label')
            if lab: spaced(dr, (120, y), lab.upper(), F['lab'], PLUM + (255,), 2); y += int(F['lab'].size * 1.6)
            for ln in L['body_lines']: dr.text((120, y), ln, font=F['body'], fill=NAVY + (255,)); y += int(F['body'].size * 1.35)
        for k, (c, (cy, ch)) in enumerate(zip(q['cards'], L['cards'])):
            card_box(dr, 90, cy, 900, letters[k], c['text'], F['card'], F['letter'], state_of(c))
        return fr

    plain = board(lambda c: 'plain')
    revealed = board(lambda c: 'right' if c['id'] in right else 'dim')

    # The "why" screen, drawn once.
    why = Image.new('RGBA', (W, H), CREAM + (255,)); wd = ImageDraw.Draw(why)
    why.alpha_composite(art_small, ((W - art_small.width) // 2, SAFE_TOP - 175))
    exp_text = r.get('explanation') or ''; aha = r.get('aha')
    f_send = font('Bold', 44)
    send_lines = wrap_balanced(wd, send, f_send, 860)
    for ts, es in [(76, 48), (72, 45), (68, 42), (64, 40), (60, 38), (58, 36), (56, 34), (54, 32), (52, 30)]:
        f_big, f_exp = font('Bold', ts), font('Medium', es)
        title_lines = wrap_balanced(wd, r.get('title') or 'The answer', f_big, 900)
        exp_lines = wrap(wd, exp_text, f_exp, 860); aha_lines = wrap(wd, aha, f_exp, 860) if aha else []
        box_h = int((len(exp_lines) + len(aha_lines) + (0.6 if aha_lines else 0)) * es * 1.4) + 60
        total = 60 + len(title_lines) * int(ts * 1.2) + 30 + box_h + 40 + len(send_lines) * int(44 * 1.3) + 56
        if SAFE_TOP + 20 + total <= SAFE_BOTTOM: break
    y = SAFE_TOP + 20
    spaced(wd, (0, y), 'THE ANSWER · ' + ans_letters, font('Medium', 34), PLUM + (255,), 3, W / 2); y += 60
    for ln in title_lines:
        tw = wd.textlength(ln, font=f_big); wd.text(((W - tw) / 2, y), ln, font=f_big, fill=NAVY + (255,)); y += int(f_big.size * 1.2)
    y += 30
    wd.rounded_rectangle((70, y, 1010, y + box_h), radius=30, fill=WHITE + (255,), outline=NAVY + (255,), width=3)
    yy = y + 30
    for ln in exp_lines: wd.text((100, yy), ln, font=f_exp, fill=NAVY + (255,)); yy += int(f_exp.size * 1.4)
    if aha_lines:
        yy += int(f_exp.size * 0.6)
        for ln in aha_lines: wd.text((100, yy), ln, font=f_exp, fill=PLUM + (255,)); yy += int(f_exp.size * 1.4)
    y += box_h + 40
    sh = len(send_lines) * int(44 * 1.3) + 56
    wd.rounded_rectangle((110, y, 970, y + sh), radius=34, fill=LILAC + (255,))
    yy = y + 28
    for ln in send_lines:
        tw = wd.textlength(ln, font=f_send); wd.text(((W - tw) / 2, yy), ln, font=f_send, fill=NAVY + (255,)); yy += int(44 * 1.3)

    f_pill = font('Bold', 44); f_pill_s = font('Bold', 40)
    blank = Image.new('RGBA', (W, H), CREAM + (255,))
    frames = os.path.join(workdir, 'frames'); os.makedirs(frames, exist_ok=True)
    N = int(FPS * DUR); sy = L['status']
    for i in range(N):
        t = i / FPS
        if t < T_REVEAL:
            fr = plain.copy(); dr = ImageDraw.Draw(fr)
            if t < T_COMMENT:
                pill(dr, 'Pause to solve', sy, f_pill, LILAC, NAVY)
                p = t / T_COMMENT; by = sy + int(44 * 1.9) + 16
                dr.rounded_rectangle((290, by, 790, by + 10), radius=5, fill=(232, 226, 245, 255))
                if p > 0.02: dr.rounded_rectangle((290, by, 290 + int(500 * p), by + 10), radius=5, fill=PLUM + (255,))
            else:
                pulse = 1 + 0.04 * math.sin((t - T_COMMENT) * 2 * math.pi * 1.5)
                pill(dr, 'Comment your pick', sy, font('Bold', int(44 * pulse)), NAVY, WHITE)
        elif t < T_WHY:
            a = ease((t - T_REVEAL) / 0.25)
            fr = Image.blend(plain, revealed, a); dr = ImageDraw.Draw(fr)
            pill(dr, 'Answer: ' + ans_letters, sy, f_pill, NAVY, WHITE, a)
            if t >= T_WHY - 0.3: fr = Image.blend(fr, why, ease((t - (T_WHY - 0.3)) / 0.3))
        elif t < T_END:
            fr = why.copy()
            if t >= T_END - 0.3: fr = Image.blend(fr, plain, ease((t - (T_END - 0.3)) / 0.3))
        else:
            # Back to the opening board with the call to play, so the last frame loops into the first.
            fr = plain.copy(); dr = ImageDraw.Draw(fr)
            pill(dr, "Today's Daily is live · playgisthunt.com", sy, f_pill_s, NAVY, WHITE, ease((t - T_END) / 0.25))
            if t >= DUR - 0.35:   # hand back to "Pause to solve"
                b = plain.copy(); bd = ImageDraw.Draw(b); pill(bd, 'Pause to solve', sy, f_pill, LILAC, NAVY)
                fr = Image.blend(fr, b, ease((t - (DUR - 0.35)) / 0.35))
        fr.convert('RGB').save(os.path.join(frames, f'{i:04d}.png'))
    wav = os.path.join(workdir, 'audio.wav'); music(wav, d['day'])
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(frames, '%04d.png'), '-i', wav,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-shortest',
                    '-movflags', '+faststart', out_mp4], check=True)
    shutil.rmtree(frames, ignore_errors=True); os.remove(wav)

def render_cover(d, art_name, out_jpg, hook):
    """The Reel's cover: art and the challenge line, all inside the central 3:4 area (y 240-1680) the profile grid shows."""
    img = Image.new('RGBA', (W, H), CREAM + (255,)); dr = ImageDraw.Draw(img)
    spaced(dr, (0, 330), 'DAILY WORD PUZZLE', font('Medium', 36), PLUM + (255,), 4, W / 2)
    for fs in (84, 78, 72, 66):
        fh = font('Bold', fs); hl = wrap_balanced(dr, hook, fh, 920)
        if len(hl) <= 3: break
    y = 400
    for ln in hl:
        tw = dr.textlength(ln, font=fh); dr.text(((W - tw) / 2, y), ln, font=fh, fill=NAVY + (255,)); y += int(fs * 1.16)
    art = Image.open(os.path.join(HERE, 'art', art_name + '.png')).convert('RGBA')
    room = 1440 - y - 40
    ah = min(room, 760); a2 = art.resize((min(900, int(art.width * ah / art.height)), min(ah, int(art.height * 900 / art.width))), Image.LANCZOS)
    img.alpha_composite(a2, ((W - a2.width) // 2, y + 30 + (room - a2.height) // 2))
    f = font('Bold', 44); t = "Yesterday's Gist Daily"; tw = dr.textlength(t, font=f)
    dr.rounded_rectangle(((W - tw) / 2 - 40, 1480, (W + tw) / 2 + 40, 1480 + 84), radius=42, fill=LILAC + (255,))
    dr.text(((W - tw) / 2, 1480 + 17), t, font=f, fill=NAVY + (255,))
    img.convert('RGB').save(out_jpg, quality=92)

def music(path, day):
    """Original synthesised music box (no licensed music): a soft pad, a pentatonic melody, a chime at the reveal."""
    sr = 44100; L = int(sr * DUR); tt = np.arange(L) / sr; audio = np.zeros(L)
    audio += sum(np.sin(2 * np.pi * f * tt) for f in [130.81, 196.0, 261.63]) * 0.02 * np.minimum(1, tt / 0.3) * np.minimum(1, (DUR - tt) / 0.3)
    rng = np.random.default_rng(int(hashlib.sha256(day.encode()).hexdigest(), 16) % 2**32)
    scale = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
    for k in range(28):
        st = 0.05 + k * 0.55
        if st > DUR - 1: break
        f = scale[rng.integers(len(scale))]; s0 = int(st * sr); e = min(L, s0 + int(1.5 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += (np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn)) * np.exp(-tn * 3.4) * 0.07
    for f in (1046.5, 1318.5, 1568.0):   # reveal chime
        s0 = int(T_REVEAL * sr); e = min(L, s0 + int(2 * sr)); tn = np.arange(e - s0) / sr
        audio[s0:e] += np.sin(2 * np.pi * f * tn) * np.exp(-tn * 2.5) * 0.06
    audio *= np.minimum(1, (DUR - tt) / 0.3)
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
    ap.add_argument('--send', help='the share line on the "why" screen (max 90 characters, no links)')
    a = ap.parse_args(); d = load(a.feed, a.expect_day)
    send = ' '.join((a.send or DEFAULT_SEND).split())
    if len(send) > 90: sys.exit('--send is longer than 90 characters.')
    if '://' in send or 'www.' in send or '@' in send: sys.exit('--send must not hold links or handles.')
    os.makedirs(a.out, exist_ok=True)
    q, r = d['question'], d['reveal']; letters = 'ABCDEFGHIJKL'
    art_name = pick_art(q.get('seasonName'), d['day'])
    hook = hook_line(q)
    render_reel(d, art_name, os.path.join(a.out, 'reel.mp4'), a.out, hook, send)
    render_cover(d, art_name, os.path.join(a.out, 'cover.jpg'), hook)
    render_still(d, art_name, os.path.join(a.out, 'linkedin.jpg'))
    cards = [{'letter': letters[i], 'text': c['text'], 'correct': c['id'] in r['correct']} for i, c in enumerate(q['cards'])]
    ans = ', '.join(c['letter'] for c in cards if c['correct'])
    body = (q.get('text') or {}).get('body') or ''
    card_list = ' '.join(f"{c['letter']}: {c['text']}" for c in cards)
    meta = {'day': d['day'], 'season': q.get('seasonName'), 'art': art_name, 'goal': q['goal'], 'goalName': q.get('goalName'), 'level': q.get('level'),
            'number': q['number'], 'of': q['of'], 'pick': q['pick'], 'instruction': q['instruction'], 'text': q.get('text'), 'cards': cards, 'answer': ans,
            'title': r.get('title'), 'explanation': r.get('explanation'), 'aha': r.get('aha'),
            'renderer': 'reel-2', 'hook': hook, 'send': send, 'reveal_at': T_REVEAL, 'duration': DUR,
            'alt_reel': f"Gist Hunt daily word puzzle video with an illustration of {ART_WORDS[art_name]}. {hook} {body} Cards: {card_list} "
                        f"\"Pause to solve\", then \"Comment your pick\". The answer is {ans}: {r.get('title') or ''}. {r.get('explanation') or ''} "
                        f"{send} It ends on \"Today's Daily is live at playgisthunt.com\".",
            'alt_cover': f"Daily word puzzle. {hook} Illustration: {ART_WORDS[art_name]}. Yesterday's Gist Daily.",
            'alt_still': f"Gist Hunt puzzle with its answer: {q['instruction']} {body} Cards: {card_list} Answer {ans} ({r.get('title') or ''}): "
                         f"{r.get('explanation') or ''} Illustration: {ART_WORDS[art_name]}. Today's Daily is live at playgisthunt.com."}
    json.dump(meta, open(os.path.join(a.out, 'meta.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps({k: meta[k] for k in ('day', 'season', 'art', 'goalName', 'number', 'answer', 'title', 'hook', 'send')}, ensure_ascii=False))

if __name__ == '__main__': main()
