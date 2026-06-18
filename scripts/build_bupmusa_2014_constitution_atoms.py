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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2014" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2014_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2014"
TEXT_DIR = PRIVATE_ROOT / "text" / "2014"
RAW_PDF_PATH = RAW_DIR / "2014_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2014_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2014_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2014_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2014_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2014_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2014_bupmusa_1st"
YEAR = 2014
ROUND = 20
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
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "국적법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국적법"},
    {"title": "공무원연금법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공무원연금법"},
    {"title": "2014 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2014/54337163"},
    {"title": "제20회 법무사 제1차 시험 확정정답", "publisher": "법원행정처", "url": "https://0gichul.com/y2014/104801"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "②",
    3: "②",
    4: "①",
    5: "①",
    6: "⑤",
    7: "③",
    8: "④",
    9: "④",
    10: "③",
    11: "④",
    12: "④",
    13: "①",
    14: "⑤",
    15: "①",
    16: "⑤",
    17: "①",
    18: "②",
    19: "⑤",
    20: "④",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    12: "single-best-true",
    13: "single-best-true",
    14: "single-best-true",
    17: "single-best-true",
    18: "single-best-true",
    19: "single-best-true",
})

FALSE_LABELS = {
    1: {"②"},
    2: {"②"},
    3: {"②"},
    4: {"①"},
    5: {"①"},
    6: {"⑤"},
    7: {"③"},
    8: {"④"},
    9: {"④"},
    10: {"③"},
    11: {"④"},
    12: {"①", "②", "③", "⑤"},
    13: {"②", "③", "④", "⑤"},
    14: {"①", "②", "③", "④"},
    15: {"①"},
    16: {"⑤"},
    17: {"②", "③", "④", "⑤"},
    18: {"①", "③", "④", "⑤"},
    19: {"①", "②", "③", "④"},
    20: {"④"},
}

TOPICS = {
    1: "행복추구권",
    2: "생명권",
    3: "교육을 받을 권리",
    4: "혼인제도와 가족제도",
    5: "영장주의",
    6: "헌법재판소 재판관 및 법관의 신분과 임기",
    7: "형사보상청구권",
    8: "대통령",
    9: "표현의 자유와 알 권리",
    10: "지방자치",
    11: "국무총리 및 부총리",
    12: "법원",
    13: "평등권",
    14: "근로의 권리와 근로3권",
    15: "국적 취득",
    16: "재산권",
    17: "대통령 자문기구",
    18: "헌법상 경제질서",
    19: "탄핵소추대상자",
    20: "북한 및 통일문제",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    5: ("헌법+형사소송법+대법원 판례", "헌법 제12조 제3항 및 강제채혈·영장주의 판례", "혈액 취득, 소변검사, 동행명령, 지문채취와 영장주의 적용 범위를 구별하는 지점이다."),
    6: ("헌법+법원조직법+헌법재판소법", "헌법 제105조·제106조 및 법원조직법 제47조", "대법원장·대법관·법관과 헌법재판소 재판관의 임기와 신분보장을 구별하는 지점이다."),
    7: ("헌법+형사보상 및 명예회복에 관한 법률+헌법재판소 결정례", "헌법 제28조 및 형사보상청구권 결정례", "형사보상의 요건, 범위, 불복, 청구기간을 구별하는 지점이다."),
    11: ("정부조직법+헌법", "정부조직법상 국무총리·부총리·국무조정실 관련 조항 및 헌법 제88조", "국무총리의 지휘감독권, 부총리의 지위, 국무회의 구성원을 구별하는 지점이다."),
    12: ("헌법+법원조직법+대법원 판례", "헌법 제27조·제101조·제109조 및 법원조직법 관련 조항", "대법관회의 의결, 심판공개, 상급심 기속력, 긴급조치 심사권을 구별하는 지점이다."),
    15: ("국적법+대법원 판례+헌법재판소 결정례", "국적법 제5조·제6조·제9조·제11조의2", "귀화허가, 국적회복허가, 간이귀화, 복수국적자 처우를 구별하는 지점이다."),
    17: ("헌법", "헌법 제91조·제92조·제93조·제127조", "대통령 자문기구 중 헌법상 필수기관과 임의기관을 구별하는 지점이다."),
    18: ("헌법+헌법재판소 결정례", "헌법 제119조 및 경제질서 관련 결정례", "시장경제질서, 경제민주화, 영업규제, 독과점 관련 헌법문구를 구별하는 지점이다."),
    19: ("헌법", "헌법 제65조 제1항", "헌법이 직접 열거한 탄핵소추대상자와 법률상 대상자를 구별하는 지점이다."),
    20: ("헌법+남북관계 관련 판례", "헌법 제3조·제4조·제69조 및 남북관계 판례", "남북합의서 성격, 평화통일조항, 남북교류협력법과 국가보안법 관계를 구별하는 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|일반적 행동자유권, 개성의 자유로운 발현권, 자기결정권, 계약의 자유는 행복추구권의 보호영역에 포함된다.|
1|②|01|X|행복추구권은 국민이 행복추구에 필요한 급부를 국가에 적극적으로 요구할 수 있는 사회적 기본권을 내용으로 하지 않는다.|행복추구권이 필요한 급부를 국가에 적극적으로 요구할 수 있는 것을 내용으로 한다고 한 부분
1|③|01|O|행복추구권은 행복추구활동을 국가권력의 간섭 없이 자유롭게 할 수 있다는 포괄적 자유권의 성격을 가진다.|
1|④|01|O|행복추구권은 다른 개별적 기본권이 적용되지 않는 경우 보충적으로 적용될 수 있다.|
1|⑤|01|O|계약자유의 원칙은 헌법 제10조의 행복추구권에 포함되는 일반적 행동자유권에서 도출된다.|
2|①|01|O|모든 인간은 헌법상 생명권의 주체가 된다.|
2|②|01|X|태아는 모체에 의존하더라도 모와 별개의 생명체로서 생명에 대한 권리가 인정될 수 있다.|태아가 모와 별개의 생명체는 아니라고 한 부분
2|③|01|O|생명이 이념적으로 절대적 가치를 지니더라도 생명에 대한 법적 평가는 예외적으로 허용될 수 있다.|
2|④|01|O|생명권 제한이 정당화되는 예외적 경우에는 생명권 박탈이 초래되더라도 곧바로 기본권의 본질적 내용을 침해한다고 단정할 수 없다.|
2|⑤|01|O|연명치료 중단에 관한 자기결정은 생명권 보호라는 헌법적 가치와 충돌할 수 있다.|
3|①|01|O|국가는 모든 국민에게 균등한 교육을 받게 하고 경제적 약자가 실질적 평등교육을 받을 수 있도록 적극적 정책을 실현하여야 한다.|
3|②|01|X|국가의 실질적 평등교육 실현의무만으로 국민에게 직접 교육비를 청구할 권리가 인정되는 것은 아니다.|국민이 직접 실질적 평등교육을 위한 교육비를 청구할 권리가 인정된다고 한 부분
3|③|01|O|교육을 받을 권리는 교육을 통해 개인의 잠재능력을 계발하여 인간다운 문화생활과 직업생활의 기초를 마련하게 한다.|
3|④|01|O|의무교육 무상의 범위는 원칙적으로 모든 학생이 경제적 차별 없이 의무교육을 받는 데 필수불가결한 비용에 한한다.|
3|⑤|01|O|의무교육 무상의 본질적 항목에는 수업료·입학금 면제와 학교·교사 등 인적·물적 시설 및 유지비 부담 제외가 포함될 수 있다.|
4|①|01|X|헌법 제36조 제1항은 혼인과 가족에 대한 제도보장뿐 아니라 혼인과 가족생활을 스스로 결정하고 형성할 자유도 보장한다.|혼인과 가족생활을 스스로 결정하고 형성할 자유를 기본권으로 보장하지 않는다고 한 부분
4|②|01|O|혼인한 부부라는 이유만으로 혼인하지 않은 자산소득자보다 더 많은 조세부담을 지워 소득재분배를 강요하는 것은 부당하다.|
4|③|01|O|가족제도가 역사적·사회적 산물이라도 헌법의 우위에서 벗어날 수 없고, 헌법이념 실현을 방해하는 가족법은 수정되어야 한다.|
4|④|01|O|우리 헌법은 제정 당시부터 혼인의 남녀동권을 헌법적 혼인질서의 기초로 선언하였다.|
4|⑤|01|O|조세나 과징금 부과 등 공법관계에서는 획일성이 요청되므로 사실혼을 법률혼과 동일하게 취급하지 않을 수 있다.|
5|①|01|X|수사기관이 범죄증거 수집 목적으로 피의자의 동의 없이 혈액을 취득·보관하는 것은 감정처분허가장에 의한 감정에 필요한 처분으로도 할 수 있다.|피의자의 동의 없는 혈액 취득·보관을 압수의 방법으로만 할 수 있다고 한 부분
5|①|02|O|수사기관이 피의자의 동의 없이 혈액을 취득·보관하는 것은 형사소송법상 압수의 방법으로도 할 수 있다.|
5|②|01|O|교도소의 안전과 질서유지를 위한 소변 제출은 수사상 강제처분이 아니므로 헌법상 영장주의가 적용되지 않을 수 있다.|
5|③|01|O|참고인에 대한 동행명령제도는 신체의 자유를 사실상 억압하여 인치하는 것과 같으므로 영장주의 원칙이 적용되어야 한다.|
5|④|01|O|피의자가 신문 중 신원 확인을 위한 지문채취에 불응하는 경우 형사처벌로 지문채취를 강제하는 것은 영장주의에 위반되지 않는다.|
5|⑤|01|O|헌법상 영장발부에서 검사의 신청을 요구한 취지는 수사단계 영장신청권자를 검사로 한정하여 인권유린을 방지하려는 데 있다.|
6|①|01|O|대법원장과 대법관의 임기는 모두 6년이다.|
6|①|02|O|대법관은 법률이 정하는 바에 따라 연임할 수 있지만 대법원장은 중임할 수 없다.|
6|②|01|O|헌법재판소 재판관은 탄핵 또는 금고 이상의 형의 선고에 의하지 아니하고는 파면되지 않는다.|
6|③|01|O|법관의 정년을 법률로 정한 규정은 헌법상 법관 신분보장에 위반되지 않는다고 판단되었다.|
6|④|01|O|현행 헌법에는 헌법재판소장의 임기와 연임 가능 여부에 대한 명시 규정이 없다.|
6|⑤|01|X|대법관이 중대한 심신상 장해로 직무를 수행할 수 없을 때에는 대법원장의 제청으로 대통령이 퇴직을 명할 수 있다.|대법관의 심신상 장해 퇴직을 대법원장이 직접 명할 수 있다고 한 부분
7|①|01|O|형사보상 받을 사람이 같은 원인으로 다른 법률에 따라 받은 손해배상액이 형사보상금 이상이면 형사보상하지 않는다.|
7|②|01|O|헌법 제28조는 형사보상에 있어서 정당한 보상을 명문으로 규정하고 있다.|
7|③|01|X|형사보상은 국가배상과 취지가 다르므로 형사보상의 범위가 국가배상상 손해배상의 범위와 동일하여야 하는 것은 아니다.|형사보상 범위가 국가배상에서의 손해배상과 동일하여야 한다고 한 부분
7|④|01|O|형사보상액 산정의 사실인정이나 보상액 판단 오류에 대하여 불복신청을 일절 허용하지 않는 것은 형사보상청구권과 재판청구권을 침해한다.|
7|⑤|01|O|형사보상 청구기간을 무죄재판 확정일부터 1년 이내로 제한한 것은 형사보상청구권을 침해한다고 판단되었다.|
8|①|01|O|우리 헌정사상 대통령직이 폐지된 예는 없다.|
8|②|01|O|대통령후보자가 1인인 때에는 득표수가 선거권자 총수의 3분의 1 이상이어야 대통령으로 당선될 수 있다.|
8|③|01|O|대통령은 공익실현 의무를 지는 헌법기관이면서 소속 정당을 위하여 정당활동을 할 수 있는 사인의 지위도 가진다.|
8|④|01|X|특정 국가정책에 대한 국민투표 회부 여부는 대통령의 재량사항이므로 국민이 원한다는 이유만으로 국민투표 불회부가 곧바로 국민투표권 침해가 되는 것은 아니다.|대통령의 국민투표 불회부가 국민투표권 침해로서 헌법에 위반된다고 한 부분
8|⑤|01|O|대통령은 국회가 의결한 법률안에 재의를 요구할 수 있으나 일부 재의요구나 수정 재의요구는 할 수 없다.|
9|①|01|O|헌법 제21조 제4항은 헌법상 표현의 자유 보호영역의 한계를 설정한 조항이라고 볼 수 없다고 판단되었다.|
9|②|01|O|익명 또는 가명으로 자신의 사상이나 견해를 표명하고 전파하는 자유도 표현의 자유에 포함된다.|
9|③|01|O|저속한 간행물의 출판을 전면 금지하고 출판사 등록을 취소할 수 있도록 하는 것은 성인의 알 권리를 침해한다.|
9|④|01|X|알 권리에는 개별적 정보공개청구권뿐 아니라 일반국민이 국가 보유정보의 공개를 청구할 수 있는 일반적 정보공개청구권도 포함된다.|알 권리에 일반적 정보공개청구권이 포함되지 않는다고 한 부분
9|⑤|01|O|자유로운 의사 형성은 충분한 정보 접근이 보장되어야 가능하므로 알 권리는 표현의 자유에 포함된다.|
10|①|01|O|지방자치단체 사이에서 특정 행정동 명칭을 독점적·배타적으로 사용할 권한은 인정되기 어렵다.|
10|②|01|O|지방자치단체의 종류는 법률로 정할 수 있지만 지방의회를 법률로 폐지할 수는 없다.|
10|③|01|X|헌법은 주민에게 과도한 부담을 주는 지방자치단체 주요 결정사항에 대한 주민투표권을 직접 규정하고 있지 않다.|헌법이 지방자치단체 주요 결정사항에 대한 주민투표권을 규정하고 있다고 한 부분
10|④|01|O|지방자치단체의 자치사무에 대한 국가감사는 법령위반사항에 한하여 가능하다.|
10|⑤|01|O|기관위임사무도 개별 법령에서 일정 사항을 조례로 정하도록 위임하면 위임조례를 제정할 수 있다.|
10|⑤|02|O|기관위임사무에 관한 위임조례는 지방자치단체의 자치조례제정권과 구별된다.|
11|①|01|O|국무총리는 대통령의 명을 받아 각 중앙행정기관의 장을 지휘·감독한다.|
11|②|01|O|국무총리는 중앙행정기관장의 명령이나 처분이 위법 또는 부당하다고 인정하면 대통령의 승인을 받아 중지 또는 취소할 수 있다.|
11|③|01|O|국무총리를 보좌하기 위하여 국무조정실을 둔다.|
11|③|02|O|국무조정실은 중앙행정기관 행정의 지휘·감독, 정책조정, 사회위험·갈등관리, 정부업무평가와 규제개혁에 관하여 국무총리를 보좌한다.|
11|④|01|X|부총리는 국무위원으로 보하고 국무회의 구성원이 된다.|총리와 부총리가 모두 국무위원이 아니라고 한 부분
11|④|02|O|국무총리는 국무위원과 구별되는 국무회의 구성원이다.|
11|⑤|01|O|국무총리가 사고로 직무를 수행할 수 없을 때에는 부총리가 그 직무를 대행할 수 있다.|
12|①|01|X|대법관회의는 대법관 전원의 3분의 2 이상 출석과 출석인원 과반수의 찬성으로 의결한다.|대법관회의 의결정족수를 전원 과반수 출석과 출석인원 3분의 2 이상 찬성으로 본 부분
12|②|01|X|상급법원 재판의 판단은 해당 사건에 관하여 하급심을 기속한다.|상급법원의 판단이 동종사건 일반에 관하여 하급심을 기속한다고 한 부분
12|③|01|X|재판의 심리는 국가안전보장·안녕질서 또는 선량한 풍속을 해할 염려가 있으면 결정으로 공개하지 않을 수 있지만 판결은 공개하여야 한다.|비공개 사유가 있으면 재판의 심리와 판결을 모두 공개하지 않을 수 있다고 한 부분
12|④|01|O|유신헌법상 긴급조치는 국회의 입법권 행사라는 실질이 없어 헌법재판소 위헌심판대상인 법률에 해당하지 않는다.|
12|④|02|O|유신헌법상 긴급조치의 위헌 여부에 대한 최종 심사권은 대법원에 속한다고 판단되었다.|
12|⑤|01|X|대법원은 헌법재판소의 한정위헌결정에 대하여 위헌결정으로서의 효력을 인정하지 않는다.|대법원이 한정위헌결정의 위헌결정 효력을 인정한다고 한 부분
13|①|01|O|예비후보자의 선거운동을 위해 명함을 돌릴 수 있는 자격을 배우자와 직계존비속에게 부여한 것 자체는 배우자 없는 후보자의 평등권을 침해하지 않는다.|
13|②|01|X|변호사시험 시험장을 서울 소재 대학교로 정한 것만으로 지방응시자를 자의적으로 차별하여 평등권을 침해한다고 보기 어렵다.|서울 소재 시험장 선정이 지방응시자의 평등권을 침해하여 위헌이라고 한 부분
13|③|01|X|시각장애인에게만 안마사 자격을 인정하는 것은 비시각장애인의 평등권을 침해하지 않는다고 판단되었다.|시각장애인 안마사 독점이 비시각장애인의 평등권을 침해하여 위헌이라고 한 부분
13|④|01|X|독립유공자의 손자녀 보상금 지급에서 나이가 많은 자를 우선하도록 한 것은 평등권을 침해한다고 판단되었다.|나이 많은 자 우선순위가 정당한 차별로서 평등권을 침해하지 않는다고 한 부분
13|⑤|01|X|태평양전쟁 전후 강제동원자 중 국외강제동원자에게만 위로금을 지급하고 국내강제동원자를 제외한 것이 곧바로 평등권 침해라고 볼 수 없다.|국외강제동원자에게만 위로금을 지급하는 것이 위헌이라고 한 부분
14|①|01|X|일할 환경에 관한 권리는 인간의 존엄성에 대한 침해를 방어하기 위한 자유권적 기본권의 성격도 가지므로 외국인 근로자에게도 인정될 수 있다.|일할 환경에 관한 권리가 외국인 근로자에게 인정되지 않는다고 한 부분
14|②|01|X|노동조합을 결성하지 않거나 가입하지 않을 자유는 헌법 제33조 제1항의 단결권 내용에 포섭된다고 보기 어렵다.|노동조합 불가입·탈퇴의 자유가 단결권의 내용에 포섭된다고 한 부분
14|③|01|X|최저임금을 직접 청구할 수 있는 구체적 권리는 헌법에서 바로 도출되지 않는다.|최저임금 청구권이 헌법에서 직접 도출된다고 한 부분
14|④|01|X|주요방위산업체에 종사하는 근로자에 대하여 법률로 제한하거나 인정하지 않을 수 있는 권리는 단체행동권이다.|주요방위산업체 근로자의 단결권을 제한하거나 인정하지 않을 수 있다고 한 부분
14|⑤|01|O|근로의 권리는 근로자 개인을 보호하기 위한 권리이므로 노동조합은 그 주체가 될 수 없다.|
15|①|01|X|병역을 기피할 목적으로 대한민국 국적을 상실하였거나 이탈하였던 사람에게는 국적회복을 허가하지 않는다.|병역기피 목적 국적상실·이탈자의 국적회복허가가 재량사항이라고 한 부분
15|②|01|O|귀화허가는 외국인에게 대한민국 국적을 부여하여 국민으로서의 법적 지위를 포괄적으로 설정하는 행위이다.|
15|②|02|O|법무부장관은 귀화신청인이 귀화요건을 갖추었더라도 귀화허가 여부에 관하여 재량권을 가진다.|
15|③|01|O|대한민국 국민인 배우자와 혼인한 외국인도 혼인 후 3년이 지나더라도 일정한 국내 주소 요건을 갖추지 못하면 간이귀화 요건을 충족하지 못한다.|
15|④|01|O|부 또는 모가 대한민국 국민이었던 외국인이 대한민국에 3년 이상 계속 주소가 있으면 간이귀화허가를 받을 수 있다.|
15|⑤|01|O|복수국적자는 대한민국 법령 적용에서 대한민국 국민으로만 처우된다.|
16|①|01|O|개인택시면허의 재산권적 성격은 인정되지만 공급과잉 억제를 위한 개인택시면허 양도금지가 재산권을 침해한다고 볼 수 없다.|
16|②|01|O|공무원의 보수청구권은 법령에 따라 구체적 내용이 형성되면 재산적 가치가 있는 공법상 권리로서 재산권에 포함된다.|
16|③|01|O|의료급여수급권은 공공부조의 일종으로 순수한 사회정책적 목적의 권리이므로 재산권 보호대상으로 보기 어렵다.|
16|④|01|O|건설공사를 위한 매장문화재 발굴비용을 사업시행자에게 부담시키는 것은 과잉금지원칙에 위배되어 재산권을 침해한다고 보기 어렵다.|
16|⑤|01|X|임용결격자가 사실상 공무원으로 장기간 근무하였더라도 적법한 공무원 신분을 취득하지 못한 이상 공무원 퇴직연금수급권을 취득한다고 볼 수 없다.|임용결격 공무원에게 퇴직연금수급권을 부여하지 않는 것이 재산권 침해로서 위헌이라고 한 부분
17|①|01|O|국가안전보장회의는 국가안전보장에 관련되는 대외정책·군사정책과 국내정책 수립에 관하여 국무회의 심의에 앞서 대통령 자문에 응하는 헌법상 필수기관이다.|
17|②|01|X|민주평화통일자문회의는 평화통일정책 수립에 관한 대통령 자문기관으로 둘 수 있는 헌법상 임의기관이다.|민주평화통일자문회의를 대통령의 필수적 자문기구로 본 부분
17|③|01|X|국가원로자문회의는 국가 중요정책에 관한 대통령 자문기관으로 둘 수 있는 헌법상 임의기관이다.|국가원로자문회의를 대통령의 필수적 자문기구로 본 부분
17|④|01|X|국민경제자문회의는 국민경제 발전을 위한 중요정책 수립에 관한 대통령 자문기관으로 둘 수 있는 헌법상 임의기관이다.|국민경제자문회의를 대통령의 필수적 자문기구로 본 부분
17|⑤|01|X|국가과학기술자문회의는 과학기술 혁신 등에 관한 대통령 자문기관으로 둘 수 있는 헌법상 임의기관이다.|국가과학기술자문회의를 대통령의 필수적 자문기구로 본 부분
18|①|01|X|대형마트 영업시간 제한과 의무휴업일 지정 규정이 해당 사업자의 영업의 자유를 침해하여 위헌이라고 볼 수 없다고 판단되었다.|대형마트 영업시간 제한 등에 대하여 영업의 자유 침해를 이유로 위헌결정이 있었다고 한 부분
18|②|01|O|자도소주구입명령제도는 직업의 자유 침해 등을 이유로 위헌이라고 판단되었다.|
18|②|02|O|탁주 공급구역 제한제도는 국민보건과 탁주제조업체 과당경쟁 방지 등을 고려하여 위헌이라고 볼 수 없다고 판단되었다.|
18|③|01|X|헌법 제119조 제2항의 경제민주화 이념은 경제영역의 정의로운 사회질서를 위한 국가목표이면서 기본권 제한 국가행위를 정당화할 수 있는 헌법규범이다.|경제민주화 이념이 기본권 제한 국가행위를 정당화하는 헌법규범이 아니라고 한 부분
18|④|01|X|헌법 제119조 제2항의 적정한 소득분배 규정만으로 입법자가 소득에 대한 누진세율 종합과세를 시행할 구체적 입법의무를 부담하지는 않는다.|적정한 소득분배 규정에 따라 누진세율 종합과세의 구체적 입법의무가 있다고 한 부분
18|⑤|01|X|헌법은 독과점의 규제와 조정 및 공정거래의 보장에 관한 국가의 노력의무를 명문으로 규정하고 있지 않다.|독과점 규제와 공정거래 보장 노력의무가 헌법에 명문으로 규정되어 있다고 한 부분
19|①|01|X|국가정보원장은 헌법이 직접 열거한 탄핵소추대상자가 아니다.|국가정보원장을 헌법에서 직접 규정한 탄핵소추대상자로 본 부분
19|②|01|X|검사는 법률상 탄핵소추대상자가 될 수 있지만 헌법이 직접 열거한 탄핵소추대상자는 아니다.|검사를 헌법에서 직접 규정한 탄핵소추대상자로 본 부분
19|③|01|X|대통령비서실장은 헌법이 직접 열거한 탄핵소추대상자가 아니다.|대통령비서실장을 헌법에서 직접 규정한 탄핵소추대상자로 본 부분
19|④|01|X|법제처장은 헌법이 직접 열거한 탄핵소추대상자가 아니다.|법제처장을 헌법에서 직접 규정한 탄핵소추대상자로 본 부분
19|⑤|01|O|법관은 헌법이 직접 규정한 탄핵소추대상자이다.|
20|①|01|O|남북기본합의서는 국가 간 조약이라기보다 남북당국의 성의 있는 이행을 상호 약속하는 신사협정의 성격을 가진다.|
20|②|01|O|우리 헌법상 평화통일조항은 1972년 제4공화국 헌법에서 처음 도입되었다.|
20|③|01|O|헌법상 평화통일의무에서 국민 개개인이 국가기관에 통일 관련 구체적 행위를 요구할 기본권이 바로 도출되지는 않는다.|
20|④|01|X|남북교류협력에 관한 법률과 국가보안법은 규제대상과 입법목적을 달리하므로 일반법과 특별법의 관계로만 볼 수 없다.|남북교류협력법과 국가보안법을 규제대상이 동일한 일반법과 특별법의 관계로 본 부분
20|⑤|01|O|북한 의과대학 졸업 탈북의료인에게 국내 의료면허를 부여할지는 의료인 능력 등을 고려하여 입법자가 형성할 수 있다.|
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
        raise ValueError("cannot locate 2014 constitution section")
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
        qid = f"2014-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2014-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2014-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v012_2014_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2014-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
