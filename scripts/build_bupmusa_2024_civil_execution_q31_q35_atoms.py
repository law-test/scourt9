# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import build_bupmusa_2024_civil_execution_q01_q10_atoms as base


base.PART = "q31-q35"
base.QUESTION_RANGE = range(31, 36)
base.SOURCE_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_q31_q35_source.json"
base.QUEUE_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_q31_q35_atom_queue.json"
base.OUT_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_q31_q35_atoms.json"
base.EXPECTED_ATOM_COUNT = 25

INDEX_PATH = base.SUBJECT_DIR / "2024_법무사_과목별_index.json"
FULL_SOURCE_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_source.json"
FULL_QUEUE_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_atom_queue.json"
FULL_OUT_PATH = base.SUBJECT_DIR / "2024_법무사_민사집행법_atoms.json"

PART_SPECS = [
    (
        "q01-q10",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_source.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_atom_queue.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_atoms.json",
    ),
    (
        "q11-q20",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q11_q20_source.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q11_q20_atom_queue.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q11_q20_atoms.json",
    ),
    (
        "q21-q30",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q21_q30_source.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q21_q30_atom_queue.json",
        base.SUBJECT_DIR / "2024_법무사_민사집행법_q21_q30_atoms.json",
    ),
    ("q31-q35", base.SOURCE_PATH, base.QUEUE_PATH, base.OUT_PATH),
]

base.LEGAL_SOURCES = [
    {"title": "민사집행법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민사집행법"},
    {"title": "민사집행규칙", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민사집행규칙"},
    {"title": "주택임대차보호법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/주택임대차보호법"},
    {"title": "근로기준법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/근로기준법"},
    {"title": "민사집행 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
    {"title": "2024 법무사 민사집행법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881313"},
]

base.OFFICIAL_ANSWERS = {
    31: "⑤",
    32: "③",
    33: "⑤",
    34: "④",
    35: "④",
}

base.QUESTION_TYPES = {no: "single-best-false" for no in base.QUESTION_RANGE}
base.UNIT_LABELS = {no: ["①", "②", "③", "④", "⑤"] for no in base.QUESTION_RANGE}
base.FALSE_LABELS = {no: {answer} for no, answer in base.OFFICIAL_ANSWERS.items()}

base.TOPICS = {
    31: "자동차에 대한 강제집행",
    32: "즉시항고",
    33: "부동산경매절차의 임차인",
    34: "금전채권 강제집행의 제3채무자",
    35: "부동산경매절차의 임금채권자",
}

base.REP_ROWS = """
31|①|법원은 영업상의 필요이나 그 밖의 상당한 이유가 있다고 인정하면 이해관계인의 신청에 따라 강제집행 대상 자동차의 운행을 허가할 수 있다.|
31|②|자동차 강제경매개시결정에 기초한 자동차 인도집행은 그 개시결정이 채무자에게 송달되기 전에도 할 수 있다.|
31|③|자동차 강제경매개시결정이 채무자에게 송달되거나 등록되기 전에 집행관이 자동차를 인도받으면 그 인도받은 때 압류의 효력이 발생한다.|
31|④|자동차집행 신청이 취하되거나 강제경매절차 취소결정의 효력이 생기면 법원사무관등은 집행관에게 그 취지를 통지하여야 하고, 자동차를 수취할 권리자가 채무자 외의 사람이면 집행관은 그 사람에게도 그 취지를 통지하여야 한다.|
31|⑤|자동차집행 신청 취하나 강제경매절차 취소 후 집행관이 자동차를 수취할 권리자에게 자동차를 인도할 수 없으면, 법원은 집행관의 신청을 받아 자동차집행절차에 따라 자동차를 매각한다는 결정을 할 수 있다.|법원이 직권으로 자동차 매각결정을 하여야 한다고 한 부분
32|①|집행비용액확정결정은 집행종료 후의 재판이므로 그 결정에 대한 즉시항고에는 항고이유서 제출에 관한 민사집행법 제15조 제3항 및 제5항이 적용되지 않는다.|
32|②|집행정지서류가 제출되었는데도 집행기관이 집행을 정지하지 않고 집행처분을 하였더라도, 집행에 관한 이의나 즉시항고 없이 강제집행절차가 그대로 완결되면 그 집행행위로 발생한 법률효과를 부인할 수 없다.|
32|③|주식양도명령이 이미 성립한 뒤 그 명령이 채무자에게 송달되기 전에 채무자가 제기한 즉시항고는 명령의 효력발생 전이라는 이유만으로 부적법하다고 볼 수 없다.|주식양도명령 송달 전 즉시항고를 항고권 발생 전의 부적법한 항고라고 한 부분
32|④|민사집행법상 즉시항고를 할 수 있는 사람이 재판을 고지받아야 할 사람이 아닌 경우, 즉시항고 제기기간은 그 재판을 고지받아야 할 사람 모두에게 고지된 날부터 진행한다.|
32|⑤|민사집행법상 즉시항고는 1주일 안에 제기하여야 하고 10일 안에 항고이유서를 제출하여야 하지만, 집행에 관한 이의신청에는 이러한 기간 제한이 적용되지 않는다.|
33|①|주택임대차보호법상 대항요건을 갖춘 임차인이 현황조사에서 임차인으로 조사·보고되었더라도 매각허가결정 전까지 스스로 권리를 증명하여 신고하지 않으면 경매절차의 이해관계인이 될 수 없다.|
33|②|경매절차 진행사실을 주택임차인에게 알리는 통지는 법률상 의무가 아니라 편의상 안내이므로, 임차인이 권리신고 전에 그 통지를 받지 못했다는 사정만으로 매각허가결정의 불복사유가 되지 않는다.|
33|③|매각허가결정 확정 후 대금지급기일이 정해진 상태에서 대항력 있는 임차인이 매각대금 납부 전에 선순위저당권의 피담보채무를 대위변제하면, 그 임차권의 대항력은 소멸하지 않는다.|
33|④|확정일자를 갖춘 임차인이 여러 명이고 모두 저당권자보다 우선하는 경우에는 각 임차인별 우선변제권을 인정하되, 임차인 상호 간에는 대항요건과 확정일자를 최종적으로 갖춘 순서로 우열을 정하고, 선순위 가압류권자에게는 우선권을 주장할 수 없다.|
33|⑤|임차인이 임차보증금 일부만 지급한 뒤 대항요건과 확정일자를 갖추고 나머지 보증금을 나중에 지급하였더라도, 특별한 사정이 없으면 대항요건과 확정일자를 갖춘 때를 기준으로 임차보증금 전액에 대한 우선변제권을 가진다.|나머지 보증금을 나중에 지급하면 임차보증금 전액에 대한 우선변제권을 가질 수 없다고 한 부분
34|①|원인채권 압류의 효력이 발생하기 전에 제3채무자가 그 지급을 위하여 어음이나 수표를 발행하면, 원인채권 압류의 효력은 어음·수표채권에 미치지 않고 제3채무자는 어음·수표 소지인에 대한 지급으로 원인채권 소멸을 압류채권자에게 대항할 수 있다.|
34|②|물품대금채권에 대한 가압류나 압류의 효력 발생 전에 물품대금 지급을 위한 신용장이 발행되면, 그 뒤 신용장대금이 지급되었더라도 수입업자는 물품대금채권 소멸을 가압류채권자나 압류채권자에게 대항할 수 있다.|
34|③|동산양도담보권자가 물상대위권 행사로 양도담보설정자의 화재보험금청구권에 압류 및 추심명령을 받은 경우, 특별한 사정이 없는 한 제3채무자인 보험회사는 양도담보 설정 후 취득한 별개 채권을 자동채권으로 하여 양도담보권자에게 상계로 대항할 수 없다.|
34|④|제3채무자의 상계 대항 법리는 피압류채권이 장래 발생할 채권으로서 압류의 효력 발생 당시 아직 발생하지 않은 경우에도, 피압류채권 발생의 기초관계와 상계 기대가 인정되면 적용될 수 있다.|피압류채권이 압류 당시 아직 발생하지 않은 장래채권이면 제3채무자의 상계 대항 법리가 적용되지 않는다고 한 부분
34|⑤|금융기관과 채무자 사이에 변제자력 악화 등 일정 사유 발생 시 대출금채권의 기한의 이익을 상실시키는 특약이 유효하게 존재하면, 예금채권 압류 후 그 특약에 따라 대출금채권과 예금채권이 상계적상에 이르러 금융기관이 상계권을 행사할 수 있다.|
35|①|사용사업주가 파견근로자보호법에 따라 파견근로자에게 임금지급의무를 부담하여 파견근로자가 사용사업주에 대한 임금채권을 가지는 경우, 그 임금채권에도 근로기준법상 최우선변제권이 인정된다.|
35|②|임금, 재해보상금과 그 밖에 근로관계로 인한 채권은 사용자의 총재산에 대하여 질권·저당권이나 동산·채권 등의 담보권으로 담보된 채권 외에는 조세·공과금 및 다른 채권보다 우선하여 변제되어야 한다.|
35|③|최종 3개월분 임금은 근로관계 종료 근로자의 경우 종료일부터, 배당요구 당시 근로관계가 계속 중인 근로자의 경우 배당요구 시점부터 각각 소급하여 3개월 사이 지급사유가 발생한 미지급 임금을 말하고, 최종 3년간 퇴직금도 그 지급사유가 배당요구종기 전에 발생하여야 한다.|
35|④|근로기준법상 최우선변제권은 최종 3개월분 임금 등 원본채권에 인정되고, 그 임금 등에 대한 지연손해금채권에는 인정되지 않는다.|임금 등에 대한 지연손해금채권에도 최우선변제권이 인정된다고 한 부분
35|⑤|근로복지공단이 임금채권보장법에 따라 최우선변제권 있는 임금·퇴직금 일부를 대지급금으로 지급하고 근로자의 임금 등 채권을 대위행사하는 경우, 공단이 대위하는 채권은 대지급금을 받지 않은 다른 근로자의 최우선변제권 있는 임금 등 채권과 같은 순위로 배당받는다.|
""".strip()


def validate_part(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if len(source["questions"]) != len(base.QUESTION_RANGE):
        raise ValueError("unexpected question count")
    if len(queue["items"]) != base.EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {base.EXPECTED_ATOM_COUNT} queue items, got {len(queue['items'])}")
    if len(completed["items"]) != base.EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {base.EXPECTED_ATOM_COUNT} atoms, got {len(completed['items'])}")
    verdict_counts = base.Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != base.Counter({"O": 20, "X": 5}):
        raise ValueError(f"unexpected source verdict counts: {verdict_counts}")
    validate_atom_text(completed["items"])


def validate_atom_text(items: list[dict[str, object]]) -> None:
    banned_tokens = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "옳지 않은"]
    for item in items:
        rep = item["rep"]
        if any(token in rep for token in banned_tokens):
            raise ValueError(f"non-atom wording in rep: {item['atomId']} {rep}")
        if base.re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in rep: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or item["xDependsOn"] != rep:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        elif item["sourceTrap"] is not None or item["xDependsOn"] is not None:
            raise ValueError(f"unexpected X metadata: {item['atomId']}")


def read_json(path: base.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def unique_sources(source_lists: list[list[dict[str, str]]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for sources in source_lists:
        for source in sources:
            key = (source.get("title", ""), source.get("url", ""))
            if key not in seen:
                seen.add(key)
                out.append(source)
    return out


def strip_part(obj: dict[str, object]) -> dict[str, object]:
    copied = deepcopy(obj)
    copied.pop("part", None)
    return copied


def build_full_outputs(
    current_source: dict[str, object],
    current_queue: dict[str, object],
    current_completed: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    part_sources = []
    part_queues = []
    part_completed = []
    for part, source_path, queue_path, completed_path in PART_SPECS:
        if part == base.PART:
            part_sources.append(current_source)
            part_queues.append(current_queue)
            part_completed.append(current_completed)
        else:
            part_sources.append(read_json(source_path))
            part_queues.append(read_json(queue_path))
            part_completed.append(read_json(completed_path))

    checked_at = base.today()
    questions = [strip_part(question) for src in part_sources for question in src["questions"]]
    queue_items = [strip_part(item) for queue in part_queues for item in queue["items"]]
    atom_items = [strip_part(item) for completed in part_completed for item in completed["items"]]
    verification_sources = unique_sources([src["verificationSources"] for src in part_sources])

    full_source = {
        "schema": "legal-scrivener/source-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": base.EXAM_ID,
        "year": base.YEAR,
        "round": base.ROUND,
        "subject": base.SUBJECT_NAME,
        "updatedAt": checked_at,
        "questionCount": len(questions),
        "verificationSources": verification_sources,
        "questions": questions,
    }
    full_queue = {
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": "법무사시험",
        "examId": base.EXAM_ID,
        "year": base.YEAR,
        "round": base.ROUND,
        "subject": base.SUBJECT_NAME,
        "updatedAt": checked_at,
        "source": str(FULL_SOURCE_PATH),
        "itemCount": len(queue_items),
        "items": queue_items,
    }
    full_completed = {
        "schema": "legal-scrivener/completed-atoms-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": base.EXAM_ID,
        "year": base.YEAR,
        "round": base.ROUND,
        "subject": base.SUBJECT_NAME,
        "updatedAt": checked_at,
        "atomPrinciple": "docs/atom_원칙_v001.md",
        "sourceQueue": str(FULL_QUEUE_PATH),
        "sourceCount": len(queue_items),
        "atomCount": len(atom_items),
        "verificationSources": verification_sources,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "xHandling": "출제 원문상 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형 문제는 선택지 조합이 아니라 ㄱ·ㄴ·ㄷ 등 개별 근거명제로 atom화한다.",
        },
        "items": atom_items,
    }
    validate_full(full_source, full_queue, full_completed)
    return full_source, full_queue, full_completed


def validate_full(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if source["questionCount"] != 35:
        raise ValueError("full question count mismatch")
    if queue["itemCount"] != 175 or completed["atomCount"] != 175:
        raise ValueError("full atom count mismatch")
    counts = base.Counter(item["no"] for item in completed["items"])
    expected = base.Counter({no: 5 for no in range(1, 36)})
    if counts != expected:
        raise ValueError(f"full question atom counts mismatch: {counts}")
    verdict_counts = base.Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != base.Counter({"O": 140, "X": 35}):
        raise ValueError(f"full verdict counts mismatch: {verdict_counts}")
    validate_atom_text(completed["items"])


def update_index(full_source: dict[str, object], full_queue: dict[str, object], full_completed: dict[str, object]) -> None:
    index = read_json(INDEX_PATH) if INDEX_PATH.exists() else {
        "schema": "legal-scrivener/subject-index/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": base.today(),
        "examId": base.EXAM_ID,
        "year": base.YEAR,
        "round": base.ROUND,
        "subjects": {},
    }
    index["updatedAt"] = base.today()
    index.setdefault("subjects", {})[base.SUBJECT_NAME] = {
        "source": str(FULL_SOURCE_PATH),
        "atomQueue": str(FULL_QUEUE_PATH),
        "completedAtoms": str(FULL_OUT_PATH),
        "questionCount": full_source["questionCount"],
        "atomQueueItemCount": full_queue["itemCount"],
        "completedAtomCount": full_completed["atomCount"],
        "completedAtomsUpdatedAt": full_completed["updatedAt"],
    }
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    blocks = base.extract_question_blocks()
    raws = base.raw_statement_map(blocks)
    source = base.build_source(raws)
    queue = base.build_queue(source)
    completed = base.build_completed(queue)
    validate_part(source, queue, completed)

    base.write_json(base.SOURCE_PATH, source)
    base.write_json(base.QUEUE_PATH, queue)
    base.write_json(base.OUT_PATH, completed)

    full_source, full_queue, full_completed = build_full_outputs(source, queue, completed)
    base.write_json(FULL_SOURCE_PATH, full_source)
    base.write_json(FULL_QUEUE_PATH, full_queue)
    base.write_json(FULL_OUT_PATH, full_completed)
    update_index(full_source, full_queue, full_completed)

    print(
        json.dumps(
            {
                "subject": base.SUBJECT_NAME,
                "part": base.PART,
                "source": str(base.SOURCE_PATH),
                "queue": str(base.QUEUE_PATH),
                "completed": str(base.OUT_PATH),
                "questions": source["questionCount"],
                "atoms": completed["atomCount"],
                "verdictCounts": dict(base.Counter(item["sourceVerdict"] for item in completed["items"])),
                "fullCompleted": str(FULL_OUT_PATH),
                "fullAtoms": full_completed["atomCount"],
                "fullVerdictCounts": dict(base.Counter(item["sourceVerdict"] for item in full_completed["items"])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
