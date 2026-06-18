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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2018" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2018_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2018"
TEXT_DIR = PRIVATE_ROOT / "text" / "2018"
RAW_PDF_PATH = RAW_DIR / "2018_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2018_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2018_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2018_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2018_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2018_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2018_bupmusa_1st"
YEAR = 2018
ROUND = 24
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
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "선거관리위원회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/선거관리위원회법"},
    {"title": "2018 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2018"},
    {"title": "2018 법무사 헌법 해설", "publisher": "김건호 헌법", "url": "local:2018_법무사_헌법_해설_법무사_김건호.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "⑤",
    3: "②",
    4: "①",
    5: "⑤",
    6: "⑤",
    7: "⑤",
    8: "③",
    9: "⑤",
    10: "④",
    11: "④",
    12: "③",
    13: "⑤",
    14: "⑤",
    15: "⑤",
    16: "②",
    17: "②",
    18: "⑤",
    19: "②",
    20: "④",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    14: "single-best-true",
    18: "count-false",
    19: "combination-false",
    20: "single-best-true",
})

FALSE_LABELS = {
    1: {"②"},
    2: {"⑤"},
    3: {"②"},
    4: {"①"},
    5: {"⑤"},
    6: {"⑤"},
    7: {"⑤"},
    8: {"③"},
    9: {"⑤"},
    10: {"④"},
    11: {"④"},
    12: {"③"},
    13: {"⑤"},
    14: {"①", "②", "③", "④"},
    15: {"⑤"},
    16: {"②"},
    17: {"②"},
    18: {"㉡", "㉢", "㉣", "㉤"},
    19: {"㉡", "㉢", "㉣"},
    20: {"①", "②", "③", "⑤"},
}

TOPICS = {
    1: "환경권",
    2: "언론과 표현의 자유",
    3: "공무원제도",
    4: "헌법상 경제질서",
    5: "직업의 자유",
    6: "헌법재판",
    7: "교육권",
    8: "명확성원칙",
    9: "재산권 제한",
    10: "탄핵심판",
    11: "대학의 자율성",
    12: "감사원",
    13: "청원권",
    14: "국회",
    15: "정당",
    16: "헌법개정",
    17: "형벌과 이중처벌금지",
    18: "지방자치제도",
    19: "국회 위원회",
    20: "선거관리위원회",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    4: ("헌법+헌법재판소 결정례", "헌법 제119조·제120조·제121조·제126조 및 관련 결정례", "경제질서, 경자유전, 국민연금, 경제민주화, 자연력 특허에 관한 조문·판례 지점이다."),
    6: ("헌법재판소법", "헌법재판소법 제23조·제25조·제47조·제72조", "헌법재판 절차의 대리인, 심판정족수, 사전심사, 기속력에 관한 조문 지점이다."),
    12: ("헌법+감사원법", "헌법 제97조·제98조·제100조 및 감사원법 제2조·제22조·제52조", "감사원의 지위, 구성, 임명, 규칙제정권과 회계검사 대상에 관한 조문 지점이다."),
    14: ("국회법", "국회법 제11조·제15조·제39조·제60조·제73조", "국회의장 선거, 위원회 출석·표결, 상임위원 겸임, 의사정족수, 발언권에 관한 조문 지점이다."),
    15: ("헌법+공직선거법+헌법재판소 결정례", "헌법 제8조 및 공직선거법 제47조", "정당의 민주성, 해산, 설립·활동의 자유와 비례대표 여성추천 비율에 관한 지점이다."),
    16: ("헌법", "헌법 제128조·제129조·제130조", "헌법개정 발의, 공고, 국회의결, 국민투표, 공포에 관한 조문 지점이다."),
    18: ("헌법+지방자치법+헌법재판소 결정례", "헌법 제117조·제118조 및 지방자치법 제4조", "지방자치단체 보장, 중층구조, 조직·운영, 경계변경, 관할권에 관한 지점이다."),
    19: ("국회법", "국회법 제37조·제39조·제41조·제45조·제63조", "예산결산특별위원회, 상임위원, 연석회의, 국가공무원 겸직 의원, 국회운영위원회 소관에 관한 조문 지점이다."),
    20: ("헌법+선거관리위원회법", "헌법 제114조 및 선거관리위원회법 제4조·제13조·제17조", "중앙선거관리위원회 구성, 위원장, 겸직제한, 법령 의견조회, 위원 신분보장에 관한 조문 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|환경권은 명문 법률규정이나 관계 법령의 규정 취지 및 조리에 비추어 주체·대상·내용·행사방법 등이 구체적으로 정립될 수 있어야 인정된다.|
1|①|02|O|사법상 권리로서 환경권을 인정하는 명문 규정이 없으면 환경권에 기하여 직접 방해배제청구권을 인정할 수 없다.|
1|②|01|X|환경영향평가 대상지역 밖의 주민도 수인한도를 넘는 환경피해나 그 우려를 입증하면 처분의 무효확인 등을 구할 원고적격이 인정될 수 있다.|환경영향평가 대상지역 밖 주민에게 원고적격이 전혀 없다고 한 부분
1|②|02|X|환경영향평가 대상지역 밖 주민의 환경상 이익도 구체적 침해 또는 침해우려가 증명되면 재판상 보호될 수 있다.|대상지역 밖 주민의 환경상 이익을 항상 추상적 공익으로만 본 부분
1|③|01|O|환경권의 보호대상인 환경에는 자연환경뿐만 아니라 생활환경도 포함된다.|
1|④|01|O|환경권은 건강하고 쾌적한 환경에 대한 침해배제를 청구할 수 있는 자유권적 측면을 가진다.|
1|④|02|O|환경권은 쾌적한 환경에서 생활할 수 있도록 국가에 배려를 요구하는 보호·보장청구권의 측면도 가진다.|
1|⑤|01|O|헌법은 국가와 국민이 환경보전을 위하여 노력하여야 한다고 규정한다.|
2|①|01|O|민사소송법상 방영금지가처분은 사법부가 개별 분쟁에 관하여 사법절차로 심리·결정하는 것이므로 헌법상 사전검열에 해당하지 않는다.|
2|②|01|O|언론인의 선거운동을 일률적으로 금지하고 처벌하는 공직선거법 조항은 선거운동의 자유를 침해한다.|
2|②|02|O|언론인의 선거운동 규제는 언론매체를 통한 활동에서 발생할 수 있는 문제를 규제하는 것으로 충분할 수 있다.|
2|③|01|O|방송통신심의위원회의 시정요구는 규제적·구속적 성격을 갖는 공권력 행사로 볼 수 있다.|
2|③|02|O|방송통신심의위원회의 시정요구는 헌법소원 또는 항고소송의 대상이 될 수 있다.|
2|④|01|O|영화의 제작과 상영은 의사표현의 한 수단으로서 언론·출판의 자유에 의하여 보장된다.|
2|④|02|O|영화의 제작과 상영은 학문·예술의 자유에 의하여도 보장될 수 있다.|
2|⑤|01|X|선거운동기간 중 인터넷언론사 게시판 등에 정당·후보자 지지·반대 글을 게시할 때 실명확인 조치를 요구하는 것은 표현의 자유를 침해한다고 볼 수 없다.|선거운동기간 인터넷언론사 게시판 실명확인 조치가 표현의 자유를 침해한다고 한 부분
2|⑤|02|X|선거운동기간 인터넷언론사 게시판 실명확인 조치는 선거의 공정성 확보라는 목적과 제한 방식 등을 고려할 때 과잉금지원칙에 위배되지 않을 수 있다.|선거운동기간 실명확인 조치를 위헌으로 단정한 부분
3|①|01|O|대통령은 국민 전체에 대한 봉사자인 헌법상 공무원에 해당한다.|
3|①|02|O|대통령은 특정 정당이나 특정 세력의 이익이 아니라 국민 전체를 위하여 공정하고 균형 있게 업무를 수행할 의무가 있다.|
3|②|01|X|공무원의 보수청구권은 법령에 의하여 구체적 내용이 형성된 경우 재산권의 내용에 포함될 수 있다.|어느 수준의 보수를 청구할 권리가 곧 헌법상 재산권이라고 한 부분
3|②|02|X|법령으로 구체화되기 전 공무원이 일정 수준의 보수를 청구할 수 있다는 기대는 재산권의 내용에 포함된다고 볼 수 없다.|구체화 전 보수수준 청구권을 재산권으로 본 부분
3|③|01|O|고도의 정책결정 업무를 담당하거나 보조하는 공무원으로서 법령에서 정무직으로 지정된 공무원은 특수경력직공무원이다.|
3|④|01|O|직업공무원제도는 헌법상 제도적 보장 중 하나이다.|
3|④|02|O|입법자는 직업공무원제도에 관하여 최소한 보장의 원칙 안에서 폭넓은 입법형성의 자유를 가진다.|
3|⑤|01|O|공무담임권은 공직취임 기회의 자의적 배제를 받지 않을 권리를 포함한다.|
3|⑤|02|O|공무담임권 보호영역에는 공무원 신분의 부당한 박탈이나 권한의 부당한 정지도 포함된다.|
4|①|01|X|국방상 또는 국민경제상 긴절한 필요가 있고 법률이 정하는 경우에는 사영기업을 국유 또는 공유로 이전할 수 있다.|긴절한 필요가 있어도 사영기업의 국유 또는 공유 이전이 인정되지 않는다고 한 부분
4|①|02|X|국방상 또는 국민경제상 긴절한 필요가 있고 법률이 정하는 경우에는 사영기업의 경영을 통제 또는 관리할 수 있다.|긴절한 필요와 법률 근거가 있어도 사영기업 경영통제·관리가 인정되지 않는다고 한 부분
4|②|01|O|자경농지 양도소득세 면제대상자를 농지소재지 거주자로 제한하는 것은 경자유전의 원칙에 위배되지 않는다.|
4|②|02|O|농지소재지 거주자 제한은 외지인의 농지투기 방지와 농업·농촌 활성화를 위한 경자유전 원칙 실현 수단으로 볼 수 있다.|
4|③|01|O|국민연금제도는 사회연대성에 기초하여 소득재분배 기능을 하므로 사회적 시장경제질서에 부합한다.|
4|③|02|O|국민연금 가입을 강제하는 법률조항은 헌법상 시장경제질서에 위배되지 않는다.|
4|④|01|O|경제주체 간 조화를 통한 경제민주화 이념은 경제영역에서 정의로운 사회질서를 형성하기 위한 국가목표이다.|
4|④|02|O|경제민주화 이념은 개인의 기본권을 제한하는 국가행위를 정당화하는 헌법규범이 될 수 있다.|
4|⑤|01|O|수력과 경제상 이용할 수 있는 자연력은 법률이 정하는 바에 따라 일정 기간 이용을 특허할 수 있다.|
5|①|01|O|법인을 구성하여 약국을 개설·운영하려는 약사들과 그 법인에게 약국개설을 금지하는 것은 직업선택 또는 직업수행의 자유를 침해할 수 있다.|
5|①|02|O|약사들로 구성된 법인의 약국개설 금지는 약사들이 약국경영을 위한 법인을 설립·운영하는 결사의 자유를 침해할 수 있다.|
5|②|01|O|성인대상 성범죄 전력자에게 형 집행 종료일부터 10년 동안 의료기관 개설·취업을 일률적으로 금지하는 것은 직업선택의 자유를 침해한다.|
5|③|01|O|치과전문의 자격시험제도 시행규칙을 마련하지 않은 행정입법부작위는 전공의 수련과정을 마친 사람의 직업의 자유를 침해한다.|
5|④|01|O|자동차 등을 이용하여 살인 또는 강간 등 범죄를 한 경우 운전면허를 필요적으로 취소하도록 한 조항은 직업의 자유를 침해한다.|
5|④|02|O|운전면허 필요적 취소조항은 운전을 생업으로 하는 사람에게 중대한 직업의 자유 제한을 초래할 수 있다.|
5|⑤|01|X|유치원 주변 학교환경위생정화구역에서 성관련 청소년유해업소를 예외 없이 금지하는 것은 직업의 자유를 침해하지 않는다.|유치원 주변 성관련 청소년유해업소 금지가 직업의 자유를 침해한다고 한 부분
5|⑤|02|X|유치원 주변 일정구역 안에서 성관련 청소년유해업소를 절대적으로 금지하는 것은 유아를 유해환경으로부터 보호하기 위한 필요·적절한 방법으로 볼 수 있다.|유치원 주변 절대금지가 위헌이라고 한 부분
6|①|01|O|헌법소원심판절차에서 당사자인 사인은 자신이 변호사 자격이 있는 경우가 아니면 변호사를 대리인으로 선임하여야 한다.|
6|②|01|O|헌법재판소법상 재판관 3인으로 구성되는 지정재판부의 사전심사는 헌법소원심판에 관한 제도이다.|
6|②|02|O|탄핵심판절차에서 재판관 3인 지정재판부가 사전심사를 담당하게 하는 것은 허용되지 않는다.|
6|③|01|O|권한쟁의심판은 종국심리에 관여한 재판관 과반수의 찬성으로 결정할 수 있다.|
6|④|01|O|정당해산심판의 인용결정에는 재판관 6명 이상의 찬성이 필요하다.|
6|⑤|01|X|헌법재판소의 합헌결정에는 위헌결정과 같은 기속력이 인정되지 않는다고 보는 것이 일반적이다.|합헌결정의 기속력 때문에 다시 헌법소원심판을 청구하면 각하된다고 한 부분
6|⑤|02|X|이미 합헌으로 선언된 법령조항도 사정변경이 없으면 헌법재판소가 다시 합헌결정을 할 수 있다.|이미 합헌결정된 법령조항에 대한 재청구가 항상 기속력에 반한다고 한 부분
7|①|01|O|부모의 자녀에 대한 교육권은 헌법에 명문으로 규정되어 있지 않지만 모든 인간이 국적과 관계없이 누리는 불가침의 인권이다.|
7|②|01|O|자녀교육은 헌법상 부모와 국가에게 공동으로 부과된 과제이다.|
7|②|02|O|학교교육의 범주에서는 국가의 교육권한이 헌법적으로 독자적인 지위를 부여받아 부모의 교육권과 함께 자녀교육을 담당한다.|
7|②|03|O|학교 밖 교육영역에서는 원칙적으로 부모의 교육권이 우위를 차지한다.|
7|③|01|O|헌법 제31조의 균등하게 교육을 받을 권리는 사교육 영역에서 개인이 별도로 교육을 시키거나 받는 행위를 국가가 금지·제한할 수 있는 근거가 아니다.|
7|④|01|O|일부 고액과외 방지를 위하여 모든 학생이 오로지 학원에서만 사적으로 배우도록 규율하는 것은 자기결정과 자기책임을 중시하는 헌법의 인간상에 위반된다.|
7|④|02|O|일부 고액과외 방지를 위하여 모든 사교육을 학원으로만 제한하는 것은 개성과 창의성 및 다양성을 지향하는 문화국가원리에 위반된다.|
7|⑤|01|X|학교교과교습학원의 교습시간만 제한하더라도 학교나 다른 사교육과의 차이에 비추어 합리적 이유 없는 차별이라고 보기 어렵다.|학원 교습시간 제한이 개인과외교습자에 비하여 불합리한 차별이라고 한 부분
7|⑤|02|X|학교교과교습학원의 교습시간 제한은 학원 운영자 등의 평등권을 침해한다고 보기 어렵다.|학원 교습시간 제한이 평등원칙에 위반된다고 한 부분
8|①|01|O|명확성원칙은 법치국가원리의 한 표현으로서 기본적으로 모든 기본권제한입법에 요구된다.|
8|①|02|O|규범의 의미내용을 알 수 없으면 법적 안정성과 예측가능성이 확보되지 않고 법집행기관의 자의적 집행이 가능해진다.|
8|②|01|O|표현의 자유 규제입법에서는 명확성원칙이 특별히 중요한 의미를 가진다.|
8|②|02|O|불명확한 규범에 의한 표현의 자유 규제는 헌법상 보호되는 표현에 대한 위축효과를 수반한다.|
8|③|01|X|급부행정 영역이나 규율대상이 다양하고 수시로 변하는 영역에서도 명확성원칙은 적용될 수 있다.|급부행정 영역이나 변동성이 큰 규율대상에는 명확성원칙이 적용되지 않는다고 한 부분
8|③|02|X|규율대상이 다양하거나 수시로 변화하는 성질이면 위임의 구체성·명확성 요구가 완화될 수 있을 뿐 배제되는 것은 아니다.|명확성 요구 완화와 명확성원칙 비적용을 혼동한 부분
8|④|01|O|명확성원칙은 모든 법규범을 순수한 기술적 개념으로만 구성할 것을 요구하지 않는다.|
8|④|02|O|명확성원칙은 기본적으로 최대한의 명확성이 아니라 최소한의 명확성을 요구한다.|
8|⑤|01|O|법문언의 의미내용을 법관의 해석으로 확인할 수 있고 그 해석이 개인적 취향에 좌우될 가능성이 없으면 명확성원칙에 반하지 않는다.|
9|①|01|O|재산권 제약이 비례원칙에 합치하면 재산권자가 수인하여야 하는 사회적 제약의 범위 안에 있다.|
9|①|02|O|재산권 제약이 비례원칙에 반하여 과잉이면 재산권자가 수인하여야 하는 사회적 제약의 한계를 넘는다.|
9|②|01|O|개발제한구역 지정 당시 상태대로 토지를 사용·수익·처분할 수 있으면 단순한 개발가능성 상실은 원칙적으로 재산권 보호범위에 속하지 않는다.|
9|②|02|O|장래 건축·개발목적 사용 기대나 이에 따른 지가상승 기회는 원칙적으로 재산권 보호범위에 속하지 않는다.|
9|③|01|O|개발제한구역 지정으로 토지를 종래 목적대로도 사용할 수 없거나 허용된 토지이용방법이 없으면 사회적 제약의 한계를 넘을 수 있다.|
9|④|01|O|도시계획시설 지정으로 토지 이용가능성이 배제되거나 종래 용도대로 사용할 수 없어 현저한 재산손실이 발생하면 수용적 효과가 인정될 수 있다.|
9|④|02|O|도시계획시설 지정이 사회적 제약의 범위를 넘는 수용적 효과를 가지면 국가나 지방자치단체는 보상을 하여야 한다.|
9|⑤|01|X|재산권 제한이 사회적 제약의 정도를 넘으면 입법자는 예외적 특별부담을 완화할 보상규정을 두어야 한다.|사회적 제약 초과시 보상규정 필요성을 금전보상만의 문제로 설명한 부분
9|⑤|02|X|사회적 제약을 넘는 재산권 제한에 대한 보상은 헌법상 반드시 금전보상만을 의미하지 않는다.|사회적 제약 초과시 보상이 반드시 금전보상만이라고 한 부분
10|①|01|O|국회가 탄핵소추사유에 관하여 별도 조사를 하지 않고 탄핵소추안을 의결하였다는 이유만으로 의결이 위헌·위법이 되는 것은 아니다.|
10|①|02|O|국회가 국정조사 결과나 특별검사 수사결과를 기다리지 않고 탄핵소추안을 의결하였다는 이유만으로 의결이 위헌·위법이 되는 것은 아니다.|
10|②|01|O|본회의가 탄핵소추안을 법제사법위원회에 회부하지 않기로 한 경우 본회의 보고 때부터 24시간 이후 72시간 이내에 무기명투표로 표결한다.|
10|②|02|O|탄핵소추안이 국회법상 표결기간 내 표결되지 않으면 폐기된 것으로 본다.|
10|③|01|O|탄핵소추절차는 국회와 대통령이라는 헌법기관 사이의 문제이다.|
10|③|02|O|탄핵소추의결은 사인으로서 대통령 개인의 기본권을 침해하는 것이 아니라 국가기관으로서 대통령의 권한행사를 정지시킨다.|
10|③|03|O|국가기관이 국민에게 공권력을 행사할 때 형성된 적법절차원칙은 탄핵소추절차에 직접 적용되지 않는다.|
10|④|01|X|탄핵사유에서 헌법에는 명문 헌법규정뿐만 아니라 헌법재판소 결정에 따라 형성·확립된 불문헌법도 포함된다.|탄핵사유의 헌법을 명문의 헌법규정만으로 한정한 부분
10|④|02|X|탄핵사유에서 법률에는 형식적 의미의 법률과 같은 효력을 가지는 국제조약 및 일반적으로 승인된 국제법규도 포함된다.|탄핵사유의 법률을 형식적 의미의 법률만으로 한정한 부분
10|⑤|01|O|탄핵소추안을 소추사유별로 나누어 발의할지 여러 소추사유를 포함한 하나의 안으로 발의할지는 발의 의원들의 자유로운 의사에 달려 있다.|
11|①|01|O|대학의 자율성은 학문의 자유를 보장하기 위한 수단으로서 대학에 부여된 헌법상 기본권이다.|
11|②|01|O|국립대학은 공법상 영조물이더라도 대학의 자율이라는 기본권의 주체가 될 수 있다.|
11|③|01|O|대학의 자치 주체를 기본적으로 대학으로 보더라도 교수나 교수회의 주체성이 부정되는 것은 아니다.|
11|③|02|O|대학의 자율성 침해 문제에서는 사안에 따라 대학, 교수, 교수회가 단독 또는 중첩적으로 주체가 될 수 있다.|
11|④|01|X|법인화되지 않은 국립대학도 헌법소원심판에서 보충성 예외가 인정되면 청구인적격이 인정될 수 있다.|법인화되지 않은 국립대학은 헌법소원 청구인적격도 인정되지 않는다고 한 부분
11|④|02|X|법인화되지 않은 국립대학에 행정소송상 당사자능력이 없어 권리구제 가능성이 없으면 헌법소원의 보충성 예외가 인정될 수 있다.|행정소송 당사자능력 부정을 헌법소원 청구인적격 부정으로 연결한 부분
11|⑤|01|O|대학의 자율성에 대한 규율 정도는 시대 사정과 학교급에 따라 달라질 수 있다.|
11|⑤|02|O|대학의 자율성에 관한 규율은 교육의 본질을 침해하지 않는 한 입법권자의 형성의 자유에 속한다.|
12|①|01|O|감사원은 대통령에 소속된 기관으로서 국무총리의 통할을 받지 않는다.|
12|①|02|O|감사원은 직무에 관하여 독립의 지위를 가진다.|
12|②|01|O|감사원은 감사원장을 포함한 5인 이상 11인 이하의 감사위원으로 구성한다.|
12|③|01|O|감사원장은 국회의 동의를 얻어 대통령이 임명한다.|
12|③|02|X|감사위원은 감사원장의 제청으로 대통령이 임명하며 국회의 동의를 요하지 않는다.|감사위원 임명에도 국회 동의가 필요하다고 한 부분
12|④|01|O|감사원은 감사 절차, 내부 규율과 감사사무 처리에 관한 규칙을 제정할 수 있다.|
12|⑤|01|O|다른 법률에 따라 감사원의 회계검사를 받도록 규정된 국가기관 아닌 단체의 회계도 감사원의 필요적 검사사항이 될 수 있다.|
13|①|01|O|헌법상 청원권은 적법한 청원을 한 국민이 국가기관에 청원 수리와 심사 및 처리결과 통지를 요구할 수 있는 권리이다.|
13|②|01|O|청원권의 보호범위에는 청원사항 처리결과에 심판서나 재결서에 준하여 이유를 명시할 것을 요구하는 권리가 포함되지 않는다.|
13|③|01|O|법률·명령·조례·규칙 등의 제정·개정 또는 폐지도 청원할 수 있는 사항에 해당한다.|
13|④|01|O|헌법상 청원권의 주체인 국민에는 법인도 포함된다.|
13|⑤|01|X|국가기관이 적법한 청원을 수리·심사하고 처리결과를 통지하면 헌법과 청원법상 의무를 이행한 것이다.|청원 처리내용이 기대에 미치지 못하면 헌법소원심판을 제기할 수 있다고 한 부분
13|⑤|02|X|청원 처리내용이 청원인의 기대에 미치지 못하더라도 더 이상 헌법소원의 대상이 되는 공권력 행사 또는 불행사라고 볼 수 없다.|청원 처리내용 자체를 헌법소원 대상으로 본 부분
14|①|01|X|국회의장과 부의장은 국회에서 무기명투표로 선거한다.|국회의장과 부의장을 기명투표로 선거한다고 한 부분
14|①|02|O|국회의장과 부의장은 재적의원 과반수의 득표로 당선된다.|
14|②|01|O|국회의장은 위원회에 출석하여 발언할 수 있다.|
14|②|02|X|국회의장은 위원회에 출석하더라도 표결에는 참가할 수 없다.|국회의장이 위원회에서 표결할 수 있다고 한 부분
14|③|01|X|국회의원은 둘 이상의 상임위원회 위원이 될 수 있다.|국회의원이 둘 이상의 상임위원이 될 수 없다고 한 부분
14|④|01|X|국회 본회의는 재적의원 5분의 1 이상의 출석으로 개의한다.|본회의 의사정족수를 재적의원 4분의 1 이상이라고 한 부분
14|⑤|01|O|국회의원은 위원회에서 같은 의제에 대하여 원칙적으로 횟수 및 시간 등에 제한 없이 발언할 수 있다.|
15|①|01|O|정당은 목적·조직과 활동이 민주적이어야 한다.|
15|①|02|O|정당은 국민의 정치적 의사형성에 참여하는 데 필요한 조직을 가져야 한다.|
15|②|01|O|정당의 목적이나 활동이 민주적 기본질서에 위배되면 정부는 헌법재판소에 정당해산을 제소할 수 있다.|
15|②|02|O|정당은 헌법재판소의 심판에 의하여 해산된다.|
15|③|01|O|정당설립의 자유에는 개인이 정당 일반 또는 특정 정당에 가입하지 않을 소극적 자유가 포함된다.|
15|③|02|O|정당설립의 자유에는 가입했던 정당으로부터 탈퇴할 자유가 포함된다.|
15|④|01|O|정당설립의 자유에는 원하는 명칭을 사용하여 정당을 설립하거나 정당활동을 할 자유도 포함된다.|
15|⑤|01|X|정당이 비례대표국회의원선거와 비례대표지방의회의원선거 후보자를 추천할 때에는 후보자 중 100분의 50 이상을 여성으로 추천하여야 한다.|비례대표 후보자 여성추천 비율을 100분의 30 이상이라고 한 부분
15|⑤|02|O|정당이 비례대표 후보자를 추천할 때에는 후보자명부 순위의 매 홀수에 여성을 추천하여야 한다.|
16|①|01|O|대통령의 임기연장 또는 중임변경을 위한 헌법개정은 제안 당시 대통령에게 효력이 없다.|
16|②|01|O|헌법개정은 국회재적의원 과반수 또는 대통령의 발의로 제안된다.|
16|②|02|X|제안된 헌법개정안은 대통령이 20일 이상의 기간 공고하여야 한다.|헌법개정안 공고기간을 30일 이상이라고 한 부분
16|③|01|O|국회는 헌법개정안이 공고된 날부터 60일 이내에 의결하여야 한다.|
16|③|02|O|헌법개정안에 대한 국회의 의결은 재적의원 3분의 2 이상의 찬성을 얻어야 한다.|
16|④|01|O|헌법개정안이 국민투표에서 필요한 찬성을 얻으면 헌법개정은 확정된다.|
16|④|02|O|헌법개정이 확정되면 대통령은 즉시 이를 공포하여야 한다.|
16|⑤|01|O|헌법개정안은 국회 의결 후 30일 이내에 국민투표에 붙여야 한다.|
16|⑤|02|O|헌법개정안은 국회의원선거권자 과반수 투표와 투표자 과반수 찬성을 얻어야 한다.|
17|①|01|O|모욕죄를 규정한 형법 조항은 표현의 자유를 침해하지 않는다.|
17|①|02|O|법원은 정당행위 규정의 적용으로 표현의 자유와 명예보호 사이의 조화를 도모할 수 있다.|
17|②|01|X|이중처벌금지원칙에서 말하는 처벌은 원칙적으로 범죄에 대한 국가 형벌권 실행으로서의 과벌을 뜻한다.|이중처벌금지원칙의 처벌을 국가가 행하는 모든 제재나 불이익처분으로 본 부분
17|②|02|X|이중처벌금지원칙의 처벌에는 국가가 행하는 모든 제재나 불이익처분이 포함되는 것은 아니다.|이중처벌금지원칙의 처벌을 모든 제재로 확대한 부분
17|③|01|O|은닉·보유·보관된 문화재에 대한 필요적 몰수는 구체적 행위 태양이나 보유권한을 고려하지 않으면 책임과 형벌 간 비례원칙에 위배될 수 있다.|
17|④|01|O|주거침입강제추행죄의 법정형을 주거침입강간죄와 동일하게 정한 것은 평등원칙에 반하지 않는다.|
17|⑤|01|O|형사범죄를 일으킨 공무원에게 공무원연금법상 급여를 제한하더라도 이중처벌에 해당하지 않는다.|
18|㉠|01|O|지방자치단체는 주민의 복리에 관한 사무를 처리하고 재산을 관리한다.|
18|㉠|02|O|지방자치단체는 법령의 범위 안에서 자치에 관한 규정을 제정할 수 있다.|
18|㉡|01|X|현행 2단계 지방자치단체 구조를 일정구역에서 단층화할지는 입법자의 입법형성권 범위에 속할 수 있다.|지방자치단체 중층구조를 단층화하려면 헌법개정이 필수라고 한 부분
18|㉡|02|X|헌법상 지방자치제도보장의 본질은 특정 지방자치단체의 존속보장이 아니라 지방자치단체에 의한 자치행정의 일반적 보장이다.|특정 중층구조 존속을 헌법이 보장한다고 본 부분
18|㉢|01|X|지방의회의 조직·권한·의원선거와 지방자치단체장의 선임방법 등 지방자치단체의 조직과 운영에 관한 사항은 법률로 정한다.|지방자치단체의 조직과 운영에 관한 사항을 조례로 정한다고 한 부분
18|㉣|01|X|지방자치단체의 관할구역 경계변경은 대통령령으로 정한다.|지방자치단체 관할구역 경계변경을 법률로 정한다고 한 부분
18|㉤|01|X|지방자치단체에는 국가의 영토고권과 같은 배타적 지배권이 부여되어 있지 않다.|지방자치단체가 관할구역 내 사람과 물건을 배타적으로 지배할 수 있다고 한 부분
18|㉤|02|X|지방자치제도 보장은 지방자치단체의 자치행정을 일반적으로 보장할 뿐 특정 자치단체의 존속이나 배타적 관할권을 보장하는 것은 아니다.|지방자치단체의 배타적 지배권을 인정한 부분
19|㉠|01|O|예산결산특별위원회는 예산안·기금운용계획안 및 결산을 심사하기 위하여 두는 위원회이다.|
19|㉠|02|O|예산결산특별위원회에는 특별위원회의 존속기한 규정이 적용되지 않는다.|
19|㉡|01|O|국회의원은 둘 이상의 상임위원회의 위원이 될 수 있다.|
19|㉡|02|X|상임위원장은 해당 상임위원 중에서 본회의 선거로 선출한다.|상임위원장을 국회의장이 임명한다고 한 부분
19|㉢|01|X|둘 이상의 위원회는 연석회의를 열어 의견을 교환할 수 있으나 표결은 할 수 없다.|연석회의에서 공통 의안을 표결할 수 있다고 한 부분
19|㉣|01|X|국무총리·국무위원 등 국가공무원 직을 겸한 의원은 상임위원을 사임할 수 있다.|국가공무원 직을 겸한 의원이 상임위원을 사임하여야 한다고 한 부분
19|㉤|01|O|국회법과 국회규칙에 관한 사항은 국회운영위원회의 소관사항이다.|
20|①|01|X|중앙선거관리위원회는 대통령이 임명하는 3인, 국회에서 선출하는 3인, 대법원장이 지명하는 3인의 위원으로 구성된다.|중앙선거관리위원회 대통령 임명 위원이 국무총리 제청에 따른다고 한 부분
20|②|01|X|중앙선거관리위원회의 위원장은 위원 중에서 호선한다.|중앙선거관리위원회 위원장을 대법원장이 지명한다고 한 부분
20|③|01|O|헌법상 중앙선거관리위원회 위원은 정당에 가입하거나 정치에 관여할 수 없다.|
20|③|02|X|중앙선거관리위원회 위원의 겸직 제한은 헌법이 아니라 선거관리위원회법에서 규율한다.|다른 공직 겸직금지가 헌법상 명시되어 있다고 한 부분
20|④|01|O|행정기관이 선거·국민투표 및 정당관계법령을 제정·개정 또는 폐지하려면 미리 해당 법령안을 중앙선거관리위원회에 송부하여 의견을 구하여야 한다.|
20|⑤|01|X|각급선거관리위원회 위원은 일정 기간과 일정 중대범죄 예외를 전제로 현행범이 아니면 체포 또는 구속되지 않는다.|중앙선거관리위원회 위원이 현행범이 아니면 언제나 체포·구속·소추되지 않는다고 한 부분
20|⑤|02|X|선거관리위원회법상 위원 신분보장은 체포·구속 제한을 정할 뿐 소추 제한까지 일반적으로 규정하지 않는다.|중앙선거관리위원회 위원이 현행범이 아니면 소추되지 않는다고 한 부분
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
        raise ValueError("cannot locate 2018 constitution section")
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
        statement = re.split(r"\s*제1교시\(1과목\)\s*①책형\s*전체|\s*제1과목\s*①책형\s*전체|\s*【\s*상 법|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    first_by_label = {}
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
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(0)] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = BOX_LABELS if QUESTION_TYPES[no] in {"count-false", "combination-false"} else CHOICE_LABELS
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
        qid = f"2018-g1-constitution-{no:02d}"
        labels = BOX_LABELS if QUESTION_TYPES[no] in {"count-false", "combination-false"} else CHOICE_LABELS
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
            items.append({"atomId": f"bupmusa-2018-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2018-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v008_2018_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2018-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
