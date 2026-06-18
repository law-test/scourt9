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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2017" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2017_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2017"
TEXT_DIR = PRIVATE_ROOT / "text" / "2017"
RAW_PDF_PATH = RAW_DIR / "2017_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2017_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2017_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2017_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2017_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2017_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2017_bupmusa_1st"
YEAR = 2017
ROUND = 23
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 103
MIN_ATOM_COUNT = 120
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ"]
LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
    "ㄱ": "01",
    "ㄴ": "02",
    "ㄷ": "03",
    "ㄹ": "04",
    "ㅁ": "05",
    "ㅂ": "06",
    "ㅅ": "07",
    "ㅇ": "08",
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "형사보상 및 명예회복에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사보상및명예회복에관한법률"},
    {"title": "2017 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2017"},
    {"title": "2017 법무사 헌법 해설", "publisher": "법무사 해설", "url": "local:2017_법무사_헌법_해설_법무사.pdf"},
    {"title": "2017 법무사 헌법 해설", "publisher": "윤우혁 헌법", "url": "local:2017_법무사_헌법_해설_법무사_윤우혁.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "④",
    2: "④",
    3: "③",
    4: "⑤",
    5: "②",
    6: "④",
    7: "④",
    8: "②",
    9: "②",
    10: "⑤",
    11: "⑤",
    12: "①·⑤",
    13: "③",
    14: "⑤",
    15: "⑤",
    16: "⑤",
    17: "④",
    18: "⑤",
    19: "①",
    20: "⑤",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    5: "count-false",
    8: "single-best-true",
    9: "single-best-true",
    12: "multi-correct-true",
})

FALSE_LABELS = {
    1: {"④"},
    2: {"④"},
    3: {"③"},
    4: {"⑤"},
    5: {"ㄷ"},
    6: {"④"},
    7: {"④"},
    8: {"①", "③", "④", "⑤"},
    9: {"①", "③", "④", "⑤"},
    10: {"⑤"},
    11: {"⑤"},
    12: {"②", "③", "④"},
    13: {"③"},
    14: {"⑤"},
    15: {"⑤"},
    16: {"⑤"},
    17: {"④"},
    18: {"⑤"},
    19: {"①"},
    20: {"⑤"},
}

TOPICS = {
    1: "위헌법률심판의 재판 전제성",
    2: "경찰 차벽과 헌법소원",
    3: "재판청구권",
    4: "헌법의 기본원리",
    5: "국무회의 심의사항",
    6: "국회의원 특권",
    7: "법률안 거부권",
    8: "법원 조직",
    9: "조약",
    10: "저항권",
    11: "죄형법정주의",
    12: "선거권",
    13: "태아와 배아의 생명 보호",
    14: "근로의 권리",
    15: "국적과 영토조항",
    16: "형사보상청구권",
    17: "법치국가원리",
    18: "기본권 경합과 충돌",
    19: "평등원칙과 평등권",
    20: "자기결정권",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    5: ("헌법", "헌법 제89조 및 제73조", "국무회의 심의사항과 대통령의 외교권한을 구별하는 조문 지점이다."),
    6: ("헌법+국회법+대법원 판례", "헌법 제44조·제45조·제49조 및 국회법 제109조", "국회의원의 면책특권, 불체포특권과 체포동의 정족수를 구별하는 지점이다."),
    7: ("헌법", "헌법 제53조", "법률안 공포, 재의요구, 확정과 국회의장 공포기한에 관한 조문 지점이다."),
    8: ("헌법+법원조직법", "헌법 제107조 및 법원조직법 제4조·제7조·제16조", "대법관 수, 행정법원 심판권, 명령·규칙 심사, 대법관회의 정족수에 관한 지점이다."),
    11: ("헌법+헌법재판소 결정례", "헌법 제12조 제1항 및 죄형법정주의 관련 결정례", "명확성원칙, 형벌법규 위임과 단체협약 위반 처벌조항의 한계를 구별하는 지점이다."),
    16: ("헌법+형사보상 및 명예회복에 관한 법률", "헌법 제28조 및 형사보상법 제3조·제8조·제27조", "형사보상과 손해배상, 대상자, 청구기간, 상속인의 청구권에 관한 조문 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|위헌법률심판에서 재판의 전제성은 구체적 사건이 법원에 계속 중일 것을 요구한다.|
1|①|02|O|위헌 여부가 문제되는 법률은 당해 소송사건의 재판에 적용되는 것이어야 한다.|
1|①|03|O|법률의 위헌 여부에 따라 당해 사건 담당 법원이 다른 내용의 재판을 하게 되면 재판의 전제성이 인정된다.|
1|②|01|O|재판의 전제성에서 다른 내용의 재판에는 문제 법률의 위헌 여부가 재판의 결론이나 주문에 영향을 주는 경우가 포함된다.|
1|②|02|O|재판의 전제성에서 다른 내용의 재판에는 주문에 영향이 없더라도 재판의 내용과 효력에 관한 법률적 의미가 달라지는 경우도 포함된다.|
1|③|01|O|당해 사건에는 구법 조항이 적용되는데 동일한 내용의 신법 조항을 제청한 경우 신법 조항은 원칙적으로 재판의 전제성이 없다.|
1|④|01|X|공소가 제기되지 않은 사실에 적용되는 법률조항의 위헌 여부는 특별한 사정이 없는 한 당해 형사사건의 재판 전제가 될 수 없다.|공소가 제기되지 않은 사실에 관한 법률조항도 당해 형사사건의 재판 전제가 될 수 있다고 한 부분
1|④|02|X|직접 적용되지 않는 법률조항도 당해 사건 적용 법률조항과 내적 관련이 있으면 예외적으로 재판의 전제성이 인정될 수 있다.|공소 미제기 법률조항의 재판 전제성을 일반적으로 인정한 부분
1|⑤|01|O|헌법재판소는 재판의 전제성 요건에 관하여 되도록 제청법원의 법률적 견해를 존중하여야 한다.|
1|⑤|02|O|재판의 전제성에 관한 제청법원의 법률적 견해가 명백히 유지될 수 없으면 헌법재판소는 제청을 부적법 각하할 수 있다.|
2|①|01|O|경찰의 차벽 설치로 서울광장 통행이 제지되면 통행하려는 사람의 기본권 침해 가능성이 인정될 수 있다.|
2|②|01|O|경찰의 차벽 설치행위는 권력적 사실행위로서 행정소송의 대상이 될 수 있다.|
2|②|02|O|차벽 설치행위가 이미 종료되고 통행이 재개되어 행정소송의 소의 이익이 부정될 가능성이 높으면 헌법소원에서 보충성 예외가 인정될 수 있다.|
2|③|01|O|헌법소원은 주관적 권리구제뿐만 아니라 객관적 헌법질서 보장기능도 가진다.|
2|③|02|O|종료된 차벽 설치행위라도 반복 가능성이 있으면 헌법소원에서 권리보호이익이 인정될 수 있다.|
2|④|01|X|서울광장 통행제지행위로 제한되는 기본권은 거주·이전의 자유가 아니라 일반적 행동자유권이다.|서울광장 차벽 설치로 침해되는 기본권을 거주·이전의 자유라고 한 부분
2|④|02|X|서울광장 출입과 통행은 그 장소를 중심으로 생활을 형성하는 행위라고 보기 어려워 거주·이전의 자유 보호영역에 해당하지 않는다.|서울광장 통행을 거주·이전의 자유 보호영역으로 본 부분
2|⑤|01|O|경찰이 차벽으로 서울광장 통행을 제지한 행위는 과잉금지원칙에 위반되어 일반적 행동자유권을 침해할 수 있다.|
3|①|01|O|법관에 의한 재판을 받을 권리는 법관이 사실을 확정하고 법률을 해석·적용하는 재판을 받을 권리를 뜻한다.|
3|①|02|O|법관의 사실확정과 법률 해석·적용 기회에 접근하기 어렵게 하는 제약이나 장벽은 허용되지 않는다.|
3|②|01|O|헌법 제27조의 재판청구권에 모든 사건에 대한 상소심 절차의 재판을 받을 권리가 당연히 포함된다고 단정할 수 없다.|
3|③|01|X|현역병이 군 입대 전에 범한 범죄에 대한 군사법원의 재판권 규정은 현역병의 재판청구권을 침해한다고 볼 수 없다.|군 입대 전 범죄에 관한 군사법원 재판권이 위헌이라고 한 부분
3|④|01|O|검사의 기소유예처분에 대하여 피의자가 불복하여 법원의 재판을 받을 절차를 법률로 마련해야 할 헌법적 의무는 존재하지 않는다.|
3|⑤|01|O|재심사유의 범위를 어떻게 정할지는 법적 안정성, 재판의 신속·적정성, 법원의 업무부담 등을 고려한 입법정책의 문제이다.|
4|①|01|O|자유민주적 기본질서에는 기본적 인권 존중, 권력분립, 의회제도, 복수정당제도, 선거제도와 사법권 독립이 포함된다.|
4|①|02|O|자유민주적 기본질서에는 사유재산과 시장경제를 골간으로 한 경제질서가 포함된다.|
4|②|01|O|우리 헌법상 경제질서는 사유재산제와 자유경쟁을 존중하는 자유시장경제질서를 기본으로 한다.|
4|②|02|O|우리 헌법상 경제질서는 사회복지와 사회정의를 실현하기 위한 국가적 규제와 조정을 용인하는 사회적 시장경제질서의 성격도 가진다.|
4|③|01|O|문화국가원리상 국가의 문화육성 대상에는 엘리트문화뿐 아니라 서민문화와 대중문화도 포함되어야 한다.|
4|④|01|O|자기책임의 원리는 인간의 자유와 유책성 및 인간의 존엄성을 반영한 원리이다.|
4|④|02|O|자기책임의 원리는 민사법이나 형사법에 한정되지 않고 법치주의에 내재하는 원리이다.|
4|⑤|01|X|헌법의 기본원리는 구체적 기본권을 직접 도출하는 근거가 될 수는 없다.|헌법의 기본원리에서 구체적 기본권을 도출할 수 있다고 한 부분
4|⑤|02|X|헌법의 기본원리는 기본권 해석과 기본권제한입법의 합헌성 심사에서 해석기준으로 작용한다.|헌법의 기본원리를 구체적 기본권 도출근거로 본 부분
5|ㄱ|01|O|정부에 제출 또는 회부된 정부 정책에 관계되는 청원의 심사는 국무회의 심의사항이다.|
5|ㄴ|01|O|각군참모총장의 임명은 국무회의 심의사항이다.|
5|ㄴ|02|O|국립대학교 총장의 임명은 국무회의 심의사항이다.|
5|ㄷ|01|O|조약안은 국무회의 심의사항이다.|
5|ㄷ|02|X|외교사절의 신임·접수는 대통령 권한이지만 헌법상 국무회의 심의사항으로 열거되어 있지 않다.|외교사절의 신임·접수를 국무회의 심의사항으로 본 부분
5|ㄹ|01|O|사면·감형과 복권은 국무회의 심의사항이다.|
5|ㅁ|01|O|군사에 관한 중요사항은 국무회의 심의사항이다.|
5|ㅂ|01|O|국회의 임시회 집회의 요구는 국무회의 심의사항이다.|
5|ㅅ|01|O|행정각부 간 권한의 획정은 국무회의 심의사항이다.|
5|ㅇ|01|O|정당해산의 제소는 국무회의 심의사항이다.|
6|①|01|O|국회의원은 국회에서 직무상 행한 발언과 표결에 관하여 국회 외에서 책임을 지지 않는다.|
6|①|02|O|국회의원 면책특권은 국회의원이 국회 안에서 자유롭게 발언·표결하도록 보장하여 국회의 기능 수행을 보장하려는 제도이다.|
6|②|01|O|국회의원 면책특권의 대상은 국회 안에서의 직무상 발언과 표결 자체에 한정되지 않는다.|
6|②|02|O|국회의원 면책특권은 직무상 발언·표결에 통상적으로 부수하여 행하여지는 행위에도 미칠 수 있다.|
6|③|01|O|국회의원은 현행범인 경우를 제외하고 회기 중 국회의 동의 없이 체포 또는 구금되지 않는다.|
6|③|02|O|회기 전에 체포 또는 구금된 국회의원은 현행범이 아닌 한 국회의 요구가 있으면 회기 중 석방된다.|
6|④|01|X|회기 중 국회의원 체포동의안은 재적의원 과반수 출석과 출석의원 과반수 찬성으로 의결한다.|국회의원 체포동의에 재적의원 과반수 찬성이 필요하다고 한 부분
6|⑤|01|O|국회의원의 불체포특권은 불수사특권이나 불기소특권을 의미하지 않는다.|
6|⑤|02|O|국회의원이 회기 중이라도 유죄판결이 확정되어 의원직이 상실되면 형 집행을 위하여 체포할 수 있다.|
7|①|01|O|국회에서 의결된 법률안은 정부에 이송되어 15일 이내에 대통령이 공포한다.|
7|②|01|O|대통령은 법률안의 일부에 대하여 재의를 요구할 수 없다.|
7|②|02|O|대통령은 법률안을 수정하여 재의를 요구할 수 없다.|
7|③|01|O|법률안이 정부에 이송된 후 15일 이내에 대통령이 공포나 재의요구를 하지 않으면 그 법률안은 법률로 확정된다.|
7|④|01|X|국회의 재의결로 확정된 법률이 정부에 이송된 후 5일 이내에 대통령이 공포하지 않으면 국회의장이 공포한다.|국회의 재의결 확정법률에 대한 국회의장 공포기한을 15일이라고 한 부분
7|⑤|01|O|법률은 특별한 규정이 없으면 공포한 날부터 20일이 지나 효력을 발생한다.|
8|①|01|X|대법관의 수는 대법원장을 포함하여 14명이다.|대법관 수가 대법원장을 제외하고 14명이라고 한 부분
8|②|01|O|행정법원의 심판권은 원칙적으로 판사 3명으로 구성된 합의부에서 행사한다.|
8|②|02|O|행정법원 합의부가 단독판사의 심판으로 결정한 사건은 행정법원 단독판사가 심판권을 행사한다.|
8|③|01|X|명령·규칙 또는 처분의 위헌·위법 여부가 재판의 전제가 되면 대법원이 이를 최종적으로 심사할 권한을 가진다.|대통령령 위헌 여부를 헌법재판소에 제청하여 심판받는다고 한 부분
8|③|02|X|헌법재판소에 위헌법률심판을 제청하는 대상은 법률의 위헌 여부이다.|대통령령 위헌 여부를 위헌법률심판 제청 대상으로 본 부분
8|④|01|X|법원조직법은 대통령선거무효소송에서 선거무효 판결에 관여대법관 3분의 2 이상의 찬성이 필요하다고 규정하지 않는다.|대통령선거무효 판결에 관여대법관 3분의 2 이상 찬성이 필요하다고 한 부분
8|⑤|01|X|대법관회의는 대법관 전원 3분의 2 이상의 출석과 출석인원 과반수 찬성으로 의결한다.|대법관회의가 출석인원 전원 찬성으로 의결하여야 한다고 한 부분
9|①|01|X|대통령은 조약을 체결·비준한다.|조약 체결권은 대통령에게 있고 비준권은 국회에 있다고 한 부분
9|①|02|X|국회는 일정한 조약의 체결·비준에 대한 동의권을 가질 뿐 조약의 비준권 자체를 가지는 것은 아니다.|조약 비준권이 국회에 속한다고 한 부분
9|②|01|O|중요한 국제조직에 관한 조약의 체결·비준에 대하여 국회는 동의권을 가진다.|
9|②|02|O|우호통상항해조약의 체결·비준에 대하여 국회는 동의권을 가진다.|
9|③|01|X|대한민국과 일본국 간의 어업에 관한 협정은 헌법 제6조 제1항에 따라 국내법과 같은 효력을 가지는 조약이다.|한일 어업협정을 국내법 효력이 없는 행정협정으로 본 부분
9|④|01|X|적법하게 체결·공포된 마라케쉬협정은 국내법과 같은 효력을 가진다.|마라케쉬협정에 의한 처벌가중을 법률에 의하지 않은 처벌로 본 부분
9|④|02|X|마라케쉬협정에 의하여 관세법위반자의 처벌이 가중되어도 죄형법정주의에 위배된다고 할 수 없다.|마라케쉬협정에 따른 처벌가중을 죄형법정주의 위반으로 본 부분
9|⑤|01|X|국회의원의 심의·표결권은 국회의 대내적 관계에서 행사되고 침해될 수 있을 뿐 다른 국가기관과의 대외적 관계에서는 직접 침해될 수 없다.|대통령의 조약 체결로 국회의원 개인의 심의·의결권이 침해된다고 한 부분
9|⑤|02|X|대통령이 국회 동의 없이 조약을 체결·비준하였더라도 국회의원 개인의 심의·표결권 침해 가능성은 인정되지 않는다.|국회의원이 대통령을 상대로 권한쟁의심판을 제기할 수 있다고 한 부분
10|①|01|O|저항권 사상은 고대 그리스의 참주 국외추방제도나 맹자의 역성혁명론에서 기원을 찾을 수 있다.|
10|②|01|O|저항권은 자연권으로 발전하여 영국의 대헌장, 미국 독립선언서, 프랑스 1789년 인권선언에서 실정화되었다.|
10|②|02|O|대한민국 헌법에는 저항권이 명문으로 규정되어 있지 않다.|
10|③|01|O|저항권은 공권력 행사자가 민주적 기본질서를 침해하거나 파괴하려는 경우 이를 회복하기 위하여 행사되는 국민의 권리이다.|
10|③|02|O|저항권은 국민이 공권력에 폭력·비폭력 또는 적극적·소극적으로 저항할 수 있는 헌법수호제도이다.|
10|④|01|O|저항권 행사에는 민주적 기본질서라는 전체 질서에 대한 중대한 침해 또는 파괴 시도가 요구된다.|
10|④|02|O|저항권 행사에는 이미 유효한 구제수단이 남아 있지 않아야 한다는 보충성 요건이 적용된다.|
10|⑤|01|X|저항권은 위헌적인 정권을 물러나게 함으로써 민주적 기본질서를 회복하려는 목적에서도 행사될 여지가 있다.|저항권을 기존의 위헌적 정권을 물러나게 할 목적으로 행사할 수 없다고 한 부분
11|①|01|O|죄형법정주의의 명확성원칙은 법률을 가치판단이 전혀 배제된 서술적 개념으로만 규정할 것을 요구하지 않는다.|
11|①|02|O|죄형법정주의의 명확성원칙은 입법의도가 건전한 일반상식을 가진 사람이 일의적으로 파악할 수 있는 정도일 것을 요구한다.|
11|②|01|O|다소 광범위하고 법관의 보충적 해석이 필요한 개념이라도 적용 단계에서 다의적으로 해석될 우려가 없으면 명확성 요구에 위배되지 않는다.|
11|③|01|O|군형법상 정당한 명령 또는 규칙은 법령 범위 안에서 군통수작용상 필요한 중요하고 구체성 있는 특정 사항에 관한 명령이나 규칙을 뜻한다.|
11|③|02|O|군형법상 정당한 명령 또는 규칙이라는 표현은 불명확하여 죄형법정주의에 위배된다고 볼 수 없다.|
11|④|01|O|처벌조항이 구성요건 행위를 직접 규정하지 않고 다른 법률조항 내용을 원용했다는 사정만으로 명확성원칙에 위반되는 것은 아니다.|
11|④|02|O|처벌조항이 원용 내용 일부를 괄호 안에 규정했다는 사정만으로 명확성원칙에 위반되는 것은 아니다.|
11|⑤|01|O|현대국가의 사회적 기능 증대와 사회현상의 복잡화로 형벌법규에서도 예외적 위임입법이 허용될 수 있다.|
11|⑤|02|X|단체협약에 위반한 자를 처벌하는 구 노동조합법 조항은 구성요건의 실질 내용을 단체협약에 위임하여 죄형법정주의의 법률주의에 위배된다.|구 노동조합법상 단체협약 위반 처벌조항이 죄형법정주의에 위배되지 않는다고 한 부분
11|⑤|03|X|단체협약에 위반한 자를 처벌하는 구 노동조합법 조항은 구성요건이 지나치게 애매하고 광범위하여 명확성원칙에 위배된다.|구 노동조합법상 단체협약 위반 처벌조항의 명확성 위반을 부정한 부분
12|①|01|O|헌법 제24조의 선거권에는 지방자치단체장 선거권이 포함된다.|
12|①|02|O|헌법 제24조의 선거권에는 지방의회의원 선거권도 포함된다.|
12|②|01|X|선거연령을 헌법으로 정하지 않은 것 자체가 곧 위헌이라고 볼 수 없다.|선거연령을 헌법으로 정하지 않은 것 자체에 위헌 소지가 있다고 한 부분
12|②|02|X|선거권과 공무담임권의 연령 설정은 입법자의 입법재량 영역에 속한다.|선거연령을 헌법에 두지 않은 것 자체를 위헌으로 본 부분
12|③|01|X|강제투표제도를 도입한 입법례가 있으므로 선거투표 참여를 법률로 강제할 수 없다는 데 이론이 없다고 볼 수 없다.|선거권이 권리라는 이유만으로 투표참여 강제가 언제나 불가능하다고 단정한 부분
12|④|01|X|집행유예자의 선거권을 전면적으로 제한하는 것은 헌법에 위반된다.|집행유예자의 선거권 전면제한이 합헌이라고 한 부분
12|④|02|X|범죄의 경중을 전혀 고려하지 않고 수형자의 선거권을 전면 제한하는 것은 헌법에 위반된다.|수형자의 선거권 전면제한이 합헌이라고 한 부분
12|⑤|01|O|재외국민의 선거권을 전면적으로 제한하는 것은 헌법에 위반된다.|
13|①|01|O|모든 인간은 헌법상 생명권의 주체가 되며 형성 중인 생명인 태아에게도 생명에 대한 권리가 인정된다.|
13|①|02|O|국가는 헌법 제10조에 따라 태아의 생명을 보호할 의무가 있다.|
13|②|01|O|살아서 출생하지 못한 태아에게 손해배상청구권을 인정하지 않는 민법상 태아 권리능력 규율은 법적 안정성 요청으로 정당화될 수 있다.|
13|②|02|O|살아서 출생하지 못한 태아의 손해배상청구권을 부정한다고 하여 곧바로 위헌적 입법불비가 초래된다고 볼 수 없다.|
13|③|01|O|초기배아는 아직 모체에 착상되거나 원시선이 나타나지 않은 이상 기본권 주체성이 인정되지 않는다.|
13|③|02|X|인간으로 발전할 잠재성을 가진 초기배아에 대하여는 국가의 보호의무가 인정된다.|초기배아에 대하여 국가의 보호필요성을 인정할 수 없다고 한 부분
13|④|01|O|직업인이 잔여배아 연구 허용 조항으로 불편을 겪더라도 이는 사실적·간접적 불이익에 불과할 수 있다.|
13|④|02|O|직업인이 잔여배아 연구 허용 조항에 대하여 기본권침해 가능성 및 자기관련성을 인정받지 못할 수 있다.|
13|⑤|01|O|배아생성자는 배아에 자신의 유전정보가 담긴 신체 일부를 제공하였으므로 배아의 관리 또는 처분에 대한 결정권을 가진다.|
13|⑤|02|O|배아생성자는 배아가 착상하여 출생하면 생물학적 부모 지위를 갖게 되므로 배아의 관리 또는 처분에 대한 결정권을 가진다.|
14|①|01|O|근로는 소득을 대가로 이루어지는 정신적·육체적 활동을 의미한다.|
14|②|01|O|근로의 권리에는 자신의 의사와 능력에 따라 근로관계를 형성할 권리가 포함된다.|
14|②|02|O|근로의 권리에는 타인의 방해 없이 근로관계를 계속 유지하고 근로 기회를 얻지 못한 경우 국가에 근로기회 제공을 요구할 권리가 포함된다.|
14|③|01|O|근로의 권리는 원칙적으로 국민의 권리이므로 외국인은 그 주체가 될 수 없다.|
14|③|02|O|근로의 권리 중 일할 환경에 관한 권리에 대해서는 외국인의 기본권 주체성이 인정될 수 있다.|
14|④|01|O|근로의 권리는 국가에 대한 직접적인 직장존속보장청구권을 보장하지 않는다.|
14|⑤|01|X|헌법 제32조 제1항의 근로의 권리는 개인인 근로자가 주체가 되는 권리이고 노동조합은 주체가 될 수 없다.|노동조합도 근로의 권리의 주체가 될 수 있다고 한 부분
15|①|01|O|국적은 헌법의 위임에 따라 국적법으로 구체화되지만 국민의 범위를 구체화·현실화하는 헌법사항이다.|
15|②|01|O|거주·이전의 자유에는 국내 체류지와 거주지를 자유롭게 정할 자유뿐만 아니라 해외여행 및 해외이주의 자유도 포함된다.|
15|②|02|O|거주·이전의 자유에는 대한민국 국적을 이탈할 수 있는 국적변경의 자유도 포함된다.|
15|③|01|O|일반적으로 외국인이 특정 국가의 국적을 선택할 권리가 자연권 또는 우리 헌법상 당연히 인정된다고 할 수 없다.|
15|④|01|O|헌법상 영토조항에 따라 북한지역도 대한민국 영토에 속한다.|
15|④|02|O|북한주민도 대한민국 국적을 취득·유지하는 데 아무런 영향이 없다고 볼 수 있다.|
15|⑤|01|X|남북한의 특수관계를 고려하면 개별 법률의 적용에서 북한지역을 외국에 준하는 지역으로 규정할 수 있다.|개별 법률에서 북한지역을 외국에 준하는 지역으로 규정할 수 없다고 한 부분
15|⑤|02|X|개별 법률의 적용에서 북한 주민 또는 법인을 외국인에 준하는 지위로 규정할 수 있다.|북한 주민 등을 외국인에 준하는 지위로 규정하는 것이 헌법상 영토조항에 위반된다고 한 부분
16|①|01|O|형사보상은 형사사법절차에 내재하는 불가피한 위험에 대하여 형사사법기관의 귀책사유를 따지지 않고 손실을 보상하는 제도이다.|
16|①|02|O|형사보상은 고의·과실로 인한 위법행위와 인과관계 있는 모든 손해를 배상하는 손해배상과 구별된다.|
16|②|01|O|국가의 형사사법행위가 고의·과실로 인한 것으로 인정되면 국가배상청구 등 별도 절차로 인과관계 있는 손해를 배상받을 수 있다.|
16|③|01|O|피고인으로 구금되었다가 무죄판결을 받은 사람은 형사보상의 대상이 된다.|
16|③|02|O|피의자로 구금되었다가 기소중지나 기소유예를 제외한 불기소처분을 받은 사람도 형사보상의 대상이 된다.|
16|④|01|O|형사보상청구는 무죄재판 확정 사실을 안 날부터 3년 이내에 하여야 한다.|
16|④|02|O|형사보상청구는 무죄재판이 확정된 날부터 5년 이내에 하여야 한다.|
16|⑤|01|X|보상을 청구할 수 있는 사람이 청구하지 않고 사망한 때에는 그 상속인이 형사보상을 청구할 수 있다.|형사보상청구권이 일신전속적이므로 상속인은 청구할 수 없다고 한 부분
17|①|01|O|법치국가원리는 국가작용이 법에 의하여 이루어져야 한다는 것을 의미한다.|
17|②|01|O|실정법의 규율 내용이 명확하여 다의적으로 해석·적용되어서는 안 된다는 명확성원칙은 법치국가원리에서 파생된다.|
17|③|01|O|헌법 제75조의 포괄위임금지원칙은 법률 명확성원칙이 행정입법에 관하여 구체화된 특별규정이다.|
17|④|01|X|국가에 의하여 일정 방향으로 유인된 신뢰이익도 법적 상태 변화에 대한 예측가능성에 따라 보호 여부가 달라질 수 있다.|보호가치 있는 신뢰이익은 예측가능성과 관계없이 언제나 보호된다고 한 부분
17|④|02|X|법률이 부여한 기회의 활용에 불과한 신뢰는 원칙적으로 사적 위험부담의 범위에 속할 수 있다.|특별한 신뢰이익을 언제나 절대적으로 보호된다고 한 부분
17|⑤|01|O|과거에 완성된 사실 또는 법률관계를 규율하는 진정소급입법은 특단의 사정이 없으면 구법에서 이미 얻은 자격 또는 권리를 존중하여야 한다.|
17|⑤|02|O|아직 완성되지 않고 진행 중인 사실관계나 법률관계를 규율하는 부진정소급입법은 특단의 사정이 없으면 구법상 기대이익을 존중하여야 할 입법의무가 없다.|
18|①|01|O|사업장 근로자의 3분의 2 이상을 대표하는 노동조합의 조직강제를 합헌으로 본 것은 적극적 단결권을 개인의 단결하지 않을 자유보다 중시한 것이다.|
18|②|01|O|학생의 학습권은 교원의 수업권에 대하여 우월한 지위에 있다.|
18|②|02|O|교원에게 고의로 수업을 거부할 자유는 인정되지 않는다.|
18|③|01|O|종교단체 설립 사립학교가 특정 종교행사와 종교수업 참가를 사실상 강제하고 대체과목을 두지 않으면 학생의 종교에 관한 인격적 법익을 침해할 수 있다.|
18|④|01|O|흡연권은 사생활의 자유를 실질적 핵으로 하는 기본권이다.|
18|④|02|O|혐연권은 사생활의 자유뿐만 아니라 생명권에까지 연결되므로 흡연권보다 상위의 기본권이다.|
18|⑤|01|X|채권자취소권을 합헌으로 본 것은 채권자의 재산권이 채무자의 일반적 행동자유권보다 상위 기본권이기 때문이 아니다.|채권자취소권 합헌의 근거를 채권자의 재산권 우위로 설명한 부분
18|⑤|02|X|채권자 재산권과 채무자·수익자의 일반적 행동자유 및 재산권이 충돌하면 규범조화적 해석과 법익형량을 종합하여 심사하여야 한다.|상충 기본권 중 채권자의 재산권을 상위 기본권으로 본 부분
19|①|01|X|국외 강제동원자에게 우선 위로금을 지급한 것은 객관적으로 정의와 형평에 반하거나 자의적인 차별이라고 보기 어렵다.|국내 강제동원자를 제외하고 국외 강제동원자에게만 위로금을 지급한 것이 위헌이라고 한 부분
19|②|01|O|대한민국 국민인 남자에게 병역의무를 부과한 법률조항은 평등권을 침해한다고 볼 수 없다.|
19|③|01|O|소년심판절차에서 검사에게 상소권이 인정되지 않는 것은 합리적 이유가 있어 피해자의 평등권을 침해한다고 볼 수 없다.|
19|④|01|O|형법상 범죄와 같은 구성요건을 두면서 법정형만 상향한 특정범죄 가중처벌 등에 관한 법률 조항은 평등원칙에 위반된다.|
19|⑤|01|O|개별법률금지원칙은 입법자가 평등원칙을 준수할 것을 요구하는 것이다.|
19|⑤|02|O|특정 규범이 개별사건법률에 해당한다는 사정만으로 곧바로 위헌이 되는 것은 아니다.|
20|①|01|O|자기결정권은 개인이 자유의지에 따라 자신의 삶과 운명을 자유롭게 결정할 수 있는 권리이다.|
20|①|02|O|자기결정권은 헌법에 명문 규정이 없더라도 기본권으로 인정된다.|
20|②|01|O|간통을 형사처벌하는 법률조항은 개인의 성적 자기결정권을 침해하여 헌법에 위반된다.|
20|②|02|O|혼인빙자간음을 형사처벌하는 법률조항은 개인의 성적 자기결정권을 침해하여 헌법에 위반된다.|
20|②|03|O|성매매를 한 사람을 형사처벌하는 법률조항은 개인의 성적 자기결정권을 침해하지 않아 헌법에 위반되지 않는다고 볼 수 있다.|
20|③|01|O|인수자가 없는 시체를 생전 본인의 의사와 무관하게 해부용 시체로 제공하도록 하는 것은 시체처분에 관한 자기결정권을 침해한다.|
20|④|01|O|2012년 헌법재판소 결정은 임부의 자기낙태를 처벌하는 조항이 임부의 자기결정권을 침해하지 않는다고 보았다.|
20|⑤|01|X|승용차 운행 시 좌석안전띠를 매지 않을 자유는 일반적 행동자유권의 보호영역에 속한다.|안전띠 착용 강제가 일반적 행동자유권을 침해하여 위헌이라고 한 부분
20|⑤|02|X|운전자에게 좌석안전띠 착용을 강제하는 규정은 생명·신체 보호와 교통사고 비용 감소라는 공익이 커서 일반적 행동자유권을 침해하지 않는다.|안전띠 착용 강제를 일반적 행동자유권 침해로 본 부분
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
        raise ValueError("cannot locate 2017 constitution section")
    section = text[start:]
    matches = list(re.finditer(r"【문\s*(\d+)】", section))
    if len(matches) < QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} constitution questions, got {len(matches)}")
    blocks = {}
    for idx, match in enumerate(matches[:QUESTION_COUNT]):
        no = int(match.group(1))
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        blocks[no] = section[match.start() : end_pos]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    first_by_label = {}
    for marker in re.finditer(r"[①②③④⑤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(CHOICE_LABELS):
            break
    if set(first_by_label) != set(CHOICE_LABELS):
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in CHOICE_LABELS]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = block[start:end]
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*상 법|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    first_by_label = {}
    for marker in re.finditer(r"([ㄱㄴㄷㄹㅁㅂㅅㅇ])\.", block):
        label = marker.group(1)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(BOX_LABELS):
            break
    if set(first_by_label) != set(BOX_LABELS):
        raise ValueError("cannot split eight box statements")
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label["ㅇ"].end() :])
    choice_start = first_by_label["ㅇ"].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in BOX_LABELS]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(1)] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-false" else CHOICE_LABELS
        split = split_box_units(blocks[no]) if labels == BOX_LABELS else split_choice_units(blocks[no])
        for label in labels:
            raw[(no, label)] = split[label]
    return raw


def source_verdict(no: int, label: str) -> str:
    return "X" if label in FALSE_LABELS[no] else "O"


def load_atom_rows() -> dict[tuple[int, str], list[dict[str, str | None]]]:
    rows = {}
    for line in ATOM_ROWS.splitlines():
        no_text, label, atom_index, verdict, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        if verdict not in {"O", "X"}:
            raise ValueError(f"bad atom verdict: {line}")
        if verdict == "X" and not trap:
            raise ValueError(f"X atom without trap: {line}")
        if verdict == "O" and trap:
            raise ValueError(f"O atom with trap: {line}")
        rows.setdefault((int(no_text), label), []).append({"atomIndex": atom_index.strip(), "sourceVerdict": verdict, "rep": rep.strip(), "trap": trap})
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
        qid = f"2017-g1-constitution-{no:02d}"
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-false" else CHOICE_LABELS
        units = [{"unitId": f"{qid}-{LABEL_CODE[label]}", "unitType": "boxStatement" if label in BOX_LABELS else "choice", "label": label, "rawStatement": raws[(no, label)], "originalVerdict": source_verdict(no, label)} for label in labels]
        questions.append({"qid": qid, "examId": EXAM_ID, "year": YEAR, "round": ROUND, "series": "법무사 1차", "group": GROUP, "groupLabel": "제1과목", "subject": SUBJECT_NAME, "no": no, "sourceLabel": question_source_label(no), "type": QUESTION_TYPES[no], "officialAnswer": OFFICIAL_ANSWERS[no], "units": units})
    return {"schema": "legal-scrivener/problem-original-current-by-subject/v1", "sourceFamily": "법무사시험", "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "updatedAt": today(), "questionCount": len(questions), "verificationSources": LEGAL_SOURCES, "questions": questions}


def build_queue(source: dict[str, object]) -> dict[str, object]:
    items = []
    for question in source["questions"]:
        q = question
        for unit in q["units"]:
            items.append({"unitId": unit["unitId"], "sourceFamily": "법무사시험", "source": unit_source_label(q["no"], unit["label"]), "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": q["no"], "unitType": unit["unitType"], "unitLabel": unit["label"], "sourceQuestionType": q["type"], "officialQuestionAnswer": q["officialAnswer"], "rawStatement": unit["rawStatement"], "originalVerdict": unit["originalVerdict"]})
    return {"schema": "legal-scrivener/atom-queue/v1", "sourceFamily": "법무사시험", "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "updatedAt": today(), "source": str(SOURCE_PATH), "itemCount": len(items), "items": items}


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
            source_is_x = row["sourceVerdict"] == "X"
            items.append({"atomId": f"bupmusa-2017-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
    return {"schema": "legal-scrivener/completed-atoms-by-subject/v2", "sourceFamily": "법무사시험", "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "updatedAt": today(), "atomPrinciple": "docs/atom_원칙_v001.md", "source": str(SOURCE_PATH), "sourceQueue": str(QUEUE_PATH), "sourceCount": len(queue["items"]), "questionCount": QUESTION_COUNT, "atomCount": len(items), "verificationSources": LEGAL_SOURCES, "policy": {"sourceStatement": "문제 원문 지문은 보존한다.", "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.", "atomSplit": "원문 보기 하나가 여러 조문·판례·학설 판단 지점을 포함하면 여러 atom으로 분해한다.", "xHandling": "원문상 틀린 판단 지점은 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.", "countAndCombination": "조합형·개수형 문제는 선택지 조합이 아니라 박스 문장별 근거명제로 atom화한다."}, "items": items}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("·", "ㆍ").replace("∙", "ㆍ").lower()


def year_to_exam_date(year: int) -> float:
    return year + 8.0 / 12.0


def weight_for_sources(sources: list[dict[str, object]], today_year: float = 2026.46, half_life: float = 4.0) -> float:
    total = 0.0
    for src in sources:
        age = max(0.0, today_year - year_to_exam_date(int(src.get("year", YEAR))))
        total += float(src.get("s", 1.0)) * (0.5 ** (age / half_life))
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


def source_from_atom(atom: dict[str, object]) -> dict[str, object]:
    return {"family": "법무사시험", "s": 1.0, "year": atom["year"], "round": atom["round"], "subject": SUBJECT_NAME, "source": integrated_source_label(atom), "sourceId": atom["atomId"], "sourceUnitId": atom["sourceUnitId"], "sourceVerdict": atom["sourceVerdict"], "sourceTrap": atom["sourceTrap"], "sourceStatement": atom["sourceStatement"]}


def new_integrated_item(atom: dict[str, object], source: dict[str, object]) -> dict[str, object]:
    return {"primary": "법무사시험", "sourceFamilies": ["법무사시험"], "subject": SUBJECT_NAME, "topic": TOPICS.get(int(atom["no"]), SUBJECT_NAME), "rep": atom["rep"], "a": atom["a"], "why": atom["why"], "basisType": atom["basisType"], "basisRef": atom["basisRef"], "sources": [source], "refs": [source["source"]], "sourceIds": [atom["atomId"]], "sourceAtomCount": 1, "quality": {"statementType": "declarative", "displayable": True, "normalizers": [], "changed": False}, "verification": {"status": "needs-legal-review", "lawAsOf": today(), "legalVerifiedAt": None, "statuteCitationStatus": "pending"}}


def rebuild_integrated(new_atoms: list[dict[str, object]]) -> dict[str, object]:
    existing = load_json(INTEGRATED_PATH) if INTEGRATED_PATH.exists() else None
    buckets = {}
    if existing:
        for old_item in existing.get("items", []):
            item = dict(old_item)
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2017-constitution-")]
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
        elif source["sourceId"] not in buckets[key]["sourceIds"]:
            buckets[key]["sources"].append(source)
            buckets[key]["refs"].append(source["source"])
            buckets[key]["sourceIds"].append(source["sourceId"])
            buckets[key]["sourceAtomCount"] = int(buckets[key]["sourceAtomCount"]) + 1
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
    current_dir = SUBJECT_DIR.parent.parent
    input_atoms = sum(len(load_json(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").get("items", [])) for year in years if (current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").exists())
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v009_2017_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


def validate_atom_text(items: list[dict[str, object]]) -> None:
    banned = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "않은 것은"]
    for item in items:
        rep = item["rep"]
        if any(token in rep for token in banned):
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
        raise ValueError(f"atom count too low: {completed['atomCount']}")
    ids = [item["atomId"] for item in completed["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    queue_units = {item["unitId"] for item in queue["items"]}
    atom_units = {item["sourceUnitId"] for item in completed["items"]}
    if queue_units != atom_units:
        raise ValueError(f"source unit coverage mismatch: {sorted(queue_units - atom_units)[:5]}")
    false_units = {f"2017-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
    false_atom_units = {item["sourceUnitId"] for item in completed["items"] if item["sourceVerdict"] == "X"}
    if not false_units.issubset(false_atom_units):
        raise ValueError(f"false source units without X atom: {sorted(false_units - false_atom_units)[:5]}")
    true_atom_errors = [item["atomId"] for item in completed["items"] if item["sourceUnitVerdict"] == "O" and item["sourceVerdict"] == "X"]
    if true_atom_errors:
        raise ValueError(f"X atoms under true source units: {true_atom_errors[:5]}")
    validate_atom_text(completed["items"])


def validate_integrated(doc: dict[str, object]) -> None:
    ids = [item["id"] for item in doc["items"]]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("bad integrated ids")


def update_index(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    index = load_json(SUBJECT_INDEX_PATH) if SUBJECT_INDEX_PATH.exists() else {"schema": "legal-scrivener/subject-index/v1", "sourceFamily": "법무사시험", "updatedAt": today(), "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subjects": {}}
    index["updatedAt"] = today()
    index.setdefault("subjects", {})[SUBJECT_NAME] = {"source": str(SOURCE_PATH), "atomQueue": str(QUEUE_PATH), "completedAtoms": str(OUT_PATH), "questionCount": source["questionCount"], "atomQueueItemCount": queue["itemCount"], "completedAtomCount": completed["atomCount"], "completedAtomsUpdatedAt": completed["updatedAt"]}
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
