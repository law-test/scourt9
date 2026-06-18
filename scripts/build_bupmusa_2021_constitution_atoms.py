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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2021" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2021_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2021"
TEXT_DIR = PRIVATE_ROOT / "text" / "2021"
RAW_PDF_PATH = RAW_DIR / "2021_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2021_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2021_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2021_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2021_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2021_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2021_bupmusa_1st"
YEAR = 2021
ROUND = 27
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 115
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS = ["㉠", "㉡", "㉢", "㉣", "㉤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05", "㉠": "01", "㉡": "02", "㉢": "03", "㉣": "04", "㉤": "05"}

OFFICIAL_ANSWERS = {1: "⑤", 2: "⑤", 3: "④", 4: "⑤", 5: "⑤", 6: "③", 7: "③", 8: "①", 9: "④", 10: "③", 11: "⑤", 12: "④", 13: "③", 14: "②", 15: "①", 16: "⑤", 17: "②", 18: "④", 19: "①", 20: "③"}
QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES[15] = "count-true"
QUESTION_TYPES[18] = "single-best-true"
FALSE_LABELS = {
    1: {"⑤"},
    2: {"⑤"},
    3: {"④"},
    4: {"⑤"},
    5: {"⑤"},
    6: {"③"},
    7: {"③"},
    8: {"①"},
    9: {"④"},
    10: {"③"},
    11: {"⑤"},
    12: {"④"},
    13: {"③"},
    14: {"②"},
    15: {"㉡", "㉢", "㉣", "㉤"},
    16: {"⑤"},
    17: {"②"},
    18: {"①", "②", "③", "⑤"},
    19: {"①"},
    20: {"③"},
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "2021 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2021"},
    {"title": "2021 법무사 헌법 해설", "publisher": "김건호 헌법", "url": "local:2021_법무사_헌법_해설_법무사_김건호.pdf"},
]

TOPICS = {
    1: "재산권",
    2: "정당제도",
    3: "개인정보자기결정권",
    4: "헌법의 기본원리",
    5: "양심적 병역거부",
    6: "국회",
    7: "정당해산심판제도",
    8: "기본권",
    9: "직업의 자유",
    10: "법원",
    11: "헌법재판소 결정례 종합",
    12: "선거운동",
    13: "헌법소원의 대상",
    14: "선거관리",
    15: "양심의 자유",
    16: "헌법재판소와 위헌법률심사",
    17: "근로의 권리",
    18: "법률유보원칙",
    19: "지방자치단체",
    20: "대통령의 권한",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    6: ("헌법", "헌법 제47조·제50조·제51조·제53조", "국회 회기, 회의 공개, 회기계속, 법률안 재의에 관한 조문 지점이다."),
    10: ("헌법+헌법재판소 결정례", "헌법 제104조·제105조·제106조·제110조 및 법관징계 관련 결정례", "법원 조직과 법관 신분보장 및 재판청구권에 관한 지점이다."),
    14: ("헌법", "헌법 제114조·제115조·제116조", "선거관리위원회 구성과 선거관리 비용에 관한 조문 지점이다."),
    20: ("헌법", "헌법 제74조·제77조·제79조·제80조·제81조", "대통령의 헌법상 권한에 관한 조문 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|시혜적 입법의 시혜대상에서 제외되었다는 이유만으로 재산권 침해가 발생하는 것은 아니다.|
1|①|02|O|시혜대상에 포함될 경우 얻을 수 있었던 단순한 재산상 이익의 기대는 헌법상 재산권의 영역에 포함되지 않는다.|
1|②|01|O|연금수급권의 내용은 사회·경제적 상황을 고려한 입법자의 정책적 판단에 따라 변경될 수 있다.|
1|②|02|O|조기노령연금 수급개시연령을 59세에서 60세로 인상하는 법률은 재산권을 침해하지 않는다고 볼 수 있다.|
1|③|01|O|유류분반환청구권에 1년의 단기소멸시효를 둔 민법 조항은 유류분 권리자의 재산권을 침해하지 않는다.|
1|④|01|O|재산권 침해가 기존 법질서 안에서 개인 재산권에 대한 개별적 침해인 경우 정당한 보상은 원칙적으로 완전보상을 뜻한다.|
1|④|02|O|완전보상은 피수용재산의 객관적 재산가치를 완전하게 보상하는 것을 뜻한다.|
1|⑤|01|X|공익사업 시행으로 지가가 상승하여 발생한 개발이익은 피수용토지가 수용 당시 가지는 객관적 가치에 포함되지 않는다.|개발이익이 피수용토지의 객관적 가치에 포함된다고 한 부분
1|⑤|02|X|손실보상액 산정에서 개발이익을 배제하여도 헌법상 정당보상 원리에 위배되지 않는다.|개발이익을 손실보상액에서 배제하는 것이 정당보상 원리에 위배된다고 한 부분
2|①|01|O|헌법은 정당을 일반 결사의 자유와 분리하여 헌법 제8조에서 독자적으로 규율한다.|
2|①|02|O|헌법 제8조는 헌법질서에서 정당의 특별한 지위를 강조한다.|
2|②|01|O|헌법상 정당설립의 자유는 자유롭게 정당에 가입할 자유를 포함한다.|
2|②|02|O|헌법상 정당설립의 자유는 자유롭게 정당에서 탈퇴할 자유를 포함한다.|
2|③|01|O|정당의 설립과 활동의 자유 보장은 선거제도 민주화와 국민주권의 실질적 현실화에 목적이 있다.|
2|③|02|O|정당의 설립과 활동의 자유 보장은 무소속 후보자의 진출을 봉쇄하는 정당의 특권 설정을 의미하지 않는다.|
2|④|01|O|정당은 행정부의 통상적인 처분만으로 해산될 수 없다.|
2|④|02|O|정당은 헌법재판소가 위헌성과 해산 필요성을 인정한 경우에만 정당정치 영역에서 배제될 수 있다.|
2|⑤|01|X|정당해산심판절차에 민사소송 법령을 준용하도록 한 헌법재판소법 조항은 공정한 재판을 받을 권리를 침해하지 않는다.|민사소송 법령 준용조항이 재판을 받을 권리를 침해한다고 한 부분
3|①|01|O|개인정보자기결정권은 자신에 관한 정보의 공개와 이용 범위를 정보주체가 스스로 결정할 권리이다.|
3|①|02|O|개인정보자기결정권은 일반적 인격권과 사생활의 비밀과 자유에 의하여 보장된다.|
3|②|01|O|개인정보의 조사·수집·보관·처리·이용은 원칙적으로 개인정보자기결정권 제한에 해당한다.|
3|③|01|O|직계혈족이라는 이유만으로 제한 없이 자녀의 가족관계증명서와 기본증명서를 발급받게 하는 조항은 개인정보자기결정권을 침해할 수 있다.|
3|④|01|X|정보주체가 이미 공개한 개인정보는 공개 당시 정보주체가 일정 범위에서 처리에 동의한 것으로 볼 수 있다.|이미 공개된 개인정보라도 별도의 동의가 항상 필요하다고 한 부분
3|④|02|X|이미 공개된 개인정보를 정보주체의 동의가 객관적으로 인정되는 범위에서 처리할 때에는 별도의 동의가 필요하지 않다.|이미 공개된 개인정보 처리에도 별도의 동의가 필요하다고 한 부분
3|⑤|01|O|공개된 법학과 교수의 직업·학력·경력 등 개인정보를 법률정보 제공 사이트에서 유료 제공한 행위는 개인정보자기결정권 침해로 평가되지 않을 수 있다.|
4|①|01|O|자유민주적 기본질서는 폭력적 지배와 자의적 지배를 배제하는 법치주의적 통치질서를 말한다.|
4|①|02|O|자유민주적 기본질서는 기본적 인권 존중, 권력분립, 의회제도, 복수정당제, 선거제도, 시장경제질서와 사법권 독립을 포함한다.|
4|②|01|O|우리 헌법상 경제질서는 자유시장경제질서를 기본으로 한다.|
4|②|02|O|우리 헌법상 경제질서는 사회복지와 사회정의 실현을 위한 국가적 규제와 조정을 용인하는 사회적 시장경제질서의 성격을 가진다.|
4|③|01|O|우리 헌법은 사회국가원리를 명문으로 규정하지는 않지만 여러 구체화된 표현을 통하여 사회국가원리를 수용한다.|
4|④|01|O|사회국가는 정의로운 사회질서 형성을 위하여 경제·사회·문화 영역에서 관여·간섭·분배·조정하는 국가이다.|
4|⑤|01|X|헌법 제8조는 복수정당제를 제도적으로 보장한다.|복수정당제가 헌법상 반드시 보장되지 않는다고 한 부분
5|①|01|O|국방의 의무의 구체적인 이행방법과 내용은 법률로 정할 사항이다.|
5|②|01|O|양심적 병역거부 허용 여부는 양심의 자유 등 기본권 규범과 국방의 의무 규범 사이의 충돌·조정 문제이다.|
5|③|01|O|양심적 병역거부는 소극적 부작위에 의한 양심실현에 해당한다.|
5|③|02|O|소극적 부작위에 의한 양심실현 제한은 양심의 자유에 대한 과도한 제한이나 본질적 내용 위협이 될 수 있다.|
5|④|01|O|진정한 양심에 따른 병역거부는 병역법상 정당한 사유에 해당할 수 있다.|
5|④|02|O|양심적 병역거부자에게 병역의무 이행을 일률적으로 강제하고 불이행을 처벌하는 것은 소수자에 대한 관용과 포용의 정신에 반할 수 있다.|
5|⑤|01|X|양심적 병역거부에서 신념의 진실성은 상황에 따라 타협적이거나 전략적이지 않음을 뜻한다.|상황에 따라 타협적이거나 전략적으로 행동해도 신념의 진실성을 부정할 수 없다고 한 부분
5|⑤|02|X|병역거부자가 신념과 관련한 문제에서 상황에 따라 다른 행동을 하면 그 신념은 진실하다고 보기 어렵다.|신념 관련 문제에서 상황에 따라 다른 행동을 해도 신념이 진실하지 않다고 단정할 수 없다고 한 부분
6|①|01|O|국회의 정기회는 법률이 정하는 바에 따라 매년 1회 집회된다.|
6|①|02|O|국회의 임시회는 대통령 또는 국회재적의원 4분의 1 이상의 요구로 집회된다.|
6|②|01|O|국회의 회의는 원칙적으로 공개된다.|
6|②|02|O|국회의 회의는 출석의원 과반수 찬성이나 국가안전보장상 필요가 있으면 공개하지 않을 수 있다.|
6|③|01|X|우리 헌법은 회기 중 의결되지 못한 의안도 다음 회기에 계속 심의할 수 있는 회기계속의 원칙을 채택한다.|국회 제출 의안이 회기 중 의결되지 못하면 폐기된다고 한 부분
6|③|02|X|국회에 제출된 법률안 기타 의안은 회기 중 의결되지 못한 이유만으로 폐기되지 않는다.|국회 제출 의안이 회기 중 의결되지 못하면 폐기된다고 한 부분
6|④|01|O|대통령은 국회에서 의결된 법률안에 이의가 있으면 이송 후 15일 이내에 이의서를 붙여 국회로 환부하고 재의를 요구할 수 있다.|
6|⑤|01|O|대통령의 재의요구가 있으면 국회는 재적의원 과반수 출석과 출석의원 3분의 2 이상 찬성으로 법률안을 확정할 수 있다.|
7|①|01|O|정당해산심판제도는 방어적 민주주의 관점에 기초한다.|
7|②|01|O|정당의 목적이나 활동이 민주적 기본질서에 위배될 때 정부는 헌법재판소에 정당해산심판을 제소할 수 있다.|
7|③|01|X|정당 목적과 활동의 사소한 위헌성까지 문제 삼아 정당을 해산하는 것은 적절하지 않다.|정당의 목적이나 활동이 사소하게 헌법에 위반되어도 해산하는 것이 헌법정신에 부합한다고 한 부분
7|④|01|O|정당 소속원의 행위라도 개인적 차원의 행위에 불과하면 정당해산심판의 대상이 되는 정당 활동으로 보기 어렵다.|
7|⑤|01|O|정당해산심판제도는 정치적 비판자 탄압 수단으로 남용되지 않도록 엄격하고 제한적으로 운용되어야 한다.|
8|①|01|X|주민등록번호 변경에 관한 규정을 두지 않은 조항은 개인정보자기결정권을 침해한다.|주민등록번호 변경을 허용하지 않아도 개인정보자기결정권 침해가 아니라고 한 부분
8|②|01|O|인터넷언론사 공개 게시판에서 정당·후보자 지지·반대 글을 게시하는 행위는 양심의 자유나 사생활 비밀의 자유 보호영역이라고 할 수 없다.|
8|③|01|O|방송의 자유는 주관적 권리로서의 성격을 가진다.|
8|③|02|O|방송의 자유는 자유로운 의견형성과 여론형성을 위한 제도적 보장의 성격도 가진다.|
8|④|01|O|군종장교가 성직자의 신분에서 주재하는 종교활동에서 소속 종단의 종교를 선전하거나 다른 종교를 비판했다는 사정만으로 종교적 중립의무 위반이 되지는 않는다.|
8|⑤|01|O|헌법상 재산권은 민법상 소유권뿐 아니라 재산적 가치 있는 사법상 물권과 채권을 포함한다.|
8|⑤|02|O|헌법상 재산권은 자기 노력의 대가나 자본 투자 등 특별한 희생을 통하여 얻은 공법상 권리도 포함할 수 있다.|
9|①|01|O|직업의 자유에서 말하는 직업은 생활의 기본적 수요를 충족하기 위한 계속적 소득활동을 의미한다.|
9|①|02|O|대학생이 방학기간에 학비 등을 벌기 위해 학원강사로 일하는 행위도 직업의 자유 보호영역에 속할 수 있다.|
9|②|01|O|성인대상 성범죄 확정자에게 형 집행 종료일부터 10년 동안 의료기관 개설·취업을 금지한 조항은 직업선택의 자유를 침해한다.|
9|③|01|O|직업수행의 자유 제한은 직업선택의 자유 제한보다 인격발현 침해 효과가 작아 더 폭넓게 허용될 수 있다.|
9|④|01|X|직업의 자유에는 해당 직업에 합당한 보수를 받을 권리까지 포함된다고 보기 어렵다.|직업의 자유에 해당 직업에 합당한 보수를 받을 권리가 포함된다고 한 부분
9|⑤|01|O|자격제도의 자격요건 판단은 원칙적으로 입법자의 입법형성권 영역에 속한다.|
9|⑤|02|O|자격요건은 입법재량 범위를 일탈하여 현저히 불합리한 경우에 한하여 위헌으로 판단될 수 있다.|
10|①|01|O|대법관의 임기는 6년이며 법률이 정하는 바에 따라 연임할 수 있다.|
10|②|01|O|법관은 탄핵 또는 금고 이상의 형 선고에 의하지 않고는 파면되지 않는다.|
10|②|02|O|법관은 징계처분에 의하지 않고는 정직·감봉 기타 불리한 처분을 받지 않는다.|
10|③|01|X|법관 징계처분 취소청구소송을 대법원 단심재판으로 정한 조항은 재판청구권을 침해하지 않는다.|법관 징계처분 취소청구소송의 대법원 단심재판이 재판청구권을 침해한다고 한 부분
10|④|01|O|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|
10|⑤|01|O|군사법원의 상고심은 대법원이 관할한다.|
11|①|01|O|공익사업 토지수용 후 환매권 발생기간을 취득일부터 10년 이내로 제한한 조항은 재산권을 침해한다.|
11|②|01|O|법인의 종업원 위반행위만으로 법인에 형벌을 부과하는 양벌규정은 책임주의원칙에 위배된다.|
11|②|02|O|법인 대표자의 법규위반행위에 대한 법인의 책임은 법인 자신의 행위에 대한 직접책임으로 볼 수 있다.|
11|②|03|O|법인 대표자 관련 양벌규정 부분은 책임주의원칙에 위배되지 않는다.|
11|③|01|O|건강보험수급권은 보험료에 대한 반대급부 성격과 경제적 유용성이 있어 헌법상 재산권 보호범위에 속할 수 있다.|
11|④|01|O|초·중등학교 교원에게 정당가입의 자유를 금지하면서 대학 교원에게 허용하는 것은 합리적 차별로서 평등원칙에 위배되지 않는다.|
11|⑤|01|X|국가공무원법상 공무 외의 일을 위한 집단행위 금지 부분은 명확성원칙에 위반되지 않는다.|공무 외의 일을 위한 집단행위 금지가 명확성원칙에 위반된다고 한 부분
11|⑤|02|X|국가공무원법상 공무 외의 일을 위한 집단행위 금지 부분은 표현의 자유를 과도하게 제한한다고 볼 수 없다.|공무 외의 일을 위한 집단행위 금지가 표현의 자유를 과도하게 제한한다고 한 부분
12|①|01|O|자유선거의 원칙은 헌법에 명시되어 있지 않지만 민주국가 선거제도에 내재하는 법원리이다.|
12|①|02|O|자유선거의 원칙은 구체적으로 선거운동의 자유를 포함한다.|
12|②|01|O|예비후보자가 법정 방법에 따라 선거운동을 하는 경우에는 선거운동기간 이전에도 선거운동을 할 수 있다.|
12|③|01|O|예비후보자의 선거운동 가능 기간을 어느 정도로 제한할지는 원칙적으로 입법정책에 맡겨질 수 있다.|
12|③|02|O|예비후보자 선거운동기간 제한이 선거운동의 자유를 형해화할 정도가 아니면 기본권 침해로 보기 어렵다.|
12|④|01|X|선거운동기간 전에도 문자메시지를 전송하는 방법으로 선거운동을 할 수 있다.|선거운동기간 전 문자메시지 선거운동이 허용되지 않는다고 한 부분
12|④|02|X|선거운동기간 전에도 인터넷 홈페이지·게시판·대화방 글·동영상 게시나 전자우편 전송 방법으로 선거운동을 할 수 있다.|선거운동기간 전 인터넷·전자우편 선거운동이 허용되지 않는다고 한 부분
12|⑤|01|O|자치구·시의 장 선거보다 군의 장 선거의 예비후보자 선거운동기간을 짧게 정한 것은 평등원칙에 위배되지 않는다고 볼 수 있다.|
13|①|01|O|행정청이 우월적 지위에서 일방적으로 강제하는 권력적 사실행위는 헌법소원의 대상이 될 수 있다.|
13|②|01|O|대통령의 법률안 제출행위는 국가기관 사이의 내부적 행위에 불과하다.|
13|②|02|O|대통령의 법률안 제출행위는 헌법소원의 대상이 되는 공권력 행사에 해당하지 않는다.|
13|③|01|X|명령·규칙이 구체적 집행절차 없이 직접 현재 기본권을 침해하면 헌법소원의 대상이 될 수 있다.|명령·규칙은 대법원의 최종심사권 때문에 헌법소원의 대상이 될 수 없다고 한 부분
13|④|01|O|예산은 국가기관만을 구속하고 일반국민을 구속하지 않는다.|
13|④|02|O|국회의 예산안 의결행위는 헌법소원의 대상이 되지 않는다.|
13|⑤|01|O|헌법해석상 특정인의 기본권 보호를 위한 국가의 입법의무가 명백한데 입법자가 아무 입법조치를 하지 않으면 그 입법부작위는 헌법소원의 대상이 될 수 있다.|
14|①|01|O|선거와 국민투표의 공정한 관리 및 정당에 관한 사무 처리를 위하여 선거관리위원회를 둔다.|
14|②|01|X|중앙선거관리위원회는 대통령 임명 3인, 국회 선출 3인, 대법원장 지명 3인의 위원으로 구성한다.|중앙선거관리위원회 9인 전원을 대통령이 임명한다고 한 부분
14|②|02|X|중앙선거관리위원회 위원장은 위원 중에서 호선한다.|중앙선거관리위원회 9인 전원을 대통령이 임명한다고 한 부분
14|③|01|O|중앙선거관리위원회 위원의 임기는 6년이다.|
14|④|01|O|각급 선거관리위원회는 선거사무와 국민투표사무에 관하여 관계 행정기관에 필요한 지시를 할 수 있다.|
14|⑤|01|O|선거에 관한 경비는 법률이 정하는 경우를 제외하고 정당 또는 후보자에게 부담시킬 수 없다.|
15|㉠|01|O|헌법상 양심은 인격적 존재가치가 파멸될 정도의 강력하고 진지한 마음의 소리로서 절박하고 구체적인 것이어야 한다.|
15|㉡|01|X|양심의 자유는 양심형성의 자유와 양심적 결정의 자유뿐 아니라 양심실현의 자유를 포함한다.|양심의 자유에 양심실현의 자유가 포함되지 않는다고 한 부분
15|㉢|01|X|근로자에게 잘못을 반성하고 사죄한다는 내용의 시말서 제출을 명령하는 것은 양심의 자유를 침해할 수 있다.|반성·사죄 내용의 시말서 제출명령이 양심의 자유 침해가 아니라고 한 부분
15|㉣|01|X|양심적 병역거부가 병역법상 정당한 사유로 인정되려면 그 양심은 깊고 확고하며 진실하여야 한다.|양심적 병역거부의 처벌 여부가 신념의 확고성과 진실성과 무관하다고 한 부분
15|㉣|02|X|양심적 병역거부 사건에서 양심의 확고성과 진실성은 관련 간접사실이나 정황사실로 판단하여야 한다.|양심적 병역거부의 처벌 여부가 신념의 확고성과 진실성과 무관하다고 한 부분
15|㉤|01|X|국법질서나 헌법체제 준수 취지의 준법서약 요구는 단순한 헌법적 의무의 확인·서약으로서 양심의 영역을 건드리는 것이 아니다.|준법서약서 제출 요구가 양심의 자유와 행복추구권을 침해한다고 한 부분
16|①|01|O|헌법재판소는 법관의 자격을 가진 9인의 재판관으로 구성한다.|
16|①|02|O|헌법재판소 재판관은 대통령이 임명한다.|
16|②|01|O|위헌법률심판의 대상인 법률에는 국회의 의결을 거친 형식적 의미의 법률이 포함된다.|
16|②|02|O|위헌법률심판의 대상인 법률에는 조약 등 형식적 의미의 법률과 동일한 효력을 가지는 법규범도 포함된다.|
16|③|01|O|위헌법률심판에서 재판의 전제가 된 경우의 재판에는 본안에 관한 재판이 포함된다.|
16|③|02|O|위헌법률심판에서 재판의 전제가 된 경우의 재판에는 소송절차에 관한 재판도 포함된다.|
16|④|01|O|헌법재판소법 제68조 제2항 헌법소원은 법률의 위헌여부 심판 제청신청이 기각된 때 청구할 수 있다.|
16|⑤|01|X|개별·구체적 사건에서 단순히 법률조항의 포섭이나 적용을 다투는 헌법소원은 허용되지 않는다.|단순한 법률조항 포섭·적용 문제도 적법한 헌법소원이라고 한 부분
17|①|01|O|헌법상 근로의 권리는 일할 자리에 관한 권리뿐 아니라 일할 환경에 관한 권리도 포함한다.|
17|①|02|O|일할 환경에 관한 권리는 건강한 작업환경, 정당한 보수, 합리적 근로조건 보장을 요구할 수 있는 권리를 포함한다.|
17|②|01|X|근로자의 퇴직급여청구권은 헌법에서 바로 도출되지 않고 관련 법률이 정하는 바에 따라 인정된다.|모든 근로자가 헌법상 권리로서 퇴직급여청구권을 갖는다고 한 부분
17|③|01|O|근로자의 최저임금청구권은 헌법상 바로 도출되는 것이 아니라 최저임금법 등 관련 법률에 따라 인정된다.|
17|④|01|O|근로의 권리는 개인인 근로자가 주체가 되는 권리이다.|
17|④|02|O|노동조합은 헌법 제32조 제1항의 근로의 권리 주체가 될 수 없다.|
17|⑤|01|O|헌법은 연소자의 근로가 특별한 보호를 받는다고 규정한다.|
18|①|01|X|대통령령은 법률에서 구체적으로 범위를 정하여 위임받은 사항에 관하여 국민의 권리·의무 사항을 규율할 수 있다.|대통령령이 법률 위임 없이 국민의 권리·의무 사항을 규율할 수 있다고 한 부분
18|②|01|X|국민의 기본권 실현과 관련된 본질적 사항을 법률이 스스로 정하지 않고 행정입법에 위임하면 법률유보원칙에 위반된다.|본질적 사항을 행정입법에 위임해도 법률유보원칙 위반이 아니라고 한 부분
18|③|01|X|오늘날 법률유보원칙은 의회유보원칙을 내포한다.|법률유보원칙과 의회유보원칙이 서로 다른 별개 원리라고 한 부분
18|④|01|O|조례에 대한 법률의 위임은 법규명령에 대한 위임처럼 반드시 구체적으로 범위를 정할 필요는 없다.|
18|④|02|O|조례에 대한 법률의 위임은 포괄적인 것으로 충분할 수 있다.|
18|⑤|01|X|입법자가 형식적 법률로 직접 규율하여야 할 사항은 일률적으로 획정할 수 없다.|입법자가 형식적 법률로 직접 규율할 사항이 일률적으로 획정되어야 한다고 한 부분
18|⑤|02|X|국민의 자유나 권리를 제한하는 경우 그 제한의 본질적 사항은 입법자가 법률로 직접 규율하여야 한다.|입법자가 형식적 법률로 직접 규율할 사항이 일률적으로 획정되어야 한다고 한 부분
19|①|01|X|헌법상 지방자치제도의 보장은 특정 지방자치단체의 존속을 보장하는 것은 아니다.|헌법상 특정 지방자치단체의 존속이 보장되어 폐치·분합이 허용되지 않는다고 한 부분
19|①|02|X|지방자치단체의 폐치·분합은 헌법적으로 허용될 수 있다.|헌법상 특정 지방자치단체의 존속이 보장되어 폐치·분합이 허용되지 않는다고 한 부분
19|②|01|O|지방자치단체 상호 간 권한의 유무나 범위에 관한 다툼이 있으면 해당 지방자치단체는 권한쟁의심판을 청구할 수 있다.|
19|③|01|O|헌법상 지방자치단체에는 의회를 두어야 한다.|
19|④|01|O|지방자치단체는 주민의 복리에 관한 사무를 처리하고 재산을 관리한다.|
19|④|02|O|지방자치단체는 법령의 범위 안에서 자치에 관한 규정을 제정할 수 있다.|
19|⑤|01|O|지방자치단체가 제정한 조례가 법령에 위반되면 효력이 없다.|
20|①|01|O|대통령은 법률이 정하는 바에 따라 사면·감형 또는 복권을 명할 수 있다.|
20|②|01|O|대통령은 헌법과 법률이 정하는 바에 따라 국군을 통수한다.|
20|③|01|X|대통령이 계엄을 선포한 때에는 지체 없이 국회에 통고하여야 한다.|계엄 선포 시 대통령이 지체 없이 국회에 보고하여 승인을 얻어야 한다고 한 부분
20|③|02|X|계엄 선포 자체에 관하여 헌법은 국회의 사전 승인 또는 사후 승인 취득을 요구하지 않는다.|계엄 선포 시 대통령이 국회 승인을 얻어야 한다고 한 부분
20|④|01|O|대통령은 국회에 출석하여 발언하거나 서한으로 의견을 표시할 수 있다.|
20|⑤|01|O|대통령은 법률이 정하는 바에 따라 훈장 기타 영전을 수여한다.|
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
        raise ValueError("cannot locate 2021 constitution section")
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
        statement = re.split(r"\s*제1교시\s*①책형\s*전체|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    first_by_label = {}
    for marker in re.finditer(r"[㉠㉡㉢㉣㉤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(BOX_LABELS):
            break
    if set(first_by_label) != set(BOX_LABELS):
        raise ValueError("cannot split five box statements")
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label["㉤"].end() :])
    choice_start = first_by_label["㉤"].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in BOX_LABELS]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(0)] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-true" else CHOICE_LABELS
        split = split_box_units(blocks[no]) if labels == BOX_LABELS else split_choice_units(blocks[no])
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
        qid = f"2021-g1-constitution-{no:02d}"
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-true" else CHOICE_LABELS
        units = [
            {
                "unitId": f"{qid}-{LABEL_CODE[label]}",
                "unitType": "boxStatement" if label in BOX_LABELS else "choice",
                "label": label,
                "rawStatement": raws[(no, label)],
                "originalVerdict": source_verdict(no, label),
            }
            for label in labels
        ]
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
            items.append({
                "atomId": f"bupmusa-2021-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}",
                "sourceUnitId": item["unitId"],
                "sourceAtomIndex": row["atomIndex"],
                "sourceFamily": "법무사시험",
                "source": item["source"],
                "year": YEAR,
                "round": ROUND,
                "subject": SUBJECT_NAME,
                "no": item["no"],
                "unitType": item["unitType"],
                "unitLabel": item["unitLabel"],
                "sourceQuestionType": item["sourceQuestionType"],
                "officialQuestionAnswer": item["officialQuestionAnswer"],
                "sourceUnitVerdict": item["originalVerdict"],
                "sourceVerdict": row["sourceVerdict"],
                "currentVerdict": "O",
                "rep": rep,
                "a": "O",
                "basisType": basis_type,
                "basisRef": basis_ref,
                "why": why,
                "sourceStatement": item["rawStatement"],
                "sourceTrap": row["trap"],
                "xDependsOn": rep if source_is_x else None,
                "reviewedAt": today(),
                "currentLawCheckedAt": today(),
            })
    return {
        "schema": "legal-scrivener/completed-atoms-by-subject/v2",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "atomPrinciple": "docs/atom_원칙_v001.md",
        "source": str(SOURCE_PATH),
        "sourceQueue": str(QUEUE_PATH),
        "sourceCount": len(queue["items"]),
        "questionCount": QUESTION_COUNT,
        "atomCount": len(items),
        "verificationSources": LEGAL_SOURCES,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "atomSplit": "원문 보기 하나가 여러 조문·판례·학설 판단 지점을 포함하면 여러 atom으로 분해한다.",
            "xHandling": "원문상 틀린 판단 지점은 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형·개수형 문제는 선택지 조합이 아니라 박스 문장별 근거명제로 atom화한다.",
        },
        "items": items,
    }


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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2021-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v005_2021_integrated", "builtAt": today(), "sourceFiles": {str(year): str(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2021-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
