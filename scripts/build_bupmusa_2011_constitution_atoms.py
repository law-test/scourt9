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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2011" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2011_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2011"
TEXT_DIR = PRIVATE_ROOT / "text" / "2011"
RAW_PDF_PATH = RAW_DIR / "2011_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2011_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2011_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2011_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2011_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2011_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2011_bupmusa_1st"
YEAR = 2011
ROUND = 17
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 100
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS_BY_QUESTION = {}
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
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "정부조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정부조직법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "2011 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2011/53136038"},
    {"title": "2011 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2011/95553"},
    {"title": "제17회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?module=file&act=procFileDownload&file_srl=95558&sid=19adea924875614072d00685057d26c3"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "④",
    3: "③",
    4: "③",
    5: "③",
    6: "①",
    7: "⑤",
    8: "③",
    9: "②",
    10: "③",
    11: "④",
    12: "②",
    13: "③",
    14: "⑤",
    15: "①",
    16: "⑤",
    17: "③",
    18: "②",
    19: "①",
    20: "⑤",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    6: "single-best-true",
    12: "single-best-true",
    17: "single-best-true",
    18: "single-best-true",
})

FALSE_LABELS = {
    1: {"⑤"},
    2: {"④"},
    3: {"③"},
    4: {"③"},
    5: {"③"},
    6: {"②", "③", "④", "⑤"},
    7: {"⑤"},
    8: {"③"},
    9: {"②"},
    10: {"③"},
    11: {"④"},
    12: {"①", "③", "④", "⑤"},
    13: {"③"},
    14: {"⑤"},
    15: {"①"},
    16: {"⑤"},
    17: {"①", "②", "④", "⑤"},
    18: {"①", "③", "④", "⑤"},
    19: {"①"},
    20: {"⑤"},
}

TOPICS = {
    1: "노동3권",
    2: "공무담임권",
    3: "집회의 자유",
    4: "언론·출판의 자유",
    5: "탄핵제도",
    6: "법원과 법관",
    7: "선거권과 피선거권",
    8: "죄형법정주의 명확성",
    9: "헌법재판소 절차",
    10: "행정입법",
    11: "지방자치제도",
    12: "헌법 전문",
    13: "헌법소원 인용결정",
    14: "국회 의사절차",
    15: "사생활의 비밀과 자유",
    16: "행정부와 감사원",
    17: "국회의원 자격상실",
    18: "헌법소원 청구권자",
    19: "정당제도",
    20: "제헌헌법",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    1: ("조문+판례", "대한민국헌법 제33조 및 노동3권 관련 헌법재판소 결정례", "근로자의 단결권, 소극적 단결권, 공무원 노동3권 제한의 입법형성권을 판례 기준으로 정리한다."),
    2: ("판례", "대한민국헌법 제25조 및 공무담임권 관련 헌법재판소 결정례", "공무담임권의 보호영역과 지방자치단체장 권한대행, 경찰공무원 당연퇴직 규정의 위헌 여부를 판례 기준으로 정리한다."),
    3: ("조문+판례", "대한민국헌법 제21조 및 집회의 자유 관련 결정례", "집회의 자유의 기능, 보호대상, 사전신고제와 야간옥외집회 금지 조항의 헌법적 한계를 판례 기준으로 정리한다."),
    4: ("판례", "대한민국헌법 제21조 및 언론·출판의 자유 관련 결정례", "검열 개념, 표현매체의 자유, 익명표현과 인터넷 선거게시판 표현을 판례 기준으로 정리한다."),
    5: ("조문", "대한민국헌법 제65조 및 헌법재판소법 탄핵심판 규정", "탄핵결정의 효과, 탄핵소추 절차, 심판절차 정지와 구두변론 원칙을 조문 기준으로 정리한다."),
    6: ("조문+판례", "대한민국헌법 제101조, 제103조, 제106조 및 법원조직법", "심급제도, 명령·규칙 심사, 대법관 연임, 법관 신분보장을 조문과 판례 기준으로 정리한다."),
    7: ("조문", "공직선거법 선거권·피선거권 규정", "대통령·국회의원 선거권과 피선거권, 정치자금범죄와 금고 이상 형에 따른 제한을 조문 기준으로 정리한다."),
    8: ("판례", "대한민국헌법 제12조, 제13조 및 죄형법정주의 명확성 결정례", "처벌법규 명확성원칙의 의미와 보충적 해석 가능성을 판례 기준으로 정리한다."),
    9: ("조문+판례", "헌법재판소법 제25조, 제36조, 제39조, 제72조 및 재심 관련 결정례", "헌법재판소 심판절차의 대리, 의견표시, 일사부재리, 재심, 지정재판부를 조문과 판례 기준으로 정리한다."),
    10: ("조문+판례", "대한민국헌법 제75조, 제95조 및 행정입법 관련 결정례", "법령보충적 행정규칙, 정관 위임, 대통령령·총리령 절차와 명령·규칙 헌법소원을 판례 기준으로 정리한다."),
    11: ("조문+판례", "대한민국헌법 제117조, 제118조 및 지방자치법", "지방자치 보장 내용, 조례안 이송·재의결, 지방의회 의장선거의 처분성을 조문과 판례 기준으로 정리한다."),
    12: ("조문", "대한민국헌법 전문 및 제9조", "헌법 전문에 포함된 표현과 헌법 본문에 규정된 민족문화 창달 조항을 구별한다."),
    13: ("조문", "헌법재판소법 제75조", "헌법소원 인용결정의 기속력, 공권력 불행사 인용, 위헌법률 선고와 공권력 취소 가능성을 조문 기준으로 정리한다."),
    14: ("조문", "대한민국헌법 제50조 및 국회법", "국회 본회의 개의, 의장단 선거, 예산안 수정동의, 해임건의안 표결, 비공개회의 요건을 조문 기준으로 정리한다."),
    15: ("판례", "대한민국헌법 제17조 및 사생활·개인정보 관련 판례", "국가기관 보도자료 명예훼손, 개인정보 자기결정권, 반론보도청구와 금융정보제공동의 규정을 판례 기준으로 정리한다."),
    16: ("조문", "대한민국헌법 제88조, 정부조직법 및 감사원법", "감사원장 직무대행, 국무총리의 명령·처분 중지·취소, 국무회의와 감사위원회 의결정족수를 조문 기준으로 정리한다."),
    17: ("조문", "대한민국헌법 제43조, 제64조, 국회법 및 공직선거법", "국회의원 사직, 당선무효, 국무위원 겸직, 제명, 비례대표 당적변경에 따른 자격상실 여부를 조문 기준으로 정리한다."),
    18: ("판례", "헌법재판소법 제68조 및 헌법소원 청구권자 관련 결정례", "외국인, 학교, 정당, 노동조합, 대통령 개인의 기본권 주체성과 헌법소원 청구권자성을 판례 기준으로 정리한다."),
    19: ("조문", "대한민국헌법 제8조 및 헌법재판소법 제55조", "정당의 자유·복수정당제·민주적 조직과 정당해산심판 관할을 조문 기준으로 정리한다."),
    20: ("헌법사", "1948년 제헌헌법", "제헌헌법의 대통령 선출, 지방자치, 국무원, 형사보상, 헌법위원회와 탄핵재판소 제도를 구별한다."),
})

ATOM_ROWS = """
1|①|01|O|단결권은 사회적 보호기능을 담당하는 자유권 또는 사회권적 성격을 띤 자유권의 성격을 가진다.|
1|②|01|O|헌법 제33조의 근로자 단결권은 단결할 자유를 의미하고, 소극적 단결권은 행복추구권에서 파생되는 일반적 행동의 자유 또는 결사의 자유에서 근거를 찾을 수 있다.|
1|③|01|O|국회는 공무원인 근로자에게 노동3권을 인정할지와 인정 범위에 관하여 광범위한 입법형성의 자유를 가진다.|
1|④|01|O|공무원노동조합의 설립 최소단위를 행정부로 정하여 특정 부처만의 노동조합 결성을 제한한 것은 단결권 제한으로 보기 어렵다고 판단되었다.|
1|⑤|01|X|소방공무원을 공무원노동조합 가입대상에서 제외한 규정은 소방공무원의 단결권을 침해하지 않는다고 판단되었다.|소방공무원의 노동조합 가입대상 제외가 단결권을 침해하는 위헌적 법률이라고 한 부분
2|①|01|O|공무담임권의 보호영역에는 공직취임기회의 자의적 배제뿐 아니라 공무원 신분의 부당한 박탈이나 권한의 부당한 정지도 포함된다.|
2|②|01|O|공무원이 특정 장소에서 근무하거나 특정 보직을 받아 근무하는 공무수행의 자유까지 공무담임권의 보호영역에 포함된다고 보기는 어렵다.|
2|③|01|O|승진시험 응시제한이나 승진기회 보장은 공직신분 유지나 업무수행에 직접 영향을 주지 않는 내부승진인사 문제로서 공무담임권 보호영역에 포함된다고 보기 어렵다.|
2|④|01|X|지방자치단체장이 금고 이상의 형을 선고받았으나 확정되지 않은 경우 부단체장이 권한을 대행하도록 한 규정은 공무담임권을 침해한다고 판단되었다.|금고 이상의 형이 확정되지 않은 지방자치단체장의 권한대행 규정이 공무담임권을 침해하지 않는다고 한 부분
2|⑤|01|O|경찰공무원이 자격정지 이상의 형의 선고유예를 받은 경우 당연퇴직하도록 한 규정은 공무담임권을 침해한다고 판단되었다.|
3|①|01|O|집회의 자유는 개인의 자기결정과 인격발현에 기여하고, 표현의 자유와 함께 민주적 공동체에 필수적인 기본권이다.|
3|②|01|O|집회의 자유로 보호되는 집회는 평화적 또는 비폭력적 집회이다.|
3|③|01|X|옥외집회 사전신고제도는 협력의무를 부과하는 것으로서 그 자체가 헌법상 금지되는 사전허가제에 해당하지는 않는다.|옥외집회 사전신고제도가 사전허가금지에 위반된다고 한 부분
3|④|01|O|야간옥외집회 일반금지와 관할 경찰서장의 예외적 허용을 결합한 규정은 야간옥외집회 허가제로서 헌법 제21조 제2항에 위반된다고 판단되었다.|
3|⑤|01|O|위헌인 야간옥외집회 금지 조항을 전제로 한 처벌조항도 헌법에 위반된다고 판단되었다.|
4|①|01|O|헌법 제21조의 검열은 행정권이 발표 전에 사상이나 의견의 내용을 심사·선별하여 허가받지 않은 발표를 금지하는 제도를 뜻한다.|
4|②|01|O|언론·출판의 자유 중 의사표현·전파의 자유에서 의사표현 또는 전파의 매개체는 원칙적으로 어떠한 형태도 가능하다.|
4|③|01|X|인터넷언론사의 공개 게시판이나 대화방에 정당·후보자에 대한 지지·반대 글을 게시하는 행위가 곧바로 양심의 자유로 보호되는 것은 아니다.|인터넷언론사의 공개 게시판 정치적 게시글이 양심의 자유로 보호된다고 한 부분
4|④|01|O|표현의 자유에는 익명 또는 가명으로 자신의 사상이나 견해를 표명하고 전파할 자유도 포함된다.|
4|⑤|01|O|선거기간 중 인터넷언론사의 선거 관련 게시판과 대화방은 정치적 의사 형성·전파 매체로서 언론·출판의 자유에 의하여 보호된다.|
5|①|01|O|탄핵결정은 피청구인의 민사상 또는 형사상 책임을 면제하지 않는다.|
5|②|01|O|탄핵소추 발의가 있으면 국회의장은 발의 후 처음 개의하는 본회의에 보고하고, 본회의는 의결로 법제사법위원회에 회부하여 조사하게 할 수 있다.|
5|③|01|X|탄핵심판청구와 동일한 사유로 형사소송이 진행 중이면 헌법재판소 재판부는 심판절차를 정지할 수 있지만 반드시 정지하여야 하는 것은 아니다.|동일 사유의 형사소송 계속 중 탄핵심판절차를 반드시 정지하여야 한다고 한 부분
5|④|01|O|탄핵소추의결서가 송달되면 피소추자의 권한행사는 정지되고, 임명권자는 피소추자의 사직원을 접수하거나 해임할 수 없다.|
5|⑤|01|O|탄핵심판은 구두변론에 의한다.|
6|①|01|O|심급제도를 몇 개의 심급으로 형성할지는 헌법에 직접 규정되어 있지 않으므로 입법자의 광범위한 형성권에 맡겨져 있다.|
6|②|01|X|명령·규칙 또는 처분의 위헌·위법 여부가 재판의 전제가 되면 대법원뿐 아니라 하급심 법원도 이를 심사할 수 있다.|명령·규칙 또는 처분의 위헌·위법 판단권한이 대법원에만 있다고 한 부분
6|③|01|X|법원 예산 편성에서 사법부의 독립성과 자율성을 존중하여야 한다는 규정만으로 법원의 독자적 예산편성권이 인정되는 것은 아니다.|현행 법률상 법원의 독자적 예산편성권이 인정된다고 한 부분
6|④|01|X|대법관은 법률이 정하는 바에 따라 연임할 수 있다.|현행 헌법상 대법관이 연임할 수 없다고 한 부분
6|⑤|01|X|법관은 탄핵 또는 금고 이상의 형의 선고에 의하지 아니하고는 파면되지 않는다.|대법원장이 법관징계위원회의 해임결정을 거쳐 법관을 해임할 수 있다고 한 부분
7|①|01|O|2011년 출제 당시 19세 이상의 국민은 대통령 및 국회의원 선거권이 있었다.|
7|②|01|O|25세 이상의 국민은 국회의원 피선거권이 있다.|
7|③|01|O|정치자금부정수수죄로 일정한 벌금형 이상이 확정된 사람은 공직선거법이 정한 기간 동안 선거권이 제한될 수 있다.|
7|④|01|O|선거일 현재 금고 이상의 형을 선고받고 그 형이 실효되지 않은 사람은 피선거권이 없다.|
7|⑤|01|X|대통령 피선거권은 연령요건 외에도 공직선거법상 일정 기간 국내 거주요건을 필요로 한다.|공직선거법이 대통령 피선거권에 국내 거주요건을 규정하지 않는다고 한 부분
8|①|01|O|죄형법정주의의 명확성원칙은 처벌대상 행위와 형벌을 누구나 예견하고 자신의 행위를 결정할 수 있도록 구성요건을 명확히 규정할 것을 요구한다.|
8|②|01|O|형벌법규가 애매하거나 추상적이면 범죄 성립 여부가 법관의 자의적 해석에 맡겨져 죄형법정주의의 법치주의적 기능이 실현될 수 없다.|
8|③|01|X|처벌법규의 구성요건이 다소 광범위하여 법관의 보충적 해석이 필요한 개념을 사용하였다는 사정만으로 명확성원칙에 배치되는 것은 아니다.|보충적 해석이 필요한 처벌법규 개념은 명확성원칙에 배치된다고 한 부분
8|④|01|O|건전한 상식과 통상적 법감정을 가진 사람이 적용대상자와 금지행위를 충분히 알 수 있으면 죄형법정주의의 명확성원칙에 위배되지 않는다.|
8|⑤|01|O|형벌법규의 내용이 불명확하면 국민이 금지행위를 알 수 없어 법 준수가 어려워진다.|
9|①|01|O|헌법재판소법 제68조 제2항 헌법소원에서 당사자와 심판대상이 같더라도 당해 사건이 다르면 일사부재리 원칙의 동일 사건이 아니다.|
9|②|01|X|헌법재판소 심판절차에서 당사자인 국가기관 또는 지방자치단체는 변호사나 변호사 자격이 있는 소속 직원을 대리인으로 선임할 수 있다.|국가기관 또는 지방자치단체가 반드시 변호사나 변호사 자격이 있는 소속 직원을 대리인으로 선임하여야 한다고 한 부분
9|③|01|O|헌법재판에서 심판에 관여한 재판관은 결정서에 의견을 표시하여야 한다.|
9|④|01|O|공권력 작용에 대한 권리구제형 헌법소원심판절차에서는 판단유탈도 재심사유로 허용될 수 있다.|
9|⑤|01|O|헌법재판소장은 재판관 3명으로 구성되는 지정재판부를 두어 헌법소원심판의 사전심사를 담당하게 할 수 있다.|
10|①|01|O|법령보충적 행정규칙은 상위법령과 결합하여 상위법령의 일부가 되는 한도에서 대외적 구속력이 발생하고, 행정규칙 자체가 독자적으로 대외적 구속력을 가지는 것은 아니다.|
10|②|01|O|포괄위임금지원칙은 법률이 정관에 자치법적 사항을 위임한 경우에는 원칙적으로 적용되지 않는다.|
10|③|01|X|대통령령은 국무회의 심의를 거치지만 총리령은 국무회의 심의를 거치지 않는다.|대통령령과 총리령이 모두 국무회의 심의를 거쳐야 한다고 한 부분
10|④|01|O|대통령령의 내용이 헌법에 위반되더라도 그 사정만으로 정당하고 적법하게 입법권을 위임한 수권법률조항이 위헌이 되는 것은 아니다.|
10|⑤|01|O|행정부에서 제정한 명령·규칙도 별도의 집행행위 없이 직접 기본권을 침해하면 헌법소원심판의 대상이 될 수 있다.|
11|①|01|O|지방자치의 본질적 내용은 자치단체의 보장, 자치기능의 보장, 자치사무의 보장이며, 헌법상 자치단체의 보장은 단체자치와 주민자치를 포괄한다.|
11|②|01|O|일정 지역의 시·군을 모두 폐지하여 지방자치단체의 중층구조를 단층화하는 것이 곧바로 헌법상 지방자치제도 보장에 위배되는 것은 아니다.|
11|③|01|O|조례안이 지방의회에서 의결되면 의장은 의결된 날부터 5일 이내에 지방자치단체의 장에게 이송하여야 한다.|
11|④|01|X|지방자치단체장이 재의를 요구한 조례안은 재적의원 과반수 출석과 출석의원 3분의 2 이상의 찬성으로 전과 같이 의결하면 조례로 확정된다.|재의 요구 조례안이 출석의원 과반수 찬성으로 확정된다고 한 부분
11|⑤|01|O|지방의회 의장선거는 행정처분의 일종으로서 항고소송의 대상이 된다.|
12|①|01|X|4·19 민주이념의 계승은 헌법 전문에 포함되어 있다.|4·19 민주이념의 계승이 헌법 전문에 포함되어 있지 않다고 본 부분
12|②|01|O|민족문화의 창달에 노력한다는 내용은 헌법 전문이 아니라 헌법 제9조에 규정되어 있다.|
12|③|01|X|자유민주적 기본질서의 확립은 헌법 전문에 포함되어 있다.|자유민주적 기본질서의 확립이 헌법 전문에 포함되어 있지 않다고 본 부분
12|④|01|X|항구적인 세계평화와 인류공영에 이바지한다는 세계평화주의는 헌법 전문에 포함되어 있다.|세계평화주의가 헌법 전문에 포함되어 있지 않다고 본 부분
12|⑤|01|X|헌법 개정의 주체가 국민이라는 내용은 헌법 전문에 포함되어 있다.|헌법 개정의 주체가 국민이라는 내용이 헌법 전문에 포함되어 있지 않다고 본 부분
13|①|01|O|헌법소원의 인용결정은 모든 국가기관과 지방자치단체를 기속한다.|
13|②|01|O|헌법재판소가 공권력 불행사에 대한 헌법소원을 인용하면 피청구인은 결정취지에 따라 새로운 처분을 하여야 한다.|
13|③|01|X|헌법소원을 인용할 때 공권력 행사가 위헌인 법률조항에 기인한 것이라고 인정되면 헌법재판소는 인용결정에서 해당 법률조항의 위헌을 선고할 수 있다.|공권력 행사가 위헌 법률조항에 기인하여도 인용결정에서 해당 법률조항의 위헌을 선고할 수 없다고 한 부분
13|④|01|O|헌법소원 인용결정에는 재판관 6명 이상의 찬성이 필요하다.|
13|⑤|01|O|헌법소원을 인용하는 경우 헌법재판소는 기본권 침해의 원인이 된 공권력의 행사를 취소할 수 있다.|
14|①|01|O|국회 본회의는 재적의원 5분의 1 이상의 출석으로 개의한다.|
14|②|01|O|국회의장과 부의장은 국회에서 무기명투표로 선거하고 재적의원 과반수의 득표로 당선된다.|
14|③|01|O|예산안에 대한 수정동의는 의원 50명 이상의 찬성이 있어야 한다.|
14|④|01|O|국무위원 해임건의안이 발의되면 의장은 처음 개의하는 본회의에 보고하고, 보고된 때부터 24시간 이후 72시간 이내에 무기명투표로 표결한다.|
14|⑤|01|X|국회 본회의 비공개는 의장 제의 또는 의원 10명 이상의 연서 동의와 출석의원 과반수 찬성이 있거나 의장이 국가안전보장을 위하여 필요하다고 인정할 때 가능하다.|의원 20명 이상 연서 동의에 의한 본회의 의결만으로 본회의를 비공개할 수 있다고 한 부분
15|①|01|X|국가기관이 보도자료 제공 등으로 실명을 공개하여 명예를 훼손한 경우에도 적시 사실이 진실이라고 믿을 상당한 이유가 있으면 위법성이 조각될 수 있다.|국가기관이 진실이라고 믿을 상당한 이유가 있어도 위법성이 인정된다고 한 부분
15|②|01|O|개인정보 자기결정권의 보호대상은 내밀한 영역의 정보에 한정되지 않고 공적 생활에서 형성되었거나 이미 공개된 개인정보도 포함한다.|
15|③|01|O|본인의 승낙을 받았더라도 승낙 범위를 넘어 예상과 다른 목적이나 방법으로 사생활 관련 사항을 공개하면 위법할 수 있다.|
15|④|01|O|사실적 주장에 관한 언론보도로 피해를 입은 사람은 보도내용의 진실 여부와 관계없이 반론보도를 청구할 수 있다.|
15|⑤|01|O|국민기초생활보장 급여 신청 시 금융거래정보자료 제공동의서를 제출하게 하는 것은 개인정보 자기결정권을 침해한다고 볼 수 없다고 판단되었다.|
16|①|01|O|감사원장이 사고로 직무를 수행할 수 없을 때에는 최장기간 재직한 감사위원이 그 직무를 대행한다.|
16|②|01|O|국무총리는 중앙행정기관 장의 명령이나 처분이 위법 또는 부당하다고 인정되면 대통령의 승인을 받아 이를 중지 또는 취소할 수 있다.|
16|③|01|O|헌법은 감사원의 규칙제정권에 관한 규정을 직접 두고 있지 않다.|
16|④|01|O|국무회의는 구성원 과반수의 출석으로 개의하고 출석구성원 3분의 2 이상의 찬성으로 의결한다.|
16|⑤|01|X|감사위원회 의사는 재적감사위원 과반수의 찬성으로 의결한다.|감사위원회가 재적감사위원 과반수 출석과 출석감사위원 과반수 찬성으로 의결한다고 한 부분
17|①|01|X|국회 폐회 중 국회의장이 국회의원의 사직을 허가하면 국회의원 자격은 소멸한다.|국회 폐회 중 국회의장이 사직을 허가하여도 국회의원 자격이 소멸하지 않는다고 본 부분
17|②|01|X|국회의원 당선인이 해당 선거에서 공직선거법상 죄 또는 정치자금법 제49조의 죄로 징역 또는 100만 원 이상의 벌금형이 확정되면 당선은 무효가 된다.|선거범죄 등으로 당선무효형이 확정되어도 국회의원 자격이 소멸하지 않는다고 본 부분
17|③|01|O|국회의원이 국무위원으로 임명되어 취임하더라도 그 사정만으로 국회의원 자격이 소멸하지 않는다.|
17|④|01|X|국회가 재적의원 3분의 2 이상의 찬성으로 국회의원을 제명하면 국회의원 자격은 소멸한다.|국회의원이 제명되어도 자격이 소멸하지 않는다고 본 부분
17|⑤|01|X|비례대표국회의원이 소속 정당의 합당·해산 또는 제명 외의 사유로 당적을 이탈·변경하면 퇴직된다.|비례대표국회의원이 당적을 이탈·변경해도 자격이 소멸하지 않는다고 본 부분
18|①|01|X|외국인도 인간의 존엄과 가치 및 행복추구권 침해를 주장하는 범위에서는 헌법소원 청구권자가 될 수 있다.|인간의 존엄과 행복추구권 침해를 주장하는 외국인이 헌법소원 청구권자로 인정되지 않는다고 본 부분
18|②|01|O|중·고등학교는 학교법인에 대한 과세처분의 위헌 여부를 다툴 헌법소원 청구권자로 인정되지 않는다.|
18|③|01|X|정당은 시·도의회의원선거와 관련하여 일정한 경우 헌법소원 청구권자로 인정될 수 있다.|시·도의회의원선거에서 정당이 헌법소원 청구권자로 인정되지 않는다고 본 부분
18|④|01|X|노동조합은 노동단체의 정치자금 기부를 금지한 법률의 위헌성을 다툴 헌법소원 청구권자로 인정될 수 있다.|정치자금 기부금지 법률의 위헌성을 다투는 노동조합이 헌법소원 청구권자로 인정되지 않는다고 본 부분
18|⑤|01|X|대통령도 대통령 지위가 아니라 개인의 표현의 자유 제한을 주장하는 경우 헌법소원 청구권자로 인정될 수 있다.|개인으로서 표현의 자유 제한을 주장하는 대통령이 헌법소원 청구권자로 인정되지 않는다고 본 부분
19|①|01|X|정당의 목적이나 활동이 민주적 기본질서에 위배될 때 정부는 헌법재판소에 정당해산심판을 청구할 수 있다.|정당해산 제소기관을 대법원이라고 한 부분
19|②|01|O|정당의 설립은 자유이다.|
19|③|01|O|복수정당제는 헌법상 보장된다.|
19|④|01|O|정당은 목적, 조직과 활동이 민주적이어야 하며 국민의 정치적 의사형성에 참여하는 데 필요한 조직을 가져야 한다.|
19|⑤|01|O|국가는 법률이 정하는 바에 따라 정당운영에 필요한 자금을 보조할 수 있다.|
20|①|01|O|제헌헌법상 대통령의 임기는 4년이고 국회에서 간접선거로 선출되었다.|
20|②|01|O|제헌헌법은 지방자치에 관한 규정을 두었다.|
20|③|01|O|제헌헌법은 대통령, 국무총리, 국무위원으로 조직되는 국무원이 대통령 권한에 속한 중요 국책을 의결하도록 하였다.|
20|④|01|O|제헌헌법은 형사피고인으로 구금되었던 자가 무죄판결을 받으면 법률이 정하는 바에 따라 국가에 보상을 청구할 수 있도록 하였다.|
20|⑤|01|X|제헌헌법에서 위헌법률심사는 헌법위원회가 담당하였고 탄핵심판은 탄핵재판소가 담당하였다.|제헌헌법상 헌법위원회가 위헌법률심사와 탄핵심판을 모두 담당하였다고 한 부분
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
    header = re.search(r"【\s*헌\s*법\s*20문\s*】", text)
    if not header:
        raise ValueError("cannot locate 2011 constitution section")
    section = text[header.start():]
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
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*상\s*법|\s*【\s*제1과목", statement)[0]
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
        qid = f"2011-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2011-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2011-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v015_2011_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2011-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
