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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2020" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2020_법무사_헌법_헌법-1책형.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2020"
TEXT_DIR = PRIVATE_ROOT / "text" / "2020"
RAW_PDF_PATH = RAW_DIR / "2020_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2020_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2020_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2020_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2020_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2020_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2020_bupmusa_1st"
YEAR = 2020
ROUND = 26
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 120
LABELS = ["①", "②", "③", "④", "⑤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}

OFFICIAL_ANSWERS = {1: "⑤", 2: "②", 3: "④", 4: "①", 5: "⑤", 6: "⑤", 7: "⑤", 8: "①", 9: "③", 10: "②", 11: "⑤", 12: "②", 13: "①", 14: "⑤", 15: "②", 16: "⑤", 17: "②", 18: "④", 19: "④", 20: "⑤"}
QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
FALSE_LABELS = {no: {answer} for no, answer in OFFICIAL_ANSWERS.items()}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "2020 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2020"},
    {"title": "2020 법무사 헌법 해설", "publisher": "김건호 헌법", "url": "local:2020_법무사_헌법_해설_법무사_김건호.pdf"},
]

TOPICS = {
    1: "조례와 지방자치",
    2: "위헌법률심판",
    3: "언론·출판의 자유",
    4: "제대군인 가산점제도",
    5: "명확성원칙",
    6: "정당",
    7: "재판청구권",
    8: "공무담임권",
    9: "신체의 자유",
    10: "국회 정족수",
    11: "직업의 자유",
    12: "국회의 동의권",
    13: "선거관리",
    14: "부담금",
    15: "행정부",
    16: "사생활의 비밀과 자유",
    17: "평등권과 평등원칙",
    18: "국회 법제사법위원회",
    19: "법원",
    20: "헌법재판소",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    2: ("헌법+헌법재판소법", "헌법재판소법 제41조·제42조·제68조", "위헌법률심판 제청절차와 재판정지에 관한 조문 지점이다."),
    10: ("헌법+국회법", "헌법 제63조·제64조·제65조·제77조·제130조 및 국회법", "국회 의사절차별 정족수의 비교 지점이다."),
    12: ("헌법", "헌법 제60조·제79조·제98조·제104조", "국회 동의가 필요한 헌법상 권한에 관한 조문 지점이다."),
    13: ("헌법", "헌법 제114조·제115조·제116조", "선거관리위원회와 선거비용에 관한 조문 지점이다."),
    15: ("헌법+정부조직법", "헌법 제86조·제87조·제88조·제95조 및 정부조직법", "국무총리·국무위원·국무회의·총리령과 부령에 관한 조문 지점이다."),
    18: ("국회법", "국회법 제37조", "상임위원회 소관 사항에 관한 조문 지점이다."),
    20: ("헌법", "헌법 제111조·제112조·제113조", "헌법재판소 구성, 재판관 신분과 결정정족수에 관한 조문 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|지방자치단체는 자치사무와 단체위임사무에 관하여 자치조례를 제정할 수 있다.|
1|①|02|O|기관위임사무라도 개별 법령의 특별한 위임이 있으면 지방자치단체는 위임 범위 내에서 위임조례를 제정할 수 있다.|
1|②|01|O|자치사무나 단체위임사무에 관한 자치조례에는 지방자치법상 법령의 범위 안이라는 사항적 한계가 적용된다.|
1|②|02|O|자치조례에는 국가법에 적용되는 일반적 위임입법의 한계가 그대로 적용되지 않는다.|
1|③|01|O|지방자치법상 법령의 범위 안은 법령에 위반되지 않는 범위 안을 뜻한다.|
1|③|02|O|국가법령이 지방 실정에 맞는 별도 규율을 용인하면 조례가 국가법령에 없는 사항을 정하더라도 법령 위반이라고 할 수 없다.|
1|④|01|O|조례는 법률상 특별한 근거 없이 지방자치단체장 고유권한을 침해하는 규정을 둘 수 없다.|
1|④|02|O|특정 사항에 관하여 일정 기간 내 반드시 주민투표를 실시하도록 한 조례안은 지방자치단체장의 고유권한을 침해할 수 있다.|
1|⑤|01|X|집행행위 없이 직접 법률상 효과를 발생시키는 조례에 대한 무효확인소송의 피고는 조례 공포권이 있는 지방자치단체장이다.|조례 무효확인소송의 피고적격 행정청을 행정주체인 지방자치단체라고 한 부분
2|①|01|O|위헌법률심판의 재판 전제성에서 말하는 재판에는 판결·결정·명령 등 형식을 불문한 재판이 포함된다.|
2|①|02|O|위헌법률심판의 재판 전제성에서 말하는 재판에는 본안 재판과 소송절차 재판, 종국재판과 중간재판이 포함된다.|
2|②|01|X|대법원 외의 법원이 위헌법률심판을 제청할 때에는 대법원을 거쳐야 한다.|대법원 외의 법원이 대법원을 거칠 필요 없이 직접 위헌심판 제청을 할 수 있다고 한 부분
2|③|01|O|법률의 위헌 여부 심판 제청신청이 기각되면 신청 당사자는 헌법재판소법 제68조 제2항 헌법소원을 청구할 수 있다.|
2|④|01|O|법원이 위헌법률심판을 제청하면 당해 소송사건의 재판은 헌법재판소 결정까지 정지된다.|
2|④|02|O|법원이 긴급하다고 인정하면 위헌법률심판 제청 후에도 종국재판 외의 소송절차를 진행할 수 있다.|
2|⑤|01|O|군사법원도 재판의 전제가 된 법률에 대하여 위헌법률심판을 제청할 수 있다.|
3|①|01|O|광고물도 사상·지식·정보를 불특정 다수인에게 전파하는 것으로서 언론·출판의 자유 보호대상이 된다.|
3|②|01|O|헌법 제21조 제1항의 언론·출판의 자유에는 방송의 자유가 포함된다.|
3|③|01|O|사전검열금지원칙은 모든 사전규제를 금지하는 것이 아니라 행정권 허가에 의존하는 사전심사를 금지한다.|
3|③|02|O|헌법상 금지되는 검열은 표현물 제출의무, 행정권 사전심사, 무허가 표현 금지, 강제수단을 요건으로 한다.|
3|④|01|X|음란표현도 헌법 제21조의 언론·출판의 자유 보호영역에 포함될 수 있다.|음란표현이 언론·출판의 자유 보호영역에 아예 포함될 여지가 없다고 한 부분
3|⑤|01|O|언론·출판은 타인의 명예나 권리 또는 공중도덕이나 사회윤리를 침해하여서는 안 된다.|
3|⑤|02|O|언론·출판이 타인의 명예나 권리를 침해하면 피해자는 배상을 청구할 수 있다.|
4|①|01|X|제대군인 가산점제도는 제대군인의 사회복귀 지원이라는 정당한 입법목적을 가진다.|제대군인 가산점제도의 입법목적 정당성이 인정되지 않는다고 한 부분
4|②|01|O|제대군인 가산점제도는 공직수행능력과 합리적 관련 없는 기준으로 여성과 장애인의 사회진출 기회를 박탈하여 수단의 적합성과 합리성을 상실한 것으로 볼 수 있다.|
4|③|01|O|제대군인 가산점제도가 응시횟수나 합격 이력과 무관하게 계속 적용되면 비제대군인의 기회가 반복적으로 박탈될 수 있다.|
4|④|01|O|제대군인 가산점제도는 공직 진입 자체를 어렵게 하므로 공무담임권에 중대한 제약으로 작용할 수 있다.|
4|⑤|01|O|여성공무원 채용목표제의 존재만으로 제대군인 가산점제도의 위헌성이 제거된다고 볼 수는 없다.|
5|①|01|O|명확성원칙은 법치국가원리의 한 표현으로서 기본적으로 모든 기본권 제한입법에 요구된다.|
5|②|01|O|법규범의 의미내용이 불명확하면 법적 안정성과 예측가능성이 확보되지 않고 자의적 집행을 가능하게 할 수 있다.|
5|③|01|O|명확성원칙의 요구 정도는 법률이나 법조항의 성격, 구성요건의 특수성, 제정 배경과 상황에 따라 달라질 수 있다.|
5|④|01|O|부담적 규정은 수익적 규정보다 명확성원칙이 더 엄격하게 요구된다.|
5|④|02|O|형사 관련 법률에서는 죄형법정주의로 인하여 명확성 기준이 더 엄격하게 적용된다.|
5|⑤|01|X|명확성원칙은 입법자가 개괄조항이나 불확정 법개념을 사용하는 것 자체를 금지하지 않는다.|명확성원칙이 개괄조항이나 불확정 법개념 사용을 금지한다고 한 부분
6|①|01|O|정부는 정당의 목적이나 활동이 민주적 기본질서에 위배될 때 국무회의 심의를 거쳐 정당해산심판을 청구할 수 있다.|
6|②|01|O|헌법재판소는 정당해산심판에서 종국결정 선고 전까지 피청구인 정당의 활동정지 가처분을 할 수 있다.|
6|③|01|O|정당은 법률이 정하는 바에 따라 국가의 보호를 받는다.|
6|③|02|O|국가는 법률이 정하는 바에 따라 정당운영에 필요한 자금을 보조할 수 있다.|
6|④|01|O|정당해산을 명하는 헌법재판소 결정은 중앙선거관리위원회가 정당법에 따라 집행한다.|
6|⑤|01|X|헌법상 정당설립의 자유는 정당활동의 자유를 포함한다.|정당활동의 자유가 헌법상 기본권으로 보호되지 않는다고 한 부분
6|⑤|02|X|헌법상 정당설립의 자유는 정당의 존속과 자유로운 가입·탈퇴의 자유도 보장한다.|정당활동의 자유가 헌법상 기본권으로 보호되지 않는다고 한 부분
7|①|01|O|모든 국민은 헌법과 법률이 정한 법관에 의하여 법률에 의한 재판을 받을 권리를 가진다.|
7|②|01|O|공정한 재판을 받을 권리는 헌법 제27조의 재판청구권에 의하여 보장된다.|
7|③|01|O|군인·군무원이 아닌 국민은 헌법상 예외 사유가 없는 한 대한민국 영역 안에서 군사법원의 재판을 받지 않는다.|
7|④|01|O|형사피해자는 법률이 정하는 바에 따라 해당 사건 재판절차에서 진술할 수 있다.|
7|⑤|01|X|헌법은 모든 국민의 신속한 재판을 받을 권리를 명시한다.|헌법에 신속한 재판을 받을 권리가 명시되어 있지 않다고 한 부분
7|⑤|02|X|형사피고인은 상당한 이유가 없는 한 지체 없이 공개재판을 받을 권리를 가진다.|헌법에 신속한 재판을 받을 권리가 명시되어 있지 않다고 한 부분
8|①|01|X|공무담임권 보호영역에는 특별한 사정 없이 특정 장소 근무나 특정 보직 근무 같은 공무수행의 자유까지 포함된다고 보기 어렵다.|공무담임권 보호영역에 특정 장소·보직에서 근무할 공무수행의 자유까지 포함된다고 한 부분
8|②|01|O|공무담임권이 공무원의 퇴직급여와 공무상 재해보상을 보장할 것까지 보호영역으로 한다고 보기 어렵다.|
8|③|01|O|공무담임권은 국가나 공공단체의 구성원으로서 직무를 담당할 수 있는 권리를 말한다.|
8|③|02|O|공무담임권은 모든 국민이 현실적으로 공직을 담당할 수 있음을 뜻하지 않고 자의적이지 않은 평등한 기회를 보장한다.|
8|④|01|O|공무담임권 보호영역에는 공직취임 기회의 자의적 배제와 공무원 신분의 부당한 박탈이 포함된다.|
8|⑤|01|O|모든 국민은 법률이 정하는 바에 따라 공무담임권을 가진다.|
9|①|01|O|미결구금일수 일부 산입을 법관 재량에 맡긴 형법 조항은 무죄추정원칙과 적법절차원칙에 위배되어 신체의 자유를 침해한다.|
9|②|01|O|동일 범죄사실로 외국에서 형을 집행받았는데도 국내 처벌에서 이를 전혀 반영하지 않을 수 있게 한 형법 조항은 신체의 자유를 침해한다.|
9|③|01|X|특정범죄 확정자로부터 디엔에이감식시료를 채취할 수 있도록 한 조항은 과잉금지원칙에 반하여 신체의 자유를 침해한다고 볼 수 없다.|디엔에이감식시료 채취조항이 신체의 자유를 침해한다고 한 부분
9|④|01|O|형사재판 계속 중인 사람에 대한 법무부장관의 출국금지는 직접 물리적 강제력을 수반하는 강제처분이 아니므로 영장주의에 위배되지 않는다.|
9|⑤|01|O|지방의회의 사무감사·조사를 위한 증인 동행명령장제도는 체포 또는 구속에 준하므로 법관 발부 영장이 필요하다.|
10|①|01|O|국무총리 해임건의 발의와 일반 탄핵소추 발의에는 모두 국회재적의원 3분의 1 이상이 필요하다.|
10|②|01|X|국회의원 자격심사 청구에는 의원 30명 이상의 연서가 필요하다.|국회의원 자격심사 청구정족수와 예산안 수정동의 정족수가 같다고 한 부분
10|②|02|X|예산안 수정동의에는 의원 50명 이상의 찬성이 필요하다.|국회의원 자격심사 청구정족수와 예산안 수정동의 정족수가 같다고 한 부분
10|③|01|O|국회 위원회와 본회의의 의사정족수는 모두 재적 5분의 1 이상 출석이다.|
10|④|01|O|국회의원 제명과 헌법개정안 의결에는 모두 국회재적의원 3분의 2 이상 찬성이 필요하다.|
10|⑤|01|O|국회의장 선출과 계엄해제 요구에는 모두 재적의원 과반수 득표 또는 찬성이 필요하다.|
11|①|01|O|직업의 자유는 개인의 주관적 공권이면서 사회적 시장경제질서의 객관적 법질서 구성요소이다.|
11|②|01|O|직업의 자유 제한은 직업수행의 자유와 직업선택의 자유 중 어느 쪽에 작용하는지에 따라 정당화 수준이 달라진다.|
11|③|01|O|직업수행 규율에서 직업선택 규율로 갈수록 자유제약 정도가 강해지고 입법재량의 폭이 좁아진다.|
11|③|02|O|직업선택을 객관적 허가조건에 걸리게 하는 제한은 주관적 사유 제한보다 침해가 심각하여 더 엄밀한 정당화가 요구된다.|
11|④|01|O|직업분야 자격제도의 자격요건 설정에는 국가의 폭넓은 입법재량이 인정된다.|
11|⑤|01|X|헌법상 직업의 자유, 근로의 권리, 사회국가원리만으로 근로자의 직접적인 직장존속보장청구권이 인정되지는 않는다.|근로자에게 국가에 대한 직접적인 직장존속보장청구권이 인정된다고 한 부분
12|①|01|O|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|
12|②|01|X|감사원장은 국회의 동의를 얻어 대통령이 임명한다.|대통령이 감사원장을 임명할 때 국회 동의가 필요 없다고 한 부분
12|③|01|O|국회는 상호원조·안전보장 조약 등 헌법상 중요 조약의 체결·비준에 대한 동의권을 가진다.|
12|④|01|O|대법관은 대법원장의 제청으로 국회의 동의를 얻어 대통령이 임명한다.|
12|⑤|01|O|국회는 선전포고, 국군의 외국 파견, 외국군대의 대한민국 영역 안 주류에 대한 동의권을 가진다.|
13|①|01|X|중앙선거관리위원회 위원의 임기는 6년이다.|중앙선거관리위원회 위원의 임기가 5년이라고 한 부분
13|②|01|O|중앙선거관리위원회는 법령의 범위 안에서 선거관리·국민투표관리 또는 정당사무에 관한 규칙을 제정할 수 있다.|
13|②|02|O|중앙선거관리위원회는 법률에 저촉되지 않는 범위 안에서 내부규율에 관한 규칙을 제정할 수 있다.|
13|③|01|O|중앙선거관리위원회 위원은 탄핵 또는 금고 이상의 형 선고에 의하지 않고는 파면되지 않는다.|
13|④|01|O|각급 선거관리위원회는 선거사무와 국민투표사무에 관하여 관계 행정기관에 필요한 지시를 할 수 있다.|
13|⑤|01|O|선거에 관한 경비는 법률이 정하는 경우를 제외하고 정당 또는 후보자에게 부담시킬 수 없다.|
14|①|01|O|공과금이 조세인지 부담금인지는 법률상 명칭이 아니라 실질적 내용을 기준으로 판단한다.|
14|②|01|O|부담금은 재정조달목적 부담금과 정책실현목적 부담금으로 구분될 수 있다.|
14|②|02|O|재정조달목적 부담금은 공적 과제가 부담금 수입의 지출 단계에서 실현된다.|
14|②|03|O|정책실현목적 부담금은 공적 과제의 전부 또는 일부가 부담금 부과 단계에서 이미 실현된다.|
14|③|01|O|재정조달목적 부담금은 조세와 유사하므로 조세법률주의, 공과금 부담 형평성, 국회의 재정감독권과의 관계상 한계를 가진다.|
14|③|02|O|재정조달목적 부담금이 정당화되려면 납부의무자가 공적 과제에 대하여 일반국민보다 특별히 밀접한 관련성을 가져야 한다.|
14|④|01|O|부담금은 국민 재산권을 제한하므로 평등원칙과 비례성원칙 같은 기본권 제한입법의 한계를 준수하여야 한다.|
14|⑤|01|X|부담금 부과에 관한 명확한 개별 법률 규정이 있으면 부담금관리 기본법 별표에 포함되지 않았다는 이유만으로 부과가 당연히 허용되지 않는 것은 아니다.|개별 법률 근거가 있어도 부담금관리 기본법 별표에 없으면 부담금 부과가 허용될 수 없다고 한 부분
15|①|01|O|군인은 현역을 면한 후가 아니면 국무총리로 임명될 수 없다.|
15|①|02|O|군인은 현역을 면한 후가 아니면 국무위원으로 임명될 수 없다.|
15|②|01|X|국무위원은 국무총리의 제청으로 대통령이 임명한다.|국무위원 임명에는 국무총리 제청이 필수적이지 않다고 한 부분
15|②|02|X|행정각부의 장은 국무위원 중에서 국무총리의 제청으로 대통령이 임명한다.|국무위원 임명에는 국무총리 제청이 필수적이지 않다고 한 부분
15|③|01|O|국무회의는 대통령·국무총리와 15인 이상 30인 이하의 국무위원으로 구성한다.|
15|④|01|O|대통령은 국무회의 의장으로서 회의를 소집하고 주재한다.|
15|⑤|01|O|국무총리 또는 행정각부의 장은 소관사무에 관하여 법률이나 대통령령의 위임 또는 직권으로 총리령 또는 부령을 발할 수 있다.|
16|①|01|O|사생활의 비밀은 국가가 사생활영역을 들여다보는 것에 대한 보호를 제공하는 기본권이다.|
16|②|01|O|사생활의 자유는 사생활을 자유롭게 형성하고 그 설계와 내용에 외부 간섭을 받지 않을 권리이다.|
16|③|01|O|흡연권은 헌법 제10조의 인간의 존엄과 행복추구권에 의하여 뒷받침된다.|
16|③|02|O|흡연권은 헌법 제17조의 사생활의 자유에 의하여 뒷받침된다.|
16|④|01|O|도로 운전 중 좌석안전띠 착용 여부는 사생활의 비밀과 자유에 의하여 보호되는 범주를 벗어난 행위이다.|
16|⑤|01|X|교도소장이 수용자 부재 중 실시한 거실 및 작업장 검사행위는 사생활의 비밀과 자유를 침해하지 않는다고 볼 수 있다.|교도소 수용자의 거실 및 작업장 검사행위가 사생활의 비밀과 자유를 침해한다고 한 부분
17|①|01|O|평등원칙은 국가가 입법, 법 해석과 집행에서 따라야 할 기준이다.|
17|①|02|O|평등원칙은 합리적 이유 없는 불평등 대우를 받지 않고 평등한 대우를 요구할 수 있는 국민의 권리이다.|
17|②|01|X|헌법 제11조 제1항 후문의 차별금지 사유는 불합리한 차별금지에 초점이 있을 뿐 절대적 차별금지를 요구하는 것은 아니다.|사회적 신분 등 예시 사유가 있으면 절대적으로 차별이 금지된다고 한 부분
17|③|01|O|평등원칙은 합리적 근거 없는 차별을 금지하는 상대적 평등을 뜻한다.|
17|③|02|O|합리적 근거 있는 차별이나 불평등은 평등원칙에 반하지 않는다.|
17|④|01|O|평등심사에서 엄격심사와 완화심사의 선택은 입법자에게 인정되는 입법형성권의 정도에 따라 달라진다.|
17|⑤|01|O|개별사건법률이라도 차별적 규율이 합리적 이유로 정당화되면 합헌일 수 있다.|
18|①|01|O|법제처 소관 사항은 국회 법제사법위원회 소관 사항이다.|
18|②|01|O|감사원 소관 사항은 국회 법제사법위원회 소관 사항이다.|
18|③|01|O|헌법재판소 사무에 관한 사항은 국회 법제사법위원회 소관 사항이다.|
18|④|01|X|국가인권위원회 소관 사항은 국회운영위원회 소관 사항이다.|국가인권위원회 소관 사항이 법제사법위원회 소관이라고 한 부분
18|⑤|01|O|탄핵소추에 관한 사항은 국회 법제사법위원회 소관 사항이다.|
19|①|01|O|명령·규칙 또는 처분의 위헌·위법 여부가 재판의 전제가 되면 대법원이 이를 최종적으로 심사할 권한을 가진다.|
19|②|01|O|헌법이 대법원을 최고법원으로 규정했다는 이유만으로 대법원이 모든 사건을 상고심으로 관할하여야 하는 것은 아니다.|
19|③|01|O|대법원장은 대법원의 일반사무를 관장한다.|
19|③|02|O|대법원장은 대법원 직원과 각급 법원 및 소속 기관의 사법행정사무에 관하여 직원을 지휘·감독한다.|
19|④|01|X|대법원장의 임기는 6년이며 중임할 수 없다.|대법원장이 중임할 수 있다고 한 부분
19|⑤|01|O|법관의 정년은 법률로 정한다.|
20|①|01|O|헌법재판소는 법관의 자격을 가진 9인의 재판관으로 구성한다.|
20|①|02|O|헌법재판소 재판관은 대통령이 임명한다.|
20|②|01|O|헌법재판소 재판관의 임기는 6년이며 법률이 정하는 바에 따라 연임할 수 있다.|
20|③|01|O|헌법재판소 재판관은 정당에 가입하거나 정치에 관여할 수 없다.|
20|④|01|O|헌법재판소 재판관은 탄핵 또는 금고 이상의 형 선고에 의하지 않고는 파면되지 않는다.|
20|⑤|01|X|헌법재판소의 법률 위헌결정, 탄핵결정, 정당해산결정, 헌법소원 인용결정에는 재판관 6인 이상의 찬성이 필요하다.|헌법재판소의 중요 인용결정에 재판관 5인 이상의 찬성이 필요하다고 한 부분
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
        raise ValueError("cannot locate 2020 constitution section")
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
        if set(first_by_label) == set(LABELS):
            break
    if set(first_by_label) != set(LABELS):
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in LABELS]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = block[start:end]
        statement = re.split(r"\s*1교시\s*①책형\s*전체|\s*【\s*제1과목", statement)[0]
        out[label := marker.group(0)] = normalize_raw(statement)
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        split = split_choice_units(blocks[no])
        for label in LABELS:
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
        qid = f"2020-g1-constitution-{no:02d}"
        units = [{"unitId": f"{qid}-{LABEL_CODE[label]}", "unitType": "choice", "label": label, "rawStatement": raws[(no, label)], "originalVerdict": source_verdict(no, label)} for label in LABELS]
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
            items.append({"atomId": f"bupmusa-2020-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2020-constitution-")]
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
    input_atoms = sum(len(load_json(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").get("items", [])) for year in years if (SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json").exists())
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v006_2020_integrated", "builtAt": today(), "sourceFiles": {str(year): str(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2020-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
