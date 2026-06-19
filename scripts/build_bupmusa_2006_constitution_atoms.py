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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2006" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2006_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2006"
TEXT_DIR = PRIVATE_ROOT / "text" / "2006"
RAW_PDF_PATH = RAW_DIR / "2006_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2006_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2006_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2006_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2006_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2006_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2006_bupmusa_1st"
YEAR = 2006
ROUND = 12
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
    {"title": "국가배상법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국가배상법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "집회 및 시위에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/집회및시위에관한법률"},
    {"title": "형사보상 및 명예회복에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사보상및명예회복에관한법률"},
    {"title": "국정감사 및 조사에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국정감사및조사에관한법률"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "재외국민등록법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/재외국민등록법"},
    {"title": "재외국민의 교육지원 등에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/재외국민의교육지원등에관한법률"},
    {"title": "2006 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2006/48361820"},
    {"title": "2006 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2006/90297"},
    {"title": "제12회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?act=procFileDownload&file_srl=90298&module=file&sid=6718356fd1dfcd3b2d763e4ac9d61843"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "⑤",
    3: "③",
    4: "⑤",
    5: "②",
    6: "①",
    7: "①",
    8: "②",
    9: "④",
    10: "②",
    11: "③",
    12: "④",
    13: "②",
    14: "①",
    15: "④",
    16: "②",
    17: "②",
    18: "②",
    19: "④",
    20: "③",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    1: "single-best-true",
    3: "single-best-true",
    6: "single-best-true",
    11: "single-best-true",
    12: "single-best-true",
    15: "single-best-true",
    19: "single-best-true",
})

FALSE_LABELS = {
    1: {"①", "③", "④", "⑤"},
    2: {"⑤"},
    3: {"①", "②", "④", "⑤"},
    4: {"⑤"},
    5: {"②"},
    6: {"②", "③", "④", "⑤"},
    7: {"①"},
    8: {"②"},
    9: {"④"},
    10: {"②"},
    11: {"①", "②", "④", "⑤"},
    12: {"①", "②", "③", "⑤"},
    13: {"②"},
    14: {"①"},
    15: {"①", "②", "③", "⑤"},
    16: {"②"},
    17: {"②"},
    18: {"②"},
    19: {"①", "②", "③", "⑤"},
    20: {"③"},
}

TOPICS = {
    1: "헌법재판소 권한",
    2: "국민주권과 국가",
    3: "헌법상 법률유보",
    4: "언론·출판의 자유",
    5: "국민과 국적",
    6: "헌법상 기본권 명문 규정",
    7: "제헌헌법",
    8: "재판청구권",
    9: "국회의 동의·승인권",
    10: "위헌결정의 효력",
    11: "헌법상 국민의 의무와 명문 규정",
    12: "기본권과 헌법재판",
    13: "위헌법률심판 제청절차",
    14: "법관의 신분보장",
    15: "헌법개정 한계",
    16: "양심의 자유",
    17: "국회 회의와 절차",
    18: "기본권 주체",
    19: "헌법상 경제질서",
    20: "합헌적 법률해석",
}
BASIS = {
    no: ("조문+판례+학설", f"{topic} 관련 헌법 조문 및 판례·학설", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
ATOM_ROWS = """
1|①|01|X|탄핵심판권은 헌법재판소의 권한이다.|탄핵심판권이 헌법재판소의 권한이 아니라고 본 부분
1|②|01|O|위헌법률심판제청권은 법원이 헌법재판소에 위헌법률심판을 제청하는 권한이지 헌법재판소의 권한이 아니다.|
1|③|01|X|정당해산심판권은 헌법재판소의 권한이다.|정당해산심판권이 헌법재판소의 권한이 아니라고 본 부분
1|④|01|X|권한쟁의심판권은 헌법재판소의 권한이다.|권한쟁의심판권이 헌법재판소의 권한이 아니라고 본 부분
1|⑤|01|X|헌법소원심판권은 헌법재판소의 권한이다.|헌법소원심판권이 헌법재판소의 권한이 아니라고 본 부분
2|①|01|O|대한민국은 민주공화국이다.|
2|②|01|O|대한민국의 영토는 한반도와 그 부속도서로 한다.|
2|③|01|O|대한민국의 주권은 국민에게 있다.|
2|④|01|O|국가는 법률이 정하는 바에 따라 재외국민을 보호할 의무를 진다.|
2|⑤|01|X|대한민국의 모든 권력은 헌법이 아니라 국민으로부터 나온다.|모든 권력이 헌법으로부터 나온다고 한 부분
3|①|01|X|공무원의 신분과 정치적 중립성 보장은 헌법이 명시적으로 법률에 위임한 사항이다.|공무원의 신분과 정치적 중립성 보장이 헌법상 법률 위임사항과 거리가 멀다고 본 부분
3|②|01|X|국가의 정당운영자금 보조는 헌법이 명시적으로 법률에 위임한 사항이다.|국가의 정당운영자금 보조가 헌법상 법률 위임사항과 거리가 멀다고 본 부분
3|③|01|O|정당해산 자체는 헌법이 헌법재판소 심판사항으로 정한 것이며, 정당해산을 법률에 명시적으로 위임한 사항으로 보기 어렵다.|
3|④|01|X|국선변호인제도는 헌법이 명시적으로 법률에 위임한 사항이다.|국선변호인제도가 헌법상 법률 위임사항과 거리가 멀다고 본 부분
3|⑤|01|X|저작자와 발명가의 권리 보호는 헌법이 명시적으로 법률에 위임한 사항이다.|저작자와 발명가의 권리가 헌법상 법률 위임사항과 거리가 멀다고 본 부분
4|①|01|O|언론·출판의 자유는 그 성질상 외국인에게도 인정될 수 있다.|
4|②|01|O|사용자의 허가 없이 사업장 안에서 유인물을 배포한 근로자를 징계할 수 있도록 한 취업규칙이 곧바로 헌법에 위반되는 것은 아니다.|
4|③|01|O|광고물도 사상, 지식, 정보 등을 불특정 다수인에게 전파하는 표현물로서 언론·출판의 자유의 보호대상이 될 수 있다.|
4|④|01|O|저속한 간행물의 출판을 전면 금지하고 출판사 등록을 취소할 수 있도록 하는 것은 성인의 알권리를 침해하여 위헌으로 판단될 수 있다.|
4|⑤|01|X|언론·출판에 대한 사전검열은 법률로도 허용되지 않는다.|언론·출판이 타인의 명예나 공중도덕을 침해해서는 안 된다는 이유로 법률상 사전검열이 가능하다고 한 부분
5|①|01|O|민족은 혈연을 기초로 한 자연적·문화적 개념이고, 국민은 국가법상 지위를 나타내는 법적 개념이다.|
5|②|01|X|국민은 국가에 대한 법적 소속관계를 전제로 하는 개념이므로 사회 구성원을 뜻하는 인민과 동일한 개념이라고 볼 수 없다.|국민이 인민과 동일한 개념이라고 한 부분
5|③|01|O|대한민국 국민이 되는 요건은 법률로 정한다.|
5|④|01|O|북한지역에 살고 있는 주민도 대한민국 국민에 해당한다.|
5|⑤|01|O|대한민국은 국적 취득에 관하여 원칙적으로 혈통주의를 취한다.|
6|①|01|O|평화적 생존권은 현행 헌법에 명시적으로 규정된 기본권으로 보기 어렵다.|
6|②|01|X|인간으로서의 존엄과 가치는 현행 헌법에 명시적으로 규정되어 있다.|인간으로서의 존엄과 가치가 헌법에 명시적으로 규정되어 있지 않다고 본 부분
6|③|01|X|신체의 자유는 현행 헌법에 명시적으로 규정되어 있다.|신체의 자유가 헌법에 명시적으로 규정되어 있지 않다고 본 부분
6|④|01|X|청원권은 현행 헌법에 명시적으로 규정되어 있다.|청원권이 헌법에 명시적으로 규정되어 있지 않다고 본 부분
6|⑤|01|X|사생활의 비밀과 자유는 현행 헌법에 명시적으로 규정되어 있다.|사생활의 비밀과 자유가 헌법에 명시적으로 규정되어 있지 않다고 본 부분
7|①|01|X|제헌헌법은 국회를 단원제로 구성하였다.|제헌헌법이 국회를 양원제로 규정하였다고 한 부분
7|②|01|O|제헌헌법은 대통령과 부통령을 국회에서 선출하고 임기를 4년으로 정하였다.|
7|③|01|O|제헌헌법은 전문, 10장, 103조로 구성되었다.|
7|④|01|O|제헌헌법은 노동3권과 사기업 근로자의 이익분배균점권 등 사회적 기본권을 규정하였다.|
7|⑤|01|O|제헌헌법은 법원을 10년 임기의 법관으로 구성하도록 규정하였다.|
8|①|01|O|모든 국민은 헌법과 법률이 정한 법관에 의하여 법률에 의한 재판을 받을 권리를 가진다.|
8|②|01|X|배심원이 법률판단까지 관여하는 배심재판은 법관에 의한 재판을 받을 권리와 충돌할 수 있다.|배심원이 법률판단까지 관여하더라도 법관이 진행하면 헌법에 위반되지 않는다고 한 부분
8|③|01|O|형사피고인은 상당한 이유가 없는 한 지체 없이 공개재판을 받을 권리를 가진다.|
8|④|01|O|교통범칙자에 대한 경찰서장의 통고처분은 불응 시 정식재판절차가 보장되므로 헌법에 위반되지 않는다고 볼 수 있다.|
8|⑤|01|O|재판을 받을 권리는 그 성질상 외국인과 법인에게도 보장될 수 있다.|
9|①|01|O|대통령은 계엄을 선포한 때에는 지체 없이 국회에 통고하여야 한다.|
9|②|01|O|국회는 상호원조 또는 안전보장에 관한 조약의 체결·비준에 대한 동의권을 가진다.|
9|③|01|O|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|
9|④|01|X|긴급재정경제처분에 대하여 국회는 사후 승인권을 가지며, 이를 조약이나 사면과 같은 동의권이라고 표현하기는 어렵다.|국회가 대통령의 긴급재정경제처분에 대하여 동의권을 가진다고 한 부분
9|⑤|01|O|감사원은 세입·세출의 결산을 매년 검사하여 대통령과 다음 연도 국회에 그 결과를 보고하여야 한다.|
10|①|01|O|위헌으로 결정된 법률은 원칙적으로 그 결정이 있는 날부터 효력을 상실하고, 형벌에 관한 법률은 소급하여 효력을 상실한다.|
10|②|01|X|유죄 확정판결의 근거가 된 형벌법률이 위헌으로 결정되면 그 확정판결에 대하여 재심을 청구할 수 있다.|형벌법률 위헌결정이 확정판결의 재심사유가 되지 않는다고 한 부분
10|③|01|O|위헌결정의 소급효가 당해사건, 동종 위헌제청 사건, 법원 계속 중인 사건에 미치는 범위에 관하여 헌법재판소와 대법원은 대체로 일치된 입장을 취하였다.|
10|④|01|O|헌법재판소의 위헌결정은 법원, 그 밖의 국가기관 및 지방자치단체를 기속한다.|
10|⑤|01|O|한정위헌결정의 기속력에 관하여 헌법재판소와 대법원의 입장은 같지 않다.|
11|①|01|X|국민의 근로의 의무는 헌법이 명문으로 규정하고 있다.|근로의 의무가 헌법에 명문으로 규정되어 있지 않다고 본 부분
11|②|01|X|국민의 환경보전을 위하여 노력할 의무는 헌법이 명문으로 규정하고 있다.|환경보전 노력 의무가 헌법에 명문으로 규정되어 있지 않다고 본 부분
11|③|01|O|국민의 헌법준수 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이 아니다.|
11|④|01|X|군인 등의 국가배상청구권에 대한 특칙은 헌법이 명문으로 규정하고 있다.|군인의 국가배상청구권 특칙이 헌법에 명문으로 규정되어 있지 않다고 본 부분
11|⑤|01|X|국가의 최저임금제 시행의무는 헌법이 명문으로 규정하고 있다.|국가의 최저임금제 시행의무가 헌법에 명문으로 규정되어 있지 않다고 본 부분
12|①|01|X|국회의원 지역선거구 인구편차에 관하여 최대선거구와 최소선거구 사이 인구수 비율이 2대 1을 넘으면 위헌이라는 기준이 확립된 판례였다고 볼 수는 없다.|국회의원 선거구 인구수 비율이 2대 1을 넘으면 위헌이라는 확립된 판례가 있다고 한 부분
12|②|01|X|재판을 받을 권리에 모든 사건에서 대법원의 상고심재판을 받을 권리까지 포함되는 것은 아니다.|재판을 받을 권리에 상고심재판을 받을 권리가 포함된다고 한 부분
12|③|01|X|헌법은 능력에 따라 균등하게 교육받을 권리를 보장하므로, 능력에 따른 교육 자체가 교육받을 권리를 침해한다고 볼 수 없다.|능력에 따라 교육하는 것이 교육받을 권리를 침해한다는 것이 다수설이라고 한 부분
12|④|01|O|국가유공자가 법률이 정하는 바에 따라 우선적으로 근로의 기회를 부여받는 것은 헌법에 위반되지 않는다.|
12|⑤|01|X|공무원은 현행 헌법상 단체행동권뿐 아니라 단결권도 법률이 정하는 바에 따라 제한될 수 있다.|공무원이 단결권을 제한받지 않는다고 한 부분
13|①|01|O|당사자는 재판 계속 중인 법원에 법률의 위헌 여부 심판 제청을 신청할 수 있다.|
13|②|01|X|위헌법률심판 제청신청 기각결정에 대하여는 항고할 수 없고, 헌법재판소법상 헌법소원심판을 청구할 수 있다.|위헌제청신청 기각 후 상급법원에 항고할 수 있다고 한 부분
13|③|01|O|제1심판결 후 항소심 계속 중에도 해당 법률이 재판의 전제가 되면 항소심 법원에 위헌법률심판 제청신청을 할 수 있다.|
13|④|01|O|상고심 계속 중에도 해당 법률이 재판의 전제가 되면 대법원에 위헌법률심판 제청신청을 할 수 있다.|
13|⑤|01|O|영업허가취소처분 취소소송을 제기한 당사자는 그 행정소송에서 재판의 전제가 되는 법률에 관하여 위헌법률심판 제청신청을 할 수 있다.|
14|①|01|X|법관은 탄핵 또는 금고 이상의 형의 선고에 의하지 않고는 파면되지 않으며, 징계처분에 의해서는 정직·감봉 등 불리한 처분을 받을 수 있다.|법관이 징계처분에 의하여 파면될 수 있다고 한 부분
14|②|01|O|법관은 중대한 심신상의 장해로 직무를 수행할 수 없는 경우가 아니면 강제퇴직당하지 않는다.|
14|③|01|O|대법관의 임기는 6년이며 법률이 정하는 바에 따라 연임할 수 있다.|
14|④|01|O|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|
14|⑤|01|O|대법원장의 임기는 6년이고 중임할 수 없다.|
15|①|01|X|대통령제를 폐지하고 의원내각제를 채택하는 것이 당연히 헌법개정의 한계를 벗어난다고 볼 수는 없다.|대통령제 폐지와 의원내각제 채택이 헌법개정의 한계를 벗어난다고 본 부분
15|②|01|X|헌법재판소를 폐지하고 그 기능을 대법원이 담당하게 하는 것이 당연히 헌법개정의 한계를 벗어난다고 볼 수는 없다.|헌법재판소 폐지와 기능 이전이 헌법개정의 한계를 벗어난다고 본 부분
15|③|01|X|감사원의 소속을 국회로 변경하는 것이 당연히 헌법개정의 한계를 벗어난다고 볼 수는 없다.|감사원 소속 변경이 헌법개정의 한계를 벗어난다고 본 부분
15|④|01|O|복수정당제를 폐지하는 것은 자유민주적 기본질서의 핵심을 침해하여 헌법개정의 한계를 벗어난 것으로 볼 수 있다.|
15|⑤|01|X|국회를 양원제로 구성하는 것이 당연히 헌법개정의 한계를 벗어난다고 볼 수는 없다.|국회 양원제 구성이 헌법개정의 한계를 벗어난다고 본 부분
16|①|01|O|양심적 병역거부자에 대하여 형벌을 부과할지 대체복무를 인정할지 여부에는 입법자에게 넓은 형성재량이 인정된다고 보았다.|
16|②|01|X|양심의 자유에는 양심상 결정을 외부로 표현하고 실현할 수 있는 자유도 포함된다.|양심의 자유에 양심상 결정의 외부 표현·실현 자유가 포함되지 않는다고 한 부분
16|③|01|O|양심의 자유가 곧바로 양심상 이유로 법적 의무의 이행을 거부하거나 대체의무 제공을 요구할 권리를 포함하는 것은 아니라고 보았다.|
16|④|01|O|양심상 결정이 종교관, 세계관 또는 그 밖의 가치체계에 기초하는지와 관계없이 양심의 자유에 의하여 보장될 수 있다.|
16|⑤|01|O|단순한 사실관계 확인이나 개인의 인격형성과 관계없는 사사로운 사유·의견은 양심의 자유의 보호대상이 아니다.|
17|①|01|O|국회의 의사공개원칙은 절대적이지 않고, 출석의원 과반수 찬성 또는 의장의 국가안전보장상 필요 인정이 있으면 공개하지 않을 수 있다.|
17|②|01|X|전 회기에 부결된 안건이라도 다음 회기에 다시 발의하여 심의할 수 있다.|전 회기에 부결된 동일안건을 다음 회기에 다시 발의하여 심의할 수 없다고 한 부분
17|③|01|O|의사공개원칙은 본회의뿐 아니라 위원회 의사절차에서도 존중되어야 한다.|
17|④|01|O|국회의원의 임기가 만료되면 국회에 제출되었으나 회기 중 의결되지 못한 법률안은 폐기된다.|
17|⑤|01|O|대통령이 임시회의 집회를 요구할 때에는 기간과 집회요구의 이유를 명시하여야 한다.|
18|①|01|O|법인이 아닌 사단도 대표자의 정함이 있고 독립된 사회적 조직체로 활동하면 성질상 법인이 누릴 수 있는 기본권의 주체가 될 수 있다.|
18|②|01|X|국회의 노동위원회와 같은 국가기관 내부기관은 원칙적으로 기본권 주체가 아니므로 헌법소원 청구인능력이 인정되지 않는다.|국회 노동위원회도 기본권 주체로서 헌법소원을 제기할 수 있다고 한 부분
18|③|01|O|외국인의 입국허가 여부는 국가의 재량사항이지만, 적법하게 입국한 외국인에게는 출국의 자유가 보장될 수 있다.|
18|④|01|O|헌법재판소는 국민과 유사한 지위에 있는 외국인도 기본권의 주체가 될 수 있다고 본다.|
18|⑤|01|O|국가나 지방자치단체는 원칙적으로 기본권의 주체가 되지 못한다.|
19|①|01|X|농지의 소작제도 금지는 현행 헌법상 경제질서 관련 규정에 명시되어 있다.|농지 소작제도 금지가 현행 헌법상 경제질서에 명시되어 있지 않다고 본 부분
19|②|01|X|소비자보호운동의 보장은 현행 헌법상 경제질서 관련 규정에 명시되어 있다.|소비자보호운동 보장이 현행 헌법상 경제질서에 명시되어 있지 않다고 본 부분
19|③|01|X|농어민 이익 보호, 중소기업 보호·육성, 지역경제 육성은 현행 헌법상 경제질서 관련 규정에 명시되어 있다.|농어민 이익보호와 중소기업·지역경제 육성이 현행 헌법상 경제질서에 명시되어 있지 않다고 본 부분
19|④|01|O|공정거래의 보장이라는 문구와 독과점에 대한 규제·조정이라는 표현은 현행 헌법상 경제질서 조항에 그대로 명시되어 있지는 않다.|
19|⑤|01|X|지하자원 등의 채취·개발 또는 이용의 특허와 국가 보호는 현행 헌법상 경제질서 관련 규정에 명시되어 있다.|지하자원 등의 채취·개발 또는 이용 특허와 국가 보호가 현행 헌법상 경제질서에 명시되어 있지 않다고 본 부분
20|①|01|O|합헌적 법률해석은 외형상 위헌적으로 보이는 법률도 헌법정신에 맞게 해석될 여지가 있으면 쉽게 위헌으로 판단하지 말라는 법률해석 지침이다.|
20|②|01|O|합헌적 법률해석의 근거로는 법질서의 통일성, 입법부의 민주적 정당성 존중, 법률의 유효추정, 법적 안정성 등이 제시된다.|
20|③|01|X|합헌적 법률해석의 전형적 표현방법은 단순위헌결정이 아니라 한정합헌결정 등 위헌적 해석을 배제하는 방식이다.|단순위헌결정이 합헌적 법률해석의 전형적 표현방법이라고 한 부분
20|④|01|O|합헌적 법률해석에는 헌법상 명시적인 근거규정이 반드시 필요하지는 않다.|
20|⑤|01|O|합헌적 법률해석은 법률에 합헌성을 부여하기 위하여 헌법의 규범적 의미와 내용을 의제하는 것까지 허용하지는 않는다.|""".strip()

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
        raise ValueError("cannot locate 2006 constitution section")
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
        statement = re.split(r"\s*제1과목\s*①책형.*|\s*제1과목\s*\([^)]*\).*|\s*【\s*상\s*법|\s*【\s*제1과목", statement)[0]
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
        qid = f"2006-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2006-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2006-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v012_2006_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2006-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
