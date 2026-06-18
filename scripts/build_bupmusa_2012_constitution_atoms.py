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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2012" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2012_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2012"
TEXT_DIR = PRIVATE_ROOT / "text" / "2012"
RAW_PDF_PATH = RAW_DIR / "2012_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2012_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2012_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2012_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2012_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2012_법무사_과목별_index.json"
INTEGRATED_PATH = PRIVATE_ROOT / "current" / "통합본" / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2012_bupmusa_1st"
YEAR = 2012
ROUND = 18
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
    {"title": "형사소송법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/형사소송법"},
    {"title": "감사원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/감사원법"},
    {"title": "법원조직법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/법원조직법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "정치자금법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정치자금법"},
    {"title": "2012 법무사 헌법 문제", "publisher": "공기출", "url": "https://0gichul.com/y2012/52652838"},
    {"title": "2012 법무사 전과목 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2012/98246"},
    {"title": "제18회 법무사 제1차 시험 확정정답 PDF", "publisher": "법원행정처", "url": "https://0gichul.com/?module=file&act=procFileDownload&file_srl=98251&sid=8b01fa36282c23b530f90cd530e7ffbd"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "①",
    3: "②",
    4: "①",
    5: "④",
    6: "⑤",
    7: "①",
    8: "⑤",
    9: "③",
    10: "②",
    11: "④",
    12: "④",
    13: "①",
    14: "④",
    15: "③",
    16: "④",
    17: "①",
    18: "④",
    19: "④",
    20: "②",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES.update({
    4: "single-best-true",
})

FALSE_LABELS = {
    1: {"②"},
    2: {"①"},
    3: {"②"},
    4: {"②", "③", "④", "⑤"},
    5: {"④"},
    6: {"⑤"},
    7: {"①"},
    8: {"⑤"},
    9: {"③"},
    10: {"②"},
    11: {"④"},
    12: {"④"},
    13: {"①"},
    14: {"④"},
    15: {"③"},
    16: {"④"},
    17: {"①"},
    18: {"④"},
    19: {"④"},
    20: {"②"},
}

TOPICS = {
    1: "변호인의 조력을 받을 권리",
    2: "헌법기관 임기",
    3: "청원권",
    4: "대통령과 행정부",
    5: "헌법소원 대상과 보충성",
    6: "재판청구권",
    7: "위임입법",
    8: "신뢰보호와 소급입법",
    9: "야간옥외집회 헌법불합치",
    10: "정당제도",
    11: "죄형법정주의 명확성",
    12: "직업의 자유",
    13: "재산권 보장",
    14: "선거소송",
    15: "개인정보 자기결정권",
    16: "국회의원 자격과 비례대표",
    17: "경제질서 조항",
    18: "법령 헌법소원 요건",
    19: "행복추구권과 일반적 행동자유권",
    20: "양심의 자유와 사전검열",
}

BASIS = {
    no: ("헌법+헌법재판소 결정례+대법원 판례", f"{topic} 관련 헌법 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    for no, topic in TOPICS.items()
}
BASIS.update({
    1: ("판례", "헌법 제12조 제4항 및 변호인의 조력을 받을 권리 결정례", "변호인의 충분한 조력을 받을 권리와 수사기록 열람·등사권의 헌법적 성격을 판례 기준으로 정리한다."),
    2: ("조문", "대한민국헌법 제98조, 제104조, 제111조, 제114조 및 감사원법", "헌법에 직접 정해진 헌법기관의 임기·중임·연임 사항과 법률 사항을 구별한다."),
    3: ("조문+판례", "대한민국헌법 제26조 및 청원권 결정례", "청원권의 내용, 결과통지의 효과, 청원 절차에 관한 입법형성권을 조문과 판례 기준으로 정리한다."),
    4: ("조문+판례", "대한민국헌법 제66조, 제84조, 제96조 및 사면 관련 판례", "대통령의 선거중립의무, 형사상 소추 특권, 법률안 제출과 사면 효과를 조문과 판례 기준으로 정리한다."),
    5: ("조문+판례", "헌법재판소법 제68조 및 헌법소원 보충성 결정례", "헌법소원의 대상성, 재판소원 금지, 보충성 원칙과 예외를 판례 기준으로 정리한다."),
    6: ("판례", "대한민국헌법 제27조 및 재판청구권 결정례", "재판상 화해 간주, 즉시항고기간, 필요적 전심, 사법보좌관, 치료감호청구권 문제를 판례 기준으로 정리한다."),
    7: ("조문+판례", "대한민국헌법 제75조 및 포괄위임금지원칙 결정례", "위임입법의 형식, 예측가능성, 명확성 심사 정도를 판례 기준으로 정리한다."),
    8: ("판례", "헌법 제13조 제2항 및 소급입법금지 결정례", "진정소급입법과 부진정소급입법, 신뢰보호원칙의 형량 기준과 예외를 판례 기준으로 정리한다."),
    9: ("판례", "헌법재판소 2008헌가25 등 야간옥외집회 결정례", "야간옥외집회 금지 조항의 허가제성, 집회의 자유, 종전 합헌결정과 헌법불합치 결론을 판례 기준으로 정리한다."),
    10: ("조문+판례", "대한민국헌법 제8조, 정당법, 정치자금법 및 정당 관련 판례", "정당해산제도, 정당의 법적 지위, 국고보조금 용도를 조문과 판례 기준으로 정리한다."),
    11: ("판례", "대한민국헌법 제12조, 제13조 및 죄형법정주의 명확성 결정례", "명확성원칙의 의미, 처벌법규의 해석가능성, 인용입법의 허용 범위를 판례 기준으로 정리한다."),
    12: ("판례", "직업의 자유 관련 헌법재판소 결정례", "법무사 보수규제, 학원 교습시간, 개인택시, 복수면허 의료기관, 이륜자동차 통행금지를 판례 기준으로 정리한다."),
    13: ("조문+판례", "대한민국헌법 제23조 및 재산권 보장 결정례", "재산권의 보호범위, 법률유보, 재산권 형성입법과 공법상 지위의 보호요건을 판례 기준으로 정리한다."),
    14: ("조문+판례", "공직선거법 선거소송 규정 및 선거쟁송 판례", "선거무효소송과 당선무효소송, 소송 당사자와 선거결과 영향 요건을 조문과 판례 기준으로 정리한다."),
    15: ("판례", "개인정보 자기결정권 관련 헌법재판소 결정례", "개인정보 자기결정권의 의의, 보호대상, 제한행위와 과잉금지 심사를 판례 기준으로 정리한다."),
    16: ("조문+판례", "대한민국헌법 제64조, 국회법 제142조 및 공직선거법", "국회의원 자격상실, 제명, 비례대표 의석승계와 퇴직 사유를 조문과 판례 기준으로 정리한다."),
    17: ("조문", "대한민국헌법 제120조, 제121조, 제123조, 제124조, 제125조", "헌법 경제질서 조항에 명문으로 규정된 내용과 규정되지 않은 내용을 구별한다."),
    18: ("판례", "헌법재판소법 제68조 및 법령소원 자기관련성 결정례", "법령소원의 직접성·현재성·자기관련성과 수혜적 법령의 제3자 자기관련성을 판례 기준으로 정리한다."),
    19: ("판례", "행복추구권 및 일반적 행동자유권 관련 헌법재판소 결정례", "수용자 건강보험, 청소년 출입금지표시, 이륜자동차 통행금지, 대마 사용, 수질부담금 관련 판단을 판례 기준으로 정리한다."),
    20: ("판례", "양심의 자유, 개인정보 자기결정권 및 사전검열 결정례", "납본제도, 인터넷 게시글 실명확인, 방송광고 사전심의, 음주측정거부 면허취소를 판례 기준으로 정리한다."),
})

ATOM_ROWS = """
1|①|01|O|헌법상 변호인의 조력을 받을 권리는 변호인의 충분한 조력을 받을 권리를 의미하고, 일정한 경우 국가는 국선변호인의 실질적 조력이 이루어지도록 필요한 절차적 조치를 취하여야 한다.|
1|②|01|X|국선변호인이 법정기간 내 항소이유서를 제출하지 않아 피고인의 항소가 기각되도록 방치되는 것은 변호인의 충분한 조력을 받을 권리를 보장하여야 할 국가의 의무에 반할 수 있다.|국선변호인의 항소이유서 미제출로 항소가 기각되어도 헌법 취지에 반하지 않는다고 한 부분
1|③|01|O|변호인의 조력을 받을 권리에는 피고인이 변호인을 통하여 수사서류를 포함한 소송관계서류를 열람·등사하고 방어를 준비할 수 있는 권리가 포함된다.|
1|④|01|O|변호인의 수사서류 열람·등사권은 피고인의 신속·공정한 재판을 받을 권리와 변호인의 조력을 받을 권리를 실현하는 구체적 수단이다.|
1|⑤|01|O|변호인의 수사서류 열람·등사권이 헌법상 기본권의 구성요소이더라도 그 절차, 대상, 제한사유, 불복절차 등 구체적 내용은 입법으로 형성될 수 있다.|
2|①|01|X|헌법은 감사위원의 임기와 연임 가능 여부를 직접 규정하지 않고, 감사위원의 임기와 연임은 법률로 정한다.|감사위원의 임기 4년과 연임 가능성이 헌법에서 정한 내용이라고 한 부분
2|②|01|O|대법원장의 임기는 6년이고 중임할 수 없다.|
2|③|01|O|대법관의 임기는 6년이고 법률이 정하는 바에 따라 연임할 수 있다.|
2|④|01|O|헌법재판소 재판관의 임기는 6년이고 법률이 정하는 바에 따라 연임할 수 있다.|
2|⑤|01|O|중앙선거관리위원회 위원의 임기는 6년이다.|
3|①|01|O|청원권은 적법한 청원을 한 국민이 국가기관에 청원의 수리·심사와 그 결과의 통지를 요구할 수 있는 권리이다.|
3|②|01|X|국가기관이 청원을 수리·심사하여 그 결과를 통지하였다면 그 결과가 청원인의 기대에 미치지 못하더라도 헌법소원 대상인 공권력의 불행사가 아니다.|청원 결과가 기대에 미치지 못하면 공권력 불행사에 해당한다고 한 부분
3|③|01|O|청원권은 국민이 이해관계나 국정에 관한 의견·희망을 해당 기관에 직접 진술하거나 본인을 대리·중개하는 제3자를 통하여 진술하는 것을 보호할 수 있다.|
3|④|01|O|공무원이 취급하는 사건 또는 사무에 관하여 청탁한다는 명목으로 금품을 받는 행위를 처벌하는 규정은 일반적 행동자유권과 청원권을 제한한다.|
3|⑤|01|O|청원사항, 청원방식, 청원절차 및 금품수수 청탁행위를 청원권의 내용으로 보장할지에 관하여 입법자는 폭넓은 형성재량을 가진다.|
4|①|01|O|대통령의 정치활동의 자유와 공무원의 선거중립을 통한 공정선거 요청이 충돌하는 경우 대통령의 선거중립의무가 우선될 수 있다.|
4|②|01|X|대통령은 재직 중 내란 또는 외환의 죄를 제외하고 형사상 소추를 받지 않으므로 재직 중 공소시효 진행은 정지된다고 볼 수 있다.|대통령 재직 중 공소시효가 당연히 정지되는 것으로 보기 어렵다고 한 부분
4|③|01|X|대통령의 법률안 제출은 국가기관 사이의 내부적 행위로서 그 자체만으로 국민에게 직접 법률효과를 발생시키지 않는다.|대통령의 법률안 제출행위가 국민에게 직접 법률효과를 발생시킨다고 한 부분
4|④|01|X|징역형의 집행유예와 벌금형이 병과된 상태에서 징역형 선고효력을 상실시키는 특별사면이 있더라도 병과된 벌금형에는 당연히 사면의 효력이 미치지 않는다.|징역형에 대한 특별사면의 효력이 병과된 벌금형에도 미친다고 한 부분
4|⑤|01|X|법률로 국무총리의 통할을 받지 않는 대통령직속기관의 설치근거와 직무범위를 정하는 것이 그 사정만으로 헌법에 위반되는 것은 아니다.|국무총리 통할을 받지 않는 대통령직속기관 설치근거와 직무범위를 법률로 정하면 헌법에 위반된다고 한 부분
5|①|01|O|형사재판이 확정된 후 제1심 공판정 심리 녹음물을 폐기한 행위는 법원행정상의 구체적 사실행위에 불과하여 헌법소원 대상인 공권력 행사로 볼 수 없다.|
5|②|01|O|진정에 대한 공람종결처분은 구속력이 없는 진정사건의 내부적 처리방식에 불과하여 헌법소원 대상인 공권력 행사라고 할 수 없다.|
5|③|01|O|도시계획시설결정은 행정처분에 해당하므로 행정심판 또는 항고소송 절차를 거치지 않은 헌법소원은 원칙적으로 보충성 요건을 갖추지 못한다.|
5|④|01|X|동행계호행위가 권력적 사실행위로서 행정처분으로 볼 수 있더라도, 헌법소원 외에 효과적인 구제방법을 기대하기 어려우면 보충성 원칙의 예외가 인정될 수 있다.|동행계호행위에 대한 헌법소원이 보충성 요건을 갖추지 못하고 보충성 예외도 아니라고 한 부분
5|⑤|01|O|법원의 재판에 대한 헌법소원은 원칙적으로 허용되지 않지만, 헌법재판소가 위헌으로 결정한 법령을 적용하여 국민의 기본권을 침해한 재판은 예외적으로 헌법소원 대상이 될 수 있다.|
6|①|01|O|특수임무수행자 보상금 등의 지급결정에 동의하면 재판상 화해가 성립된 것으로 보는 규정은 재판청구권을 침해하지 않는다고 판단되었다.|
6|②|01|O|형사소송법이 즉시항고 제기기간을 민사재판보다 짧은 3일로 정한 것은 재판청구권을 침해하지 않는다고 판단되었다.|
6|③|01|O|교원 징계처분에 관하여 재심청구를 거치지 않고는 행정소송을 제기할 수 없도록 한 규정은 재판청구권을 침해하지 않는다고 판단되었다.|
6|④|01|O|사법보좌관의 소송비용액확정재판에 대하여 동일 심급 안에서 법관의 재판을 다시 받을 수 있으면 재판청구권 침해가 아니라고 판단되었다.|
6|⑤|01|X|피고인이 스스로 치료감호를 청구할 수 있는 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|피고인의 치료감호청구권이 헌법상 재판청구권의 보호범위에 포함된다고 한 부분
7|①|01|X|법률이 전문적·기술적 사항을 고시 등 행정규칙 형식에 위임하였다는 사정만으로 곧바로 헌법에 위반되는 것은 아니다.|법규적 사항을 고시에 위임하면 헌법에 위반된다고 한 부분
7|②|01|O|헌법 제75조의 구체적 위임은 법률에 대통령령으로 규정될 내용과 범위의 기본사항이 규정되어 수범자가 대통령령의 대강을 예측할 수 있어야 한다는 뜻이다.|
7|③|01|O|현대 행정입법 허용의 배경에는 입법수요의 급증과 기능적 권력분립론에 따른 행정입법 필요성이 있다.|
7|④|01|O|모의총포 제조·판매·소지를 금지하면서 대통령령에 구체적 대상을 위임한 규정은 총포와 유사하여 범죄악용이나 위해 가능성이 있는 물건임을 예측할 수 있으면 포괄위임금지원칙에 위배되지 않는다.|
7|⑤|01|O|포괄위임금지원칙에서 요구되는 위임의 명확성 정도는 규율 대상 사실관계의 특성에 따라 달라질 수 있다.|
8|①|01|O|신뢰보호원칙은 기존 법질서에 대한 합리적 신뢰와 새 입법의 공익 목적을 형량하여 신뢰 파괴가 정당화될 수 없는 경우 새 입법을 제한하는 법치국가 원리이다.|
8|②|01|O|신뢰보호원칙 위반 여부는 침해되는 이익의 보호가치, 침해 정도, 신뢰 손상 정도, 신뢰침해 방법과 새 입법의 공익 목적을 종합적으로 형량하여 판단한다.|
8|③|01|O|이미 완성된 과거 사실관계나 법률관계를 규율하는 입법은 진정소급효 입법이고, 진행 중인 사실관계나 법률관계를 규율하는 입법은 부진정소급효 입법이다.|
8|④|01|O|헌법 제13조 제2항이 금지하는 소급입법은 진정소급효를 가지는 법률을 의미하고, 부진정소급효 입법은 원칙적으로 허용된다.|
8|⑤|01|X|국민이 소급입법을 예상할 수 있었던 경우 등 특별한 사정이 있으면 진정소급입법도 예외적으로 허용될 수 있다.|소급입법 예상가능성만으로는 진정소급입법이 정당화될 수 없다고 한 부분
9|①|01|O|야간옥외집회 일반금지와 관할 경찰서장의 예외적 허용을 규정한 조항은 집회에 대한 허가제에 해당하여 위헌이라는 것이 위헌의견의 주된 논거였다.|
9|②|01|O|집회의 자유는 국민이 집단적으로 의견과 주장을 표명하여 여론 형성에 영향을 미치게 하는 자유로서 표현의 자유와 함께 민주적 공동체에 필수적인 기본권이다.|
9|③|01|X|헌법재판소의 종전 야간옥외집회 금지 조항 합헌결정은 재판관 전원일치가 아니라 다수 합헌의견과 일부 반대의견으로 이루어졌다.|종전 합헌결정이 재판관 전원일치였다고 한 부분
9|④|01|O|야간옥외집회 금지 조항 합헌의견은 외국 입법례와 일몰 후 옥외집회 시간규제의 정당성을 인정한 미국 판례 등을 논거로 들었다.|
9|⑤|01|O|헌법재판소는 야간옥외집회 금지 조항 사건에서 위헌의견 5명, 헌법불합치의견 2명, 합헌의견 2명의 의견분포를 전제로 헌법불합치와 잠정적용을 선고하였다.|
10|①|01|O|우리 헌법사에서 정당해산심판제도는 1960년 6월헌법에서 처음 채택되었다.|
10|①|02|O|진보당 사건 당시에는 정당해산심판제도가 없어 정부의 등록취소로 정당이 해체되었다.|
10|②|01|X|정당은 소유재산 귀속관계에서 법인격 없는 사단으로 볼 수 있고, 판례는 정당의 지구당도 법인격 없는 사단에 해당한다고 보았다.|정당 지구당은 법인격 없는 사단에 해당하지 않는다고 한 부분
10|③|01|O|헌법은 법률이 정하는 바에 따라 국가가 정당운영에 필요한 자금을 보조할 수 있다고 규정한다.|
10|③|02|O|정당 국고보조금은 법률이 정한 정당운영 경비와 선거관계비용 등 용도에 사용하여야 한다.|
10|④|01|O|기본권의 성질상 정당도 일정한 경우 기본권의 주체가 될 수 있다.|
10|⑤|01|O|정당 국고보조금제도는 이익집단의 부당한 영향력을 줄여 정치부패를 방지하고 정당 간 자금조달 격차를 완화하여 공평한 경쟁을 유도하려는 목적을 가진다.|
11|①|01|O|명확성원칙은 수범자가 규범의 의미내용에서 금지·허용 행위를 알 수 있어야 법적 안정성과 예측가능성이 확보된다는 법치국가 원리의 표현이다.|
11|②|01|O|처벌법규의 명확성은 통상의 해석방법으로 보호법익, 금지행위, 처벌의 종류와 정도를 알 수 있으면 충족될 수 있다.|
11|③|01|O|처벌법규의 구성요건이 다소 광범위하여 법관의 보충적 해석이 필요한 개념을 사용하였다는 사정만으로 명확성원칙에 배치되는 것은 아니다.|
11|④|01|X|처벌법규가 구성요건이 되는 행위를 같은 조항에서 직접 규정하지 않고 다른 법률조항의 내용을 원용하였다는 사정만으로 곧바로 명확성원칙에 위반되는 것은 아니다.|처벌법규가 다른 법률조항의 내용을 원용하면 불명확하다고 한 부분
11|⑤|01|O|처벌법규의 입법목적, 전체 내용과 구조를 통하여 일반인의 이해와 판단으로 행위유형을 정형화하거나 한정할 합리적 해석기준을 찾을 수 있으면 명확성원칙에 위반되지 않는다.|
12|①|01|O|법무사 보수를 대한법무사협회 회칙에 정하게 하고 초과보수나 명목 여하를 불문한 금품수수를 금지한 법무사법 규정은 헌법에 위반되지 않는다고 판단되었다.|
12|②|01|O|학교교과교습학원의 교습시간을 05시부터 22시까지로 정한 조례는 학생·부모의 자유, 자녀교육권, 직업의 자유, 평등권을 침해하지 않는다고 판단되었다.|
12|③|01|O|개인택시운송사업자의 운전면허가 취소된 경우 개인택시운송사업면허를 취소할 수 있도록 한 규정은 직업의 자유와 재산권을 침해하지 않는다고 판단되었다.|
12|④|01|X|의사와 한의사 복수면허를 가진 의료인에게도 하나의 의료기관만 개설하게 하고 다른 의료기관 개설을 금지한 규정은 직업의 자유를 침해한다고 판단되었다.|복수면허 의료인의 복수 의료기관 개설금지가 직업의 자유를 침해하지 않는다고 한 부분
12|⑤|01|O|이륜자동차의 고속도로 통행금지로 퀵서비스 배달업 수행에 지장이 생기더라도 이는 간접적·사실상 효과에 그쳐 직업수행의 자유를 침해하지 않는다고 판단되었다.|
13|①|01|X|헌법상 재산권은 사법상 재산권과 특별한 희생을 통하여 얻은 공법상 권리를 포함할 수 있지만, 국가의 일방적 급부를 받을 지위가 항상 재산권에 포함되는 것은 아니다.|국가로부터 일방적 급부를 받는 경우도 재산권에 포함된다고 한 부분
13|②|01|O|헌법 제23조는 재산권 보장을 선언하면서 그 내용과 한계는 법률로 정한다고 규정하여 재산권의 구체적 내용이 법률에 의해 형성되도록 한다.|
13|③|01|O|헌법상 재산권의 내용과 한계를 정하는 법률은 재산권을 단순히 제한하는 것이 아니라 재산권의 내용을 형성하는 의미를 가진다.|
13|④|01|O|재산권의 내용과 한계를 형성할 때 입법자는 광범위한 입법형성권을 가지지만 본질적 내용 침해 금지와 사회적 기속성에 따른 한계를 준수하여야 한다.|
13|⑤|01|O|공법상 재산적 가치 있는 지위가 헌법상 재산권으로 보호되려면 법률에 의하여 구체적 권리로 형성되어 개인의 주관적 공권 형태를 갖추어야 한다.|
14|①|01|O|선거무효소송은 선거일 지정, 선거인명부 작성, 후보자등록, 투표·개표관리 등 선거라는 집합적 행위의 효력을 다투는 쟁송이다.|
14|②|01|O|당선무효소송은 선거가 적법·유효하게 실시된 것을 전제로 당선인 결정 자체의 위법을 다투므로 선거무효사유가 있으면 따로 당선무효 여부를 판단할 필요가 없다.|
14|③|01|O|개표참관인이 시정요구 거부 등을 이유로 스스로 퇴장한 경우에는 참관업무를 포기한 것으로 보아 선거무효사유가 되지 않을 수 있다.|
14|④|01|X|국회의원 지역구 선거의 효력에 이의가 있는 선거인·후보자 추천 정당 또는 후보자는 관할 선거구선거관리위원회 위원장을 피고로 하여 대법원에 소를 제기한다.|국회의원 지역구 선거소송의 피고를 중앙선거관리위원회 위원장이라고 한 부분
14|⑤|01|O|선거쟁송에서는 선거에 관한 규정 위반이 있더라도 그 위반이 선거 결과에 영향을 미쳤다고 인정될 때에 한하여 선거나 당선의 무효를 결정한다.|
15|①|01|O|개인정보 자기결정권은 자기 정보가 언제, 누구에게, 어느 범위까지 알려지고 이용되도록 할 것인지 정보주체가 스스로 결정할 수 있는 권리이다.|
15|②|01|O|개인정보 자기결정권의 보호대상인 개인정보는 개인의 동일성을 식별할 수 있게 하는 정보이다.|
15|③|01|X|개인정보 자기결정권의 보호대상에는 공적 생활에서 형성되었거나 이미 공개된 개인정보도 포함될 수 있다.|공적 생활에서 형성되었거나 이미 공개된 개인정보는 보호대상이 아니라고 한 부분
15|④|01|O|개인정보의 조사, 수집, 보관, 처리, 이용 행위는 원칙적으로 개인정보 자기결정권에 대한 제한에 해당한다.|
15|⑤|01|O|채무불이행자명부나 그 부본을 누구든지 보거나 복사할 수 있도록 한 것은 과잉금지원칙에 반하여 개인정보 자기결정권을 침해한다고 볼 수 없다고 판단되었다.|
16|①|01|O|비례대표국회의원 의석을 배분받으려면 정당은 정당투표에서 유효투표총수의 100분의 3 이상을 득표하거나 지역구국회의원 총선거에서 5석 이상의 의석을 차지하여야 한다.|
16|②|01|O|비례대표국회의원 당선자가 선거범죄로 당선무효되어 궐원이 발생한 경우 의석 승계를 금지하는 것은 대의민주주의 원리와 자기책임원리에 반하고 차순위 후보자의 공무담임권을 침해한다고 판단되었다.|
16|③|01|O|징계로 제명된 국회의원은 국회의원의 자격을 상실하고, 그 궐원으로 인한 보궐선거에서 후보자가 될 수 없다.|
16|④|01|X|국회의원 자격심사에서 본회의가 해당 의원의 자격이 없다고 의결하려면 재적의원 3분의 2 이상의 찬성이 필요하다.|국회의원 자격상실 의결에 재적의원 과반수 찬성만 있으면 된다고 한 부분
16|⑤|01|O|비례대표국회의원이 소속 정당의 합당·해산 또는 제명 외의 사유로 당적을 이탈·변경하거나 둘 이상의 당적을 가지면 퇴직된다.|
17|①|01|X|농지의 소작제도는 금지되고, 농업생산성 제고와 농지의 합리적 이용 또는 불가피한 사정으로 발생하는 농지의 임대차와 위탁경영은 법률이 정하는 바에 따라 인정된다.|농지의 소작제도가 헌법상 인정된다고 한 부분
17|②|01|O|광물 기타 중요한 지하자원, 수산자원, 수력과 경제상 이용할 수 있는 자연력은 법률이 정하는 바에 따라 일정 기간 채취·개발 또는 이용을 특허할 수 있다.|
17|③|01|O|국가는 균형 있는 국민경제의 성장과 안정, 적정한 소득분배, 시장지배와 경제력 남용 방지, 경제민주화를 위하여 경제에 관한 규제와 조정을 할 수 있다.|
17|④|01|O|국가는 건전한 소비행위를 계도하고 생산품의 품질향상을 촉구하기 위한 소비자보호운동을 법률이 정하는 바에 따라 보장한다.|
17|⑤|01|O|국가는 대외무역을 육성하고 이를 규제·조정할 수 있다.|
18|①|01|O|법률 또는 법률조항 자체가 헌법소원 대상이 되려면 원칙적으로 구체적 집행행위 없이 직접, 현재, 자기의 기본권 침해가 있어야 한다.|
18|②|01|O|침해적 법령의 경우에는 일반적으로 법령의 수규자가 당사자로서 자신의 기본권 침해를 주장하게 된다.|
18|③|01|O|수혜적 법령에서 수혜범위 제외자가 자신이 평등원칙에 반하여 제외되었다고 주장하면 자기관련성이 인정될 수 있다.|
18|④|01|X|청구인이 법령의 직접적인 수규자가 아니더라도 그 법령으로 자신의 기본권을 직접·현재 침해받는 법적 관련성이 있으면 자기관련성이 인정될 수 있다.|법령의 직접 적용을 받는 자가 아니면 언제나 자기관련성이 인정되지 않는다고 한 부분
18|⑤|01|O|헌법소원심판은 개인의 주관적 권리구제 기능뿐 아니라 객관적 헌법질서의 수호·유지 기능도 가진다.|
19|①|01|O|교도소 수용 중 국민건강보험급여를 정지하도록 한 조항은 수용자의 인간의 존엄성과 행복추구권을 침해하지 않는다고 판단되었다.|
19|②|01|O|당구장 출입문에 18세 미만자 출입금지표시를 하게 하는 규정은 출입이 제지되는 18세 미만자의 일반적 행동자유권을 제한할 수 있다.|
19|③|01|O|긴급자동차를 제외한 이륜자동차와 원동기장치자전거의 고속도로 또는 자동차전용도로 통행을 금지한 규정은 일반적 행동자유권을 침해하지 않는다고 판단되었다.|
19|④|01|X|일반적 행동자유권은 가치 있는 행동뿐 아니라 개인의 생활영역에서 자유롭게 행위할 일반적 자유를 넓게 보호영역으로 한다.|일반적 행동자유권이 가치 있는 행동만 보호영역으로 한다고 한 부분
19|⑤|01|O|수질부담금의 부과가 마실 물을 자유롭게 선택할 수 있는 국민의 행복추구권을 침해하는 것은 아니라고 판단되었다.|
20|①|01|O|정기간행물의 납본제도가 그 내용을 심사하여 공개나 배포를 허가·금지하는 제도가 아니라면 사전검열에 해당하지 않는다.|
20|②|01|X|인터넷언론사의 공개 게시판이나 대화방에 정당·후보자에 대한 지지·반대 글을 게시하는 행위가 곧바로 양심의 자유나 사생활 비밀의 자유로 보호되는 것은 아니다.|공개 게시판의 정당·후보자 지지·반대 글 게시가 양심의 자유나 사생활 비밀의 자유로 보호된다고 한 부분
20|③|01|O|실명인증자료의 보관 및 제출의무가 개인의 인적정보 수집 목적의 조항이 아니라면 개인정보 자기결정권 제한으로 보기 어렵다.|
20|④|01|O|민간기구 형식을 취하더라도 행정권이 개입하는 텔레비전 방송광고 사전심의는 행정기관에 의한 사전검열로서 헌법상 금지되는 사전검열에 해당할 수 있다.|
20|⑤|01|O|음주측정거부자에게 운전면허 필요적 취소를 규정한 것은 양심의 자유나 행복추구권 등을 침해하지 않는다고 판단되었다.|
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
        raise ValueError("cannot locate 2012 constitution section")
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
        qid = f"2012-g1-constitution-{no:02d}"
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
            items.append({"atomId": f"bupmusa-2012-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}", "sourceUnitId": item["unitId"], "sourceAtomIndex": row["atomIndex"], "sourceFamily": "법무사시험", "source": item["source"], "year": YEAR, "round": ROUND, "subject": SUBJECT_NAME, "no": item["no"], "unitType": item["unitType"], "unitLabel": item["unitLabel"], "sourceQuestionType": item["sourceQuestionType"], "officialQuestionAnswer": item["officialQuestionAnswer"], "sourceUnitVerdict": item["originalVerdict"], "sourceVerdict": row["sourceVerdict"], "currentVerdict": "O", "rep": rep, "a": "O", "basisType": basis_type, "basisRef": basis_ref, "why": why, "sourceStatement": item["rawStatement"], "sourceTrap": row["trap"], "xDependsOn": rep if source_is_x else None, "reviewedAt": today(), "currentLawCheckedAt": today()})
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
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2012-constitution-")]
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
    return {"title": "법무사_헌법 통합 atom", "subject": SUBJECT_NAME, "schema": "bupmusa/constitution-integrated-atom/v1", "version": "bupmusa_constitution_v014_2012_integrated", "builtAt": today(), "sourceFiles": {str(year): str(current_dir / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years}, "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"}, "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"}, "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))}, "items": items}


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
    false_units = {f"2012-g1-constitution-{no:02d}-{LABEL_CODE[label]}" for no, labels in FALSE_LABELS.items() for label in labels}
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
