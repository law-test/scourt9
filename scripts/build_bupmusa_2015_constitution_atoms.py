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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2015" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2015_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2015"
TEXT_DIR = PRIVATE_ROOT / "text" / "2015"
RAW_PDF_PATH = RAW_DIR / "2015_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2015_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2015_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2015_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2015_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2015_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2015_bupmusa_1st"
YEAR = 2015
ROUND = 21
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 106
MIN_ATOM_COUNT = 120
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS_BY_QUESTION = {
    15: ["가", "나", "다", "라", "마"],
    18: ["가", "나", "다", "라", "마", "바", "사", "아"],
    19: ["가", "나", "다", "라", "마", "바", "사", "아"],
}
LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
    "가": "01",
    "나": "02",
    "다": "03",
    "라": "04",
    "마": "05",
    "바": "06",
    "사": "07",
    "아": "08",
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "형사보상 및 명예회복에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사보상및명예회복에관한법률"},
    {"title": "2015 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2015/108486"},
    {"title": "2015 법무사 확정정답 공지", "publisher": "법원행정처", "url": "https://anaham.tistory.com/12165"},
    {"title": "2015 법무사 헌법 해설", "publisher": "천책상장", "url": "local:2015_법무사_헌법_해설_법무사_천책상장.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "①",
    2: "⑤",
    3: "④",
    4: "②",
    5: "⑤",
    6: "④",
    7: "①",
    8: "③",
    9: "④",
    10: "②",
    11: "②",
    12: "②",
    13: "⑤",
    14: "⑤",
    15: "①",
    16: "④",
    17: "④",
    18: "①",
    19: "③",
    20: "⑤",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    2: "single-best-true",
    7: "single-best-true",
    15: "count-true",
    18: "count-false",
    19: "count-false",
    20: "single-best-true",
})

FALSE_LABELS = {
    1: {"①"},
    2: {"①", "②", "③", "④"},
    3: {"④"},
    4: {"②"},
    5: {"⑤"},
    6: {"④"},
    7: {"②", "③", "④", "⑤"},
    8: {"③"},
    9: {"④"},
    10: {"②"},
    11: {"②"},
    12: {"②"},
    13: {"⑤"},
    14: {"⑤"},
    15: {"가", "나", "라", "마"},
    16: {"④"},
    17: {"④"},
    18: {"가", "나"},
    19: {"가", "사", "아"},
    20: {"①", "②", "③", "④"},
}

TOPICS = {
    1: "헌법의 기본원리",
    2: "정당제도",
    3: "평등권과 평등원칙",
    4: "적법절차",
    5: "종교의 자유",
    6: "사생활의 비밀과 자유",
    7: "변호인의 조력을 받을 권리",
    8: "학문의 자유와 대학의 자율성",
    9: "기본권 주체",
    10: "집회의 자유",
    11: "직업의 자유",
    12: "예산제도",
    13: "대통령과 행정부",
    14: "재판청구권",
    15: "국회 운영과 의사절차",
    16: "국민투표권",
    17: "국가긴급권과 통치행위",
    18: "국무회의 심의사항",
    19: "헌법 명문 규정",
    20: "권리구제형 헌법소원",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    12: ("헌법", "헌법 제54조·제55조·제57조", "예산안 제출·의결, 준예산, 예비비, 증액동의 조문을 구별하는 지점이다."),
    13: ("헌법+사면법+헌법재판소 결정례", "헌법 제68조·제86조·제87조·제89조·제94조 및 사면법 제9조", "대통령과 행정부 구성, 특별사면, 임명제청 요건을 구별하는 지점이다."),
    15: ("헌법+국회법", "헌법 제47조·제49조·제50조 및 국회법 제70조", "국회의 회기, 회의 공개, 의결, 의안 발의 요건을 구별하는 지점이다."),
    16: ("헌법+헌법재판소 결정례", "헌법 제72조·제130조 및 국민투표권 결정례", "중요정책 국민투표, 헌법개정 국민투표, 국민투표권자 범위를 구별하는 지점이다."),
    18: ("헌법", "헌법 제89조", "국무회의 필수 심의사항으로 헌법에 열거된 사항과 열거되지 않은 사항을 구별하는 지점이다."),
    19: ("헌법+국회법", "헌법 제43조·제46조·제53조·제62조·제63조·제116조 및 관련 법원리", "헌법 명문 규정과 헌법상 원리 또는 비명문 사항을 구별하는 지점이다."),
    20: ("헌법재판소법+헌법재판소 결정례", "헌법재판소법 제68조 제1항 및 관련 결정례", "권리구제형 헌법소원의 현재성, 청구기간, 자기관련성, 직접성, 보충성을 구별하는 지점이다."),
})

ATOM_ROWS = """
1|①|01|X|헌법의 기본원리는 구체적 기본권을 직접 도출하는 근거가 될 수 없다.|헌법의 기본원리에서 구체적 기본권을 도출할 수 있다고 한 부분
1|①|02|X|헌법의 기본원리는 입법과 정책결정의 방향을 제시하고 헌법수호의 지침으로 작용한다.|헌법 기본원리의 기능에 구체적 기본권 도출근거를 포함한 부분
1|②|01|O|자유민주적 기본질서에는 기본적 인권 존중, 권력분립, 의회제도, 복수정당제도와 선거제도가 포함된다.|
1|②|02|O|자유민주적 기본질서에는 사유재산과 시장경제를 골간으로 한 경제질서와 사법권 독립이 포함된다.|
1|③|01|O|우리 헌법상 경제질서는 사유재산제와 자유경쟁을 존중하는 자유시장경제질서를 기본으로 한다.|
1|③|02|O|우리 헌법상 경제질서는 사회복지와 사회정의를 위한 국가적 규제와 조정을 용인하는 사회적 시장경제질서 성격도 가진다.|
1|④|01|O|문화국가원리상 국가의 문화육성 대상에는 엘리트문화뿐 아니라 서민문화와 대중문화도 포함된다.|
1|⑤|01|O|명확성원칙에서 요구되는 명확성의 정도는 법률이나 법조항의 성격에 따라 달라질 수 있다.|
2|①|01|X|정당의 지구당은 중앙당의 단순한 하부조직이 아니라 독자성을 가진 단체로서 법인격 없는 사단에 해당할 수 있다.|정당 지구당이 법인격 없는 사단에 해당하지 않는다고 한 부분
2|②|01|X|정당의 대통령선거 후보경선에서 여론조사 결과를 반영한 것은 헌법소원심판 대상인 공권력 행사에 해당하지 않는다.|정당 후보경선 여론조사 반영을 공권력 행사로 본 부분
2|③|01|X|정당해산결정은 헌법 제8조 제4항의 요건 외에도 비례원칙을 준수하여야 한다.|정당 목적이나 활동이 민주적 기본질서에 위배되면 비례원칙 검토 없이 해산할 수 있다고 한 부분
2|④|01|X|해산된 정당의 강령 또는 기본정책과 동일하거나 유사한 정당은 창당할 수 없다.|해산정당과 유사한 명칭 사용 금지까지 유사명칭 전부로 확장한 부분
2|④|02|X|헌법재판소 결정으로 해산된 정당의 명칭과 같은 명칭은 다시 정당 명칭으로 사용할 수 없다.|해산정당과 유사한 명칭까지 모두 사용할 수 없다고 한 부분
2|⑤|01|O|위헌정당해산결정 시 그 정당 소속 국회의원의 의원직 상실은 위헌정당해산제도의 본질적 효력으로 인정될 수 있다.|
3|①|01|O|국내통화 위조·변조 등을 가중처벌한 특정범죄 가중처벌 등에 관한 법률 조항은 형법 조항과의 관계에서 형벌체계상 균형을 잃어 평등원칙에 위반된다고 판단되었다.|
3|②|01|O|형법상 폭행·가혹행위죄의 법정형이 폭행죄나 공무집행방해죄보다 무겁다는 사정만으로 평등원칙에 위반된다고 볼 수 없다.|
3|③|01|O|지방공무원 면직처분 불복 시 필요적으로 소청심사를 거치게 한 것은 평등원칙에 위반되지 않는다고 판단되었다.|
3|④|01|X|행정사 결격사유로 금고 이상 실형 집행 종료 또는 면제 후 3년 미경과자를 정한 조항은 직업선택의 자유를 침해하지 않는다고 판단되었다.|행정사 결격사유가 다른 국가자격보다 엄격하여 평등권을 침해한다고 한 부분
3|⑤|01|O|사실혼 배우자에게 상속권을 인정하지 않는 민법 조항은 사실혼 배우자의 평등권을 침해한다고 보기 어렵다.|
4|①|01|O|적법절차원칙은 형사소송절차에 한정되지 않고 국가작용 전반에 대한 헌법심사 기준으로 적용될 수 있다.|
4|②|01|X|적법절차원칙은 기본권 제한과 관련되는지 여부와 관계없이 입법작용과 행정작용에도 적용될 수 있다.|적법절차원칙이 기본권 제한이 있을 때에만 적용된다고 한 부분
4|③|01|O|적법절차원칙의 절차적 요청에는 당사자에 대한 적절한 고지와 의견·자료 제출 기회 부여가 포함된다.|
4|④|01|O|범칙금 미납자에 대하여 행정청 이의제기나 의견진술 기회 없이 경찰서장이 즉결심판을 청구하도록 한 것은 적법절차원칙에 위배된다고 보기 어렵다.|
4|⑤|01|O|사법경찰관이 위험발생 염려가 없는데도 사건 종결 전에 압수물을 폐기한 행위는 적법절차원칙에 반한다.|
5|①|01|O|보호자가 사망 위험이 예견되는 자녀에게 필요한 수혈을 종교적 신념 등을 이유로 거부하고 방해하면 유기치사죄가 성립할 수 있다.|
5|②|01|O|종교의 자유에는 신앙의 자유와 종교적 행위의 자유가 포함된다.|
5|②|02|O|종교적 행위의 자유에는 신앙고백, 종교적 의식 및 집회·결사, 종교전파·교육의 자유가 포함된다.|
5|③|01|O|종교전파의 자유는 자신의 종교나 종교적 확신을 알리고 선전하는 자유를 뜻한다.|
5|③|02|O|종교전파의 자유가 국민이 선택한 임의의 장소에서 자유롭게 포교할 권리까지 보장하는 것은 아니다.|
5|④|01|O|구치소 내 종교의식 또는 행사에 미결수용자의 참석을 일률적으로 불허한 것은 종교의 자유를 침해할 수 있다.|
5|⑤|01|X|종교단체 운영 교육기관에도 학교설립인가 또는 학원설립등록을 요구하는 것이 종교의 자유를 침해한다고 볼 수 없다.|종교단체 교육기관 인가·등록 요구가 종교의 자유를 침해하여 위헌이라고 한 부분
6|①|01|O|사생활의 비밀은 국가가 사생활영역을 들여다보는 것에 대한 보호를 제공한다.|
6|①|02|O|사생활의 자유는 국가가 사생활의 자유로운 형성을 방해하거나 금지하는 것에 대한 보호를 의미한다.|
6|②|01|O|사생활의 비밀과 자유는 개인 사생활이 함부로 공개되지 않을 소극적 권리를 보장한다.|
6|②|02|O|사생활의 비밀과 자유는 자신에 대한 정보를 자율적으로 통제할 적극적 권리까지 보장하려는 취지를 가진다.|
6|③|01|O|사생활의 비밀과 자유는 개인의 내밀한 내용의 비밀 유지와 사생활 불가침을 보장한다.|
6|③|02|O|사생활의 비밀과 자유는 양심영역·성적영역 같은 내밀한 영역과 정신적 내면생활의 보호를 포함한다.|
6|④|01|X|구치소장이 미결수용자의 배우자 접견 내용을 녹음한 행위는 사생활의 비밀과 자유를 제한하지만 과잉금지원칙에 위반되지 않는다고 판단되었다.|미결수용자의 배우자 접견 녹음이 사생활의 비밀과 자유를 침해하여 위헌이라고 한 부분
6|⑤|01|O|도로 운전 중 좌석안전띠 착용 여부는 사생활영역의 문제가 아니므로 안전띠 착용의무와 범칙금 통고가 사생활의 비밀과 자유를 침해하지 않는다.|
7|①|01|O|가사소송에서 변호사를 대리인으로 선임하여 조력을 받는 것은 헌법 제12조 제4항의 변호인의 조력을 받을 권리 보호영역에 포함되지 않는다.|
7|②|01|X|형사사건에서 변호인의 조력을 받을 권리는 피의자와 피고인 모두에게 보장된다.|변호인의 조력을 받을 권리가 피고인에게만 인정된다고 한 부분
7|③|01|X|형사절차가 종료되어 교정시설에 수용 중인 수형자는 원칙적으로 변호인의 조력을 받을 권리의 주체가 될 수 없다.|수형자도 원칙적으로 변호인의 조력을 받을 권리의 주체가 된다고 한 부분
7|④|01|X|미결수용자의 변호인 접견권도 국가안전보장·질서유지 또는 공공복리를 위하여 필요한 경우 법률로 제한될 수 있다.|변호인의 조력을 받을 권리를 법률로도 제한할 수 없다고 한 부분
7|⑤|01|X|미결수용자나 변호인이 원하는 특정 시점에 접견이 이루어지지 않았다는 사정만으로 변호인의 조력을 받을 권리가 곧바로 침해되는 것은 아니다.|원하는 특정 시점에 접견이 이루어지지 않으면 변호인의 조력을 받을 권리가 침해된다고 한 부분
8|①|01|O|학문의 자유는 진리를 탐구하는 자유를 의미한다.|
8|①|02|O|학문의 자유에는 탐구 결과에 대한 발표의 자유와 가르치는 자유가 포함된다.|
8|②|01|O|국립대학 교원 성과연봉제는 학문의 자유를 침해한다고 볼 수 없다.|
8|③|01|X|교육의 자주성과 대학의 자율성은 학문의 자유 보장수단으로서 대학에 부여된 헌법상 기본권이다.|대학의 자율성이 대학에게 부여된 헌법상 기본권이 아니라고 한 부분
8|④|01|O|초·중·고등학교 교사는 수업의 자유를 내세워 자신이 연구한 결과를 학생에게 여과 없이 전파할 수 없다.|
8|⑤|01|O|경찰대학 입학연령을 21세 미만으로 제한한 규정은 학문의 자유를 침해한다고 볼 수 없다.|
9|①|01|O|평등권에서 도출되는 선거에서의 기회균등 원칙은 후보자뿐 아니라 정당에도 보장된다.|
9|②|01|O|초기배아는 모체에 착상되거나 원시선이 나타나기 전까지 기본권 주체성을 인정하기 어렵다.|
9|③|01|O|권리능력 없는 단체는 성질상 생명·신체의 안전에 관한 기본권의 주체가 될 수 없다.|
9|④|01|X|범죄피해자인 외국인의 구조청구에는 해당 국가의 상호보증이 요구된다.|범죄피해자인 외국인이 상호보증과 관계없이 범죄피해자구조를 청구할 수 있다고 한 부분
9|⑤|01|O|직업의 자유 중 직장선택의 자유는 인간의 권리로서 외국인도 제한적으로 주체가 될 수 있다.|
10|①|01|O|옥외집회 신고사항에 미비점이 있거나 신고 범위를 일탈하였더라도 신고내용과 동일성이 유지되면 미신고 옥외집회가 아니다.|
10|②|01|X|집회 해산은 공공의 안녕질서에 대한 추상적 위협만으로는 부족하고 법정 사유와 직접적 위험 등 요건을 충족하여야 한다.|공공의 안녕질서에 대한 위협이 예상되면 원칙적으로 집회를 해산할 수 있다고 한 부분
10|③|01|O|집회에 대한 허가제는 헌법상 금지된다.|
10|④|01|O|집회의 자유에는 집회의 시간·장소·방법과 목적을 스스로 결정할 권리가 포함된다.|
10|④|02|O|옥외집회를 야간에 주최하는 것도 원칙적으로 집회의 자유로 보호된다.|
10|⑤|01|O|옥외집회 신고의무는 집회 자체 보호와 이익충돌 방지를 위한 사전적 협력의무이다.|
11|①|01|O|직업의 자유는 개인의 주관적 공권이자 사회적 시장경제질서라는 객관적 법질서의 구성요소이다.|
11|②|01|X|직업의 계속성 요건은 개방적으로 해석되므로 휴가기간 중 하는 일이나 수습직 활동도 직업 개념에 포함될 수 있다.|휴가기간 중 하는 일이 직업 개념에 포함될 수 없다고 한 부분
11|②|02|O|무보수 봉사직은 생활의 기본적 수요를 충족하기 위한 계속적 소득활동이 아니므로 직업으로 보기 어렵다.|
11|③|01|O|객관적 사유에 의하여 직업선택의 자유를 제한하는 경우에는 엄격한 비례원칙 심사가 적용된다.|
11|④|01|O|직업의 자유에는 해당 직업에 합당한 보수를 받을 권리까지 포함된다고 보기 어렵다.|
11|⑤|01|O|직업수행의 자유에 대해서는 직업결정의 자유나 전직의 자유보다 상대적으로 더 넓은 법률상 규제가 가능하다.|
12|①|01|O|정부는 회계연도마다 예산안을 편성하여 회계연도 개시 90일 전까지 국회에 제출하여야 한다.|
12|①|02|O|국회는 회계연도 개시 30일 전까지 예산안을 의결하여야 한다.|
12|②|01|X|국회가 의결한 예산 또는 예산안 의결은 헌법소원의 대상이 되는 공권력 행사에 해당하지 않는다.|예산이 일반국민을 구속하여 헌법소원의 대상이 된다고 한 부분
12|③|01|O|새 회계연도 개시까지 예산안이 의결되지 못하면 정부는 일정 경비를 전년도 예산에 준하여 집행할 수 있다.|
12|③|02|O|예산안 미의결 시 전년도 예산에 준하여 집행할 수 있는 경비에는 기관·시설 유지운영, 법률상 지출의무 이행, 이미 승인된 사업 계속 경비가 포함된다.|
12|④|01|O|예비비는 총액으로 국회의 의결을 얻어야 한다.|
12|④|02|O|예비비 지출은 차기 국회의 승인을 얻어야 한다.|
12|⑤|01|O|국회는 정부 동의 없이 정부 제출 지출예산 각항의 금액을 증가하거나 새 비목을 설치할 수 없다.|
13|①|01|O|군인은 현역을 면한 후가 아니면 국무총리로 임명될 수 없다.|
13|①|02|O|군인은 현역을 면한 후가 아니면 국무위원으로 임명될 수 없다.|
13|②|01|O|대통령은 소속 정당을 위하여 정당활동을 할 수 있는 사인의 지위를 가진다.|
13|②|02|O|대통령은 국민 모두에 대한 봉사자로서 공익실현 의무를 지는 헌법기관의 지위도 가진다.|
13|③|01|O|대통령의 특별사면은 국무회의 심의를 거쳐야 한다.|
13|③|02|O|대통령의 특별사면에는 국회의 동의가 필요하지 않다.|
13|④|01|O|대통령 임기가 만료될 때에는 임기만료 70일 내지 40일 전에 후임자를 선거한다.|
13|⑤|01|X|국무위원은 국무총리의 제청으로 대통령이 임명한다.|국무위원 임명에는 국무총리 제청이 필수적이지 않다고 한 부분
13|⑤|02|X|행정각부의 장은 국무위원 중에서 국무총리의 제청으로 대통령이 임명한다.|국무위원과 행정각부의 장의 임명제청 요건을 다르게 본 부분
14|①|01|O|헌법 제27조 제1항의 재판청구권이 모든 사건에 대하여 대법원 법관의 균등한 재판을 받을 권리나 상고심 재판을 받을 권리를 의미하지 않는다.|
14|②|01|O|재심청구권은 재판을 받을 권리에 당연히 포함된다고 할 수 없다.|
14|②|02|O|재심사유의 범위는 입법자가 법적 안정성, 재판의 신속·적정성, 법원 업무부담 등을 고려하여 정할 입법정책 문제이다.|
14|③|01|O|필요적 전심절차로서의 행정심판에는 사법절차가 준용되어야 한다.|
14|③|02|O|임의적 전심절차인 행정심판에는 당사자의 선택권이 보장되므로 반드시 사법절차가 준용될 필요는 없다.|
14|④|01|O|헌법재판소는 공정한 재판을 받을 권리가 헌법상 기본권으로 보장된다고 본다.|
14|⑤|01|X|국민참여재판을 받을 권리는 헌법 제27조 제1항 재판청구권의 보호범위에 속한다고 볼 수 없다.|국민참여재판을 받을 권리가 재판청구권의 보호범위에 속한다고 한 부분
15|가|01|X|국회의 임시회는 대통령 또는 국회재적의원 4분의 1 이상의 요구로 집회된다.|국회의 임시회 요구정족수를 국회재적의원 3분의 1 이상으로 본 부분
15|나|01|X|국회 정기회의 회기는 100일을 초과할 수 없다.|국회 정기회 회기를 120일까지로 본 부분
15|나|02|O|국회 임시회의 회기는 30일을 초과할 수 없다.|
15|다|01|O|출석의원 과반수의 찬성이 있으면 국회의 회의는 공개하지 않을 수 있다.|
15|라|01|X|국회의결에서 가부동수인 때에는 부결된 것으로 본다.|국회의결 가부동수 때 국회의장이 결정권을 가진다고 한 부분
15|마|01|X|국회의원은 10인 이상의 찬성으로 의안을 발의할 수 있다.|법률안 발의에 의원 20인 이상의 찬성이 필요하다고 한 부분
16|①|01|O|국민투표권은 국민이 국가의 특정 사안에 직접 결정권을 행사하는 참정권의 한 내용이다.|
16|②|01|O|헌법 제72조의 중요정책 국민투표는 국가안위에 관한 대통령의 구체적 정책에 대한 국민 승인절차이다.|
16|③|01|O|헌법개정 국민투표는 확정된 헌법개정안에 대하여 국민이 최종 승인 여부를 결정하는 절차이다.|
16|④|01|X|국민투표권자의 범위는 대통령선거권자 및 국회의원선거권자의 범위와 일치되어야 한다고 판단되었다.|국민투표권자 범위가 대통령선거권자·국회의원선거권자와 반드시 일치할 필요는 없다고 한 부분
16|⑤|01|O|국민투표권은 대한민국 국민의 자격이 있는 사람에게 반드시 인정되어야 하는 권리이다.|
17|①|01|O|대통령의 긴급재정경제명령은 고도의 정치적 결단에 의하여 발동되는 국가긴급권으로서 통치행위 성격을 가진다.|
17|①|02|O|대통령의 긴급재정경제명령이 국민의 기본권 침해와 직접 관련되면 헌법재판소 심판대상이 된다.|
17|②|01|O|비상계엄 선포나 확대가 국헌문란 목적 달성을 위하여 행하여진 경우 법원은 그 행위가 범죄행위인지 심사할 수 있다.|
17|③|01|O|남북정상회담 개최 자체는 고도의 정치적 성격을 가져 특별한 사정이 없으면 사법심사 대상이 되기 어렵다.|
17|③|02|O|남북정상회담 개최과정에서 필요한 신고나 승인 없이 북한 측에 사업권 대가를 송금한 행위 자체는 사법심사의 대상이 될 수 있다.|
17|④|01|X|국가긴급권은 본질적으로 일시적·잠정적으로만 행사되어야 한다는 시간적 한계를 가진다.|국가긴급권에 시간적 한계가 인정되지 않는다고 한 부분
17|④|02|O|국가긴급권은 위기상황의 직접 원인을 제거하는 데 필수불가결한 최소한도에서 행사되어야 한다.|
17|⑤|01|O|국군 해외파견결정은 국방과 외교에 관한 고도의 정치적 결단을 요하는 문제이다.|
17|⑤|02|O|국군 해외파견결정이 헌법과 법률 절차에 따라 이루어진 것이 명백하면 대통령과 국회의 판단은 존중되어야 한다.|
18|가|01|X|총리령안은 헌법 제89조의 국무회의 필수 심의사항으로 명시되어 있지 않다.|총리령안을 헌법 제89조의 국무회의 필수 심의사항으로 본 부분
18|나|01|X|부령안은 헌법 제89조의 국무회의 필수 심의사항으로 명시되어 있지 않다.|부령안을 헌법 제89조의 국무회의 필수 심의사항으로 본 부분
18|다|01|O|국회의 임시회 집회 요구는 헌법 제89조의 국무회의 심의사항이다.|
18|라|01|O|감형은 헌법 제89조의 국무회의 심의사항이다.|
18|마|01|O|대통령의 긴급재정경제처분은 헌법 제89조의 국무회의 심의사항이다.|
18|바|01|O|영전수여는 헌법 제89조의 국무회의 심의사항이다.|
18|사|01|O|각군참모총장의 임명은 헌법 제89조의 국무회의 심의사항이다.|
18|아|01|O|대사의 임명은 헌법 제89조의 국무회의 심의사항이다.|
19|가|01|X|자유선거의 원칙은 헌법에 명시되어 있지는 않지만 민주국가 선거제도에 내재하는 법원리이다.|자유선거의 원칙이 헌법에 명문으로 규정되어 있다고 본 부분
19|나|01|O|국회의원은 국가이익을 우선하여 양심에 따라 직무를 행한다고 헌법에 규정되어 있다.|
19|다|01|O|법률은 특별한 규정이 없으면 공포한 날부터 20일이 지나 효력을 발생한다고 헌법에 규정되어 있다.|
19|라|01|O|선거운동은 법률이 정하는 범위에서 하되 균등한 기회가 보장되어야 한다고 헌법에 규정되어 있다.|
19|마|01|O|국회의원은 법률이 정하는 직을 겸할 수 없다고 헌법에 규정되어 있다.|
19|바|01|O|국회나 그 위원회는 국무총리·국무위원 또는 정부위원의 출석과 답변을 요구할 수 있다고 헌법에 규정되어 있다.|
19|사|01|X|대법원장의 정치적 중립의무는 헌법에 명시되어 있지 않다.|대법원장의 정치적 중립의무가 헌법에 명문으로 규정되어 있다고 본 부분
19|아|01|X|국회는 국무총리 또는 국무위원 해임을 대통령에게 건의할 수 있지만 정부위원 해임건의권은 헌법에 명시되어 있지 않다.|국회가 정부위원에 대한 해임건의권을 헌법상 가진다고 본 부분
20|①|01|X|법률이 일반적 효력을 발생하기 전이라도 공포되어 있고 사실상 위험성이 이미 발생한 경우 예외적으로 현재성이 인정될 수 있다.|공포되었지만 시행 전인 법률은 현재성 요건 때문에 언제나 헌법소원을 청구할 수 없다고 한 부분
20|②|01|X|공권력의 불행사에 대한 헌법소원도 청구기간의 제한을 받는다.|공권력의 불행사에 대한 헌법소원이 청구기간 제한을 받지 않는다고 한 부분
20|③|01|X|공권력 작용에 단순히 간접적·사실적·경제적 이해관계만 있는 제3자에게는 자기관련성이 인정되지 않는다.|간접적·사실적·경제적 이해관계가 있는 제3자에게 자기관련성을 인정한 부분
20|④|01|X|법률조항이 하위규범의 시행을 예정하고 있으면 집행행위에는 입법행위도 포함되므로 법률의 직접성이 부인될 수 있다.|하위규범 시행이 예정되어 있어도 법률의 직접성이 인정된다고 한 부분
20|⑤|01|O|보충성 요건의 다른 권리구제절차는 공권력 행사 또는 불행사를 직접 대상으로 하여 그 효력을 다툴 수 있는 절차를 의미한다.|
20|⑤|02|O|보충성 요건의 다른 권리구제절차에는 사후적·보충적 구제수단인 손해배상청구나 손실보상청구가 포함되지 않는다.|
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
        raise ValueError("cannot locate 2015 constitution section")
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


def unit_labels(no: int) -> list[str]:
    return BOX_LABELS_BY_QUESTION.get(no, CHOICE_LABELS)


def split_box_units(block: str, labels: list[str]) -> dict[str, str]:
    first_by_label = {}
    last = labels[-1]
    first_choice_in_block = re.search(r"[①②③④⑤]", block)
    choice_limit = first_choice_in_block.start() if first_choice_in_block else len(block)
    cursor = 0
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\.")
        candidates = list(pattern.finditer(block, cursor, choice_limit))
        marker = None
        for candidate in candidates:
            immediately_repeated = block[candidate.end() : candidate.end() + len(label) + 1] == f"{label}."
            if not immediately_repeated:
                marker = candidate
                break
        if marker is None:
            raise ValueError(f"cannot split box statements: missing {label} in {labels}")
        first_by_label[label] = marker
        cursor = marker.end()
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label[last].end() :])
    choice_start = first_by_label[last].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in labels]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[labels[idx]] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = unit_labels(no)
        split = split_box_units(blocks[no], labels) if no in BOX_LABELS_BY_QUESTION else split_choice_units(blocks[no])
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
        qid = f"2015-g1-constitution-{no:02d}"
        labels = unit_labels(no)
        units = [{"unitId": f"{qid}-{LABEL_CODE[label]}", "unitType": "boxStatement" if no in BOX_LABELS_BY_QUESTION else "choice", "label": label, "rawStatement": raws[(no, label)], "originalVerdict": source_verdict(no, label)} for label in labels]
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
            items.append({"atomId": f"bupmusa-2015-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2015-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v011_2015_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2015-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
