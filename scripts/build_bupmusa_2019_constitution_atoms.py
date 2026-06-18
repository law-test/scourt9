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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2019" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2019_법무사_헌법_헌법-1책형.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2019"
TEXT_DIR = PRIVATE_ROOT / "text" / "2019"
RAW_PDF_PATH = RAW_DIR / "2019_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2019_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2019_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2019_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2019_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2019_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2019_bupmusa_1st"
YEAR = 2019
ROUND = 25
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 120
CHOICE_LABELS = ["①", "②", "③", "④", "⑤"]
BOX_LABELS = ["가", "나", "다", "라", "마"]
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
}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "2019 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2019"},
    {"title": "2019 법무사 헌법 해설", "publisher": "이상용 헌법", "url": "local:2019_법무사_헌법_해설_법무사_이상용.pdf"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "②",
    3: "③",
    4: "①",
    5: "①",
    6: "④",
    7: "③",
    8: "③",
    9: "④",
    10: "③",
    11: "③",
    12: "①",
    13: "④",
    14: "④",
    15: "⑤",
    16: "⑤",
    17: "②",
    18: "③",
    19: "④",
    20: "③",
}

QUESTION_TYPES = {
    1: "single-best-false",
    2: "single-best-false",
    3: "single-best-false",
    4: "single-best-false",
    5: "single-best-false",
    6: "single-best-false",
    7: "single-best-false",
    8: "count-false",
    9: "single-best-true",
    10: "single-best-true",
    11: "single-best-true",
    12: "single-best-false",
    13: "single-best-false",
    14: "single-best-false",
    15: "single-best-false",
    16: "single-best-false",
    17: "odd-one",
    18: "single-best-false",
    19: "single-best-true",
    20: "single-best-false",
}

FALSE_LABELS = {
    1: {"⑤"},
    2: {"②"},
    3: {"③"},
    4: {"①"},
    5: {"①"},
    6: {"④"},
    7: {"③"},
    8: {"나", "다", "마"},
    9: {"①", "②", "③", "⑤"},
    10: {"①", "②", "④", "⑤"},
    11: {"①", "②", "④", "⑤"},
    12: {"①"},
    13: {"④"},
    14: {"④"},
    15: {"⑤"},
    16: {"⑤"},
    17: {"①", "③", "④", "⑤"},
    18: {"③"},
    19: {"①", "②", "③", "⑤"},
    20: {"③"},
}

TOPICS = {
    1: "무상교육과 교육기본권",
    2: "집회의 자유",
    3: "주민소환제와 지방자치",
    4: "행복추구권",
    5: "언론·출판의 자유",
    6: "합헌적 법률해석",
    7: "보안처분과 형벌불소급",
    8: "헌법 조문",
    9: "낙태와 자기결정권",
    10: "위헌법률심판과 헌법소원 대상",
    11: "예산",
    12: "국회 의사절차",
    13: "국무총리",
    14: "헌법소원의 보충성",
    15: "변호사의 직업의 자유",
    16: "대법원",
    17: "규칙제정권",
    18: "혼인과 가족제도",
    19: "대통령 선거",
    20: "1987년 제9차 개정헌법",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    8: ("헌법+법원조직법", "헌법 제8조·제26조·제27조·제64조·제111조 및 법원조직법 제4조", "헌법 조문에 명시된 사항과 법률 규정 사항을 구별하는 지점이다."),
    10: ("헌법+헌법재판소법+헌법재판소 결정례", "헌법 제6조, 헌법 제111조, 헌법재판소법 제41조·제68조 및 관련 결정례", "위헌심사 대상이 되는 법률·조약·국제법규·관습법과 헌법 개별규정을 구별하는 지점이다."),
    11: ("헌법+헌법재판소 결정례", "헌법 제54조·제55조·제56조·제57조 및 예산 관련 결정례", "예산안 제출기한, 계속비, 추가경정예산안, 예산의 헌법소원 대상성을 구별하는 조문 지점이다."),
    16: ("헌법+법원조직법", "헌법 제102조·제104조 및 법원조직법 제4조·제7조·제13조", "대법원의 구성과 심판권, 대법원장 권한대행에 관한 조문 지점이다."),
    17: ("헌법+감사원법", "헌법 제64조·제100조·제108조·제113조·제114조 및 감사원법 제52조", "기관별 규칙제정권의 헌법 근거와 법률 근거를 구별하는 조문 지점이다."),
    19: ("헌법", "헌법 제67조·제68조", "대통령 선거 방식, 최고득표자 동수, 단독후보, 궐위와 임기만료 선거기한에 관한 조문 지점이다."),
    20: ("헌법사+헌법 조문", "1980년 제8차 개정헌법, 1987년 제9차 개정헌법 및 현행 헌법 전문·제21조·제30조·제35조", "현행 헌법에서 처음 규정되거나 부활한 내용을 구별하는 헌법사 지점이다."),
})

ATOM_ROWS = """
1|①|01|O|의무교육제도는 국민의 교육을 받을 권리를 뒷받침하는 헌법상 교육기본권에 부수되는 제도보장이다.|
1|①|02|O|의무교육제도는 교육의 자주성·전문성·정치적 중립성을 지도원리로 한다.|
1|②|01|O|헌법 제31조 제2항은 초등교육과 법률이 정하는 교육을 의무교육으로 실시하도록 규정한다.|
1|②|02|O|초등교육 이외의 교육을 의무교육으로 할 범위와 실시 시점은 입법자의 형성의 자유에 속한다.|
1|③|01|O|중학교교육에 대한 의무교육을 단계적으로 실시하는 경우 그 혜택을 아직 받지 못한 지역 주민의 구체적 헌법상 권리가 침해된다고 볼 수 없다.|
1|③|02|O|초등교육 이외의 의무교육은 구체적 법률 규정으로 비로소 헌법상 권리로 구체화된다.|
1|④|01|O|교육의 기회균등권은 정신적·육체적 능력 이외의 성별·종교·경제력·사회적 신분 등에 따른 교육기회 차별을 금지한다.|
1|④|02|O|교육의 기회균등권은 경제적 약자가 실질적 평등교육을 받을 수 있도록 국가가 적극적 정책을 실현할 의무를 포함한다.|
1|⑤|01|X|의무교육 무상원칙이 곧 학교급식 경비 전부를 국가와 지방자치단체가 부담하여야 한다는 뜻은 아니다.|급식 경비 전면 무상이 아니면 의무교육 무상원칙에 위배된다고 한 부분
1|⑤|02|X|의무교육 대상 학생의 학부모에게 급식 관련 비용 일부를 부담하게 하는 법률조항이 입법형성권을 넘어 의무교육 무상원칙에 반한다고 보기 어려울 수 있다.|급식 관련 비용 일부를 학부모에게 부담시키면 당연히 위헌이라고 한 부분
2|①|01|O|집회의 자유는 개인의 인격발현에 기여하는 기본권이다.|
2|①|02|O|집회의 자유는 국민이 의견과 주장을 집단적으로 표명하여 여론 형성에 영향을 미치게 하는 민주주의의 근본요소이다.|
2|②|01|X|집회의 자유로 보호되는 집회는 평화적 또는 비폭력적 집회이다.|평화적 또는 비폭력적 집회만 보호된다고 할 수 없다고 한 부분
2|②|02|X|폭력을 사용한 의견의 강요는 집회의 자유로 보호되지 않는다.|폭력적 집회도 집회의 자유로 보호된다고 한 부분
2|③|01|O|신고된 범위 내의 도로 집회나 시위로 교통이 방해되더라도 특별한 사정이 없으면 일반교통방해죄가 성립하지 않는다.|
2|③|02|O|집회나 시위가 신고 범위를 현저히 일탈하거나 중대한 조건 위반으로 도로 통행을 불가능하게 하면 일반교통방해죄가 성립할 수 있다.|
2|④|01|O|학문·예술·체육·종교·의식·친목·오락·관혼상제 및 국경행사에 관한 집회에는 집회 및 시위에 관한 법률상 신고규정이 적용되지 않는다.|
2|⑤|01|O|집회는 일반적으로 일정한 장소를 전제로 특정 목적을 가진 다수인이 일시적으로 회합하는 것을 말한다.|
2|⑤|02|O|집회의 공동 목적은 내적인 유대관계로 족하다.|
3|①|01|O|주민소환제는 임기 종료 전 주민이 직접 특정 지방공직자의 해직을 청구하는 제도이다.|
3|①|02|O|주민소환제는 주민의 참정기회를 확대하고 주민대표나 행정기관에 대한 통제와 책임성을 확보하는 제도적 의의를 가진다.|
3|②|01|O|주민소환제는 선거제도의 실패를 보완하는 긍정적 기능을 가진다.|
3|②|02|O|주민소환제는 정치적 악용·남용이나 선출직 공직자 활동 위축으로 지방행정의 효율성을 저해할 소지도 있다.|
3|③|01|X|주민소환제 자체는 지방자치의 본질적 내용이라고 할 수 없다.|주민소환제 자체가 지방자치의 본질적 내용이라고 한 부분
3|③|02|X|특정한 내용의 주민소환제를 반드시 보장하여야 한다는 헌법상 요구가 있다고 볼 수 없다.|주민소환제에 대한 특정한 헌법상 보장 요구가 있다고 한 부분
3|④|01|O|주민소환권은 주민소환제에 부수하여 법률상 창설되는 권리이다.|
3|④|02|O|주민소환권은 헌법 제37조 제1항의 열거되지 않은 기본권으로 볼 수 없다.|
3|⑤|01|O|지방자치법상 주민투표권이나 주민소환청구권은 법률이 보장하는 참정권으로 볼 수 있다.|
3|⑤|02|O|지방자치법상 주민투표권이나 주민소환청구권은 헌법이 보장하는 선거권·공무담임권·국민투표권과 같은 참정권은 아니다.|
4|①|01|X|행복추구권은 국민이 행복 추구 활동을 국가권력의 간섭 없이 자유롭게 할 수 있는 포괄적 자유권이다.|행복추구권이 국가에 필요한 급부를 적극적으로 요구할 수 있는 권리라고 한 부분
4|①|02|X|행복추구권은 국민이 행복 추구에 필요한 급부를 국가에 적극적으로 요구할 수 있는 것을 내용으로 하지 않는다.|행복추구권의 급부청구권성을 인정한 부분
4|②|01|O|기부행위는 행복추구권에서 파생되는 일반적 행동자유권에 의하여 보호된다.|
4|②|02|O|기부행위자는 재산을 사회적 약자나 소외계층을 위해 출연함으로써 행복감과 만족감을 실현할 수 있다.|
4|③|01|O|일반적 행동자유권은 모든 행위를 할 자유와 하지 않을 자유를 보호한다.|
4|③|02|O|일반적 행동자유권의 보호영역에는 위험한 스포츠를 즐길 권리 같은 위험한 생활방식으로 살아갈 권리도 포함된다.|
4|④|01|O|게임물이용자 본인인증수단 마련을 강제하는 조항은 게임 이용자의 일반적 행동자유권을 제한한다.|
4|④|02|O|게임물이용자 본인인증수단 마련 조항은 게임 과몰입과 중독 방지라는 중대한 공익 등을 고려하면 일반적 행동자유권을 침해하지 않는다고 볼 수 있다.|
4|⑤|01|O|수형자의 가족에 대한 접견교통권은 헌법 제10조 행복추구권에 포함되는 일반적 행동자유권에서 나온다.|
5|①|01|O|건강기능식품 기능성 광고도 헌법 제21조 제1항의 표현의 자유 보호대상이다.|
5|①|02|X|식품의약품안전처장이 위탁한 건강기능식품 기능성 광고 사전심의는 행정권 개입 가능성이 있으면 헌법상 금지되는 사전검열에 해당한다.|한국건강기능식품협회의 독립성을 이유로 사전검열성을 부정한 부분
5|②|01|O|의사표현의 자유는 헌법 제21조 제1항의 언론·출판의 자유에 속한다.|
5|②|02|O|TV 방송도 의사표현의 한 수단으로서 헌법상 언론·출판의 자유에 의하여 보장된다.|
5|③|01|O|표현내용에 대한 규제는 중대한 공익 실현을 위하여 불가피한 경우에 엄격한 요건 아래 허용된다.|
5|③|02|O|표현내용과 무관한 표현방법 규제는 합리적인 공익상 이유로 비교적 폭넓게 제한될 수 있다.|
5|④|01|O|방송의 자유는 주관적 권리와 객관적 규범질서로서 제도적 보장의 성격을 함께 가진다.|
5|④|02|O|방송매체의 특수성을 고려하면 방송 기능 보장을 위한 규율 필요성은 신문 등 인쇄매체보다 높다.|
5|⑤|01|O|선거운동의 자유는 선거과정에서 의사표현을 하는 자유로서 헌법 제21조의 언론·출판의 자유에 의하여 보호된다.|
5|⑤|02|O|후보자 입장에서 선거운동의 자유는 헌법 제25조의 공무담임권 중 피선거권 행사를 위한 전제가 된다.|
6|①|01|O|법률 개념이 다의적이고 어의의 범위 안에서 여러 해석이 가능하면 헌법에 합치되는 해석을 택하여야 한다.|
6|①|02|O|합헌적 법률해석은 위헌적 결과가 될 해석을 배제하면서 합헌적이고 긍정적인 면을 살리는 법리이다.|
6|②|01|O|합헌적 법률해석은 헌법의 최고규범성에서 나오는 법질서 통일성에 바탕을 둔다.|
6|②|02|O|합헌적 법률해석은 권력분립과 입법권 존중의 정신에 뿌리를 둔다.|
6|③|01|O|합헌적 법률해석은 법 문구의 말뜻이 완전히 다른 의미로 변질되지 않는 범위 안에서 이루어져야 한다.|
6|③|02|O|합헌적 법률해석은 입법자의 명백한 의지와 입법목적을 헛되게 하는 내용으로 할 수 없다.|
6|④|01|X|헌법재판소도 법률의 위헌 여부를 판단하기 위하여 불가피하게 법령을 해석하거나 적용 범위를 판단할 수 있다.|합헌적 법률해석이 헌법재판소의 임무가 전혀 아니라고 한 부분
6|④|02|X|헌법재판소의 선행 법률해석이 대법원이나 각급 법원을 구속하는 것은 아니다.|헌법재판소의 법률해석 관련 역할을 전면 부정한 부분
6|⑤|01|O|합헌적인 한정축소해석은 위헌적 해석 가능성과 그에 따른 법적용을 소극적으로 배제한다.|
6|⑤|02|O|적용범위 축소에 의한 한정위헌결정은 위헌적 법적용 영역과 그에 상응하는 해석 가능성을 적극적으로 배제한다.|
7|①|01|O|보안처분이라도 형벌적 성격이 강하여 신체의 자유를 박탈하거나 이에 준하면 소급효금지원칙을 적용할 수 있다.|
7|①|02|O|보안처분이라는 형식을 이유로 형벌불소급원칙을 유명무실하게 하는 것은 허용되지 않는다.|
7|②|01|O|성폭력 치료프로그램 이수명령은 과거 범죄행위 제재가 아니라 건전한 사회복귀 촉진과 범죄예방·사회보호를 목적으로 하는 보안처분이다.|
7|②|02|O|성폭력 치료프로그램 이수명령이 형벌과 병과되더라도 이중처벌금지원칙에 위배된다고 할 수 없다.|
7|③|01|X|노역장유치는 실질적으로 신체의 자유를 박탈하므로 징역형과 유사한 형벌적 성격을 가진다.|노역장유치를 형벌과 구별되는 환형처분으로만 본 부분
7|③|02|X|노역장유치기간 하한을 중하게 변경한 조항을 시행 전 범죄행위에 적용하도록 하는 것은 형벌불소급원칙에 위반된다.|노역장유치기간 하한 강화의 소급적용에 형벌불소급 문제가 없다고 한 부분
7|④|01|O|전자장치 부착명령은 전통적 의미의 형벌이 아니라 비형벌적 보안처분이다.|
7|④|02|O|전자장치 부착명령에는 소급효금지원칙이 적용되지 않는다.|
7|⑤|01|O|가정폭력 보호처분 중 사회봉사명령은 보안처분의 성격을 가진다.|
7|⑤|02|O|가정폭력 보호처분 중 사회봉사명령은 실질적으로 신체적 자유를 제한하므로 원칙적으로 행위시법을 적용하여야 한다.|
8|가|01|O|모든 국민은 법률이 정하는 바에 의하여 국가기관에 문서로 청원할 권리를 가진다.|
8|나|01|X|형사피고인은 유죄의 판결이 확정될 때까지 무죄로 추정된다.|무죄추정의 종기를 유죄판결 선고 때까지라고 한 부분
8|다|01|X|정당의 목적이나 활동이 민주적 기본질서에 위배될 때에는 정부가 헌법재판소에 그 해산을 제소할 수 있다.|정당해산 제소권자를 국회라고 한 부분
8|라|01|O|국회는 의원의 자격을 심사하고 의원을 징계할 수 있다.|
8|라|02|O|국회의원을 제명하려면 국회재적의원 3분의 2 이상의 찬성이 있어야 한다.|
8|라|03|O|국회의원의 자격심사·징계·제명처분에 대하여는 법원에 제소할 수 없다.|
8|마|01|O|헌법재판소는 법관의 자격을 가진 9인의 재판관으로 구성한다.|
8|마|02|X|대법관의 수가 대법원장을 포함하여 14명이라는 점은 헌법이 아니라 법원조직법에 규정되어 있다.|대법원 대법관 수가 헌법에 명시되어 있다고 한 부분
9|①|01|X|자기낙태죄 조항의 위헌 여부는 임신한 여성의 자기결정권과 태아의 생명권이 직접 충돌하는 사안으로 보는 것이 적절하지 않다.|자기낙태죄 위헌 여부를 두 기본권의 직접 충돌 문제로 본 부분
9|①|02|X|자기낙태죄 조항의 위헌 여부는 임신한 여성의 자기결정권 제한이 과잉금지원칙에 위배되는지를 중심으로 심사한다.|규범조화적 해결만으로 사안을 설명한 부분
9|②|01|X|국가가 생명을 보호하는 입법적 조치를 할 때 인간생명의 발달단계에 따라 보호정도나 보호수단을 달리할 수 있다.|인간생명의 발달단계에 따라 보호수단을 달리할 수 없다고 한 부분
9|②|02|X|태아가 모체 밖에서 독자적으로 생존할 수 있는 시점 전까지는 국가가 생명보호의 수단과 정도를 달리 정할 수 있다.|태아 생명 보호수단이 모든 단계에서 동일하여야 한다고 한 부분
9|③|01|X|임신 제1삼분기에는 아무 사유 없이 낙태할 수 있도록 하여야 한다는 견해는 헌법불합치 결정의 법정의견이 아니라 위헌의견의 논지이다.|임신 제1삼분기 무사유 낙태 허용을 법정의견처럼 전제한 부분
9|④|01|O|업무상동의낙태죄와 자기낙태죄는 대향범 관계에 있다.|
9|④|02|O|자기낙태죄가 위헌이면 같은 목표를 실현하기 위한 의사낙태죄 조항도 같은 이유에서 위헌이라고 보아야 한다.|
9|⑤|01|X|모자보건법상 낙태 정당화사유에는 다양하고 광범위한 사회적·경제적 사유가 포함되어 있지 않다.|모자보건법상 정당화사유에 사회적·경제적 사유가 포함된다고 한 부분
9|⑤|02|O|모자보건법상 정당화사유는 임신한 여성의 자기결정권을 보장하기에 불충분하다.|
10|①|01|X|대한민국과 미국 사이의 상호방위조약 관련 주한미군 지위협정 조항은 국회의 동의를 요하는 조약으로서 위헌법률심판 대상이 될 수 있다.|주한미군 지위협정 조항이 위헌법률심판 대상이 될 수 없다고 본 부분
10|②|01|X|국회의 동의를 얻어 체결되어 국내법적 효력을 가지는 국제통화기금협정 조항은 위헌법률심판 대상이 될 수 있다.|국제통화기금협정 조항이 위헌법률심판 대상이 될 수 없다고 본 부분
10|③|01|O|헌법의 개별규정 자체는 헌법소원에 의한 위헌심사의 대상이 아니다.|
10|③|02|O|위헌법률심판과 헌법재판소법 제68조 제2항 헌법소원심판의 대상인 법률은 국회의 의결을 거쳐 제정된 형식적 의미의 법률을 뜻한다.|
10|④|01|X|법률과 같은 효력을 가지는 일반적으로 승인된 국제법규는 위헌법률심판 대상이 될 수 있다.|일반적으로 승인된 국제법규가 위헌법률심판 대상이 될 수 없다고 본 부분
10|⑤|01|X|민법 시행 전 상속을 규율한 구 관습법처럼 법률과 같은 효력을 가지는 관습법은 헌법소원심판 대상이 될 수 있다.|법률과 같은 효력을 가지는 구 관습법이 헌법소원심판 대상이 될 수 없다고 본 부분
11|①|01|X|정부는 회계연도마다 예산안을 편성하여 회계연도 개시 90일 전까지 국회에 제출하여야 한다.|예산안 제출기한을 회계연도 개시 60일 전이라고 한 부분
11|①|02|O|국회는 예산안을 회계연도 개시 30일 전까지 의결하여야 한다.|
11|②|01|X|국회는 정부의 동의 없이 정부가 제출한 지출예산 각항의 금액을 증가할 수 없다.|정부 동의 없이 지출예산 각항 금액을 증가할 수 있다고 한 부분
11|②|02|X|국회는 정부의 동의 없이 정부가 제출한 예산에 새 비목을 설치할 수 없다.|정부 동의 없이 새 비목을 설치할 수 있다고 한 부분
11|③|01|O|한 회계연도를 넘어 계속하여 지출할 필요가 있을 때에는 정부는 연한을 정하여 계속비로서 국회의 의결을 얻어야 한다.|
11|④|01|X|정부는 예산에 변경을 가할 필요가 있을 때에는 추가경정예산안을 편성하여 국회에 제출할 수 있다.|예산 변경시 제출하는 예산안을 수정예산안이라고 한 부분
11|⑤|01|X|국회의 예산안 의결은 국가기관만을 구속하고 일반국민을 직접 구속하지 않는다.|예산안 의결이 일반국민을 구속한다고 한 부분
11|⑤|02|X|국회의 예산안 의결은 헌법재판소법 제68조 제1항의 공권력 행사에 해당하지 않아 헌법소원 대상이 아니다.|예산안 의결이 헌법소원심판 대상이라고 한 부분
12|①|01|X|우리나라 국회의 법률안 심의는 본회의 중심주의가 아니라 소관 상임위원회 중심주의로 이루어진다.|우리나라 국회가 본회의 중심주의를 채택한다고 한 부분
12|①|02|O|상임위원회는 회부된 안건을 심사하고 그 결과를 본회의에 보고하여 본회의의 판단자료를 제공한다.|
12|②|01|O|안건신속처리제도는 쟁점안건이 위원회에 장기간 계류되는 상황을 최소화하기 위한 제도적 장치이다.|
12|②|02|O|신속처리대상 안건은 일정기간이 지나면 자동으로 다음 단계로 진행하도록 설계되어 있다.|
12|③|01|O|국회법상 직권상정권한은 국회의장의 의사정리권에 속한다.|
12|③|02|O|국회법상 직권상정권한은 위원회 중심주의를 채택한 국회에서 비상적·예외적 의사절차에 해당한다.|
12|④|01|O|무제한토론 중 해당 회기가 종료되면 무제한토론은 종결 선포된 것으로 본다.|
12|④|02|O|무제한토론 중 회기 종료로 종결 선포된 안건은 바로 다음 회기에서 지체 없이 표결하여야 한다.|
12|⑤|01|O|국회 본회의는 재적의원 5분의 1 이상의 출석으로 개의한다.|
13|①|01|O|국무총리는 국무회의의 부의장이 된다.|
13|②|01|O|1954년 제2차 개정헌법에서는 국무총리제가 폐지되었다.|
13|③|01|O|헌법 제86조 제2항의 국무총리의 통할을 받는 행정각부에 모든 행정기관이 포함된다고 볼 수 없다.|
13|④|01|X|우리 헌법이 국무총리제도를 둔 주된 이유는 대통령 유고시 권한대행자와 대통령 보좌기관이 필요하다는 데 있다.|국무총리제도의 주된 이유를 대통령 권력 견제라고 한 부분
13|④|02|X|국무총리는 대통령의 첫째 가는 보좌기관으로서 대통령의 명을 받아 행정각부를 통할하는 지위에 있다.|국무총리가 대통령 권력 견제를 주된 기능으로 한다고 한 부분
13|⑤|01|O|국무총리는 국무위원의 해임을 대통령에게 건의할 수 있다.|
14|①|01|O|헌법소원 제기 후 종국결정 전에 다른 법률상 권리구제절차를 거치면 사전에 구제절차를 거치지 않은 하자가 치유될 수 있다.|
14|②|01|O|손해배상청구나 손실보상청구는 헌법재판소법 제68조 제1항 단서의 다른 법률상 구제절차에 해당하지 않는다.|
14|②|02|O|진정은 헌법재판소법 제68조 제1항 단서의 다른 법률상 구제절차에 해당하지 않는다.|
14|②|03|O|형의 집행 및 수용자의 처우에 관한 법률상 청원제도는 헌법재판소법 제68조 제1항 단서의 다른 법률상 구제절차에 해당하지 않는다.|
14|③|01|O|명령·규칙 자체의 효력을 다투는 행정소송의 길이 없으면 그 명령·규칙에 대하여 곧바로 헌법소원을 청구할 수 있다.|
14|③|02|O|금치기간 중 집필을 전면 금지하는 시행령 조항은 다른 구제절차 없이 바로 헌법소원심판을 청구할 수 있다.|
14|④|01|X|행정관청의 고시는 그 내용의 성질에 따라 법규명령·행정규칙 또는 행정처분으로 달라질 수 있다.|행정관청의 고시가 언제나 일반적·추상적 성격을 가진다고 한 부분
14|④|02|X|구체적 규율 성격을 가지는 고시는 행정처분에 해당할 수 있다.|행정관청의 고시는 모두 바로 헌법소원심판 대상이 된다고 한 부분
14|⑤|01|O|이미 종료된 권력적 사실행위가 행정심판이나 행정소송 대상으로 인정되기 어려우면 헌법소원심판 외에 효과적 구제방법이 없을 수 있다.|
14|⑤|02|O|구속 피의자를 수갑과 포승 사용 상태로 피의자신문받게 한 행위는 보충성 원칙의 예외가 인정될 수 있다.|
15|①|01|O|변호사가 법률사건 수임 알선의 대가로 금품을 제공하는 행위를 금지·처벌하는 것은 변호사의 직업수행의 자유를 제한한다.|
15|②|01|O|변호사시험 응시결격조항은 변호사 자격을 취득하려는 사람의 직업선택의 자유를 제한한다.|
15|②|02|O|변호사 자격요건 설정에는 국가의 폭넓은 입법재량이 인정되므로 유연하고 탄력적인 심사가 필요하다.|
15|③|01|O|변호사에게 수임사건의 건수와 수임액을 소속지방변호사회에 보고하도록 하는 것은 직업수행의 자유를 제한한다.|
15|④|01|O|법학전문대학원 졸업 후 5년 내 5회로 변호사시험 응시기회를 제한하는 조항은 직업선택의 자유를 제한한다.|
15|⑤|01|X|변호사시험 합격자의 시험성적 비공개는 알 권리 중 정보공개청구권을 제한한다.|시험성적 비공개가 직업선택의 자유를 제한한다고 한 부분
15|⑤|02|X|변호사시험 합격자 성적 비공개는 법조인으로서 직역 선택이나 직업수행에 어떠한 제한을 두는 것이 아니므로 직업선택의 자유를 제한한다고 볼 수 없다.|시험성적 비공개를 직업선택의 자유 제한으로 본 부분
16|①|01|O|대법원의 심판권은 원칙적으로 대법관 전원의 3분의 2 이상으로 구성된 합의체에서 행사한다.|
16|①|02|O|대법원 전원합의체에서는 대법원장이 재판장이 된다.|
16|②|01|O|대법원에는 법률이 정하는 바에 따라 대법관이 아닌 법관을 둘 수 있다.|
16|③|01|O|대법관의 수는 대법원장을 포함하여 14명이다.|
16|④|01|O|대법관은 대법원장의 제청으로 국회의 동의를 얻어 대통령이 임명한다.|
16|④|02|O|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|
16|⑤|01|X|대법원장이 궐위되거나 직무를 수행할 수 없을 때에는 선임대법관이 그 권한을 대행한다.|대법원장 권한대행자를 법원행정처장이라고 한 부분
17|①|01|X|국회의 규칙제정권은 헌법에 근거한다.|국회 규칙제정권이 다른 규범적 근거를 가진다고 본 부분
17|②|01|O|감사원규칙은 헌법이 아니라 감사원법에 근거한다.|
17|③|01|X|대법원의 규칙제정권은 헌법에 근거한다.|대법원 규칙제정권이 다른 규범적 근거를 가진다고 본 부분
17|④|01|X|헌법재판소의 규칙제정권은 헌법에 근거한다.|헌법재판소 규칙제정권이 다른 규범적 근거를 가진다고 본 부분
17|⑤|01|X|중앙선거관리위원회의 규칙제정권은 헌법에 근거한다.|중앙선거관리위원회 규칙제정권이 다른 규범적 근거를 가진다고 본 부분
18|①|01|O|헌법 제36조 제1항은 혼인과 가족생활을 스스로 결정하고 형성할 자유를 기본권으로 보장한다.|
18|①|02|O|헌법 제36조 제1항은 혼인과 가족에 관한 제도보장을 포함한다.|
18|②|01|O|헌법 제36조 제1항은 가족생활에서도 인간의 존엄과 양성평등이 보장되어야 한다는 기본권 성격을 가진다.|
18|②|02|O|헌법 제36조 제1항은 혼인과 가족생활에 관한 제도보장의 성격을 함께 가진다.|
18|③|01|X|중혼은 취소되더라도 배우자나 출생한 자녀의 신분관계가 사실상 완전히 원상회복될 수 없는 한계가 있다.|중혼금지에 현행법상 어떠한 예외적 고려도 없다고 한 부분
18|③|02|X|중혼으로 출생한 자녀의 신분관계를 보호할 사회적 이익이 인정될 수 있다.|중혼금지의 공익만으로 예외를 전면 부정한 부분
18|④|01|O|민법이 중혼의 취소청구권자에서 직계비속을 제외한 것은 합리적 이유 없는 차별로서 평등원칙에 위반된다.|
18|⑤|01|O|부모가 자녀의 건강에 반하는 방향으로 자녀교육권을 행사하면 국가는 부모의 자녀교육권을 제한할 수 있다.|
19|①|01|X|대통령 선거에서 최고득표자가 2인 이상이면 국회 재적의원 과반수가 출석한 공개회의에서 다수표를 얻은 사람을 당선자로 한다.|최고득표자 동수시 국회 재적의원 3분의 2 출석이 필요하다고 한 부분
19|②|01|X|대통령은 국민의 보통·평등·직접·비밀선거에 의하여 선출된다.|대통령 선거의 헌법상 방식에 직접선거 대신 자유선거를 든 부분
19|③|01|X|대통령후보자가 1인일 때에는 득표수가 선거권자 총수의 3분의 1 이상이어야 대통령으로 당선될 수 있다.|단독 대통령후보자 당선요건을 선거권자 총수 과반수라고 한 부분
19|④|01|O|대통령이 궐위되면 60일 이내에 후임자를 선거하여야 한다.|
19|④|02|O|대통령 당선자가 사망하거나 판결 기타 사유로 자격을 상실하면 60일 이내에 후임자를 선거하여야 한다.|
19|⑤|01|X|대통령의 임기가 만료될 때에는 임기만료 70일 내지 40일 전에 후임자를 선거하여야 한다.|대통령 임기만료 선거기한을 60일 내지 40일 전이라고 한 부분
20|①|01|O|범죄피해자구조청구권은 1987년 제9차 개정헌법에서 처음 규정되었다.|
20|②|01|O|대한민국임시정부의 법통 계승은 1987년 제9차 개정헌법에서 처음 규정되었다.|
20|③|01|X|환경권은 1980년 제8차 개정헌법에서 처음 규정되었다.|환경권이 1987년 제9차 개정헌법에서 처음 규정되었다고 한 부분
20|④|01|O|언론·출판에 대한 허가나 검열과 집회·결사에 대한 허가는 인정되지 않는다는 조항은 1987년 제9차 개정헌법에서 부활하였다.|
20|⑤|01|O|헌법재판제도는 현행 헌법에서 최초로 규정된 것이 아니다.|
20|⑤|02|O|헌법재판소는 1960년 제3차 개정헌법에서 처음 규정되었다.|
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
        raise ValueError("cannot locate 2019 constitution section")
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
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    first_by_label = {}
    for marker in re.finditer(r"(?<![가-힣])([가나다라마])\.", block):
        label = marker.group(1)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(BOX_LABELS):
            break
    if set(first_by_label) != set(BOX_LABELS):
        raise ValueError("cannot split five box statements")
    first_choice = re.search(r"[①②③④⑤]", block[first_by_label["마"].end() :])
    choice_start = first_by_label["마"].end() + first_choice.start() if first_choice else len(block)
    ordered = [first_by_label[label] for label in BOX_LABELS]
    out = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else choice_start
        out[marker.group(1)] = normalize_raw(block[start:end])
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw = {}
    for no in range(1, QUESTION_COUNT + 1):
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-false" else CHOICE_LABELS
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
        qid = f"2019-g1-constitution-{no:02d}"
        labels = BOX_LABELS if QUESTION_TYPES[no] == "count-false" else CHOICE_LABELS
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
            items.append({"atomId": f"bupmusa-2019-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2019-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v007_2019_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2019-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
