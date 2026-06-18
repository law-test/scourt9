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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2010" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2010_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2010"
TEXT_DIR = PRIVATE_ROOT / "text" / "2010"
RAW_PDF_PATH = RAW_DIR / "2010_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2010_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2010_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2010_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2010_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2010_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2010_bupmusa_1st"
YEAR = 2010
ROUND = 16
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
    {"title": "국적법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국적법"},
    {"title": "국가인권위원회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국가인권위원회법"},
    {"title": "상고심절차에 관한 특례법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상고심절차에관한특례법"},
    {"title": "소액사건심판법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/소액사건심판법"},
    {"title": "2010 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2010/51571570"},
    {"title": "2010 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2010/94175"},
    {"title": "제16회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?module=file&act=procFileDownload&file_srl=94176&sid=ed8bb1c917166e37b2f91ba53bba78b0"},
]

OFFICIAL_ANSWERS = {
    1: "①",
    2: "②",
    3: "④",
    4: "⑤",
    5: "①",
    6: "⑤",
    7: "②",
    8: "⑤",
    9: "③",
    10: "③",
    11: "③",
    12: "③",
    13: "③",
    14: "②",
    15: "③",
    16: "③",
    17: "④",
    18: "①",
    19: "⑤",
    20: "④",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    5: "single-best-true",
    8: "single-best-true",
    11: "single-best-true",
    12: "single-best-true",
    14: "single-best-true",
    18: "single-best-true",
})

FALSE_LABELS = {
    1: {"①"},
    2: {"②"},
    3: {"④"},
    4: {"⑤"},
    5: {"②", "③", "④", "⑤"},
    6: {"⑤"},
    7: {"②"},
    8: {"①", "②", "③", "④"},
    9: {"③"},
    10: {"③"},
    11: {"①", "②", "④", "⑤"},
    12: {"①", "②", "④", "⑤"},
    13: {"③"},
    14: {"①", "③", "④", "⑤"},
    15: {"③"},
    16: {"③"},
    17: {"④"},
    18: {"②", "③", "④", "⑤"},
    19: {"⑤"},
    20: {"④"},
}

TOPICS = {
    1: "조세법률주의",
    2: "재판청구권",
    3: "직업공무원제도",
    4: "검열금지",
    5: "국적법",
    6: "위헌법률심판",
    7: "열거되지 않은 기본권",
    8: "국회 의사절차",
    9: "정당제도와 정당설립의 자유",
    10: "합헌적 법률해석",
    11: "종교의 자유와 정교분리",
    12: "국가인권위원회",
    13: "국회 입법절차",
    14: "헌법재판 절차",
    15: "헌법소원 청구권자",
    16: "개인정보 자기결정권",
    17: "과잉금지원칙",
    18: "양심의 자유",
    19: "국무회의와 행정부",
    20: "대법원 단심 사건",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    1: ("조문+판례", "대한민국헌법 제38조, 제59조 및 조세법률주의 결정례", "조세법률주의의 내용, 조세감면, 위임입법과 조례에 의한 지방세 사항을 판례 기준으로 정리한다."),
    2: ("판례", "대한민국헌법 제27조 및 재판청구권 관련 결정례", "국민참여재판, 군사법원 관할, 심리불속행, 소액사건 상고이유 제한을 판례 기준으로 정리한다."),
    3: ("조문+판례", "대한민국헌법 제7조 및 직업공무원제도 결정례", "직업공무원제도의 제도보장, 정치적 중립성, 직제개폐에 따른 직권면직을 판례 기준으로 정리한다."),
    4: ("판례", "대한민국헌법 제21조 및 검열금지 결정례", "검열의 의미, 영화등급분류, 출판금지가처분, 정보삭제명령과 등급분류보류 제도를 판례 기준으로 정리한다."),
    5: ("조문", "2010년 출제 당시 국적법", "복수국적자의 국적선택·외국국적 포기, 귀화요건, 혼인귀화와 출생에 의한 국적취득을 출제 당시 조문 기준으로 정리한다."),
    6: ("조문+판례", "헌법재판소법 제41조 및 위헌법률심판 결정례", "위헌법률심판 대상, 폐지 법률, 한정위헌 청구, 조약, 재판전제성을 판례 기준으로 정리한다."),
    7: ("판례", "대한민국헌법 제10조, 제37조 제1항 및 열거되지 않은 기본권 결정례", "헌법에 열거되지 않은 기본권으로 인정되는 자유와 인정되지 않는 주장을 판례 기준으로 정리한다."),
    8: ("조문+판례", "대한민국헌법 제49조, 제50조, 제53조 및 국회법", "법률안 확정과 공포, 일사부재의, 회의공개, 가부동수와 재의요구 제한을 조문 기준으로 정리한다."),
    9: ("조문+판례", "대한민국헌법 제8조, 정당법 및 정치자금 관련 결정례", "정당 성립, 교원 정당활동 제한, 정당설립의 자유, 정책연구위원 배정, 후원금 국고귀속을 조문과 판례 기준으로 정리한다."),
    10: ("판례", "합헌적 법률해석 관련 헌법재판소 결정례", "합헌적 법률해석의 의미, 한계, 법원 적용가능성, 법질서 통일과 입법권 존중 기능을 판례 기준으로 정리한다."),
    11: ("조문+판례", "대한민국헌법 제20조 및 종교의 자유·정교분리 결정례", "국교금지, 시험일, 문화요소화된 종교행사 지원, 종교학교 인가, 양심적 병역거부를 판례 기준으로 정리한다."),
    12: ("조문+판례", "국가인권위원회법 및 국가인권위원회 관련 결정례", "국가인권위원회 구성, 의견제출, 조사대상, 인권위원 선거출마 제한, 진정대상 기본권을 조문과 판례 기준으로 정리한다."),
    13: ("조문", "대한민국헌법 제52조, 제89조 및 국회법", "정부 법률안 제출권, 국무회의 심의, 국회의원 표결, 심의·표결권, 의장의 토론참가 제한을 조문 기준으로 정리한다."),
    14: ("조문+판례", "헌법재판소법 제25조, 제32조, 제36조, 제40조, 제57조, 제65조 및 가처분 결정례", "헌법재판 대리, 의견표시, 권한쟁의 결정, 가처분, 심리방식을 조문과 판례 기준으로 정리한다."),
    15: ("판례", "헌법재판소법 제68조 및 헌법소원 청구권자 관련 결정례", "기본권능력, 대통령·국회의원·비법인사단·외국인의 헌법소원 청구권자성을 판례 기준으로 정리한다."),
    16: ("판례", "개인정보 자기결정권 관련 헌법재판소 결정례", "개인정보 자기결정권의 보호대상, 내용, 교육정보시스템, 열손가락 지문날인, 헌법상 근거를 판례 기준으로 정리한다."),
    17: ("조문+판례", "대한민국헌법 제37조 제2항 및 과잉금지원칙 결정례", "과잉금지원칙의 근거와 목적정당성, 수단적정성, 피해최소성, 법익균형성을 판례 기준으로 정리한다."),
    18: ("판례", "대한민국헌법 제19조 및 양심의 자유 결정례", "사죄문 제출명령, 음주측정거부 면허취소, 양심적 병역거부 처벌, 법위반사실 공표명령, 인터넷 실명확인을 판례 기준으로 정리한다."),
    19: ("조문", "대한민국헌법 제88조, 제89조, 제82조, 제94조, 제95조", "국무회의 필수기관성, 영전수여 심의, 행정각부 장 임명, 부서, 총리령·부령 발령권을 조문 기준으로 정리한다."),
    20: ("조문", "공직선거법, 법관징계법, 해양사고의 조사 및 심판에 관한 법률, 독점규제 및 공정거래에 관한 법률", "대법원이 단심으로 처리하는 선거소송·법관징계·해양안전심판 재결 소송과 공정거래위원회 처분 불복 소송을 조문 기준으로 정리한다."),
})

ATOM_ROWS = """
1|①|01|X|조세법규는 과세요건과 조세감면요건을 막론하고 특별한 사정이 없는 한 엄격하게 해석하여야 하며, 합리적 이유가 있다는 명목의 유추해석이나 확장해석은 허용되지 않는다.|조세법규의 유추 또는 확장해석이 합리적 이유가 있으면 허용된다고 한 부분
1|②|01|O|조세법률주의의 핵심 내용은 과세요건법정주의와 과세요건명확주의이다.|
1|③|01|O|조세의 감면에도 조세법률주의가 적용된다.|
1|④|01|O|조세입법에서도 특별한 사정이 있으면 법률로 정하여야 할 사항을 구체적 범위를 정하여 행정입법에 위임할 수 있다.|
1|⑤|01|O|지방세법이 정하는 범위 안에서 지방세의 세목, 과세객체, 과세표준, 세율 등에 관한 사항을 조례로 정하는 것은 조세법률주의에 위배되지 않는다.|
2|①|01|O|국민참여재판에서 배심원이 사실인정, 법령적용, 형의 양정에 관하여 법관에게 의견을 제시하도록 한 것은 법관에 의한 재판을 받을 권리를 침해하지 않는다고 판단되었다.|
2|②|01|X|국민참여재판을 받을 권리는 헌법상 재판청구권으로 직접 보호되는 기본권이라고 볼 수 없다.|국민참여재판을 받을 권리가 헌법상 재판청구권으로 보호된다고 한 부분
2|③|01|O|현역병 입대 전에 저지른 범죄에 대한 군사법원의 재판권을 정한 규정은 현역병의 재판청구권을 침해한다고 볼 수 없다고 판단되었다.|
2|④|01|O|심리불속행재판의 판결이유를 생략할 수 있도록 한 규정은 재판청구권을 침해한다고 볼 수 없다고 판단되었다.|
2|⑤|01|O|소액사건의 상고이유를 제한한 규정은 재판청구권을 침해한다고 볼 수 없다고 판단되었다.|
3|①|01|O|직업공무원제도는 헌법과 법률에 따라 공무원의 신분이 보장되는 공직구조에 관한 제도이다.|
3|②|01|O|직업공무원제도는 공무원의 신분과 정치적 중립성을 보장하여 공무원이 국민 전체에 대한 봉사자로서 법에 따라 소임을 다하도록 하는 제도이다.|
3|③|01|O|직업공무원제도는 기본권과 구별되지만 헌법상 제도보장으로 인정된 이상 입법자가 법률로 폐지할 수 없다.|
3|④|01|X|직제개폐로 폐직된 때를 공무원 직권면직 사유로 정하는 것은 그 사정만으로 직업공무원제도에 반하지 않는다.|직제개폐로 폐직된 때의 직권면직 사유가 직업공무원제도에 반한다고 한 부분
3|⑤|01|O|헌법상 직업공무원제도는 국민주권원리에 바탕을 둔 민주적이고 법치주의적인 공직제도이다.|
4|①|01|O|헌법상 검열은 행정권이 발표 전에 사상이나 의견의 내용을 심사·선별하여 허가받지 않은 발표를 금지하는 제도이다.|
4|②|01|O|명예훼손 도서의 출판 전에 법원이 출판금지를 명하는 것은 행정권에 의한 사전검열에 해당하지 않는다.|
4|③|01|O|언론·출판에 대하여 검열을 수단으로 한 제한은 법률로도 허용되지 않는다.|
4|④|01|O|인터넷 포털사이트의 불법정보에 대하여 방송통신위원회가 포털 운영자에게 삭제명령을 하는 것은 헌법이 금지하는 검열에 해당하지 않는다.|
4|⑤|01|X|행정기관이 영화 상영 전에 내용을 심사하여 등급분류를 보류하고 등급분류를 받지 않은 영화의 상영을 금지하는 제도는 검열금지원칙에 위반된다.|의회가 행정기관의 영화 등급분류보류와 미분류 영화 상영금지를 정할 수 있다고 한 부분
5|①|01|O|2010년 출제 당시 대한민국 국적을 취득한 외국국적자는 원칙적으로 대한민국 국적 취득일부터 6개월 안에 외국국적을 포기하여야 하고, 이를 이행하지 않으면 그 기간이 지난 때 대한민국 국적을 상실하였다.|
5|②|01|X|귀화허가를 받기 위해 언제나 대한민국 민법상 성년이어야 하는 것은 아니다.|귀화허가를 받으려면 반드시 대한민국 민법상 성년이어야 한다고 한 부분
5|③|01|X|대한민국 국민과 혼인하였다는 사정만으로 바로 대한민국 국적을 취득하는 것은 아니다.|대한민국 국민과 결혼하면 바로 국적을 취득한다고 한 부분
5|④|01|X|출생으로 복수국적자가 된 사람의 국적선택 기간은 단순히 민법상 성년이 되기 전까지로 정해지는 것이 아니다.|출생 복수국적자가 민법상 성년이 되기 전까지 하나의 국적을 선택하여야 한다고 한 부분
5|⑤|01|X|출생에 의한 국적취득에서는 원칙적으로 혈통주의를 취하지만 일정한 경우 출생지주의도 인정된다.|출생에 의한 국적취득에서 혈통주의만 인정되고 출생지주의는 인정되지 않는다고 한 부분
6|①|01|O|법규명령, 행정규칙, 조례는 위헌법률심판의 대상이 되는 법률에 해당하지 않는다.|
6|②|01|O|폐지된 법률이라도 그 위헌 여부가 관련 소송사건 재판의 전제가 되면 위헌법률심판의 대상이 될 수 있다.|
6|③|01|O|법률의 해석·적용에 대한 한정합헌 또는 한정위헌 판단을 구하는 청구는 원칙적으로 부적법하다.|
6|④|01|O|조약도 위헌법률심판의 대상이 될 수 있다.|
6|⑤|01|X|재판의 전제성은 원칙적으로 위헌법률심판 제청 시뿐 아니라 헌법재판소 결정 시에도 갖추어져야 한다.|재판의 전제성을 위헌법률심판 청구 시점에만 갖추면 된다고 한 부분
7|①|01|O|일반적 행동의 자유권은 헌법상 열거되지 않은 기본권으로 인정된다.|
7|②|01|X|평화적 생존권은 헌법상 열거되지 않은 독자적 기본권으로 인정되지 않는다.|평화적 생존권이 헌법상 열거되지 않은 기본권으로 인정된다고 본 부분
7|③|01|O|생명권은 헌법상 열거되지 않은 기본권으로 인정된다.|
7|④|01|O|자기결정권은 헌법상 열거되지 않은 기본권으로 인정될 수 있다.|
7|⑤|01|O|명예권은 헌법상 열거되지 않은 기본권으로 인정될 수 있다.|
8|①|01|X|국회에서 의결되어 정부에 이송된 법률안에 대하여 대통령이 15일 이내에 공포나 재의요구를 하지 않으면 법률로 확정되지만, 효력 발생에는 공포가 필요하다.|대통령이 15일 이내 공포나 재의요구를 하지 않은 법률안이 공포 없이 효력이 발생한다고 한 부분
8|②|01|X|국회에서 부결된 법률안은 같은 회기 중 다시 발의하거나 제출하지 못한다.|정기회에서 부결된 법률안을 다음 임시회에서 다시 발의하지 못한다고 한 부분
8|③|01|X|헌법상 국회 회의공개 원칙은 본회의뿐 아니라 위원회에도 원칙적으로 적용된다.|국회 회의공개 원칙이 위원회와 소위원회에 원칙적으로 적용되지 않는다고 한 부분
8|④|01|X|국회 의결에서 가부동수인 때에는 부결된 것으로 본다.|찬성 130명과 반대 130명의 가부동수이면 법률안이 가결된다고 한 부분
8|⑤|01|O|대통령은 국회에서 의결되어 정부에 이송된 법률안에 이의가 있으면 이의서를 붙여 환부하여 재의를 요구할 수 있지만, 법률안 일부에 대하여 또는 수정하여 재의를 요구할 수 없다.|
9|①|01|O|정당은 중앙당이 중앙선거관리위원회에 등록함으로써 성립한다.|
9|②|01|O|초·중등학교 교원의 정당가입과 선거운동을 금지하면서 대학교원에게 이를 허용하는 차별은 직무의 본질과 근무태양 차이에 비추어 합리적 차별로 볼 수 있다.|
9|③|01|X|정당설립의 자유는 헌법상 기본권으로 인정되므로 이를 근거로 헌법소원심판을 청구할 수 있다.|정당설립의 자유가 헌법상 기본권이 아니라고 한 부분
9|④|01|O|교섭단체를 구성한 정당에만 정책연구위원을 배정하는 것은 그렇지 못한 정당을 합리적 이유 없이 차별한다고 볼 수 없다.|
9|⑤|01|O|대통령선거 경선후보자가 당내경선 과정에서 탈퇴하여 후원회를 둘 자격을 상실한 경우 후원회 후원금 전액을 국고에 귀속하게 하는 것은 선거의 자유 등을 침해한다.|
10|①|01|O|합헌적 법률해석은 법률규정에 위헌적 해석 가능성과 합헌적 해석 가능성이 공존할 때 위헌적 해석을 배제하고 헌법에 합치되도록 해석하여야 한다는 지침이다.|
10|②|01|O|합헌적 법률해석으로 해당 법조항의 본래 의미나 목적을 새롭게 변경하는 것은 허용되지 않는다.|
10|③|01|X|합헌적 법률해석은 헌법재판소뿐 아니라 일반 법원도 법률을 해석할 때 사용할 수 있는 해석기법이다.|합헌적 법률해석이 일반 법원과 무관한 해석기법이라고 한 부분
10|④|01|O|합헌적 법률해석은 헌법을 최고규범으로 하는 통일적 법질서를 유지하기 위하여 필요하다.|
10|⑤|01|O|합헌적 법률해석은 민주주의와 권력분립의 관점에서 입법부의 입법권 행사를 존중하는 기능을 가진다.|
11|①|01|X|대한민국헌법은 정교분리원칙과 함께 국교를 인정하지 않는다고 명시한다.|헌법이 국가의 특정 종교 국교 지정을 금지하지 않는다고 한 부분
11|②|01|X|사법시험 제1차 시험일을 일요일로 정한 공고가 기독교 신자인 수험생의 종교의 자유를 침해한다고 볼 수 없다고 판단되었다.|일요일 시험 공고가 종교의 자유 제한으로서 허용될 수 없다고 한 부분
11|③|01|O|특정 종교의 의식·행사·유형물이 사회공동체에서 관습화된 문화요소로 인식될 정도에 이르면 이에 대한 국가 지원은 정교분리원칙에 위배되지 않을 수 있다.|
11|④|01|X|종교단체가 운영하는 학교형태 교육기관에 행정청의 학교설립인가를 요구하는 것이 그 자체로 정교분리원칙에 반하는 것은 아니다.|종교단체 운영 교육기관에 학교설립인가를 요구하는 것이 정교분리원칙에 반한다고 한 부분
11|⑤|01|X|헌법재판소 결정례상 종교의 자유에 종교적 양심을 이유로 병역대체의무 제공을 요구할 권리가 당연히 포함되는 것은 아니다.|종교의 자유에 병역대체의무 제공을 요구할 권리가 포함된다고 한 부분
12|①|01|X|국가인권위원회는 위원장 1명과 상임위원 3명을 포함한 11명의 인권위원으로 구성되고, 인권위원 중 4명 이상은 여성이어야 한다.|국가인권위원회 인권위원 중 3명 이상만 여성이면 된다고 한 부분
12|②|01|X|국가인권위원회는 인권의 보호와 향상에 중대한 영향을 미치는 재판이 계속 중인 경우 법원 또는 헌법재판소의 요청이 없어도 의견을 제출할 수 있다.|법원 또는 헌법재판소의 요청이 있어야 의견을 제출하여야 한다고 한 부분
12|③|01|O|국가인권위원회의 조사대상에는 법인, 단체 또는 사인에 의한 차별행위도 포함된다.|
12|④|01|X|국가인권위원회 인권위원에게 퇴직 후 2년간 공직선거 출마를 금지하는 것은 평등원칙에 위배된다고 판단되었다.|인권위원의 퇴직 후 2년간 공직선거 출마 금지가 평등원칙에 위배되지 않는다고 한 부분
12|⑤|01|X|국가기관의 업무수행과 관련하여 국가인권위원회에 진정할 수 있는 기본권 침해는 법률이 정한 범위의 인권침해행위에 한정된다.|국가기관 업무수행 관련 기본권 침해는 종류를 막론하고 국가인권위원회에 진정할 수 있다고 한 부분
13|①|01|O|대한민국헌법은 제헌헌법부터 현행헌법까지 정부의 법률안 제출권을 인정하여 왔다.|
13|②|01|O|정부가 법률안을 제출하려면 국무회의 심의를 거쳐야 한다.|
13|③|01|X|국회의원은 표결에서 이미 표시한 의사를 임의로 변경할 수 없다.|국회의원이 투표함 폐쇄 전까지 표시한 의사를 변경할 수 있다고 한 부분
13|④|01|O|국회의원의 법률안 심의·표결권은 입법 직무 수행을 위한 권한이므로 국회의원의 개별 의사에 따라 이를 포기할 수 없다.|
13|⑤|01|O|국회의장이 토론에 참가할 때에는 의장석에서 물러나야 하며 그 안건의 표결이 끝날 때까지 의장석에 돌아갈 수 없다.|
14|①|01|X|헌법재판에서 변호사강제주의가 적용되더라도 국가기관 또는 지방자치단체는 변호사 자격이 있는 소속 직원을 대리인으로 선임할 수 있고, 국선대리인 제도는 헌법소원심판에서 인정된다.|모든 헌법재판에서 변호사강제주의가 원칙이므로 자력이 없는 자가 국선대리인 선임을 신청할 수 있다고 한 부분
14|②|01|O|헌법재판소법상 심판에 관여한 재판관은 심판 종류를 불문하고 결정서에 의견을 표시하여야 하며 탄핵심판도 이에 포함된다.|
14|③|01|X|헌법재판소는 권한쟁의심판에서 권한침해의 원인이 된 피청구인의 처분을 취소하거나 그 무효를 확인할 수 있다.|권한침해 원인 처분의 무효확인만 가능하고 취소는 할 수 없다고 한 부분
14|④|01|X|헌법소원심판에서도 필요한 경우 가처분이 허용될 수 있다.|헌법소원심판에서는 가처분이 허용되지 않는다고 한 부분
14|⑤|01|X|헌법재판의 심리방식은 심판종류별로 달라 탄핵심판, 정당해산심판, 권한쟁의심판은 원칙적으로 구두변론에 의한다.|헌법재판의 심리방식이 서면심리 원칙이고 필요할 때만 구두변론이라고 한 부분
15|①|01|O|헌법소원심판은 기본권 주체가 될 수 있는 기본권능력자가 청구할 수 있고, 기본권 주체가 아닌 자는 청구할 수 없다.|
15|②|01|O|대통령은 소속 정당을 위하여 정당활동을 할 수 있는 사인의 지위와 관련해서는 기본권 주체로서 헌법소원을 제기할 적격이 있다.|
15|③|01|X|국회의원이 국회 안의 의안처리과정에서 질의권, 토론권, 표결권 침해를 주장하는 경우에는 헌법소원이 아니라 권한쟁의심판으로 다투어야 한다.|국회의원이 의안처리과정에서 질의권·토론권·표결권 침해를 이유로 헌법소원을 제기할 적격이 있다고 한 부분
15|④|01|O|법인이 아닌 사단·재단도 대표자가 있고 독립된 사회적 조직체로 활동하면 성질상 법인이 누릴 수 있는 기본권 침해에 대하여 그 이름으로 헌법소원심판을 청구할 수 있다.|
15|⑤|01|O|외국인도 기본권 주체성이 인정되는 범위에서는 헌법소원을 제기할 수 있다.|
16|①|01|O|개인정보 자기결정권의 보호대상인 개인정보는 개인의 인격주체성을 특징짓고 동일성을 식별할 수 있게 하는 일체의 정보이다.|
16|②|01|O|개인정보 자기결정권은 자기 정보가 언제, 누구에게, 어느 범위까지 알려지고 이용되도록 할 것인지를 정보주체가 스스로 결정할 수 있는 권리이다.|
16|③|01|X|졸업생의 성명, 생년월일, 졸업일자 등을 교육정보시스템에 보유하는 것은 개인정보 자기결정권을 침해하지 않는다고 판단되었다.|졸업생의 성명, 생년월일, 졸업일자 등의 보유가 개인정보 자기결정권을 침해한다고 한 부분
16|④|01|O|주민등록증 발급신청서에 열 손가락 지문을 날인하게 하는 것은 신원확인 기능 수행과 정확성 제고를 위한 것으로 개인정보 자기결정권을 침해하지 않는다고 판단되었다.|
16|⑤|01|O|개인정보 자기결정권은 헌법 제10조의 일반적 인격권 및 헌법 제17조의 사생활의 비밀과 자유에 의하여 보장된다.|
17|①|01|O|과잉금지원칙은 법치주의와 헌법 제37조 제2항에서 근거를 찾을 수 있다.|
17|②|01|O|기본권 제한입법에서 과잉금지원칙은 목적의 정당성, 수단의 적정성, 피해의 최소성, 법익의 균형성을 내용으로 한다.|
17|③|01|O|목적의 정당성은 국민의 기본권을 제한하려는 입법목적이 헌법과 법률 체제상 정당성을 인정받아야 함을 뜻한다.|
17|④|01|X|수단의 적정성은 입법목적 달성에 적합한 수단을 요구하지만 유일하게 효과적인 수단만을 선택하여야 한다는 뜻은 아니다.|수단의 적정성이 유일하게 효과적이고 적합한 수단 선택을 요구한다고 한 부분
17|⑤|01|O|법익의 균형성은 입법으로 보호하려는 공익과 침해되는 사익을 비교·형량할 때 보호되는 공익이 더 커야 함을 의미한다.|
18|①|01|O|사용자가 근로자에게 자신의 잘못을 반성하고 사죄한다는 내용의 시말서 제출을 명령하는 것은 양심의 자유를 침해한다고 판단되었다.|
18|②|01|X|음주측정거부자에게 운전면허 필요적 취소를 규정한 것은 양심의 자유나 행복추구권을 침해하지 않는다고 판단되었다.|음주측정거부에 대한 필요적 운전면허 취소가 양심의 자유 침해라고 본 부분
18|③|01|X|2010년 출제 당시 양심적 병역거부를 이유로 한 입영거부를 형사처벌하는 것은 양심의 자유 침해로 보지 않았다.|양심적 병역거부 형사처벌을 양심의 자유 침해라고 본 부분
18|④|01|X|사업자단체에 법위반사실 공표를 명하는 제도는 위반사실 자체의 공표를 명하는 한 양심의 자유 침해로 보지 않았다.|사업자단체에 대한 법위반사실 공표명령을 양심의 자유 침해라고 본 부분
18|⑤|01|X|선거운동기간 중 인터넷언론사 게시판에서 실명확인을 요구하는 것은 양심의 자유 침해로 보지 않았다.|인터넷언론사 게시판 실명확인제가 양심의 자유 침해라고 본 부분
19|①|01|O|국무회의는 헌법상 필수기관이므로 이를 폐지하려면 헌법개정절차를 거쳐야 한다.|
19|②|01|O|대통령이 국가대표 선수에게 체육훈장을 수여하려면 국무회의 심의를 거쳐야 한다.|
19|③|01|O|행정각부의 장은 국무위원 중에서 임명된다.|
19|④|01|O|국무총리와 관계 국무위원은 대통령의 국법상 행위가 이루어지는 문서에 부서하여야 한다.|
19|⑤|01|X|총리령은 국무총리가, 부령은 행정각부의 장이 소관사무에 관하여 법률이나 대통령령의 위임 또는 직권으로 발한다.|국무총리와 국무위원이 법률이나 대통령령의 위임 또는 직권으로 법규명령을 발할 수 있다고 한 부분
20|①|01|O|시·도지사 선거소송과 시·도지사 당선소송은 대법원이 단심으로 처리한다.|
20|②|01|O|법관의 징계처분에 대한 취소청구는 대법원이 단심으로 처리한다.|
20|③|01|O|해양사고사건에 관한 중앙해양안전심판원 재결에 대한 소송은 대법원이 단심으로 처리한다.|
20|④|01|X|공정거래위원회 처분에 대한 불복의 소는 대법원이 단심으로 처리하는 사건이 아니다.|공정거래위원회 처분에 대한 불복의 소가 대법원 단심 사건이라고 본 부분
20|⑤|01|O|국회의원 선거소송과 국회의원 당선소송은 대법원이 단심으로 처리한다.|
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
        raise ValueError("cannot locate 2010 constitution section")
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
        statement = re.split(r"\s*제1과목\s*①책형.*|\s*【\s*상\s*법|\s*【\s*제1과목", statement)[0]
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
        qid = f"2010-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2010-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2010-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v016_2010_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2010-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
