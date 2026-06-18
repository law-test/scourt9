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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민법_q01_q10_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민법_q01_q10_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_민법_q01_q10_atoms.json"

SUBJECT_NAME = "민법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_RANGE = range(1, 11)
EXPECTED_ATOM_COUNT = 50

LEGAL_SOURCES = [
    {"title": "민법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민법"},
    {"title": "2024 법무사 민법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881318"},
    {"title": "민법 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
]

OFFICIAL_ANSWERS = {
    1: "③",
    2: "⑤",
    3: "④",
    4: "①",
    5: "③",
    6: "①",
    7: "④",
    8: "③",
    9: "⑤",
    10: "②",
}

QUESTION_TYPES = {
    1: "single-best-false",
    2: "single-best-false",
    3: "single-best-false",
    4: "single-best-false",
    5: "single-best-false",
    6: "single-best-false",
    7: "multi-select-false",
    8: "single-best-false",
    9: "single-best-true",
    10: "single-best-true",
}

UNIT_LABELS = {
    1: ["①", "②", "③", "④", "⑤"],
    2: ["①", "②", "③", "④", "⑤"],
    3: ["①", "②", "③", "④", "⑤"],
    4: ["①", "②", "③", "④", "⑤"],
    5: ["①", "②", "③", "④", "⑤"],
    6: ["①", "②", "③", "④", "⑤"],
    7: ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"],
    8: ["①", "②", "③", "④", "⑤"],
    9: ["①", "②", "③", "④", "⑤"],
    10: ["①", "②", "③", "④", "⑤"],
}

FALSE_LABELS = {
    1: {"③"},
    2: {"⑤"},
    3: {"④"},
    4: {"①"},
    5: {"③"},
    6: {"①"},
    7: {"ㄴ", "ㄹ"},
    8: {"③"},
    9: {"①", "②", "③", "④"},
    10: {"①", "③", "④", "⑤"},
}

TOPICS = {
    1: "임차인의 매수청구권",
    2: "도급",
    3: "상계",
    4: "채권의 목적",
    5: "민법상 조합",
    6: "증여",
    7: "소멸시효",
    8: "지역권과 주위토지통행권",
    9: "채권자취소권",
    10: "조건·기한·기간",
}

REP_ROWS = """
1|①|건물매수청구권의 대상이 되는 건물은 특별한 사정이 없는 한 무허가 건물이라도 임차인의 건물매수청구권 대상이 될 수 있다|
1|②|건물매수청구권 행사로 토지소유자가 지급할 건물 시가를 산정할 때 임차인이 그 건물에서 영업하며 얻던 수익까지 고려할 필요는 없다|
1|③|토지임차인의 채무불이행으로 토지임대차계약이 해지된 경우 토지임차인은 지상건물매수청구권을 행사할 수 없다|채무불이행으로 해지된 토지임차인에게 건물매수청구권을 인정한 부분
1|④|일시사용을 위한 임대차임이 명백한 경우에는 부속물매수청구권 규정이 적용되지 않는다|
1|⑤|건물 자체의 수선·증개축 부분이 건물의 구성부분을 이루고 독립된 물건으로 볼 수 없으면 임차인의 부속물매수청구권 대상이 될 수 없다|
2|①|완성된 목적물 또는 완성 전 성취된 부분에 하자가 있으면 도급인은 원칙적으로 상당한 기간을 정해 수급인에게 하자보수를 청구할 수 있다|
2|②|신축건물 수급인의 공사대금채권 양수인이 민법 제666조에 따른 저당권설정을 청구하여 도급인이 저당권을 설정하는 행위는 특별한 사정이 없는 한 사해행위가 아니다|
2|③|제작물공급계약은 대체물 제작·공급이면 매매 규정이, 부대체물 제작·공급이면 도급 규정이 주로 적용된다|
2|④|수급인의 하자담보책임은 무과실책임이지만, 하자 발생·확대에 기여한 도급인의 잘못은 손해배상 범위 산정에서 참작될 수 있다|
2|⑤|민법 제666조의 수급인의 목적부동산에 대한 저당권설정청구권은 공사에 관한 채권으로서 3년의 단기소멸시효가 적용된다|수급인의 저당권설정청구권 소멸시효를 10년으로 본 부분
3|①|상속채권자가 상속개시 후 한정승인 전에 상계하였더라도 이후 상속인이 한정승인을 하면 그 상계는 민법 제1031조의 취지에 따라 소급하여 효력을 잃을 수 있다|
3|②|불법행위 손해배상채무자가 채권양도인에 대한 별도 채권자 지위에서 채권양수인을 상대로 채권자취소권을 행사하여 가액배상을 구하는 것은 민법 제496조에 반하지 않는다|
3|③|수탁보증인의 주채무자에 대한 사전구상권에는 담보제공청구권이 항변권으로 부착되어 있으므로 이를 자동채권으로 하는 상계는 원칙적으로 허용되지 않는다|
3|④|채권양수인이 양수채권을 자동채권으로 상계하는 경우 상계효력은 채권양수인이 채권양도로 대항할 수 있게 된 시점보다 앞선 변제기로 소급하지 않는다|채권양도 전에 이미 양 채권의 변제기가 도래했다는 이유로 상계효력이 그 변제기로 소급한다고 본 부분
3|⑤|민법 제492조 제1항의 채무 이행기 도래는 채권자가 이행을 청구할 수 있는 시기가 도래한 것을 뜻하고, 채무자가 이행지체에 빠진 시기를 뜻하지 않는다|
4|①|무상수치인은 임치물을 자기 재산과 동일한 주의로 보관하면 되고, 선량한 관리자의 주의까지 부담하지는 않는다|보수 없는 임치수치인에게도 선량한 관리자의 주의의무가 있다고 본 부분
4|②|원본채권의 소멸시효가 지분적 이자채권의 소멸시효보다 먼저 완성되면 지분적 이자채권은 그 자체의 소멸시효가 완성되지 않았더라도 소멸한다|
4|③|외화채권을 채권자가 우리나라 통화로 청구하는 경우 법원은 사실심 변론종결 당시의 외국환시세를 기준으로 환산하여 이행을 명한다|
4|④|확정된 금전채무의 지연손해금채무는 이행기의 정함이 없는 채무로서 채권자의 이행청구를 받은 때부터 지체책임이 발생한다|
4|⑤|금전으로 가액을 산정할 수 없는 것도 채권의 목적이 될 수 있다|
5|①|조합계약에서는 조합 해산청구, 탈퇴, 제명이 문제될 뿐 일반계약처럼 조합계약을 해제하여 상대방에게 원상회복의무를 부담시킬 수 없다|
5|②|업무집행조합원의 임무위배나 권한초과로 조합재산에 손해가 발생한 경우 조합원은 개인 지위에서 곧바로 자기 손해배상을 구할 수 없다|
5|③|민법 제706조의 조합원은 조합원의 출자가액이나 지분이 아니라 조합원의 인원수를 뜻한다|민법 제706조의 조합원을 출자가액이나 지분으로 본 부분
5|④|조합원이 다른 조합원 전원의 동의로 조합지분을 양도하면 조합원의 지위를 상실하고, 조합원 지위 변동은 조합지분 양도양수 약정으로 효력이 생긴다|
5|⑤|조합계약이 조합원 지분의 양도를 개괄적으로 인정하더라도, 지분 전부가 아니라 일부를 제3자에게 양도하는 것까지 당연히 허용되는 것은 아니다|
6|①|부담부증여에서 증여자는 부담의 한도에서 매도인과 같은 담보책임을 부담한다|부담부증여의 담보책임을 부담의 한도가 아니라 증여 전체 부분에 미친다고 본 부분
6|②|증여 의사가 서면으로 표시되지 않은 경우 각 당사자는 증여를 해제할 수 있지만, 이미 이행한 부분에는 영향을 미치지 않는다|
6|③|서면에 의하지 않은 증여라는 이유로 하는 해제에는 10년의 제척기간이 적용되지 않는다|
6|④|정기의 급여를 목적으로 한 증여는 증여자 또는 수증자의 사망으로 효력을 잃는다|
6|⑤|무상으로 일방적 급부를 하는 증여계약은 급부와 반대급부의 불균형을 전제로 하는 민법 제104조의 불공정한 법률행위에 해당하기 어렵다|
7|ㄱ|연예인의 임금채권은 1년간 행사하지 않으면 소멸시효가 완성된다|
7|ㄴ|영업양도 후 채권자가 영업양도인을 상대로 판결을 받아 소멸시효가 중단되거나 기간이 연장되더라도 그 효력은 상호를 속용하는 영업양수인에게 미치지 않는다|영업양도인에 대한 소멸시효 중단·연장 효과가 상호속용 영업양수인에게도 미친다고 본 부분
7|ㄷ|부동산경매절차에서 채무자에게 교부할 잉여금이 공탁되면 채무자의 공탁금지급청구권은 공탁일부터 소멸시효가 진행한다|
7|ㄹ|채무불이행에 따른 해제 의사표시 당시 본래 채권이 이미 시효완성으로 소멸하였다면 그 채무불이행을 이유로 한 해제권과 원상회복청구권은 행사할 수 없다|본래 채권의 시효완성 후에도 시효완성 전 채무불이행을 이유로 해제권과 원상회복청구권을 행사할 수 있다고 본 부분
7|ㅁ|채무자가 제3채무자를 상대로 제기한 금전채권 이행청구소송으로 생긴 시효중단 효력은 그 채권에 압류 및 추심명령을 받은 추심채권자에게도 미친다|
8|①|요역지가 분필되어 일부 소유권이 이전되더라도 요역지 소유자가 지역권설정등기를 아직 받지 못했다면 타인 소유 대지 부분까지 요역지로 하여 지역권설정등기 이행을 청구할 수 있다|
8|②|주위토지통행권은 통행로가 항상 특정 장소로 고정되는 것이 아니므로 기존 통행로 이용 상태가 바뀌면 손해가 더 적은 다른 장소로 통행해야 할 수 있다|
8|③|주위토지통행권의 범위는 장래 이용상황을 미리 대비하여 정하는 것이 아니라 현재 토지의 용법에 따른 이용 범위를 기준으로 정한다|주위토지통행권 범위를 장래 이용상황까지 미리 대비하여 정해야 한다고 본 부분
8|④|통행지역권은 요역지 소유자가 승역지 위에 도로를 설치하여 승역지를 사용하는 객관적 상태가 시효기간 계속된 경우에 한하여 시효취득이 인정될 수 있다|
8|⑤|통행지역권을 주장하려면 그 토지의 통행으로 편익을 얻는 요역지가 있음을 주장·증명하여야 한다|
9|①|사해행위 전에 성립한 채권이 양도된 경우 채권양도의 대항요건이 사해행위 후에 갖추어졌더라도 양수인은 채권자취소권을 행사할 수 있다|채권양도의 대항요건이 사해행위 후에 갖추어지면 채권양수인이 채권자취소권을 행사할 수 없다고 본 부분
9|②|채권자취소권의 피보전채권은 사해행위 전에 성립되어 있으면 충분하고, 사해행위 당시 액수나 범위가 구체적으로 확정되어 있을 필요는 없다|피보전채권이 사해행위 전에 이미 구체적 액수나 범위까지 확정되어야 한다고 본 부분
9|③|사해행위 목적 부동산에 우선변제권 있는 임차인이 있으면 수익자가 배상할 부동산 가액에서 우선변제권 있는 임차보증금반환채권액을 공제하여야 한다|우선변제권 있는 임차보증금반환채권액을 가액배상 산정에서 공제하지 않는다고 본 부분
9|④|저당권이 설정된 부동산에 관한 사해행위 후 저당권설정등기가 말소된 경우 가액배상액은 원칙적으로 사실심 변론종결 당시의 부동산 가액을 기준으로 산정한다|사해행위 후 저당권이 말소된 경우 가액산정 기준시를 저당권설정등기 말소 당시로 본 부분
9|⑤|사해행위 후 채무자가 자력을 회복하여 사실심 변론종결시 채권자를 해하지 않게 되면 채권자취소권은 책임재산 보전 필요성이 없어져 소멸하고, 그 사정변경은 취소소송 상대방이 증명하여야 한다|
10|①|기한은 채무자의 이익을 위한 것으로 추정된다|기한을 채권자의 이익을 위한 것으로 추정한 부분
10|②|법률행위 당시 이미 성취한 조건이 정지조건이면 조건 없는 법률행위로 하고, 해제조건이면 그 법률행위는 무효로 한다|
10|③|조건이 선량한 풍속 기타 사회질서에 위반하면 그 조건만이 아니라 그 법률행위 전체가 무효이다|사회질서 위반 조건에서 조건만 무효이고 법률행위는 유효하다고 본 부분
10|④|연령계산에서는 출생일을 산입한다|연령계산에서 출생일을 산입하지 않는다고 본 부분
10|⑤|제척기간에는 소멸시효 중단 규정이 준용되지 않는다|제척기간에 소멸시효 중단 규정이 준용된다고 본 부분
""".strip()

LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
    "ㄱ": "ga",
    "ㄴ": "na",
    "ㄷ": "da",
    "ㄹ": "ra",
    "ㅁ": "ma",
}


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.find("【민 법 40문】")
    if start == -1:
        raise ValueError("cannot locate 2024 civil-law section")
    end = text.find("【가족관계", start)
    section = text[start : end if end != -1 else len(text)]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 1 <= int(m.group(1)) <= 40]
    if len(matches) != 40:
        raise ValueError(f"expected 40 civil-law questions, got {len(matches)}")
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
        if set(first_by_label) == {"①", "②", "③", "④", "⑤"}:
            break
    if set(first_by_label) != {"①", "②", "③", "④", "⑤"}:
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in ["①", "②", "③", "④", "⑤"]]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = re.split(r"\s*제2과목\s*①책형|\s*【\s*제2과목", block[start:end])[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    choice_start = re.search(r"[①②③④⑤]", block)
    stem = block[: choice_start.start()] if choice_start else block
    markers = list(re.finditer(r"([ㄱㄴㄷㄹㅁ])\.", stem))
    if not markers:
        raise ValueError("cannot split box statements")
    out: dict[str, str] = {}
    for idx, marker in enumerate(markers):
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(stem)
        out[marker.group(1)] = normalize_raw(stem[marker.end() : end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in QUESTION_RANGE:
        split = split_box_units(blocks[no]) if no == 7 else split_choice_units(blocks[no])
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
    return ("민법+판례", f"{topic} 관련 민법 조문 및 대법원 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")


def complete_sentence(rep: str) -> str:
    rep = rep.strip()
    return rep if rep.endswith((".", "다", "음")) and rep.endswith(".") else rep.rstrip(".") + "."


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in QUESTION_RANGE:
        qid = f"2024-g1-civil-law-{no:02d}"
        units = []
        for idx, label in enumerate(UNIT_LABELS[no], start=1):
            units.append(
                {
                    "unitId": f"{qid}-{LABEL_CODE[label]}",
                    "unitType": "box" if no == 7 else "choice",
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
                "groupLabel": "제2과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": QUESTION_TYPES[no],
                "officialAnswer": OFFICIAL_ANSWERS[no],
                "units": units,
            }
        )
    return {
        "schema": "legal-scrivener/source-by-subject-part/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "part": "q01-q10",
        "updatedAt": today(),
        "questionCount": len(list(QUESTION_RANGE)),
        "verificationSources": LEGAL_SOURCES,
        "questions": questions,
    }


def build_queue(source: dict[str, object]) -> dict[str, object]:
    items = []
    for question in source["questions"]:
        for unit in question["units"]:
            items.append(
                {
                    "unitId": unit["unitId"],
                    "sourceFamily": "법무사시험",
                    "source": question["sourceLabel"],
                    "examId": EXAM_ID,
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "part": "q01-q10",
                    "no": question["no"],
                    "unitType": unit["unitType"],
                    "unitLabel": unit["label"],
                    "sourceQuestionType": question["type"],
                    "officialQuestionAnswer": question["officialAnswer"],
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
        "part": "q01-q10",
        "updatedAt": today(),
        "source": str(SOURCE_PATH),
        "itemCount": len(items),
        "items": items,
    }


def build_completed(queue: dict[str, object]) -> dict[str, object]:
    reps = load_rep_rows()
    items = []
    checked_at = today()
    for qitem in queue["items"]:
        no = qitem["no"]
        label = qitem["unitLabel"]
        spec = reps[(no, label)]
        verdict = qitem["originalVerdict"]
        if (verdict == "X") != (spec["trap"] is not None):
            raise ValueError(f"rep trap mismatch for q{no} {label}")
        basis_type, basis_ref, why = basis(no)
        rep = complete_sentence(spec["rep"])
        items.append(
            {
                "atomId": f"bupmusa-2024-civil-law-q{no:02d}-{LABEL_CODE[label]}",
                "sourceUnitId": qitem["unitId"],
                "sourceFamily": "법무사시험",
                "source": qitem["source"],
                "year": YEAR,
                "round": ROUND,
                "subject": SUBJECT_NAME,
                "part": "q01-q10",
                "no": no,
                "unitType": qitem["unitType"],
                "unitLabel": label,
                "sourceQuestionType": qitem["sourceQuestionType"],
                "officialQuestionAnswer": qitem["officialQuestionAnswer"],
                "sourceVerdict": verdict,
                "currentVerdict": "O",
                "rep": rep,
                "a": "O",
                "basisType": basis_type,
                "basisRef": basis_ref,
                "why": why,
                "sourceStatement": qitem["rawStatement"],
                "sourceTrap": spec["trap"],
                "xDependsOn": rep if verdict == "X" else None,
                "reviewedAt": checked_at,
                "currentLawCheckedAt": checked_at,
            }
        )
    return {
        "schema": "legal-scrivener/completed-atoms-by-subject-part/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "part": "q01-q10",
        "updatedAt": checked_at,
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
    if source["questionCount"] != 10:
        raise ValueError("question count mismatch")
    if queue["itemCount"] != EXPECTED_ATOM_COUNT or completed["atomCount"] != EXPECTED_ATOM_COUNT:
        raise ValueError("atom count mismatch")
    counts = Counter(item["no"] for item in completed["items"])
    if counts != Counter({no: 5 for no in QUESTION_RANGE}):
        raise ValueError(f"question atom counts mismatch: {counts}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 33, "X": 17}):
        raise ValueError(f"verdict counts mismatch: {verdict_counts}")
    banned_tokens = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳"]
    for item in completed["items"]:
        rep = item["rep"]
        if any(token in rep for token in banned_tokens):
            raise ValueError(f"non-atomic wording detected: {item['atomId']} {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace detected: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or item["xDependsOn"] != rep:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        else:
            if item["sourceTrap"] is not None or item["xDependsOn"] is not None:
                raise ValueError(f"unexpected X metadata: {item['atomId']}")


def main() -> None:
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = extract_question_blocks()
    raws = raw_statement_map(blocks)
    source = build_source(raws)
    queue = build_queue(source)
    completed = build_completed(queue)
    validate(source, queue, completed)

    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_PATH.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "subject": SUBJECT_NAME,
                "part": "q01-q10",
                "source": str(SOURCE_PATH),
                "queue": str(QUEUE_PATH),
                "completed": str(OUT_PATH),
                "questions": source["questionCount"],
                "atoms": completed["atomCount"],
                "verdictCounts": dict(Counter(item["sourceVerdict"] for item in completed["items"])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
