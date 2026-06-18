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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민법_q21_q30_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민법_q21_q30_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_민법_q21_q30_atoms.json"

SUBJECT_NAME = "민법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_RANGE = range(21, 31)
EXPECTED_ATOM_COUNT = 50

LEGAL_SOURCES = [
    {"title": "민법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민법"},
    {"title": "2024 법무사 민법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881318"},
    {"title": "2024 법무사 민법 해설(3)", "publisher": "아쉽공 기출해설", "url": "https://ebssir.tistory.com/entry/2024%EB%85%84-%EB%B2%95%EB%AC%B4%EC%82%AC-%EB%AF%BC%EB%B2%95-%ED%95%B4%EC%84%A43-%EC%95%84%EC%89%BD%EA%B3%B5-%EA%B8%B0%EC%B6%9C%ED%95%B4%EC%84%A4"},
    {"title": "민법 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
]

OFFICIAL_ANSWERS = {
    21: "④",
    22: "②",
    23: "②",
    24: "④",
    25: "③",
    26: "④",
    27: "①",
    28: "③",
    29: "②",
    30: "②",
}

QUESTION_TYPES = {
    21: "single-best-false",
    22: "single-best-false",
    23: "single-best-false",
    24: "single-best-false",
    25: "multi-select-false",
    26: "single-best-false",
    27: "single-best-false",
    28: "single-best-false",
    29: "single-best-false",
    30: "single-best-false",
}

UNIT_LABELS = {
    21: ["①", "②", "③", "④", "⑤"],
    22: ["①", "②", "③", "④", "⑤"],
    23: ["①", "②", "③", "④", "⑤"],
    24: ["①", "②", "③", "④", "⑤"],
    25: ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"],
    26: ["①", "②", "③", "④", "⑤"],
    27: ["①", "②", "③", "④", "⑤"],
    28: ["①", "②", "③", "④", "⑤"],
    29: ["①", "②", "③", "④", "⑤"],
    30: ["①", "②", "③", "④", "⑤"],
}

FALSE_LABELS = {
    21: {"④"},
    22: {"②"},
    23: {"②"},
    24: {"④"},
    25: {"ㄱ", "ㄷ", "ㄹ"},
    26: {"④"},
    27: {"①"},
    28: {"③"},
    29: {"②"},
    30: {"②"},
}

TOPICS = {
    21: "점유와 유치권",
    22: "이혼과 사실혼 해소에 따른 재산분할",
    23: "매매와 해약금",
    24: "공동소유",
    25: "법률행위 취소",
    26: "예금계약",
    27: "동시이행항변",
    28: "신의칙과 권리남용",
    29: "권리의 주체와 객체",
    30: "보증",
}

REP_ROWS = """
21|①|유치권자가 점유침탈로 유치물 점유를 상실하면 유치권은 소멸하고, 점유회수의 소로 승소하여 점유를 회복하기 전에는 유치권이 되살아나지 않는다|
21|②|유치권의 불가분성에 따라 유치물의 각 부분은 피담보채권 전부를 담보하고, 이는 목적물이 분할 가능하거나 여러 물건인 경우에도 적용된다|
21|③|부동산 점유자의 자력탈환권은 침탈 후 사회관념상 가능한 한 신속한 범위에서만 행사할 수 있으므로, 침탈 후 상당한 시간이 지나면 점유자가 침탈사실을 알았는지와 관계없이 행사할 수 없다|
21|④|계약명의신탁에서 명의신탁자가 명의수탁자에게 가지는 부동산 매수자금 상당의 부당이득반환청구권은 민법 제320조 제1항의 그 물건에 관하여 생긴 채권에 해당하지 않는다|계약명의신탁자의 매수자금 상당 부당이득반환청구권이 유치권의 견련관계 있는 채권이라고 본 부분
21|⑤|수급인의 재료와 노력으로 건축되어 독립한 건물이 된 기성부분이 수급인의 소유라면 수급인은 그 기성부분에 관하여 유치권을 가질 수 없다|
22|①|사실혼관계가 일방 당사자의 사망으로 종료된 경우 생존 상대방에게 재산분할청구권은 인정되지 않는다|
22|②|이혼으로 인한 재산분할청구권은 협의 또는 심판으로 구체적 내용이 형성되기 전에는 범위와 내용이 불명확ㆍ불확정하므로 채권자대위권으로 보전할 수 없다|협의나 심판절차가 개시되면 재산분할청구권 보전을 위해 채권자대위권을 행사할 수 있다고 본 부분
22|③|협의이혼을 예정한 재산분할협의에서 분할대상 재산과 액수는 협의이혼 성립일을 기준으로 정하고, 그때까지 변제된 분할대상 채무액은 원칙적으로 공제된다|
22|④|재산분할에서 상대방이 귀속 몫보다 적극재산을 더 많이 보유하거나 소극재산 부담이 더 적으면 적극재산 분배뿐 아니라 소극재산 분담 방식의 재산분할도 가능하다|
22|⑤|협의상이혼을 전제로 재산분할청구권 포기 서면을 작성했더라도 공동재산 청산ㆍ분배에 관한 실질적 협의가 없으면 이는 허용되지 않는 사전포기에 불과하다|
23|①|매매예약완결권은 형성권으로서 약정한 행사기간 안에, 약정이 없으면 예약 성립일부터 10년 안에 행사하여야 하고 그 기간이 지나면 제척기간 경과로 소멸한다|
23|②|매매계약에서 매수인이 중도금을 지급하여 이행에 착수한 이상 매도인이 아직 이행에 착수하지 않았더라도 매수인은 민법 제565조에 따라 계약금을 포기하고 해제할 수 없다|상대방인 매도인이 이행에 착수하지 않았으면 이미 이행에 착수한 매수인도 계약금을 포기하고 해제할 수 있다고 본 부분
23|③|매매예약 성립 후 예약완결 의사표시 전에 목적물이 멸실 등으로 이전할 수 없게 되면 예약완결권을 행사할 수 없고, 그 후 예약완결 의사표시를 하더라도 매매의 효력은 생기지 않는다|
23|④|매매계약에서 계약금 일부만 지급된 경우 해약금의 기준은 실제 교부받은 계약금이 아니라 약정계약금이므로, 매도인은 지급받은 일부 계약금의 배액 상환만으로 계약을 해제할 수 없다|
23|⑤|민법 제565조의 이행착수는 특별한 사정이 없으면 이행기 전에도 가능하다|
24|①|공유자가 보존권을 행사한 결과가 다른 공유자의 이해와 충돌할 때에는 그 행사를 공유물의 보존행위로 볼 수 없다|
24|②|집합건물 대지를 구분소유자인 공유자와 구분소유자가 아닌 공유자가 공유하는 경우 특별한 사정 아래 구분소유자에게 대지를 취득시키고 다른 공유자에게 지분가격을 취득시키는 공유물분할청구는 허용될 수 있다|
24|③|조합재산의 처분ㆍ변경은 특별한 사정이 없으면 민법 제706조 제2항이 민법 제272조에 우선 적용되어 업무집행자가 없는 경우 조합원 과반수, 업무집행자가 여럿이면 그 과반수, 업무집행자가 1인이면 그 업무집행자가 결정한다|
24|④|여러 채권자가 하나의 근저당권을 준공유하는 경우 준공유자 전원이 피담보채권 확정 전에 변제비율이나 우선변제 약정을 하면 그 약정에 따르고, 이를 등기하면 제3자에게도 효력이 있다|피담보채권 확정 전 다른 변제비율이나 우선변제 약정을 하더라도 준공유자들이 그 약정에 구속되지 않는다고 본 부분
24|⑤|총유물 보존행위에는 민법 제265조가 적용되지 않고, 법인 아닌 사단이 총유재산 보존행위로 소송을 하려면 사원총회 결의나 정관이 정한 절차를 거쳐야 한다|
25|ㄱ|상대방이 표의자의 착오를 알고 이를 이용한 경우에는 착오가 표의자의 중대한 과실로 인한 것이더라도 표의자는 의사표시를 취소할 수 있다|상대방이 착오를 알고 이용한 경우에도 표의자의 중대한 과실이 있으면 취소할 수 없다고 본 부분
25|ㄴ|동기의 착오가 중요부분 착오가 되려면 동기가 의사표시 내용으로 표시되어 법률행위의 내용으로 인정되고, 보통 사람이 표의자 입장에 섰더라면 같은 의사표시를 하지 않았을 정도로 중요한 부분에 관한 착오여야 한다|
25|ㄷ|제한능력자의 법률행위가 취소된 경우 제한능력자는 그 행위로 받은 이익이 현존하는 한도에서만 상환할 책임이 있다|제한능력자가 취소된 법률행위로 수령한 급부 전부를 부당이득으로 반환해야 한다고 본 부분
25|ㄹ|타인 소유 부동산을 임대한 사정만으로 임대차계약 해지사유나 착오취소사유가 되는 것은 아니고, 임대인 소유라는 점을 특히 계약 내용으로 삼은 경우에 착오취소가 문제될 수 있다|목적물이 임대인 소유라는 점을 계약 내용으로 삼지 않아도 타인 소유 부동산 임대이면 해지와 착오취소가 가능하다고 본 부분
25|ㅁ|상품 선전ㆍ광고의 다소 과장이나 허위는 상거래 관행과 신의칙상 시인되는 한 기망성이 없지만, 중요한 사항의 구체적 사실을 비난받을 정도로 허위 고지하면 기망행위에 해당한다|
26|①|예금자가 예금 의사로 금융기관에 돈을 제공하고 금융기관이 그 의사에 따라 돈을 받아 확인하면 예금계약이 성립하며, 직원의 횡령은 예금계약 성립에 영향을 주지 않는다|
26|②|수취인 예금계좌에 자금이체되어 예금원장에 입금기록이 되면 특별한 사정이 없는 한 원인관계 존재 여부와 관계없이 수취인과 수취은행 사이에 입금액 상당 예금계약이 성립한다|
26|③|예금주의 지급지시나 출금동의가 없었는데 은행 착오로 인출과 입금기록이 완료된 경우에도 수취인과 수취은행 사이에는 입금액 상당 예금계약이 성립한다|
26|④|착오송금 반환 요청이 있고 수취인도 착오송금 사실을 인정하여 반환을 승낙한 경우 수취은행이 특별한 사정 없이 대출채권 등을 자동채권으로 착오입금 예금채권과 상계하는 것은 신의칙에 반하거나 권리남용에 해당한다|착오송금 반환 요청과 수취인의 반환 승낙이 있는 경우 수취은행의 상계가 원칙적으로 가능하다고 본 부분
26|⑤|만기가 정해진 예금계약의 예금반환채무는 특별한 사정이 없으면 임치인의 적법한 지급청구가 있어야 이행할 수 있으므로, 만기 도래만으로 금융기관이 지체책임을 부담하지 않는다|
27|①|어음상 권리가 시효완성으로 소멸하여 채무자에게 이중지급 위험이 없고 다른 어음상 채무자에 대한 권리행사도 불가능한 경우에는 원인채권 행사에 대하여 어음상환의 동시이행항변을 인정할 필요가 없다|어음상 권리가 시효완성으로 소멸하여도 원인채권 행사에 대한 어음상환 동시이행항변을 인정할 필요가 있다고 본 부분
27|②|토지임차인의 매수청구권 행사로 건물 매매 유사의 법률관계가 성립하면 임차인의 건물명도ㆍ소유권이전등기의무와 임대인의 건물대금지급의무는 서로 대가관계에 있다|
27|③|부동산 명도 전에 잔대금을 먼저 지급하기로 한 매매에서도 계약이 해제되지 않은 상태에서 명도기일이 지나도록 명도가 되지 않으면 그때부터 잔대금지급채무와 명도의무는 동시이행관계에 있다|
27|④|매수인이 매매목적 부동산 일부에 대해서만 소유권이전등기의무 이행을 구하는 경우에도 특별한 사정이 없으면 매도인은 매매잔대금 전부에 관하여 동시이행항변권을 행사할 수 있다|
27|⑤|항변권이 붙은 채권을 자동채권으로 하는 상계는 상대방의 항변권 행사 기회를 잃게 하므로 그 성질상 허용되지 않는다|
28|①|계속적 보증계약에서 보증인은 원칙적으로 변제기 주채무 전액에 책임을 지고, 채권자의 신의칙 위반 등 특별한 사정이 있는 경우에 한하여 책임을 합리적 범위로 제한할 수 있다|
28|②|위임계약에서 보수액 약정이 있더라도 위임 경위와 업무처리 내용 등 제반 사정상 약정보수액이 부당하게 과다하여 신의칙이나 형평에 반하면 상당한 범위의 보수액만 청구할 수 있다|
28|③|사정변경 해제ㆍ해지에서 사정이란 계약성립의 기초가 된 사정을 말하고, 당사자가 계약의 기초로 삼지 않은 사정이나 일방이 변경 위험을 떠안기로 한 사정은 포함되지 않는다|사정변경의 사정에 일방당사자가 변경에 따른 불이익이나 위험을 떠안기로 한 사정까지 포함된다고 본 부분
28|④|점유자가 취득시효완성 후 그 사실을 모르고 토지에 관하여 권리를 주장하지 않기로 하였더라도 특별한 사정이 없으면 그와 반대로 취득시효를 주장하는 것은 신의칙상 허용되지 않는다|
28|⑤|상속인이 피상속인 생전에 상속포기 약정을 했더라도 상속개시 후 민법상 절차와 방식에 따른 상속포기를 하지 않은 이상 상속권 주장은 권리남용이나 신의칙 위반이 아니다|
29|①|종중의 목적과 본질상 공동선조와 성과 본을 같이 하는 후손은 성별 구별 없이 성년이 되면 당연히 종중 구성원이 되고, 자녀의 성과 본이 모의 성과 본으로 변경된 경우 성년인 자녀는 모가 속한 종중의 구성원이 된다|
29|②|사단법인 사원은 민법이나 정관에 다른 규정이 없으면 서면이나 대리인으로 결의권을 행사할 수 있다|사단법인의 결의권을 서면으로 행사하는 것은 금지되고 대리인을 통한 행사는 허용된다고 본 부분
29|③|의사능력은 자기 행위의 의미나 결과를 합리적으로 판단할 정신적 능력으로서 구체적 법률행위별로 판단하고, 특별한 법률적 의미나 효과가 있는 행위에서는 그 법률적 의미나 효과도 이해할 수 있어야 인정된다|
29|④|민법 제35조의 이사 기타 대표자는 법인의 대표기관을 의미하므로 대표권 없는 이사의 행위로는 법인의 불법행위가 성립하지 않는다|
29|⑤|구분건물 전유부분에 대한 소유권보존등기만 된 상태에서 전유부분에 내려진 가압류결정의 효력은 특별한 사정이 없으면 종물 내지 종된 권리인 대지권에도 미친다|
30|①|주채무 소멸시효 완성으로 보증채무가 소멸한 뒤 보증인이 보증채무를 이행하거나 승인하더라도 그 행위만으로 주채무의 소멸시효이익 포기 효과가 발생하지 않는다|
30|②|채권자와 주채무자 사이의 확정판결로 주채무 소멸시효기간이 10년으로 연장되더라도 보증채무까지 당연히 10년의 소멸시효기간이 적용되는 것은 아니다|주채무 확정판결로 주채무 시효가 10년으로 연장되면 보증채무도 당연히 10년 시효가 적용된다고 본 부분
30|③|주채무자에 대한 시효중단은 보증인에게도 효력이 있고, 그 중단사유가 압류ㆍ가압류ㆍ가처분인 경우에도 보증인에게 통지하여야 비로소 효력이 생기는 것은 아니다|
30|④|수탁보증인의 사전구상권과 사후구상권은 발생원인과 법적 성질이 다른 별개의 독립된 권리이므로 사후구상권 발생 후에도 사전구상권은 병존하고, 목적달성으로 한쪽이 소멸하면 다른 쪽도 소멸한다|
30|⑤|민법 제447조는 어느 연대채무자나 불가분채무자를 위하여 보증인이 된 자의 다른 채무자에 대한 구상권 규정이므로, 연대채무자 모두를 위하여 물상보증인이 된 자가 연대채무자 1인에게 구상권을 행사하는 경우에는 적용되지 않는다|
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
    labels = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"]
    choice_start = re.search(r"[①②③④⑤]", block)
    stem = block[: choice_start.start()] if choice_start else block
    markers = [m for m in re.finditer(r"([ㄱㄴㄷㄹㅁ])\.", stem) if m.group(1) in labels]
    if len(markers) != len(labels):
        raise ValueError(f"cannot split box statements: got {len(markers)}")
    out: dict[str, str] = {}
    for idx, marker in enumerate(markers):
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(stem)
        out[marker.group(1)] = normalize_raw(stem[marker.end() : end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in QUESTION_RANGE:
        split = split_box_units(blocks[no]) if no == 25 else split_choice_units(blocks[no])
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
                    "unitType": "box" if no == 25 else "choice",
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
        "part": "q21-q30",
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
                    "part": "q21-q30",
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
        "part": "q21-q30",
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
                "part": "q21-q30",
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
        "part": "q21-q30",
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
    if verdict_counts != Counter({"O": 38, "X": 12}):
        raise ValueError(f"verdict counts mismatch: {verdict_counts}")
    banned_tokens = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "옳지 않은"]
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
                "part": "q21-q30",
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
