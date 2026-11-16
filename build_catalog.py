"""Build data/videos.json from (1) seed playlists/videos in your vault and
(2) searches generated from taxonomy.py. Requires: pip install yt-dlp

Usage:  python build_catalog.py [--per-query 10] [--target 6000]
Search results are cached in data/cache/ so reruns are cheap."""
import argparse, hashlib, json, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from taxonomy import TAXONOMY, FACETS
import cleaning

HERE = Path(__file__).parent
DATA = HERE / "data"; CACHE = DATA / "cache"; CACHE.mkdir(parents=True, exist_ok=True)
YTDLP = [sys.executable, "-m", "yt_dlp"]

# Seeds from CultureTube.org.md and other vault notes: (url, category, subcategory, topic, label)
SEEDS = [
  ("https://www.youtube.com/playlist?list=PLrfQuiP4c1KWmK_7Q9n4jZql6F3si31hL", "Dance", "Street & Club", "Choreography", "Tim Milgram"),
  ("https://www.youtube.com/playlist?list=PLibQWLsmnSqGgcDo-95UIGp9EiF5vz6yl", "Dance", "Street & Club", "Choreography", "Urban Dance Camp"),
  ("https://www.youtube.com/playlist?list=PLOT99LmkLIkkNiPspscOHhLcLuS5Cbipb", "Dance", "Street & Club", "Tutorials", "Steezy Studio"),
  ("https://www.youtube.com/playlist?list=PLqtVCj5iilH6BnMc4hIRzVyJ_wtPgky9B", "Dance", "Indian Classical", "Kathak", "Learn Kathak with Maharaj ji"),
  ("https://www.youtube.com/playlist?list=PLG5S0pMf2_ZgK3N51-bVr-oJq7nQ2jsX7", "Dance", "Street & Club", "Choreography", "Prithvi FamousDance"),
  ("https://www.youtube.com/playlist?list=PLZelnKT8VJwxRSmbrnmjgO5037kimdpDC", "Dance", "Street & Club", "House dance", "House dance documentaries"),
  ("https://www.youtube.com/playlist?list=PLB9CAA2877007AC02", "Dance", "Street & Club", "House dance", "House dance steps"),
  ("https://www.youtube.com/playlist?list=PLZy_yosa6uXRMYx2nctvFkYhyNPXtWPxW", "Dance", "Indian Classical", "Khajuraho Dance Festival", "Khajuraho Dance Festival"),
  ("https://www.youtube.com/playlist?list=PLqR22EoucCyccs5J639SCefaM7mD9dMSz", "Music", "Theory & Craft", "Musical instruments of the world", "Instrument Guides"),
  ("https://www.youtube.com/playlist?list=PLPa_jYZmA6i7rYAvxkc1SlWpOoGfqr0t-", "Culture & Anthropology", "Anthropology", "Transcripts", "Playlist for Transcripts"),
  ("https://www.youtube.com/playlist?list=PLN4qWiJRKcbndqojrU2GVWSwWTbWeooH1", "Arts", "Film & Notation", "Labanotation", "Labanotation (vault)"),
  ("https://www.youtube.com/playlist?list=PLN4qWiJRKcblfzBNp-9vbIAuMIIacSl2l", "Dance", "Ballet & Concert", "Contemporary dance", "Contemporary & Modern (vault)"),
  ("https://www.youtube.com/playlist?list=PLwpackPwhK5Pk1_P0oCyo_SKaK51EhiwQ", "Body & Mind", "Anatomy & Physiology", "Functional anatomy", "Anatomy Basics (vault)"),
  ("https://www.youtube.com/playlist?list=PLekhl8ZQS2PbLtpx03GUbTH5CKqPZA2r_", "Body & Mind", "Anatomy & Physiology", "Functional anatomy", "Anatomy Basics (vault)"),
  ("https://www.youtube.com/playlist?list=PLUl4u3cNGP60IKRN_pFptIBxeiMc0MCJP", "Body & Mind", "Anatomy & Physiology", "Functional anatomy", "Anatomy Basics (vault)"),
  ("https://www.youtube.com/playlist?list=PL44ABC9278E2EE706", "Body & Mind", "Anatomy & Physiology", "Functional anatomy", "Anatomy Basics (vault)"),
  ("https://www.youtube.com/playlist?list=PL8dPuuaLjXtOAKed_MxxWBNaPno5h3Zs8", "Body & Mind", "Anatomy & Physiology", "Functional anatomy", "Crash Course A&P (vault)"),
]
SEED_VIDEOS = [  # single videos: (id, category, subcategory, topic, label)
  ("fzg3tneMvTA", "Dance", "Street & Club", "Featured", "CultureTube.org"),
  ("diU70KshcjA", "Dance", "Street & Club", "After Ever After", "CultureTube.org"),
  ("mIQr_TrFTUk", "Dance", "Street & Club", "After Ever After", "CultureTube.org"),
  ("z7EbH8HZ6UY", "Dance", "Street & Club", "After Ever After", "CultureTube.org"),
  ("TKZyeShtnNk", "Culture & Anthropology", "Histories & Movements", "Come As You Are", "CultureTube.org"),
  ("WLsOZ6Ijndg", "Music", "Electronic & Club", "Psytrance", "Dark Psytrance & Techno (vault)"),
  ("nCBWzNQ-1UM", "Music", "Electronic & Club", "Psytrance", "Dark Psytrance & Techno (vault)"),
  ("kENBz2xbIEU", "Dance", "Jazz & Social", "Choreography", "Homework (vault)"),
] + [(v, "Dance", "Ballet & Concert", "Dance research", "Dance Research References (vault)") for v in
     ["KhSXr6DW6bE", "bYa-YFwK1Gc", "otIKEYcHsps", "a4YyS0cuJEw", "s6i4WTWY1sU", "G0MYajFs3UQ", "qRn_pozXbWA", "nj-ffuoHvZA", "oCX0Hvt06BI"]]

SEED_PLAYLIST_CAP = 300
MIN_DURATION = 90          # drop Shorts / clips
BAD_TITLE = re.compile(r"#shorts|\bshorts\b|reaction|prank|tiktok compilation", re.I)

def ytdlp_json(target, cache_key):
    f = CACHE / (hashlib.md5(cache_key.encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    for attempt in range(3):
        p = subprocess.run(YTDLP + ["--flat-playlist", "-J", "--no-warnings", target],
                           capture_output=True, text=True, timeout=180)
        if p.returncode == 0 and p.stdout.strip():
            d = json.loads(p.stdout)
            f.write_text(json.dumps(d))
            return d
        time.sleep(2 + attempt * 3)
    print("  FAILED:", cache_key, p.stderr.strip()[:200], file=sys.stderr)
    return None

def make(e, cat, sub, topic, source, facet=None, rank=None):
    vid = e.get("id")
    return {
        "id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": e.get("title"),
        "channel": e.get("channel") or e.get("uploader"),
        "channel_id": e.get("channel_id"),
        "duration": int(e["duration"]) if e.get("duration") else None,
        "views": e.get("view_count"),
        "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
        "category": cat, "subcategory": sub, "topic": topic,
        "tags": sorted({t for t in [facet, topic.lower()] if t}),
        "source": source, "search_rank": rank,
    }

def ok(e):
    if not e or not e.get("id") or len(e["id"]) != 11: return False
    if e.get("title") in (None, "[Private video]", "[Deleted video]"): return False
    if e.get("live_status") in ("is_live", "is_upcoming"): return False
    if e.get("duration") and e["duration"] < MIN_DURATION: return False
    if BAD_TITLE.search(e.get("title", "")): return False
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-query", type=int, default=10)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    videos, order = {}, []
    rejected, to_review = [], []
    seen_titles = {}
    def judge(e, cat, sub, topic, source, curated=False):
        keep, why = cleaning.verdict(e, topic, curated, cat)
        if keep:
            nt = re.sub(r"[^a-z0-9]+", "", (e.get("title") or "").lower())
            if nt in seen_titles and seen_titles[nt] != e["id"] and not curated:
                keep, why = False, "duplicate-title"
            else:
                seen_titles.setdefault(nt, e["id"])
        if not keep:
            row = {"id": e["id"], "title": e.get("title"), "channel": e.get("channel") or e.get("uploader"),
                   "category": cat, "subcategory": sub, "topic": topic, "reason": why, "source": source}
            (to_review if why == "unreviewed" else rejected).append(row)
        return keep
    def add(v, extra_tags=()):
        if v["id"] in videos:   # merge: keep first placement, accumulate tags/topics
            old = videos[v["id"]]
            old["tags"] = sorted(set(old["tags"]) | set(v["tags"]) | set(extra_tags))
            alt = f'{v["category"]} / {v["subcategory"]} / {v["topic"]}'
            if alt != f'{old["category"]} / {old["subcategory"]} / {old["topic"]}':
                old.setdefault("also_in", [])
                if alt not in old["also_in"]: old["also_in"].append(alt)
            return
        videos[v["id"]] = v; order.append(v["id"])

    # 1) seeds
    print("Seeds…")
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(lambda s: ytdlp_json(s[0], s[0]), SEEDS))
    for (url, cat, sub, topic, label), d in zip(SEEDS, res):
        ents = [e for e in (d or {}).get("entries", []) if ok(e)][:SEED_PLAYLIST_CAP]
        print(f"  {label}: {len(ents)}")
        for e in ents:
            if not judge(e, cat, sub, topic, f"seed:{label}", curated=True): continue
            v = make(e, cat, sub, topic, f"seed:{label}"); v["tags"].append("curated"); add(v)
    seed_ids = [s[0] for s in SEED_VIDEOS]
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(lambda i: ytdlp_json(f"https://www.youtube.com/watch?v={i}", "v:" + i), seed_ids))
    for (vid, cat, sub, topic, label), d in zip(SEED_VIDEOS, res):
        if d:
            d["id"] = vid
            if not judge(d, cat, sub, topic, f"seed:{label}", curated=True): continue
            v = make(d, cat, sub, topic, f"seed:{label}"); v["tags"].append("curated"); add(v)

    # 2) taxonomy searches
    jobs = []
    for cat, subs in TAXONOMY.items():
        facets = subs["facets"]
        for sub, topics in subs.items():
            if sub == "facets": continue
            for t in topics:
                for fc in facets:
                    jobs.append((cat, sub, t, fc, FACETS[fc].format(t=t)))
    print(f"Searches: {len(jobs)} queries")
    n_fetch = 15   # fixed so the cache is reused whatever --per-query is
    def run(j):
        q = j[4]
        return ytdlp_json(f"ytsearch{n_fetch}:{q}", f"s{n_fetch}:{q}")
    done = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for j, d in zip(jobs, ex.map(run, jobs)):
            done += 1
            if done % 50 == 0: print(f"  {done}/{len(jobs)}  videos={len(videos)}", flush=True)
            cat, sub, t, fc, q = j
            ents = [e for e in (d or {}).get("entries", []) if ok(e)]
            kept = 0
            for r, e in enumerate(ents):
                if kept >= a.per_query: break
                if e["id"] in videos:          # already placed: just merge tags, doesn't use a slot
                    add(make(e, cat, sub, t, f"search:{q}", fc, r + 1)); continue
                if judge(e, cat, sub, t, f"search:{q}"):
                    add(make(e, cat, sub, t, f"search:{q}", fc, r + 1)); kept += 1

    out = [videos[i] for i in order]
    (DATA / "videos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    # compact index for the website: categories -> subcategories -> topics -> counts
    idx = {}
    for v in out:
        idx.setdefault(v["category"], {}).setdefault(v["subcategory"], {}).setdefault(v["topic"], 0)
        idx[v["category"]][v["subcategory"]][v["topic"]] += 1
    (DATA / "categories.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    (DATA / "rejected.json").write_text(json.dumps(rejected, ensure_ascii=False, indent=1))
    (DATA / "to_review.json").write_text(json.dumps(to_review, ensure_ascii=False, indent=1))
    from collections import Counter
    print("Rejected:", dict(Counter(r["reason"].split(":")[0] for r in rejected)), "| unreviewed:", len(to_review))
    print(f"Wrote {len(out)} videos")

if __name__ == "__main__":
    main()
