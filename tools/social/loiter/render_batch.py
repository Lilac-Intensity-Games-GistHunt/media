import json, os, sys, subprocess
import loiter_ads as L
from PIL import Image
FIELDS = [(L.PINK, None), (L.YEL, L.PAPER), (L.LILAC, None), (L.MINT, None)]
def prep(i, c):
    f, card = FIELDS[i % 4]
    d = dict(id=f"w23-{i+1}", q=c['q'], t=c.get('t'), l=c['l'], r=c['r'], field=f)
    if card: d['card'] = card
    return d
def render_one(i):
    c = prep(i, json.load(open('week23_cards.json'))[i])
    outdir = os.path.join(L.HERE, 'out23', f'c{i+1:02d}'); os.makedirs(outdir, exist_ok=True)
    final = os.path.join(outdir, 'reel.mp4')
    if os.path.exists(final): return i
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{L.W}x{L.H}", "-r", str(L.FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(outdir, 'v.mp4')], stdin=subprocess.PIPE)
    for f in range(int(L.T_TOTAL * L.FPS)): p.stdin.write(L.frame(c, f / L.FPS).convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0
    L.build_audio(os.path.join(outdir, 'a.wav'), seed=i + 11)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, 'v.mp4'), "-i", os.path.join(outdir, 'a.wav'), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
                    os.path.join(outdir, 'tmp.mp4')], check=True)
    os.replace(os.path.join(outdir, 'tmp.mp4'), final)
    L.frame(c, 6.6).convert("RGB").save(os.path.join(outdir, 'cover.jpg'), quality=90)
    os.remove(os.path.join(outdir, 'v.mp4'))
    print('done', i + 1, flush=True); return i
if __name__ == "__main__":
    import concurrent.futures as cf
    n = len(json.load(open('week23_cards.json')))
    with cf.ProcessPoolExecutor(2) as ex: list(ex.map(render_one, range(n)))
    print('ALL DONE', flush=True)
