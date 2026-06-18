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

CHOICES = "①②③④⑤"

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


def compact(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"([,.;:?!])(?=\S)", r"\1 ", text)
    return text


def subject_for(group: int, no: int) -> str:
    for start, end, subject in GROUPS[group]["subjects"]:
        if start <= no <= end:
            return subject
    raise ValueError(f"unknown subject for group {group}, no {no}")


def question_type(stem: str) -> str:
    stem = stem.replace(" ", "")
    if "옳지않은것을모두고른" in stem:
        return "multi-select-false"
    if "옳은것을모두고른" in stem:
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


def build_candidates(question: dict) -> list[dict]:
    qtype = question["type"]
    if qtype not in {"single-best-false", "single-best-true"}:
        return []
    out = []
    answer = question["original"]["officialAnswer"]
    for choice in question["original"]["choices"]:
        if qtype == "single-best-false":
            verdict = "X" if choice["label"] == answer else "O"
        else:
            verdict = "O" if choice["label"] == answer else "X"
        out.append(
            {
                "candidateId": f"{question['qid']}-{choice['label']}",
                "examId": question["examId"],
                "sourceFamily": "법무사시험",
                "source": question["sourceLabel"],
                "year": question["year"],
                "round": question["round"],
                "group": question["group"],
                "subject": question["subject"],
                "no": question["no"],
                "choice": choice["label"],
                "statement": choice["text"],
                "answer": verdict,
                "sourceQuestionType": qtype,
                "needsAtomNormalization": True,
                "needsLegalReview": True,
            }
        )
    return out


def build_year(year: int) -> tuple[Path, Path]:
    meta = EXAMS[year]
    raw_dir = PRIVATE_ROOT / "raw" / str(year)
    text_dir = PRIVATE_ROOT / "text" / str(year)
    out_dir = PRIVATE_ROOT / "current"
    raw_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

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
            "problemOriginal": "공개 법무사시험 제1차 문제 PDF 및 정답가안에서 추출",
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
            },
            "pdfSha256": {key: sha256(path) for key, path in pdf_paths.items()},
            "rawTextSha256": {key: hashlib.sha256(text.encode("utf-8")).hexdigest() for key, text in texts.items()},
            "answers": {str(group): {str(no): ans for no, ans in rows.items()} for group, rows in answers.items()},
        },
        "questions": questions,
    }

    candidates = []
    for question in questions:
        candidates.extend(build_candidates(question))
    candidate_doc = {
        "schema": "legal-scrivener/ox-candidates/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "examId": meta["examId"],
        "year": year,
        "round": meta["round"],
        "candidatePolicy": "single-best true/false 문항만 보기별 OX 후보를 자동 산출하고, 모두 고르기 문항은 원문만 보존",
        "items": candidates,
    }

    source_path = out_dir / f"legal_scrivener_{year}_source.json"
    candidate_path = out_dir / f"legal_scrivener_{year}_ox_candidates.json"
    write_json(source_path, source)
    write_json(candidate_path, candidate_doc)
    return source_path, candidate_path


def main() -> None:
    source_path, candidate_path = build_year(2025)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
    by_subject: dict[str, int] = {}
    for q in source["questions"]:
        by_subject[q["subject"]] = by_subject.get(q["subject"], 0) + 1
    print(f"source={source_path}")
    print(f"candidates={candidate_path}")
    print(f"questions={len(source['questions'])}")
    print(f"candidateItems={len(candidates['items'])}")
    print("subjects=" + ", ".join(f"{k}:{v}" for k, v in by_subject.items()))


if __name__ == "__main__":
    main()
