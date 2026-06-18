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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민법_q11_q20_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민법_q11_q20_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_민법_q11_q20_atoms.json"

SUBJECT_NAME = "민법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_RANGE = range(11, 21)
EXPECTED_ATOM_COUNT = 49

LEGAL_SOURCES = [
    {"title": "민법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민법"},
    {"title": "2024 법무사 민법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881318"},
    {"title": "민법 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
]

OFFICIAL_ANSWERS = {
    11: "②",
    12: "③",
    13: "①",
    14: "①",
    15: "②",
    16: "③",
    17: "③",
    18: "④",
    19: "②",
    20: "①",
}

QUESTION_TYPES = {
    11: "multi-select-true",
    12: "multi-select-true",
    13: "multi-select-true",
    14: "single-best-false",
    15: "single-best-false",
    16: "single-best-false",
    17: "single-best-false",
    18: "single-best-false",
    19: "single-best-false",
    20: "multi-select-false",
}

UNIT_LABELS = {
    11: ["ㄱ", "ㄴ", "ㄷ", "ㄹ"],
    12: ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"],
    13: ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"],
    14: ["①", "②", "③", "④", "⑤"],
    15: ["①", "②", "③", "④", "⑤"],
    16: ["①", "②", "③", "④", "⑤"],
    17: ["①", "②", "③", "④", "⑤"],
    18: ["①", "②", "③", "④", "⑤"],
    19: ["①", "②", "③", "④", "⑤"],
    20: ["㉠", "㉡", "㉢", "㉣", "㉤"],
}

FALSE_LABELS = {
    11: {"ㄷ", "ㄹ"},
    12: {"ㄴ", "ㄹ"},
    13: {"ㄴ", "ㄷ"},
    14: {"①"},
    15: {"②"},
    16: {"③"},
    17: {"③"},
    18: {"④"},
    19: {"②"},
    20: {"㉠", "㉢", "㉣"},
}

TOPICS = {
    11: "공유물 독점점유와 소수지분권자의 청구",
    12: "대리권과 표현대리",
    13: "인지와 친생자관계 및 미성년자 대리",
    14: "채권양도",
    15: "반사회질서와 불공정 법률행위",
    16: "상속회복청구",
    17: "계약해제",
    18: "물권적 청구권",
    19: "법률행위 해석",
    20: "부동산실명법상 명의신탁",
}

REP_ROWS = """
11|ㄱ|공유물의 소수지분권자가 다른 공유자와 협의하지 않고 공유물 전부나 일부를 독점적으로 점유하는 경우 다른 소수지분권자는 보존행위로서 공유물 인도를 청구할 수 없다|
11|ㄴ|공유물의 소수지분권자는 다른 소수지분권자를 전면적으로 배제하고 자신만 단독으로 공유물을 점유하도록 인도를 청구할 권원이 없다|
11|ㄷ|공유물의 소수지분권자가 다른 공유자를 배제하고 공유물을 독점적으로 점유하는 경우 그 점유는 자신의 지분비율을 초과하는 한도에서 위법하다|피고의 점유가 지분비율과 무관하게 공유물 전체 범위에서 위법하다고 본 부분
11|ㄹ|공유물을 독점적으로 점유하는 소수지분권자에 대하여 다른 소수지분권자는 공유물 인도청구는 할 수 없지만 자신의 지분권에 기초하여 방해상태 제거와 공동점유 방해행위 금지를 청구할 수 있다|다른 소수지분권자가 방해상태 제거나 공동점유 방해행위 금지도 청구할 수 없다고 본 부분
12|ㄱ|대리권남용으로 외형상 형성된 법률관계를 기초로 새로운 법률상 이해관계를 맺은 선의의 제3자에게는 민법 제107조 제2항이 유추적용되고, 제3자의 악의 증명책임은 무효를 주장하는 자에게 있다|
12|ㄴ|대부중개업자가 금전소비대차계약과 담보권설정계약 체결 권한을 수여받았더라도 특별한 사정이 없으면 계약 체결 후 이를 해제할 권한까지 당연히 가진다고 볼 수 없다|대부중개업자가 계약 체결 후 해제권한까지 당연히 가진다고 본 부분
12|ㄷ|특정한 법률행위를 위임한 경우 대리인이 본인의 지시에 따라 행위하면 본인은 자기가 안 사정이나 과실로 알지 못한 사정에 관하여 대리인의 부지를 주장하지 못한다|
12|ㄹ|부부 일방이 의식불명 상태에 있다는 사정만으로 배우자가 채무부담행위를 포함한 모든 법률행위에 관한 대리권을 당연히 갖는 것은 아니다|배우자가 모든 법률행위에 관한 대리권을 당연히 갖는다고 본 부분
12|ㅁ|민법 제129조의 대리권소멸 후 표현대리 규정은 법정대리인의 대리권이 소멸된 경우에도 적용될 수 있다|
13|ㄱ|인지청구권은 일신전속적 신분관계상 권리로서 포기할 수 없고 포기하더라도 효력이 없으므로 실효의 법리가 적용될 여지도 없다|
13|ㄴ|혼인외 출생자가 부의 사망 후 인지의 소로 친생자로 인지되면 피인지자보다 후순위 상속인이던 직계존속 또는 형제자매는 민법 제860조 단서의 제3자 보호대상에 포함되지 않는다|후순위 상속인이 인지의 소급효 제한으로 보호되는 제3자에 포함된다고 본 부분
13|ㄷ|제3자가 제기한 친생자관계부존재확인소송 계속 중 친자 중 한쪽이 사망하면 생존자만 피고가 되고 사망자에 대한 소송은 종료되며 상속인이나 검사가 절차를 수계할 수 없다|친자 중 한쪽이 사망한 경우 검사가 망인의 소송절차를 수계할 수 있다고 본 부분
13|ㄹ|전 등기명의인이 미성년자이고 부동산을 친권자에게 증여하는 행위가 이해상반행위라 하더라도 친권자 앞으로 이전등기가 마쳐진 이상 특별한 사정이 없으면 필요한 절차를 적법하게 거친 것으로 추정된다|
13|ㅁ|친권자가 여러 미성년자의 법정대리인으로 상속재산분할협의를 한 경우 민법 제921조에 위반되어 그 협의는 피대리자 전원의 추인이 없는 한 무효이다|
14|①|제1차 지명채권양도 후 확정일자 있는 증서에 의한 대항요건을 갖춘 경우 그 뒤 제1차 양도계약이 합의해지되어 채권이 양도인에게 돌아오더라도 특별한 사정이 없으면 처분권한 없이 한 제2차 양도계약이 채권양도로서 유효하게 되지는 않는다|제1차 양도계약의 합의해지와 통지 후 처분권한 없이 한 제2차 양도계약이 유효하게 될 수 있다고 본 부분
14|②|채권양도금지특약은 양수인이 악의이거나 중대한 과실로 특약을 알지 못한 경우 그 양수인에게 대항할 수 있고, 양수인의 악의 또는 중과실은 특약으로 대항하려는 자가 주장ㆍ증명하여야 한다|
14|③|민법 제449조 제2항 단서의 선의의 제3자에는 악의의 양수인으로부터 다시 선의로 양수한 전득자도 포함된다|
14|④|지명채권양도의 확정일자 있는 증서에 의한 통지나 승낙은 제3자에 대한 대항요건이고, 당해 채권을 양수한 양수인에게까지 확정일자 있는 통지나 승낙이 대항요건으로 필요한 것은 아니다|
14|⑤|채권양도의 통지는 채무자가 통지 내용을 알 수 있는 객관적 상태에 놓이면 도달하고, 민사소송법상 송달장소 등에 관한 규정은 채권양도 통지의 도달에 유추적용되지 않는다|
15|①|대물변제예약이 불공정한 법률행위인지 판단할 때 목적물 가격 사이의 불균형은 원칙적으로 대물변제 효력이 발생할 변제기 당시를 기준으로 하고, 채권액도 변제기까지의 원리액을 기준으로 한다|
15|②|도박채무 변제를 위한 부동산 처분 위임에서 도박채무 부담행위와 변제약정이 무효라도 그 무효는 처분대금으로 도박채무 변제에 충당한 부분에 한정되고, 부동산 처분 대리권 수여행위까지 무효라고 볼 수 없다|도박채무 변제약정의 무효가 부동산 처분 대리권 수여행위까지 미친다고 본 부분
15|③|증언의 대가 약정이 통상적으로 용인될 수 있는 손해전보 수준을 초과하면 금전적 대가가 결부되어 민법 제103조의 반사회질서 법률행위로 무효이다|
15|④|금전소비대차의 이율이 경제적ㆍ사회적 여건에 비추어 사회통념상 허용한도를 초과하여 현저하게 고율이면 그 초과 부분의 이자약정은 민법 제103조에 따라 무효이다|
15|⑤|전전매수 사실을 알면서 상속인을 기망하여 토지를 이중매도하게 한 매수인과 상속인 사이의 양도계약은 반사회적 법률행위로서 무효이다|
16|①|포괄적 유증을 받은 자에게도 민법 제999조의 상속회복청구권 규정이 유추적용된다|
16|②|상속회복청구의 상대방인 참칭상속인은 재산상속인으로 오인될 외관을 갖추거나 상속인이라고 참칭하여 상속재산의 전부 또는 일부를 점유하는 자를 말한다|
16|③|진정상속인이 참칭상속인으로부터 상속재산을 양수한 제3자를 상대로 상속재산 등기말소를 구하는 경우에도 청구원인이 상속을 원인으로 한 권리 귀속이면 상속회복청구권의 제척기간이 적용된다|참칭상속인으로부터 상속재산을 양수한 제3자에 대한 등기말소청구에는 상속회복청구권의 단기 제척기간이 적용되지 않는다고 본 부분
16|④|상속회복청구의 소는 진정상속인과 참칭상속인이 주장하는 피상속인이 동일인임을 전제로 하므로, 양쪽이 주장하는 피상속인이 다른 경우에는 상속을 원인으로 한 소유권 주장이라도 상속회복청구의 소가 아니다|
16|⑤|상속회복청구권이 제척기간 경과로 소멸하면 진정상속인은 상속에 따라 승계한 개개의 권리의무를 총괄적으로 상실하고, 참칭상속인은 상속개시시로 소급하여 상속인 지위를 취득한 것으로 본다|
17|①|매매계약 당사자 일방이 사망하고 여러 상속인이 있는 경우 특별한 사정이 없으면 그 상속인 전원이 해제 의사표시를 하여야 계약을 해제할 수 있다|
17|②|매매계약 해제 후 매도인이 별다른 이의 없이 일부 변제를 수령하면 특별한 사정이 없는 한 해제된 계약을 부활시키는 약정이 있었다고 해석되고, 매도인은 새로운 이행 최고 없이 바로 다시 해제권을 행사할 수 없다|
17|③|계약해제 전에 계약상 채권을 양수하고 이를 피보전권리로 처분금지가처분결정을 받은 채권자도 특별한 사정이 없는 한 민법 제548조 제1항 단서의 제3자에 해당하지 않는다|계약상 채권을 양수하고 처분금지가처분결정을 받은 채권자가 해제의 소급효가 미치지 않는 제3자에 해당한다고 본 부분
17|④|계약해제의 원상회복의무를 규정한 민법 제548조 제1항 본문은 부당이득에 관한 특별규정으로서, 반환범위는 이익 현존 여부나 청구인의 선의ㆍ악의를 불문하고 특별한 사정이 없으면 받은 이익 전부이다|
17|⑤|계약해제로 인한 원상회복청구권은 해제자가 채무불이행 원인의 일부를 제공했다는 사유만으로 손해배상의 과실상계에 준하여 일반적으로 제한될 수 없다|
18|①|토지 매수인이 소유권이전등기를 받지 않았더라도 매매계약 이행으로 토지를 인도받으면 점유ㆍ사용권을 취득하고, 그 매수인으로부터 다시 토지를 매수한 자도 그 점유ㆍ사용권을 취득한다|
18|②|소유권에 기한 물상청구권은 소유권과 분리하여 소유권 없는 전소유자에게 유보할 수 없으므로, 일단 소유권을 상실한 전소유자는 제3자인 불법점유자를 상대로 물권적 방해배제를 청구할 수 없다|
18|③|부동산 양도담보권설정자는 등기명의가 양도담보권자 앞으로 되어 있어도 실질적 소유자로서 불법점유자인 제3자에게 불법점유 상태 배제를 청구할 수 있다|
18|④|토지소유자가 토지사용권 없는 건물의 철거와 대지 인도를 청구할 수 있는 경우 건물점유자가 대항력 있는 임차인이라도 토지소유자의 건물퇴거청구에 대항할 수 없다|대항력 있는 건물임차인이 토지소유자의 건물퇴거청구에 대항할 수 있다고 본 부분
18|⑤|진정명의회복을 원인으로 한 소유권이전등기청구권과 무효등기 말소청구권은 모두 진정한 소유자의 등기명의 회복을 목적으로 하는 소유권에 기한 방해배제청구권이다|
19|①|하나의 법률관계에 관하여 여러 계약서가 순차 작성되고 법률관계나 우열관계가 명확하지 않으면 서로 양립할 수 없는 부분은 원칙적으로 나중에 작성된 계약서 내용대로 변경되었다고 해석한다|
19|②|계약당사자 일방이 합의해지에 관한 조건을 제시한 경우 계약의 합의해지가 성립하려면 그 조건에 관한 합의까지 이루어져야 한다|계약당사자 일방이 제시한 계약해지 조건에 관한 합의가 없어도 합의해지가 성립할 수 있다고 본 부분
19|③|타인의 이름으로 법률행위를 한 경우 계약당사자는 행위자와 상대방의 일치한 의사에 따르고, 의사가 일치하지 않으면 구체적 사정을 토대로 합리적 상대방이 누구를 당사자로 이해할 것인지에 따라 확정한다|
19|④|성립의 진정이 인정되는 처분문서는 그 내용을 부정할 분명하고 수긍할 수 있는 이유가 없으면 문서 내용의 법률행위 존재를 인정하여야 한다|
19|⑤|계약 성립에는 본질적 사항이나 중요사항에 관한 구체적 의사합치 또는 장래 특정할 기준과 방법에 관한 합의가 있으면 충분하다|
20|㉠|부동산실명법에 위반되어 무효인 명의신탁약정에 기하여 타인 명의 등기가 마쳐졌다는 사정만으로 그 등기가 당연히 불법원인급여에 해당하지는 않는다|부동산실명법 위반 명의신탁등기가 당연히 불법원인급여에 해당한다고 본 부분
20|㉡|3자간 등기명의신탁에서는 명의신탁약정과 수탁자 명의 등기가 무효이고 매도인과 명의신탁자 사이의 매매계약은 유효하므로, 명의신탁자는 매도인에 대한 소유권이전등기청구권을 보전하기 위해 매도인을 대위하여 수탁자에게 말소등기를 구할 수 있다|
20|㉢|양자간 등기명의신탁에서 수탁자의 처분으로 제3취득자가 유효하게 소유권을 취득하면 명의신탁자의 물권적 청구권은 더 이상 인정되지 않고, 수탁자가 나중에 우연히 소유권을 다시 취득하더라도 마찬가지이다|수탁자가 나중에 신탁부동산 소유권을 다시 취득하면 명의신탁자의 물권적 청구권도 인정된다고 본 부분
20|㉣|부동산실명법 시행 후 계약명의신탁에서 선의의 매도인으로부터 수탁자 명의 이전등기가 마쳐진 경우 수탁자는 부동산 자체가 아니라 명의신탁자로부터 제공받은 매수자금을 부당이득으로 반환한다|수탁자가 당해 부동산 자체를 부당이득으로 반환해야 한다고 본 부분
20|㉤|3자간 등기명의신탁에서 명의신탁자가 명의신탁 부동산을 인도받아 점유하고 있으면 매도인에 대한 소유권이전등기청구권의 소멸시효는 진행되지 않는다|
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
    "㉠": "ga",
    "㉡": "na",
    "㉢": "da",
    "㉣": "ra",
    "㉤": "ma",
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


def split_box_units(no: int, block: str) -> dict[str, str]:
    labels = UNIT_LABELS[no]
    choice_start = re.search(r"[①②③④⑤]", block)
    stem = block[: choice_start.start()] if choice_start else block
    if labels[0] == "㉠":
        first_by_label: dict[str, re.Match[str]] = {}
        for marker in re.finditer(r"([㉠㉡㉢㉣㉤])", stem):
            label = marker.group(1)
            first_by_label.setdefault(label, marker)
            if set(first_by_label) == set(labels):
                break
        markers = [first_by_label[label] for label in labels if label in first_by_label]
    else:
        markers = [m for m in re.finditer(r"([ㄱㄴㄷㄹㅁ])\.", stem) if m.group(1) in labels]
    if len(markers) != len(labels):
        raise ValueError(f"cannot split box statements for q{no}: got {len(markers)}")
    out: dict[str, str] = {}
    for idx, marker in enumerate(markers):
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(stem)
        out[marker.group(1)] = normalize_raw(stem[marker.end() : end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in QUESTION_RANGE:
        split = split_box_units(no, blocks[no]) if no in {11, 12, 13, 20} else split_choice_units(blocks[no])
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
    return rep if rep.endswith(".") else rep.rstrip(".") + "."


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in QUESTION_RANGE:
        qid = f"2024-g1-civil-law-{no:02d}"
        units = []
        for label in UNIT_LABELS[no]:
            units.append(
                {
                    "unitId": f"{qid}-{LABEL_CODE[label]}",
                    "unitType": "box" if no in {11, 12, 13, 20} else "choice",
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
        "part": "q11-q20",
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
                    "part": "q11-q20",
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
        "part": "q11-q20",
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
                "part": "q11-q20",
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
        "part": "q11-q20",
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
    expected_counts = Counter({11: 4, 12: 5, 13: 5, 20: 5})
    expected_counts.update({no: 5 for no in range(14, 20)})
    counts = Counter(item["no"] for item in completed["items"])
    if counts != expected_counts:
        raise ValueError(f"question atom counts mismatch: {counts}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 34, "X": 15}):
        raise ValueError(f"verdict counts mismatch: {verdict_counts}")
    banned_tokens = [
        "?",
        "？",
        "위 ①",
        "위 ②",
        "위 ③",
        "위 ④",
        "위 ⑤",
        "위 ㉠",
        "위 ㉡",
        "위 ㉢",
        "위 ㉣",
        "위 ㉤",
        "다음 설명",
        "가장 옳",
        "옳지 않은",
    ]
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
                "part": "q11-q20",
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
