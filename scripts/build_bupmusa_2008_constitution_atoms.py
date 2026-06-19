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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2008" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2008_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2008"
TEXT_DIR = PRIVATE_ROOT / "text" / "2008"
RAW_PDF_PATH = RAW_DIR / "2008_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2008_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2008_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2008_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2008_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2008_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2008_bupmusa_1st"
YEAR = 2008
ROUND = 14
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
    {"title": "2008 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2008/48828064"},
    {"title": "2008 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2008/92300"},
    {"title": "제14회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?act=procFileDownload&file_srl=92301&module=file&sid=d1271676939c72a342e87cb615a7d79d"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "③",
    3: "④",
    4: "④",
    5: "④",
    6: "②",
    7: "⑤",
    8: "③",
    9: "①",
    10: "②",
    11: "③",
    12: "⑤",
    13: "②",
    14: "③",
    15: "②",
    16: "④",
    17: "④",
    18: "①",
    19: "③",
    20: "①",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    10: "single-best-true",
    11: "single-best-true",
})

FALSE_LABELS = {
    1: {"⑤"},
    2: {"③"},
    3: {"④"},
    4: {"④"},
    5: {"④"},
    6: {"②"},
    7: {"⑤"},
    8: {"③"},
    9: {"①"},
    10: {"①", "③", "④", "⑤"},
    11: {"①", "②", "④", "⑤"},
    12: {"⑤"},
    13: {"②"},
    14: {"③"},
    15: {"②"},
    16: {"④"},
    17: {"④"},
    18: {"①"},
    19: {"③"},
    20: {"①"},
}

TOPICS = {
    1: "직업선택의 자유",
    2: "국회 의장단과 교섭단체",
    3: "탄핵제도",
    4: "수용자 기본권",
    5: "신체의 자유",
    6: "재판청구권",
    7: "국회 권한과 절차",
    8: "혼인·가족생활과 평등",
    9: "선거제도",
    10: "대통령 권한과 국회 통제",
    11: "국민의 의무",
    12: "헌법재판소",
    13: "국회의원 지위",
    14: "교육제도",
    15: "행정부",
    16: "죄형법정주의",
    17: "정당",
    18: "대법원",
    19: "정신적 자유",
    20: "청원권·형사보상·재판청구권",
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
1|①|01|O|변호사 아닌 사람의 법률사무 취급 및 알선을 금지하는 변호사법 규정은 일반 국민의 직업선택의 자유를 과도하게 제한한다고 볼 수 없다.|
1|②|01|O|의료인이 아닌 사람의 의료행위를 금지·처벌하는 구 의료법 규정은 의료행위의 위험성과 국민보건 보호 필요성에 비추어 비례원칙에 반하지 않는다고 판단되었다.|
1|③|01|O|군법무관 임용시험 합격자에게 군법무관시보 임용일부터 10년간 근무하여야 변호사 자격을 유지하도록 한 제도는 직업선택의 자유를 침해하지 않는다고 판단되었다.|
1|④|01|O|2000년 보건복지부령상 시각장애인만 안마사 자격인정을 받을 수 있도록 한 비맹제외기준은 일반인의 직업선택의 자유를 침해하여 헌법에 위반된다고 판단되었다.|
1|⑤|01|X|금고 이상의 형 집행 종료 후 5년이 지나지 않은 사람을 변호사 결격사유로 정한 것은 직업선택의 자유의 본질적 내용을 침해한다고 볼 수 없다.|변호사 결격사유가 직업선택의 자유를 본질적으로 침해하여 입법재량을 일탈하였다고 한 부분
2|①|01|O|국회는 의장 1인과 부의장 2인을 선출하고, 의장이 사고가 있을 때에는 의장이 지정하는 부의장이 그 직무를 대리한다.|
2|②|01|O|국회의장과 부의장의 임기는 2년이고, 총선거 후 처음 선출된 의장과 부의장의 임기는 선출일부터 의원 임기개시 후 2년이 되는 날까지이다.|
2|③|01|X|국회의장은 원칙적으로 당적을 가질 수 없지만, 부의장에게 같은 당적 보유 금지가 당연히 적용되는 것은 아니다.|의장과 부의장이 모두 원칙적으로 당적을 가질 수 없다고 한 부분
2|④|01|O|국회의장과 부의장은 국회에서 무기명투표로 선거하고 재적의원 과반수의 득표로 당선된다.|
2|⑤|01|O|국회에 20인 이상의 소속의원을 가진 정당은 하나의 교섭단체가 되고, 다른 교섭단체에 속하지 않는 20인 이상의 의원도 따로 교섭단체를 구성할 수 있다.|
3|①|01|O|현행 헌법은 탄핵소추 대상에 검사를 명시적으로 열거하고 있지 않다.|
3|②|01|O|감사위원에 대하여도 국회는 탄핵소추권을 가진다.|
3|③|01|O|탄핵소추 발의가 있는 경우 국회가 법제사법위원회에 회부하기로 의결하지 않으면 본회의에서 무기명투표로 탄핵소추 여부를 표결한다.|
3|④|01|X|헌법재판소는 국회의 탄핵소추절차에 적법절차원칙이 직접 적용된다고 보지는 않았다.|헌법재판소가 적법절차원칙이 탄핵소추절차에도 직접 적용된다고 판시하였다고 한 부분
3|⑤|01|O|탄핵결정은 공직에서 파면함에 그치며, 그 결정으로 민사상 또는 형사상 책임이 면제되지는 않는다.|
4|①|01|O|마약류 관련 수형자에게 마약류반응검사를 위한 소변 제출을 요구한 행위는 법관의 영장을 필요로 하는 강제처분이라고 할 수 없다고 판단되었다.|
4|②|01|O|구속 피의자에 대한 계구사용은 도주, 폭행, 소요, 자해 또는 자살 위험이 구체적으로 드러나 이를 제거할 필요가 있을 때 필요한 범위에서 이루어져야 한다.|
4|③|01|O|구금·수용시설 수용자에 대한 신체검사는 인격권과 신체의 자유를 제한하더라도 본질적 내용을 침해하거나 과잉금지원칙에 위배되어서는 안 된다.|
4|④|01|X|금치처분을 받은 사람의 접견, 서신수발, 운동을 일률적으로 금지하는 것은 수용자의 기본권을 과도하게 제한하여 헌법에 위반될 수 있다.|금치처분자의 접견·서신수발·운동 금지가 헌법에 위반되지 않는다고 한 부분
4|⑤|01|O|선거일 현재 금고 이상의 형 선고를 받고 그 집행이 종료되지 않은 사람의 선거권을 제한하는 규정은 위헌적 법률조항이라고 볼 수 없다고 판단되었다.|
5|①|01|O|헌법은 체포 또는 구속을 당한 사람의 가족 등 법률이 정하는 사람에게 그 이유와 일시·장소가 지체 없이 통지되어야 한다고 규정한다.|
5|②|01|O|비상계엄이 선포된 때에는 법률이 정하는 바에 따라 영장제도에 관하여 특별한 조치를 할 수 있다.|
5|③|01|O|일사부재리 또는 이중처벌금지원칙에서 처벌은 원칙적으로 국가 형벌권 실행으로서의 과벌을 의미하고, 국가의 모든 제재나 불이익처분이 포함되는 것은 아니다.|
5|④|01|X|체포·구속적부심사 결정에 대하여 검사와 피의자는 모두 항고할 수 없다고 보는 것이 형사소송법의 구조에 맞다.|검사만 항고하지 못하고 피의자는 항고할 수 있다고 한 부분
5|⑤|01|O|자백이 유일한 불리한 증거일 때 유죄의 증거로 삼거나 처벌할 수 없다는 원칙은 즉결심판절차에도 적용된다.|
6|①|01|O|모든 국민은 신속한 재판을 받을 권리를 가진다.|
6|②|01|X|반국가행위자의 처벌에 관한 특별조치법이 피고인의 출석 없이는 상소할 수 없도록 제한하고 상소권회복청구를 전면 봉쇄한 것은 재판청구권을 침해한다고 판단되었다.|상소 제한과 상소권회복청구 전면 봉쇄가 재판청구권을 침해하지 않는다고 한 부분
6|③|01|O|군인 또는 군무원이 아닌 국민은 헌법이 정한 예외적 경우를 제외하고 군사법원의 재판을 받지 않을 권리를 가진다.|
6|④|01|O|형사피해자는 법률이 정하는 바에 따라 해당 사건의 재판절차에서 진술할 수 있는 권리를 가진다.|
6|⑤|01|O|관세법상 통고처분을 행정심판이나 행정소송 대상에서 제외하는 것은 법관에 의한 재판을 받을 권리나 적법절차원칙에 반한다고 볼 수 없다고 판단되었다.|
7|①|01|O|국회의 정기회는 법률이 정하는 바에 따라 매년 1회 집회되고, 정기회의 회기는 100일을 초과할 수 없다.|
7|②|01|O|국회에 제출된 법률안 기타 의안은 회기 중 의결되지 못하였다는 이유로 폐기되지 않지만, 국회의원의 임기가 만료된 때에는 폐기된다.|
7|③|01|O|대통령의 재의요구가 있는 법률안은 국회가 재적의원 과반수 출석과 출석의원 3분의 2 이상의 찬성으로 전과 같은 의결을 하면 법률로 확정된다.|
7|④|01|O|국회는 정부의 동의 없이 정부가 제출한 지출예산 각항의 금액을 증가하거나 새 비목을 설치할 수 없다.|
7|⑤|01|X|국무총리에 대한 탄핵소추 의결에는 국회재적의원 3분의 2 이상이 아니라 국회재적의원 과반수의 찬성이 필요하다.|국무총리 탄핵소추 의결에 국회재적의원 3분의 2 이상의 찬성이 필요하다고 한 부분
8|①|01|O|헌법은 혼인과 가족생활이 개인의 존엄과 양성의 평등을 기초로 성립·유지되어야 한다고 규정한다.|
8|②|01|O|부부의 자산소득을 합산하여 과세하는 것은 혼인한 부부를 사실혼 부부나 독신자보다 불리하게 차별하여 헌법에 위반된다고 판단되었다.|
8|③|01|X|국가유공자 가족에게 만점의 10퍼센트 가산점을 일률적으로 부여하는 것은 일반 공직시험 응시자의 평등권을 침해한다고 판단되었다.|국가유공자 가족 10퍼센트 가산점이 일반 공직시험 응시자의 평등권을 침해하지 않는다고 한 부분
8|④|01|O|호주제는 남계혈통 중심의 가 유지·계승을 강요하여 혼인과 가족생활에 관한 개인과 가족의 자율적 결정권을 존중하라는 헌법 제36조 제1항에 부합하지 않는다고 판단되었다.|
8|⑤|01|O|사업주가 근로여성의 혼인, 임신 또는 출산을 퇴직사유로 예정하는 근로계약을 체결하는 것은 허용되지 않는다.|
9|①|01|X|보통선거원칙에 반하는 선거권 제한도 헌법 제37조 제2항의 요건을 충족하면 정당화될 수 있다.|보통선거원칙에 반하는 선거권 제한은 헌법 제37조 제2항에 의하여도 정당화될 수 없다고 한 부분
9|②|01|O|헌법재판소는 국회의원 지역선거구 사이의 인구편차가 평균인구수 기준 상하 50퍼센트 편차를 초과하면 위헌이라고 본 바 있다.|
9|③|01|O|모든 국민은 법률이 정하는 바에 따라 공무담임권을 가진다.|
9|④|01|O|선거에 관한 경비는 법률이 정하는 경우를 제외하고 정당 또는 후보자에게 부담시킬 수 없다.|
9|⑤|01|O|선거운동은 각급 선거관리위원회의 관리 아래 법률이 정하는 범위 안에서 하여야 한다.|
10|①|01|X|대통령의 긴급처분·명령은 사후에 지체 없이 국회 승인을 얻어야 하므로 국회 통제를 전혀 요하지 않는 권한이 아니다.|긴급처분·명령권이 국회의 동의나 승인을 요하지 않는다고 본 부분
10|②|01|O|대통령의 비상계엄 선포는 국회의 사전 동의나 승인을 요하지 않지만, 대통령은 지체 없이 국회에 통고하여야 하고 국회의 해제 요구가 있으면 해제하여야 한다.|
10|③|01|X|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|일반사면권이 국회의 동의나 승인을 요하지 않는다고 본 부분
10|④|01|X|대통령의 선전포고에는 국회의 동의가 필요하다.|선전포고가 국회의 동의나 승인을 요하지 않는다고 본 부분
10|⑤|01|X|대통령이 헌법재판소장을 임명하려면 국회의 동의를 얻어야 한다.|헌법재판소장 임명이 국회의 동의나 승인을 요하지 않는다고 본 부분
11|①|01|X|납세의 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이다.|납세의 의무가 현행 헌법상 명문 국민의 의무가 아니라고 본 부분
11|②|01|X|자녀에게 초등교육과 법률이 정하는 교육을 받게 할 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이다.|자녀에게 초등교육과 법률이 정하는 교육을 받게 할 의무가 현행 헌법상 명문 국민의 의무가 아니라고 본 부분
11|③|01|O|모성 보호를 위하여 노력할 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이 아니다.|
11|④|01|X|환경보전을 위하여 노력할 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이다.|환경보전을 위하여 노력할 의무가 현행 헌법상 명문 국민의 의무가 아니라고 본 부분
11|⑤|01|X|국방의 의무는 현행 헌법이 국민의 의무로 명문 규정한 사항이다.|국방의 의무가 현행 헌법상 명문 국민의 의무가 아니라고 본 부분
12|①|01|O|헌법재판소 재판관은 정당에 가입할 수 없다.|
12|②|01|O|헌법재판소법은 사인이 당사자인 경우 원칙적으로 변호사강제주의를 채택하고 있다.|
12|③|01|O|헌법소원의 인용결정은 모든 국가기관과 지방자치단체를 기속한다.|
12|④|01|O|입법부작위에 대한 헌법소원은 명시적 입법위임 또는 구체적 기본권 보장을 위한 국가의 행위의무가 명백한 경우가 아니면 원칙적으로 인정되지 않는다.|
12|⑤|01|X|국가기관은 국민의 기본권을 보호·실현할 책임을 지는 지위에 있으므로 원칙적으로 헌법소원을 청구할 수 있는 기본권 주체가 아니다.|국가기관도 헌법소원을 청구할 수 있다고 한 부분
13|①|01|O|국회는 국회재적의원 3분의 2 이상의 찬성으로 의원을 제명할 수 있다.|
13|②|01|X|비례대표국회의원이 소속 정당에서 제명되어 당적을 이탈한 경우에는 의원직을 상실하지 않는다.|비례대표국회의원이 소속 정당에서 제명되어 당적을 이탈하면 퇴직된다고 한 부분
13|③|01|O|국회의원은 법률이 정하는 정부투자기관의 임직원을 겸직할 수 없다.|
13|④|01|O|국회의원은 국회에서 직무상 행한 발언과 표결에 관하여 국회 밖에서 책임을 지지 않는다.|
13|⑤|01|O|국회의원의 청렴의무는 헌법에 명문으로 규정되어 있다.|
14|①|01|O|현재 우리나라의 의무교육은 6년의 초등교육과 3년의 중등교육으로 한다.|
14|②|01|O|국가와 지방자치단체는 학문·예술 또는 체육 등의 분야에서 재능이 특히 뛰어난 사람의 교육에 필요한 시책을 수립·실시할 법률상 의무가 있다.|
14|③|01|X|국가와 지방자치단체가 설립·경영하는 학교에는 유아교육을 위한 학교도 포함될 수 있다.|국가와 지방자치단체가 설립·경영하는 학교에 유아교육을 위한 곳이 포함되지 않는다고 한 부분
14|④|01|O|교원은 특정 정당이나 정파를 지지하거나 반대하기 위하여 학생을 지도하거나 선동해서는 안 되며, 법률이 정하는 바에 따라 다른 공직에 취임할 수 있다.|
14|⑤|01|O|교원노동조합과 그 조합원은 파업·태업 등 업무의 정상적 운영을 저해하는 쟁의행위를 할 수 없다.|
15|①|01|O|국무회의는 헌법개정 없이 폐지할 수 없는 헌법상 필수기관이다.|
15|②|01|X|행정각부의 장을 국무위원 중에서 국무총리의 제청으로 대통령이 임명한다는 규정은 1987년 헌법개정 때 새로 신설된 조항이라고 볼 수 없다.|행정각부의 장 임명 규정이 1987년 헌법개정 때 신설되었다고 한 부분
15|③|01|O|헌법은 국영기업체 관리자의 임명을 국무회의 심의사항으로 명문 규정하고 있다.|
15|④|01|O|국무회의는 의원내각제의 국무회의와 같은 의결기관이 아니라 심의기관이다.|
15|⑤|01|O|감사원은 대통령에 소속되어 있지만 직무에 관하여 독립의 지위를 가진다.|
16|①|01|O|모든 국민은 행위시의 법률에 의하여 범죄를 구성하지 않는 행위로 소추되지 않는다.|
16|②|01|O|모든 국민은 법률과 적법절차에 의하지 않고는 처벌·보안처분 또는 강제노역을 받지 않는다.|
16|③|01|O|죄형법정주의에서 법률은 원칙적으로 형식적 의미의 법률을 뜻하므로 명령이나 규칙으로 범죄와 형벌을 규정하는 것은 원칙적으로 허용되지 않는다.|
16|④|01|X|절대적 부정기형은 형의 내용과 범위를 사후에 정하게 하므로 죄형법정주의에 반하여 허용되지 않는다.|절대적 부정기형이 합리성이 인정되는 범위에서 제한적으로 허용된다고 한 부분
16|⑤|01|O|형벌법규의 내용이 애매하거나 적용범위가 지나치게 광범위하면 명확성원칙 등에 반하여 헌법에 위반될 수 있다.|
17|①|01|O|정당의 설립은 자유이고 복수정당제는 보장된다.|
17|②|01|O|정당은 목적, 조직과 활동이 민주적이어야 하며 국민의 정치적 의사형성에 참여하는 데 필요한 조직을 가져야 한다.|
17|③|01|O|정당은 법률이 정하는 바에 따라 국가의 보호를 받고, 국가는 법률이 정하는 바에 따라 정당운영에 필요한 자금을 보조할 수 있다.|
17|④|01|X|정당의 시·도당 법정당원수는 2천인이 아니라 정당법이 정한 1천인 이상 기준을 기준으로 판단하여야 한다.|시·도당이 2천인 이상의 당원을 가져야 한다고 한 부분
17|⑤|01|O|정당이 임기만료 국회의원선거에 참여하여 의석을 얻지 못하고 유효투표총수의 100분의 2 이상도 득표하지 못하면 등록이 취소된다.|
18|①|01|X|대법원장의 임기는 6년이고 중임할 수 없다.|대법원장이 연임할 수 없지만 중임은 가능하다고 한 부분
18|②|01|O|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|
18|③|01|O|헌법은 대법원에 부를 둘 수 있다고 명문으로 규정하고 있다.|
18|④|01|O|대법관회의는 대법관 전원의 3분의 2 이상 출석과 출석인원 과반수 찬성으로 의결한다.|
18|⑤|01|O|대법원장은 대법관회의의 의장이 되고 표결권을 가지며, 가부동수인 때에는 결정권을 가진다.|
19|①|01|O|영상물등급위원회의 상영등급분류보류제도는 헌법이 금지하는 사전검열에 해당하여 헌법에 위반된다고 판단되었다.|
19|②|01|O|신문보도의 명예훼손 표현에 대한 헌법적 심사기준은 피해자가 공적 인물인지 사인인지, 표현 대상이 공적 관심사인지 사적 영역인지에 따라 달라질 수 있다.|
19|③|01|X|청소년유해매체물 결정권한을 청소년보호위원회 등에 부여하는 것이 법관의 고유권한을 박탈하여 재판청구권을 침해한다고 볼 수는 없다.|청소년유해매체물 결정권한 부여가 법관에 의한 재판을 받을 권리를 침해한다고 한 부분
19|④|01|O|정정보도청구권 제도는 언론의 자유의 본질적 내용을 침해하거나 언론기관의 재판청구권을 부당하게 침해한다고 볼 수 없다.|
19|⑤|01|O|대통령선거의 공정을 위하여 선거일 전 일정 기간 여론조사결과 공표를 금지하는 것 자체는 금지기간이 지나치게 길지 않으면 위헌이라고 볼 수 없다.|
20|①|01|X|헌법 제26조는 국가가 청원을 심사할 의무를 명문으로 규정하지만, 청원 처리 결과를 통지할 의무까지 명문으로 규정하고 있지는 않다.|헌법 제26조가 청원 심사의무뿐 아니라 통지의무도 명문으로 규정한다고 한 부분
20|②|01|O|형사피의자로서 구금되었던 사람이 법률이 정하는 불기소처분을 받은 때에는 형사보상을 청구할 수 있다.|
20|③|01|O|배당이의자가 배당이의의 소 첫 변론기일에 출석하지 않으면 소를 취하한 것으로 보는 것은 재판청구권을 침해한다고 볼 수 없다고 판단되었다.|
20|④|01|O|헌법상 법관에 의하여 법률에 의한 재판을 받을 권리에 모든 사건에서 상고심 재판을 받을 권리까지 포함되지는 않는다.|
20|⑤|01|O|타인의 범죄행위로 재산상 피해만을 입은 국민에게는 헌법 제30조의 범죄피해자구조청구권이 인정되지 않는다.|
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
        raise ValueError("cannot locate 2008 constitution section")
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
        qid = f"2008-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2008-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2008-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v014_2008_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2008-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
