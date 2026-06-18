from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
LOCAL_PDF_ROOT = WORKSPACE / "0gichul_법과목_기출"

CHOICES = "①②③④⑤"
BOX_LABEL_RE = re.compile(r"([ㄱ-ㅎ])\s*[.)]\s*")

EXAMS = {
    2025: {
        "examId": "2025_bupmusa_1st",
        "year": 2025,
        "round": 31,
        "series": "법무사 제1차",
        "booklet": "①책형",
        "date": "2025-08-30",
        "pageUrl": "https://0gichul.com/y2025/130911268",
        "files": {
            "answers": {
                "url": "https://0gichul.com/files/attach/binaries/122010655/268/911/130/85a0103ce0acf37ce0028e47426d7e14",
                "name": "2025_법무사_1차_정답가안.pdf",
            },
            "period1": {
                "url": "https://0gichul.com/files/attach/binaries/122010655/268/911/130/e0a130dd3d1801477503da0003c2c16c",
                "name": "2025_법무사_1차_1교시_문제.pdf",
            },
            "period2": {
                "url": "https://0gichul.com/files/attach/binaries/122010655/268/911/130/18dcf579552c06134284032ee8e6efa5",
                "name": "2025_법무사_1차_2교시_문제.pdf",
            },
        },
    }
}

GROUPS = {
    1: {
        "period": "period1",
        "label": "제1과목",
        "subjects": [(1, 20, "헌법"), (21, 50, "상법")],
    },
    2: {
        "period": "period1",
        "label": "제2과목",
        "subjects": [(1, 40, "민법"), (41, 50, "가족관계의 등록 등에 관한 법률")],
    },
    3: {
        "period": "period2",
        "label": "제3과목",
        "subjects": [(1, 35, "민사집행법"), (36, 50, "상업등기법 및 비송사건절차법")],
    },
    4: {
        "period": "period2",
        "label": "제4과목",
        "subjects": [(1, 30, "부동산등기법"), (31, 50, "공탁법")],
    },
}

SUBJECT_FILE_NAMES = {
    "헌법": "헌법",
    "상법": "상법",
    "민법": "민법",
    "가족관계의 등록 등에 관한 법률": "가족관계등록법",
    "민사집행법": "민사집행법",
    "상업등기법 및 비송사건절차법": "상업등기법_비송사건절차법",
    "부동산등기법": "부동산등기법",
    "공탁법": "공탁법",
}


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(url: str, path: Path, referer: str) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": referer,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        path.write_bytes(response.read())


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def subject_file_name(subject: str) -> str:
    if subject in SUBJECT_FILE_NAMES:
        return SUBJECT_FILE_NAMES[subject]
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", subject).strip("_")


def compact(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"([,.;:?!])(?=\S)", r"\1 ", text)
    return text


def find_local_subject_pdfs(year: int) -> dict[str, list[dict[str, str]]]:
    if not LOCAL_PDF_ROOT.exists():
        return {}
    out: dict[str, list[dict[str, str]]] = {}
    for path in LOCAL_PDF_ROOT.rglob(f"{year}_법무사_*.pdf"):
        subject = path.parent.name
        kind = "commentary" if "해설" in path.name else "problem"
        out.setdefault(subject, []).append(
            {
                "kind": kind,
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return {subject: sorted(rows, key=lambda row: (row["kind"], row["path"])) for subject, rows in sorted(out.items())}


def subject_for(group: int, no: int) -> str:
    for start, end, subject in GROUPS[group]["subjects"]:
        if start <= no <= end:
            return subject
    raise ValueError(f"unknown subject for group {group}, no {no}")


def question_type(stem: str) -> str:
    stem = stem.replace(" ", "")
    if "몇개" in stem:
        if "옳지않은" in stem or "아닌" in stem:
            return "count-false"
        if "옳은" in stem:
            return "count-true"
        if "있는경우" in stem or "해당하는경우" in stem or "할수있는경우" in stem:
            return "count-true"
        return "count-unknown"
    if "아닌것끼리고른" in stem or "아닌것을모두고른" in stem:
        return "multi-select-false"
    if "옳지않은것을모두고른" in stem:
        return "multi-select-false"
    if "옳은것을모두고른" in stem:
        return "multi-select-true"
    if "경우를모두고른" in stem or "해당하는것을모두고른" in stem or "있는것을모두고른" in stem:
        return "multi-select-true"
    if "옳지않은" in stem:
        return "single-best-false"
    if "아닌것은" in stem and "몇개" not in stem:
        return "single-best-false"
    if "옳은" in stem:
        return "single-best-true"
    return "unknown"


def restore_answers(answer_text: str) -> dict[int, dict[int, str]]:
    pairs = re.findall(r"(\d{1,2})([\u2460-\u2464])", answer_text)
    if len(pairs) < 200:
        raise ValueError(f"answer table has only {len(pairs)} pairs")
    pairs = pairs[-200:]
    answers: dict[int, dict[int, str]] = {i: {} for i in range(1, 5)}
    for row in range(25):
        chunk = pairs[row * 8 : (row + 1) * 8]
        for group in range(1, 5):
            n1, a1 = chunk[(group - 1) * 2]
            n2, a2 = chunk[(group - 1) * 2 + 1]
            answers[group][int(n1)] = a1
            answers[group][int(n2)] = a2
    for group, rows in answers.items():
        missing = [i for i in range(1, 51) if i not in rows]
        if missing:
            raise ValueError(f"group {group} answer missing: {missing}")
    return answers


def group_slice(text: str, group: int) -> str:
    label = GROUPS[group]["label"]
    start_match = re.search(rf"【\s*{label}\s*50문제\s*】", text)
    if not start_match:
        raise ValueError(f"cannot find {label}")
    next_group = group + 1
    if next_group in GROUPS and GROUPS[next_group]["period"] == GROUPS[group]["period"]:
        next_label = GROUPS[next_group]["label"]
        next_match = re.search(rf"【\s*{next_label}\s*50문제\s*】", text[start_match.end() :])
        end = start_match.end() + next_match.start() if next_match else len(text)
    else:
        end = len(text)
    return text[start_match.start() : end]


def split_questions(group_text: str) -> dict[int, str]:
    matches = list(re.finditer(r"【문\s*(\d{1,2})】", group_text))
    out: dict[int, str] = {}
    for i, match in enumerate(matches):
        no = int(match.group(1))
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(group_text)
        body = group_text[start:end]
        body = re.sub(r"【\s*제\d과목\s*50문제\s*】\s*①책형", " ", body)
        body = re.sub(r"【[^】]*\d+문】", " ", body)
        body = re.sub(r"제\d과목\s*①책형\s*전체\s*\d+-\d+", " ", body)
        out[no] = compact(body)
    return out


def is_choice_marker(text: str, marker: re.Match[str]) -> bool:
    prev = text[: marker.start()].rstrip()
    next_text = text[marker.end() : marker.end() + 3].lstrip()
    if prev and prev[-1] == "위" and next_text.startswith("의"):
        return False
    return True


def parse_question_text(text: str) -> tuple[str, list[dict[str, str]]]:
    markers = [m for m in re.finditer(r"[\u2460-\u2464]", text) if is_choice_marker(text, m)]
    if len(markers) > 5 and "".join(m.group(0) for m in markers[-5:]) == CHOICES:
        markers = markers[-5:]
    if not markers:
        return compact(text), []
    stem = compact(text[: markers[0].start()])
    choices = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        choices.append({"label": marker.group(0), "text": compact(text[marker.end() : end])})
    return stem, choices


def split_box_statements(stem: str) -> list[dict[str, str]]:
    markers = list(BOX_LABEL_RE.finditer(stem))
    if not markers:
        return []
    out = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(stem)
        statement = compact(stem[marker.end() : end])
        if statement:
            out.append({"label": marker.group(1), "text": statement})
    return out


def selected_box_labels(question: dict) -> set[str]:
    answer_text = question["original"].get("officialAnswerText") or ""
    return set(re.findall(r"[ㄱ-ㅎ]", answer_text))


def derive_verdict(question: dict, unit: dict) -> tuple[str | None, str]:
    qtype = question["type"]
    if unit["unitType"] == "choice" and qtype in {"single-best-false", "single-best-true"}:
        is_answer_choice = unit["label"] == question["original"]["officialAnswer"]
        if qtype == "single-best-false":
            return ("X" if is_answer_choice else "O"), "official-single-best"
        return ("O" if is_answer_choice else "X"), "official-single-best"

    if unit["unitType"] == "box":
        selected = selected_box_labels(question)
        if selected and qtype in {"multi-select-true", "single-best-true"}:
            return ("O" if unit["label"] in selected else "X"), "official-combination"
        if selected and qtype in {"multi-select-false", "single-best-false"}:
            return ("X" if unit["label"] in selected else "O"), "official-combination"

    return None, "requires-legal-basis-review"


def build_atom_queue_items(question: dict) -> list[dict]:
    box_units = split_box_statements(question["original"]["stem"])
    if box_units:
        units = [{"unitType": "box", **unit} for unit in box_units]
    else:
        units = [{"unitType": "choice", **choice} for choice in question["original"]["choices"]]

    items = []
    for unit in units:
        verdict, derivation = derive_verdict(question, unit)
        unit_label = unit["label"]
        unit_id = f"{question['qid']}-{unit_label}"
        items.append(
            {
                "unitId": unit_id,
                "examId": question["examId"],
                "sourceFamily": "법무사시험",
                "source": question["sourceLabel"],
                "year": question["year"],
                "round": question["round"],
                "group": question["group"],
                "subject": question["subject"],
                "no": question["no"],
                "unitType": unit["unitType"],
                "unitLabel": unit_label,
                "rawStatement": unit["text"],
                "sourceQuestionType": question["type"],
                "officialQuestionAnswer": question["original"]["officialAnswer"],
                "officialQuestionAnswerText": question["original"]["officialAnswerText"],
                "originalVerdict": verdict,
                "verdictDerivation": derivation,
                "atomWork": {
                    "status": "basis-needed",
                    "instruction": "원문 지문을 그대로 옮기지 말고, O/X 판단 근거인 조문·판례·학설 지점을 자기완결식 atom으로 작성한다.",
                    "basisTypesAllowed": ["조문", "판례", "학설"],
                    "basisType": None,
                    "basisRef": None,
                    "atomRep": None,
                    "xDependsOn": None,
                    "reviewedAt": None,
                    "currentLawVerdict": None,
                    "needs": [
                        "legal-basis-search",
                        "atom-normalization",
                        "current-law-check",
                    ],
                },
            }
        )
    return items


def write_subject_files(year: int, source: dict, atom_queue_doc: dict, out_dir: Path) -> dict[str, dict[str, object]]:
    subject_dir = out_dir / str(year) / "과목별"
    subject_paths: dict[str, dict[str, object]] = {}
    subjects = sorted({question["subject"] for question in source["questions"]})
    for subject in subjects:
        file_subject = subject_file_name(subject)
        questions = [question for question in source["questions"] if question["subject"] == subject]
        items = [item for item in atom_queue_doc["items"] if item["subject"] == subject]
        subject_source = {
            **source,
            "schema": "legal-scrivener/problem-original-current-by-subject/v1",
            "subject": subject,
            "questions": questions,
            "subjectSummary": {
                "questionCount": len(questions),
                "atomQueueItemCount": len(items),
            },
        }
        subject_queue = {
            **atom_queue_doc,
            "schema": "legal-scrivener/atom-queue-by-subject/v1",
            "subject": subject,
            "items": items,
            "subjectSummary": {
                "questionCount": len(questions),
                "atomQueueItemCount": len(items),
            },
        }
        source_path = subject_dir / f"{year}_법무사_{file_subject}_source.json"
        queue_path = subject_dir / f"{year}_법무사_{file_subject}_atom_queue.json"
        write_json(source_path, subject_source)
        write_json(queue_path, subject_queue)
        subject_paths[subject] = {
            "source": str(source_path),
            "atomQueue": str(queue_path),
            "questionCount": len(questions),
            "atomQueueItemCount": len(items),
        }
    return subject_paths


def build_year(year: int) -> tuple[Path, Path, Path]:
    meta = EXAMS[year]
    raw_dir = PRIVATE_ROOT / "raw" / str(year)
    text_dir = PRIVATE_ROOT / "text" / str(year)
    out_dir = PRIVATE_ROOT / "current"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    local_subject_pdfs = find_local_subject_pdfs(year)
    pdf_paths: dict[str, Path] = {}
    for key, file_meta in meta["files"].items():
        path = raw_dir / file_meta["name"]
        download(file_meta["url"], path, meta["pageUrl"])
        pdf_paths[key] = path

    texts: dict[str, str] = {}
    for key, path in pdf_paths.items():
        text = pdf_text(path)
        texts[key] = text
        (text_dir / f"{path.stem}.txt").write_text(text, encoding="utf-8")

    answers = restore_answers(texts["answers"])

    questions = []
    for group in range(1, 5):
        period = GROUPS[group]["period"]
        sliced = group_slice(texts[period], group)
        qtexts = split_questions(sliced)
        missing = [i for i in range(1, 51) if i not in qtexts]
        if missing:
            raise ValueError(f"group {group} question missing: {missing}")
        for no in range(1, 51):
            stem, choices = parse_question_text(qtexts[no])
            official = answers[group][no]
            official_text = next((c["text"] for c in choices if c["label"] == official), "")
            subject = subject_for(group, no)
            question = {
                "qid": f"{year}-g{group}-{no:02d}",
                "examId": meta["examId"],
                "year": year,
                "round": meta["round"],
                "series": meta["series"],
                "group": group,
                "groupLabel": GROUPS[group]["label"],
                "subject": subject,
                "no": no,
                "sourceLabel": f"법무사{meta['round']}회 {GROUPS[group]['label']} {no}번",
                "extraction": {
                    "problemPdf": str(pdf_paths[period]),
                    "preferredLocalSubjectPdf": next(
                        (
                            row["path"]
                            for row in local_subject_pdfs.get(subject, [])
                            if row["kind"] == "problem"
                        ),
                        None,
                    ),
                },
                "type": question_type(stem),
                "original": {
                    "stem": stem,
                    "choices": choices,
                    "officialAnswer": official,
                    "officialAnswerText": official_text,
                },
                "current": {
                    "changedByCurrentLaw": False,
                    "stem": stem,
                    "choices": choices,
                    "currentAnswer": official,
                    "currentAnswerText": official_text,
                    "reviewedAt": None,
                    "reviewNote": "현행법 기준 검증 전",
                },
            }
            questions.append(question)

    source = {
        "schema": "legal-scrivener/problem-original-current/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "sourcePolicy": {
            "problemOriginal": "이미 내려받은 과목별 PDF를 우선 기준으로 확인하고, 과목별 PDF가 없는 과목은 공개 법무사시험 제1차 통합 문제 PDF와 정답가안에서 추출",
            "current": "현행법 기준 수정본은 current 필드에 별도 보존",
            "storage": "로컬 private JSON 생성 후 Supabase 적재 대상으로 사용",
        },
        "exam": {
            "examId": meta["examId"],
            "year": year,
            "round": meta["round"],
            "series": meta["series"],
            "booklet": meta["booklet"],
            "date": meta["date"],
            "questionCount": len(questions),
            "sources": {
                "pageUrl": meta["pageUrl"],
                "problemPdfPeriod1": str(pdf_paths["period1"]),
                "problemPdfPeriod2": str(pdf_paths["period2"]),
                "answerPdf": str(pdf_paths["answers"]),
                "answerBasis": "제31회 법무사 제1차 시험 정답가안 ①책형",
                "localSubjectPdfs": local_subject_pdfs,
            },
            "pdfSha256": {key: sha256(path) for key, path in pdf_paths.items()},
            "rawTextSha256": {key: hashlib.sha256(text.encode("utf-8")).hexdigest() for key, text in texts.items()},
            "answers": {str(group): {str(no): ans for no, ans in rows.items()} for group, rows in answers.items()},
        },
        "questions": questions,
    }

    atom_queue_items = []
    for question in questions:
        atom_queue_items.extend(build_atom_queue_items(question))
    atom_queue_doc = {
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "examId": meta["examId"],
        "year": year,
        "round": meta["round"],
        "queuePolicy": {
            "coverage": "일반 보기, 개수형, 조합형, 박스형의 모든 판단 지문을 atom 제작 대상으로 큐에 올린다.",
            "atomPrinciple": "atom은 지문 복사본이 아니라 O/X 판단 근거인 조문·판례·학설 지점이다.",
            "verdict": "공식정답으로 역산 가능한 경우 originalVerdict를 채우고, 개수형 등 확정 불가능한 경우 근거 검토 대상으로 둔다.",
            "xHandling": "X 지문은 독립 atom이 아니라 올바른 O atom 또는 근거 법리에 종속시킨다.",
        },
        "items": atom_queue_items,
    }

    source_path = out_dir / f"legal_scrivener_{year}_source.json"
    queue_path = out_dir / f"legal_scrivener_{year}_atom_queue.json"
    subject_index_path = out_dir / str(year) / "과목별" / f"{year}_법무사_과목별_index.json"
    legacy_candidate_path = out_dir / f"legal_scrivener_{year}_ox_candidates.json"
    write_json(source_path, source)
    write_json(queue_path, atom_queue_doc)
    subject_paths = write_subject_files(year, source, atom_queue_doc, out_dir)
    write_json(
        subject_index_path,
        {
            "schema": "legal-scrivener/subject-index/v1",
            "sourceFamily": "법무사시험",
            "updatedAt": today(),
            "examId": meta["examId"],
            "year": year,
            "round": meta["round"],
            "subjects": subject_paths,
        },
    )
    if legacy_candidate_path.exists():
        legacy_candidate_path.unlink()
    return source_path, queue_path, subject_index_path


def main() -> None:
    source_path, queue_path, subject_index_path = build_year(2025)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    by_subject: dict[str, int] = {}
    for q in source["questions"]:
        by_subject[q["subject"]] = by_subject.get(q["subject"], 0) + 1
    queue_by_subject: dict[str, int] = {}
    queue_by_derivation: dict[str, int] = {}
    for item in queue["items"]:
        queue_by_subject[item["subject"]] = queue_by_subject.get(item["subject"], 0) + 1
        key = item["verdictDerivation"]
        queue_by_derivation[key] = queue_by_derivation.get(key, 0) + 1
    print(f"source={source_path}")
    print(f"atomQueue={queue_path}")
    print(f"subjectIndex={subject_index_path}")
    print(f"questions={len(source['questions'])}")
    print(f"atomQueueItems={len(queue['items'])}")
    print("subjects=" + ", ".join(f"{k}:{v}" for k, v in by_subject.items()))
    print("queueSubjects=" + ", ".join(f"{k}:{v}" for k, v in queue_by_subject.items()))
    print("verdictDerivation=" + ", ".join(f"{k}:{v}" for k, v in queue_by_derivation.items()))


if __name__ == "__main__":
    main()
