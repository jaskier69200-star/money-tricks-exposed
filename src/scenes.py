"""Choose one background clip per scene: the AI clip library or a real Pixabay video, alternating.
A real clip is used only when its tags hold every word of the line's search (or of a pair of them): a loose match
once put a pond behind "popcorn". When nothing matches, the line's library category does the shot.

- assets/library/: clips made once on the owner's PC (Z-Image image + DepthFlow 3D motion, 6 s, 1080x1920),
  listed in library.json by category. The script writer names a category per line. A line whose search words
  name its category (its name or tags) gets library and real shots in turn; one that doesn't (an anchor, a maze)
  tries real footage first, its strong words alone too.
- With no library (empty assets/library), every shot is real footage (pick_stock_only) with on-theme fallbacks.
- Pixabay: real footage searched with the line's "search" words. The first test showed loose matching is not enough
  ("man pull ups gym" gave hands counting money; "man" matched): generic words don't count, the subject must match.
  Each chosen segment is cut to 1080x1920, given the cinema grade (dark, teal and orange, vignette) so it blends with
  the library, and rejected if it looks empty (a grey frame slipped through once).
- Recently shown clips are skipped (state.json → "recent_clips"), so a viewer doesn't see the same shot twice in a row.
"""
import math
import random
import subprocess
from itertools import combinations

from common import ROOT, STATE_FILE, find_ffmpeg, load_config, load_json, save_json
import footage

LIBRARY = ROOT / "assets" / "library"
RECENT_KEEP = 160   # about 5 days of videos
MAX_SHOT = 5.8      # a library clip lasts 6 s: longer lines get two shots
GENERIC = {"man", "men", "woma", "wome", "guy", "pers", "peop", "male", "huma", "some"}  # word roots that match anything
DEFAULT_GRADE = ("eq=brightness=-0.07:contrast=1.08:saturation=0.8,"
                 "colorbalance=rs=-0.05:bs=0.06:rh=0.06:bh=-0.05,vignette=angle=PI/4")


def library():
    return load_json(LIBRARY / "library.json", {"clips": []})["clips"]


def recent():
    return load_json(STATE_FILE, {}).get("recent_clips", [])


def remember(ids):
    """Called once the video really reached Zernio (make_video saves the ids in info.json)."""
    state = load_json(STATE_FILE, {})
    state["recent_clips"] = (state.get("recent_clips", []) + list(ids))[-RECENT_KEEP:]
    save_json(STATE_FILE, state)


def category_roots():
    """Word roots of each library category's name and tags, e.g. 'bank' → {bank, atm, loan, inte, fees}."""
    roots = {}
    for c in library():
        roots.setdefault(c["cat"], set()).update(footage.word_roots(" ".join(list(c["tags"]) + c["cat"].split("-"))))
    return roots


def pick_library(category, rng, avoid, used):
    """A clip of the category not shown recently; else the one shown longest ago, not yet in this video if possible.
    Never a clip of another category: with about 4 clips each, a busy category is often all recent, and a random
    fallback would put a casino behind a supermarket line. None if the category is not in the library."""
    same = [c for c in library() if c["cat"] == category]
    if not same:
        return None
    fresh = [c for c in same if c["id"] not in avoid]
    if fresh:
        return rng.choice(fresh)
    order = recent()
    pool = [c for c in same if c["id"] not in used] or same
    return min(pool, key=lambda c: order.index(c["id"]) if c["id"] in order else -1)


WOMEN = {"woman", "women", "girl", "girls", "lady", "female"}
MEN = {"man", "men", "boy", "guy", "male", "businessman", "athlete", "boxer"}
# a long tag list is tag spam: a frog clip with 23 tags (movie, cinema, popcorn...) stood in for a movie theater and a
# waterfall with 22 (movie, watching...) for a cinema audience. In the 6 Nov test the 5 wrong shots had 22 to 35 tags.
MAX_TAGS = 15
FIRST_TAGS = 5  # an uploader's first tags say what the clip shows; further down, a word is often an afterthought


def names_subject(tags, roots):
    """True if the clip's first tags are about the search. A lone word must be a whole tag among the first 3 ("form" found
    waves tagged "to form", "basket" a flower called "cape basket", "milk" a nursing bison); of several words, one must be
    among the first 5."""
    if len(roots) == 1:
        return any(t.startswith(roots[0]) and " " not in t for t in tags[:3])
    return any(w.startswith(r) for r in roots for t in tags[:FIRST_TAGS] for w in t.split())


def match_score(clip, query):
    """2 = the tags hold every specific word of the search, 1 = its subject (first specific word) and at least half
    of them, 0 = no match. Off-topic tags, tag spam, and women when the search asks for a man, never match."""
    tags = [t.strip() for t in (clip.get("tags") or "").lower().split(",") if t.strip()]
    if not tags or len(tags) > MAX_TAGS or footage.off_topic(tags, query):
        return 0
    words = set(query.lower().split())
    if words & {"man", "men"} and set(tags) & WOMEN and not set(tags) & MEN:
        return 0
    text = ", ".join(tags)
    roots = [r for r in footage.word_roots(query) if r not in GENERIC]
    if not roots:
        return 1 if footage.relevant(clip, query) else 0
    found = sum(1 for r in roots if r in text)
    if found == len(roots) and names_subject(tags, roots):
        return 2
    return 1 if roots[0] in text and found >= math.ceil(len(roots) / 2) else 0


def looks_empty(path, at):
    """True if the frame is nearly black or flat (one colour): nothing to see behind the captions."""
    raw = subprocess.run([find_ffmpeg(), "-v", "error", "-ss", f"{at:.2f}", "-i", str(path), "-frames:v", "1",
                          "-vf", "scale=32:32,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    if not raw:
        return True
    mean = sum(raw) / len(raw)
    spread = (sum((p - mean) ** 2 for p in raw) / len(raw)) ** 0.5
    return mean < 30 or spread < 12


def prepare_stock(path, start, seconds, out):
    """Cut the segment, fill 1080x1920, give it the cinema grade. Returns False if FFmpeg failed."""
    grade = load_config().get("style", {}).get("stock_grade", DEFAULT_GRADE)
    result = subprocess.run([find_ffmpeg(), "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", str(path),
                             "-t", f"{seconds + 0.3:.2f}", "-an", "-vf",
                             f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,{grade}",
                             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
                            capture_output=True)
    return result.returncode == 0 and out.exists()


def pick_stock(query, rng, avoid, seconds, work_dir, strict=False):
    """A real clip for the search words, cut and graded for this shot, not shown recently. None if nothing fits.
    strict=True keeps only clips whose tags hold every specific word of the search."""
    name, key = footage.provider()
    if not name:  # no PIXABAY_API_KEY: the library does every shot
        return None
    try:
        found = [c for c in footage.search(query, name, key) if c["duration"] >= seconds + 1]
    except Exception as e:  # network, rate limit: the library takes over
        print(f"  stock search '{query}' failed ({type(e).__name__}), using the library")
        return None
    scored = [(match_score(c, query), c) for c in found if c["id"] not in avoid]
    best = max((s for s, _ in scored), default=0)
    if not best or (strict and best < 2):
        return None
    good = [c for s, c in scored if s == best]  # clips matching every word beat partial matches
    rng.shuffle(good)
    for clip in good[:4]:
        try:
            path = footage.download(clip)
        except Exception as e:
            print(f"  stock download failed ({type(e).__name__}), trying another one")
            continue
        start = round(rng.uniform(0.3, max(0.3, clip["duration"] - seconds - 0.5)), 2)
        work_dir.mkdir(parents=True, exist_ok=True)
        out = work_dir / f"{clip['id']}_{start:.0f}.mp4"
        if prepare_stock(path, start, seconds, out) and not looks_empty(out, seconds / 2):
            return {"id": clip["id"], "path": out}
        print(f"  stock clip {clip['id']} looks empty or broken, trying another one")
    return None


# words that never make a search on their own: alone, "used" finds anything, "frozen" finds ice, not a turkey,
# and "machine" finds factories (Pixabay's slot machine clips are tagged casino, not slot)
WEAK_WORDS = {"used", "new", "old", "big", "small", "large", "full", "empty", "red", "black", "white", "dark", "bright",
              "vintage", "closeup", "colorful", "sparkling", "frozen", "happy", "american", "british", "fine", "real",
              "front", "hand", "hands", "woman", "man", "women", "men", "people", "person", "couple", "modern", "luxury",
              "machine"}
NOUNS_IN_ING = {"shopping", "clothing", "building", "painting", "parking", "wedding", "booking", "banking", "cooking",
                "packaging", "bottling", "roasting", "ceiling"}


def stock_queries(search, style=None, singles=True):
    """Searches to try in order: the line's words, the pairs holding its subject (its first strong word: the writer puts
    the noun first; adjectives and verbs don't count), the subject alone, then, given a style (no library), the channel's
    on-theme fallbacks (config style → fallback_searches). A search that loses its subject finds anything: "vacuum cleaner"
    gave a pressure washer, "store entrance" an ants' nest, "grocery basket woman" a basketball game."""
    words = search.split()
    strong = [w for w in words if w not in WEAK_WORDS and (not w.endswith("ing") or w in NOUNS_IN_ING)]
    subject = strong[0] if strong else None
    queries = [search]
    if len(words) > 2:
        queries += [" ".join(pair) for pair in combinations(words, 2) if subject in pair]
    if singles and subject:
        queries.append(subject)
    queries += (style or {}).get("fallback_searches", [])
    return list(dict.fromkeys(queries))


def pick_stock_strict(queries, rng, avoid, seconds, work_dir):
    """The first clip whose tags hold every word of a query, trying the queries in order. None if none does."""
    for query in queries:
        clip = pick_stock(query, rng, avoid, seconds, work_dir, strict=True)
        if clip:
            return clip
    return None


def pick_stock_only(search, style, rng, avoid, seconds, work_dir):
    """Stock-only channels: a clip matching every word beats a loose one (a pond once stood in for 'popcorn').
    Only when nothing matches fully, anywhere, does a partial match of the line's own words get used."""
    return (pick_stock_strict(stock_queries(search, style), rng, avoid, seconds, work_dir)
            or pick_stock(search, rng, avoid, seconds, work_dir))


def plan_scenes(lines, total, seed, work_dir):
    """One or two shots per line, from its start to the next line's start. Returns a list of
    {id, path, start, dur, media_start, ai, zoom} where ai tells if the clip is AI-made (TikTok label)."""
    style = load_config().get("style", {})
    stock_share = style.get("stock_share", 0.5)
    roots = category_roots()
    has_library = bool(roots)  # no library: every shot, the hook too, is real footage
    cat_ids = {}
    for c in library():
        cat_ids.setdefault(c["cat"], []).append(c["id"])
    rng = random.Random(f"{seed}-scenes")
    avoid, used = set(recent()), set()
    shots, stock_turn = [], 0.0
    for i, line in enumerate(lines):
        start = 0.0 if i == 0 else line["start"]
        end = lines[i + 1]["start"] if i + 1 < len(lines) else total
        pieces = 2 if end - start > MAX_SHOT else 1
        step = (end - start) / pieces
        search, scene = line.get("search", ""), line.get("scene", "")
        if has_library and scene not in roots:
            raise SystemExit(f"Scene '{scene}' is not a library category: fix this line (add_content.py checks it).")
        fits = bool(set(footage.word_roots(search)) & roots.get(scene, set()))
        for p in range(pieces):
            s, e = start + p * step, start + (p + 1) * step
            clip = None
            # a fitting hook stays library; then about stock_share of the shots are real footage, plus the lines
            # whose words don't fit their category and those whose category has no clip left unseen in this video
            # (in a test, the popcorn script showed the same popcorn clip three times)
            stock_turn += stock_share
            spent = all(cid in used for cid in cat_ids.get(scene, []))
            if search and (not has_library or not fits or spent or (i > 0 and stock_turn >= 1)):
                if has_library:
                    clip = pick_stock_strict(stock_queries(search, singles=not fits or spent), rng, avoid, e - s, work_dir)
                else:
                    clip = pick_stock_only(search, style, rng, avoid, e - s, work_dir)
                if clip:
                    stock_turn -= 1
                    shots.append({"id": clip["id"], "path": clip["path"], "start": round(s, 3), "dur": round(e - s, 3),
                                  "media_start": 0, "ai": False, "zoom": 1.1})
            if not clip:
                if not has_library:
                    raise SystemExit(f"No Pixabay clip found for '{search}': change this line's search words.")
                clip = pick_library(scene, rng, avoid, used)
                shots.append({"id": clip["id"], "path": LIBRARY / f"{clip['id']}.mp4", "start": round(s, 3),
                              "dur": round(e - s, 3), "media_start": 0, "ai": True, "zoom": 1.08})
            avoid.add(clip["id"])
            used.add(clip["id"])
    return shots
