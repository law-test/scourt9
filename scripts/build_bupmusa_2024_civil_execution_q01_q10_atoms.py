# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2024" / "과목별"
RAW_TEXT_PATH = PRIVATE_ROOT / "text" / "2024" / "2024_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_민사집행법_q01_q10_atoms.json"

SUBJECT_NAME = "민사집행법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 3
PART = "q01-q10"
QUESTION_RANGE = range(1, 11)
EXPECTED_ATOM_COUNT = 50

LEGAL_SOURCES = [
    {"title": "민사집행법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민사집행법"},
    {"title": "민사집행규칙", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민사집행규칙"},
    {"title": "민법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민법"},
    {"title": "2024 법무사 민사집행법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881313"},
    {"title": "민사집행 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
]

OFFICIAL_ANSWERS = {
    1: "④",
    2: "③",
    3: "④",
    4: "②",
    5: "④",
    6: "⑤",
    7: "③",
    8: "④",
    9: "①",
    10: "④",
}

QUESTION_TYPES = {no: "single-best-false" for no in QUESTION_RANGE}
UNIT_LABELS = {no: ["①", "②", "③", "④", "⑤"] for no in QUESTION_RANGE}
FALSE_LABELS = {no: {answer} for no, answer in OFFICIAL_ANSWERS.items()}

TOPICS = {
    1: "부동산경매절차의 배당요구",
    2: "부동산경매절차의 매수인",
    3: "부동산경매절차의 통지",
    4: "보전집행의 취소",
    5: "피압류채권의 특정",
    6: "배당받을 채권자",
    7: "물상대위권 행사",
    8: "경매개시결정",
    9: "압류명령의 효력",
    10: "배당요구의 종기결정 및 공고",
}

REP_ROWS = """
1|①|임금 및 퇴직금 우선변제권자가 배당요구종기까지 소명자료를 제출하지 못했더라도 배당표 확정 전까지 자격을 보완하면 우선배당을 받을 수 있다.|
1|②|적법한 배당요구가 필요한 선순위채권자가 배당요구를 하지 않아 배당에서 제외되면, 대신 배당받은 후순위채권자에게 부당이득반환을 청구할 수 없다.|
1|③|경매개시결정등기 후 체납처분압류등기가 된 조세채권은 배당요구종기까지 교부청구를 하여야 경매절차에서 배당받을 수 있다.|
1|④|저당부동산의 소유권을 취득한 제3취득자가 민법 제367조에 따라 비용 우선상환을 받으려면 경매절차의 배당요구종기까지 배당요구를 하여야 한다.|제3취득자가 배당요구 없이도 비용 우선상환을 받을 수 있다고 한 부분
1|⑤|대항력과 우선변제권을 모두 가진 주택임차인이 경매절차에서 보증금 전액을 배당받지 못하면 대항요건 유지로 임대차 존속을 주장할 수 있고, 양수인은 임대인 지위를 승계한다.|
2|①|매각허가에 정당한 이유가 없거나 다른 조건으로 허가하여야 한다고 주장하는 매수인 또는 매각허가를 주장하는 매수신고인은 매각허가결정에 즉시항고할 수 있다.|
2|②|천재지변 등 매수인에게 책임 없는 사유로 부동산이 현저히 훼손된 사실이 매각허가결정 확정 뒤 밝혀지면, 매수인은 대금 납부 전까지 매각허가결정 취소를 신청할 수 있다.|
2|③|매수인이 매각대금을 낸 뒤 강제집행 일시정지를 명한 재판정본이 제출되어 배당절차가 진행되는 경우, 해당 채권자에게 배당될 금액은 공탁의 대상이 된다.|일시정지 재판정본 제출 뒤 해당 채권자를 배당에서 제외한다고 한 부분
2|④|매수신고 후 매각대금 납부 전 강제집행을 하지 않거나 신청·위임을 취하한다는 화해조서 또는 공정증서가 제출되면, 최고가매수신고인 또는 매수인과 차순위매수신고인의 동의가 있어야 효력이 생긴다.|
2|⑤|매수인이 재매각기일 3일 전까지 대금, 지연이자, 절차비용을 지급하면 재매각절차는 취소되고, 차순위매수신고인이 매각허가결정을 받았더라도 먼저 지급한 매수인이 목적물의 권리를 취득한다.|
3|①|집행법원이 이해관계인에게 매각기일 등을 통지하지 않아 매각허가결정 항고기간을 지키지 못한 경우, 특별한 사정이 없으면 추후보완이 허용된다.|
3|②|공유지분 매각에서 다른 공유자는 매각기일 등의 통지를 받아야 하므로, 통지를 받지 못한 공유자는 이해관계인으로서 절차상 흠을 이유로 항고할 수 있다.|
3|③|이해관계인이 기일통지를 받지 못했더라도 매각기일을 알고 출석해 입찰에 참가하여 권리보호 조치를 할 수 있었다면, 특별한 사정이 없는 한 통지누락은 매각허가결정 이의사유가 되지 않는다.|
3|④|매각기일 공고와 기존 이해관계인 통지가 완료된 뒤 권리신고가 있으면, 그 신고가 매각기일 전에 이루어졌더라도 새 이해관계인에게 매각기일 및 매각결정기일을 통지하지 않은 것이 위법하다고 볼 수 없다.|통지절차 완료 후 권리신고한 이해관계인에게도 다시 기일을 통지하여야 한다고 한 부분
3|⑤|권리신고를 하지 않은 대항력 있는 주택임차인에게 경매절차 진행사실을 통지하지 않았더라도 그 사정만으로 경매절차가 위법하게 되는 것은 아니다.|
4|①|채권가압류 신청취하로 가압류결정의 효력은 소멸하지만, 이미 제3채무자에게 가압류결정정본이 송달되어 집행된 경우에는 취하통지서가 제3채무자에게 송달되어야 가압류집행의 효력이 장래를 향하여 소멸한다.|
4|②|채권가압류 신청취하 사실을 제3채무자가 다른 방법으로 알았더라도, 이미 집행된 채권가압류의 효력을 소멸시키려면 제3채무자에게 취하통지서가 송달되어야 한다.|제3채무자가 다른 방법으로 취하 사실을 알면 취하통지서 송달이 필요 없다고 한 부분
4|③|가압류가 본압류로 이행되어 강제집행이 이루어진 경우 본집행이 계속되는 한 채무자는 가압류 이의·취소신청이나 가압류집행 자체의 취소를 구할 실익이 없다.|
4|④|가처분취소결정의 집행으로 처분금지가처분등기가 말소되면 그 효력은 확정적이므로, 그 후 소유권이전등기를 마친 사람은 특별한 사정이 없는 한 제한 없이 소유권 취득의 효력으로 가처분채권자에게 대항할 수 있다.|
4|⑤|금전채권 보전을 위한 채권가압류가 채권자의 신청으로 취소되면, 특별한 사정이 없는 한 가압류에 따른 소멸시효 중단효과는 소급적으로 소멸한다.|
5|①|피압류채권의 내용이 특정되지 않은 압류명령은 무효이고, 채권자가 나중에 보완하더라도 압류명령이 소급하여 유효하게 되지는 않는다.|
5|②|예금채권 압류에서 일정 순서에 따라 청구금액에 이를 때까지의 금액이라는 문언만으로는 송달 후 새로 입금되는 예금채권까지 압류 대상에 포함된다고 해석할 수 없으며, 이는 압류 및 추심명령에서도 같다.|
5|③|채무자나 제3채무자가 여러 명이거나 채무자가 제3채무자에게 여러 채권을 가진 경우 전부명령은 각 대상별 전부금액을 특정하여야 하고, 특정하지 않으면 무효이다.|
5|④|채무자나 제3채무자가 여러 명인 경우 압류 대상 채권합계액이나 각자별 집행 범위가 명확하지 않으면, 채권합계액이 집행채권액을 초과하지 않더라도 원칙적으로 압류명령은 특정성이 없어 무효이다.|집행 범위가 불명확해도 채권합계액이 집행채권액 이하이면 압류명령이 유효하다고 한 부분
5|⑤|채무자가 제3채무자에게 여러 채권을 가지더라도 대상 채권의 합계액이 집행채권액보다 적거나 모두 하나의 계약에서 발생하는 등 특별한 사정이 있으면, 채권별 압류 부분을 따로 특정하지 않아도 압류 등 결정은 유효할 수 있다.|
6|①|집행력 있는 정본을 가진 채권자, 경매개시결정등기 후 가압류한 채권자, 법률상 우선변제청구권자는 배당요구종기까지 배당요구를 하여야 배당받을 수 있다.|
6|②|첫 경매개시결정등기 전에 등기한 전세권자는 배당요구를 하면 매각으로 전세권이 소멸하므로 배당받을 수 있다.|
6|③|첫 경매개시결정등기 전 전세권보다 앞선 저당권이나 가압류가 매각으로 소멸하면 전세권도 함께 소멸하므로, 그 전세권자는 배당받을 수 있다.|
6|④|압류·참가압류·교부청구를 한 국세·지방세 등 공과금채권자는 그 압류 또는 참가압류 등기가 첫 경매개시결정등기 전에 이루어진 경우 별도 교부청구 없이 배당받는다.|
6|⑤|과세관청이 파산선고 전 체납처분으로 부동산을 압류한 경우, 파산선고 후 별제권 행사에 따른 부동산경매절차에서 체납처분에 배당할 금원은 파산관재인이 아니라 과세관청이 배당받는다.|체납처분에 배당할 금원을 파산관재인이 배당받는다고 한 부분
7|①|근저당권자가 공탁금에 물상대위권 행사를 위한 압류를 하지 않고 일반채권에 기한 가압류만 한 상태에서 다른 채권자의 압류로 공탁관이 사유신고를 하면, 근저당권자는 그 뒤 물상대위권 행사를 위한 압류나 배당요구를 할 수 없다.|
7|②|저당권에 기한 물상대위권자라도 집행권원에 의한 강제집행 방법을 선택하여 압류 및 전부명령을 받은 경우, 압류가 경합된 상태에서 발부된 전부명령은 무효이다.|
7|③|수용보상금채권이 물상대위권 행사 전 양도 또는 전부명령으로 이전되었더라도, 보상금 직접 지급 전 또는 강제집행절차의 배당요구종기 전이면 담보물권자는 물상대위권으로 우선변제를 받을 수 있다.|보상금채권이 먼저 양도 또는 전부되면 담보물권자가 더 이상 물상대위권을 행사할 수 없다고 한 부분
7|④|수용보상금에 일반채권자의 가압류나 압류가 먼저 있더라도 담보물권자는 물상대위권으로 우선변제를 받을 수 있으나, 사업시행자의 집행공탁 및 사유신고 또는 추심채권자의 추심신고가 있은 뒤에는 물상대위권을 행사할 수 없다.|
7|⑤|수용되는 토지에 가압류가 집행되어 있어도 토지수용으로 가압류의 효력은 소멸하고, 특별한 규정이 없는 한 그 가압류의 효력이 수용보상금채권에 당연히 이전되거나 처분금지효로 미치지 않는다.|
8|①|경매개시결정은 채무자에게 고지되어야 효력이 생기므로, 경매개시결정 고지 없이는 경매절차를 유효하게 속행할 수 없다.|
8|②|부동산 경매개시결정등기 후 점유를 이전받거나 피담보채권이 발생하여 유치권을 취득한 사람은 경매절차의 매수인에게 유치권을 행사할 수 없다.|
8|③|이중경매개시결정 후 선행경매신청이 취하되거나 선행절차가 취소·정지되면, 그때까지 진행된 선행경매절차의 결과는 유효한 범위에서 후행경매절차에 승계되어 이용된다.|
8|④|체납처분압류가 먼저 되어 있더라도 경매개시결정 전에 민사유치권을 취득한 유치권자는 원칙적으로 경매절차의 매수인에게 유치권을 행사할 수 있다.|체납처분압류 후 경매개시결정 전 취득한 민사유치권을 매수인에게 행사할 수 없다고 한 부분
8|⑤|경매로 인한 압류 효력이 발생하기 전에 유치권을 취득하였다면, 유치권 취득이 근저당권 설정 후이고 그 근저당권에 기해 경매절차가 개시되었더라도 유치권으로 매수인에게 대항할 수 있다.|
9|①|차임채권 압류 후 임대차가 종료되어 차임채권이 불법행위 손해배상채권으로 바뀐 경우, 특별한 사정이 없는 한 기존 압류의 효력은 그 손해배상채권에 미치지 않는다.|차임채권 압류의 효력이 임대차 종료 후 손해배상채권에도 그대로 유지된다고 한 부분
9|②|채권압류 후 그 채권의 발생원인인 계약상 지위를 이전하는 계약인수가 이루어지면, 양수인은 압류로 제한된 상태의 채권을 이전받으므로 제3채무자는 계약관계 소멸을 내세워 압류채권자에게 대항할 수 없다.|
9|③|채권압류는 집행채권의 소멸시효를 중단시키고 그 효력은 압류명령 신청시에 발생하며, 피압류채권이 이미 부존재하는 경우에도 특별한 사정이 없는 한 집행채권의 소멸시효는 중단된다.|
9|④|채권자가 추심권을 포기하더라도 압류의 효력은 유지되므로 압류로 인한 소멸시효 중단효과는 상실되지 않고, 압류명령 신청을 취하하면 그 중단효과가 소급하여 상실된다.|
9|⑤|채권압류만으로 피압류채권 자체의 소멸시효가 중단되지는 않지만, 압류 및 추심명령이 제3채무자에게 송달되면 피압류채권에 대하여 최고로서의 시효중단 효력이 인정될 수 있다.|
10|①|배당요구종기가 정해지면 법원은 경매개시결정 전에 등기된 최선순위 전세권자에게 배당요구종기를 고지하여야 한다.|
10|②|배당요구종기 결정과 공고는 경매개시결정에 따른 압류의 효력이 생긴 때부터 1주 이내에 하여야 한다.|
10|③|소유권이전에 관한 가등기가 있는 부동산에 경매개시결정이 있으면, 법원은 가등기권리자에게 담보가등기 여부와 그 내용 또는 권리 내용을 신고하도록 상당한 기간을 정하여 최고하여야 한다.|
10|④|이미 배당요구 또는 채권신고를 한 사람에게는 배당요구종기가 연기되더라도 다시 고지하거나 최고하지 않아도 된다.|이미 배당요구 또는 채권신고를 한 사람에게도 종기 연기 시 다시 고지·최고하여야 한다고 한 부분
10|⑤|법원사무관등은 첫 경매개시결정등기 전 등기된 가압류채권자, 매각으로 소멸하는 저당권·전세권 등 우선변제청구권자, 조세 등 공과금 주관 공공기관에 채권의 유무와 원인 및 액수를 배당요구종기까지 신고하도록 최고하여야 한다.|
""".strip()

LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.find("【민사집행법 35문】")
    if start == -1:
        raise ValueError("cannot locate 2024 civil-execution section")
    end = text.find("【상업등기법 및 비송사건절차법 15문】", start)
    section = text[start : end if end != -1 else len(text)]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 1 <= int(m.group(1)) <= 35]
    if len(matches) != 35:
        raise ValueError(f"expected 35 civil-execution questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        if no in QUESTION_RANGE:
            blocks[no] = section[match.start() : end_pos]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in re.finditer(r"[①②③④⑤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(LABEL_CODE):
            break
    if set(first_by_label) != set(LABEL_CODE):
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in ["①", "②", "③", "④", "⑤"]]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = re.split(r"\s*제3과목\s*①책형\s*전체|\s*【\s*제3과목", block[start:end])[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in QUESTION_RANGE:
        split = split_choice_units(blocks[no])
        for label in UNIT_LABELS[no]:
            raw[(no, label)] = split[label]
    return raw


def source_verdict(no: int, label: str) -> str:
    return "X" if label in FALSE_LABELS[no] else "O"


def load_rep_rows() -> dict[tuple[int, str], dict[str, str | None]]:
    rows: dict[tuple[int, str], dict[str, str | None]] = {}
    for line in REP_ROWS.splitlines():
        no_text, label, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        rows[(int(no_text), label)] = {"rep": rep.strip(), "trap": trap}
    return rows


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def basis(no: int) -> tuple[str, str, str]:
    topic = TOPICS[no]
    return (
        "민사집행법+민법+판례",
        f"{topic} 관련 민사집행법·민사집행규칙·민법 조문 및 대법원 판례",
        f"{topic}의 출제 지점을 독립 명제로 정리한다.",
    )


def complete_sentence(rep: str) -> str:
    rep = rep.strip()
    return rep if rep.endswith(".") else rep.rstrip(".") + "."


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in QUESTION_RANGE:
        qid = f"2024-g3-civil-execution-{no:02d}"
        units = []
        for idx, label in enumerate(UNIT_LABELS[no], start=1):
            units.append(
                {
                    "unitId": f"{qid}-{LABEL_CODE[label]}",
                    "unitType": "choice",
                    "label": label,
                    "rawStatement": raws[(no, label)],
                    "originalVerdict": source_verdict(no, label),
                }
            )
        questions.append(
            {
                "qid": qid,
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 1차",
                "group": GROUP,
                "groupLabel": "제3과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": QUESTION_TYPES[no],
                "officialAnswer": OFFICIAL_ANSWERS[no],
                "units": units,
            }
        )
    return {
        "schema": "legal-scrivener/problem-original-current-by-subject-part/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "part": PART,
        "updatedAt": today(),
        "questionCount": len(questions),
        "verificationSources": LEGAL_SOURCES,
        "questions": questions,
    }


def build_queue(source: dict[str, object]) -> dict[str, object]:
    items = []
    for question in source["questions"]:
        q = question
        for unit in q["units"]:
            items.append(
                {
                    "unitId": unit["unitId"],
                    "sourceFamily": "법무사시험",
                    "source": q["sourceLabel"],
                    "examId": EXAM_ID,
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "part": PART,
                    "no": q["no"],
                    "unitType": unit["unitType"],
                    "unitLabel": unit["label"],
                    "sourceQuestionType": q["type"],
                    "officialQuestionAnswer": q["officialAnswer"],
                    "rawStatement": unit["rawStatement"],
                    "originalVerdict": unit["originalVerdict"],
                }
            )
    return {
        "schema": "legal-scrivener/atom-queue-part/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "part": PART,
        "updatedAt": today(),
        "source": str(SOURCE_PATH),
        "itemCount": len(items),
        "items": items,
    }


def build_completed(queue: dict[str, object]) -> dict[str, object]:
    reps = load_rep_rows()
    items = []
    for item in queue["items"]:
        key = (item["no"], item["unitLabel"])
        if key not in reps:
            raise ValueError(f"missing rep row: {key}")
        rep = complete_sentence(str(reps[key]["rep"]))
        trap = reps[key]["trap"]
        basis_type, basis_ref, why = basis(item["no"])
        source_is_x = item["originalVerdict"] == "X"
        atom = {
            "atomId": f"bupmusa-2024-civil-execution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}",
            "sourceUnitId": item["unitId"],
            "sourceFamily": "법무사시험",
            "source": item["source"],
            "year": YEAR,
            "round": ROUND,
            "subject": SUBJECT_NAME,
            "part": PART,
            "no": item["no"],
            "unitType": item["unitType"],
            "unitLabel": item["unitLabel"],
            "sourceQuestionType": item["sourceQuestionType"],
            "officialQuestionAnswer": item["officialQuestionAnswer"],
            "sourceVerdict": item["originalVerdict"],
            "currentVerdict": "O",
            "rep": rep,
            "a": "O",
            "basisType": basis_type,
            "basisRef": basis_ref,
            "why": why,
            "sourceStatement": item["rawStatement"],
            "sourceTrap": trap,
            "xDependsOn": rep if source_is_x else None,
            "reviewedAt": today(),
            "currentLawCheckedAt": today(),
        }
        if source_is_x and not trap:
            raise ValueError(f"X item without sourceTrap: {key}")
        items.append(atom)
    return {
        "schema": "legal-scrivener/completed-atoms-by-subject-part/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "part": PART,
        "updatedAt": today(),
        "atomPrinciple": "docs/atom_원칙_v001.md",
        "sourceQueue": str(QUEUE_PATH),
        "sourceCount": len(queue["items"]),
        "atomCount": len(items),
        "verificationSources": LEGAL_SOURCES,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "xHandling": "출제 원문상 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형 문제는 선택지 조합이 아니라 ㄱ·ㄴ·ㄷ 등 개별 근거명제로 atom화한다.",
        },
        "items": items,
    }


def validate(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if len(source["questions"]) != len(QUESTION_RANGE):
        raise ValueError("unexpected question count")
    if len(queue["items"]) != EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {EXPECTED_ATOM_COUNT} queue items, got {len(queue['items'])}")
    if len(completed["items"]) != EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {EXPECTED_ATOM_COUNT} atoms, got {len(completed['items'])}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 40, "X": 10}):
        raise ValueError(f"unexpected source verdict counts: {verdict_counts}")
    ids = [item["atomId"] for item in completed["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    forbidden_in_rep = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳"]
    for item in completed["items"]:
        rep = item["rep"]
        if any(token in rep for token in forbidden_in_rep):
            raise ValueError(f"non-atom wording in rep: {item['atomId']} {rep}")
        if not rep.endswith("."):
            raise ValueError(f"rep must be a declarative sentence: {item['atomId']}")
        if item["sourceVerdict"] == "X" and item["xDependsOn"] != rep:
            raise ValueError(f"X item must depend on corrected rep: {item['atomId']}")
        if item["sourceVerdict"] == "O" and item["xDependsOn"] is not None:
            raise ValueError(f"O item must not have xDependsOn: {item['atomId']}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    blocks = extract_question_blocks()
    raws = raw_statement_map(blocks)
    source = build_source(raws)
    queue = build_queue(source)
    completed = build_completed(queue)
    validate(source, queue, completed)
    write_json(SOURCE_PATH, source)
    write_json(QUEUE_PATH, queue)
    write_json(OUT_PATH, completed)
    counts = Counter(item["sourceVerdict"] for item in completed["items"])
    print(f"wrote {OUT_PATH}")
    print(f"questions={len(source['questions'])} atoms={len(completed['items'])} O={counts['O']} X={counts['X']}")


if __name__ == "__main__":
    main()
