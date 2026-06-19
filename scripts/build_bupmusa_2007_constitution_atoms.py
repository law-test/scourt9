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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2007" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2007_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2007"
TEXT_DIR = PRIVATE_ROOT / "text" / "2007"
RAW_PDF_PATH = RAW_DIR / "2007_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2007_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2007_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2007_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2007_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2007_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2007_bupmusa_1st"
YEAR = 2007
ROUND = 13
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
    {"title": "2007 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2007/48390198"},
    {"title": "2007 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2007/91388"},
    {"title": "제13회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?act=procFileDownload&file_srl=91389&module=file&sid=55bbba4f4467e95a2e4f968dde06301b"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "③",
    3: "③",
    4: "④",
    5: "②",
    6: "③",
    7: "①",
    8: "⑤",
    9: "④",
    10: "①",
    11: "⑤",
    12: "③",
    13: "⑤",
    14: "③",
    15: "④",
    16: "⑤",
    17: "④",
    18: "⑤",
    19: "⑤",
    20: "⑤",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    4: "single-best-true",
    7: "single-best-true",
    20: "single-best-true",
})

FALSE_LABELS = {
    1: {"②"},
    2: {"③"},
    3: {"③"},
    4: {"①", "②", "③", "⑤"},
    5: {"②"},
    6: {"③"},
    7: {"②", "③", "④", "⑤"},
    8: {"⑤"},
    9: {"④"},
    10: {"①"},
    11: {"⑤"},
    12: {"③"},
    13: {"⑤"},
    14: {"③"},
    15: {"④"},
    16: {"⑤"},
    17: {"④"},
    18: {"⑤"},
    19: {"⑤"},
    20: {"①", "②", "③", "④"},
}

TOPICS = {
    1: "평등권",
    2: "대통령",
    3: "국회의원",
    4: "국회의 권한",
    5: "교육제도",
    6: "국제질서",
    7: "선거관리위원회와 규칙제정권",
    8: "공무원",
    9: "집회의 자유",
    10: "사생활의 비밀과 자유",
    11: "위헌법률심판",
    12: "법원과 헌법재판소 구성",
    13: "직업선택의 자유",
    14: "재산권 보장",
    15: "제9차 헌법개정",
    16: "지방자치단체",
    17: "기본권 제한",
    18: "무죄추정원칙",
    19: "행정입법",
    20: "입법권과 위헌제청",
}
BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    1: ("판례", "국가배상법 제2조 및 국가배상 관련 대법원 판례", "국가배상책임의 직무범위, 보상규정과의 관계, 위법한 행정처분 및 법관 재판에 관한 손해배상 기준을 정리한다."),
    2: ("판례", "대한민국헌법 제11조, 제24조 및 선거권 평등 관련 헌법재판소 결정례", "선거구 인구편차, 투표가치 평등, 자유선거와 부재자투표 보장의 기준을 정리한다."),
    3: ("조문+판례", "대한민국헌법 제12조, 제27조 및 신체의 자유 관련 결정례", "변호인 접견교통권, 일사부재리, 적법절차와 제재 병과의 한계를 정리한다."),
    4: ("조문+판례", "대한민국헌법 제8조, 정당법 및 정당 관련 헌법재판소 결정례", "정당의 헌법상 지위, 정당의 자유, 등록취소, 재산관계와 정당해산 제소권을 정리한다."),
    5: ("판례", "대한민국헌법 제21조 및 알권리·검열금지 관련 결정례", "알권리의 직접적 근거, 검열의 의미, 옥외광고 규제, 수용자 신문열람 제한의 기준을 정리한다."),
    6: ("조문+판례", "대한민국헌법 제21조, 집회 및 시위에 관한 법률 및 집회·결사의 자유 결정례", "집회 주최자 권한, 위험물 휴대 금지, 집회 장소 제한과 결사의 자유 보호대상을 정리한다."),
    7: ("판례", "헌법재판소법 및 헌법재판소 변형결정 관련 결정례", "헌법불합치, 한정위헌·한정합헌, 적용중지와 심판대상 확장의 법리를 정리한다."),
    8: ("조문+판례", "헌법재판소법 제68조, 제69조, 제72조 및 헌법소원 결정례", "헌법소원 청구기간, 재판소원 예외, 공법인의 권리구제, 보충성과 지정재판부 각하요건을 정리한다."),
    9: ("판례", "대한민국헌법 제119조, 제126조 및 경제질서 관련 결정례", "사기업 통제·관리, 과징금, 독과점 규제, 경제적 기본권 제한과 부동산 실명제 법리를 정리한다."),
    10: ("조문", "대한민국헌법 제76조, 제77조, 제79조", "긴급명령·긴급재정경제명령, 계엄, 사면과 계엄해제 요구의 요건을 정리한다."),
    11: ("조문+판례", "대한민국헌법 제11조, 제38조, 제59조 및 조세법률주의 결정례", "조세법률주의와 조세평등주의, 조례·조약과 조세감면의 법률유보를 정리한다."),
    12: ("조문", "대한민국헌법 제65조 및 헌법재판소법상 탄핵심판 절차", "탄핵소추 발의·의결, 소추위원, 권한정지, 파면 전제와 파면 후 공직취임 제한을 정리한다."),
    13: ("판례", "대한민국헌법 제19조, 제20조 및 양심·종교의 자유 관련 결정례", "사죄광고, 불고지죄, 준법서약, 양심적 병역거부와 종교교육의 자유 침해 여부를 정리한다."),
    14: ("조문+학설", "대한민국헌법 제28조 및 형사보상 관련 법령·학설", "형사보상청구권의 보상범위, 직접효, 불구속 무죄와 면소·공소기각의 보상 가능성을 정리한다."),
    15: ("조문+학설", "대한민국헌법 제61조 및 국정감사 및 조사에 관한 법률", "국정조사권의 근거, 상임위원회의 권한, 대상기관, 수사 중 사건과 지방자치단체 사무의 한계를 정리한다."),
    16: ("조문+판례", "대한민국헌법 제101조, 제103조, 제107조 및 법원조직법", "사법부 견제, 명령·규칙 심사, 법관 임명, 대법관 임기와 법관 징계 종류를 정리한다."),
    17: ("학설+판례", "대한민국헌법상 기본권 효력 관련 학설 및 결정례", "기본권의 대사인효, 입법권 구속, 비권력작용과 제3자효 문제를 정리한다."),
    18: ("조문", "대한민국헌법 제88조, 제97조, 제111조, 제114조 및 법원조직법", "국무회의, 감사원, 헌법재판소, 중앙선거관리위원회와 대법원의 구성 정원을 정리한다."),
    19: ("조문", "대한민국헌법 제53조, 제54조, 제63조, 제64조", "해임건의, 의원 제명, 예산안 제출·의결, 법률안 공포와 재의요구 제한을 정리한다."),
    20: ("조문", "대한민국헌법 제2조 제2항, 공직선거법, 재외국민등록법, 재외국민의 교육지원 등에 관한 법률", "재외국민 보호, 등록, 선거권, 재외선거인 등록과 한글학교 등록을 정리한다."),
})
ATOM_ROWS = """
1|①|01|O|법 앞의 평등은 일체의 차별적 대우를 부정하는 절대적 평등이 아니라 합리적 이유 없는 차별을 금지하는 상대적 평등을 의미한다.|
1|②|01|X|독립유공자나 그 유족에게 국가보은적 견지에서 서훈 등급에 따라 부가연금을 차등지급하는 것은 헌법 제11조 제3항의 영전일대 원칙에 위배되지 않는다고 판단되었다.|독립유공자 부가연금 차등지급이 영전일대 원칙에 위배된다고 한 부분
1|③|01|O|시혜적 법률처럼 입법자에게 넓은 형성의 자유가 인정되는 경우에는 법률 내용이 현저히 합리성을 결여하지 않는 한 평등원칙에 반한다고 할 수 없다.|
1|④|01|O|평등원칙은 국민의 기본권 보장에 관한 헌법상 최고원리이면서 국민의 권리로서 기본권 중의 기본권이다.|
1|⑤|01|O|현행 헌법은 군인·군무원·경찰공무원 등의 국가배상청구권 제한을 헌법 자체에서 규정하고 있다.|
2|①|01|O|대통령선거에서 후보자가 1인일 때에는 그 득표수가 선거권자 총수의 3분의 1 이상이어야 당선될 수 있다.|
2|②|01|O|대통령선거 결과 최고득표자가 2인 이상이면 국회가 재적의원 과반수가 출석한 공개회의에서 다수표를 얻은 사람을 당선자로 결정한다.|
2|③|01|X|대통령이 궐위된 때에는 잔여임기가 6개월 미만인 경우에도 헌법이 정한 기간 안에 후임자를 선거하여야 한다.|대통령 궐위 때 잔여임기 6개월 미만이면 국무총리가 잔여임기 동안 권한대행을 한다고 한 부분
2|④|01|O|대통령은 내란 또는 외환의 죄를 제외하고는 재직 중 형사상 소추를 받지 않지만 탄핵소추는 받을 수 있다.|
2|⑤|01|O|대통령은 국회 임시회의 소집을 요구할 수 있다.|
3|①|01|O|국회의장의 위법한 의안처리행위로 헌법상 기본원리가 훼손되었더라도 구체적 기본권 침해가 없으면 국회의원의 헌법소원심판청구는 허용될 수 없다.|
3|②|01|O|국회의원은 법률이 정하는 직을 겸할 수 없다.|
3|③|01|X|국회의원이 본회의나 위원회 발언 내용을 직전에 원내기자실에서 출입기자들에게 배포한 행위도 직무상 발언과 밀접하게 부수되는 경우 면책특권의 보호대상이 될 수 있다.|국회의원의 발언자료 사전배포 행위가 면책특권의 대상이 되지 않는다고 한 부분
3|④|01|O|현행범인 경우에는 국회의원에게 불체포특권이 인정되지 않는다.|
3|⑤|01|O|국회의원은 국가이익과 소속 정당의 이익이 충돌하면 국가이익을 우선하여 양심에 따라 직무를 수행할 의무가 있다.|
4|①|01|X|국가 예산안을 심의·확정하는 것은 국회의 권한이다.|국가 예산안 심의·확정이 국회의 권한에 속하지 않는다고 본 부분
4|②|01|X|선전포고와 국군의 외국 파견에 대한 동의권은 국회의 권한이다.|선전포고와 국군의 외국 파견 동의가 국회의 권한에 속하지 않는다고 본 부분
4|③|01|X|국정을 감사하거나 특정 국정사안에 대하여 조사하는 것은 국회의 권한이다.|국정감사와 국정조사가 국회의 권한에 속하지 않는다고 본 부분
4|④|01|O|국회는 국무총리 또는 국무위원을 직접 해임하는 권한이 아니라 해임을 건의하는 권한을 가진다.|
4|⑤|01|X|중앙선거관리위원회 위원에 대한 탄핵소추 의결은 국회의 권한이다.|중앙선거관리위원회 위원 탄핵소추 의결이 국회의 권한에 속하지 않는다고 본 부분
5|①|01|O|헌법 제31조 제6항은 교육제도, 교육재정, 교원의 지위에 관한 기본적인 사항을 법률로 정하도록 하여 교육제도 법정주의를 채택하고 있다.|
5|②|01|X|의무취학 시기를 만 6세가 된 다음날 이후 학년초로 정한 구 교육법 규정은 능력에 따라 균등하게 교육받을 권리의 본질적 내용을 침해한다고 볼 수 없다고 판단되었다.|의무취학 연령의 획일적 기준이 교육받을 권리의 본질적 내용을 침해한다고 한 부분
5|③|01|O|학원 등록제도는 국민의 교육받을 권리를 실질적으로 보장하고 교육시설 수준을 유지하기 위한 공공복리 목적의 효과적 수단이 될 수 있다.|
5|④|01|O|거주지를 기준으로 중·고등학교 입학을 제한하는 제도는 입시경쟁 부작용 방지라는 목적과 보완책을 고려할 때 학교선택권을 본질적으로 침해하거나 과도하게 제한한다고 볼 수 없다고 판단되었다.|
5|⑤|01|O|대학자치의 내용으로서 대학은 인사, 학사, 시설, 재정 등에 관한 자주적 결정권을 가진다.|
6|①|01|O|대한민국은 침략적 전쟁을 부인한다.|
6|②|01|O|외국인의 법적 지위는 국제법과 조약이 정하는 바에 의하여 보장되므로 상호주의가 기본이 된다.|
6|③|01|X|조약의 체결과 비준권은 대통령에게 있고, 국회는 헌법이 정한 중요 조약에 대하여 동의권을 가진다.|조약의 체결권은 대통령에게 있고 비준권은 국회에 속한다고 한 부분
6|④|01|O|헌법에 의하여 체결·공포된 조약과 일반적으로 승인된 국제법규는 국내법과 같은 효력을 가진다.|
6|⑤|01|O|집단학살 금지, 포로에 관한 제네바협정, 부전조약 등은 일반적으로 승인된 국제법규의 예로 들 수 있다.|
7|①|01|O|대법원, 헌법재판소, 중앙선거관리위원회뿐 아니라 국회도 헌법상 내부규율에 관한 규칙을 독자적으로 제정할 수 있다.|
7|②|01|X|중앙선거관리위원회 위원장은 위원 중에서 호선한다.|중앙선거관리위원회 위원장을 대통령이 임명한다고 한 부분
7|③|01|X|선거에 관한 경비는 법률이 정하는 경우를 제외하고 정당 또는 후보자에게 부담시킬 수 없다.|선거경비를 수익자부담 원칙에 따라 정당 또는 후보자가 원칙적으로 부담한다고 한 부분
7|④|01|X|각급 선거관리위원회는 선거사무와 국민투표사무에 관하여 관계 행정기관에 필요한 지시를 할 수 있고, 이는 헌법상 명시되어 있다.|중앙선거관리위원회만 헌법상 관계 행정기관 지시권이 명시되어 있다고 한 부분
7|⑤|01|X|중앙선거관리위원회 위원은 정당에 가입하거나 정치에 관여할 수 없다.|중앙선거관리위원회 위원이 당적을 가질 수 있다고 한 부분
8|①|01|O|공무원은 직무상 의무와 청렴의무 등 높은 윤리적·도덕적 의무를 부담하고, 직업공무원제도 보장에 따라 정치적 중립성, 신분보장, 생활보장을 받는다.|
8|②|01|O|지방공사와 지방공단의 임직원을 형법상 뇌물죄 적용에서 공무원으로 보도록 한 지방공기업법 규정은 평등원칙과 죄형법정주의에 위배되지 않는다고 판단되었다.|
8|③|01|O|금고 이상의 형의 집행유예판결을 받은 공무원을 당연퇴직사유로 정한 것은 공익과 신분상 불이익의 균형을 고려할 때 위헌이라고 볼 수 없다고 판단되었다.|
8|④|01|O|일반 공상공무원에게 군인·경찰상이공무원과 달리 연금 및 사망일시금을 지급하지 않는 것이 합리적 이유 없는 차별이라고 단정할 수 없다고 판단되었다.|
8|⑤|01|X|공무원의 공무 외 집단행위를 금지한 지방공무원법 규정은 공무원 신분상 의무를 정한 것으로 언론·출판의 자유와 집회·결사의 자유의 본질적 내용을 과도하게 침해한다고 볼 수 없다.|공무원의 집단행위 금지 규정이 기본권의 본질적 내용을 과도하게 침해한다고 한 부분
9|①|01|O|헌법상 집회의 자유는 집회를 통하여 형성된 의사를 집단적으로 표현하고 불특정 다수인의 의사에 영향을 줄 자유를 포함하므로 시위의 자유도 보호한다.|
9|②|01|O|집회의 자유는 민주사회에서 중요한 역할을 하지만 집단행동의 속성상 공공의 안녕질서 등과 충돌할 가능성이 있어 제한 필요성이 상대적으로 강하게 인정될 수 있다.|
9|③|01|O|집회의 자유로 보호되는 것은 평화적·비폭력적 집회에 한정되고, 폭력 등을 사용한 의견 강요는 헌법적으로 보호될 수 없다.|
9|④|01|X|사전신고 없이 옥외집회나 시위를 주최한 사람에게 형벌을 부과하는 것이 그 자체로 헌법에 위배된다고 볼 수는 없다.|미신고 옥외집회·시위 주최자에게 형벌을 부과하는 규정이 헌법에 위배된다고 한 부분
9|⑤|01|O|야간 옥외집회에 관하여 다른 옥외집회보다 상대적으로 규제를 강화하는 집회 및 시위에 관한 법률 규정은 헌법에 위배되지 않는다고 본 결정례가 있었다.|
10|①|01|X|명예훼손적 보도에 대한 헌법적 심사기준은 피해자가 공적 인물인지 사인인지, 표현 대상이 공적 관심사인지 사적 영역인지에 따라 차이를 둘 수 있다.|명예훼손적 보도 심사기준에 공적 인물 여부와 공적 관심사 여부에 따른 차이를 두어서는 안 된다고 한 부분
10|②|01|O|사생활의 비밀과 자유는 사생활이 침해되거나 공개되지 않을 소극적 권리뿐 아니라 자신에 관한 정보를 자율적으로 통제할 적극적 권리까지 보장하려는 취지를 가진다.|
10|③|01|O|사생활의 비밀과 자유에 관한 헌법규정은 1980년 제8차 헌법개정에서 신설되었다.|
10|④|01|O|일반 도로 운전 중 좌석안전띠 착용 여부는 사생활의 기본조건이나 인격적 핵심영역으로 보기 어려우므로 안전띠 착용의무는 사생활의 비밀과 자유를 침해하지 않는다고 판단되었다.|
10|⑤|01|O|국정감사·조사권은 개인의 사생활을 침해하거나 계속 중인 재판 또는 수사 중인 사건의 소추에 관여할 목적으로 행사되어서는 안 된다.|
11|①|01|O|법원이 당사자의 위헌제청신청에 관한 결정을 한 경우 당사자는 이에 대하여 항고할 수 없다.|
11|②|01|O|헌법재판소의 법률 위헌결정은 법원, 그 밖의 국가기관 및 지방자치단체를 기속한다.|
11|③|01|O|위헌으로 결정된 법률 또는 법률조항에 근거한 유죄 확정판결에 대하여는 재심을 청구할 수 있다.|
11|④|01|O|행정처분의 근거 법률이 헌법에 위반된다는 사유는 특별한 사정이 없는 한 취소소송의 전제가 될 수 있을 뿐 당연무효사유라고 볼 수는 없다.|
11|⑤|01|X|법원이 위헌법률심판을 제청하면 당해 소송사건 재판은 원칙적으로 정지되고, 긴급한 경우에도 종국재판까지 할 수 있는 것은 아니다.|위헌법률심판 제청 후 긴급한 경우 법원이 소송절차를 진행하여 종국재판을 할 수 있다고 한 부분
12|①|01|O|대법원장은 국회의 동의를 얻어 대통령이 임명한다.|
12|②|01|O|대법관은 대법원장의 제청으로 국회의 동의를 얻어 대통령이 임명한다.|
12|③|01|X|헌법재판소 재판관 9인은 대통령이 임명하지만, 그 중 3인은 국회에서 선출하는 사람, 3인은 대법원장이 지명하는 사람을 임명하므로 모든 재판관 임명에 국회의 동의가 필요한 것은 아니다.|헌법재판관 전원을 대통령이 국회의 동의를 얻어 임명한다고 한 부분
12|④|01|O|대법원장이 아닌 법관은 법률이 정하는 바에 따라 연임할 수 있다.|
12|⑤|01|O|사법권은 법관으로 구성된 법원에 속한다.|
13|①|01|O|헌법상 재판청구권이 모든 사건에 관하여 대법원에 상고하여 재판받을 권리를 부여하는 것은 아니다.|
13|②|01|O|변호사 아닌 사람이 금품 등 이익을 얻을 목적으로 법률사무를 취급하는 것을 금지하고 처벌하는 규정은 직업선택의 자유를 침해한다고 볼 수 없다.|
13|③|01|O|고소·고발장 작성을 법무사에게만 허용하고 일반행정사에게 허용하지 않은 법률규정은 일반행정사의 직업선택의 자유나 평등권을 침해한다고 볼 수 없다.|
13|④|01|O|행정사에게 모든 겸직을 금지하고 그 위반행위를 징역형을 포함하여 형사처벌하도록 한 법률은 직업선택의 자유를 침해한다.|
13|⑤|01|X|무자격자의 일반행정사 업무수행은 형사처벌하면서 미등록 외국어번역행정사 업무수행은 과태료만 부과하는 차이가 합리적 이유 없는 차별이라고 볼 수는 없다.|무자격 일반행정사와 미등록 외국어번역행정사의 제재 차이가 평등원칙에 위반된다고 한 부분
14|①|01|O|토지소유자의 주소 또는 거소 불명으로 협의취득 협의를 할 수 없을 때 공시송달로 협의에 갈음하도록 하는 것은 재산권의 본질적 내용을 침해한다고 판단되었다.|
14|②|01|O|상속회복청구권의 행사기간을 상속개시일부터 10년으로 제한하는 것은 재산권의 본질적 내용을 침해한다고 판단되었다.|
14|③|01|X|공무원이 퇴직 후 국가안보 등에 관한 법을 위반한 경우 연금급여를 제한하는 것은 재산권 제한의 한계를 벗어나 위헌으로 판단될 수 있다.|퇴직 후 국가안보 관련 법 위반에 따른 연금급여 제한이 위헌이 아니라고 한 부분
14|④|01|O|신고로 확정되는 국세에서 신고일 뒤 설정된 전세권·질권·저당권 담보채권보다 국세를 우선징수하도록 하는 것은 재산권의 본질적 내용을 침해한다고 볼 수 없다고 판단되었다.|
14|⑤|01|O|경매절차에서 매각허가결정 항고 시 매각대금의 10분의 1에 해당하는 보증을 공탁하도록 하는 것은 재산권의 본질적 내용을 침해한다고 볼 수 없다고 판단되었다.|
15|①|01|O|현행 헌법은 형사피해자의 해당 사건 공판절차 진술권을 신설하였다.|
15|②|01|O|현행 헌법은 국가가 여자, 모성, 노인, 청소년의 권익보호와 복지향상을 위하여 노력하여야 한다는 규정을 명문화하였다.|
15|③|01|O|현행 헌법은 대통령직선제를 도입하고 대통령 임기를 5년으로 단축하였다.|
15|④|01|X|현행 헌법은 대통령의 국회해산권을 엄격히 제한한 것이 아니라 국회해산권 자체를 두지 않았다.|현행 헌법이 긴급한 경우에 한하여 대통령의 국회해산권 행사를 허용한다고 한 부분
15|⑤|01|O|현행 헌법은 헌법위원회를 폐지하고 헌법재판소를 신설하였다.|
16|①|01|O|지방자치단체의 종류는 법률로 정한다.|
16|②|01|O|헌법재판소는 국가기관과 지방자치단체 사이 및 지방자치단체 상호간 권한쟁의심판을 관장한다.|
16|③|01|O|지방자치단체는 주민의 복리에 관한 사무를 처리하고 재산을 관리하며 법령의 범위 안에서 자치에 관한 규정을 제정할 수 있다.|
16|④|01|O|지방자치단체에는 의회를 둔다.|
16|⑤|01|X|지방의회의 조직·권한·의원선거, 지방자치단체장의 선임방법, 그 밖의 지방자치단체 조직과 운영에 관한 사항은 모두 법률로 정한다.|지방자치단체장의 선임방법과 조직·운영 사항을 조례로 정한다고 한 부분
17|①|01|O|기본권은 원칙적으로 법률로 제한하지만, 법률이 구체적으로 범위를 정하여 위임하면 대통령령에 의한 기본권 제한도 가능하다.|
17|②|01|O|기본권 최대보장과 최소제한 원칙은 일반적 법률유보에 의한 제한과 헌법 직접규정에 의한 제한을 해석할 때에도 존중되어야 한다.|
17|③|01|O|본질적 내용 침해금지원칙에서 본질적 내용은 각 기본권의 특유한 내용을 의미하고, 근로3권이 유명무실해질 정도에 이르면 본질적 내용 침해가 된다.|
17|④|01|X|노래연습장에 18세 미만자의 출입을 금지하는 것은 직업행사의 자유를 제한하지만 피해최소성과 법익균형성에 반하여 위헌이라고 볼 수 없다고 판단되었다.|노래연습장 18세 미만자 출입금지가 직업행사의 자유를 침해하여 헌법에 위반된다고 한 부분
17|⑤|01|O|미결수용자와 변호인이 아닌 사람 사이의 서신검열은 질서유지 또는 공공복리를 위한 최소한의 제한으로서 헌법에 위반된다고 할 수 없다고 판단되었다.|
18|①|01|O|무죄추정원칙은 증거법에 한정되지 않고 수사절차부터 공판절차까지 형사절차 전 과정을 지배하는 지도원리이다.|
18|②|01|O|도주나 증거인멸 우려 또는 조사실 안전·질서유지를 위한 필요가 없는데 피의자에게 수갑과 포승을 채운 채 조사받도록 한 조치는 무죄추정원칙에 위배된다.|
18|③|01|O|미결수용자가 수사 또는 재판을 받기 위하여 수용시설 밖으로 나올 때 사복을 입지 못하고 재소자용 의류를 입게 하는 것은 무죄추정원칙에 위배된다.|
18|④|01|O|사립학교법상 형사사건으로 기소된 교원에게 필요적으로 직위해제처분을 하도록 하는 것은 무죄추정원칙에 위배된다.|
18|⑤|01|X|행정청의 과징금부과처분에 판결 확정 전 공정력과 집행력을 인정하는 것은 형벌집행과 같다고 볼 수 없어 무죄추정원칙에 위배되지 않는다.|과징금부과처분의 공정력과 집행력이 무죄추정원칙에 위배된다고 한 부분
19|①|01|O|위임명령은 일반적으로 헌법에 근거하고 법률의 구체적 위임에 따라 행정부가 발하는 명령을 말한다.|
19|②|01|O|위임명령과 집행명령은 모두 행정작용이므로 헌법이나 법률에 위반되면 효력이 인정될 수 없다.|
19|③|01|O|행정입법의 위헌·위법 여부가 재판의 전제가 되는 경우 대법원은 이에 관하여 최종심사권을 가진다.|
19|④|01|O|대통령령의 내용이 헌법에 위반되더라도 그 사정만으로 정당하고 적법하게 입법권을 위임한 수권법률조항까지 곧바로 위헌이 되는 것은 아니다.|
19|⑤|01|X|시행령의 근거 법률에 대하여 헌법재판소가 위헌결정을 한 경우 그 시행령이 당연히 유효하여 당해 사건에 항상 적용되어야 하는 것은 아니다.|근거 법률 위헌결정 후에도 시행령이 당연히 유효하여 항상 적용되어야 한다고 한 부분
20|①|01|X|헌법상 법률사항에 대한 입법은 원칙적으로 국회가 담당하며, 국회 밖 기관에 일반적·포괄적으로 위임할 수는 없다.|국회 밖 기관에 일반적·포괄적 입법위임도 가능하다고 한 부분
20|②|01|X|법률안 제출권은 국회의원뿐 아니라 정부도 가진다.|법률안 제출권을 국회의원만 가진다고 한 부분
20|③|01|X|소급입법에 의하여 참정권을 제한하는 법률은 허용되지 않는다.|소급입법으로 참정권을 제한할 수 있다고 한 부분
20|④|01|X|대통령은 법률안 일부에 대하여 또는 법률안을 수정하여 재의를 요구할 수 없다.|대통령이 법률안 일부에 대하여 환부하고 재의를 요구할 수 있다고 한 부분
20|⑤|01|O|법원은 법률의 위헌 여부가 재판의 전제가 된 경우에만 헌법재판소에 위헌법률심판을 제청할 수 있다.|
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
        raise ValueError("cannot locate 2007 constitution section")
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
        qid = f"2007-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2007-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2007-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v013_2007_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2007-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
