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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2013" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2013_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2013"
TEXT_DIR = PRIVATE_ROOT / "text" / "2013"
RAW_PDF_PATH = RAW_DIR / "2013_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2013_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2013_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2013_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2013_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2013_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2013_bupmusa_1st"
YEAR = 2013
ROUND = 19
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
    {"title": "국회에서의 증언ㆍ감정 등에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회에서의증언ㆍ감정등에관한법률"},
    {"title": "사면법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/사면법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "선거관리위원회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/선거관리위원회법"},
    {"title": "2013 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2013/53135183"},
    {"title": "제19회 법무사 제1차 시험 확정정답", "publisher": "법원행정처", "url": "https://0gichul.com/y2013/101572"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "①",
    3: "③",
    4: "①",
    5: "②",
    6: "②",
    7: "④",
    8: "④",
    9: "①",
    10: "②",
    11: "⑤",
    12: "①",
    13: "④",
    14: "⑤",
    15: "③",
    16: "③",
    17: "④",
    18: "①",
    19: "⑤",
    20: "②",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    9: "single-best-true",
})

FALSE_LABELS = {
    1: {"⑤"},
    2: {"①"},
    3: {"③"},
    4: {"①"},
    5: {"②"},
    6: {"②"},
    7: {"④"},
    8: {"④"},
    9: {"②", "③", "④", "⑤"},
    10: {"②"},
    11: {"⑤"},
    12: {"①"},
    13: {"④"},
    14: {"⑤"},
    15: {"③"},
    16: {"③"},
    17: {"④"},
    18: {"①"},
    19: {"⑤"},
    20: {"②"},
}

TOPICS = {
    1: "감사원",
    2: "국회 증언·감정 제도",
    3: "대통령 사면권",
    4: "대법원",
    5: "선거관리위원회",
    6: "대학의 자율성",
    7: "국민투표",
    8: "기본권 충돌",
    9: "헌법개정 필요 사항",
    10: "혼인과 가족제도",
    11: "헌법소원 대상과 요건",
    12: "직업선택의 자유",
    13: "이중처벌금지",
    14: "알 권리",
    15: "정당제도 명문 규정",
    16: "헌법재판 절차와 효력",
    17: "헌법재판소 결정정족수",
    18: "권한쟁의심판",
    19: "헌법재판 일반심판절차",
    20: "죄형법정주의",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    1: ("조문", "대한민국헌법 제97조, 제98조 및 감사원법", "감사원의 소속·직무 독립성, 회계검사·직무감찰, 감사위원 신분보장을 조문 기준으로 정리한다."),
    2: ("조문", "국회에서의 증언ㆍ감정 등에 관한 법률", "국회 증언·서류제출 요구, 동행명령, 고발, 공개 제한의 요건을 조문 기준으로 정리한다."),
    3: ("조문", "대한민국헌법 제79조 및 사면법", "일반사면·특별사면·복권의 절차와 효과를 헌법과 사면법 기준으로 정리한다."),
    4: ("조문+판례", "대한민국헌법 제101조, 제104조 및 법원조직법", "대법원의 구성, 전원합의체 관할, 상고심 재판청구권의 범위를 조문과 헌법재판소 결정례 기준으로 정리한다."),
    5: ("조문", "대한민국헌법 제114조 및 선거관리위원회법", "중앙선거관리위원회의 구성, 위원장 선출, 직무, 위원의 정치적 중립과 신분보장을 조문 기준으로 정리한다."),
    6: ("판례", "헌법 제22조, 제31조 및 헌법재판소 대학의 자율성 결정례", "대학의 자율성의 주체, 국가의 교육제도 형성권, 제한심사 기준을 판례 기준으로 정리한다."),
    7: ("조문+판례", "대한민국헌법 제72조 및 국민투표법", "중요정책 국민투표의 성격, 신임투표 결부 금지, 국민투표무효소송의 구조를 조문과 판례 기준으로 정리한다."),
    8: ("판례", "헌법재판소 기본권 충돌 결정례", "기본권 충돌의 해결 방식과 흡연권·혐연권 관계를 판례 기준으로 정리한다."),
    9: ("조문", "대한민국헌법 제41조, 제67조, 제98조, 제105조, 제111조", "헌법에 직접 정해진 임기·정년·기관존치·피선거연령 사항인지 여부를 조문 기준으로 정리한다."),
    10: ("판례", "대한민국헌법 제36조 및 헌법재판소 혼인·가족제도 결정례", "혼인·가족생활 보장, 부부 자산소득 합산과세, 친자관계, 부모의 양육권·의무를 판례 기준으로 정리한다."),
    11: ("조문+판례", "헌법재판소법 제68조, 제69조 및 헌법소원 결정례", "헌법소원 대상, 청구기간, 직접성 요건을 조문과 판례 기준으로 정리한다."),
    12: ("판례", "헌법재판소 직업의 자유 결정례", "학교환경위생정화구역 내 영업 제한의 직업의 자유 침해 여부를 판례 기준으로 정리한다."),
    13: ("조문+판례", "대한민국헌법 제13조 및 이중처벌금지 결정례", "이중처벌금지원칙의 의미, 형벌과 행정제재의 구별, 동일행위 반복제재 여부를 판례 기준으로 정리한다."),
    14: ("판례", "대한민국헌법 제21조 및 알 권리 결정례", "시험정보, 국회 회의, 수사기록, 수용자 기사, 후보자 토론회 관련 알 권리 제한을 판례 기준으로 정리한다."),
    15: ("조문", "대한민국헌법 제8조", "헌법 제8조가 정당제도에 관하여 명문으로 정한 사항과 정하지 않은 사항을 구별한다."),
    16: ("조문", "헌법재판소법 제41조, 제48조, 제57조, 제61조, 제67조", "헌법재판 절차 계속 중 관련 절차의 정지와 결정 효력을 조문 기준으로 정리한다."),
    17: ("조문", "헌법재판소법 제23조", "헌법재판소 결정정족수 중 재판관 6명 이상의 찬성을 요하는 결정을 조문 기준으로 정리한다."),
    18: ("조문+판례", "대한민국헌법 제111조 및 헌법재판소법 권한쟁의심판 규정", "권한쟁의심판의 당사자능력, 권한침해 가능성, 국회의원의 청구 가능성을 조문과 판례 기준으로 정리한다."),
    19: ("조문", "헌법재판소법 제25조, 제30조, 제32조, 제34조, 제40조", "헌법재판소 심판절차의 대리, 변론·공개, 증거조사, 준용 법령을 조문 기준으로 정리한다."),
    20: ("조문+판례", "대한민국헌법 제12조, 제13조 및 죄형법정주의 결정례", "죄형법정주의의 명확성원칙과 처벌법규 위임 가능성을 판례 기준으로 정리한다."),
})

ATOM_ROWS = """
1|①|01|O|감사원은 국가의 세입·세출 결산, 국가 및 법률이 정한 단체의 회계검사, 행정기관 및 공무원 직무감찰을 소관 업무로 한다.|
1|②|01|O|감사원은 세입·세출 결산을 매년 검사하여 대통령과 다음 연도 국회에 그 결과를 보고하여야 한다.|
1|③|01|O|감사원은 대통령 소속이지만 직무에 관하여 독립의 지위를 가진다.|
1|④|01|O|감사위원은 탄핵결정, 금고 이상의 형 선고, 장기의 심신쇠약으로 직무수행이 불가능하게 된 경우가 아니면 본인의 의사에 반하여 면직되지 않는다.|
1|⑤|01|X|감사위원은 정당에 가입하거나 정치운동에 관여할 수 없다.|감사위원이 정당에 가입할 수 있다고 한 부분
2|①|01|X|국회로부터 공무원 등이 증언 요구를 받거나 국가기관이 서류 제출을 요구받은 경우에도 직무상 비밀이라는 이유만으로 증언이나 서류 제출을 거부할 수 없다.|직무상 비밀에 속한다는 이유만으로 증언이나 서류 제출을 거부할 수 있다고 한 부분
2|②|01|O|국정감사나 국정조사를 위한 위원회는 증인이 정당한 이유 없이 출석하지 않으면 의결로 지정 장소까지 동행할 것을 명령할 수 있다.|
2|③|01|O|국회가 감사 또는 조사 시 작성한 서류나 녹취한 녹음테이프 등은 원칙적으로 외부에 공표할 수 없다.|
2|③|02|O|국회 증언·감정 관련 법률 위반 여부가 수사 또는 재판 대상이 된 경우에는 의장의 승인을 얻어 관련 서류 등을 교부할 수 있다.|
2|④|01|O|본회의 또는 위원회가 증인이 정당한 이유 없이 출석하지 않았다고 인정하면 고발하여야 한다.|
2|⑤|01|O|국회 증인·참고인이 중계방송 또는 사진보도 등에 응하지 않겠다는 의사를 표명하면 의결로 중계방송·녹음·녹화·사진보도를 금지할 수 있다.|
2|⑤|02|O|국회 증인·참고인이 특별한 이유로 회의 비공개를 요구하면 의결로 회의 일부 또는 전부를 공개하지 않을 수 있다.|
3|①|01|O|일반사면은 원칙적으로 형 선고의 효력을 상실시키고, 형을 선고받지 않은 자에 대하여는 공소권을 상실시킨다.|
3|①|02|O|특별사면은 원칙적으로 형의 집행을 면제한다.|
3|②|01|O|일반사면은 국무회의 심의와 국회의 동의를 거쳐 대통령령의 형식으로 한다.|
3|③|01|X|법무부장관은 특별사면 상신을 신청받은 경우 사면심사위원회 심사를 거쳐 대통령에게 상신한다.|법무부장관이 스스로 상신의 적정성을 심사하여 대통령에게 특별사면을 상신한다고 한 부분
3|④|01|O|복권의 효과는 장래에 향하여 발생하고 형 선고 시로 소급하지 않는다.|
3|⑤|01|O|형의 집행유예를 선고받은 자에 대해서도 특별사면이나 감형을 하거나 유예기간을 단축할 수 있다.|
4|①|01|X|대법관의 수는 대법원장을 포함하여 14명이다.|대법관의 수를 대법원장을 포함하여 13명이라고 한 부분
4|②|01|O|명령 또는 규칙이 헌법이나 법률에 위반된다고 인정하는 경우에는 대법관 전원의 3분의 2 이상의 합의체에서 심판하여야 한다.|
4|②|02|O|종전 대법원 판시의 헌법·법률·명령 또는 규칙 해석적용 의견을 변경할 필요가 있는 경우에는 대법관 전원의 3분의 2 이상의 합의체에서 심판하여야 한다.|
4|③|01|O|헌법상 대법원이 최고법원이라는 사정만으로 모든 사건을 대법원이 상고심으로 관할하여야 하는 것은 아니다.|
4|③|02|O|헌법과 법률이 정한 법관에 의한 재판을 받을 권리가 모든 사건에 대한 상고심 재판을 받을 권리를 의미하지는 않는다.|
4|④|01|O|심급제도 자체는 헌법상 필수적이지만 모든 재판이 반드시 3심제이어야 하는 것은 아니다.|
4|⑤|01|O|대법관은 대법원장의 제청으로 국회의 동의를 얻어 대통령이 임명한다.|
5|①|01|O|중앙선거관리위원회는 대통령 임명 3명, 국회 선출 3명, 대법원장 지명 3명의 위원으로 구성된다.|
5|②|01|X|중앙선거관리위원회 위원장은 위원 중에서 호선한다.|중앙선거관리위원회 위원장을 대통령이 지명하여 임명한다고 한 부분
5|③|01|O|선거관리위원회는 선거와 국민투표의 공정한 관리 및 정당에 관한 사무를 처리한다.|
5|④|01|O|중앙선거관리위원회 위원은 정당에 가입하거나 정치에 관여할 수 없다.|
5|④|02|O|중앙선거관리위원회 위원은 탄핵 또는 금고 이상의 형의 선고에 의하지 아니하고는 파면되지 않는다.|
5|⑤|01|O|행정기관은 선거·국민투표 및 정당관계 법령안을 제정·개정·폐지하려면 미리 중앙선거관리위원회에 송부하여 의견을 구하여야 한다.|
6|①|01|O|대학 자율의 규율 정도는 시대 사정과 학교 단계에 따라 다를 수 있으므로 교육의 본질을 침해하지 않는 한 입법형성의 자유에 속한다.|
6|②|01|X|대학의 자율과 관련한 기본권의 주체는 대학뿐 아니라 교수나 교수회도 될 수 있다.|교수나 교수회가 대학의 자율 관련 기본권 주체가 될 수 없다고 한 부분
6|③|01|O|대학의 자율성은 학문의 자유의 확실한 보장수단으로서 대학에 부여된 헌법상 기본권이다.|
6|④|01|O|국가는 헌법 제31조 제6항에 따라 학교제도의 조직·계획·운영·감독에 관한 포괄적 형성권과 규율권을 가진다.|
6|⑤|01|O|대학의 자유를 제한하는 법률조항의 위헌 여부는 헌법 제37조 제2항의 한계를 벗어나 본질적 내용을 자의적으로 침해하는지에 따라 판단된다.|
7|①|01|O|헌법 제72조는 대통령에게 국민투표 실시 여부, 시기, 부의사항과 설문내용 등을 정할 임의적 국민투표발의권을 독점적으로 부여한다.|
7|②|01|O|헌법 제72조의 중요정책 국민투표 대상에는 대통령에 대한 신임이 포함되지 않는다.|
7|③|01|O|특정 정책 국민투표에 대통령 자신의 신임을 결부시키는 행위는 헌법적으로 허용되지 않는다.|
7|④|01|X|국민투표 효력에 이의가 있는 투표인은 투표인 10만명 이상의 찬성을 얻어 중앙선거관리위원회 위원장을 피고로 하여 대법원에 제소할 수 있다.|국민투표를 부의한 대통령을 피고로 하여 제소한다고 한 부분
7|⑤|01|O|국민투표무효소송에서 대법원은 법령 위반 사실이 국민투표 결과에 영향을 미쳤다고 인정할 때에 한하여 국민투표 전부 또는 일부의 무효를 판단한다.|
8|①|01|O|상하 위계질서가 있는 기본권끼리 충돌하면 상위기본권 우선의 원칙에 따라 하위기본권이 제한될 수 있다.|
8|②|01|O|정정보도청구권과 보도기관의 언론의 자유가 충돌하면 상충 기본권 모두가 최대한 기능과 효력을 발휘하도록 조화로운 방법을 찾아야 한다.|
8|③|01|O|비흡연자에게 영향이 없는 흡연은 기본권 충돌을 일으키지 않지만 공동 생활공간의 흡연은 흡연권과 혐연권의 충돌을 초래한다.|
8|④|01|X|헌법재판소는 기본권 충돌 문제를 언제나 기본권서열이론으로 해결하여 온 것은 아니다.|헌법재판소가 기본권 충돌 문제에서 기본권서열이론을 선택하여 해결하여 왔다고 한 부분
8|⑤|01|O|흡연권은 사생활의 자유를 실질적 핵으로 하고 혐연권은 사생활의 자유뿐 아니라 생명권에도 연결되므로 혐연권이 흡연권보다 상위 기본권이다.|
9|①|01|O|헌법재판소장의 정년은 헌법개정 없이 법률로 연장할 수 있다.|
9|②|01|X|법관의 임기는 헌법에 규정되어 있으므로 헌법개정 없이 연장할 수 없다.|헌법개정 없이 법관의 임기를 연장할 수 있다고 본 부분
9|③|01|X|지방의회는 헌법상 지방자치제도의 구성요소이므로 헌법개정 없이 폐지할 수 없다.|헌법개정 없이 지방의회를 폐지할 수 있다고 본 부분
9|④|01|X|대통령 피선거연령은 헌법에 규정되어 있으므로 헌법개정 없이 만 35세로 낮출 수 없다.|헌법개정 없이 대통령 피선거연령을 만 35세로 인하할 수 있다고 본 부분
9|⑤|01|X|감사위원의 임기는 헌법에 규정되어 있으므로 헌법개정 없이 연장할 수 없다.|헌법개정 없이 감사위원의 임기를 연장할 수 있다고 본 부분
10|①|01|O|현행 헌법은 혼인과 가족생활에 대한 국가의 보장의무를 규정하고 있다.|
10|②|01|X|부부의 자산소득을 합산과세하는 것은 혼인한 자를 차별하여 헌법에 위반된다고 판단되었다.|부부 자산소득 합산과세가 헌법에 위반되지 않는다고 한 부분
10|③|01|O|2013년 출제 당시 간통죄 처벌은 헌법재판소 결정례상 헌법에 위반되지 않는다고 판단되었다.|
10|④|01|O|부 또는 모 사망 후 인지청구의 제소기간을 사망 사실을 안 때부터 1년으로 제한한 것은 헌법에 위반되지 않는다고 판단되었다.|
10|⑤|01|O|자녀의 양육과 교육은 부모의 권리인 동시에 부모에게 부과된 의무이다.|
11|①|01|O|헌법소원 대상인 공권력의 행사 또는 불행사는 대한민국 국가기관의 공권력 작용을 의미하고 외국이나 국제기관의 공권력 작용은 포함되지 않는다.|
11|②|01|O|헌법소원 대상 행위의 국가기관에는 입법·행정·사법 등 모든 기관이 포함된다.|
11|②|02|O|공법상 사단·재단 등 공법인이나 국립대학교 같은 영조물의 작용도 헌법소원 대상이 될 수 있다.|
11|③|01|O|공권력 행사 또는 불행사로 기본권을 침해받은 자는 법원의 재판을 제외하고 헌법소원심판을 청구할 수 있다.|
11|④|01|O|권리구제형 헌법소원은 원칙적으로 기본권 침해 사유를 안 날부터 90일 이내, 그 사유가 있는 날부터 1년 이내에 청구하여야 한다.|
11|⑤|01|X|부진정입법부작위를 다투는 헌법소원도 법령소원으로서 원칙적으로 기본권 침해의 직접성 요건을 갖추어야 한다.|부진정입법부작위에 대한 법령소원에서 직접성 요건을 요구하지 않는다고 한 부분
12|①|01|X|대학교 학교환경위생정화구역 안에서 당구장 시설과 영업을 금지한 것은 직업의 자유를 과도하게 제한하여 위헌이라고 판단되었다.|대학교 정화구역 내 당구장 설치금지가 헌법에 위반되지 않는다고 한 부분
12|①|02|O|유치원 및 초·중·고등학교 학교환경위생정화구역 안에서 당구장 설치를 금지한 것은 헌법에 위반되지 않는다고 판단되었다.|
12|②|01|O|초·중·고등학교 및 대학교 학교환경위생정화구역 안에서 여관시설과 영업행위를 금지한 것은 헌법에 위반되지 않는다고 판단되었다.|
12|③|01|O|청소년 보호를 위한 자판기 설치 제한은 담배소매인의 직업수행의 자유 제한이 있더라도 법익형량상 허용될 수 있다.|
12|④|01|O|학교환경위생정화구역 안에서 노래방 설치를 제한하는 것은 직업의 자유에 대한 과도한 침해가 아니라고 판단되었다.|
12|⑤|01|O|학교환경위생정화구역 내 납골시설의 설치·운영을 절대적으로 금지한 것은 직업의 자유에 대한 과도한 침해가 아니라고 판단되었다.|
13|①|01|O|이중처벌금지원칙은 일사부재리 원칙을 국가형벌권의 기속원리로 헌법상 선언한 것이다.|
13|①|02|O|이중처벌금지원칙은 동일한 범죄행위에 대하여 국가가 형벌권을 거듭 행사할 수 없도록 하여 신체의 자유를 보장한다.|
13|②|01|O|음주운전 금지규정을 2회 이상 위반한 사람이 다시 위반한 때 운전면허를 필요적으로 취소하는 것은 이중처벌금지원칙에 위배되지 않는다.|
13|③|01|O|벌금을 납입하지 않은 때 노역장에 유치하는 것은 이중처벌금지원칙에 위배되지 않는다.|
13|④|01|X|헌법 제13조 제1항의 처벌은 원칙적으로 범죄에 대한 국가 형벌권 실행으로서의 과벌을 의미하고 국가의 모든 제재나 불이익처분을 포함하지 않는다.|이중처벌금지의 처벌에 국가가 행하는 일체의 제재나 불이익처분이 모두 포함된다고 한 부분
13|⑤|01|O|이중처벌 문제는 처벌 또는 제재가 동일한 행위를 대상으로 거듭 행해질 때 발생한다.|
14|①|01|O|한의사국가시험 문제와 정답을 공개하지 않도록 한 것이 과잉금지원칙에 위반하여 알 권리를 침해한다고 볼 수 없다고 판단되었다.|
14|②|01|O|국회 예산결산특별위원회 계수조정소위원회 회의에 대한 시민단체 방청을 불허한 것이 알 권리를 침해하지 않는다고 판단되었다.|
14|③|01|O|구속적부심 피의자의 변호인에게 고소장과 피의자신문조서 열람·등사를 거부한 정보비공개결정은 변호인의 조력권과 알 권리를 침해한다.|
14|④|01|O|수용소에서 교화상 또는 구금목적상 특히 부적당하다고 인정되는 기사를 삭제하는 것이 알 권리를 과잉제한한다고 볼 수 없다.|
14|⑤|01|X|공직선거 후보자 중 주요 후보만 초청하여 방송토론회를 개최하기로 한 결정이 국민의 알 권리와 후보자 선택의 자유를 침해한다고 볼 수 없다고 판단되었다.|주요 후보만 초청한 방송토론회 개최 결정이 국민의 알 권리와 후보자 선택의 자유를 침해한다고 한 부분
15|①|01|O|헌법은 정당의 설립이 자유라고 명문으로 규정한다.|
15|②|01|O|헌법은 정당의 목적이 민주적이어야 한다고 명문으로 규정한다.|
15|③|01|X|헌법은 정당이 공직선거 후보자를 추천하여야 한다고 명문으로 규정하지 않는다.|정당의 공직선거 후보자 추천의무가 헌법에 명문으로 규정되어 있다고 본 부분
15|④|01|O|헌법은 정당이 국민의 정치적 의사형성에 참여하는 데 필요한 조직을 가져야 한다고 명문으로 규정한다.|
15|⑤|01|O|헌법은 국가가 법률이 정하는 바에 따라 정당운영에 필요한 자금을 보조할 수 있다고 명문으로 규정한다.|
16|①|01|O|법원이 위헌법률심판을 제청한 때에는 당해 소송사건의 재판은 헌법재판소의 위헌 여부 결정이 있을 때까지 정지된다.|
16|②|01|O|탄핵소추의 의결을 받은 자는 헌법재판소 심판이 있을 때까지 권한행사가 정지된다.|
16|③|01|X|헌법소원이 제기되어 통지를 받은 법원도 헌법재판소 결정이 있을 때까지 재판을 반드시 정지하여야 하는 것은 아니다.|헌법소원 통지를 받은 법원이 반드시 재판을 정지하여야 한다고 한 부분
16|④|01|O|헌법재판소는 정당해산심판 청구를 받으면 청구인의 신청 또는 직권으로 종국결정 선고 시까지 피청구인의 활동을 정지할 수 있다.|
16|⑤|01|O|국가기관 또는 지방자치단체 처분을 취소하는 권한쟁의심판 결정은 그 처분의 상대방에게 이미 생긴 효력에 영향을 미치지 않는다.|
17|①|01|O|법률의 위헌결정에는 재판관 6명 이상의 찬성이 필요하다.|
17|②|01|O|탄핵결정에는 재판관 6명 이상의 찬성이 필요하다.|
17|③|01|O|정당해산결정에는 재판관 6명 이상의 찬성이 필요하다.|
17|④|01|X|국가기관 상호간 권한쟁의심판에 관한 결정에는 재판관 6명 이상의 찬성이 필요하지 않다.|국가기관 상호간 권한쟁의심판 결정에 재판관 6명 이상의 찬성이 필요하다고 본 부분
17|⑤|01|O|종전 헌법재판소의 헌법 또는 법률 해석적용 의견을 변경하는 경우에는 재판관 6명 이상의 찬성이 필요하다.|
18|①|01|X|지방의회의원과 지방의회의장 사이의 권한쟁의심판은 헌법재판소가 관장하는 지방자치단체 상호간 권한쟁의심판 범위에 속하지 않는다.|지방의회의원과 지방의회의장 사이의 권한쟁의가 지방자치단체 상호간 권한쟁의심판 범위에 속한다고 한 부분
18|②|01|O|권한쟁의심판의 당사자능력은 원칙적으로 헌법에 의하여 설치된 국가기관에 한정하여 인정된다.|
18|②|02|O|법률에 의하여 설치된 국가기관은 원칙적으로 권한쟁의심판 당사자능력이 인정되지 않는다.|
18|③|01|O|지방자치단체가 기관위임사무 수행 경비에 대하여 예산배정을 요청하였으나 기획재정부장관이 거부한 경우 그 거부처분에 대한 권한쟁의심판청구는 부적법하다.|
18|④|01|O|국가기관의 행위가 독자적 권능 행사가 아닌 경우에는 그 행위가 제한되더라도 권한쟁의심판상 권한 침해 가능성이 없다.|
18|⑤|01|O|국회의원은 국회의 권한인 입법권 자체의 침해를 주장하며 권한쟁의심판을 청구할 수 없다.|
19|①|01|O|각종 심판절차에서 당사자인 국가기관 또는 지방자치단체는 변호사나 변호사 자격이 있는 소속 직원을 대리인으로 선임할 수 있다.|
19|②|01|O|탄핵심판, 정당해산심판, 권한쟁의심판은 원칙적으로 구두변론에 의한다.|
19|③|01|O|헌법재판소 심판의 변론과 결정 선고는 공개한다.|
19|③|02|O|헌법재판소 심판의 서면심리와 평의는 공개하지 않는다.|
19|④|01|O|재판부는 사건 심리에 필요하다고 인정하면 직권 또는 당사자 신청으로 증거조사를 할 수 있다.|
19|⑤|01|X|헌법재판소 심판절차에는 특별한 규정이 없으면 헌법재판 성질에 반하지 않는 한도에서 민사소송에 관한 법령을 준용한다.|헌법재판소 심판절차에 행정소송법령을 준용한다고 한 부분
19|⑤|02|O|탄핵심판에는 형사소송에 관한 법령을 함께 준용한다.|
19|⑤|03|O|권한쟁의심판과 헌법소원심판에는 행정소송법을 함께 준용한다.|
20|①|01|O|죄형법정주의는 처벌대상 행위와 형벌을 누구나 예견하고 자신의 행위를 결정할 수 있도록 구성요건의 명확한 규정을 요구한다.|
20|②|01|X|죄형법정주의에서도 법률이 구체적으로 범위를 정하여 처벌법규를 하위법령에 위임하는 것은 허용될 수 있다.|처벌법규의 하위법령 위임이 허용되지 않는다고 한 부분
20|③|01|O|처벌법규 구성요건이 다소 광범위하여 법관의 보충적 해석이 필요하다는 사정만으로 명확성원칙에 배치된다고 할 수 없다.|
20|④|01|O|구성요건의 명확성 정도는 구성요건의 특수성, 법적 규제의 원인이 된 여건, 처벌의 정도 등을 종합하여 판단한다.|
20|⑤|01|O|죄형에 관한 법률조항이 시행령에 포괄위임되었는지는 명확성원칙 위반 여부와 포괄위임입법금지 여부의 문제이다.|
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
        raise ValueError("cannot locate 2013 constitution section")
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
        qid = f"2013-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2013-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2013-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v013_2013_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2013-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
