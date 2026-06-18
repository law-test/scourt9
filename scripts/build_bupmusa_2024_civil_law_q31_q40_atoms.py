from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2024" / "과목별"
RAW_TEXT_PATH = PRIVATE_ROOT / "text" / "2024" / "2024_법무사_1차_1교시_문제.txt"
INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민법_q31_q40_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민법_q31_q40_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_민법_q31_q40_atoms.json"
FULL_SOURCE_PATH = SUBJECT_DIR / "2024_법무사_민법_source.json"
FULL_QUEUE_PATH = SUBJECT_DIR / "2024_법무사_민법_atom_queue.json"
FULL_OUT_PATH = SUBJECT_DIR / "2024_법무사_민법_atoms.json"

SUBJECT_NAME = "민법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_RANGE = range(31, 41)
EXPECTED_ATOM_COUNT = 50

LEGAL_SOURCES = [
    {"title": "민법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/민법"},
    {"title": "2024 법무사 민법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881318"},
    {"title": "2024 법무사 민법 해설(4)", "publisher": "아쉽공 기출해설", "url": "https://ebssir.tistory.com/entry/2024%EB%85%84-%EB%B2%95%EB%AC%B4%EC%82%AC-%EB%AF%BC%EB%B2%95-%ED%95%B4%EC%84%A44-%EC%95%84%EC%89%BD%EA%B3%B5-%EA%B8%B0%EC%B6%9C%ED%95%B4%EC%84%A4"},
    {"title": "민법 판례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/precSc.do"},
]

PART_SPECS = [
    (
        "q01-q10",
        SUBJECT_DIR / "2024_법무사_민법_q01_q10_source.json",
        SUBJECT_DIR / "2024_법무사_민법_q01_q10_atom_queue.json",
        SUBJECT_DIR / "2024_법무사_민법_q01_q10_atoms.json",
    ),
    (
        "q11-q20",
        SUBJECT_DIR / "2024_법무사_민법_q11_q20_source.json",
        SUBJECT_DIR / "2024_법무사_민법_q11_q20_atom_queue.json",
        SUBJECT_DIR / "2024_법무사_민법_q11_q20_atoms.json",
    ),
    (
        "q21-q30",
        SUBJECT_DIR / "2024_법무사_민법_q21_q30_source.json",
        SUBJECT_DIR / "2024_법무사_민법_q21_q30_atom_queue.json",
        SUBJECT_DIR / "2024_법무사_민법_q21_q30_atoms.json",
    ),
    ("q31-q40", SOURCE_PATH, QUEUE_PATH, OUT_PATH),
]

OFFICIAL_ANSWERS = {
    31: "①",
    32: "④",
    33: "⑤",
    34: "③",
    35: "④",
    36: "③",
    37: "③",
    38: "③",
    39: "④",
    40: "⑤",
}

QUESTION_TYPES = {
    31: "single-best-false",
    32: "single-best-false",
    33: "single-best-true",
    34: "single-best-false",
    35: "single-best-false",
    36: "single-best-false",
    37: "single-best-false",
    38: "single-best-false",
    39: "single-best-false",
    40: "single-best-true",
}

UNIT_LABELS = {
    31: ["①", "②", "③", "④", "⑤"],
    32: ["①", "②", "③", "④", "⑤"],
    33: ["①", "②", "③", "④", "⑤"],
    34: ["①", "②", "③", "④", "⑤"],
    35: ["①", "②", "③", "④", "⑤"],
    36: ["①", "②", "③", "④", "⑤"],
    37: ["①", "②", "③", "④", "⑤"],
    38: ["①", "②", "③", "④", "⑤"],
    39: ["①", "②", "③", "④", "⑤"],
    40: ["①", "②", "③", "④", "⑤"],
}

FALSE_LABELS = {
    31: {"①"},
    32: {"④"},
    33: {"①", "②", "③", "④"},
    34: {"③"},
    35: {"④"},
    36: {"③"},
    37: {"③"},
    38: {"③"},
    39: {"④"},
    40: {"①", "②", "③", "④"},
}

TOPICS = {
    31: "부동산 취득시효",
    32: "소비대차와 준소비대차",
    33: "채무불이행",
    34: "사무관리와 부당이득",
    35: "임대차",
    36: "여행계약",
    37: "수인의 채권자 및 채무자",
    38: "양육",
    39: "저당권",
    40: "채권자대위",
}

REP_ROWS = """
31|①|소유권이전등기가 경료 당시 실체관계와 부합하지 않아 무효였더라도 취득시효완성 후 적법한 권리자로부터 권리를 양수하여 실체관계에 부합하게 되었다면 그 등기명의자는 취득시효완성 후 소유권을 취득한 자에 해당하여 그에게 취득시효완성을 주장할 수 없다|그 등기명의자가 취득시효완성 후 소유권을 취득한 자에 해당하지 않아 취득시효완성을 주장할 수 있다고 본 부분
31|②|진정한 권리자가 아니었던 채무자나 물상보증인이 채무담보 목적으로 저당권설정등기를 해준 뒤 부동산을 시효취득한 경우 저당목적물의 시효취득으로 저당권자의 권리는 소멸하지 않는다|
31|③|양도담보권설정자가 양도담보부동산을 20년간 소유의 의사로 평온ㆍ공연하게 점유하였더라도 점유취득시효를 원인으로 담보목적 소유권이전등기의 말소를 구할 수 없다|
31|④|취득시효완성 후 소유자가 토지에 관한 권리를 주장하는 소를 제기하여 승소판결을 받더라도 그 판결로 시효중단 효력이 발생하지 않고, 점유자가 그 소송에서 시효취득을 주장하지 않았다는 사정만으로 시효이익을 포기한 것도 아니다|
31|⑤|등기부취득시효에서 소유자로 등기한 자는 적법ㆍ유효한 등기를 마친 자일 필요가 없고, 선의ㆍ무과실은 등기가 아니라 점유취득에 관한 것이다|
32|①|준소비대차계약이 성립하려면 금전 기타 대체물의 급부를 목적으로 하는 기존채무가 존재하여야 하고, 기존채무의 존재는 채권자가 증명할 책임이 있다|
32|②|민법상 소비대차는 낙성계약이므로 현실의 금전 수수나 경제적 이익 취득이 있어야만 성립하는 것은 아니지만, 같은 종류ㆍ품질ㆍ수량으로 반환할 약정이 없으면 소비대차라고 할 수 없다|
32|③|반환시기에 관하여 약정이 없는 소비대차에서 반환 최고는 소장 송달로도 할 수 있다|
32|④|부동산 대물반환예약 또는 양도담보 약정에서 채무자는 피담보채무 변제로 소유권이전등기절차 이행의무를 소멸시킬 수 있고, 채무자가 소유권이전등기절차 이행의무를 부담한다는 이유만으로 근저당권설정등기 말소청구가 허용될 수 없다고 단정할 수 없다|채무자가 소유권이전등기절차 이행의무를 부담한다는 이유만으로 그 부동산의 근저당권설정등기 말소청구가 허용될 수 없다고 본 부분
32|⑤|금전소비대차계약 성립 후 차주의 신용불안이나 재산상태 현저한 변경으로 대여금반환청구권 행사가 위태롭게 되어 대여의무 이행이 공평과 신의칙에 반하면 대주는 대여의무 이행을 거절할 수 있다|
33|①|금전채무 이행지체로 발생하는 지연손해금은 손해배상금의 성질을 가지므로 민법 제163조 제1호의 3년 단기소멸시효 대상이 아니다|금전채무 지연이자를 민법 제163조 제1호의 3년 단기소멸시효 대상으로 본 부분
33|②|매수인의 중도금 지급이 선행되어야 매도인이 원매도인에게 잔금을 지급하고 이전등기서류를 마련할 수 있는 특별한 사정을 매수인이 알고 계약한 경우, 잔금지급기일이 지났다는 이유만으로 중도금지급의무가 이전등기서류 제공의무와 동시이행관계가 되지는 않는다|잔금지급기일을 도과하면 매수인의 중도금지급의무가 매도인의 이전등기서류 제공의무와 동시이행관계가 된다고 본 부분
33|③|이행기의 정함이 없는 양수채권에 관하여 채권양수인이 소를 제기하고 소송 계속 중 채권양도통지가 이루어진 경우 특별한 사정이 없으면 채무자는 채권양도통지가 도달한 다음 날부터 이행지체책임을 진다|채무자가 소장부본을 송달받은 다음 날부터 이행지체책임을 진다고 본 부분
33|④|소유권에 기한 등기말소청구권자가 그 후 소유권을 상실하여 등기말소를 청구할 수 없게 되더라도 등기말소의무자에게 민법 제390조의 이행불능 손해배상청구권을 가진다고 할 수 없다|소유권 상실로 등기말소를 청구할 수 없게 되면 등기말소의무자에게 이행불능 손해배상청구권을 가진다고 본 부분
33|⑤|채무불이행으로 인한 손해배상청구소송에서 재산적 손해 발생은 인정되나 구체적 손해액 증명이 곤란한 경우 법원은 변론 전체의 취지와 관련 간접사실을 종합하여 상당한 손해액을 정할 수 있다|
34|①|임차인이 임대차 종료 후 목적물을 계속 점유하였더라도 본래 목적대로 사용ㆍ수익하지 않아 실질적 이익을 얻지 않았다면 임대인에게 손해가 발생했더라도 부당이득반환의무는 성립하지 않는다|
34|②|부당이득제도는 실질적으로 이득이 귀속된 경우에 반환의무를 부담시키는 것이므로 이득자에게 실질적 이득이 귀속된 바 없다면 반환의무를 부담시킬 수 없다|
34|③|사무관리에서 타인을 위하여 사무를 처리하는 의사는 관리자 자신의 이익을 위한 의사와 병존할 수 있고, 반드시 외부적으로 표시되거나 사무관리 당시 확정되어 있을 필요는 없다|타인을 위하여 사무를 처리하는 의사가 외부적으로 표시되어야 하고 사무관리 당시에 확정되어 있어야 한다고 본 부분
34|④|제3자와의 약정에 따라 타인의 사무를 처리한 경우에는 의무 없이 타인의 사무를 처리한 것이 아니므로 원칙적으로 그 타인과의 관계에서 사무관리가 성립한다고 볼 수 없다|
34|⑤|민법 제742조의 비채변제 규정은 변제자가 채무없음을 알면서 변제한 경우에 적용되고, 채무없음을 알았다는 점은 반환청구권을 부인하는 측이 증명하여야 한다|
35|①|주택임대차보호법상 임차인의 계약갱신요구로 갱신 효력이 발생한 뒤 임차인의 해지통지가 갱신기간 개시 전 임대인에게 도달하였더라도, 그 통지가 도달한 날부터 3개월이 지나면 갱신된 임대차계약의 해지효력이 발생한다|
35|②|주택임대차보호법상 임차권등기명령에 따른 임차권등기에는 민법 제168조 제2호의 압류ㆍ가압류ㆍ가처분에 준하는 소멸시효중단 효력이 없다|
35|③|주택임대차보호법상 임대인 또는 그 직계존비속이 목적주택에 실제 거주하려는 경우라는 점은 임대인이 증명하여야 하고, 실제 거주의사는 단순한 의사표명만으로 곧바로 인정되지 않는다|
35|④|법인 임차인의 직원이 법인이 임차한 주택을 인도받아 주민등록을 마치고 거주하면 주택임대차보호법 제3조 제3항의 대항력을 갖춘 것이며, 업무관련성ㆍ임대료ㆍ지리적 근접성 등을 추가로 고려하여 판단하지 않는다|직원이 법인 임차 주택에 주민등록을 마치고 거주하더라도 업무관련성 등 제반사정을 고려하여 대항력 요건을 판단하여야 한다고 본 부분
35|⑤|임대인의 필요비상환의무는 특별한 사정이 없으면 임차인의 차임지급의무와 대응관계에 있으므로 임차인은 지출한 필요비 한도에서 차임 지급을 거절할 수 있다|
36|①|여행자는 여행을 시작하기 전에는 언제든지 여행계약을 해제할 수 있으나 상대방에게 발생한 손해를 배상하여야 한다|
36|②|해외여행 중 여행업자의 고의 또는 과실로 여행자가 상해를 입고 국내 귀환 필요성이 인정되는 경우 귀환운송비 등 추가비용은 여행업자의 고의 또는 과실로 발생한 통상손해에 포함된다|
36|③|민법 제674조의6과 제674조의7에 따른 여행주최자의 담보책임 및 여행자의 해지권은 여행기간 중에도 행사할 수 있고 계약에서 정한 여행 종료일부터 6개월 내에 행사하여야 한다|여행주최자의 담보책임 및 여행자의 해지권을 여행 종료일부터 1년 내에 행사하여야 한다고 본 부분
36|④|기획여행업자는 여행계약 실시 중 여행자가 부딪칠 수 있는 위험을 고지하여 여행자에게 위험 수용 여부를 선택할 기회를 주는 등 합리적 조치를 취할 신의칙상 안전배려의무를 부담한다|
36|⑤|부득이한 사유로 여행계약이 해지된 경우 추가비용은 해지사유가 어느 당사자의 사정에 속하면 그 당사자가 부담하고, 누구의 사정에도 속하지 않으면 각 당사자가 절반씩 부담한다|
37|①|공유물 무단점유자에 대한 차임 상당 부당이득반환청구권은 특별한 사정이 없으면 각 공유자에게 지분비율만큼 귀속된다|
37|②|민법 제428조의2에서 보증인의 서명은 원칙적으로 보증인이 직접 자기 이름을 쓰는 것을 의미하지만, 보증인의 기명날인은 타인이 대행하여도 무방하다|
37|③|부진정연대채무자 중 1인의 상계나 상계계약으로 채무가 소멸하면 그 효력은 소멸한 채무 전액에 관하여 다른 부진정연대채무자에게도 미치며, 이는 채권자가 다른 부진정연대채무자의 존재를 알았는지에 좌우되지 않는다|채권자가 상계 당시 다른 부진정연대채무자의 존재를 알았던 경우에 한하여 상계 효력이 다른 부진정연대채무자에게 미친다고 본 부분
37|④|여러 사람이 공동임대인으로 하나의 임대차계약을 체결한 경우 특별한 사정이 없으면 공동임대인 전원의 해지의사표시로 임대차계약 전부를 해지하여야 하며, 임대차목적물 일부 양도로 공동임대인이 된 경우에도 같다|
37|⑤|연대채무자 중 1인이 다른 연대채무자에게 통지하지 않고 공동면책행위를 한 경우 다른 연대채무자에게 채권자에 대한 대항사유가 있으면 그 부담부분 한도에서 면책행위자에게 대항할 수 있고, 그 사유가 상계이면 상계로 소멸할 채권은 면책행위자에게 이전된다|
38|①|양육자는 인지판결 확정 전에 발생한 과거 양육비에 대하여도 상대방이 부담함이 상당한 범위에서 비용상환을 청구할 수 있다|
38|②|부모의 친권 중 양육권만 제한되어 미성년후견인이 양육권을 행사하는 경우 미성년후견인은 민법 제837조를 유추적용하여 비양육친을 상대로 양육비심판을 청구할 수 있다|
38|③|장래양육비 사건의 항고심에서 일정 시점 이후 양육자로 지정된 자가 자녀를 양육하지 않는 사실이 확인되면 이를 반영하여 장래양육비 지급기간을 다시 정하여야 한다|항고심에서 양육자가 더 이상 자녀를 양육하지 않는 사실이 확인되어도 장래양육비 지급기간을 다시 정할 수 없다고 본 부분
38|④|종전에 정해진 양육비가 과다하다며 감액을 청구하는 경우 법원은 자녀 성장에도 불구하고 감액이 필요할 정도로 청구인의 소득과 재산이 실질적으로 감소하였는지를 심리ㆍ판단하여야 한다|
38|⑤|한국어 습득이 충분하지 않은 기간에 이혼한 외국인 배우자에 대하여 한국어 소통능력이 부족하다는 추상적 판단만으로 미성년 자녀의 양육자 지정에 부적합하다고 평가하여서는 안 된다|
39|①|민법 제365조의 일괄경매청구권은 토지 저당권자가 토지 경매를 신청한 후에도 토지에 관한 경매기일 공고시까지 토지상 건물에 대하여 추가신청할 수 있다|
39|②|공동근저당 목적부동산 일부의 경매절차에서 공동근저당권자가 선순위근저당권자로 채권 전액을 청구하였다면 먼저 우선변제받고 후순위근저당권자는 잔액에서 변제받으며, 이는 선순위와 후순위 근저당권자가 동일인인 경우에도 같다|
39|③|근저당권설정등기상 근저당권자가 다른 사람과 함께 채무자로부터 유효하게 변제받을 수 있고 채무자도 그들 중 누구에게든 유효하게 변제할 수 있는 관계라면 그 근저당권설정등기도 유효하다|
39|④|건물 저당권 실행으로 경락인이 건물소유를 위한 지상권을 취득한 뒤 건물을 제3자에게 양도하면 특별한 사정이 없는 한 건물과 함께 종된 권리인 지상권도 양도하기로 한 것으로 본다|경락인이 건물을 제3자에게 양도한 때 별도 합의가 없으면 지상권도 양도하기로 한 것으로 볼 수 없다고 본 부분
39|⑤|공동저당권이 설정된 여러 부동산 중 일부가 채무자 소유이고 일부가 물상보증인 소유인 경우 각 부동산의 경매대가를 동시에 배당할 때에는 민법 제368조 제1항이 적용되지 않는다|
40|①|채권자대위권 행사에서 제3채무자는 채무자에 대한 모든 항변사유로 채권자에게 대항할 수 있지만, 채권자는 채무자가 주장할 수 있는 사유의 범위 안에서만 주장할 수 있고 자신과 제3채무자 사이의 독자적 사유는 주장할 수 없다|채권자가 자신과 제3채무자 사이의 독자적 사정에 기한 사유도 주장할 수 있다고 본 부분
40|②|채권자가 대위권을 행사할 당시 이미 채무자가 그 권리를 재판상 행사하였다면 설령 채무자가 이후 불성실한 소송수행으로 패소 확정판결을 받았더라도 채권자는 채무자를 대위하여 그 권리를 행사할 당사자적격이 없다|채무자가 재판상 권리를 행사한 뒤 불성실한 소송수행으로 패소 확정판결을 받으면 채권자에게 대위행사의 당사자적격이 있다고 본 부분
40|③|임대인의 임대차계약 해지권은 행사상의 일신전속권으로 볼 수 없으므로 채권자대위권의 대상이 될 수 있다|임대인의 임대차계약 해지권이 행사상의 일신전속권에 해당하여 채권자대위권의 대상이 되지 않는다고 본 부분
40|④|부동산 소유권이전등기청구권자가 등기를 마치기 전에 제3자가 소유자를 상대로 확정판결을 받아 이전등기를 마친 경우 그 확정판결이 당연무효이거나 재심으로 취소되지 않는 한, 종전 청구권자가 소유자를 대위하여 제3자 명의 등기의 말소를 구하는 것은 기판력에 저촉된다|확정판결이 당연무효이거나 재심으로 취소되지 않았더라도 종전 청구권자가 소유자를 대위하여 제3자 명의 등기말소를 구할 수 있다고 본 부분
40|⑤|채무자 소유 부동산을 시효취득한 채권자의 공동상속인이 소유권이전등기청구권을 보전하기 위하여 채무자의 제3채무자에 대한 말소등기청구권을 대위행사하는 경우 자신의 지분 범위에서만 대위행사할 수 있다|
""".strip()

LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
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
        "part": "q31-q40",
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
                    "part": "q31-q40",
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
        "part": "q31-q40",
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
                "part": "q31-q40",
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
        "part": "q31-q40",
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


def validate_part(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if source["questionCount"] != 10:
        raise ValueError("question count mismatch")
    if queue["itemCount"] != EXPECTED_ATOM_COUNT or completed["atomCount"] != EXPECTED_ATOM_COUNT:
        raise ValueError("atom count mismatch")
    counts = Counter(item["no"] for item in completed["items"])
    if counts != Counter({no: 5 for no in QUESTION_RANGE}):
        raise ValueError(f"question atom counts mismatch: {counts}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 34, "X": 16}):
        raise ValueError(f"verdict counts mismatch: {verdict_counts}")
    validate_atom_text(completed["items"])


def validate_atom_text(items: list[dict[str, object]]) -> None:
    banned_tokens = [
        "?",
        "？",
        "위 ①",
        "위 ②",
        "위 ③",
        "위 ④",
        "위 ⑤",
        "다음 설명",
        "가장 옳",
        "옳지 않은",
    ]
    for item in items:
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


def read_json(path: Path) -> dict[str, object]:
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
        if part == "q31-q40":
            part_sources.append(current_source)
            part_queues.append(current_queue)
            part_completed.append(current_completed)
        else:
            part_sources.append(read_json(source_path))
            part_queues.append(read_json(queue_path))
            part_completed.append(read_json(completed_path))

    checked_at = today()
    questions = [strip_part(question) for src in part_sources for question in src["questions"]]
    queue_items = [strip_part(item) for queue in part_queues for item in queue["items"]]
    atom_items = [strip_part(item) for completed in part_completed for item in completed["items"]]
    verification_sources = unique_sources([src["verificationSources"] for src in part_sources])

    full_source = {
        "schema": "legal-scrivener/source-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": checked_at,
        "questionCount": len(questions),
        "verificationSources": verification_sources,
        "questions": questions,
    }
    full_queue = {
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": checked_at,
        "source": str(FULL_SOURCE_PATH),
        "itemCount": len(queue_items),
        "items": queue_items,
    }
    full_completed = {
        "schema": "legal-scrivener/completed-atoms-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
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
    if source["questionCount"] != 40:
        raise ValueError("full question count mismatch")
    if queue["itemCount"] != 199 or completed["atomCount"] != 199:
        raise ValueError("full atom count mismatch")
    counts = Counter(item["no"] for item in completed["items"])
    expected = Counter({no: 5 for no in range(1, 41)})
    expected[11] = 4
    if counts != expected:
        raise ValueError(f"full question atom counts mismatch: {counts}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 139, "X": 60}):
        raise ValueError(f"full verdict counts mismatch: {verdict_counts}")
    validate_atom_text(completed["items"])


def update_index(full_source: dict[str, object], full_queue: dict[str, object], full_completed: dict[str, object]) -> None:
    index = read_json(INDEX_PATH) if INDEX_PATH.exists() else {
        "schema": "legal-scrivener/subject-index/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subjects": {},
    }
    index["updatedAt"] = today()
    index.setdefault("subjects", {})[SUBJECT_NAME] = {
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
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = extract_question_blocks()
    raws = raw_statement_map(blocks)
    source = build_source(raws)
    queue = build_queue(source)
    completed = build_completed(queue)
    validate_part(source, queue, completed)

    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_PATH.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    full_source, full_queue, full_completed = build_full_outputs(source, queue, completed)
    FULL_SOURCE_PATH.write_text(json.dumps(full_source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FULL_QUEUE_PATH.write_text(json.dumps(full_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FULL_OUT_PATH.write_text(json.dumps(full_completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_index(full_source, full_queue, full_completed)

    print(
        json.dumps(
            {
                "subject": SUBJECT_NAME,
                "part": "q31-q40",
                "source": str(SOURCE_PATH),
                "queue": str(QUEUE_PATH),
                "completed": str(OUT_PATH),
                "questions": source["questionCount"],
                "atoms": completed["atomCount"],
                "verdictCounts": dict(Counter(item["sourceVerdict"] for item in completed["items"])),
                "fullCompleted": str(FULL_OUT_PATH),
                "fullAtoms": full_completed["atomCount"],
                "fullVerdictCounts": dict(Counter(item["sourceVerdict"] for item in full_completed["items"])),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
