#!/usr/bin/env python3
# civproc.json → Supabase seed.sql (subjects, articles, atoms, atom_traps, atom_sources)
import json, re, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(HERE + "/data/civproc.json", encoding="utf-8"))

# lawtext.js (JS 객체 리터럴) → JSON 으로 변환해 title/body 추출
lt = {}
try:
    raw = open(HERE + "/data/lawtext.js", encoding="utf-8").read()
    raw = raw[raw.index("{"): raw.rindex("}") + 1]
    raw = re.sub(r'([{,]\s*)(title|body)\s*:', r'\1"\2":', raw)
    lt = json.loads(raw)
except Exception as e:
    print("lawtext parse skipped:", e)

def q(s):
    return "null" if s is None else "'" + str(s).replace("'", "''") + "'"

def parse_src(s):
    y = re.search(r"(\d{4})", s or "")
    n = re.search(r"문\s*0*(\d+)", s or "")
    return (y.group(1) if y else "null", n.group(1) if n else "null")

def chunked(rows, head, n=400):
    return "\n".join(head + "\n" + ",\n".join(rows[i:i+n]) + ";" for i in range(0, len(rows), n))

lines = ["-- 법원직.com seed (민사소송법 통합본 v022) — 0001_init.sql 적용 후 실행",
         "begin;",
         "insert into subjects(id,slug,name,sort) values (1,'civ-proc','민사소송법',1) on conflict (slug) do nothing;"]

arows = []
for a in data["articles"]:
    info = lt.get(a["art"], {})
    arows.append("(1,%s,%s,%s,%s,%s)" % (q(a["art"]), q(info.get("title")), q(info.get("body")), q(a["pyeon"]), q(a["jang"])))
lines.append(chunked(arows, "insert into articles(subject_id,article_no,title,body,pyeon,jang) values"))

aid = 0
atoms, traps, srcs = [], [], []
def emit(article_no, pyeon, o, ref, freq, verified, xs, sources):
    global aid
    aid += 1; me = aid
    atoms.append("(%d,1,%s,%s,'O',%s,%s,%d,%s)" % (
        me, q(article_no), q(pyeon), q(o), q(ref), int(freq or 1), "true" if verified else "false"))
    for x in xs or []:
        traps.append("(%d,%s,%s)" % (me, q(x.get("q")), q(x.get("src"))))
    for s in sources or []:
        y, n = parse_src(s)
        srcs.append("(%d,%s,%s,%s)" % (me, q(s), y, n))

for a in data["articles"]:
    for at in a["atoms"]:
        emit(a["art"], a["pyeon"], at["o"], at["ref"], at["freq"], at.get("verified"), at["x"], at["sources"])
for b in data["bucket"]:
    emit(b.get("art"), "판례·논점", b["o"], b["ref"], b["freq"], False, b["x"], b["sources"])

lines.append(chunked(atoms, "insert into atoms(id,subject_id,article_no,pyeon,ans,statement,ref,freq,verified) values"))
lines.append(chunked(traps, "insert into atom_traps(atom_id,statement,source_label) values"))
lines.append(chunked(srcs,  "insert into atom_sources(atom_id,source_label,year,qno) values"))
lines.append("select setval(pg_get_serial_sequence('atoms','id'), (select max(id) from atoms));")
lines.append("update atoms a set article_id = ar.id from articles ar where ar.subject_id=1 and ar.article_no=a.article_no;")
lines.append("commit;")

out = HERE + "/supabase/seed.sql"
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("articles:", len(arows), "| atoms:", len(atoms), "| traps:", len(traps), "| sources:", len(srcs))
print("lawtext merged:", sum(1 for a in data["articles"] if a["art"] in lt), "조문")
print("written bytes:", os.path.getsize(out))
