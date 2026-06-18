from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2022" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2022_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2022"
TEXT_DIR = PRIVATE_ROOT / "text" / "2022"
RAW_PDF_PATH = RAW_DIR / "2022_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2022_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2022_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2022_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2022_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2022_법무사_과목별_index.json"
INTEGRATED_DIR = PRIVATE_ROOT / "current" / "통합본"
INTEGRATED_PATH = INTEGRATED_DIR / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2022_bupmusa_1st"
YEAR = 2022
ROUND = 28
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 120
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS = ["㉠", "㉡", "㉢", "㉣", "㉤"]
LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
    "㉠": "01",
    "㉡": "02",
    "㉢": "03",
    "㉣": "04",
    "㉤": "05",
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "인사청문회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/인사청문회법"},
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "국적법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국적법"},
    {"title": "형사보상 및 명예회복에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사보상및명예회복에관한법률"},
    {"title": "2022 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2022"},
    {"title": "2022 법무사 헌법 해설", "publisher": "김건호 헌법", "url": "local:2022_법무사_헌법_해설_법무사_김건호.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "③",
    3: "②",
    4: "⑤",
    5: "⑤",
    6: "①",
    7: "③",
    8: "①",
    9: "②",
    10: "③",
    11: "⑤",
    12: "⑤",
    13: "④",
    14: "②",
    15: "③",
    16: "③",
    17: "②",
    18: "⑤",
    19: "①",
    20: "②",
}

QUESTION_TYPES = {
    1: "single-best-false",
    2: "single-best-true",
    3: "single-best-false",
    4: "single-best-false",
    5: "single-best-true",
    6: "single-best-false",
    7: "single-best-false",
    8: "single-best-false",
    9: "combination-false",
    10: "single-best-false",
    11: "single-best-false",
    12: "single-best-true",
    13: "single-best-false",
    14: "single-best-false",
    15: "single-best-false",
    16: "single-best-true",
    17: "single-best-false",
    18: "single-best-false",
    19: "count-false",
    20: "single-best-false",
}

FALSE_LABELS = {
    1: {"⑤"},
    2: {"①", "②", "④", "⑤"},
    3: {"②"},
    4: {"⑤"},
    5: {"①", "②", "③", "④"},
    6: {"①"},
    7: {"③"},
    8: {"①"},
    9: {"㉡", "㉣"},
    10: {"③"},
    11: {"⑤"},
    12: {"①", "②", "③", "④"},
    13: {"④"},
    14: {"②"},
    15: {"③"},
    16: {"①", "②", "④", "⑤"},
    17: {"②"},
    18: {"⑤"},
    19: set(),
    20: {"②"},
}

TOPICS = {
    1: "재판청구권",
    2: "인사청문회",
    3: "헌법소원의 대상",
    4: "통신의 비밀과 통신의 자유",
    5: "법무사와 직업의 자유",
    6: "정치적 표현의 자유",
    7: "소급입법과 형벌불소급",
    8: "재산권",
    9: "평등원칙",
    10: "국무회의",
    11: "탄핵소추 대상",
    12: "국회의 입법권",
    13: "대한민국 국민과 국적",
    14: "감사원",
    15: "헌법개정 절차",
    16: "공무원제도",
    17: "직업의 자유",
    18: "헌법 전문",
    19: "정당",
    20: "형사보상청구권",
}

BASIS = {
    1: ("헌법+헌법재판소 결정례", "헌법 제27조 및 재판청구권 관련 헌법재판소 결정례", "재판청구권의 보호영역과 절차보장 기준에 관한 법리이다."),
    2: ("헌법+국회법+인사청문회법+헌법재판소 결정례", "국회법·인사청문회법상 인사청문 절차 및 관련 결정례", "인사청문회의 근거, 담당 위원회, 보고서 효력, 송부요청 기간에 관한 지점이다."),
    3: ("헌법재판소법+헌법재판소 결정례", "헌법소원의 공권력 행사성 및 부작위 심판요건 관련 결정례", "헌법소원의 대상이 되는 공권력 행사와 부작위 요건을 구별하는 법리이다."),
    4: ("헌법+통신비밀보호법+헌법재판소 결정례", "통신의 비밀·통신의 자유 및 개인정보 관련 결정례", "통신제한, 수용자 서신, 이동통신 본인확인에 관한 기본권 제한 법리이다."),
    5: ("헌법+법무사법+헌법재판소 결정례", "법무사 직역과 직업의 자유 관련 결정례", "법무사 직업수행 제한과 직업선택 제한의 위헌심사 지점이다."),
    6: ("헌법+공직선거법+정당법+헌법재판소 결정례", "정치적 표현의 자유와 선거·경선 규제 관련 결정례", "공무원·군무원·공공기관 직원의 정치적 표현 제한 법리이다."),
    7: ("헌법+헌법재판소 결정례", "소급입법, 공소시효, 형벌불소급 관련 결정례", "진정·부진정소급입법과 형벌불소급 적용범위의 구별 지점이다."),
    8: ("헌법+헌법재판소 결정례", "재산권 보호영역과 공무원연금·기탁금·영업기회 관련 결정례", "재산권 침해 여부와 보호영역에 관한 법리이다."),
    9: ("헌법+헌법재판소 결정례", "평등원칙 관련 헌법재판소 결정례", "비교집단 간 차별취급의 합리성 판단 지점이다."),
    10: ("헌법+헌법재판소 결정례", "헌법 제63조·제88조 및 국무회의 관련 결정례", "국무회의의 성격과 국무위원 해임건의 요건에 관한 지점이다."),
    11: ("헌법+검찰청법", "헌법 제65조 및 검찰청법상 검사 신분보장 규정", "탄핵소추 대상의 헌법상 명시 여부를 구별하는 조문 지점이다."),
    12: ("헌법+헌법재판소 결정례", "헌법 제51조·제52조·제53조 및 입법권 관련 결정례", "법률안 제출, 심의·표결, 재의, 계속심사, 권한쟁의 당사자능력에 관한 지점이다."),
    13: ("헌법+국적법+대법원 판례+헌법재판소 결정례", "헌법 제2조와 국적법 및 국민 범위 관련 판례", "국민 요건, 북한주민, 혈통주의, 귀화와 국적회복에 관한 지점이다."),
    14: ("헌법+감사원법+헌법재판소 결정례", "헌법 제97조·제98조, 감사원법 및 감사 범위 관련 결정례", "감사원의 지위, 감사위원 임명, 직무감찰, 감사 범위에 관한 조문 지점이다."),
    15: ("헌법", "헌법 제128조부터 제130조 및 제89조", "헌법개정의 발의, 공고, 의결, 국민투표, 공포와 국무회의 심의에 관한 조문 지점이다."),
    16: ("헌법+국가공무원법+헌법재판소 결정례", "헌법 제7조·제33조, 국가공무원법 및 공무원제도 관련 결정례", "직업공무원제도, 공무담임권, 공무원 노동권과 품위유지의무에 관한 지점이다."),
    17: ("헌법+헌법재판소 결정례", "직업의 자유 관련 헌법재판소 결정례", "직업수행 제한, 기업의 자유, 최저임금 환산, 외국인근로자 사업장 변경 제한에 관한 법리이다."),
    18: ("헌법 전문+헌법재판소 결정례", "현행 헌법 전문 및 헌법 전문 관련 결정례", "헌법 전문의 문언과 전문상 이념의 규범적 효력에 관한 지점이다."),
    19: ("헌법+헌법재판소 결정례", "헌법 제8조 및 정당해산·정당활동의 자유 관련 결정례", "정당해산 요건과 정당설립·존속·활동의 자유에 관한 지점이다."),
    20: ("헌법+형사보상법+헌법재판소 결정례", "헌법 제28조 및 형사보상청구권 관련 결정례", "형사보상청구권의 주체, 심사기준, 관할과 기간에 관한 지점이다."),
}

ATOM_ROWS = """
1|①|01|O|법관에 의한 재판을 받을 권리는 법관이 사실을 확정하고 법률을 해석·적용하는 재판을 받을 권리를 보장한다.|
1|①|02|O|법관의 사실확정과 법률 해석·적용 기회에 접근하기 어렵게 하는 제약이나 장벽은 재판청구권의 본질적 내용을 침해할 수 있다.|
1|②|01|O|재판청구권은 재판이라는 국가적 행위를 청구할 수 있는 적극적 측면을 포함한다.|
1|②|02|O|재판청구권은 헌법과 법률이 정한 법관이 아닌 자의 재판이나 법률에 의하지 않은 재판을 받지 않을 소극적 측면을 포함한다.|
1|③|01|O|피고인이 스스로 치료감호를 청구할 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|
1|③|02|O|피고인이 법원으로부터 직권으로 치료감호를 선고받을 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|
1|④|01|O|공정한 재판을 받을 권리는 헌법 제27조의 재판청구권에 의하여 보장된다.|
1|⑤|01|X|형사소송법상 즉시항고 제기기간을 3일로 정한 조항은 입법재량의 한계를 일탈하여 재판청구권을 침해한다.|형사소송법상 즉시항고 제기기간 3일이 형사재판의 특성을 반영한 합리적 차별이라고 한 부분
2|①|01|X|인사청문회 제도는 헌법이 아니라 국회법과 인사청문회법 등 법률에 규정되어 있다.|헌법이 일부 고위공직자의 임명시 인사청문회 실시를 규정한다고 한 부분
2|②|01|X|헌법상 국회 동의가 필요한 대법원장·헌법재판소장·국무총리·감사원장·대법관 등에 대한 인사청문회는 인사청문특별위원회에서 실시한다.|대법원장·대법관·헌법재판소장은 법제사법위원회, 국무총리·감사원장은 정무위원회가 인사청문회를 실시한다고 한 부분
2|②|02|X|헌법상 국회에서 선출하는 헌법재판소 재판관과 중앙선거관리위원회 위원에 대한 인사청문회는 인사청문특별위원회에서 실시한다.|헌법상 국회 선출 공직후보자의 인사청문 담당 위원회를 누락한 부분
2|③|01|O|국회에 선출권이나 동의권이 없는 공직후보자에 관한 국회 인사청문경과보고서는 임명권자를 법적으로 구속하지 않는다.|
2|④|01|X|국회가 기간 내 인사청문경과보고서를 송부하지 못하면 임명권자는 10일 이내의 범위에서 기간을 정하여 송부를 요청할 수 있다.|인사청문경과보고서 송부 재요청 기간을 15일 이내라고 한 부분
2|⑤|01|X|대통령당선인은 국무총리 후보자에 대한 인사청문 실시를 요청할 수 있다.|대통령당선인은 법률적 지위가 없어 인사청문 요청을 할 수 없다고 한 부분
2|⑤|02|X|대통령당선인은 대통령직 인수에 관한 법률에 따라 국무위원 후보자에 대한 인사청문 요청을 할 수 있다.|대통령당선인의 국무위원 후보자 인사청문 요청권을 부정한 부분
3|①|01|O|행정규칙은 원칙적으로 헌법소원의 대상이 될 수 없다.|
3|①|02|O|법령의 위임에 따라 구체적 내용을 보충하는 행정규칙은 예외적으로 헌법소원의 대상이 될 수 있다.|
3|①|03|O|재량준칙이 행정관행으로 형성되어 자기구속을 발생시키는 경우에는 그 행정규칙도 헌법소원의 대상이 될 수 있다.|
3|②|01|X|중앙선거관리위원회가 특정 정당명칭이 유사명칭에 해당하여 사용할 수 없다고 결정·공표한 행위는 헌법소원의 대상인 공권력 행사에 해당하지 않는다.|중앙선거관리위원회의 유사명칭 결정·공표가 정당의 법적 지위에 영향을 미치는 공권력 행사라고 한 부분
3|③|01|O|대통령기록물 소관 기록관이 대통령기록물을 중앙기록물관리기관으로 이관하는 행위는 국가기관 사이의 내부적·절차적 행위에 불과하다.|
3|③|02|O|대통령기록물 이관행위는 헌법소원의 대상이 되는 공권력 행사에 해당하지 않는다.|
3|④|01|O|경찰서장이 시장에게 개인정보 확인자료를 요청하더라도 시장에게 협조의무가 없으면 그 요청행위만으로 공권력 행사성이 인정되지 않는다.|
3|⑤|01|O|행정권력의 부작위에 대한 헌법소원은 헌법에서 유래하는 구체적 작위의무가 특별히 인정되는 경우에 한하여 허용된다.|
4|①|01|O|인터넷회선 감청은 헌법 제18조의 통신의 비밀과 자유를 제한한다.|
4|①|02|O|인터넷회선 감청은 헌법 제17조의 사생활의 비밀과 자유도 제한하므로 과잉금지원칙을 준수하여야 한다.|
4|②|01|O|교도소장이 법원 등 관계기관이 수용자에게 보낸 문서를 법령상 기간준수 확인 등을 위하여 열람하는 행위는 수용자의 통신의 자유를 침해하지 않을 수 있다.|
4|③|01|O|통신제한조치기간 연장에 총연장기간이나 총연장횟수의 제한을 두지 않은 통신비밀보호법 조항은 통신의 비밀을 침해한다.|
4|④|01|O|수용자가 발송하는 모든 서신을 봉함하지 않은 상태로 제출하게 하는 것은 수용자의 통신비밀의 자유를 침해한다.|
4|⑤|01|X|이동통신서비스 가입 시 본인확인절차를 거치게 하는 조항은 개인정보자기결정권을 침해하지 않는다.|이동통신서비스 가입 본인확인절차가 익명 가입 희망자의 통신의 자유를 침해한다고 한 부분
4|⑤|02|X|이동통신서비스 가입 시 본인확인절차를 거치게 하는 조항은 통신의 자유를 침해하지 않는다.|이동통신서비스 가입 본인확인절차가 익명 가입 희망자의 통신의 자유를 침해한다고 한 부분
5|①|01|X|법무사보수기준제는 법무사의 직업행사의 자유를 제한한다.|법무사보수기준제가 직업선택 자체를 제한한다고 전제한 부분
5|①|02|X|법무사보수기준제의 직업의 자유 제한 여부는 비례원칙으로 심사한다.|법무사보수기준제의 심사기준이 비례성원칙이 아니라 자의금지원칙이라고 한 부분
5|②|01|X|전자등기 사용자등록 조항은 무자격 등기 브로커에 의한 등기신청을 허용하는 규정이 아니다.|전자등기 사용자등록 조항이 무자격 등기 브로커의 무차별 등기를 가능하게 한다고 한 부분
5|②|02|X|전자등기 사용자등록 조항은 법무사의 직업선택의 자유를 침해할 가능성이 있다고 보기 어렵다.|전자등기 사용자등록 조항이 법무사의 직업선택의 자유를 침해한다고 한 부분
5|③|01|X|비법무사의 등기신청대행 등 법무행위 업 수행을 금지·처벌하는 법무사법 조항은 직업선택의 자유를 침해하지 않는다.|비법무사의 등기신청대행 금지·처벌이 직업선택의 자유를 과도하게 제한한다고 한 부분
5|④|01|X|고소고발장 작성사무를 법무사 업무 관련 서류로 규정한 것은 일반행정사의 직업선택의 자유를 침해하지 않는다.|고소고발장 작성사무의 법무사 업무 규정이 일반행정사의 직업선택의 자유를 침해한다고 한 부분
5|⑤|01|O|일정 경력을 가진 공무원에게 법무사시험 없이 법무사자격을 부여하는 제도는 합리성을 가질 수 있다.|
5|⑤|02|O|경력공무원 법무사자격 부여제도는 일반인이 법무사시험 합격으로 법무사가 될 수 있는 길을 열어 두면 직업선택의 자유를 침해하지 않는다고 볼 수 있다.|
6|①|01|X|공무원이 선거에서 특정 정당 또는 특정인을 지지하기 위하여 정당가입을 권유하는 행위를 형사처벌하는 조항은 정치적 표현의 자유를 침해하지 않는다.|공무원의 선거 관련 정당가입 권유운동 처벌조항이 정치적 표현의 자유를 침해한다고 한 부분
6|②|01|O|당원이 아닌 자에게도 투표권을 부여하는 당내경선에서 시설관리공단 상근직원의 경선운동을 금지하는 조항은 정치적 표현의 자유를 침해한다.|
6|③|01|O|당내경선의 경선운동은 원칙적으로 공직선거에서의 당선 또는 낙선을 위한 선거운동에 해당하지 않는다.|
6|③|02|O|경선운동 금지조항이 과잉금지원칙에 반하는지 판단할 때에는 엄격한 심사기준이 적용되어야 한다.|
6|④|01|O|공무원이라는 지위만으로 정치적 표현의 자유를 전면적으로 부정할 수는 없다.|
6|④|02|O|공무원의 정치적 표현의 자유도 과잉금지원칙에 따라 제한될 수 있다.|
6|⑤|01|O|군무원이 연설·문서 등으로 정치적 의견을 공표하는 행위를 처벌하는 조항은 군무원의 정치적 표현의 자유를 침해하지 않는다고 볼 수 있다.|
7|①|01|O|진정소급입법은 신법이 이미 종료된 사실관계나 법률관계에 적용되는 경우를 말한다.|
7|①|02|O|진정소급입법은 원칙적으로 허용되지 않고 특단의 사정이 있는 경우에만 예외적으로 허용된다.|
7|①|03|O|부진정소급입법은 현재 진행 중인 사실관계나 법률관계에 적용되는 경우를 말하며 원칙적으로 허용된다.|
7|②|01|O|피적용자에게 유리한 시혜적 소급입법을 할 것인지 여부는 원칙적으로 입법자의 판단에 맡겨져 있다.|
7|③|01|X|공소시효에 관한 규정은 원칙적으로 형벌불소급원칙의 효력범위에 포함되지 않는다.|공소시효제도에는 원칙적으로 형벌불소급원칙이 적용된다고 한 부분
7|④|01|O|형벌불소급원칙에서 말하는 처벌은 형식적 의미의 형벌 유형에 국한되지 않는다.|
7|④|02|O|제재의 실제 효과가 형벌적 성격이 강하여 신체의 자유를 박탈하거나 이에 준하면 형벌불소급원칙이 적용될 수 있다.|
7|⑤|01|O|위치추적 전자장치 부착명령은 형벌과 구별되는 비형벌적 보안처분으로서 소급효금지원칙이 적용되지 않는다.|
8|①|01|X|재건축사업에서 관리처분계획인가 고시 후 별도 영업손실보상 없이 임차권자의 사용·수익을 중지시키는 조항은 임차권자의 재산권을 침해하지 않는다.|별도 영업손실보상 없이 재건축사업구역 내 임차권자의 사용·수익을 중지시키는 것이 재산권을 침해한다고 한 부분
8|②|01|O|지방의회의원 보수가 기존 퇴직연금에 미치지 못하는데도 연금 전액 지급을 정지하는 규정은 퇴직연금수급권자의 재산권을 침해한다.|
8|③|01|O|정당 공천심사 탈락으로 후보자등록을 하지 못한 예비후보자에게 기탁금 반환을 허용하지 않는 것은 예비후보자의 재산권을 침해한다.|
8|④|01|O|영리획득의 단순한 기회나 기업활동의 사실적·법적 여건은 헌법상 재산권 보장의 대상이 되지 않는다.|
8|④|02|O|시설이전명령으로 화약류저장소 영업을 하지 못하여 상실되는 영리획득 기회는 헌법상 재산권으로 보기 어렵다.|
8|⑤|01|O|공무원연금법상 각종 급여는 사회보장적 급여의 성격과 공로보상 또는 후불임금의 성격을 함께 가진다.|
8|⑤|02|O|공무원연금법상 퇴직연금수급권은 경제적 가치 있는 권리로서 헌법상 재산권의 성격을 가진다.|
9|㉠|01|O|국가를 상대로 하는 당사자소송에서 가집행선고를 제한하는 행정소송법 조항은 평등원칙에 반한다.|
9|㉡|01|X|국세징수법상 공매절차의 계약보증금을 국고에 귀속시키는 조항은 민사집행법상 경매절차와 합리적 이유 없이 달리 취급하여 평등원칙에 위반된다.|국세징수절차와 민사집행절차의 성질이 달라 계약보증금 국고귀속 차별이 합리적이라고 한 부분
9|㉢|01|O|집행유예 소년범에게 실형 종료·면제 소년범과 같은 자격제한 특례를 두지 않은 구 소년법 조항은 평등원칙에 위반된다.|
9|㉣|01|X|고소인·고발인만 검찰청법상 항고권자로 규정한 조항은 기소유예처분을 받은 피의자의 평등권을 침해하지 않는다.|고소인·고발인만 검찰청법상 항고권자로 둔 조항이 기소유예처분 피의자의 평등권을 침해한다고 한 부분
9|㉤|01|O|친고죄에서 고소취소 가능시기를 제1심 판결선고 전까지로 제한한 형사소송법 조항은 항소심 단계 고소취소자를 자의적으로 차별하지 않는다.|
10|①|01|O|국무회의 심의를 거쳐야 하는 중요한 정책인지에 관하여 대통령이나 국무위원에게 일정한 판단재량이 인정된다.|
10|①|02|O|국무회의 심의대상에 관한 대통령이나 국무위원의 일차적 판단은 명백히 비합리적이거나 자의적이지 않으면 존중된다.|
10|②|01|O|국무회의는 행정부 내 최고의 정책 심의기관이지만 의결기관은 아니다.|
10|②|02|O|국무회의의 의결은 대통령에 대하여 법적 구속력을 갖지 않는다.|
10|③|01|X|국무총리 또는 국무위원 해임건의는 국회재적의원 3분의 1 이상의 발의와 국회재적의원 과반수의 찬성이 필요하다.|국무위원 해임건의에 국회재적의원 과반수 발의와 재적의원 3분의 2 이상 찬성이 필요하다고 한 부분
10|④|01|O|대통령의 직무상 해외순방 중 국무총리가 주재한 국무회의에서 정당해산심판청구서 제출안을 의결한 것은 위법하지 않다.|
10|⑤|01|O|국무회의는 대통령·국무총리와 15인 이상 30인 이하의 국무위원으로 구성한다.|
11|①|01|O|대통령은 헌법 제65조에 명시된 탄핵소추 대상이다.|
11|②|01|O|법관은 헌법 제65조에 명시된 탄핵소추 대상이다.|
11|③|01|O|국무위원은 헌법 제65조에 명시된 탄핵소추 대상이다.|
11|④|01|O|헌법재판소 재판관은 헌법 제65조에 명시된 탄핵소추 대상이다.|
11|⑤|01|X|검사는 헌법 제65조에 명시적으로 열거된 탄핵소추 대상이 아니다.|검사가 헌법에 명시된 탄핵소추 대상이라고 전제한 부분
11|⑤|02|X|검사의 탄핵 가능성은 검찰청법상 신분보장 규정에서 확인된다.|검사가 헌법에 명시된 탄핵소추 대상이라고 전제한 부분
12|①|01|X|헌법상 국회의원과 정부는 법률안을 제출할 수 있다.|국회의원만 법률안을 제출할 수 있다고 한 부분
12|②|01|X|국회의원의 법률안 심의·표결권은 헌법기관인 국회의원 각자에게 보장되는 권한이다.|법률안 심의·표결권이 국회의원 각자가 아니라 국회에만 부여된다고 한 부분
12|③|01|X|대통령의 재의요구 후 법률안 재의결에는 재적의원 과반수의 출석과 출석의원 3분의 2 이상의 찬성이 필요하다.|대통령 재의요구 후 재의결에 재적의원 3분의 2 이상의 출석이 필요하다고 한 부분
12|④|01|X|국회에 제출된 법률안은 회기 중 의결되지 못한 이유만으로 폐기되지 않는다.|국회에 제출된 법률안은 회기 중 의결되지 못하면 원칙적으로 폐기된다고 한 부분
12|④|02|X|국회에 제출된 법률안은 국회의원의 임기가 만료된 때에는 폐기된다.|회기 중 미의결 법률안의 계속심사 원칙과 임기만료 예외를 잘못 설명한 부분
12|⑤|01|O|현행법상 국회의원은 국회의 조약 체결·비준 동의권 침해를 주장하며 대통령을 상대로 권한쟁의심판을 청구할 수 없다.|
13|①|01|O|헌법은 대한민국 국민이 되는 요건을 법률로 정하도록 위임한다.|
13|②|01|O|대한민국헌법의 영토조항상 북한지역도 대한민국의 영토에 포함된다.|
13|②|02|O|북한주민은 일반적으로 대한민국 국민에 포함된다.|
13|③|01|O|우리 국적법은 1998년 개정 전 부계혈통주의를 채택한 적이 있다.|
13|③|02|O|1998년 국적법 개정으로 우리 국적법은 부모양계혈통주의로 전환되었다.|
13|④|01|X|대한민국 국민과 혼인한 외국인은 자동으로 대한민국 국적을 취득하지 않고 귀화허가를 받아야 한다.|외국인이 대한민국 국민과 혼인하면 자동으로 대한민국 국적을 취득한다고 한 부분
13|⑤|01|O|대한민국 국민이었던 외국인은 법무부장관의 국적회복허가를 받아 대한민국 국적을 취득할 수 있다.|
13|⑤|02|O|병역을 기피할 목적으로 대한민국 국적을 상실하거나 이탈한 사람은 국적회복허가 대상에서 제외된다.|
14|①|01|O|감사원은 대통령에 소속하되 직무에 관하여 독립의 지위를 가진다.|
14|②|01|X|감사위원은 감사원장의 제청으로 국회의 동의 없이 대통령이 임명한다.|감사위원 임명에 국회의 동의가 필요하다고 한 부분
14|③|01|O|감사원의 직무감찰 대상 공무원에는 국회·법원 및 헌법재판소 소속 공무원이 제외된다.|
14|④|01|O|감사원은 징계사유가 있는 공무원에 대하여 소속 장관 또는 임용권자에게 징계를 요구할 수 있다.|
14|④|02|O|감사원은 직무감찰 결과 비위사실이 밝혀지더라도 해당 공무원을 직접 징계할 수는 없다.|
14|⑤|01|O|감사원은 지방자치단체의 자치사무에 대하여 합법성 감사뿐만 아니라 합목적성 감사도 할 수 있다.|
15|①|01|O|헌법개정은 국회재적의원 과반수 또는 대통령의 발의로 제안된다.|
15|②|01|O|제안된 헌법개정안은 대통령이 20일 이상의 기간 공고하여야 한다.|
15|②|02|O|국회는 헌법개정안이 공고된 날부터 60일 이내에 의결하여야 한다.|
15|③|01|X|헌법개정안은 국회 의결만으로 확정되지 않고 국민투표를 거쳐야 확정된다.|헌법개정안이 국회 재적의원 3분의 2 이상 찬성만으로 확정된다고 한 부분
15|③|02|X|헌법개정안은 국회 의결 후 30일 이내 국민투표에서 국회의원선거권자 과반수 투표와 투표자 과반수 찬성을 얻어야 확정된다.|헌법개정안이 국회 의결 즉시 확정되어 공포된다고 한 부분
15|④|01|O|대통령의 임기연장 또는 중임변경을 위한 헌법개정은 그 제안 당시 대통령에게 효력이 없다.|
15|⑤|01|O|대통령이 발의하는 헌법개정안은 국무회의 심의를 거쳐야 한다.|
16|①|01|X|직업공무원제도는 헌법상 제도적 보장이므로 최소한 보장의 원칙이 적용된다.|직업공무원제도에 최대한 보장의 원칙이 적용된다고 한 부분
16|①|02|X|입법자는 직업공무원제도에 관하여 최소한 보장의 원칙 안에서 폭넓은 입법형성의 자유를 가진다.|직업공무원제도에 최대한 보장의 원칙이 적용된다고 한 부분
16|②|01|X|공무원이 금고 이상의 형의 선고유예를 받은 경우 범죄의 유형과 내용에 관계없이 당연퇴직하도록 하는 것은 공무담임권을 침해한다.|금고 이상의 형의 선고유예를 받은 공무원의 당연퇴직이 헌법에 위배되지 않는다고 한 부분
16|③|01|O|헌법 제7조 제1항의 국민전체에 대한 봉사자로서 국민에 대하여 책임을 지는 공무원은 넓은 의미의 공무원을 말한다.|
16|③|02|O|헌법 제7조 제2항의 신분과 정치적 중립성이 보장되는 공무원은 직업으로 공무를 담당하는 협의의 공무원을 말한다.|
16|④|01|X|사실상 노무에 종사하는 공무원은 법률이 정하는 바에 따라 단체행동권을 가질 수 있다.|모든 공무원이 단체행동권을 가질 수 없다고 한 부분
16|⑤|01|X|공무원의 품위손상행위를 징계사유로 규정한 국가공무원법 조항은 명확성원칙에 위배되지 않는다.|공무원 품위유지의무 및 품위손상 징계사유가 명확성원칙에 위배된다고 한 부분
17|①|01|O|법 규정이 직업의 자유를 직접 규율하지 않더라도 간접적으로 직업의 행사를 저해하거나 불가능하게 하면 직업의 자유 제한이 인정될 수 있다.|
17|②|01|X|어린이통학버스 운영 시 보호자를 반드시 동승하게 하는 조항은 학원 등의 영업방식을 제한하여 직업수행의 자유를 제한한다.|어린이통학버스 보호자동승 조항이 비용지출만 유발하고 직업수행의 자유를 제한하지 않는다고 한 부분
17|②|02|X|어린이통학버스 보호자동승 조항은 과잉금지원칙에 반하여 직업수행의 자유를 침해한다고 볼 수 없다.|어린이통학버스 보호자동승 조항이 직업수행의 자유 제한조차 아니라고 한 부분
17|③|01|O|헌법 제15조의 직업의 자유에는 기업의 설립과 경영의 자유를 뜻하는 기업의 자유가 포함된다.|
17|④|01|O|최저임금 비교대상임금을 시간급으로 환산할 때 소정근로시간과 법정 주휴시간을 합산하게 하는 규정은 사용자의 직업의 자유를 제한한다.|
17|④|02|O|최저임금 비교대상임금 환산규정은 사용자의 계약의 자유도 제한한다.|
17|⑤|01|O|외국인근로자의 사업장 변경 사유를 제한하는 규정은 직업선택의 자유 중 직장선택의 자유를 제한한다.|
18|①|01|O|현행 헌법 전문은 헌법을 국회의 의결을 거쳐 국민투표에 의하여 개정한다고 밝히고 있다.|
18|②|01|O|헌법 전문과 헌법 제9조의 전통은 역사성과 시대성을 띤 개념으로서 오늘날의 의미로 포착하여야 한다.|
18|②|02|O|가족제도에 관한 전통은 개인의 존엄과 양성평등에 반하지 않아야 한다.|
18|③|01|O|3·1정신은 우리나라 헌법의 연혁적·이념적 기초로서 헌법이나 법률해석의 기준으로 작용할 수 있다.|
18|③|02|O|3·1정신에 기초하여 곧바로 국민의 개별적 기본권성을 도출할 수는 없다.|
18|④|01|O|헌법 전문의 대한민국임시정부 법통 계승 선언으로부터 독립유공자와 그 유족에 대한 예우를 하여야 할 헌법적 의무가 도출될 수 있다.|
18|⑤|01|X|4·19혁명공로자에 대한 보훈 수준을 애국지사와 동일하게 설정하여야 하는 것은 아니다.|4·19민주이념이 헌법 전문에 함께 규정되어 있으므로 4·19혁명공로자의 보훈 수준을 애국지사와 동일하게 해야 한다고 한 부분
19|㉠|01|O|정당의 목적이나 활동 중 어느 하나라도 민주적 기본질서에 위배되면 정당해산의 사유가 될 수 있다.|
19|㉡|01|O|정당해산심판제도는 1960년 6월 15일 제3차 헌법 개정을 통해 우리 헌법에 도입되었다.|
19|㉢|01|O|헌법 제8조 제4항의 민주적 기본질서는 최대한 엄격하고 협소한 의미로 이해하여야 한다.|
19|㉣|01|O|정당이 당원이나 후원자로부터 정치자금을 모금하는 것은 정당활동의 자유의 내용에 포함된다.|
19|㉤|01|O|헌법 제8조 제1항 전단의 정당설립의 자유에는 정당존속의 자유가 포함된다.|
19|㉤|02|O|헌법 제8조 제1항 전단의 정당설립의 자유에는 정당활동의 자유가 포함된다.|
20|①|01|O|헌법상 형사보상청구권은 구금되었던 형사피고인에게 인정된다.|
20|①|02|O|헌법상 형사보상청구권은 구금되었던 형사피의자에게도 인정된다.|
20|②|01|X|형사보상청구권의 구체적 내용과 절차를 정하는 입법은 완화된 의미의 비례원칙을 준수하여야 한다.|형사보상청구권의 구체적 내용과 절차에 관한 위헌심사 기준이 자의금지원칙이라고 한 부분
20|②|02|X|형사보상청구권은 헌법상 정당한 보상을 명문으로 보장하므로 법률로 제한되어도 본질적 내용이 침해되어서는 안 된다.|형사보상청구권의 구체적 내용과 절차에 관한 위헌심사 기준이 자의금지원칙이라고 한 부분
20|③|01|O|헌법 제28조의 형사보상청구권에서 말하는 정당한 보상은 헌법 제23조 제3항의 재산권 침해에 대한 정당한 보상과 차이가 있다.|
20|④|01|O|형사피고인으로서 구금되었던 자의 형사보상청구는 무죄재판을 한 법원이 관할한다.|
20|⑤|01|O|형사피고인으로서 구금되었던 자의 형사보상청구는 무죄재판 확정 사실을 안 날부터 3년 이내에 하여야 한다.|
20|⑤|02|O|형사피고인으로서 구금되었던 자의 형사보상청구는 무죄재판이 확정된 때부터 5년 이내에 하여야 한다.|
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def ensure_raw_text() -> str:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(f"missing local problem PDF: {SOURCE_PDF}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    if not RAW_PDF_PATH.exists():
        shutil.copy2(SOURCE_PDF, RAW_PDF_PATH)
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(RAW_PDF_PATH)).pages)
    RAW_TEXT_PATH.write_text(text, encoding="utf-8")
    return text


def extract_question_blocks(text: str) -> dict[int, str]:
    start = text.find("【헌 법 20문】")
    if start == -1:
        raise ValueError("cannot locate 2022 constitution section")
    section = text[start:]
    matches = list(re.finditer(r"【문\s*(\d+)】", section))
    if len(matches) < QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} constitution questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches[:QUESTION_COUNT]):
        no = int(match.group(1))
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        blocks[no] = section[match.start() : end_pos]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in re.finditer(r"[①②③④⑤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(CHOICE_LABELS):
            break
    if set(first_by_label) != set(CHOICE_LABELS):
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in CHOICE_LABELS]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = block[start:end]
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in re.finditer(r"[㉠㉡㉢㉣㉤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(BOX_LABELS):
            break
    if set(first_by_label) != set(BOX_LABELS):
        raise ValueError("cannot split five box statements")
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label["㉤"].end() :])
    choice_start = first_by_label["㉤"].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in BOX_LABELS]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(0)] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = BOX_LABELS if QUESTION_TYPES[no] in {"combination-false", "count-false"} else CHOICE_LABELS
        split = split_box_units(blocks[no]) if labels == BOX_LABELS else split_choice_units(blocks[no])
        for label in labels:
            raw[(no, label)] = split[label]
    return raw


def source_verdict(no: int, label: str) -> str:
    return "X" if label in FALSE_LABELS[no] else "O"


def load_atom_rows() -> dict[tuple[int, str], list[dict[str, str | None]]]:
    rows: dict[tuple[int, str], list[dict[str, str | None]]] = {}
    for line in ATOM_ROWS.splitlines():
        no_text, label, atom_index, verdict, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        if verdict not in {"O", "X"}:
            raise ValueError(f"bad atom verdict: {line}")
        if verdict == "X" and not trap:
            raise ValueError(f"X atom without trap: {line}")
        if verdict == "O" and trap:
            raise ValueError(f"O atom with trap: {line}")
        rows.setdefault((int(no_text), label), []).append(
            {
                "atomIndex": atom_index.strip(),
                "sourceVerdict": verdict,
                "rep": rep.strip(),
                "trap": trap,
            }
        )
    return rows


def complete_sentence(rep: str) -> str:
    rep = rep.strip()
    return rep if rep.endswith(".") else rep.rstrip(".") + "."


def question_source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def unit_source_label(no: int, label: str) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {label} 기출"


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in range(1, QUESTION_COUNT + 1):
        qid = f"2022-g1-constitution-{no:02d}"
        labels = BOX_LABELS if QUESTION_TYPES[no] in {"combination-false", "count-false"} else CHOICE_LABELS
        units = []
        for label in labels:
            units.append(
                {
                    "unitId": f"{qid}-{LABEL_CODE[label]}",
                    "unitType": "boxStatement" if label in BOX_LABELS else "choice",
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
                "groupLabel": "제1과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": question_source_label(no),
                "type": QUESTION_TYPES[no],
                "officialAnswer": OFFICIAL_ANSWERS[no],
                "units": units,
            }
        )
    return {
        "schema": "legal-scrivener/problem-original-current-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
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
                    "source": unit_source_label(q["no"], unit["label"]),
                    "examId": EXAM_ID,
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
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
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "source": str(SOURCE_PATH),
        "itemCount": len(items),
        "items": items,
    }


def build_completed(queue: dict[str, object]) -> dict[str, object]:
    atom_rows = load_atom_rows()
    items = []
    for item in queue["items"]:
        key = (item["no"], item["unitLabel"])
        if key not in atom_rows:
            raise ValueError(f"missing atom rows: {key}")
        basis_type, basis_ref, why = BASIS[item["no"]]
        for row in atom_rows[key]:
            rep = complete_sentence(str(row["rep"]))
            trap = row["trap"]
            source_is_x = row["sourceVerdict"] == "X"
            items.append(
                {
                    "atomId": f"bupmusa-2022-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}",
                    "sourceUnitId": item["unitId"],
                    "sourceAtomIndex": row["atomIndex"],
                    "sourceFamily": "법무사시험",
                    "source": item["source"],
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "no": item["no"],
                    "unitType": item["unitType"],
                    "unitLabel": item["unitLabel"],
                    "sourceQuestionType": item["sourceQuestionType"],
                    "officialQuestionAnswer": item["officialQuestionAnswer"],
                    "sourceUnitVerdict": item["originalVerdict"],
                    "sourceVerdict": row["sourceVerdict"],
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
            )
    return {
        "schema": "legal-scrivener/completed-atoms-by-subject/v2",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "atomPrinciple": "docs/atom_원칙_v001.md",
        "source": str(SOURCE_PATH),
        "sourceQueue": str(QUEUE_PATH),
        "sourceCount": len(queue["items"]),
        "questionCount": QUESTION_COUNT,
        "atomCount": len(items),
        "verificationSources": LEGAL_SOURCES,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "atomSplit": "원문 보기 하나가 여러 조문·판례·학설 판단 지점을 포함하면 여러 atom으로 분해한다.",
            "xHandling": "원문상 틀린 판단 지점은 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형·개수형 문제는 선택지 조합이 아니라 박스 문장별 근거명제로 atom화한다.",
        },
        "items": items,
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text)
    cleaned = cleaned.replace("·", "ㆍ").replace("∙", "ㆍ")
    return cleaned.lower()


def year_to_exam_date(year: int) -> float:
    return year + 8.0 / 12.0


def weight_for_sources(sources: list[dict[str, object]], today_year: float = 2026.46, half_life: float = 4.0) -> float:
    total = 0.0
    for src in sources:
        year = int(src.get("year", YEAR))
        source_weight = float(src.get("s", 1.0))
        age = max(0.0, today_year - year_to_exam_date(year))
        total += source_weight * (0.5 ** (age / half_life))
    return round(math.log1p(total), 4)


def grade_items(items: list[dict[str, object]]) -> None:
    sorted_items = sorted(items, key=lambda item: (-float(item["weight"]), str(item["rep"])))
    cuts = [(0.04, "S"), (0.11, "A+"), (0.23, "A"), (0.40, "B+"), (0.60, "B"), (0.77, "C+"), (0.89, "C"), (0.96, "D+"), (1.00, "D")]
    n = len(sorted_items)
    for rank, item in enumerate(sorted_items, start=1):
        p = rank / n
        item["grade"] = next(grade for cut, grade in cuts if p <= cut)
        item["rank"] = rank


def integrated_source_label(atom: dict[str, object]) -> str:
    return f"{atom['year']} 법무사 {atom['round']}회 헌법 {atom['no']}번 {atom['unitLabel']}"


def new_integrated_item(atom: dict[str, object], source: dict[str, object]) -> dict[str, object]:
    return {
        "primary": "법무사시험",
        "sourceFamilies": ["법무사시험"],
        "subject": SUBJECT_NAME,
        "topic": TOPICS.get(int(atom["no"]), SUBJECT_NAME),
        "rep": atom["rep"],
        "a": atom["a"],
        "why": atom["why"],
        "basisType": atom["basisType"],
        "basisRef": atom["basisRef"],
        "sources": [source],
        "refs": [source["source"]],
        "sourceIds": [atom["atomId"]],
        "sourceAtomCount": 1,
        "quality": {"statementType": "declarative", "displayable": True, "normalizers": [], "changed": False},
        "verification": {"status": "needs-legal-review", "lawAsOf": today(), "legalVerifiedAt": None, "statuteCitationStatus": "pending"},
    }


def source_from_atom(atom: dict[str, object]) -> dict[str, object]:
    return {
        "family": "법무사시험",
        "s": 1.0,
        "year": atom["year"],
        "round": atom["round"],
        "subject": SUBJECT_NAME,
        "source": integrated_source_label(atom),
        "sourceId": atom["atomId"],
        "sourceUnitId": atom["sourceUnitId"],
        "sourceVerdict": atom["sourceVerdict"],
        "sourceTrap": atom["sourceTrap"],
        "sourceStatement": atom["sourceStatement"],
    }


def rebuild_integrated(new_atoms: list[dict[str, object]]) -> dict[str, object]:
    existing = load_json(INTEGRATED_PATH) if INTEGRATED_PATH.exists() else None
    buckets: dict[tuple[str, str], dict[str, object]] = {}
    if existing:
        for old_item in existing.get("items", []):
            item = dict(old_item)
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2022-constitution-")]
            if not item["sources"]:
                continue
            item["refs"] = [src["source"] for src in item["sources"]]
            item["sourceIds"] = [src["sourceId"] for src in item["sources"]]
            item["sourceAtomCount"] = len(item["sources"])
            for transient in ["id", "rank", "grade", "weight", "weightedSourceSum", "freq"]:
                item.pop(transient, None)
            buckets[(str(item["a"]), normalize_key(str(item["rep"])))] = item

    for atom in new_atoms:
        key = (str(atom["a"]), normalize_key(str(atom["rep"])))
        source = source_from_atom(atom)
        if key not in buckets:
            buckets[key] = new_integrated_item(atom, source)
        else:
            item = buckets[key]
            if source["sourceId"] not in item["sourceIds"]:
                item["sources"].append(source)
                item["refs"].append(source["source"])
                item["sourceIds"].append(source["sourceId"])
                item["sourceAtomCount"] = int(item["sourceAtomCount"]) + 1

    items = list(buckets.values())
    for index, item in enumerate(items, start=1):
        item["sourceFamilies"] = sorted({src["family"] for src in item["sources"]})
        item["freq"] = len(item["sources"])
        item["weightedSourceSum"] = round(sum(float(src["s"]) * (0.5 ** (max(0.0, 2026.46 - year_to_exam_date(int(src["year"]))) / 4.0)) for src in item["sources"]), 6)
        item["weight"] = weight_for_sources(item["sources"])
        item["id"] = f"bupmusa-constitution-integrated-{index:05d}"
    grade_items(items)
    items.sort(key=lambda item: (int(item["rank"]), str(item["id"])))
    years = sorted({int(src["year"]) for item in items for src in item["sources"]}, reverse=True)
    input_atoms = sum(len(load_json(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").get("items", [])) for year in years if (SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").exists())
    return {
        "title": "법무사_헌법 통합 atom",
        "subject": SUBJECT_NAME,
        "schema": "bupmusa/constitution-integrated-atom/v1",
        "version": "bupmusa_constitution_v004_2022_integrated",
        "builtAt": today(),
        "sourceFiles": {str(year): str(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years},
        "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"},
        "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"},
        "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))},
        "items": items,
    }


def validate_atom_text(items: list[dict[str, object]]) -> None:
    banned_tokens = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "않은 것은"]
    for item in items:
        rep = item["rep"]
        if any(token in rep for token in banned_tokens):
            raise ValueError(f"non-atom wording in rep: {item['atomId']} {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in rep: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or item["xDependsOn"] != rep:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        elif item["sourceTrap"] is not None or item["xDependsOn"] is not None:
            raise ValueError(f"unexpected X metadata: {item['atomId']}")
        if item["currentVerdict"] != "O" or item["a"] != "O":
            raise ValueError(f"completed atom must be O: {item['atomId']}")


def validate(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if source["questionCount"] != QUESTION_COUNT:
        raise ValueError("unexpected question count")
    if queue["itemCount"] != SOURCE_UNIT_COUNT:
        raise ValueError("source unit count mismatch")
    if completed["atomCount"] < MIN_ATOM_COUNT:
        raise ValueError(f"atom count too low for legal-point split: {completed['atomCount']}")
    ids = [item["atomId"] for item in completed["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    source_unit_ids = {item["unitId"] for item in queue["items"]}
    covered_unit_ids = {item["sourceUnitId"] for item in completed["items"]}
    if source_unit_ids != covered_unit_ids:
        missing = sorted(source_unit_ids - covered_unit_ids)
        raise ValueError(f"missing atom coverage for source units: {missing[:5]}")
    false_units = {
        f"2022-g1-constitution-{no:02d}-{LABEL_CODE[label]}"
        for no, labels in FALSE_LABELS.items()
        for label in labels
    }
    false_atom_units = {
        item["sourceUnitId"] for item in completed["items"] if item["sourceVerdict"] == "X"
    }
    if not false_units.issubset(false_atom_units):
        missing = sorted(false_units - false_atom_units)
        raise ValueError(f"false source units without X atom: {missing}")
    true_atom_errors = [
        item["atomId"]
        for item in completed["items"]
        if item["sourceUnitVerdict"] == "O" and item["sourceVerdict"] == "X"
    ]
    if true_atom_errors:
        raise ValueError(f"X atoms under true source units: {true_atom_errors[:5]}")
    validate_atom_text(completed["items"])


def validate_integrated(doc: dict[str, object]) -> None:
    items = doc["items"]
    if not items:
        raise ValueError("empty integrated atom")
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate integrated ids")


def update_index(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    index = load_json(SUBJECT_INDEX_PATH) if SUBJECT_INDEX_PATH.exists() else {
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
        "source": str(SOURCE_PATH),
        "atomQueue": str(QUEUE_PATH),
        "completedAtoms": str(OUT_PATH),
        "questionCount": source["questionCount"],
        "atomQueueItemCount": queue["itemCount"],
        "completedAtomCount": completed["atomCount"],
        "completedAtomsUpdatedAt": completed["updatedAt"],
    }
    write_json(SUBJECT_INDEX_PATH, index)


def main() -> None:
    text = ensure_raw_text()
    blocks = extract_question_blocks(text)
    raws = raw_statement_map(blocks)
    source = build_source(raws)
    queue = build_queue(source)
    completed = build_completed(queue)
    validate(source, queue, completed)
    write_json(SOURCE_PATH, source)
    write_json(QUEUE_PATH, queue)
    write_json(OUT_PATH, completed)
    integrated = rebuild_integrated(completed["items"])
    validate_integrated(integrated)
    write_json(INTEGRATED_PATH, integrated)
    update_index(source, queue, completed)
    counts = Counter(item["sourceVerdict"] for item in completed["items"])
    per_question = Counter(item["no"] for item in completed["items"])
    print(f"wrote {OUT_PATH}")
    print(f"wrote {INTEGRATED_PATH}")
    print(f"sourceUnits={queue['itemCount']} atoms={completed['atomCount']} O={counts['O']} X={counts['X']}")
    print("perQuestion=" + ", ".join(f"{key}:{value}" for key, value in sorted(per_question.items())))
    print(f"integratedItems={integrated['stats']['items']} merged={integrated['stats']['duplicatesMerged']}")


if __name__ == "__main__":
    main()
