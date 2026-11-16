"""Trim data/videos.json into site/data.json (compact arrays) for the static site."""
import json
from pathlib import Path
HERE = Path(__file__).parent
vids = json.loads((HERE / "data/videos.json").read_text())
FACETS = ["doc", "perf", "learn", "hist", "lec"]
FCODE = {"doc": "d", "perf": "p", "learn": "t", "hist": "h", "lec": "l"}
cats, subs, topics = [], [], []
def ix(lst, x):
    if x not in lst: lst.append(x)
    return lst.index(x)
rows = []
for v in vids:
    f = [x for x in FACETS if x in v["tags"]]
    rows.append([v["id"], v["title"], v["channel"] or "", v["duration"] or 0,
                 ix(cats, v["category"]), ix(subs, v["category"] + "|" + v["subcategory"]),
                 ix(topics, v["topic"]), "".join(FCODE[x] for x in f), 1 if "curated" in v["tags"] else 0])
out = {"fields": ["id", "title", "channel", "duration", "cat", "sub", "topic", "facets", "curated"],
       "cats": cats, "subs": subs, "topics": topics, "videos": rows}
(HERE / "site/data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(len(rows), "videos ->", (HERE / "site/data.json").stat().st_size // 1024, "KB")
