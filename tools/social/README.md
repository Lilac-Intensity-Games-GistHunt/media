# Gist Hunt social posts toolkit

`make_post.py` turns one answer from the social feed (`/api/social/yesterday`) into a "Yesterday's Gist Daily" post:
a 9:16 Reel for Instagram and TikTok, a 4:5 still for LinkedIn, and `meta.json` with alt texts. It refuses to render
if the feed has no question, the day is not the one expected, or the answer doesn't match the cards.

    python3 -I tools/social/make_post.py feed.json --out /tmp/post --expect-day 2026-12-14

- `art/`: the December illustrations with their words removed, on transparent edges. The season picks the art:
  Hanukkah → hedgehog; Christmas → reindeer, gingerbread, tree friends or gingerbread + tree; New Year → the toast;
  no season → the winter animals (polar bears, owl, fox). `kwanzaa_family.png` is kept but never picked.
  The art is AI-made, so posts carry the AI label.
- `fonts/`: Poppins (SIL Open Font License).
- Music: synthesised in the script, no licensed audio.
- `fixtures/`: a sample feed answer for testing.
