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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2009" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2009_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2009"
TEXT_DIR = PRIVATE_ROOT / "text" / "2009"
RAW_PDF_PATH = RAW_DIR / "2009_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2009_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2009_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2009_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2009_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2009_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2009_bupmusa_1st"
YEAR = 2009
ROUND = 15
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
    {"title": "2009 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2009/50837052"},
    {"title": "2009 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2009/93240"},
    {"title": "제15회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?act=procFileDownload&file_srl=93241&module=file&sid=3aca73d80769fa29149604c24eff4046"},
]

OFFICIAL_ANSWERS = {
    1: "④",
    2: "②",
    3: "②",
    4: "④",
    5: "⑤",
    6: "④",
    7: "③",
    8: "⑤",
    9: "①",
    10: "②",
    11: "⑤",
    12: "④",
    13: "①",
    14: "②",
    15: "①",
    16: "②",
    17: "②",
    18: "②",
    19: "⑤",
    20: "③",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    4: "single-best-true",
    5: "single-best-true",
    7: "single-best-true",
    13: "single-best-true",
    14: "single-best-true",
    18: "single-best-true",
})

FALSE_LABELS = {
    1: {"④"},
    2: {"②"},
    3: {"②"},
    4: {"①", "②", "③", "⑤"},
    5: {"①", "②", "③", "④"},
    6: {"④"},
    7: {"①", "②", "④", "⑤"},
    8: {"⑤"},
    9: {"①"},
    10: {"②"},
    11: {"⑤"},
    12: {"④"},
    13: {"②", "③", "④", "⑤"},
    14: {"①", "③", "④", "⑤"},
    15: {"①"},
    16: {"②"},
    17: {"②"},
    18: {"①", "③", "④", "⑤"},
    19: {"⑤"},
    20: {"③"},
}

TOPICS = {
    1: "국가배상",
    2: "선거의 원칙",
    3: "신체의 자유",
    4: "정당",
    5: "언론·출판의 자유와 알권리",
    6: "집회·결사의 자유",
    7: "헌법재판소 결정",
    8: "헌법소원",
    9: "경제질서",
    10: "대통령 권한",
    11: "조세법률주의와 조세평등주의",
    12: "탄핵심판",
    13: "양심의 자유와 종교의 자유",
    14: "형사보상청구권",
    15: "국정감사 및 국정조사",
    16: "법원",
    17: "기본권의 효력",
    18: "헌법기관 구성",
    19: "국회",
    20: "재외국민의 법적 지위",
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
1|①|01|O|경매담당 공무원의 잘못된 기일통지로 경락허가결정이 취소된 경우에는 그 위법한 직무집행과 상당인과관계 있는 경락대금 및 등기비용 손해에 관하여 국가배상책임이 인정될 수 있다.|
1|②|01|O|향토예비군대원이 훈련 등 직무집행과 관련하여 공상을 입고 다른 법령에 따른 재해보상금 등을 받을 수 있으면 국가배상법에 따른 손해배상을 청구할 수 없다.|
1|③|01|O|국가배상책임에서 공무원의 직무에는 권력적 작용뿐 아니라 비권력적 작용도 포함되지만, 행정주체가 사경제주체로서 하는 활동은 제외된다.|
1|④|01|X|행정처분이 항고소송에서 취소되었다는 사실만으로 곧바로 공무원의 고의 또는 과실에 의한 불법행위가 성립한다고 볼 수는 없다.|행정처분이 취소되면 곧바로 공무원의 고의 또는 과실에 의한 불법행위가 성립한다고 한 부분
1|⑤|01|O|법관의 재판에 법령 규정을 따르지 않은 잘못이 있더라도 국가배상책임은 권한 취지에 명백히 어긋난 행사라고 인정할 특별한 사정이 있을 때 인정된다.|
2|①|01|O|국회의원 선거구 사이의 인구편차가 문제되는 경우 선거구구역표는 전체가 불가분의 일체를 이루므로 선거구구역표 전부에 관하여 위헌선언을 하는 것이 상당하다.|
2|②|01|X|국회의원 선거구 인구편차의 허용한계는 시·도의원 선거구와 동일하게 4대 1로 볼 수 없고, 국회의원 선거구에는 더 엄격한 기준이 적용되었다.|국회의원과 시·도의원 선거구 인구편차의 적절한 상한선을 모두 4대 1로 본 부분
2|③|01|O|1인 1표주의는 평등선거원칙에 입각한 것이며, 선거의 평등에는 투표가치의 실질적 평등 요청이 포함된다.|
2|④|01|O|자유선거원칙의 한 내용인 선거운동의 자유는 표현의 자유의 한 태양이므로 헌법 제21조에 의해서도 보호된다.|
2|⑤|01|O|선상에 장기 기거하는 사람에게 팩시밀리 등을 통한 부재자투표를 허용하지 않는 것은 보통선거원칙을 침해할 수 있다.|
3|①|01|O|신체구속을 당한 피의자와 변호인 사이의 자유로운 접견은 변호인의 조력을 받을 권리의 핵심 내용으로서 함부로 제한할 수 없다.|
3|②|01|X|외국에서 형사처벌 확정판결을 받은 행위라도 국내에서 다시 형사처벌하는 것이 일사부재리원칙에 당연히 반한다고 볼 수는 없다.|외국 확정판결을 받은 행위의 국내 재처벌이 일사부재리원칙상 허용될 수 없다고 한 부분
3|③|01|O|적법절차원칙은 절차의 적법성뿐 아니라 실체적 법률내용도 합리성과 정당성을 갖추어야 한다는 의미를 가진다.|
3|④|01|O|적법절차원칙은 형사절차뿐 아니라 기본권 제한과 관련된 행정절차에도 적용된다.|
3|⑤|01|O|일사부재리원칙은 거듭된 국가 형벌권 행사를 금지하는 것이므로 모든 제재나 불이익처분까지 당연히 포함하는 것은 아니다.|
4|①|01|X|정당국가적 민주주의가 강조되더라도 대의제 민주주의를 당연히 후퇴시키는 것은 아니며, 양자는 헌법질서 안에서 조화되어야 한다.|정당국가적 민주주의가 대의제 민주주의보다 우선한다고 한 부분
4|②|01|X|헌법 제8조 제1항의 정당의 자유는 국민 개인뿐 아니라 단체로서의 정당도 누릴 수 있는 기본권적 성격을 가진다.|정당의 자유가 국민 개인의 기본권일 뿐 정당 자체의 기본권이 아니라고 한 부분
4|③|01|X|임기만료에 의한 국회의원선거에 참여한 정당은 의석을 얻지 못하고 유효투표총수의 100분의 2 이상도 득표하지 못한 때 등록이 취소된다.|의석을 얻지 못하거나 유효투표총수 100분의 2 이상을 득표하지 못하면 등록이 취소된다고 한 부분
4|③|02|O|정당이 등록취소 등으로 해산한 경우 잔여재산은 정당법이 정한 방식에 따라 처분되고, 처분되지 않은 잔여재산은 국고에 귀속된다.|
4|④|01|O|정당은 중요한 공적 기능을 수행하는 자발적 조직이고, 그 소유재산의 귀속관계에서는 법인격 없는 사단으로서의 법적 지위를 가진다.|
4|⑤|01|X|정당해산심판은 정부가 국무회의 심의를 거쳐 헌법재판소에 제소하는 것이며, 국회는 정당해산심판의 제소권자가 아니다.|정부나 국회가 정당해산을 제소할 수 있다고 한 부분
5|①|01|X|알권리와 정보접근의 자유는 헌법상 직접 도출될 수 있으므로 이를 구체화하는 법률이 없다는 이유만으로 그 실현이 전면적으로 불가능하다고 볼 수는 없다.|정보접근·수집·처리의 자유가 법률이 제정되어 있지 않으면 실현 불가능하다고 한 부분
5|②|01|X|헌법상 검열금지는 행정권이 발표 전에 내용을 심사하고 허가받지 않은 발표를 금지하는 사전검열을 뜻하며, 발표 후 사법적 규제까지 금지하는 것은 아니다.|검열금지가 행정권의 사전허가 심사 금지만을 뜻하는 것이 아니라고 한 부분
5|③|01|X|옥외광고물과 게시시설의 설치장소 등에 관하여 허가나 신고를 요구하는 것이 그 자체로 과잉금지원칙에 어긋난다고 볼 수는 없다.|옥외광고물 허가·신고제가 과잉금지원칙에 어긋난다고 한 부분
5|④|01|X|구치소가 미결수용자의 신문열람에 관하여 구금목적상 부적당한 일부 기사를 제한하더라도 알권리의 본질적 내용을 침해한다고 단정할 수는 없다.|미결수용자 신문 일부 기사 삭제가 알권리의 본질적 내용을 침해한다고 한 부분
5|⑤|01|O|알권리의 핵심에는 국민이 정부에 대하여 일반적 정보공개를 구할 권리가 포함된다.|
6|①|01|O|집회 또는 시위의 주최자와 질서유지인은 특정한 사람이나 단체가 집회나 시위에 참가하는 것을 막을 수 있다.|
6|②|01|O|집회 또는 시위의 주최자는 다른 사람의 생명이나 신체에 위해를 끼칠 수 있는 철봉, 곤봉, 돌덩이 등의 기구를 휴대하거나 사용해서는 안 된다.|
6|③|01|O|집회·결사의 자유도 절대적 기본권은 아니므로 헌법 제37조 제2항에 근거한 법률상 제한을 받을 수 있다.|
6|④|01|X|국내주재 외교기관이나 각급 법원 인근 집회·시위 금지 규정이 입법목적 달성에 필요한 범위를 넘는 과도한 제한으로 언제나 위헌이라고 일반화할 수는 없다.|외교기관이나 각급 법원 인근 집회·시위 금지 규정이 모두 과도한 제한으로 위헌이라고 한 부분
6|⑤|01|O|농지개량조합을 공법인으로 보는 이상 결사의 자유가 보호하는 헌법상 단체로 볼 수 없다.|
7|①|01|X|태아 성별 고지를 전면적으로 금지하는 제도는 태아 생명보호와 성비 불균형 해소라는 목적만으로 곧바로 헌법에 합치된다고 볼 수 없다.|태아성별 고지 금지가 헌법에 합치한다고 단정한 부분
7|②|01|X|헌법재판소의 한정위헌 또는 한정합헌 결정에서 위헌적으로 배제되는 해석가능성이나 축소된 적용범위는 주문에 표시될 수 있다.|한정위헌 또는 한정합헌 결정의 판단을 주문에 기재할 수 없다고 한 부분
7|③|01|O|헌법불합치결정은 법질서의 혼란을 방지하기 위하여 효력상실을 잠정적으로 유보하는 변형결정이지만 그 본질은 위헌결정이다.|
7|④|01|X|헌법불합치결정에서 일정한 기한까지 법률 적용을 잠정적으로 중지하도록 정하는 것이 권력분립원칙상 전혀 불가능한 것은 아니다.|헌법불합치결정에서 잠정적 적용중지가 전혀 불가능하다고 한 부분
7|⑤|01|X|제청된 법률조항의 위헌성 때문에 당해 법률 전부를 시행할 수 없다고 인정되는 경우에는 법률 전부에 대하여 헌법불합치결정을 할 수 있다.|법률 전부에 대한 헌법불합치결정이 변형결정의 취지상 불가능하다고 한 부분
8|①|01|O|권리구제형 헌법소원은 그 사유가 있음을 안 날부터 90일 이내, 그 사유가 있은 날부터 1년 이내에 청구하여야 한다.|
8|②|01|O|법원이 헌법재판소가 위헌으로 결정한 법률을 적용하여 기본권을 침해한 경우에는 예외적으로 그 재판에 대한 헌법소원이 허용될 수 있다.|
8|③|01|O|공법인도 법률의 위헌여부심판 제청신청이 기각된 때에는 일정한 요건 아래 위헌심사형 헌법소원을 제기할 수 있다.|
8|④|01|O|전심절차로 권리구제 가능성이 거의 없거나 권리구제절차 허용 여부가 객관적으로 불확실하면 헌법소원의 보충성 예외가 인정될 수 있다.|
8|⑤|01|X|헌법소원심판청구를 지정재판부에서 각하하려면 재판관 과반수가 아니라 지정재판부 재판관 전원의 일치된 의견이 필요하다.|지정재판부가 재판관 과반수 의견으로 헌법소원심판청구를 각하한다고 한 부분
9|①|01|X|헌법 제126조의 사기업 경영에 대한 통제 또는 관리는 사기업 경영에 대한 국가의 감독·통제 체계를 뜻하고, 기업 소유권 보유주체의 변경까지 포함하는 것은 아니다.|사기업 경영 통제 또는 관리에 기업 소유권 보유주체 변경이 포함된다고 한 부분
9|②|01|O|공정거래위원회가 부당내부거래 사업자에게 매출액의 일정 범위 안에서 과징금을 부과하도록 하는 것은 이중처벌금지원칙에 위반되지 않는다.|
9|③|01|O|독과점규제의 목적이 경쟁 회복에 있다면 그 수단도 자유롭고 공정한 경쟁을 가능하게 하는 방법이어야 한다.|
9|④|01|O|경제적 기본권 제한을 정당화하는 공익은 헌법에 명시적으로 규정된 목표에만 한정되지 않는다.|
9|⑤|01|O|부동산 실권리자명의 등기에 관한 법률의 명의신탁 관련 규정은 질서유지 또는 공공복리를 위한 조항으로서 재산권보장의 본질을 침해한다고 볼 수 없다.|
10|①|01|O|대통령은 국가 안위에 관계되는 중대한 교전상태에서 국가보위를 위하여 긴급한 조치가 필요하고 국회 집회가 불가능할 때 법률의 효력을 가지는 명령을 발할 수 있다.|
10|②|01|X|영장제도, 언론·출판·집회·결사의 자유, 정부나 법원의 권한에 관한 특별조치는 경비계엄이 아니라 비상계엄이 선포된 때 법률이 정하는 바에 따라 가능하다.|경비계엄 선포 때 영장제도와 언론·출판·집회·결사의 자유 등에 특별조치를 할 수 있다고 한 부분
10|③|01|O|대통령은 중대한 재정·경제상 위기에서 긴급조치가 필요하고 국회 집회를 기다릴 여유가 없을 때 최소한의 재정·경제상 처분 또는 법률 효력의 명령을 할 수 있다.|
10|④|01|O|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|
10|⑤|01|O|국회가 재적의원 과반수의 찬성으로 계엄 해제를 요구하면 대통령은 이를 해제하여야 한다.|
11|①|01|O|조세법률주의는 조세의 종목과 세율뿐 아니라 납세의무자, 과세물건, 과세표준, 과세절차까지 법률로 정하여야 한다는 원칙이다.|
11|②|01|O|조세평등주의는 헌법상 평등원칙이 조세법 영역에서 구현된 것으로, 조세 부과와 징수가 납세자의 담세능력에 상응하여 공정하고 평등해야 함을 요구한다.|
11|③|01|O|조세법률주의에 따라 조세법률의 행정편의적 확장해석이나 유추해석은 허용되지 않는다.|
11|④|01|O|법률이 정한 범위 안에서 조례로 지방세 세목을 정하거나 조약으로 세율을 정하는 것이 곧바로 조세법률주의를 침해하는 것은 아니다.|
11|⑤|01|X|조세의 감면도 조세의 부과·징수와 밀접하게 관련되므로 조세법률주의의 적용 대상이 된다.|조세의 감면에는 조세법률주의가 적용되지 않는다고 한 부분
12|①|01|O|국무총리, 행정각부의 장, 헌법재판소 재판관, 법관, 감사위원에 대한 탄핵소추는 국회재적의원 3분의 1 이상의 발의와 과반수 찬성 의결로 이루어진다.|
12|②|01|O|탄핵심판에서는 국회 법제사법위원회의 위원장이 소추위원이 된다.|
12|③|01|O|탄핵소추 의결을 받은 사람은 탄핵심판이 있을 때까지 그 권한행사가 정지된다.|
12|④|01|X|피청구인이 결정 선고 전에 해당 공직에서 이미 파면된 때에는 탄핵심판에서 다시 그 공직 파면 결정을 선고할 수 없다.|결정 선고 전에 이미 파면된 피청구인에 대하여 다시 파면 결정을 선고하여야 한다고 한 부분
12|⑤|01|O|탄핵결정으로 파면된 사람은 결정 선고일부터 5년이 지나지 않으면 공무원이 될 수 없다.|
13|①|01|O|민법 제764조의 명예회복에 적당한 처분에 사죄광고를 포함시켜 법원이 이를 명하는 것은 양심의 자유를 침해한다고 판단되었다.|
13|②|01|X|국가보안법상 불고지죄는 양심의 자유를 침해하는 것으로 판단되지 않았다.|국가보안법상 불고지죄를 양심의 자유 침해로 본 부분
13|③|01|X|준법서약서 제도는 양심의 자유를 침해하는 것으로 판단되지 않았다.|준법서약서 제도를 양심의 자유 침해로 본 부분
13|④|01|X|2009년 출제 당시 양심적 병역거부를 이유로 한 병역의무 불이행 처벌은 양심의 자유 침해로 보지 않았다.|양심적 병역거부 처벌을 양심의 자유 침해로 본 부분
13|⑤|01|X|사립대학교에서 종교 관련 학점 이수를 졸업요건으로 정하는 것이 곧바로 종교의 자유 침해로 판단된 것은 아니다.|사립대학교의 종교학점 졸업요건을 종교의 자유 침해로 본 부분
14|①|01|O|형사보상청구권은 국가기관의 고의·과실을 요건으로 하지 않는다.|
14|①|02|X|형사보상에서 무죄판결을 받은 당사자에게 귀책사유가 있는지는 보상 여부나 범위에서 문제될 수 있다.|형사보상에서 무죄판결을 받은 당사자의 귀책사유도 문제되지 않는다고 한 부분
14|②|01|O|헌법 제28조의 정당한 보상은 일반적으로 형사보상청구권자가 입은 손실의 완전한 보상을 의미한다고 해석된다.|
14|③|01|X|2009년 출제 당시 형사보상법상 형사보상은 구금 등에 따른 손실보상을 중심으로 하므로 불구속 기소 후 무죄판결만으로 형사보상이 당연히 인정되는 것은 아니었다.|현행 형사보상법이 불구속 기소 후 무죄판결자에게도 형사보상을 인정한다고 한 부분
14|④|01|X|헌법 제28조는 형사보상청구권 자체를 보장하고 법률은 그 구체적 내용을 형성하므로, 이를 단순한 프로그램규정으로만 볼 수는 없다.|통설이 헌법 제28조를 프로그램규정으로 본다고 한 부분
14|⑤|01|X|면소 또는 공소기각 재판을 받은 사람도 법률이 정한 일정한 경우에는 형사보상청구권이 인정될 수 있다.|면소 또는 공소기각 재판을 받은 사람에게 형사보상청구권이 인정되지 않는다고 한 부분
15|①|01|X|미국 연방헌법은 국정조사권을 명문으로 규정하지 않지만, 의회의 권한행사를 위한 보조적 권한으로 국정조사권이 인정된다.|미국 연방헌법에 국정조사권 규정을 두고 있다고 한 부분
15|②|01|O|상임위원회는 국정감사뿐 아니라 국정조사도 행할 수 있다.|
15|③|01|O|국정감사 대상기관에는 상임위원회가 선정한 기관과 본회의가 승인한 기관이 포함되고, 국정조사 대상기관은 본회의가 승인한 기관으로 한정된다.|
15|④|01|O|수사 중인 사건이라도 탄핵소추나 해임건의를 위한 목적이면 국정조사의 대상이 될 수 있다.|
15|⑤|01|O|지방자치단체의 고유사무는 지방자치 보장의 취지상 국정감사 및 국정조사의 대상에서 제외된다고 보는 견해가 다수이다.|
16|①|01|O|입법부는 대법원장·대법관 임명동의권, 법원 예산 심의·확정권, 국정감사·조사권 등을 통하여 사법부를 견제할 수 있다.|
16|②|01|X|명령 또는 규칙의 위헌·위법 여부가 재판의 전제가 된 경우 대법원이 최종심사권을 가지지만, 명령·규칙에 대한 헌법소원이 언제나 배제되는 것은 아니다.|명령 또는 규칙의 위헌·위법 판단에 법원이 전속적 관할권을 가진다고 한 부분
16|③|01|O|대법원장과 대법관이 아닌 법관은 대법관회의의 동의를 얻어 대법원장이 임명한다.|
16|④|01|O|대법관의 임기는 6년이며 연임할 수 있다.|
16|⑤|01|O|법관에 대한 징계처분은 정직, 감봉, 견책의 세 종류이다.|
17|①|01|O|우리나라에서는 기본권의 대사인적 효력에 관하여 간접효력설이 다수설이지만, 일부 기본권에는 예외적으로 직접효력이 인정될 수 있다.|
17|②|01|X|평등권은 입법권도 구속하며, 입법자의 형성의 자유는 평등심사의 기준과 강도에 영향을 줄 뿐 입법권 구속력을 배제하지 않는다.|입법자의 형성의 자유 때문에 평등권의 입법권 구속력을 인정하지 않는다고 한 부분
17|③|01|O|국가의 관리작용과 국고작용 등 비권력작용에도 기본권의 효력이 미친다고 보는 것이 다수 견해이다.|
17|④|01|O|기본권의 제3자적 효력 문제는 사인이나 사적 단체에 의한 기본권 침해가 늘어나는 상황에서 사회적 약자를 보호하기 위하여 제기되었다.|
17|⑤|01|O|국가배상청구권과 형사보상청구권은 성질상 사인 간 관계에 적용될 수 없다.|
18|①|01|X|국무회의는 대통령, 국무총리와 15인 이상 30인 이하의 국무위원으로 구성된다.|국무회의 구성을 대통령과 국무위원만으로 연결한 부분
18|②|01|O|감사원은 감사원장을 포함한 5인 이상 11인 이하의 감사위원으로 구성된다.|
18|③|01|X|헌법재판소는 헌법재판소장을 포함한 9인의 재판관으로 구성된다.|헌법재판소가 헌법재판소장을 포함한 11인의 재판관으로 구성된다고 한 부분
18|④|01|X|중앙선거관리위원회는 9인의 위원으로 구성되고 위원장은 위원 중에서 호선한다.|중앙선거관리위원회가 위원장과 9인의 위원으로 구성된다고 한 부분
18|⑤|01|X|대법원은 대법원장과 13인의 대법관으로 구성된다.|대법원이 대법원장과 12인의 대법관으로 구성된다고 한 부분
19|①|01|O|국무총리 또는 국무위원의 해임건의는 국회재적의원 3분의 1 이상의 발의와 국회재적의원 과반수 찬성으로 한다.|
19|②|01|O|국회의원을 제명하려면 국회재적의원 3분의 2 이상의 찬성이 필요하고, 국회의원 징계 및 제명 처분에 대하여는 법원에 제소할 수 없다.|
19|③|01|O|정부는 회계연도마다 예산안을 편성하여 회계연도 개시 90일 전까지 국회에 제출하고, 국회는 회계연도 개시 30일 전까지 이를 의결하여야 한다.|
19|④|01|O|국회에서 의결된 법률안은 정부에 이송되고 대통령은 15일 이내에 이를 공포한다.|
19|⑤|01|X|대통령은 법률안에 이의가 있을 때 이의서를 붙여 법률안 전체를 환부하여 재의를 요구할 수 있을 뿐, 일부에 대하여 또는 수정하여 재의를 요구할 수 없다.|대통령이 법률안 일부에 대하여 또는 법률안을 수정하여 재의를 요구할 수 있다고 한 부분
20|①|01|O|국가는 법률이 정하는 바에 따라 재외국민을 보호할 의무를 진다.|
20|②|01|O|외국의 일정한 지역에 계속하여 90일 이상 거주할 의사를 가지고 체류하는 대한민국 국민은 재외국민등록법에 따라 등록하여야 한다.|
20|③|01|X|재외국민에게 인정되는 선거권은 대통령선거에만 한정되지 않고 법률이 정한 국회의원선거 등에도 미칠 수 있다.|재외국민 선거권이 오직 대통령선거에만 인정된다고 한 부분
20|④|01|O|재외국민이 재외선거를 하려면 법률이 정한 신청기간에 재외국민 등록과 별도로 재외공관을 직접 방문하여 재외선거인 등록신청을 하여야 한다.|
20|⑤|01|O|재외국민에게 한국어, 한국역사 및 한국문화 등을 교육하기 위하여 재외국민단체 등이 한글학교를 설립할 때에는 해당 지역 관할 재외공관의 장에게 등록하면 된다.|
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
        raise ValueError("cannot locate 2009 constitution section")
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
        qid = f"2009-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2009-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2009-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v015_2009_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2009-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
