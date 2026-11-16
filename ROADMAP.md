# CultureTube.org — Build Roadmap

Goal: a fast, minimal, static "video library" site (in the spirit of HackerTube) for movement, music,
arts, culture/anthropology and the body. The data lives in `data/videos.json`; the site is a static
front-end over it.

## Files in this folder

| File | What it is |
|---|---|
| `taxonomy.py` | Categories → subcategories → topics, plus the search "facets" (documentary, performance, tutorial, lecture). Edit this to add or remove styles. |
| `build_catalog.py` | Pulls your seed playlists/videos and runs one YouTube search per topic × facet with yt-dlp, filters out Shorts/live/junk, dedupes, and writes the JSON. Results are cached in `data/cache/`, so reruns are cheap. |
| `data/videos.json` | The catalog: one object per video (`id, url, title, channel, duration, views, thumbnail, category, subcategory, topic, tags, source, also_in`). |
| `data/categories.json` | Category tree with counts, used for site navigation. |

| `cleaning.py` | Junk rules, blocked/trusted channels and topic aliases, used by the build. |
| `data/review.json`, `data/blocklist.txt` | Your manual keep/drop decisions and exclusions (these win over the rules). |
| `data/rejected.json`, `data/to_review.json` | Build outputs: what was dropped and why, and what still needs a human look. |
| `export_site_data.py` | Writes the compact `site/data.json` for the website. |

Rebuild: `pip install yt-dlp && python build_catalog.py --per-query 6 && python export_site_data.py`
(Each search's 15 results are cached, so changing `--per-query` (max 15) or the rules doesn't hit YouTube again.)

---

## Phase 1 — Clean the data (most of the quality comes from this phase)

- [x] **Cleanup pass (2026-11-16).** `cleaning.py` now runs inside the build. Catalog went from 7,118 noisy videos to **6,723 cleaned** (798 removed, 403 better ones backfilled from the cached results).
  - Junk title rules: kids content, film songs, lyric videos, trailers and teasers, TikTok, Roblox, "study/focus/sleep" background music, fitness and weight loss. Official music videos are dropped outside the Music section.
  - Blocked channels (nursery-rhyme channels, Bollywood labels…), a `data/blocklist.txt` of IDs, and near-duplicate titles.
  - Relevance check: the title or channel must mention the topic or one of its `ALIASES`. Otherwise the video goes to `data/to_review.json`.
  - Manual review: 1,115 off-keyword videos were read and judged. The decisions live in `data/review.json` (792 keep / 323 drop) and override all other rules.
  - All dropped videos, with reasons, are in `data/rejected.json`.
- [ ] **Keep reviewing.** After any taxonomy change, run the build and then read `data/to_review.json`. Add `"id": "keep"|"drop"` to `data/review.json` and rebuild. Known weak spots: Sattriya (YouTube search returns Manipuri films), Kathakali (returns Kathak lessons), Release technique (returns generic tutorials). These need curated seed playlists instead of search.
- [ ] **Allowlist trusted channels** (a starter list is in `cleaning.TRUSTED_CHANNELS`: Films Division, Prasar Bharati, darbarfestival, UNESCO, Red Bull, Jacob's Pillow, CrashCourse…). Next, pull *their* uploads and playlists in as seeds; they usually beat search results.
- [ ] **Add the rest of your vault as seeds.** Notes like *African Dance Forms*, *Indian Folk Dances*, *Latin American Dance Forms*, *Notable Pioneers and Companies* list styles and artists that could become topics. `00_Dance styles of the world.md` alone could add hundreds of country-level folk-dance topics.
- [ ] **Enrich metadata** for the final set (`yt-dlp -J <url>` without `--flat-playlist`): upload date, description, chapters, language, and whether captions exist. Do this in batches and cache it.
- [ ] **Dead-link check** monthly. Re-run the build and drop videos that are now private or deleted.
- [ ] **Hand-written fields** for the best ~300 videos: a one-line "why watch" note, region/country, era, and level (intro / intermediate / deep).
- [ ] Add `region` and `country` fields so the site can have a world map / browse-by-place view.

## Phase 2 — Minimum viable site ✅ (built in `site/`)

Run locally: `python export_site_data.py && python3 -m http.server 8765 -d site`, then open http://localhost:8765

- [x] Stack: plain static site, `site/index.html` + `style.css` + `app.js` (no framework, no build step). Data is `site/data.json` (~810 KB compact arrays), produced by `export_site_data.py`.
- [x] **Home page:** dense thumbnail grid, sidebar with 5 categories → subcategories with counts, infinite scroll.
- [x] **Category / topic views:** breadcrumbs plus topic chips. State lives in the URL hash (`#c=Dance&s=Indian+Classical&t=Kathak&f=d`), so every view is shareable.
- [x] **Video card:** thumbnail, duration, CURATED badge, title, channel, topic and type.
- [x] **Watch:** `youtube-nocookie` embed in a modal with "Open on YouTube" and 8 related videos from the same topic.
- [x] **Client-side search** (accent-insensitive, multi-word AND over title/channel/topic/category; `/` focuses it).
- [x] Filters: type chips (Documentaries / Performances / Tutorials / Lectures / History), length buckets, curated only.
- [x] Sort: curated first, shuffle, longest, shortest, channel A–Z.
- [x] Dark/light mode (follows system, toggle remembered), keyboard (Enter opens a card, Esc closes), phone layout with slide-out menu.
- [ ] Deploy: push `site/` to GitHub Pages / Cloudflare Pages / Netlify (drag-and-drop the folder works on Netlify).
- [ ] Buy and point the domain `culturetube.org`.
- [ ] SEO: pre-render a static page per subcategory/topic (the hash routes aren't indexed), add `sitemap.xml` and Open Graph tags.

## Phase 3 — What makes it special

- [ ] **Curated "paths":** ordered watch-lists such as *Intro to Kathak (6 videos)*, *House dance: origins → steps → battles*, or *Anatomy for dancers*. Store them as `data/paths/*.json`.
- [ ] **Cross-links between sections:** show related videos from other categories on each topic page, e.g. Kathak dance ↔ Hindustani tabla ↔ Mughal court culture ↔ hip anatomy. Use the `also_in` field plus a hand-made `related.json`.
- [ ] **Browse by world map** using the `region`/`country` fields.
- [ ] **Transcripts + semantic search (fits the MovementRAG idea):** fetch captions with `yt-dlp --write-auto-subs --skip-download`, embed them, and add "ask the library" search or Q&A that cites timestamps.
- [ ] **Auto-classification:** run titles and descriptions through an LLM to fix wrong categories, add tags (style, region, era, level), and flag off-topic results. Have a person review the low-confidence ones.
- [ ] **"Submit a video"** form (a GitHub issue template or Google Form) for community suggestions, moderated by you.
- [ ] RSS feed / weekly "new additions" page.

## Phase 4 — Operations

- [ ] Put this folder in a git repo. CI (GitHub Actions) runs the build weekly, opens a PR with the diff, and deploys on merge.
- [ ] Analytics without cookies (Plausible / GoatCounter).
- [ ] An About page covering the curation philosophy, credits to channels, and a takedown contact.
- [ ] Respect YouTube ToS: embed only, link back to creators, don't scrape at aggressive rates (keep `--workers` modest).
