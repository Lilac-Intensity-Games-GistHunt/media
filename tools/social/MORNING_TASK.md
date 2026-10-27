# Gist Hunt morning task: steps (reel-2)

The scheduled task "Gist Hunt puzzle posts (morning, Oct 28 – Jan 2)" reads this file from `main` and follows it.
Its own instructions hold the feed key and the hard rules (drafts only, never publish, never print the key, never touch the
Kwanzaa greeting or any post not listed here). Those rules win over anything in this file.

## STEP 0 - Is today a post day?
Get today's date in New York (`TZ=America/New_York date +%F`) and its UTC offset (`TZ=America/New_York date +%:z`).
Find the date in the CALENDAR. If it is not a row, reply only "Not a post day: <date>" and stop.

CALENDAR (post date | Daily it shows | expected season | Metricool uuids IG+TikTok / LinkedIn, or NEW = create both)
```
2026-10-28 | 2026-10-27 | Halloween | NEW
2026-10-30 | 2026-10-29 | Halloween | NEW
2026-11-01 | 2026-10-31 | Halloween (peak) or Clocks go back | NEW
2026-11-04 | 2026-11-03 | none | NEW
2026-11-06 | 2026-11-05 | none | NEW
2026-11-08 | 2026-11-07 | none | NEW
2026-11-11 | 2026-11-10 | none | NEW
2026-11-13 | 2026-11-12 | Thanksgiving | NEW
2026-11-15 | 2026-11-14 | Thanksgiving | NEW
2026-11-18 | 2026-11-17 | Thanksgiving | NEW
2026-11-21 | 2026-11-20 | Thanksgiving or Black Friday | NEW
2026-11-22 | 2026-11-21 | Thanksgiving or Black Friday | NEW
2026-11-25 | 2026-11-24 | Thanksgiving or Black Friday | NEW
2026-11-27 | 2026-11-26 | Thanksgiving (peak) | NEW
2026-11-28 | 2026-11-27 | Black Friday (peak) | NEW
2026-12-01 | 2026-11-30 | Black Friday / Cyber Monday | -8569509349988413453 / 4677228669795189117
2026-12-02 | 2026-12-01 | Black Friday | NEW
2026-12-05 | 2026-12-04 | Hanukkah | 5404090076457094699 / 7686230021308894376
2026-12-08 | 2026-12-07 | Hanukkah | 6232002692901127206 / -2839994431911673847
2026-12-09 | 2026-12-08 | Hanukkah | NEW
2026-12-11 | 2026-12-10 | Hanukkah or Christmas | -9143133268621179825 / -1774673869838464083
2026-12-15 | 2026-12-14 | Christmas | -6344507044962416261 / 7885143979503144718
2026-12-16 | 2026-12-15 | Christmas | NEW
2026-12-18 | 2026-12-17 | Christmas | -620664513017263262 / 3011829654373811755
2026-12-21 | 2026-12-20 | Christmas (caption may nod to the solstice, the longest night) | 6083866124695586174 / -7317059254601363607
2026-12-24 | 2026-12-23 | Christmas | 7630657393272114038 / 568129636945643400
2026-12-25 | 2026-12-24 (peak) | Christmas | -1703610410592679226 / 8350945525856684780
2026-12-30 | 2026-12-29 | New Year | NEW
2026-12-31 | 2026-12-30 | New Year | -514638667969443367 / -7675284212380841404
2027-01-02 | 2027-01-01 | New Year | NEW
```
The season in the feed (`question.seasonName`) wins over the "expected season" column, which is only a hint.
Never touch the Kwanzaa greeting (Dec 26, uuids 5235452468068761820 / 4881212155189151911) or any other post, including the
owner's own posts at other times on the same dates. All puzzle posts publish at 18:00 America/New_York on the post date.

## STEP 1 - Read the feed (only with the key, never in a URL)
Set `SOCIAL_FEED_KEY` inside the same shell command (never echo it), then
`curl -sS -o /tmp/feed.json -w '%{http_code}' -H "Authorization: Bearer $SOCIAL_FEED_KEY" https://playgisthunt.com/api/social/yesterday`
- `{"error":"Not found."}`: the key is wrong or the feed is switched off (`SOCIAL_FEED_ENABLED`). Change nothing; reply saying so.
- 404 with `"question":null`: nothing to post. On a row with uuids, leave the existing drafts exactly as they are (their greeting
  Reel can still go out); on a NEW date create nothing. Reply saying so, with the feed's message.
- 200 but `day` is not the Daily date in the CALENDAR: change nothing; reply with both dates.
- If playgisthunt.com can't be reached at all: reply that it must be in claude.ai Settings -> Capabilities allowed domains.

## STEP 2 - Write the send line, then render
Read the question in /tmp/feed.json and write the **send line**: one sentence, at most 90 characters, starting "Send this to",
naming someone from the question's own little world (e.g. "Send this to whoever shakes the dice for far too long.").
It must not give away the answer, name a real person or brand, or hold a link. Gist voice (STEP 4).

In the `media` clone (git user "Gist Hunt" <noreply@playgisthunt.com>):
`python3 -I tools/social/make_post.py /tmp/feed.json --out /tmp/post --expect-day <Daily date> --send "<send line>"`
It writes `reel.mp4` (14 s, 9:16), `cover.jpg` (the Reel's cover), `linkedin.jpg` (4:5 still with the answer) and `meta.json`
(hook, send, answer letters, alt texts). It refuses on any mismatch; if it fails, change nothing and report the error.

Look before uploading: extract frames at 0.0, 3, 7.8, 10.5 and 13.0 s (`ffmpeg -nostdin -ss T -i reel.mp4 -frames:v 1 f_T.png`)
and open them, `cover.jpg` and `linkedin.jpg` with the Read tool. Check:
- the challenge line and the whole board are on screen at 0.0 s; nothing is cut off or overlapping; text is readable;
- at 7.8 s the peach cards match `meta.json` "answer";
- 10.5 s shows the title, the explanation and the send line;
- nothing that matters sits in the top 250 px or the bottom 350 px (the art at the very top is fine);
- the art suits the season (Halloween pumpkin/scarecrow/mushroom; Clocks go back sleepy fox; Thanksgiving harvest friends;
  Black Friday squirrel; Hanukkah hedgehog; Christmas reindeer/gingerbread/tree; New Year toast; no season: autumn animals in
  Oct-Nov, winter animals in Dec-Jan).
If not, don't upload; report what's wrong.

## STEP 3 - Upload media
Copy to `<YYYY-MM>/<post date>_puzzle_reel.mp4`, `<YYYY-MM>/<post date>_puzzle_cover.jpg` and
`<YYYY-MM>/<post date>_puzzle_linkedin.jpg` in the clone (e.g. `2026-11/`), commit "Puzzle post <post date>",
`git pull --rebase`, push. Public URL: `https://raw.githubusercontent.com/Lilac-Intensity-Games-GistHunt/media/main/<path>`.

## STEP 4 - Captions
Voice: dry, warm and funny; small stakes, big feelings; clever before silly; never smug, never cruel; play it straight and
don't explain the joke. Kind and respectful about every holiday (Halloween spooky-silly, no gore; Thanksgiving never politics;
Black Friday never mocks real brands). No invented numbers, prizes, badges or claims ("90% get this wrong" is out);
"free" only about the Daily. Never give the answer in the Instagram/TikTok caption (the Reel reveals it).

**Hook (the caption's first line, at most 125 characters).** Write three candidates, each from a different angle:
a curious detail from the question's world, a playful challenge, a relatable moment. Each must be true to the question.
Keep the one a stranger would most need to finish reading; it is also the TikTok title (at most 90 characters, shorten if needed).

- **Instagram + TikTok text:** (1) the hook; (2) "Yesterday's Gist Daily, question N: <instruction> Comment your pick before
  the reveal."; (3) the send line; (4) "Today's Daily is live, and free, at playgisthunt.com." then "From Lilac Intensity Games.";
  (5) 4-5 hashtags: #GistHunt #DailyPuzzle #WordGames plus the season (#Halloween, #Thanksgiving, #Hanukkah, #Christmas,
  #NewYear) or #CozyGames.
- **First comment (IG + TikTok post):** a short no-peeking line with the reveal time, worded fresh each day, e.g.
  "No peeking. The answer lands at 0:07."
- **LinkedIn text (no link in the body; LinkedIn shows link posts to fewer people):** the hook; "Yesterday's Gist Daily asked:
  <instruction> The answer and why are in the picture."; one short line on what the question shows about careful reading;
  "Today's Daily is free to play. The link is in the first comment."; "From Lilac Intensity Games."; 3 hashtags
  (#GistHunt #ReadingComprehension #WordGames).
- **First comment (LinkedIn post):** "Today's Gist Daily: https://playgisthunt.com"

## STEP 5 - Metricool
Connector "Metricool Social Media Management"; blogId/brandId 7081870; timezone America/New_York. Every post stays
`draft:true` at `publicationDate {dateTime:"<post date>T18:00:00", timezone:"America/New_York"}`.
Use the date's own UTC offset from STEP 0 in fromDate/toDate.

Fields:
- IG + TikTok post: `media` [reel URL]; `videoThumbnailUrl` cover URL; `mediaAltText` [meta.alt_reel]; `firstCommentText`;
  `instagramData {type:"REEL", showReelOnFeed:true, isAiGenerated:true}`;
  `tiktokData {privacyOption:"PUBLIC_TO_EVERYONE", commercialContentOwnBrand:true, title:<TikTok title>, isAigc:true}`.
- LinkedIn post: `media` [linkedin.jpg URL]; `mediaAltText` [meta.alt_still]; `firstCommentText`;
  `linkedinData {previewIncluded:true, type:"post"}`. No `videoThumbnailUrl` (it is a picture, not a video).
- Never include `twitterData` (updates fail with it).

Rows with uuids: `getScheduledPosts(brandId 7081870, fromDate <post date>T00:00:00<offset>, toDate <post date>T23:59:59<offset>,
timezone America/New_York)`, find each post by its uuid (ids change on every update; use the id returned now), and
`updateScheduledPost(id, uuid, blogId, info)` where info is the FULL post as returned, changing only the fields above.
Keep `draft:true`, `autoPublish:true` and the providers as they are. If a uuid can't be found, don't create a duplicate; report it.

NEW rows: first call getScheduledPosts for that date; if an 18:00 puzzle draft for that date already exists (a re-run), update it
instead. Otherwise `createScheduledPost` twice (providers `[{network:"instagram"},{network:"tiktok"}]` with the Reel;
`[{network:"linkedin"}]` with the still), draft:true, 18:00.

If Metricool rejects `firstCommentText` or `videoThumbnailUrl` for a network, send the post again without that field and report it.
Afterwards call getScheduledPosts for the date again and confirm both puzzle posts show draft:true, 18:00 and the new media.

## STEP 6 - Reply (the owner reads this)
Post date; the Daily and question number; season and picture; the answer; the hook candidates and the one chosen; the send line;
the captions and first comments used; the plannerUrl links; anything skipped or wrong. Never include the key.
End with: "These stay drafts until about 12:07, when the noon task schedules them for 18:00. To hold them, edit them in Metricool
or tell Claude to stop the auto-approve."

(Since 27 Oct 2026 the owner has the posts automated: a second scheduled task, "Gist Hunt puzzle posts (noon auto-approve)",
checks today's two 18:00 drafts at 12:07 New York time and switches them to scheduled. This task still only ever makes drafts.)
