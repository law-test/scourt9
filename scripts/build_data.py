#!/usr/bin/env python3
# 통합본 v022 → 법원직.com 프론트 데이터(civproc.js / civproc.json) 변환
import json, re, os
from collections import Counter

SRC = "/sessions/gallant-vibrant-lamport/mnt/cowork/법원직_민사소송법_OX/통합본/민소_조문별_통합본_v022.json"
OUT_DIR = "/sessions/gallant-vibrant-lamport/mnt/cowork/scourt9/web/data"
os.makedirs(OUT_DIR, exist_ok=True)

J = json.load(open(SRC, encoding="utf-8"))
jo = J["조문"]
bucket = J.get("판례·논점 버킷", [])

def parse(k):
    m = re.match(r"제(\d+)조(?:의(\d+))?", k)
    if not m:
        return (99999, 0)
    return (int(m.group(1)), int(m.group(2) or 0))

TREE = [
 ("제1편 총칙", [
    ("제1장 법원", 1, 50),
    ("제2장 당사자", 51, 97),
    ("제3장 소송비용", 98, 133),
    ("제4장 소송절차", 134, 247),
 ]),
 ("제2편 제1심의 소송절차", [
    ("제1장 소의 제기", 248, 271),
    ("제2장 변론과 그 준비", 272, 287),
    ("제3장 증거", 288, 384),
    ("제4장 제소전화해의 절차", 385, 389),
 ]),
 ("제3편 상소", [
    ("제1장 항소", 390, 421),
    ("제2장 상고", 422, 438),
    ("제3장 항고", 439, 450),
 ]),
 ("제4편 재심", [("재심", 451, 461)]),
 ("제5편 독촉절차", [("독촉절차", 462, 474)]),
 ("제6편 공시최고절차", [("공시최고절차", 475, 497)]),
 ("제7편 판결의 확정 및 집행정지", [("판결의 확정 및 집행정지", 498, 502)]),
]

def locate(mainnum):
    for pyeon, jangs in TREE:
        for jang, s, e in jangs:
            if s <= mainnum <= e:
                return pyeon, jang
    return "관련 특별법", "소액사건심판법·민사집행법 등"

articles = {}
for k, v in jo.items():
    atoms = []
    for a in v:
        atoms.append({
            "o": a.get("o"),
            "ref": a.get("ref"),
            "freq": a.get("freq", 1),
            "sources": a.get("출처", []),
            "x": [{"q": xx.get("q"), "src": xx.get("출처")} for xx in a.get("x", [])],
            "verified": bool(a.get("검증")),
        })
    articles[k] = {"atoms": atoms, "count": len(atoms),
                   "freqMax": max([a.get("freq", 1) for a in v] or [0])}

ordered = sorted(articles.keys(), key=parse)
arts_out = []
for k in ordered:
    p, j = locate(parse(k)[0])
    arts_out.append({"art": k, "pyeon": p, "jang": j, **articles[k]})

bucket_out = []
for a in bucket:
    bucket_out.append({
        "art": a.get("art"),
        "o": a.get("o"), "ref": a.get("ref"), "freq": a.get("freq", 1),
        "sources": a.get("출처", []),
        "x": [{"q": xx.get("q"), "src": xx.get("출처")} for xx in a.get("x", [])],
    })

ox = []
oid = 0
for k in ordered:
    p, j = locate(parse(k)[0])
    for a in articles[k]["atoms"]:
        oid += 1
        ox.append({"id": "O%d" % oid, "art": k, "pyeon": p, "ans": "O",
                   "stmt": a["o"], "ref": a["ref"], "freq": a["freq"], "sources": a["sources"]})
        for xx in a["x"]:
            oid += 1
            ox.append({"id": "X%d" % oid, "art": k, "pyeon": p, "ans": "X",
                       "stmt": xx["q"], "ref": a["ref"], "freq": a["freq"],
                       "sources": [xx["src"]] if xx.get("src") else [], "truth": a["o"]})

for a in bucket:
    oid += 1
    ox.append({"id": "O%d" % oid, "art": a.get("art") or "판례·논점", "pyeon": "판례·논점",
               "ans": "O", "stmt": a["o"], "ref": a.get("ref"),
               "freq": a.get("freq", 1), "sources": a.get("출처", [])})
    for xx in a.get("x", []):
        oid += 1
        ox.append({"id": "X%d" % oid, "art": a.get("art") or "판례·논점", "pyeon": "판례·논점",
                   "ans": "X", "stmt": xx.get("q"), "ref": a.get("ref"),
                   "freq": a.get("freq", 1),
                   "sources": [xx.get("출처")] if xx.get("출처") else [], "truth": a["o"]})

tree_out = []
for pyeon, jangs in TREE:
    tree_out.append({"pyeon": pyeon, "jangs": [{"jang": jg[0]} for jg in jangs]})

data = {
    "subject": "민사소송법", "slug": "civ-proc",
    "version": J.get("version"), "updatedAt": J.get("updatedAt"),
    "stats": {"atoms": J.get("통합 atom 수"), "freq": J.get("빈출 atom 수"),
              "articles": len(articles), "ox": len(ox), "bucket": len(bucket_out)},
    "tree": tree_out,
    "articles": arts_out,
    "bucket": bucket_out,
    "ox": ox,
}

js = "window.CIVPROC = " + json.dumps(data, ensure_ascii=False) + ";\n"
open(OUT_DIR + "/civproc.js", "w", encoding="utf-8").write(js)
json.dump(data, open(OUT_DIR + "/civproc.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

c = Counter(a["pyeon"] for a in arts_out)
print("articles", len(arts_out), "ox", len(ox), "bucket", len(bucket_out))
print("ox by ans:", dict(Counter(o["ans"] for o in ox)))
print("bytes(js):", len(js))
for p, _ in TREE:
    print("  ", p, c.get(p, 0), "조문")
print("   관련 특별법:", c.get("관련 특별법", 0))
