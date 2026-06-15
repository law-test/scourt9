#!/usr/bin/env python3
# 민소 조문 완비(민법위키 civil_procedure_articles.json) + 통합본 v022 atom 병합
# -> data/civproc.js / civproc.json / lawtext.js
import json, re, os
from collections import Counter, OrderedDict

ART = "/sessions/gallant-vibrant-lamport/mnt/cowork/law-test-wiki/assets/civil_procedure_articles.json"
SRC = "/sessions/gallant-vibrant-lamport/mnt/cowork/법원직_민사소송법_OX/통합본/민소_조문별_통합본_v022.json"
OUT = "/sessions/gallant-vibrant-lamport/mnt/cowork/scourt9_tmp_out"  # placeholder, overridden below
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT_DIR, exist_ok=True)

def num(k):
    m = re.search(r"(\d+)", k or ""); return int(m.group(1)) if m else 99999

def strip_prefix(body):
    if not body: return ""
    return re.sub(r"^제\d+조(?:의\d+)?\s*\([^)]*\)\s*", "", body.strip(), count=1)

AJ = json.load(open(ART, encoding="utf-8"))["items"]
artmap = OrderedDict()
for x in AJ:
    a = x["article_no"]
    artmap[a] = {"title": x.get("title") or "", "body": strip_prefix(x.get("body") or ""),
                 "part": x.get("part") or "기타", "chapter": x.get("chapter") or (x.get("part") or "기타"),
                 "sb": x.get("sort_base", 9999), "ss": x.get("sort_sub", 0)}

J = json.load(open(SRC, encoding="utf-8"))
jo = J["조문"]; bucket = J.get("판례·논점 버킷", [])
def atoms_of(v):
    return [{"o": a.get("o"), "ref": a.get("ref"), "freq": a.get("freq", 1),
             "sources": a.get("출처", []),
             "x": [{"q": xx.get("q"), "src": xx.get("출처")} for xx in a.get("x", [])],
             "verified": bool(a.get("검증"))} for a in v]
ouratoms = {k: atoms_of(v) for k, v in jo.items()}

order = sorted(artmap, key=lambda a: (artmap[a]["sb"], artmap[a]["ss"]))
articles = []; seen = set()
for a in order:
    m = artmap[a]; ats = ouratoms.get(a, [])
    articles.append({"art": a, "title": m["title"], "pyeon": m["part"], "jang": m["chapter"],
                     "atoms": ats, "count": len(ats), "freqMax": max([t["freq"] for t in ats] or [0]), "hasBody": True})
    seen.add(a)
extra = [k for k in ouratoms if k not in seen]
for k in sorted(extra, key=num):
    ats = ouratoms[k]
    articles.append({"art": k, "title": "", "pyeon": "관련 특별법", "jang": "소액사건심판법·민사집행법 등",
                     "atoms": ats, "count": len(ats), "freqMax": max([t["freq"] for t in ats] or [0]), "hasBody": False})

# tree from part -> chapter (출현 순서 유지)
tree = []; pidx = {}
for a in order:
    p = artmap[a]["part"]; c = artmap[a]["chapter"]
    if p not in pidx:
        pidx[p] = {"pyeon": p, "jangs": [], "_s": set()}; tree.append(pidx[p])
    if c not in pidx[p]["_s"]:
        pidx[p]["_s"].add(c); pidx[p]["jangs"].append({"jang": c})
if extra:
    tree.append({"pyeon": "관련 특별법", "jangs": [{"jang": "소액사건심판법·민사집행법 등"}]})
for t in tree: t.pop("_s", None)

partof = {a["art"]: a["pyeon"] for a in articles}
ox = []; oid = 0
for k in sorted(ouratoms, key=num):
    p = partof.get(k, "기타")
    for a in ouratoms[k]:
        oid += 1
        ox.append({"id": "O%d" % oid, "art": k, "pyeon": p, "ans": "O", "stmt": a["o"],
                   "ref": a["ref"], "freq": a["freq"], "sources": a["sources"]})
        for xx in a["x"]:
            oid += 1
            ox.append({"id": "X%d" % oid, "art": k, "pyeon": p, "ans": "X", "stmt": xx["q"],
                       "ref": a["ref"], "freq": a["freq"],
                       "sources": [xx["src"]] if xx.get("src") else [], "truth": a["o"]})
bucket_out = []
for a in bucket:
    bucket_out.append({"art": a.get("art"), "o": a.get("o"), "ref": a.get("ref"), "freq": a.get("freq", 1),
                       "sources": a.get("출처", []),
                       "x": [{"q": xx.get("q"), "src": xx.get("출처")} for xx in a.get("x", [])]})
    oid += 1
    ox.append({"id": "O%d" % oid, "art": a.get("art") or "판례·논점", "pyeon": "판례·논점", "ans": "O",
               "stmt": a["o"], "ref": a.get("ref"), "freq": a.get("freq", 1), "sources": a.get("출처", [])})
    for xx in a.get("x", []):
        oid += 1
        ox.append({"id": "X%d" % oid, "art": a.get("art") or "판례·논점", "pyeon": "판례·논점", "ans": "X",
                   "stmt": xx.get("q"), "ref": a.get("ref"), "freq": a.get("freq", 1),
                   "sources": [xx.get("출처")] if xx.get("출처") else [], "truth": a["o"]})

n_atoms = sum(len(v) for v in ouratoms.values()) + len(bucket)
n_freq = sum(1 for v in ouratoms.values() for a in v if a.get("freq", 1) >= 2)
n_quiz_arts = sum(1 for a in articles if a["count"] > 0)
data = {
    "subject": "민사소송법", "slug": "civ-proc", "version": J.get("version"), "updatedAt": J.get("updatedAt"),
    "stats": {"atoms": J.get("통합 atom 수"), "freq": J.get("빈출 atom 수"),
              "articles": len(articles), "quizArticles": n_quiz_arts, "ox": len(ox), "bucket": len(bucket_out)},
    "tree": tree, "articles": articles, "bucket": bucket_out, "ox": ox,
}
open(OUT_DIR + "/civproc.js", "w", encoding="utf-8").write("window.CIVPROC = " + json.dumps(data, ensure_ascii=False) + ";\n")
json.dump(data, open(OUT_DIR + "/civproc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

lawtext = {a: {"title": artmap[a]["title"], "body": artmap[a]["body"]} for a in order}
open(OUT_DIR + "/lawtext.js", "w", encoding="utf-8").write("window.LAWTEXT = " + json.dumps(lawtext, ensure_ascii=False) + ";\n")

print("articles(완비):", len(articles), "| 기출조문:", n_quiz_arts, "| ox:", len(ox), "| lawtext:", len(lawtext))
print("tree 편:", [t["pyeon"] for t in tree])
print("civproc.js bytes:", os.path.getsize(OUT_DIR + "/civproc.js"), "| lawtext.js bytes:", os.path.getsize(OUT_DIR + "/lawtext.js"))
