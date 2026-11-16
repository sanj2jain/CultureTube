# CultureTube

A fast, minimal video library for **movement, music, arts, culture and the body**.

CultureTube collects good YouTube videos (documentaries, performances, tutorials, lectures and histories) and sorts them into a clear, browsable catalog. Think of it as a hand-tended library instead of an endless recommendation feed: you can go from *Dance → Indian Classical → Kathak* and find documentaries, performances and lessons, all in one place.

The website is plain HTML, CSS and JavaScript. It has no framework and no build step, so it runs anywhere you can host static files.

---

## What's in the library today

**6,723 videos** across five sections:

| Section | Videos |
|---|---|
| Dance | 3,329 |
| Music | 1,429 |
| Body & Mind | 830 |
| Culture & Anthropology | 591 |
| Arts | 544 |

Each section is split into subcategories (for example *Street & Club*, *Ballet & Concert*, *Latin American & Caribbean*) and then into individual topics such as *House dance*, *Flamenco* or *Haka*.

## What the site can do

- Browse by section, subcategory and topic, with video counts in the sidebar
- Search titles, channels and topics (press `/` to jump to the search box)
- Filter by type (documentary, performance, tutorial, lecture, history), by length, or show curated picks only
- Sort by curated-first, shuffle, longest, shortest or channel name
- Watch in a pop-up player (privacy-friendly `youtube-nocookie` embed) with related videos underneath
- Share any view: the current filters are saved in the page address
- Dark and light mode, keyboard shortcuts, and a layout that works on phones

---

## Try it on your computer

You need **Python 3** installed. Nothing else is required to view the site.

1. Open a terminal in this folder.
2. Start a small local web server:

   ```bash
   python3 -m http.server 8765 -d site
   ```

3. Open <http://localhost:8765> in your browser.

Press `Ctrl + C` in the terminal to stop the server.

## Rebuild the catalog

Only do this if you change the topics or the cleaning rules. You'll need [yt-dlp](https://github.com/yt-dlp/yt-dlp):

```bash
pip install yt-dlp
```

```bash
python3 build_catalog.py --per-query 6
```

```bash
python3 export_site_data.py
```

The first command searches YouTube for every topic and writes `data/videos.json`. The second turns that into the smaller `site/data.json` that the website reads.

Search results are saved in `data/cache/`, so rebuilding again after small changes is quick and doesn't contact YouTube for searches it already ran. Use `--workers` to control how many searches run at once (default 8). Keep it modest so YouTube isn't hit too hard.

---

## How it works

```
taxonomy.py ──► build_catalog.py ──► data/videos.json ──► export_site_data.py ──► site/data.json ──► website
                     ▲
                 cleaning.py  (+ your review decisions and blocklist)
```

1. **`taxonomy.py`** lists every section, subcategory and topic, along with the kinds of video to look for (documentary, performance, tutorial and so on).
2. **`build_catalog.py`** pulls in hand-picked seed playlists, then runs a YouTube search for each topic and video type. It removes Shorts, live streams and duplicates.
3. **`cleaning.py`** filters out junk: kids' content, film songs, lyric videos, trailers, "music for studying", fitness videos and similar. It also checks that each video is actually about its topic. Videos it isn't sure about go to a review list instead of the site.
4. **`export_site_data.py`** writes a compact copy of the catalog for the website.

### Your manual decisions always win

| File | What to put in it |
|---|---|
| `data/review.json` | Your keep/drop decision for a specific video, e.g. `"VIDEO_ID": "keep"` |
| `data/blocklist.txt` | Video IDs or channel names to always exclude, one per line |

After a build, two files tell you what happened:

| File | What it shows |
|---|---|
| `data/rejected.json` | Every video that was dropped, and why |
| `data/to_review.json` | Videos that still need a human to look at them |

## Project layout

```
CultureTube/
├── README.md              ← you are here
├── ROADMAP.md             ← the detailed build plan and checklist
├── taxonomy.py            ← sections, subcategories and topics
├── build_catalog.py       ← finds videos on YouTube
├── cleaning.py            ← junk filters, trusted/blocked channels, topic aliases
├── export_site_data.py    ← prepares data for the website
├── data/
│   ├── videos.json        ← the full catalog
│   ├── categories.json    ← category tree with counts
│   ├── review.json        ← your keep/drop decisions
│   ├── blocklist.txt      ← always-excluded videos/channels
│   ├── rejected.json      ← what was dropped and why
│   ├── to_review.json     ← what still needs a look
│   └── cache/             ← saved YouTube search results
└── site/
    ├── index.html
    ├── style.css
    ├── app.js
    └── data.json          ← the catalog the website loads
```

---

## Further steps

These are the next things to do, roughly in order. The full checklist lives in [ROADMAP.md](ROADMAP.md).

### 1. Put the site online
- [ ] Deploy the `site/` folder to a free static host: GitHub Pages, Cloudflare Pages or Netlify. On Netlify you can simply drag and drop the folder.
- [ ] Buy the domain `culturetube.org` and point it at the host.
- [ ] Add an **About** page: the curation philosophy, credits to the channels, and a contact for takedown requests.

### 2. Keep improving the catalog
- [ ] Work through `data/to_review.json` and record decisions in `data/review.json`.
- [ ] Fix known weak topics with hand-picked playlists, since search doesn't work well for them: **Sattriya** (search returns Manipuri films), **Kathakali** (returns Kathak lessons) and **Release technique** (returns generic tutorials).
- [ ] Pull in uploads and playlists from trusted channels (Films Division, Prasar Bharati, Darbar Festival, UNESCO, Jacob's Pillow, CrashCourse and others). These usually beat search results.
- [ ] Add more topics from your notes, such as African, Indian folk and Latin American dance forms, and notable pioneers and companies.
- [ ] Check for dead links once a month and remove videos that have become private or been deleted.

### 3. Add richer information to videos
- [ ] Fetch upload date, description, chapters, language and captions for each video.
- [ ] Add **region** and **country** fields, which would allow a "browse by world map" view.
- [ ] Write a short "why watch" note, era and level (intro / intermediate / deep) for the best ~300 videos.

### 4. Help people find the site
- [ ] Create a real page for each topic so search engines can index it. Today's views live after the `#` in the address, which search engines ignore.
- [ ] Add a `sitemap.xml` and link-preview tags (Open Graph) so shared links look good.

### 5. Features that make it special
- [ ] **Curated paths:** ordered watch-lists such as *Intro to Kathak (6 videos)* or *House dance: origins → steps → battles*.
- [ ] **Cross-links between sections,** e.g. Kathak dance ↔ Hindustani tabla ↔ Mughal court culture ↔ hip anatomy.
- [ ] **"Ask the library":** search inside video transcripts and answer questions with links to the exact moment in a video.
- [ ] **Automatic tagging** with an AI model to fix wrong categories and add style, region, era and level, with a person checking the uncertain ones.
- [ ] A **"Suggest a video"** form for the community.
- [ ] An RSS feed or weekly "new additions" page.

### 6. Housekeeping for the repository
- [ ] Add a `requirements.txt` (currently just `yt-dlp`) so setup is one command.
- [ ] Decide whether `data/cache/` (about 1,000 files) should stay in git or move to `.gitignore`. Keeping it makes rebuilds fast for anyone who clones the repo, but it adds to the repo's size.
- [ ] Choose a license for the code.
- [ ] Set up a GitHub Action that rebuilds the catalog weekly, opens a pull request with the changes, and deploys when it's merged.
- [ ] Add privacy-friendly, cookie-free analytics (Plausible or GoatCounter).

---

## A note on YouTube

CultureTube only **embeds** and **links to** videos; it never re-hosts them. Every video links back to its creator on YouTube. Please keep the build gentle on YouTube's servers by leaving the number of parallel workers low.
