#!/usr/bin/env python3
# 형사소송법: 목차(법제처) + 통합본 atom 병합 → data/crimproc.js
import json, re, os
SRC="/sessions/gallant-vibrant-lamport/mnt/cowork/scourt9_src/형소_목차.txt"
UNI="/sessions/gallant-vibrant-lamport/mnt/cowork/법원직_형사소송법_OX/통합본/형소_조문별_v001.json"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data")
os.makedirs(OUT,exist_ok=True)
TREE=[
 ("제1편 총칙",[("제1장 법원의 관할",1,16),("제2장 법원직원의 제척ㆍ기피ㆍ회피",17,25),
   ("제3장 소송행위의 대리와 보조",26,29),("제4장 변호",30,36),("제5장 재판",37,46),
   ("제6장 서류",47,59),("제7장 송달",60,65),("제8장 기간",66,67),
   ("제9장 피고인의 소환ㆍ구속",68,105),("제10장 압수와 수색",106,138),("제11장 검증",139,145),
   ("제12장 증인신문",146,168),("제13장 감정",169,179),("제14장 통역과 번역",180,183),
   ("제15장 증거보전",184,185),("제16장 소송비용",186,194)]),
 ("제2편 제1심",[("제1장 수사",195,245),("제2장 공소",246,265),("제3장 공판",266,337)]),
 ("제3편 상소",[("제1장 통칙",338,356),("제2장 항소",357,370),("제3장 상고",371,401),("제4장 항고",402,419)]),
 ("제4편 특별소송절차",[("제1장 재심",420,440),("제2장 비상상고",441,447),("제3장 약식절차",448,458)]),
 ("제5편 재판의 집행",[("재판의 집행",459,493)]),
]
def mainnum(k): m=re.match(r"제(\d+)조",k); return int(m.group(1)) if m else 99999
def subnum(k): m=re.match(r"제(\d+)조(?:의(\d+))?",k); return (int(m.group(1)),int(m.group(2) or 0)) if m else (99999,0)
def locate(n):
    for p,js in TREE:
        for j,s,e in js:
            if s<=n<=e: return p,j
    return "기타","기타"

uni=json.load(open(UNI,encoding="utf-8")) if os.path.exists(UNI) else {}
def atoms_of(v):
    return [{"o":a.get("o"),"ref":a.get("ref"),"freq":a.get("freq",1),"sources":a.get("sources",[]),
             "x":[{"q":xx.get("q"),"src":xx.get("src")} for xx in a.get("x",[])],"verified":bool(a.get("검증"))} for a in v]

arts=[]
for ln in open(SRC,encoding="utf-8"):
    ln=ln.rstrip("\n")
    if not ln.strip(): continue
    m=re.match(r"(제\d+조(?:의\d+)?)\s+(.*)",ln)
    if not m: continue
    art,title=m.group(1),m.group(2).strip()
    p,j=locate(mainnum(art))
    ats=atoms_of(uni.get(art,[]))
    arts.append({"art":art,"title":title,"pyeon":p,"jang":j,"atoms":ats,"count":len(ats),
                 "freqMax":max([t["freq"] for t in ats] or [0]),"hasBody":False})
arts.sort(key=lambda a:subnum(a["art"]))

tree=[]; idx={}
for a in arts:
    p,j=a["pyeon"],a["jang"]
    if p not in idx: idx[p]={"pyeon":p,"jangs":[],"_s":set()}; tree.append(idx[p])
    if j not in idx[p]["_s"]: idx[p]["_s"].add(j); idx[p]["jangs"].append({"jang":j})
for t in tree: t.pop("_s",None)

partof={a["art"]:a["pyeon"] for a in arts}
ox=[]; oid=0
for a in arts:
    for at in a["atoms"]:
        oid+=1
        ox.append({"id":"O%d"%oid,"art":a["art"],"pyeon":a["pyeon"],"ans":"O","stmt":at["o"],
                   "ref":at["ref"],"freq":at["freq"],"sources":at["sources"]})
        for xx in at["x"]:
            oid+=1
            ox.append({"id":"X%d"%oid,"art":a["art"],"pyeon":a["pyeon"],"ans":"X","stmt":xx["q"],
                       "ref":at["ref"],"freq":at["freq"],
                       "sources":[xx["src"]] if xx.get("src") else [],"truth":at["o"]})
n_atoms=sum(len(uni.get(a["art"],[])) for a in arts)
n_quiz=sum(1 for a in arts if a["count"]>0)
data={"subject":"형사소송법","slug":"crim-proc","version":"법제처 2025-09-19 / OX v001","updatedAt":"2026-06-15",
 "stats":{"atoms":n_atoms,"freq":sum(1 for a in arts for t in a["atoms"] if t["freq"]>=2),
          "articles":len(arts),"quizArticles":n_quiz,"ox":len(ox),"bucket":0},
 "tree":tree,"articles":arts,"bucket":[],"ox":ox}
open(OUT+"/crimproc.js","w",encoding="utf-8").write("window.CRIMPROC = "+json.dumps(data,ensure_ascii=False)+";\n")
json.dump(data,open(OUT+"/crimproc.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("형소 조문:",len(arts),"| atom:",n_atoms,"| 기출조문:",n_quiz,"| ox:",len(ox))
