#!/usr/bin/env python3
# 형법: 목차(법제처) + 통합본 atom 병합 → data/penal.js
import json, re, os
SRC="/sessions/gallant-vibrant-lamport/mnt/cowork/scourt9_src/형법_목차.txt"
UNI="/sessions/gallant-vibrant-lamport/mnt/cowork/법원직_형법_OX/통합본/형법_조문별_v002.json"
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data")
os.makedirs(OUT,exist_ok=True)
TREE=[
 ("제1편 총칙",[("제1장 형법의 적용범위",1,8),("제2장 죄",9,40),("제3장 형",41,86)]),
 ("제2편 각칙",[
   ("제1장 내란의 죄",87,91),("제2장 외환의 죄",92,104),("제3장 국기에 관한 죄",105,106),
   ("제4장 국교에 관한 죄",107,113),("제5장 공안을 해하는 죄",114,118),("제6장 폭발물에 관한 죄",119,121),
   ("제7장 공무원의 직무에 관한 죄",122,135),("제8장 공무방해에 관한 죄",136,144),
   ("제9장 도주와 범인은닉의 죄",145,151),("제10장 위증과 증거인멸의 죄",152,155),
   ("제11장 무고의 죄",156,157),("제12장 신앙에 관한 죄",158,163),("제13장 방화와 실화의 죄",164,176),
   ("제14장 일수와 수리에 관한 죄",177,184),("제15장 교통방해의 죄",185,191),
   ("제16장 먹는 물에 관한 죄",192,197),("제17장 아편에 관한 죄",198,206),("제18장 통화에 관한 죄",207,213),
   ("제19장 유가증권, 우표와 인지에 관한 죄",214,224),("제20장 문서에 관한 죄",225,237),
   ("제21장 인장에 관한 죄",238,240),("제22장 성풍속에 관한 죄",241,245),("제23장 도박과 복표에 관한 죄",246,249),
   ("제24장 살인의 죄",250,256),("제25장 상해와 폭행의 죄",257,265),("제26장 과실치사상의 죄",266,268),
   ("제27장 낙태의 죄",269,270),("제28장 유기와 학대의 죄",271,275),("제29장 체포와 감금의 죄",276,282),
   ("제30장 협박의 죄",283,286),("제31장 약취·유인 및 인신매매의 죄",287,296),("제32장 강간과 추행의 죄",297,306),
   ("제33장 명예에 관한 죄",307,312),("제34장 신용, 업무와 경매에 관한 죄",313,315),("제35장 비밀침해의 죄",316,318),
   ("제36장 주거침입의 죄",319,322),("제37장 권리행사를 방해하는 죄",323,328),("제38장 절도와 강도의 죄",329,346),
   ("제39장 사기와 공갈의 죄",347,354),("제40장 횡령과 배임의 죄",355,361),("제41장 장물에 관한 죄",362,365),
   ("제42장 손괴의 죄",366,372)]),
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
data={"subject":"형법","slug":"penal","version":"법제처 2026-03-12 / OX v002(정제·빈출)","updatedAt":"2026-06-16",
 "stats":{"atoms":n_atoms,"freq":sum(1 for a in arts for t in a["atoms"] if t["freq"]>=2),
          "articles":len(arts),"quizArticles":n_quiz,"ox":len(ox),"bucket":0},
 "tree":tree,"articles":arts,"bucket":[],"ox":ox}
open(OUT+"/penal.js","w",encoding="utf-8").write("window.PENAL = "+json.dumps(data,ensure_ascii=False)+";\n")
json.dump(data,open(OUT+"/penal.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("형법 조문:",len(arts),"| atom:",n_atoms,"| 기출조문:",n_quiz,"| ox:",len(ox))
