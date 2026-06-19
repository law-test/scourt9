from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
CURRENT_ROOT = PRIVATE_ROOT / "current"
SUBJECT_NAME = "상법"
OUT_PATH = CURRENT_ROOT / "통합본" / "법무사_상법_통합_atom.json"

TODAY_DECIMAL = 2026.46
HALF_LIFE_YEARS = 4.0
SOURCE_WEIGHT = 1.0
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


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("·", "ㆍ").replace("∙", "ㆍ").lower()


def year_to_exam_date(year: int) -> float:
    return year + 8.0 / 12.0


def weight_for_sources(sources: list[dict[str, object]]) -> tuple[float, float]:
    total = 0.0
    seen = set()
    for src in sources:
        key = (src.get("sourceId"), src.get("source"))
        if key in seen:
            continue
        seen.add(key)
        age = max(0.0, TODAY_DECIMAL - year_to_exam_date(int(src.get("year", TODAY_DECIMAL - 14))))
        total += float(src.get("s", SOURCE_WEIGHT)) * (0.5 ** (age / HALF_LIFE_YEARS))
    return round(total, 6), round(math.log1p(total), 4)


def grade_items(items: list[dict[str, object]]) -> None:
    ranked = sorted(items, key=lambda item: (-float(item["weight"]), str(item["rep"])))
    n = max(1, len(ranked))
    for rank, item in enumerate(ranked, 1):
        pct = rank / n
        item["rank"] = rank
        item["grade"] = next(grade for cut, grade in GRADE_CUTS if pct <= cut)


def source_label(atom: dict[str, object]) -> str:
    label = atom.get("unitLabel")
    label_text = f" {label}" if label else ""
    return f"{atom['year']} 법무사 {atom['round']}회 {SUBJECT_NAME} {atom['no']}번{label_text}"


def source_from_atom(atom: dict[str, object]) -> dict[str, object]:
    return {
        "family": "법무사시험",
        "s": SOURCE_WEIGHT,
        "year": atom["year"],
        "round": atom["round"],
        "subject": SUBJECT_NAME,
        "source": source_label(atom),
        "sourceId": atom["atomId"],
        "sourceUnitId": atom["sourceUnitId"],
        "sourceVerdict": atom["sourceVerdict"],
        "sourceTrap": atom["sourceTrap"],
        "sourceStatement": atom["sourceStatement"],
    }


def new_integrated_item(atom: dict[str, object], source: dict[str, object]) -> dict[str, object]:
    return {
        "primary": "법무사시험",
        "sourceFamilies": ["법무사시험"],
        "subject": SUBJECT_NAME,
        "topic": atom.get("topic") or f"{SUBJECT_NAME} {atom['no']}번",
        "rep": atom["rep"],
        "a": atom["a"],
        "why": atom["why"],
        "basisType": atom["basisType"],
        "basisRef": atom["basisRef"],
        "sources": [source],
        "refs": [source["source"]],
        "sourceIds": [source["sourceId"]],
        "sourceAtomCount": 1,
        "quality": {
            "statementType": "declarative",
            "displayable": True,
            "normalizers": [],
            "changed": False,
        },
        "verification": {
            "status": "needs-legal-review",
            "lawAsOf": today(),
            "legalVerifiedAt": None,
            "statuteCitationStatus": "pending",
        },
    }


def atom_files() -> list[Path]:
    files = sorted(CURRENT_ROOT.glob("20*/과목별/*_법무사_상법_atoms.json"), reverse=True)
    return [path for path in files if re.search(r"\\(20\d{2})\\과목별\\", str(path))]


def load_atoms(path: Path) -> list[dict[str, object]]:
    data = read_json(path)
    if data.get("subject") != SUBJECT_NAME:
        raise ValueError(f"not commercial law atoms: {path}")
    return list(data.get("items", []))


def validate_atoms(atoms: list[dict[str, object]], path: Path) -> None:
    if not atoms:
        raise ValueError(f"empty atom file: {path}")
    ids = [atom["atomId"] for atom in atoms]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate atom ids in {path}")
    banned = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "옳은 것은", "옳지 않은 것은"]
    for atom in atoms:
        rep = str(atom.get("rep", ""))
        if any(token in rep for token in banned):
            raise ValueError(f"non-atom wording in {atom['atomId']}: {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in {atom['atomId']}: {rep}")
        if atom.get("sourceVerdict") == "X":
            if not atom.get("sourceTrap") or atom.get("xDependsOn") != rep:
                raise ValueError(f"bad X dependency in {atom['atomId']}")
        elif atom.get("sourceTrap") is not None or atom.get("xDependsOn") is not None:
            raise ValueError(f"unexpected X metadata in {atom['atomId']}")
        if atom.get("currentVerdict") != "O" or atom.get("a") != "O":
            raise ValueError(f"completed atom must be O in {atom['atomId']}")


def build() -> dict[str, object]:
    files = atom_files()
    buckets: dict[tuple[str, str], dict[str, object]] = {}
    input_atoms = 0
    source_files: dict[str, str] = {}
    years: set[int] = set()
    verdict_counts: Counter[str] = Counter()

    for path in files:
        year = int(path.name[:4])
        atoms = load_atoms(path)
        validate_atoms(atoms, path)
        source_files[str(year)] = str(path)
        years.add(year)
        input_atoms += len(atoms)
        for atom in atoms:
            verdict_counts[str(atom["sourceVerdict"])] += 1
            key = (str(atom["a"]), normalize_key(str(atom["rep"])))
            source = source_from_atom(atom)
            if key not in buckets:
                buckets[key] = new_integrated_item(atom, source)
            elif source["sourceId"] not in buckets[key]["sourceIds"]:
                buckets[key]["sources"].append(source)
                buckets[key]["refs"].append(source["source"])
                buckets[key]["sourceIds"].append(source["sourceId"])
                buckets[key]["sourceAtomCount"] = int(buckets[key]["sourceAtomCount"]) + 1

    items = list(buckets.values())
    for index, item in enumerate(items, 1):
        item["freq"] = len(item["sources"])
        item["weightedSourceSum"], item["weight"] = weight_for_sources(item["sources"])
        item["id"] = f"bupmusa-commercial-law-integrated-{index:05d}"
    grade_items(items)
    items.sort(key=lambda item: (int(item["rank"]), str(item["id"])))

    stats = {
        "sourceYears": sorted(years, reverse=True),
        "inputAtoms": input_atoms,
        "items": len(items),
        "duplicatesMerged": max(0, input_atoms - len(items)),
        "sourceVerdictCounts": dict(verdict_counts),
        "gradeCounts": dict(Counter(str(item["grade"]) for item in items)),
    }
    return {
        "title": "법무사_상법 통합 atom",
        "subject": SUBJECT_NAME,
        "schema": "bupmusa/commercial-law-integrated-atom/v1",
        "version": "bupmusa_commercial_law_v002_2024_2025_integrated",
        "builtAt": today(),
        "sourceFiles": source_files,
        "weighting": {
            "H": HALF_LIFE_YEARS,
            "today": TODAY_DECIMAL,
            "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0",
            "gradeScope": "법무사 상법 통합 atom 내 상대평가",
        },
        "integration": {
            "method": "exact-normalized-text",
            "scope": "법무사시험 상법 누적",
        },
        "stats": stats,
        "items": items,
    }


def validate_integrated(doc: dict[str, object]) -> None:
    items = list(doc.get("items", []))
    if not items:
        raise ValueError("empty integrated document")
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate integrated ids")
    source_ids = [source["sourceId"] for item in items for source in item.get("sources", [])]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate integrated source ids")
    if int(doc["stats"]["inputAtoms"]) != len(source_ids):
        raise ValueError("input atom count mismatch")


def main() -> None:
    doc = build()
    validate_integrated(doc)
    write_json(OUT_PATH, doc)
    print(f"wrote {OUT_PATH}")
    print(f"years={doc['stats']['sourceYears']}")
    print(f"inputAtoms={doc['stats']['inputAtoms']} items={doc['stats']['items']} merged={doc['stats']['duplicatesMerged']}")
    print(f"sourceVerdict={doc['stats']['sourceVerdictCounts']}")


if __name__ == "__main__":
    main()
