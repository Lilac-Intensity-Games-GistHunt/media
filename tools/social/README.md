# Gist Hunt social posts toolkit

`make_post.py` turns one answer from the social feed (`/api/social/yesterday`) into a "Yesterday's Gist Daily" post:
a 9:16 Reel for Instagram and TikTok (reel-2, 14 s), its cover, a 4:5 still for LinkedIn, and `meta.json` with alt texts.
It refuses to render if the feed has no question, the day is not the one expected, or the answer doesn't match the cards.

    python3 -I tools/social/make_post.py feed.json --out /tmp/post --expect-day 2026-12-14 --send "Send this to ..."

Reel-2 (27 Oct 2026): the challenge line (built from the playstyle and the pick) and the whole board on the first frame;
"Pause to solve", "Comment your pick" at 5.5 s, the reveal at 7 s; the answer, why and the send line at 9 s; the board again
with "Today's Daily is live · playgisthunt.com" at 12.4 s, looping into the first frame. Everything that matters stays between
y=250 and y=1570, clear of the Reels/TikTok buttons and caption. `cover.jpg` keeps its text inside the 3:4 profile-grid crop.

`MORNING_TASK.md` holds the scheduled morning task's steps and posting calendar. The task's own instructions hold the feed
key and the hard rules, and those rules win over this file. No secrets go in this repo.

- `art/`: the autumn and December illustrations with their words removed, on transparent edges. The season picks the art:
  Halloween → pumpkin, scarecrow or mushroom; Clocks go back → sleepy fox; Thanksgiving → harvest friends; Black Friday → squirrel;
  Hanukkah → hedgehog; Christmas → reindeer, gingerbread, tree friends or gingerbread + tree; New Year → the toast;
  no season → autumn animals (Sep–Nov) or winter animals (Dec–Feb). `kwanzaa_family.png` is kept but never picked.
  The art is AI-made, so posts carry the AI label.
- `fonts/`: Poppins (SIL Open Font License).
- Music: synthesised in the script, no licensed audio.
- `fixtures/`: a sample feed answer for testing.
