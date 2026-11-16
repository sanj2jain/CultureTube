"use strict";
const $ = (s) => document.querySelector(s);
const PAGE = 96;
const FACETS = [["", "All"], ["d", "Documentaries"], ["p", "Performances"], ["t", "Tutorials"], ["l", "Lectures"], ["h", "History"]];
const FACET_NAME = { d: "Documentary", p: "Performance", t: "Tutorial", l: "Lecture", h: "History" };

let DB, videos = [], view = [], shown = 0;
const state = { cat: "", sub: "", topic: "", q: "", f: "", d: "", sort: "curated", cur: false };

// ---------- theme ----------
const root = document.documentElement;
try { const t = localStorage.getItem("ct-theme"); if (t) root.dataset.theme = t; } catch {}
$("#themeBtn").onclick = () => {
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  try { localStorage.setItem("ct-theme", root.dataset.theme); } catch {}
};

// ---------- helpers ----------
const fmtDur = (s) => {
  if (!s) return "";
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${x}` : `${m}:${x}`;
};
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
let seed = Math.floor(Math.random() * 1e9);
const rnd = (i) => { let x = (i + 1) * 2654435761 ^ seed; x ^= x >>> 13; x = Math.imul(x, 1274126177); return (x ^ (x >>> 16)) >>> 0; };
const catColor = (ci) => `var(--c${ci % 5})`;

// ---------- URL state ----------
function readHash() {
  const p = new URLSearchParams(location.hash.slice(1));
  state.cat = p.get("c") || ""; state.sub = p.get("s") || ""; state.topic = p.get("t") || "";
  state.q = p.get("q") || ""; state.f = p.get("f") || ""; state.d = p.get("d") || "";
  state.sort = p.get("sort") || "curated"; state.cur = p.get("cur") === "1";
}
function writeHash() {
  const p = new URLSearchParams();
  for (const [k, key] of [["cat", "c"], ["sub", "s"], ["topic", "t"], ["q", "q"], ["f", "f"], ["d", "d"]]) if (state[k]) p.set(key, state[k]);
  if (state.sort !== "curated") p.set("sort", state.sort);
  if (state.cur) p.set("cur", "1");
  const h = p.toString();
  history.replaceState(null, "", h ? "#" + h : location.pathname + location.search);
}
function set(patch) { Object.assign(state, patch); writeHash(); render(); }

// ---------- load ----------
fetch("data.json", { cache: "no-cache" }).then((r) => r.json()).then((d) => {
  DB = d;
  videos = d.videos.map((r, i) => {
    const [id, title, channel, dur, ci, si, ti, facets, cur] = r;
    const [cat, sub] = d.subs[si].split("|");
    const topic = d.topics[ti];
    return { i, id, title, channel, dur, ci, cat, sub, topic, facets, cur, hay: norm(`${title} ${channel} ${topic} ${sub} ${cat}`) };
  });
  buildSide(); readHash(); syncControls(); render();
});

// ---------- sidebar ----------
function buildSide() {
  const tree = {};
  for (const v of videos) {
    tree[v.cat] ??= { n: 0, ci: v.ci, subs: {} };
    tree[v.cat].n++; tree[v.cat].subs[v.sub] = (tree[v.cat].subs[v.sub] || 0) + 1;
  }
  let h = `<button class="all" data-cat=""><span>All videos</span><span class="n">${videos.length.toLocaleString()}</span></button>`;
  for (const [cat, o] of Object.entries(tree)) {
    h += `<div class="cat" data-c="${esc(cat)}"><button data-cat="${esc(cat)}"><span><i class="dot" style="background:${catColor(o.ci)}"></i>${esc(cat)}</span><span class="n">${o.n}</span></button><div class="subs">`;
    for (const [sub, n] of Object.entries(o.subs).sort((a, b) => b[1] - a[1]))
      h += `<button data-cat="${esc(cat)}" data-sub="${esc(sub)}"><span>${esc(sub)}</span><span class="n">${n}</span></button>`;
    h += `</div></div>`;
  }
  h += `<div class="about">A hand-seeded library of ${videos.length.toLocaleString()} videos on movement, music, arts, culture and the body. All videos are embedded from YouTube and belong to their creators.</div>`;
  $("#side").innerHTML = h;
  $("#side").onclick = (e) => {
    const b = e.target.closest("button"); if (!b) return;
    document.body.classList.remove("menu");
    set({ cat: b.dataset.cat || "", sub: b.dataset.sub || "", topic: "" });
    scrollTo({ top: 0 });
  };
}
$("#menuBtn").onclick = () => document.body.classList.toggle("menu");
$("#scrim").onclick = () => document.body.classList.remove("menu");
$("#home").onclick = (e) => { e.preventDefault(); $("#q").value = ""; set({ cat: "", sub: "", topic: "", q: "", f: "" }); };

// ---------- controls ----------
$("#facetChips").innerHTML = FACETS.map(([k, v]) => `<button class="chip" data-f="${k}">${v}</button>`).join("");
$("#facetChips").onclick = (e) => { const b = e.target.closest("[data-f]"); if (b) set({ f: b.dataset.f }); };
$("#dur").onchange = (e) => set({ d: e.target.value });
$("#sort").onchange = (e) => { if (e.target.value === "shuffle") seed = Math.floor(Math.random() * 1e9); set({ sort: e.target.value }); };
$("#curOnly").onchange = (e) => set({ cur: e.target.checked });
let qt;
$("#q").oninput = (e) => { clearTimeout(qt); qt = setTimeout(() => set({ q: e.target.value.trim() }), 120); };
addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== $("#q") && !$("#player").open) { e.preventDefault(); $("#q").focus(); }
});
addEventListener("hashchange", () => { closeVideo(); readHash(); syncControls(); render(); });

function syncControls() {
  $("#q").value = state.q; $("#dur").value = state.d; $("#sort").value = state.sort; $("#curOnly").checked = state.cur;
}

// ---------- filtering ----------
const DUR = { s: [0, 600], m: [600, 1800], l: [1800, 3600], x: [3600, 1e9] };
function filtered(ignoreTopic = false) {
  const toks = norm(state.q).split(/\s+/).filter(Boolean);
  return videos.filter((v) =>
    (!state.cat || v.cat === state.cat) &&
    (!state.sub || v.sub === state.sub) &&
    (ignoreTopic || !state.topic || v.topic === state.topic) &&
    (!state.f || v.facets.includes(state.f)) &&
    (!state.cur || v.cur) &&
    (!state.d || (v.dur >= DUR[state.d][0] && v.dur < DUR[state.d][1])) &&
    toks.every((t) => v.hay.includes(t)));
}
function sorted(list) {
  const s = state.sort;
  const by = {
    curated: (a, b) => b.cur - a.cur || rnd(a.i) - rnd(b.i),
    shuffle: (a, b) => rnd(a.i) - rnd(b.i),
    long: (a, b) => b.dur - a.dur,
    short: (a, b) => (a.dur || 1e9) - (b.dur || 1e9),
    channel: (a, b) => a.channel.localeCompare(b.channel) || a.title.localeCompare(b.title),
  }[s];
  if (state.q && s === "curated") {   // with a query, rank title matches first
    const t = norm(state.q);
    return list.sort((a, b) => (norm(b.title).includes(t) - norm(a.title).includes(t)) || by(a, b));
  }
  return list.sort(by);
}

// ---------- render ----------
function render() {
  // sidebar highlight
  document.querySelectorAll("#side button").forEach((b) => {
    const on = (b.dataset.cat || "") === state.cat && (b.dataset.sub || "") === state.sub;
    b.classList.toggle("on", on);
  });
  document.querySelectorAll("#side .cat").forEach((c) => c.classList.toggle("open", c.dataset.c === state.cat));
  document.querySelectorAll("#facetChips .chip").forEach((c) => c.classList.toggle("on", c.dataset.f === state.f));

  // crumbs
  const parts = [`<a data-k="all">All</a>`];
  if (state.cat) parts.push(`<a data-k="cat">${esc(state.cat)}</a>`);
  if (state.sub) parts.push(`<a data-k="sub">${esc(state.sub)}</a>`);
  if (state.topic) parts.push(`<span>${esc(state.topic)}</span>`);
  $("#crumbs").innerHTML = parts.join(`<span class="sep">/</span>`);
  $("#crumbs").onclick = (e) => {
    const k = e.target.dataset.k;
    if (k === "all") set({ cat: "", sub: "", topic: "" });
    if (k === "cat") set({ sub: "", topic: "" });
    if (k === "sub") set({ topic: "" });
  };

  // topic chips (only inside a category)
  const tEl = $("#topics");
  if (state.cat) {
    const counts = {};
    for (const v of filtered(true)) counts[v.topic] = (counts[v.topic] || 0) + 1;
    const list = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    tEl.innerHTML = list.map(([t, n]) => `<button class="chip${t === state.topic ? " on" : ""}" data-t="${esc(t)}">${esc(t)} <span style="opacity:.55">${n}</span></button>`).join("")
      + (list.length > 14 ? `<button class="chip more" data-more>${tEl.classList.contains("expanded") ? "Show less" : "Show all " + list.length}</button>` : "");
    tEl.hidden = !list.length;
  } else { tEl.innerHTML = ""; tEl.hidden = true; }
  tEl.onclick = (e) => {
    if (e.target.closest("[data-more]")) { tEl.classList.toggle("expanded"); render(); return; }
    const b = e.target.closest("[data-t]"); if (b) set({ topic: b.dataset.t === state.topic ? "" : b.dataset.t });
  };

  view = sorted(filtered());
  $("#count").textContent = `${view.length.toLocaleString()} video${view.length === 1 ? "" : "s"}`;
  $("#empty").hidden = view.length > 0;
  $("#grid").innerHTML = ""; shown = 0; more();
  document.title = (state.topic || state.sub || state.cat || "") ? `${state.topic || state.sub || state.cat} · CultureTube` : "CultureTube";
}

function card(v) {
  return `<div class="card" data-id="${v.id}" tabindex="0" style="--cat:${catColor(v.ci)}">
    <div class="thumb"><img loading="lazy" src="https://i.ytimg.com/vi/${v.id}/mqdefault.jpg" alt="">
      ${v.dur ? `<span class="dur">${fmtDur(v.dur)}</span>` : ""}${v.cur ? `<span class="star">CURATED</span>` : ""}</div>
    <h3>${esc(v.title)}</h3>
    <div class="meta">${esc(v.channel)}</div>
    <div class="meta"><span class="tag">${esc(v.topic)}</span>${v.facets ? " · " + FACET_NAME[v.facets[0]] : ""}</div>
  </div>`;
}
function more() {
  if (shown >= view.length) return;
  $("#grid").insertAdjacentHTML("beforeend", view.slice(shown, shown + PAGE).map(card).join(""));
  shown += PAGE;
}
new IntersectionObserver((es) => es[0].isIntersecting && more(), { rootMargin: "1200px" }).observe($("#sentinel"));

// ---------- player ----------
const byId = () => Object.fromEntries(videos.map((v) => [v.id, v]));
let ID;
function openVideo(id) {
  ID ??= byId();
  const v = ID[id]; if (!v) return;
  $("#frame").src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
  $("#pTitle").textContent = v.title;
  $("#pSub").textContent = `${v.channel} · ${v.cat} / ${v.sub} / ${v.topic}${v.dur ? " · " + fmtDur(v.dur) : ""}`;
  $("#pYT").href = `https://www.youtube.com/watch?v=${id}`;
  const rel = videos.filter((x) => x.topic === v.topic && x.id !== id).sort((a, b) => rnd(a.i) - rnd(b.i)).slice(0, 8);
  $("#pRelated").innerHTML = rel.length ? `<div class="related-title">More in ${esc(v.topic)}</div>` + rel.map(card).join("") : "";
  if (!$("#player").open) $("#player").showModal();
  $("#player .player-inner").scrollTop = 0;
}
function closeVideo() { $("#frame").src = "about:blank"; if ($("#player").open) $("#player").close(); }
document.addEventListener("click", (e) => { const c = e.target.closest(".card"); if (c) openVideo(c.dataset.id); });
document.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.classList?.contains("card")) openVideo(e.target.dataset.id); });
$("#pClose").onclick = closeVideo;
$("#player").addEventListener("close", () => { $("#frame").src = "about:blank"; });
$("#player").addEventListener("click", (e) => { if (e.target === $("#player")) closeVideo(); });
