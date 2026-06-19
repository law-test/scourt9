from __future__ import annotations

import json
import math
import re
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
BAR_DIR = WORKSPACE / "law-test-private" / "private_problem_banks" / "current"
BUPMUSA_DIR = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사" / "current" / "통합본"
DATA_DIR = ROOT / "data"

TODAY_DECIMAL = 2026.46
HALF_LIFE_YEARS = 4.0
SOURCE_WEIGHTS = {"법원직": 1.0, "변호사시험": 0.5, "법무사시험": 0.5}
FAMILY_ORDER = {"법원직": 0, "변호사시험": 1, "법무사시험": 2}
GRADE_CUTS = [
    (0.04, "S"),
    (0.11, "A+"),
    (0.23, "A"),
    (0.40, "B+"),
    (0.60, "B"),
    (0.77, "C+"),
    (0.89, "C"),
    (0.96, "D+"),
    (1.00, "D"),
]

TASKS = [
    {
        "slug": "civproc",
        "window": "CIVPROC",
        "subject": "민사소송법",
        "law": "민사소송법",
        "schema": "all-test/civproc-integrated-atom/v1",
        "title": "all_test(법원직 중심)_민사소송법 조문별 통합 atom",
        "version": "civproc_v024_all-test_bar-integrated",
        "bar_file": "ox_msa_unified_selfcontained_v002.json",
        "bar_subjects": {"민사소송법"},
        "out_dir": WORKSPACE / "법원직_민사소송법_OX" / "통합본",
        "out_name": "all_test(법원직 중심)_민사소송법_통합_atom.json",
    },
    {
        "slug": "constitution",
        "window": "CONSTITUTION",
        "subject": "헌법",
        "law": "헌법",
        "schema": "all-test/constitution-integrated-atom/v1",
        "title": "all_test(법원직 중심)_헌법 조문별 통합 atom",
        "version": "constitution_v023_all-test_bar-bupmusa-integrated",
        "scourt_integrated_file": WORKSPACE / "법원직_헌법_OX" / "통합본" / "법원직_헌법_통합_atom.json",
        "bar_file": "ox_public_bar_all_minimal_atoms_selfcontained_v002.json",
        "bar_subjects": {"헌법"},
        "bupmusa_file": "법무사_헌법_통합_atom.json",
        "out_dir": WORKSPACE / "법원직_헌법_OX" / "통합본",
        "out_name": "all_test(법원직 중심)_헌법_통합_atom.json",
    },
    {
        "slug": "penal",
        "window": "PENAL",
        "subject": "형법",
        "law": "형법",
        "schema": "all-test/penal-integrated-atom/v1",
        "title": "all_test(법원직 중심)_형법 조문별 통합 atom",
        "version": "penal_v004_all-test_bar-integrated",
        "bar_file": "ox_criminal_bar_all_minimal_atoms_selfcontained_v002.json",
        "bar_subjects": {"형법"},
        "out_dir": WORKSPACE / "법원직_형법_OX" / "통합본",
        "out_name": "all_test(법원직 중심)_형법_통합_atom.json",
    },
    {
        "slug": "crimproc",
        "window": "CRIMPROC",
        "subject": "형사소송법",
        "law": "형사소송법",
        "schema": "all-test/crimproc-integrated-atom/v1",
        "title": "all_test(법원직 중심)_형사소송법 조문별 통합 atom",
        "version": "crimproc_v004_all-test_bar-integrated",
        "bar_file": "ox_criminal_bar_all_minimal_atoms_selfcontained_v002.json",
        "bar_subjects": {"형사소송법"},
        "out_dir": WORKSPACE / "법원직_형사소송법_OX" / "통합본",
        "out_name": "all_test(법원직 중심)_형사소송법_통합_atom.json",
    },
]


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_text(text: str | None) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣一-龥]", "", text or "").lower()


def clean_text(text: str | None) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace(" .", ".").replace(" ,", ",")
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([,;:])(?=\S)", r"\1 ", text)
    return text


def parse_article(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.search(r"제\s*(\d+)\s*조(?:\s*의\s*(\d+))?", raw)
    if not m:
        return None
    return f"제{m.group(1)}조" + (f"의{m.group(2)}" if m.group(2) else "")


def source_year(source: str, family: str, round_no: int | None = None) -> float:
    if family == "변호사시험":
        if round_no:
            return 2011 + round_no + 0.35
        m = re.search(r"변시\s*(\d+)", source or "")
        if m:
            return 2011 + int(m.group(1)) + 0.35
    m = re.search(r"(20\d{2})", source or "")
    if m:
        return float(m.group(1))
    return TODAY_DECIMAL - 14


def weight_for_sources(sources: list[dict]) -> tuple[float, float]:
    total = 0.0
    seen = set()
    for src in sources:
        key = (src.get("family"), src.get("sourceId"), src.get("source"))
        if key in seen:
            continue
        seen.add(key)
        family = src.get("family") or "법원직"
        s = SOURCE_WEIGHTS.get(family, 1.0)
        exam_year = float(src.get("year") or source_year(src.get("source", ""), family, src.get("round")))
        age = max(0.0, TODAY_DECIMAL - exam_year)
        total += s * (0.5 ** (age / HALF_LIFE_YEARS))
    return total, round(math.log1p(total), 4)


def grade_items(items: list[dict]) -> None:
    ranked = sorted(items, key=lambda x: (-x.get("weight", 0), x.get("id", "")))
    n = max(1, len(ranked))
    for i, item in enumerate(ranked, 1):
        pct = i / n
        for cut, grade in GRADE_CUTS:
            if pct <= cut:
                item["grade"] = grade
                break


def family_from_text(source: str) -> str:
    source = source or ""
    if "법무사" in source:
        return "법무사시험"
    return "변호사시험" if "변시" in source or "변호사" in source else "법원직"


def make_source(family: str, source: str, source_id: str, round_no: int | None = None) -> dict:
    return {
        "family": family,
        "s": SOURCE_WEIGHTS.get(family, 1.0),
        "source": source,
        "sourceId": source_id,
        **({"round": round_no} if round_no else {}),
    }


def make_bupmusa_source(src: dict, fallback_id: str) -> dict:
    source = src.get("source") or fallback_id
    return {
        "family": "법무사시험",
        "s": SOURCE_WEIGHTS["법무사시험"],
        "source": source,
        "sourceId": src.get("sourceId") or fallback_id,
        **({"year": src.get("year")} if src.get("year") else {}),
        **({"round": src.get("round")} if src.get("round") else {}),
        **({"subject": src.get("subject")} if src.get("subject") else {}),
        **({"sourceUnitId": src.get("sourceUnitId")} if src.get("sourceUnitId") else {}),
        **({"sourceVerdict": src.get("sourceVerdict")} if src.get("sourceVerdict") else {}),
        **({"sourceTrap": src.get("sourceTrap")} if src.get("sourceTrap") else {}),
    }


def deploy_sources(at: dict, fallback_ref: str) -> list[dict]:
    families = at.get("sourceFamilies") or ["법원직"]
    source_texts = at.get("sources") or ([fallback_ref] if fallback_ref else [])
    out = []
    for idx, source in enumerate(source_texts):
        fam = family_from_text(source)
        if "법원직" not in families and fam != "법원직":
            continue
        if fam != "법원직":
            continue
        out.append(make_source("법원직", source, at.get("sourceItemId") or f"{source}-{idx}"))
    if not out and "법원직" in families and fallback_ref:
        out.append(make_source("법원직", fallback_ref, at.get("sourceItemId") or fallback_ref))
    return out


def scourt_items_from_deploy(data: dict) -> list[dict]:
    items = []
    article_rows = [(article, at) for article in data.get("articles", []) for at in article.get("atoms", [])]
    bucket_article = {"art": None, "title": "판례·논점", "pyeon": "판례·논점"}
    article_rows.extend((bucket_article, at) for at in data.get("bucket", []))
    for article, at in article_rows:
            families = at.get("sourceFamilies") or ["법원직"]
            if "법원직" not in families:
                continue
            refs = [s["source"] for s in deploy_sources(at, at.get("ref") or "")]
            if not refs:
                continue
            item = {
                "primary": "법원직",
                "sourceFamilies": ["법원직"],
                "art": article.get("art"),
                "sourceArt": at.get("sourceArt") or at.get("art") or article.get("art"),
                "topic": at.get("topic"),
                "rep": clean_text(at.get("o") or at.get("rep")),
                "a": at.get("ans") or "O",
                "why": at.get("why") or "법원직 기출 atom. 현행법 법리검증 대기.",
                "ref": refs[0],
                "sources": deploy_sources(at, at.get("ref") or ""),
                "refs": refs,
                "sourceIds": [s["sourceId"] for s in deploy_sources(at, at.get("ref") or "")],
                "scourtIds": [s["sourceId"] for s in deploy_sources(at, at.get("ref") or "")],
                "barIds": [],
                "sourceAtomCount": len(refs),
                "quality": {"statementType": "declarative", "displayable": True, "normalizers": [], "changed": False},
                "variants": [],
                "x": [],
                "verification": {
                    "status": "needs-legal-review",
                    "lawAsOf": today(),
                    "legalVerifiedAt": None,
                    "statuteCitationStatus": "pending",
                },
            }
            for i, xx in enumerate(at.get("x") or [], 1):
                xfams = xx.get("sourceFamilies") or families
                if "법원직" not in xfams:
                    continue
                xsources = xx.get("sources") or ([xx.get("src")] if xx.get("src") else [])
                xsources = [s for s in xsources if family_from_text(s) == "법원직"]
                if not xsources:
                    continue
                xweight_sum, xweight = weight_for_sources(
                    [make_source("법원직", s, xx.get("sourceItemId") or f"{s}-{i}") for s in xsources]
                )
                item["x"].append(
                    {
                        "q": clean_text(xx.get("q")),
                        "src": xsources[0],
                        "freq": len(xsources),
                        "sources": xsources,
                        "sourceFamilies": ["법원직"],
                        "allTestId": xx.get("allTestId"),
                        "verified": bool(xx.get("verified")),
                        "truth": xx.get("truth"),
                        "weight": xweight,
                        "sourceItemId": xx.get("sourceItemId"),
                        "art": xx.get("art") or article.get("art"),
                        "sourceArt": xx.get("sourceArt") or at.get("sourceArt") or article.get("art"),
                        "topic": xx.get("topic") or at.get("topic"),
                        "quality": xx.get("quality") or item["quality"],
                    }
                )
            item["variants"].append(
                {
                    "primary": "법원직",
                    "rep": item["rep"],
                    "a": item["a"],
                    "refs": refs,
                    "sourceIds": item["sourceIds"],
                    "quality": item["quality"],
                }
            )
            items.append(item)
    return items


def scourt_items_from_integrated(path: Path) -> list[dict]:
    data = read_json(path)
    items = []
    for raw in data.get("items", []):
        item = deepcopy(raw)
        item["primary"] = "법원직"
        item["sourceFamilies"] = ["법원직"]
        item.setdefault("refs", [s.get("source") for s in item.get("sources", []) if s.get("source")])
        item.setdefault("sourceIds", [s.get("sourceId") for s in item.get("sources", []) if s.get("sourceId")])
        item["scourtIds"] = item.get("scourtIds") or item.get("sourceIds") or []
        item.setdefault("barIds", [])
        item.setdefault("bupmusaIds", [])
        for source in item.get("sources", []):
            source["family"] = "법원직"
            source["s"] = SOURCE_WEIGHTS["법원직"]
        item["sourceAtomCount"] = len(item.get("sources", [])) or item.get("sourceAtomCount", 1)
        items.append(item)
    return items


def scourt_items(task: dict, base: dict) -> list[dict]:
    integrated_path = task.get("scourt_integrated_file")
    if integrated_path:
        return scourt_items_from_integrated(Path(integrated_path))
    return scourt_items_from_deploy(base)


def should_accept_bar_art(task: dict, raw_art: str | None, ref: str | None, existing_arts: set[str]) -> str | None:
    art = parse_article(raw_art)
    if not art or art not in existing_arts:
        return None
    raw = raw_art or ""
    ref = ref or ""
    law = task["law"]
    if law in raw or f"{law} {art}" in ref:
        return art
    if task["slug"] == "civproc" and "민사소송법" in raw:
        return art
    if ref == "" and task["slug"] == "civproc":
        return art
    return None


def bar_items(task: dict, existing_arts: set[str]) -> tuple[list[dict], dict, list[dict]]:
    raw = read_json(BAR_DIR / task["bar_file"])
    out = []
    skipped = {"otherSubject": 0, "noStatement": 0, "unresolvedX": 0}
    unresolved_x = []
    for it in raw.get("items", []):
        if it.get("subject") not in task["bar_subjects"]:
            skipped["otherSubject"] += 1
            continue
        rep = clean_text(it.get("rep") or it.get("q"))
        if not rep:
            skipped["noStatement"] += 1
            continue
        verdict = it.get("a") or it.get("source_answer") or "O"
        truth = clean_text(it.get("truth"))
        srcs = it.get("src") or it.get("years") or it.get("refs") or []
        if isinstance(srcs, str):
            srcs = [srcs]
        if not srcs:
            srcs = [f"변시{it.get('round') or ''}"]
        round_no = it.get("round")
        pid = it.get("pid") or it.get("id") or f"bar-{len(out)+1}"
        if verdict == "X" and not truth:
            skipped["unresolvedX"] += 1
            unresolved_x.append(
                {
                    "sourceId": pid,
                    "source": srcs[0],
                    "sources": srcs,
                    "round": round_no,
                    "year": it.get("year") or (2011 + int(round_no) if round_no else None),
                    "subject": it.get("subject"),
                    "topic": it.get("topic"),
                    "art": it.get("art"),
                    "statement": rep,
                    "sourceAnswer": verdict,
                    "reason": "truth가 없어 대표 O atom에 종속시킬 수 없어 화면용 atom에서 보류",
                }
            )
            continue
        source_statement = it.get("source_statement") or it.get("q") or rep
        false_statement = rep if verdict == "X" else None
        if verdict == "X":
            rep = truth
        sources = [
            make_source("변호사시험", s, f"bar-{pid}-{idx+1}", round_no)
            for idx, s in enumerate(srcs)
        ]
        art = should_accept_bar_art(task, it.get("art"), it.get("ref"), existing_arts)
        quality_normalizers = ["bar-selfcontained-source"]
        if verdict == "X":
            quality_normalizers.append("bar-x-promoted-to-truth")
        quality = {
            "statementType": "declarative",
            "displayable": True,
            "normalizers": quality_normalizers,
            "changed": verdict == "X",
        }
        item = {
            "primary": "변호사시험",
            "sourceFamilies": ["변호사시험"],
            "art": art,
            "sourceArt": it.get("art") or it.get("topic"),
            "topic": it.get("topic"),
            "rep": rep,
            "a": "O",
            "why": clean_text(it.get("why") or "변호사시험 기출 atom. 현행법 법리검증 대기."),
            "ref": srcs[0],
            "sources": sources,
            "refs": srcs,
            "sourceIds": [s["sourceId"] for s in sources],
            "scourtIds": [],
            "barIds": [s["sourceId"] for s in sources],
            "sourceAtomCount": len(sources),
            "quality": quality,
            "variants": [
                {
                    "primary": "변호사시험",
                    "rep": rep,
                    "a": "O",
                    "refs": srcs,
                    "sourceIds": [s["sourceId"] for s in sources],
                    "round": round_no,
                    "original": {
                        "statement": source_statement,
                        "verdict": verdict,
                        "source": srcs[0],
                    },
                }
            ],
            "x": [],
            "verification": {
                "status": "needs-legal-review",
                "lawAsOf": today(),
                "legalVerifiedAt": None,
                "statuteCitationStatus": "pending",
            },
            "bar": {
                "round": round_no,
                "year": it.get("year") or (2011 + int(round_no) if round_no else None),
                "pid": pid,
                "subjectGroup": it.get("subject_group"),
                "sourceRef": it.get("ref"),
            },
        }
        if false_statement:
            item["x"].append(
                {
                    "q": false_statement,
                    "src": srcs[0],
                    "freq": len(srcs),
                    "sources": srcs,
                    "sourceFamilies": ["변호사시험"],
                    "truth": rep,
                    "sourceItemId": pid,
                    "art": art,
                    "sourceArt": it.get("art") or it.get("topic"),
                    "topic": it.get("topic"),
                    "quality": quality,
                }
            )
        out.append(item)
    return out, skipped, unresolved_x


def bupmusa_items(task: dict, existing_arts: set[str]) -> tuple[list[dict], dict]:
    file_name = task.get("bupmusa_file")
    if not file_name:
        return [], {"missingFile": 0, "noStatement": 0}
    path = BUPMUSA_DIR / file_name
    if not path.exists():
        return [], {"missingFile": 1, "noStatement": 0}
    raw = read_json(path)
    out = []
    skipped = {"missingFile": 0, "noStatement": 0}
    for idx, it in enumerate(raw.get("items", []), 1):
        rep = clean_text(it.get("rep"))
        if not rep:
            skipped["noStatement"] += 1
            continue
        raw_sources = it.get("sources") or []
        sources = [
            make_bupmusa_source(src, f"bupmusa-{it.get('id') or idx}-{sidx}")
            for sidx, src in enumerate(raw_sources, 1)
        ]
        if not sources:
            sources = [make_bupmusa_source({}, f"bupmusa-{it.get('id') or idx}")]
        art = parse_article(it.get("art") or it.get("sourceArt") or it.get("basisRef") or rep)
        if art not in existing_arts:
            art = None
        refs = [s["source"] for s in sources]
        source_ids = [s["sourceId"] for s in sources]
        item = {
            "primary": "법무사시험",
            "sourceFamilies": ["법무사시험"],
            "art": art,
            "sourceArt": it.get("basisRef") or it.get("sourceArt") or it.get("topic"),
            "topic": it.get("topic"),
            "rep": rep,
            "a": it.get("a") or "O",
            "why": clean_text(it.get("why") or "법무사시험 기출 atom. 현행법 법리검증 대기."),
            "ref": refs[0],
            "sources": sources,
            "refs": refs,
            "sourceIds": source_ids,
            "scourtIds": [],
            "barIds": [],
            "bupmusaIds": source_ids,
            "sourceAtomCount": len(sources),
            "quality": {
                "statementType": "declarative",
                "displayable": True,
                "normalizers": ["bupmusa-selfcontained-source"],
                "changed": False,
            },
            "variants": [
                {
                    "primary": "법무사시험",
                    "rep": rep,
                    "a": it.get("a") or "O",
                    "refs": refs,
                    "sourceIds": source_ids,
                    "original": {
                        "statement": (raw_sources[0].get("sourceStatement") if raw_sources else None) or rep,
                        "verdict": (raw_sources[0].get("sourceVerdict") if raw_sources else None) or it.get("a"),
                        "source": refs[0],
                    },
                }
            ],
            "x": [],
            "verification": it.get("verification")
            or {
                "status": "needs-legal-review",
                "lawAsOf": today(),
                "legalVerifiedAt": None,
                "statuteCitationStatus": "pending",
            },
            "bupmusa": {
                "sourceIntegratedId": it.get("id"),
                "basisType": it.get("basisType"),
                "basisRef": it.get("basisRef"),
                "grade": it.get("grade"),
            },
        }
        out.append(item)
    return out, skipped


def inherit_article_from_existing(targets: list[dict], existing: list[dict]) -> None:
    by_rep: dict[tuple[str, str], str] = {}
    for item in existing:
        art = item.get("art")
        if not art:
            continue
        key = (item.get("a") or "O", norm_text(item.get("rep")))
        by_rep.setdefault(key, art)
    for item in targets:
        if item.get("art"):
            continue
        item["art"] = by_rep.get((item.get("a") or "O", norm_text(item.get("rep"))))


def merge_items(items: list[dict], prefix: str) -> list[dict]:
    merged: dict[tuple, dict] = {}
    for item in items:
        key = (item.get("art") or "__bucket__", item.get("a") or "O", norm_text(item.get("rep")))
        if key not in merged:
            merged[key] = deepcopy(item)
            continue
        cur = merged[key]
        seen = {(s.get("family"), s.get("sourceId"), s.get("source")) for s in cur.get("sources", [])}
        for source in item.get("sources", []):
            skey = (source.get("family"), source.get("sourceId"), source.get("source"))
            if skey not in seen:
                cur["sources"].append(source)
                seen.add(skey)
        for field in ("refs", "sourceIds", "scourtIds", "barIds", "bupmusaIds"):
            vals = cur.setdefault(field, [])
            for val in item.get(field, []):
                if val not in vals:
                    vals.append(val)
        for fam in item.get("sourceFamilies", []):
            if fam not in cur["sourceFamilies"]:
                cur["sourceFamilies"].append(fam)
        cur["variants"].extend(item.get("variants", []))
        xseen = {norm_text(x.get("q")) + "|" + (x.get("src") or "") for x in cur.get("x", [])}
        for x in item.get("x", []):
            xkey = norm_text(x.get("q")) + "|" + (x.get("src") or "")
            if xkey not in xseen:
                cur.setdefault("x", []).append(x)
                xseen.add(xkey)
        if "법원직" in cur["sourceFamilies"]:
            cur["primary"] = "법원직"
        elif "변호사시험" in cur["sourceFamilies"]:
            cur["primary"] = "변호사시험"
        else:
            cur["primary"] = "법무사시험"
    out = list(merged.values())
    for i, item in enumerate(out, 1):
        item["sourceFamilies"] = sorted(set(item["sourceFamilies"]), key=lambda x: FAMILY_ORDER.get(x, 99))
        item["scourtCount"] = sum(1 for s in item.get("sources", []) if s.get("family") == "법원직")
        item["barCount"] = sum(1 for s in item.get("sources", []) if s.get("family") == "변호사시험")
        item["bupmusaCount"] = sum(1 for s in item.get("sources", []) if s.get("family") == "법무사시험")
        item["freq"] = len(item.get("sources", []))
        item["sourceAtomCount"] = item["freq"]
        item["weightedSourceSum"], item["weight"] = weight_for_sources(item.get("sources", []))
        item["id"] = f"{prefix}-{i:05d}"
        for j, x in enumerate(item.get("x", []), 1):
            x["allTestId"] = x.get("allTestId") or f"{item['id']}-x-{j:02d}"
            x["truth"] = x.get("truth") or item.get("rep")
    out.sort(key=lambda x: (-x.get("weight", 0), x.get("art") or "zzz", x.get("rep") or ""))
    for i, item in enumerate(out, 1):
        item["id"] = f"{prefix}-{i:05d}"
    grade_items(out)
    return out


def to_app_atom(item: dict) -> dict:
    return {
        "o": item["rep"],
        "ans": item.get("a") or "O",
        "ref": item.get("ref"),
        "freq": item.get("freq", 1),
        "sources": item.get("refs", []),
        "sourceFamilies": item.get("sourceFamilies", []),
        "scourtCount": item.get("scourtCount", 0),
        "barCount": item.get("barCount", 0),
        "bupmusaCount": item.get("bupmusaCount", 0),
        "topic": item.get("topic"),
        "allTestId": item.get("id"),
        "sourceAtomCount": item.get("sourceAtomCount", 1),
        "x": [
            {
                "q": x.get("q"),
                "src": x.get("src"),
                "freq": x.get("freq", 1),
                "sources": x.get("sources", []),
                "sourceFamilies": x.get("sourceFamilies", []),
                "allTestId": x.get("allTestId"),
                "verified": bool(x.get("verified")),
                "truth": x.get("truth"),
                "weight": x.get("weight"),
                "grade": x.get("grade"),
            }
            for x in item.get("x", [])
        ],
        "verified": False,
        "weight": item.get("weight", 0),
        "grade": item.get("grade"),
    }


def build_ox(data: dict) -> list[dict]:
    ox = []
    oid = 0
    rows = []
    for article in data.get("articles", []):
        for at in article.get("atoms", []):
            rows.append((article.get("art"), article.get("pyeon"), at))
    for at in data.get("bucket", []):
        rows.append((at.get("art") or "변호사시험 기타", "변호사시험 기타", at))
    for art, pyeon, at in rows:
        oid += 1
        ans = at.get("ans") or "O"
        item = {
            "id": f"{ans}{oid}",
            "art": art,
            "pyeon": pyeon,
            "ans": ans,
            "stmt": at.get("o"),
            "ref": at.get("ref"),
            "freq": at.get("freq", 1),
            "sources": at.get("sources", []),
        }
        if ans == "X" and at.get("truth"):
            item["truth"] = at["truth"]
        ox.append(item)
        for xx in at.get("x") or []:
            oid += 1
            ox.append(
                {
                    "id": f"X{oid}",
                    "art": art,
                    "pyeon": pyeon,
                    "ans": "X",
                    "stmt": xx.get("q"),
                    "ref": at.get("ref"),
                    "freq": xx.get("freq", 1),
                    "sources": xx.get("sources") or ([xx.get("src")] if xx.get("src") else []),
                    "truth": xx.get("truth") or at.get("o"),
                }
            )
    return ox


def update_deploy_data(task: dict, base: dict, items: list[dict], stats: dict) -> dict:
    data = deepcopy(base)
    article_by_art = {a.get("art"): a for a in data.get("articles", [])}
    for article in data.get("articles", []):
        article["atoms"] = []
        article["count"] = 0
        article["freqMax"] = 0
    bucket = []
    for item in items:
        atom = to_app_atom(item)
        art = item.get("art")
        if art in article_by_art:
            article_by_art[art]["atoms"].append(atom)
        else:
            atom["art"] = item.get("sourceArt") or "변호사시험 기타"
            bucket.append(atom)
    for article in data.get("articles", []):
        article["atoms"].sort(key=lambda x: (-(x.get("weight") or 0), -(x.get("freq") or 1), x.get("o") or ""))
        article["count"] = len(article["atoms"])
        article["freqMax"] = max([a.get("freq", 1) for a in article["atoms"]] or [0])
    data["bucket"] = sorted(bucket, key=lambda x: (-(x.get("weight") or 0), x.get("o") or ""))
    data["ox"] = build_ox(data)
    data["version"] = task["version"]
    data["updatedAt"] = today()
    data["stats"] = {
        "atoms": sum(len(a.get("atoms", [])) for a in data.get("articles", [])) + len(data["bucket"]),
        "sourceAtoms": stats["inputAtoms"],
        "freq": sum(1 for item in items if item.get("freq", 1) >= 2),
        "articles": len(data.get("articles", [])),
        "quizArticles": sum(1 for a in data.get("articles", []) if a.get("atoms")),
        "ox": len(data["ox"]),
        "bucket": len(data["bucket"]),
        "legalVerified": 0,
        "legalReviewPending": len(data["ox"]),
        "scourtItems": stats["scourtInputAtoms"],
        "barItems": stats["barInputAtoms"],
        "bupmusaItems": stats.get("bupmusaInputAtoms", 0),
        "barUnresolvedXItems": stats.get("barUnresolvedXItems", 0),
        "crossSourceItems": sum(1 for item in items if len(item.get("sourceFamilies", [])) >= 2),
    }
    data["integration"] = {
        "mode": "all_test(법원직 중심)",
        "sources": ["법원직", "변호사시험", "법무사시험"],
        "barSourceWeight": 0.5,
        "scourtSourceWeight": 1.0,
        "bupmusaSourceWeight": 0.5,
        "barSubjects": sorted(task["bar_subjects"]),
        "barUnplacedPolicy": "조문번호가 확실하지 않은 변호사시험 atom은 bucket에 둠",
        "barUnresolvedXPolicy": "truth가 없는 변호사시험 X 지문은 대표 atom 또는 CBT 문항으로 노출하지 않음",
        "bupmusaUnplacedPolicy": "조문번호가 확실하지 않은 법무사시험 atom은 bucket에 둠",
    }
    data["weighting"] = {
        "H": HALF_LIFE_YEARS,
        "today": TODAY_DECIMAL,
        "formula": "W=ln(1+Σ s·0.5^(age/H)); 법원직 s=1.0, 변호사시험 s=0.5, 법무사시험 s=0.5",
        "gradeScope": f"{task['subject']} 통합 atom 내 상대평가",
    }
    return data


def build(task: dict) -> dict:
    base_path = DATA_DIR / f"{task['slug']}.json"
    base = read_json(base_path)
    existing_arts = {a.get("art") for a in base.get("articles", []) if a.get("art")}
    scourt_source_path = Path(task.get("scourt_integrated_file") or base_path)
    scourt = scourt_items(task, base)
    bar, skipped, unresolved_bar_x = bar_items(task, existing_arts)
    bupmusa, bupmusa_skipped = bupmusa_items(task, existing_arts)
    inherit_article_from_existing(bupmusa, scourt + bar)
    merged = merge_items(scourt + bar + bupmusa, f"all-{task['slug']}")
    grade_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for item in merged:
        grade_counts[item["grade"]] = grade_counts.get(item["grade"], 0) + 1
        fam_key = "+".join(item.get("sourceFamilies", []))
        family_counts[fam_key] = family_counts.get(fam_key, 0) + 1
    stats = {
        "scourtInputAtoms": len(scourt),
        "barInputAtoms": len(bar),
        "bupmusaInputAtoms": len(bupmusa),
        "inputAtoms": len(scourt) + len(bar) + len(bupmusa),
        "items": len(merged),
        "representativeOItems": sum(1 for item in merged if item.get("a") != "X"),
        "representativeXItems": sum(1 for item in merged if item.get("a") == "X"),
        "nestedXItems": sum(len(item.get("x", [])) for item in merged),
        "exactDuplicatesMerged": len(scourt) + len(bar) + len(bupmusa) - len(merged),
        "articles": len({item.get("art") for item in merged if item.get("art")}),
        "bucketItems": sum(1 for item in merged if not item.get("art")),
        "gradeCounts": grade_counts,
        "familyCounts": family_counts,
        "weightMax": max([item.get("weight", 0) for item in merged] or [0]),
        "weightMin": min([item.get("weight", 0) for item in merged] or [0]),
        "barSkipped": skipped,
        "barUnresolvedXItems": len(unresolved_bar_x),
        "bupmusaSkipped": bupmusa_skipped,
    }
    all_test = {
        "title": task["title"],
        "subject": task["subject"],
        "schema": task["schema"],
        "version": task["version"],
        "builtAt": today(),
        "sourceFiles": {
            "법원직": str(scourt_source_path),
            "변호사시험": str(BAR_DIR / task["bar_file"]),
            **({"법무사시험": str(BUPMUSA_DIR / task["bupmusa_file"])} if task.get("bupmusa_file") else {}),
        },
        "weighting": {
            "H": HALF_LIFE_YEARS,
            "today": TODAY_DECIMAL,
            "formula": "W=ln(1+Σ s·0.5^(age/H)); 법원직 s=1.0, 변호사시험 s=0.5, 법무사시험 s=0.5",
            "gradeScope": f"{task['subject']} 통합 atom 내 상대평가",
        },
        "integration": {
            "method": "exact-normalized-text-by-article",
            "barSubjectFilter": sorted(task["bar_subjects"]),
            "unplacedPolicy": "조문번호가 현행 화면 조문과 확실히 맞거나 기존 atom과 같은 법리문장으로 매칭될 때 조문에 배치",
            "barXPolicy": "truth가 없는 변호사시험 X 지문은 대표 atom으로 만들지 않고 unresolvedBarX에 보류",
        },
        "stats": stats,
        "unresolvedBarX": unresolved_bar_x,
        "items": merged,
    }
    write_json(task["out_dir"] / task["out_name"], all_test)
    app_data = update_deploy_data(task, base, merged, stats)
    write_json(base_path, app_data)
    (DATA_DIR / f"{task['slug']}.js").write_text(
        f"window.{task['window']} = " + json.dumps(app_data, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return {
        "subject": task["subject"],
        "allTest": str(task["out_dir"] / task["out_name"]),
        "deploy": str(base_path),
        "stats": stats,
        "appStats": app_data["stats"],
    }


def main() -> None:
    selected = set(sys.argv[1:])
    tasks = [task for task in TASKS if not selected or task["slug"] in selected]
    if selected and len(tasks) != len(selected):
        known = ", ".join(task["slug"] for task in TASKS)
        raise SystemExit(f"unknown task slug. known: {known}")
    results = [build(task) for task in tasks]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
