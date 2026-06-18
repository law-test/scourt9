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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2016" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2016_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2016"
TEXT_DIR = PRIVATE_ROOT / "text" / "2016"
RAW_PDF_PATH = RAW_DIR / "2016_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2016_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2016_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2016_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2016_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2016_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2016_bupmusa_1st"
YEAR = 2016
ROUND = 22
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 101
MIN_ATOM_COUNT = 120
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS_BY_QUESTION = {
    3: ["가", "나", "다", "라", "마", "바"],
    6: ["가", "나", "다", "라", "마"],
    7: ["가", "나", "다", "라", "마"],
    12: ["가", "나", "다", "라", "마", "바"],
    14: ["가", "나", "다", "라"],
    20: ["가", "나", "다", "라", "마"],
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
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "형사보상 및 명예회복에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사보상및명예회복에관한법률"},
    {"title": "2016 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2016/116303"},
    {"title": "2016 법무사 헌법 확정정답", "publisher": "법원행정처", "url": "https://anaham.tistory.com/13884"},
    {"title": "2016 법무사 헌법 해설", "publisher": "천책상장", "url": "local:2016_법무사_헌법_해설_법무사_천책상장.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "④",
    3: "④",
    4: "④",
    5: "③",
    6: "④",
    7: "⑤",
    8: "⑤",
    9: "②",
    10: "④",
    11: "①",
    12: "③",
    13: "③",
    14: "③",
    15: "②",
    16: "①·②",
    17: "⑤",
    18: "②",
    19: "⑤",
    20: "①",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    3: "count-false",
    6: "count-true",
    7: "count-true",
    12: "count-false",
    14: "combination-true",
    16: "multi-correct-true",
    20: "count-false",
})

FALSE_LABELS = {
    1: {"⑤"},
    2: {"④"},
    3: {"가", "다", "라", "바"},
    4: {"④"},
    5: {"③"},
    6: {"나"},
    7: set(),
    8: {"⑤"},
    9: {"②"},
    10: {"④"},
    11: {"①"},
    12: {"가", "나", "다"},
    13: {"③"},
    14: {"가", "라"},
    15: {"②"},
    16: {"③", "④", "⑤"},
    17: {"⑤"},
    18: {"②"},
    19: {"⑤"},
    20: {"라"},
}

TOPICS = {
    1: "수형자의 기본권",
    2: "근로3권",
    3: "신체의 자유 조문",
    4: "국적",
    5: "공정한 재판을 받을 권리",
    6: "국회 의결정족수",
    7: "사회보장수급권",
    8: "행정부",
    9: "국방의 의무와 군사재판",
    10: "지방자치",
    11: "헌법소원의 보충성",
    12: "국회 조문",
    13: "기본권 주체",
    14: "대통령 임명권",
    15: "혼인과 가족생활",
    16: "검열금지",
    17: "헌법재판과 관습법",
    18: "개인정보자기결정권",
    19: "정당제도",
    20: "직업선택의 자유",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    3: ("헌법", "헌법 제12조", "신체의 자유, 영장주의, 변호인 조력권, 체포·구속적부심사의 조문 문구를 구별하는 지점이다."),
    4: ("국적법+대법원 판례", "국적법 제2조·제3조·제5조·제7조 및 귀화허가 판례", "출생·인지에 의한 국적취득, 귀화요건과 귀화허가 재량을 구별하는 지점이다."),
    6: ("헌법+국회법", "헌법 제63조·제64조·제65조·제77조·제130조 및 국회법 제15조·제54조·제73조·제95조·제138조", "국회 발의·청구·개의·의결정족수를 조문별로 구별하는 지점이다."),
    8: ("헌법", "헌법 제86조·제87조·제88조·제94조·제95조", "국무총리, 국무위원, 국무회의, 총리령·부령의 조문 요건을 구별하는 지점이다."),
    12: ("헌법", "헌법 제41조·제44조·제45조·제47조", "국회의 구성, 의원정수, 불체포특권, 면책특권과 회기 조문을 구별하는 지점이다."),
    14: ("헌법", "헌법 제98조·제104조·제111조·제114조", "대통령이 임명하는 헌법기관 구성원과 다른 기관의 임명·지명 권한을 구별하는 지점이다."),
    16: ("헌법+헌법재판소 결정례", "헌법 제21조 제2항 및 검열금지 관련 결정례", "사전검열 해당 여부에 관한 헌법재판소 판단을 구별하는 지점이다."),
    17: ("헌법+헌법재판소법+헌법재판소 결정례", "헌법재판소법 제47조·제68조·제75조 및 관습법 위헌심판 결정례", "헌법재판의 기속력, 재심판 금지, 국가배상과 관습법 심판대상성을 구별하는 지점이다."),
    20: ("헌법+헌법재판소 결정례", "헌법 제15조 및 직업의 자유 관련 결정례", "직업 해당성, 자격요건 심사강도와 직업수행 제한의 비례심사를 구별하는 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|수형자의 기본권 제한 한계는 헌법 제37조 제2항에 따라 법률로 설정되어야 한다.|
1|①|02|O|수용시설의 안전과 질서유지를 위한 수형자 기본권 제한도 본질적 내용 침해와 과잉금지원칙 위반은 허용되지 않는다.|
1|②|01|O|수형자가 헌법소원 국선대리인 변호사를 접견하는 내용을 녹음·기록한 행위는 재판을 받을 권리를 침해한다.|
1|③|01|O|수용거실 지정은 교도소장의 재량적 판단사항이다.|
1|③|02|O|수용자에게 특정 수용거실 배정을 신청할 권리가 인정된다고 볼 수 없다.|
1|③|03|O|교도소장의 독거수용 거부는 헌법소원심판의 대상인 공권력 행사에 해당하지 않을 수 있다.|
1|④|01|O|금치 처분을 받은 수형자에 대한 절대적 운동 금지는 인간의 존엄과 가치 및 신체의 자유를 침해할 수 있다.|
1|⑤|01|X|외부 재판 출정 시 운동화 착용을 불허한 행위는 공정한 재판을 받을 권리나 평등권을 침해한다고 볼 수 없다.|운동화 착용 불허가 공정한 재판을 받을 권리와 평등권을 침해한다고 한 부분
1|⑤|02|X|외부 재판 출정 시 운동화 착용을 불허한 행위는 인격권과 행복추구권을 침해한다고 볼 수 없다.|운동화 착용 불허가 인격권과 행복추구권을 침해한다고 한 부분
2|①|01|O|제헌헌법은 근로자의 단결·단체교섭·단체행동의 자유를 법률의 범위 안에서 보장하였다.|
2|②|01|O|취업활동 체류자격이 없는 외국인도 노동조합법상 근로자성이 인정되면 노동조합을 결성하거나 가입할 수 있다.|
2|③|01|O|헌법은 사립학교 교원의 단체행동권을 제한하는 명문 규정을 두고 있지 않다.|
2|④|01|X|노동조합 설립신고와 요건 미충족 시 반려 제도는 헌법상 금지된 단체결성 허가제에 해당하지 않는다.|노동조합 설립신고 반려 제도가 단체결성 허가제라고 한 부분
2|④|02|X|노동조합 설립신고 반려 제도는 근로자의 단결권을 과도하게 침해한다고 볼 수 없다.|노동조합 설립신고 반려 제도가 근로자의 단결권을 침해한다고 한 부분
2|⑤|01|O|헌법 제33조 제1항의 단결권은 근로자 개인뿐 아니라 근로자단체 자체의 단결권도 보장한다.|
3|가|01|X|헌법 제12조 제1항은 누구든지 법률에 의하지 아니하고는 체포·구속·압수·수색 또는 심문을 받지 아니한다고 규정한다.|체포·구속·압수·수색 또는 심문 근거에 대통령령을 포함한 부분
3|나|01|O|모든 국민은 고문을 받지 아니하며 형사상 자기에게 불리한 진술을 강요당하지 않는다.|
3|다|01|X|현행범이 아닌 긴급한 경우 사후영장청구는 장기 3년 이상의 형에 해당하는 죄에 관하여 허용된다.|사후영장청구 요건을 장기 1년 이상의 형으로 낮춘 부분
3|라|01|X|누구든지 체포 또는 구속을 당한 때에는 즉시 변호인의 조력을 받을 권리를 가진다.|변호인 조력권 보장 시점을 48시간 이내로 제한한 부분
3|마|01|O|체포 또는 구속을 당하는 사람에게는 그 이유와 변호인의 조력을 받을 권리가 고지되어야 한다.|
3|마|02|O|체포 또는 구속을 당한 사람의 가족 등 법률이 정하는 자에게는 그 이유와 일시·장소가 지체 없이 통지되어야 한다.|
3|바|01|X|체포 또는 구속을 당한 사람은 적부의 심사를 법원에 청구할 권리를 가진다.|체포·구속적부심사 청구기관에 검찰을 포함한 부분
4|①|01|O|출생 당시에 부 또는 모가 대한민국 국민인 사람은 출생과 동시에 대한민국 국적을 취득한다.|
4|①|02|O|부모가 모두 분명하지 않거나 국적이 없는 경우 대한민국에서 출생한 사람은 출생과 동시에 대한민국 국적을 취득한다.|
4|②|01|O|대한민국 국민인 부 또는 모에 의하여 인지된 미성년자는 일정 요건을 갖추면 신고로 대한민국 국적을 취득할 수 있다.|
4|②|02|O|인지에 의한 국적취득에는 출생 당시에 부 또는 모가 대한민국 국민이었을 것이 요구된다.|
4|③|01|O|국적법상 일반귀화에는 5년 이상 계속하여 대한민국에 주소가 있을 것이 요구된다.|
4|③|02|O|국적법상 일반귀화에는 성년, 품행 단정, 생계유지능력과 기본소양 요건이 요구된다.|
4|④|01|X|대한민국에 특별한 공로가 있는 사람도 특별귀화허가를 받으려면 대한민국에 주소가 있어야 한다.|특별공로자가 대한민국에 주소 없이 귀화허가를 받을 수 있다고 한 부분
4|④|02|X|특정 분야의 우수능력자로서 대한민국 국익에 기여할 것으로 인정되는 사람도 특별귀화허가를 받으려면 대한민국에 주소가 있어야 한다.|우수능력자가 대한민국에 주소 없이 귀화허가를 받을 수 있다고 한 부분
4|⑤|01|O|법무부장관은 귀화신청인이 귀화요건을 갖추었더라도 귀화허가 여부에 관하여 재량권을 가진다.|
5|①|01|O|검사가 정당한 사유를 밝히지 않고 수사기록 일체의 열람·등사를 전부 거부하면 신속·공정한 재판을 받을 권리를 침해할 수 있다.|
5|①|02|O|검사가 정당한 사유 없이 수사기록 열람·등사를 전부 거부하면 변호인의 조력을 받을 권리를 침해할 수 있다.|
5|②|01|O|검사가 법원 증인으로 채택된 수감자를 반복 소환하여 피고인 측 변호인의 접근을 차단하고 회유·압박하면 공정한 재판을 받을 권리를 침해할 수 있다.|
5|③|01|X|피고인을 일시 퇴정하게 하고 증인을 진술하게 할 수 있도록 한 형사소송법 조항은 피고인의 공정한 재판을 받을 권리를 침해하지 않는다.|증인신문 중 피고인 퇴정 조항이 반대신문권을 완전히 박탈한다고 한 부분
5|④|01|O|약식명령 피고인의 정식재판청구기간을 고지일부터 7일 이내로 정한 것은 재판청구권을 침해한다고 볼 수 없다.|
5|⑤|01|O|자기 또는 배우자의 직계존속을 고소하지 못하게 한 형사소송법 조항은 평등원칙에 위반되지 않는다.|
6|가|01|O|국무총리 해임건의 발의정족수는 국회재적의원 3분의 1 이상이다.|
6|가|02|O|국무총리 탄핵소추 발의정족수는 국회재적의원 3분의 1 이상이다.|
6|나|01|X|국회의원 자격심사 청구정족수는 의원 30인 이상의 연서이다.|국회의원 자격심사 청구정족수와 예산안 수정동의 정족수가 같다고 한 부분
6|나|02|X|예산안 수정동의 정족수는 의원 50인 이상의 찬성이다.|예산안 수정동의 정족수를 의원 자격심사 청구정족수와 같게 본 부분
6|다|01|O|국회 위원회 의사정족수는 재적위원 5분의 1 이상의 출석이다.|
6|다|02|O|국회 본회의 의사정족수는 재적의원 5분의 1 이상의 출석이다.|
6|라|01|O|국회의원 제명에는 국회재적의원 3분의 2 이상의 찬성이 필요하다.|
6|라|02|O|헌법개정안 국회의결에는 국회재적의원 3분의 2 이상의 찬성이 필요하다.|
6|마|01|O|국회의장 선출에는 재적의원 과반수의 득표가 필요하다.|
6|마|02|O|국회의 계엄해제 요구에는 재적의원 과반수의 찬성이 필요하다.|
7|가|01|O|교도시설 수용자에 대한 국민건강보험급여 정지는 수용자의 건강권과 인간다운 생활을 할 권리를 침해한다고 볼 수 없다.|
7|나|01|O|산재보험의 내용과 시행 범위 및 방법은 입법자의 재량영역에 속한다.|
7|나|02|O|산재보험수급권은 산재보험법에 의하여 구체화되는 법률상 권리이다.|
7|다|01|O|국가의 인간다운 생활 보장 의무 이행 여부는 입법 부재나 현저한 불합리성이 있는 경우에 한하여 위헌으로 판단될 수 있다.|
7|라|01|O|공무원연금법상 급여는 사회보장수급권 성격과 재산권 성격을 함께 가진다.|
7|라|02|O|퇴직연금수급권은 퇴직일시금과 퇴직수당수급권보다 상대적으로 사회보장적 급여 성격이 강하다.|
7|마|01|O|일정한 법정요건을 갖춰 발생한 산재보험수급권은 구체적 법적 권리로 보장된다.|
7|마|02|O|산재보험수급권은 경제적·재산적 가치가 있는 공법상 권리로서 헌법상 재산권 보호대상에 포함된다.|
8|①|01|O|군인은 현역을 면한 후가 아니면 국무총리로 임명될 수 없다.|
8|①|02|O|군인은 현역을 면한 후가 아니면 국무위원으로 임명될 수 없다.|
8|②|01|O|국무총리는 국무위원의 해임을 대통령에게 건의할 수 있다.|
8|③|01|O|국무총리 또는 행정각부의 장은 소관사무에 관하여 법률이나 대통령령의 위임 또는 직권으로 총리령 또는 부령을 발할 수 있다.|
8|④|01|O|국무회의는 대통령, 국무총리와 15인 이상 30인 이하의 국무위원으로 구성된다.|
8|⑤|01|X|국무위원은 국무총리의 제청으로 대통령이 임명한다.|국무위원 임명에 국무총리의 제청이 필수적이지 않다고 한 부분
8|⑤|02|X|행정각부의 장은 국무위원 중에서 국무총리의 제청으로 대통령이 임명한다.|국무위원과 행정각부의 장의 임명제청 요건을 다르게 본 부분
9|①|01|O|현역병의 군 입대 전 범죄에 관한 군사법원 재판권 규정은 재판청구권을 침해한다고 볼 수 없다.|
9|②|01|X|전투경찰순경에 대한 징계처분으로 영창을 규정한 구 전투경찰대 설치법 조항은 적법절차원칙에 위배되지 않는다.|전투경찰순경 영창제도가 적법절차원칙에 위배된다고 한 부분
9|③|01|O|산업기능요원 편입 후 1년 이상 종사자에게만 편입취소 후 입영 시 복무기간 단축을 허용한 병역법 조항은 평등권을 침해한다.|
9|④|01|O|헌법 제39조 제2항의 불이익한 처우는 단순한 사실상·경제상 불이익이 아니라 법적 불이익을 의미한다.|
9|⑤|01|O|국방의 의무에는 병역법상 직접적인 병력형성의무뿐 아니라 간접적인 병력형성의무도 포함된다.|
9|⑤|02|O|국방의 의무에는 병력형성 이후 군작전명령에 복종하고 협력하여야 할 의무도 포함된다.|
10|①|01|O|지방자치제도의 헌법적 보장은 주민에 의한 자기통치의 실현을 핵심으로 한다.|
10|①|02|O|지방자치의 본질적 내용인 핵심영역은 입법이나 중앙정부의 침해로부터 보호되어야 한다.|
10|②|01|O|제도적 보장으로서 주민의 자치권은 원칙적으로 개별 주민에게 인정된 기본권이라고 볼 수 없다.|
10|②|02|O|헌법상 주민자치의 범위는 법률로 형성되고 핵심영역이 아닌 한 법률로 제한될 수 있다.|
10|③|01|O|지방자치단체의 조례제정 범위에는 자치사무와 법령에 따라 위임된 단체위임사무가 포함된다.|
10|③|02|O|기관위임사무에 관한 사항은 원칙적으로 지방자치단체 조례의 제정범위에 속하지 않는다.|
10|④|01|X|지방자치단체장이 궐위되거나 공소제기 후 구금상태에 있으면 부단체장이 그 권한을 대행한다.|금고 이상의 형을 선고받고 확정되지 않은 경우까지 권한대행 사유로 포함한 부분
10|⑤|01|O|세 자녀 이상 세대 양육비 지원 조례안은 지방자치단체 고유의 자치사무인 주민복지증진 사무에 해당할 수 있다.|
10|⑤|02|O|주민 편의와 복리증진에 관한 조례안은 제정에 반드시 법률의 개별적 위임이 필요한 것은 아니다.|
11|①|01|X|기소유예처분을 받은 피의자가 범죄혐의를 부인하며 취소를 구하는 헌법소원은 보충성원칙의 예외가 될 수 있다.|기소유예처분을 받은 피의자가 수사기관 진정을 거치지 않았으므로 보충성 요건을 결하였다고 한 부분
11|②|01|O|고용노동부장관의 전교조 시정요구는 권리·의무에 변동을 일으키는 행정행위에 해당할 수 있다.|
11|②|02|O|전교조 시정요구에 대하여 다른 불복절차를 거치지 않고 곧바로 제기한 헌법소원은 보충성 요건을 결할 수 있다.|
11|③|01|O|수사기관의 피의사실 보도자료 배포행위가 범죄행위에 해당하면 고소와 항고 및 재정신청 등 권리구제절차를 거칠 수 있다.|
11|③|02|O|피의사실 보도자료 배포행위에 대한 권리구제절차를 거치지 않은 헌법소원은 보충성 요건을 갖추지 못할 수 있다.|
11|④|01|O|국가인권위원회의 진정 각하 또는 기각결정에 대하여 사전구제절차를 거치지 않은 헌법소원은 보충성 요건을 충족하지 못할 수 있다.|
11|⑤|01|O|정보비공개결정에 대하여 정보공개법상 불복절차를 거치지 않고 곧바로 제기한 헌법소원은 보충성 요건을 결여할 수 있다.|
12|가|01|X|국회는 국민의 보통·평등·직접·비밀선거로 선출된 국회의원으로 구성된다.|국회의원 선거를 공개선거라고 한 부분
12|나|01|X|국회의원의 수는 법률로 정하되 200인 이상이어야 한다.|국회의원 수를 300인 이하로만 정한 부분
12|다|01|X|국회의원은 현행범인 경우를 제외하고 회기 중 국회의 동의 없이 체포 또는 구금되지 않는다.|현행범인 경우에도 국회 동의 없이는 체포 또는 구금되지 않는다고 한 부분
12|라|01|O|국회의원은 국회에서 직무상 행한 발언과 표결에 관하여 국회 외에서 책임을 지지 않는다.|
12|마|01|O|국회의 정기회는 법률이 정하는 바에 따라 매년 1회 집회된다.|
12|마|02|O|국회의 임시회는 대통령 또는 국회재적의원 4분의 1 이상의 요구에 의하여 집회된다.|
12|바|01|O|국회 정기회의 회기는 100일을 초과할 수 없다.|
12|바|02|O|국회 임시회의 회기는 30일을 초과할 수 없다.|
13|①|01|O|태아도 헌법상 생명권의 주체가 되며 국가는 태아의 생명을 보호할 의무가 있다.|
13|①|02|O|초기배아는 독립된 인간과의 개체적 연속성을 확정하기 어려워 기본권 주체성을 인정하기 어렵다.|
13|②|01|O|학생은 국가와 부모의 교육권 범주 안에서 자신의 교육에 관하여 스스로 결정할 권리를 가진다.|
13|②|02|O|학생은 자신의 능력과 개성 및 적성에 맞는 학교를 자유롭게 선택할 권리를 가진다.|
13|③|01|X|외국인의 국내 직업의 자유는 법률에 따른 정부 허가에 의해 발생하는 권리로 볼 수 있다.|근로가 허용된 외국인에게 자격제도 자체를 다툴 직업선택의 자유가 회복된다고 한 부분
13|③|02|X|의료행위 자격제도 자체를 다투는 외국인에게 직업선택의 자유에 관한 기본권 주체성이 인정된다고 볼 수 없다.|근로가 허용된 외국인이 의료인 자격제도 자체를 다툴 수 있다고 한 부분
13|④|01|O|법인은 그 성질에 반하지 않는 범위에서 사회적 신용이나 명예 등 인격권의 주체가 될 수 있다.|
13|④|02|O|법인은 사회적 신용이나 명예 유지와 법인격의 자유로운 발현을 위하여 자율적으로 의사결정하고 행동할 수 있다.|
13|⑤|01|O|대통령은 소속 정당을 위한 정당활동을 할 수 있는 사인의 지위를 가진다.|
13|⑤|02|O|대통령은 사인으로서의 지위와 관련하여 기본권 주체성을 가진다.|
14|가|01|X|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|일반 법관을 대통령이 임명한다고 본 부분
14|나|01|O|감사원 감사위원은 감사원장의 제청으로 대통령이 임명한다.|
14|다|01|O|헌법재판관은 대통령이 임명한다.|
14|다|02|O|헌법재판관 중 국회에서 선출하는 3인도 대통령이 임명한다.|
14|라|01|X|중앙선거관리위원회는 대통령이 임명하는 3인, 국회에서 선출하는 3인, 대법원장이 지명하는 3인의 위원으로 구성된다.|대법원장이 지명하는 중앙선거관리위원을 대통령이 임명한다고 본 부분
15|①|01|O|중혼의 취소청구권자에서 직계비속을 제외한 민법 조항은 합리적 이유 없이 직계비속을 차별하여 평등원칙에 위반된다고 판단되었다.|
15|②|01|X|중혼 취소청구권의 제척기간 또는 소멸사유를 규정하지 않은 민법 조항은 후혼배우자의 인격권과 행복추구권을 침해하지 않는다고 판단되었다.|중혼 취소청구권에 소멸사유가 없어 후혼배우자의 인격권과 행복추구권을 침해한다고 한 부분
15|②|02|X|중혼 취소청구권의 소멸에 관한 규정을 두지 않은 민법 조항은 평등원칙에 반한다고 볼 수 없다고 판단되었다.|중혼 취소청구권 소멸규정 부재가 평등원칙에 반한다고 한 부분
15|③|01|O|부부자산소득합산과세는 혼인한 부부를 사실혼 부부나 독신자에 비하여 차별하여 헌법 제36조 제1항에 위반된다고 판단되었다.|
15|④|01|O|호주제는 남계혈통 중심의 가 유지와 계승을 강요하여 혼인과 가족생활에 관한 헌법 제36조 제1항에 부합하지 않는다고 판단되었다.|
15|⑤|01|O|친생부인의 소 제척기간을 부가 그 사유를 안 날부터 2년 이내로 정한 민법 조항은 헌법에 위반되지 않는다고 판단되었다.|
16|①|01|O|교과서 검·인정 제도는 헌법상 금지되는 사전검열에 해당하지 않는다고 판단되었다.|
16|②|01|O|등급분류를 받지 않은 비디오물의 유통금지 중 등급보류 부분을 제외한 부분은 사전검열에 해당하지 않는다고 판단되었다.|
16|③|01|X|한국광고자율심의기구가 수행한 텔레비전 방송광고 사전심의는 헌법상 금지되는 사전검열에 해당한다고 판단되었다.|텔레비전 방송광고 사전심의가 검열에 해당하지 않는다고 본 부분
16|④|01|X|영상물등급위원회의 외국음반 국내제작 추천제도는 사전검열에 해당한다고 판단되었다.|외국음반 국내제작 추천제도가 검열에 해당하지 않는다고 본 부분
16|⑤|01|X|영상물등급위원회의 비디오물 등급분류 보류제도는 행정기관에 의한 사전검열에 해당한다고 판단되었다.|비디오물 등급분류 보류제도가 검열에 해당하지 않는다고 본 부분
17|①|01|O|헌법재판소 결정의 기속력이 국회와 결정이유에 미치는지 여부는 헌법재판권과 입법권의 범위와 한계를 고려하여 신중하게 판단하여야 한다.|
17|②|01|O|헌법재판소법 제68조 제2항 후문의 당해 사건 소송절차에는 상소심 절차가 포함된다.|
17|②|02|O|헌법재판소법 제68조 제2항 후문의 당해 사건 소송절차에는 대법원 파기환송 전후의 소송절차가 포함된다.|
17|③|01|O|헌법재판소의 위헌결정 전에는 일반적으로 법률의 위헌성이 객관적으로 명백하다고 할 수 없다.|
17|③|02|O|위헌결정 전 법률에 따라 행위한 공무원에게는 특별한 사정이 없는 한 고의 또는 과실이 인정되기 어렵다.|
17|④|01|O|지방자치단체장의 토론대회 공모가 민법상 우수현상광고 또는 이와 유사한 사법상 법률행위에 불과하면 헌법소원 대상인 공권력 행사로 볼 수 없다.|
17|⑤|01|X|법률과 같은 효력을 가지는 관습법은 헌법재판소법 제68조 제2항 헌법소원심판의 대상이 될 수 있다.|관습법은 형식적 의미의 법률과 같은 효력이 없어 위헌심판 대상이 될 수 없다고 한 부분
17|⑤|02|X|위헌심판의 대상인 법률에는 형식적 의미의 법률뿐 아니라 법률과 동일한 효력을 갖는 규범도 포함될 수 있다.|위헌심판 대상 법률을 형식적 의미의 법률로만 본 부분
18|①|01|O|일정한 성범죄를 저지른 사람에게 신상정보를 제출하게 하여 보존·관리하는 것은 정당한 목적을 위한 적합한 수단이 될 수 있다.|
18|①|02|O|카메라등이용촬영죄로 유죄판결이 확정된 사람을 신상정보 등록대상자로 정한 조항은 개인정보자기결정권을 침해하지 않는다고 판단되었다.|
18|②|01|X|모든 등록대상자에게 일률적으로 20년 동안 신상정보 등록의무를 부과한 관리조항은 개인정보자기결정권을 침해한다고 판단되었다.|모든 등록대상 성범죄자에게 20년 등록기간을 적용해도 개인정보자기결정권을 침해하지 않는다고 한 부분
18|③|01|O|주민등록번호 유출 또는 오·남용 피해 가능성을 고려하지 않고 주민등록번호 변경을 일체 허용하지 않는 것은 개인정보자기결정권을 과도하게 침해할 수 있다.|
18|④|01|O|인터넷게시판 본인확인제는 게시판 이용자의 표현의 자유와 개인정보자기결정권을 침해한다고 판단되었다.|
18|⑤|01|O|2015년 헌법재판소 결정은 선거운동기간 인터넷언론 게시판 실명확인제 조항이 정치적 익명표현의 자유 등을 침해하지 않는다고 보았다.|
19|①|01|O|정당해산심판제도는 정부의 일방적 행정처분에 의한 야당 등록취소에 대한 반성에서 도입된 제도이다.|
19|①|02|O|정당해산심판제도는 발생사적 측면에서 정당을 보호하기 위한 절차로서의 성격이 부각된다.|
19|②|01|O|정당이 민주적 기본질서를 부정하고 적극적으로 공격하는 것으로 보이더라도 정치적 의사형성에 참여하는 정당으로 존재하는 한 헌법상 두텁게 보호된다.|
19|③|01|O|강제적 정당해산은 정당활동 자유에 대한 근본적 제한이므로 비례원칙을 준수하여야 한다.|
19|③|02|O|정당해산결정은 대안적 수단이 없고 사회적 이익이 정당활동 자유 제한의 불이익을 초과할 정도로 큰 경우에 한하여 정당화될 수 있다.|
19|④|01|O|정당 보조금 배분에서 교섭단체 구성 여부에 따라 차등을 두는 것은 정당 간 경쟁상태를 현저하게 변경시킬 정도로 합리성을 결여한 차별이라고 보기 어렵다.|
19|⑤|01|X|국회의원선거에서 의석을 얻지 못하고 유효투표총수의 2퍼센트 이상을 득표하지 못한 정당의 등록을 취소하는 조항은 정당설립의 자유를 침해한다고 판단되었다.|소수 득표 정당 등록취소 조항이 정당설립의 자유를 침해하지 않는다고 한 부분
20|가|01|O|게임 결과물 환전업은 헌법 제15조가 보장하는 직업에 해당한다.|
20|나|01|O|일반학원 강사에게 대학 졸업 이상 학력 기준을 요구하는 것은 직업선택의 자유를 제한한다.|
20|나|02|O|일반학원 강사의 대학 졸업 이상 학력 기준에 대하여 일률적 자격기준 설정만큼 효과적인 다른 절차를 쉽게 찾기 어려우므로 최소침해원칙 위반이 문제되지 않는다고 판단되었다.|
20|다|01|O|전문분야 자격제도의 자격요건에 관한 법률조항은 합리적 근거 없이 현저히 자의적인 경우에만 헌법에 위반된다.|
20|라|01|X|운전전문학원 졸업생의 교통사고 비율을 이유로 학원 등록취소 또는 운영정지를 명할 수 있도록 한 조항은 직업의 자유를 침해한다고 판단되었다.|운전전문학원 교통사고 비율에 따른 제재가 직업의 자유를 침해하지 않는다고 한 부분
20|마|01|O|건설업자의 명의대여행위에 대하여 건설업 등록을 필요적으로 말소하도록 한 조항은 직업수행의 자유와 재산권을 침해하지 않는다고 판단되었다.|
20|마|02|O|법인 임원이 금고 이상의 형을 선고받은 경우 법인의 건설업 등록을 필요적으로 말소하도록 한 조항은 직업수행의 자유를 침해한다고 판단되었다.|
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
        raise ValueError("cannot locate 2016 constitution section")
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
    label_pattern = "|".join(re.escape(label) for label in labels)
    for marker in re.finditer(rf"({label_pattern})\.", block):
        label = marker.group(1)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(labels):
            break
    if set(first_by_label) != set(labels):
        raise ValueError(f"cannot split box statements: expected {labels}, got {sorted(first_by_label)}")
    last = labels[-1]
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label[last].end() :])
    choice_start = first_by_label[last].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in labels]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(1)] = normalize_raw(block[start:end])
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
        qid = f"2016-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2016-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2016-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v010_2016_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2016-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
