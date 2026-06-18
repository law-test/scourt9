from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2024" / "과목별"
RAW_TEXT_PATH = PRIVATE_ROOT / "text" / "2024" / "2024_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_부동산등기법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_부동산등기법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_부동산등기법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "부동산등기법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 4
QUESTION_COUNT = 30
EXPECTED_ATOM_COUNT = 150

LEGAL_SOURCES = [
    {"title": "부동산등기법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/부동산등기법"},
    {"title": "부동산등기규칙", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/부동산등기규칙"},
    {"title": "도시 및 주거환경정비법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/도시 및 주거환경정비법"},
    {"title": "채무자 회생 및 파산에 관한 법률", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/채무자 회생 및 파산에 관한 법률"},
    {"title": "2024 법무사 부동산등기법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881308"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "③",
    3: "③",
    4: "④",
    5: "④",
    6: "②",
    7: "③",
    8: "①,④",
    9: "⑤",
    10: "④",
    11: "④",
    12: "④",
    13: "④",
    14: "②",
    15: "②",
    16: "④",
    17: "④",
    18: "③",
    19: "④",
    20: "③",
    21: "①",
    22: "④",
    23: "⑤",
    24: "⑤",
    25: "③",
    26: "②",
    27: "④",
    28: "⑤",
    29: "④",
    30: "②",
}

QUESTION_TYPES = {
    3: "single-best-true",
    7: "single-best-true",
    11: "multi-select-true",
    15: "count-true",
    17: "single-best-true",
    18: "count-true",
    30: "single-best-true",
}

BASIS = {
    1: ("본인서명사실확인서+등기예규", "본인서명사실확인 등에 관한 법률 및 본인서명사실확인서 첨부 등기신청 심사 예규", "본인서명사실확인서의 서명, 위임받은 사람, 용도 기재와 등기신청서의 부합 여부를 판단한다."),
    2: ("채무자회생법+등기예규", "채무자 회생 및 파산에 관한 법률, 회생절차 관련 등기예규·선례", "보전처분등기, 부인등기, 회생계획에 따른 처분과 회생절차 종결등기의 수리 여부를 판단한다."),
    3: ("민법+법무사법+등기선례", "민법 제921조, 법무사법 제3조, 대리 등기신청 관련 판례·선례", "대리인에 의한 등기신청에서 특별대리인, 법무사 업무범위, 쌍방위임의 효과를 판단한다."),
    4: ("토지보상법+등기예규", "공익사업을 위한 토지 등의 취득 및 보상에 관한 법률, 수용등기 예규·선례", "협의취득, 수용, 환매특약 말소, 수용등기 촉탁과 첨부정보를 판단한다."),
    5: ("민법+등기예규", "민법 제245조, 시효취득으로 인한 소유권이전등기 예규·선례", "시효취득 이전등기의 신청구조, 농지취득자격증명, 미등기토지 보존등기와 부담등기 말소를 판단한다."),
    6: ("부동산등기법+등기규칙", "부동산등기법상 건물 표시변경·합병·멸실등기 규정과 선례", "건물 합병 제한, 멸실등기 대위신청, 제3자 권리의 승낙 필요 여부를 판단한다."),
    7: ("도시정비법+등기예규", "도시 및 주거환경정비법상 이전고시와 정비사업 등기처리 예규", "이전고시에 따른 등기신청, 대위등기, 권리등기 제한과 담보권 이전등기의 처리방식을 판단한다."),
    8: ("민법+특별법+등기선례", "민법 제289조의2, 도시철도법, 전원개발촉진법, 구분지상권 등기선례", "구분지상권 설정등기의 승낙서, 직권말소, 단독신청 가능성과 특약 등기를 판단한다."),
    9: ("민법+등기예규", "민법상 공유물분할 및 공유물분할등기 예규·선례", "공유물분할에 따른 분필, 지분이전, 부담등기 전사와 등기필정보 제공을 판단한다."),
    10: ("부동산등기법+판례", "부동산등기법상 등기의 효력 및 실체관계 부합 등기 판례", "등기의 유효성, 환지처분, 구분건물 등기와 가처분등기의 효력을 판단한다."),
    11: ("등기예규", "재외국민의 상속재산분할협의와 상속등기 관련 등기예규", "재외국민이 대리인에게 상속재산분할협의를 위임한 경우 위임장, 공증, 인감증명과 원인증서를 판단한다."),
    12: ("민법+등기예규", "소유권보존·말소·포기·유류분반환 관련 등기예규·선례", "특정 일부 토지의 말소, 유류분반환, 공유자 보존등기, 소유권 포기와 상속재산분할 경정을 판단한다."),
    13: ("부동산등기법+민법", "부동산등기법 제28조, 채권자대위등기 예규·판례", "채권자대위 등기신청의 요건, 대위말소 가능성, 완료통지와 등기필정보 작성 여부를 판단한다."),
    14: ("부동산등기법+등기규칙", "부동산등기법 제25조, 부동산등기규칙의 일괄신청 및 첨부정보 원용 규정", "동시신청, 일괄신청, 신탁등기와 공동근저당의 신청구조를 판단한다."),
    15: ("부동산등기법", "부동산등기법상 주등기와 부기등기 규정", "소유권 외 권리의 권리등기, 처분제한, 변경등기, 신탁등기와 본등기의 주등기·부기등기 여부를 판단한다."),
    16: ("부동산등기법+등기예규", "재외국민 부동산등기용등록번호 부여절차 예규", "주민등록번호 없는 재외국민의 부동산등기용등록번호 부여기관, 첨부서면, 보존기간과 통지를 판단한다."),
    17: ("민법+등기예규", "근저당권이전등기와 피담보채권 양도·대위변제 관련 등기예규·선례", "근저당권 확정 전후의 이전원인, 채무자 승낙서와 대위변제 첨부정보를 판단한다."),
    18: ("부동산등기법+등기예규", "공동신청·단독신청·촉탁신청 및 말소회복등기 관련 예규·선례", "가압류말소, 경정등기, 보존등기, 말소회복등기를 공동신청할 수 있는지를 판단한다."),
    19: ("부동산등기규칙+예규", "부동산등기규칙상 접수절차와 출입사무원 제도 예규", "전자신청과 방문신청의 접수시점, 접수번호, 출입사무원 표시와 허가취소 사유를 판단한다."),
    20: ("부동산등기법+등기예규", "관공서 촉탁등기와 첨부정보 관련 등기예규·선례", "관공서 촉탁기관, 등기필정보, 주소증명정보와 인감증명 제출 필요성을 판단한다."),
    21: ("부동산등기법+등기규칙", "부동산등기법상 등기필정보 작성·통지·실효·재사용 규정", "등기필정보의 재발급 가능성, 통지방법, 비밀번호 사용과 변경등기 후 제공정보를 판단한다."),
    22: ("민법+등기예규", "민법 제368조 제2항, 공동저당 대위등기 예규", "공동저당 대위등기의 부기등기 형식, 원인일자, 신청인, 첨부정보와 국민주택채권을 판단한다."),
    23: ("민법+등기예규", "민법상 지역권 및 지역권설정등기 예규·선례", "승역지 관할, 등기권리자, 말소동의, 등록면허세와 대지권 토지의 지역권 설정 가능성을 판단한다."),
    24: ("신탁법+등기예규", "신탁법 및 신탁원부 기록 변경등기 관련 등기예규", "수익자·위탁자·수탁자 변경, 법원 촉탁, 직권변경과 종전수익자 승낙 필요성을 판단한다."),
    25: ("상법+등기예규", "법인의 합병·분할을 원인으로 한 소유권이전등기 예규·선례", "합병·분할의 등기원인, 중간 생략 가능성, 단독신청과 토지거래허가 첨부 여부를 판단한다."),
    26: ("부동산등기법", "부동산등기법상 등기소 관할과 관할지정·관할변경 규정", "관할 위임, 관할등기소 지정, 관할위반 등기의 각하와 직권말소, 처리권한 이전을 판단한다."),
    27: ("부동산등기법+등기예규", "부동산등기법상 가등기 및 가등기에 의한 본등기 예규·선례", "가등기 대상 청구권, 단독신청, 가처분명령 촉탁, 명의신탁해지 예약과 본등기 첨부정보를 판단한다."),
    28: ("민법+등기예규", "민법상 환매 및 환매특약등기 관련 등기예규·선례", "환매특약등기의 신청구조, 환매권 양도, 환매권 행사와 직권말소 범위를 판단한다."),
    29: ("등기수수료규칙+예규", "등기사항증명서 등 수수료규칙 및 등기신청수수료 예규", "전자신청 과오납, 표시등기 수수료, 공유자 표시변경, 전자촉탁과 합유명의인변경 수수료를 판단한다."),
    30: ("부동산등기법+등기예규", "처분금지가처분에 기한 소유권이전등기와 후행등기 말소 예규·선례", "가처분에 기한 본안승소 후 소유권이전등기와 후행 소유권·경매개시결정등기의 말소신청을 판단한다."),
}

LABEL_CODE = {
    "①": "01",
    "②": "02",
    "③": "03",
    "④": "04",
    "⑤": "05",
    "ㄱ": "ga",
    "ㄴ": "na",
    "ㄷ": "da",
    "ㄹ": "ra",
    "ㅁ": "ma",
    "ㅂ": "ba",
}

REP_ROWS = """
1|①|O|본인서명사실확인서와 신청서 등의 서명은 본인 고유의 필체로 성명을 적는 방식이어야 하며, 등기관이 알아볼 수 없으면 등기신청을 수리하지 않는다.|
1|②|X|등기신청서의 성명 기재는 본인서명사실확인서의 서명이 한글·한자·영문 중 어느 문자로 되어 있는지에 반드시 맞출 필요는 없다.|본인서명사실확인서 서명의 문자 종류와 등기신청서 성명 기재 문자를 반드시 일치시켜야 한다고 한 부분
1|③|O|본인서명사실확인서상 등기의무자의 주소가 주민등록표의 주소이동내역에서 확인되지 않아도 성명과 주민등록번호 등으로 동일인이 인정되면 그 사정만으로 각하하지 않는다.|
1|④|O|자격자대리인이 본인서명사실확인서를 첨부하여 등기신청을 대리하는 경우 위임받은 사람의 성명란에 자격명과 성명이 적혀 있으면 주소 기재가 없어도 된다.|
1|⑤|O|본인서명사실확인서의 위임받은 사람과 위임장의 수임인은 같은 사람이어야 하고, 본인서명사실확인서의 용도와 위임장의 위임취지는 서로 부합하여야 한다.|
2|①|O|회생절차개시 신청 후 보전처분등기는 법원사무관 등의 촉탁으로 하며, 보전처분등기 후 같은 부동산에 보전처분이나 강제집행 등의 등기촉탁이 있어도 수리한다.|
2|②|O|부인등기는 부인권자가 단독으로 신청하고, 부인등기 후 부인된 등기의 명의인을 등기의무자로 하는 등기신청은 각하된다.|
2|③|X|관리인이 회생계획에 따라 채무자 명의 부동산을 처분하여 등기를 신청하는 경우에는 별도의 법원 허가서나 허가 불요 증명서를 첨부할 필요가 없다.|회생계획에 따른 처분등기에도 법원 허가서 또는 허가 불요 증명서 첨부가 필요하다고 한 부분
2|④|O|회생법원이 회생채권 또는 회생담보권에 기한 강제집행 등의 취소를 명한 경우 그 말소등기 촉탁을 집행법원이 하더라도 등기관은 수리할 수 있다.|
2|⑤|O|회생절차개시 및 회생계획인가 등기가 되어 있지 않은 부동산 권리에 대한 회생절차종결등기 촉탁은 부인등기가 있는 경우를 제외하고 각하된다.|
3|①|X|금융기관 지배인이 계속 반복하여 근저당권설정등기 신청업무를 대행하면 신청대행수수료를 받지 않았더라도 법무사법상 업무제한에 위반될 수 있다.|지배인의 반복적 등기신청 대행이 수수료가 없으면 법무사법에 위반되지 않는다고 한 부분
3|②|X|친권자가 미성년자인 자의 채무를 위하여 그 자의 부동산을 담보로 제공하거나 제3자에게 처분하는 것만으로 항상 특별대리인이 필요한 것은 아니다.|미성년자 자신의 채무를 위한 담보제공이나 처분에 항상 특별대리인이 필요하다고 한 부분
3|③|O|미성년자인 두 자녀의 공유부동산에 관하여 공유물분할계약을 하는 경우에는 이해상반을 해소하기 위하여 미성년자 중 한 명에 관한 특별대리인을 선임하면 된다.|
3|④|X|등기권리자와 등기의무자 쌍방의 위임을 받은 법무사는 절차 종료 전 등기의무자만의 등기신청 중지 요청에 당연히 응하여야 하는 것은 아니다.|쌍방위임을 받은 법무사에게 등기의무자 일방의 중지 요청에 따를 의무가 있다고 한 부분
3|⑤|X|수감 중인 등기의무자의 위임장에 교도소장의 작성확인을 받았다는 사정만으로 인감날인과 인감증명 제출을 대체할 수 없다.|교도소장의 위임장 작성확인만으로 인감날인과 인감증명을 대체할 수 있다고 한 부분
4|①|O|사업인정 전에 공공용지 협의취득을 원인으로 하는 소유권이전등기는 일반 원칙에 따라 사업시행자와 등기의무자가 공동으로 신청한다.|
4|②|O|토지수용으로 인한 소유권이전등기는 사업시행자가 관공서이면 촉탁하여야 하지만, 사업시행자와 등기의무자가 공동신청한 경우에도 수리할 수 있다.|
4|③|O|토지수용으로 사업시행자가 원시취득하면 재결로 존속이 인정된 권리를 제외한 토지의 다른 권리는 소멸하므로 환매특약등기도 직권말소 대상이 될 수 있다.|
4|④|X|토지수용으로 인한 소유권이전등기에서 협의에 의한 수용을 증명하려면 협의성립확인서 등 정해진 첨부정보를 제공하여야 하고 단순 협의서만으로는 부족하다.|사업시행자와 토지소유자의 협의서만 첨부하면 협의성립확인서 없이도 수리하여야 한다고 한 부분
4|⑤|O|관공서가 등기권리자로서 수용을 원인으로 한 소유권이전등기를 촉탁하는 경우에도 자격자대리인에게 위임하여 신청할 수 있다.|
5|①|O|시효취득은 민법 제187조의 예외로 등기하여야 소유권을 취득하고, 현재 등기기록상 소유자를 등기의무자로 하여 공동신청한다.|
5|②|O|당사자 사이의 시효취득확인서로 등기를 신청하는 경우 등기원인은 시효취득, 등기원인일자는 점유개시일로 제공한다.|
5|③|O|시효취득한 부동산이 농지법상 농지에 해당하더라도 시효취득 이전등기에는 농지취득자격증명을 첨부정보로 제공할 필요가 없다.|
5|④|X|대장상 소유자미복구 미등기토지에 관하여 국가 상대 판결 이유에서 원고 소유임이 인정되면 원고는 그 판결로 자기 명의 소유권보존등기를 신청할 수 있다.|원고 소유임이 판결 이유에서 인정되어도 반드시 국가를 대위하여 보존등기 후 이전등기만 하여야 한다고 한 부분
5|⑤|O|취득시효완성 후 이전등기 전에 설정된 저당권이나 지상권 등은 등기명의인과의 공동신청 또는 말소등기절차 이행판결에 따른 단독신청으로 말소한다.|
6|①|O|합병하려는 모든 건물에 등기원인, 연월일, 접수번호가 같은 저당권등기가 있으면 공시혼란 우려가 없어 합병할 수 있고 저당권자 승낙정보도 필요하지 않다.|
6|②|X|건축물대장상 합병 후 합병등기 전에 소유자가 달라지거나 합병 제한사유가 생기면 합병 후 건물을 공유로 하거나 제한권리를 공유지분으로 바꾸는 등기를 할 수 없다.|합병등기 전 소유자 변경이나 합병 제한사유가 있어도 합병 후 공유 및 지분권리 변경등기를 할 수 있다고 한 부분
6|③|O|멸실건물의 소유권 등기명의인이 1개월 안에 멸실등기를 신청하지 않으면 그 대지소유자는 건물소유자를 대위하여 멸실등기를 신청할 수 있다.|
6|④|O|멸실된 건물이 근저당권 등 제3자 권리의 목적이어도 멸실 사실이 건축물대장에 기록되어 있으면 멸실등기 신청에 그 권리자의 승낙정보를 제공할 필요가 없다.|
6|⑤|O|집합건축물대장상 구분건물 변경 후 등기기록 표시가 대장과 일치하지 않는 경우 소유자가 같고 합병 제한사유가 없으면 건물 표시변경등기를 신청할 수 있다.|
7|①|X|정비사업 시행자가 대위하여 부동산 표시변경등기나 등기명의인 표시변경등기를 신청하는 경우 일괄신청 가능성이 등기원인 또는 등기목적 동일성에만 제한되는 것은 아니다.|정비사업 시행자의 대위등기 일괄신청을 등기원인 또는 등기목적이 동일한 경우로만 제한한 부분
7|②|X|이전고시 통지 후 대지와 건축물 등기 전 권리에 관한 등기를 금지하는 규정에 위반한 등기라고 하여 부동산등기법 제58조로 직권말소하는 것은 아니다.|이전고시 후 금지된 권리등기를 부동산등기법 제58조에 따라 직권말소한다고 한 부분
7|③|O|정비사업 시행자는 공사가 전부 완료되기 전이라도 완공된 부분에 대하여 준공인가를 받고 이전고시를 하면 그 부분만에 관한 등기신청을 할 수 있다.|
7|④|X|정비사업 이전고시 등기에서 등기관은 신청정보와 관리처분계획·인가서면·이전고시서면의 부합 여부를 심사하지만 종전토지와 건물의 등기기록상 등기사항까지 일치하는지 심사하지는 않는다.|등기관이 종전토지와 건물의 등기기록상 등기사항 일치 여부까지 심사한다고 한 부분
7|⑤|X|정비사업 이전고시에 따른 담보권 등 권리등기는 소유권보존등기와 동시에 신청하더라도 접수번호를 반드시 동일하게 부여하는 것은 아니다.|담보권 등 권리등기와 소유권보존등기에 같은 접수번호를 부여한다고 한 부분
8|①|X|구분지상권설정등기 신청에서 토지를 사용하는 권리자와 그 권리를 목적으로 하는 권리자 전원의 승낙서가 항상 필요한 것은 아니고, 등기관이 그 권리를 직권말소하지도 않는다.|구분지상권설정등기 시 기존 사용권리자 전원의 승낙이 필요하고 그 권리를 직권말소한다고 한 부분
8|②|O|동일 토지에 지상권이 미치는 범위가 서로 다른 둘 이상의 구분지상권은 각기 따로 기록할 수 있으므로 다른 구분지상권자의 승낙정보가 필요하지 않다.|
8|③|O|도시철도법상 도시철도건설자가 재결로 구분지상권설정등기를 한 경우 그보다 먼저 마친 가등기에 의한 지상권설정 본등기가 신청되어도 그 구분지상권은 말소할 수 없다.|
8|④|X|전원개발사업자가 전원개발촉진법에 따른 사용재결을 받은 경우에는 그 법에 따른 절차로 단독 구분지상권설정등기를 신청할 수 있다.|전원개발촉진법상 사용재결을 받은 전원개발사업자의 단독 구분지상권설정등기를 부정한 부분
8|⑤|O|구분지상권 설정행위로 구분지상권 행사를 위하여 토지사용을 제한하는 특약을 한 때에는 그 특약을 신청정보로 제공하여야 한다.|
9|①|O|공유물분할로 분필 후 일방 단독소유가 된 토지에도 다른 공유자 지분의 근저당권 등이 전사되어 효력이 인정되면 그 말소는 통상 말소절차에 따른다.|
9|②|O|공유물분할소송 변론종결 전 일부 공유자의 지분이 제3자에게 이전되었는데 소송승계 없이 종전 공유자를 포함하여 판결이 선고되면 그 판결로 등기를 신청할 수 없다.|
9|③|O|공유지 분할등기를 하려면 먼저 토지분할절차와 분필등기를 한 뒤, 각 분필 부동산별로 공유물분할을 원인으로 한 소유권이전등기를 독립하여 신청할 수 있다.|
9|④|O|공유물분할로 소유권을 취득한 사람이 다시 등기의무자로 소유권이전등기를 신청하는 경우 공유물분할등기의 등기필정보와 종전 공유자 등기필정보를 함께 제공하여야 한다.|
9|⑤|X|여러 부동산을 공유물분할 원인으로 이전등기하려면 각 부동산의 공유자가 동일하여야 하므로, 공유자 구성이 다른 부동산을 하나의 공유물분할 합의로 단독소유화할 수는 없다.|공유자 구성이 다른 부동산까지 하나의 공유물분할 합의로 단독소유화할 수 있다고 한 부분
10|①|O|지적공부가 멸실된 토지를 제외하고 지적공부에 등록되어 있지 않은 토지는 존재하거나 특정된 토지로 볼 수 없어 그 소유권보존등기는 효력이 없다.|
10|②|O|구분소유권의 물리적 요건을 갖추지 못한 건물부분이 대장과 등기부에 구분건물로 기록되어 경매매각되었더라도 원칙적으로 매수인은 소유권을 취득하지 못한다.|
10|③|O|환지에 대한 등기로서 효력이 존속하는 등기는 환지처분공고 당시 종전토지에 있던 등기에 한정되고, 공고 후 환지등기 전 종전토지 등기는 환지에 대한 효력이 없다.|
10|④|X|근저당권설정계약의 채권자가 아닌 제3자 명의로 근저당권설정등기가 된 뒤 채권자가 부기등기로 이전받은 경우라도 전체 등기가 실체관계에 부합하면 유효할 수 있다.|제3자 명의 근저당권설정등기 후 채권자에게 이전된 등기를 실체관계 부합 여부와 무관하게 무효라고 한 부분
10|⑤|O|본등기금지가처분등기 촉탁에 따라 가등기에 의한 본등기를 금지한다는 취지의 가처분등기가 마쳐진 경우 그 등기는 효력이 없다.|
11|ㄱ|O|재외국민이 상속재산분할협의 권한을 대리인에게 위임하려면 분할대상 부동산과 대리인의 인적사항을 구체적으로 특정한 위임장을 첨부정보로 제공하여야 한다.|
11|ㄴ|O|재외국민의 상속재산분할협의 위임장에는 원칙적으로 인감날인과 인감증명을 제출하지만, 재외공관에서 본인이 직접 작성했다는 취지의 공증을 받아 제출할 수도 있다.|
11|ㄷ|X|재외공관에서 본인이 직접 작성했다는 취지의 공증을 받은 상속재산분할협의 위임장을 제출하는 경우 재외국민등록부등본을 별도 첨부정보로 제공하여야 하는 것은 아니다.|재외공관 공증 위임장 제출에도 재외국민등록부등본을 반드시 제공하여야 한다고 한 부분
11|ㄹ|O|대리인은 재외국민의 대리인임을 밝히고 대리인 자격으로 상속재산분할협의서를 작성하여 이를 등기원인증서로 제공하여야 한다.|
11|ㅁ|O|대리인이 작성한 상속재산분할협의서에는 원칙적으로 대리인의 인감날인과 인감증명이 필요하지만, 직접 작성 공증이 있으면 인감증명을 제출하지 않을 수 있다.|
12|①|O|토지 특정 일부에 대한 소유권이전등기 말소판결을 받은 사람은 판결 주문에 분할 명령이 없어도 분필등기 후 그 부분의 소유권이전등기를 말소할 수 있다.|
12|②|O|공동상속인 사이에 유류분반환을 원인으로 부동산 전부 이전등기를 신청하는 경우 유류분액 초과 여부를 확인할 수 있는 정보를 반드시 제공하여야 하는 것은 아니다.|
12|③|O|공유자 중 한 명은 공유자 전원을 위하여 그 전원 명의로 소유권보존등기를 신청할 수 있지만, 자기 지분만에 관한 소유권보존등기는 신청할 수 없다.|
12|④|X|부동산 소유권을 포기한 사람은 소유권 포기에 따른 등기를 단독으로 신청할 수 없고, 소유권을 취득하는 국가 등과 공동으로 이전등기를 신청하여야 한다.|소유권 포기자가 포기에 따른 등기를 단독으로 신청할 수 있다고 한 부분
12|⑤|O|피상속인 사망 후 법정상속등기가 마쳐지고 공동상속인 중 한 명이 사망한 경우 그 상속등기는 상속재산협의분할에 의한 소유권경정등기로 고칠 수 없다.|
13|①|O|채권자가 채무자의 소유권이전등기청구권을 보전하기 위하여 채무자를 대위하여 등기를 신청하는 경우 채무자의 무자력은 요건이 아니다.|
13|②|O|주택법상 금지사항 부기등기가 마쳐진 주택에 대한 가압류채권자는 입주예정자가 없음을 증명하여 그 부기등기 말소를 대위신청할 수 있다.|
13|③|O|구분건물 일부만에 관하여 소유권보존등기를 신청하는 경우 구분건물 소유자는 다른 구분건물 소유자를 대위하여 건물 전부의 소유권보존등기를 신청할 수 있다.|
13|④|X|진정한 소유자가 보존등기명의인을 상대로 말소판결을 받은 경우 그 판결에 따른 말소등기는 대위신청이 아니라 판결에 의한 단독신청으로 처리한다.|진정한 소유자가 보존등기명의인을 대위하여 보존등기 말소를 신청할 수 있다고 한 부분
13|⑤|O|대위신청에 따른 등기를 한 경우 등기관은 대위신청인과 피대위자에게 등기완료통지를 하지만 등기필정보는 작성·통지하지 않는다.|
14|①|O|같은 등기소에 동시에 여러 등기신청을 할 때 첨부정보의 내용이 같으면 먼저 접수되는 신청에 첨부정보를 제공하고 다른 신청에는 원용의 뜻을 제공할 수 있다.|
14|②|X|서로 다른 소유자의 부동산을 같은 매수인에게 이전하는 경우에는 같은 등기소 관할 안에 있더라도 하나의 신청정보로 일괄신청할 수 없다.|서로 다른 소유자의 각 부동산을 같은 매수인에게 이전하는 등기를 하나의 신청서로 일괄신청할 수 있다고 한 부분
14|③|O|공유자 전원이 공유 부동산 전체를 다른 공동매수인들에게 이전하려는 경우에는 하나의 신청서로 신청할 수 없다.|
14|④|O|신탁등기의 신청은 해당 부동산에 관한 권리의 설정등기, 보존등기, 이전등기 또는 변경등기와 동시에 하여야 한다.|
14|⑤|O|창설적 공동근저당에서는 각 근저당권설정자가 서로 다르더라도 일괄신청이 가능하다.|
15|ㄱ|O|소유권 외의 권리를 목적으로 하는 권리에 관한 등기는 부기등기로 한다.|
15|ㄴ|X|소유권에 대한 처분제한등기는 부기등기가 아니라 주등기로 한다.|소유권에 대한 처분제한등기를 부기등기 대상에 포함한 부분
15|ㄷ|X|등기상 이해관계 있는 제3자의 승낙이 없는 권리변경등기는 부기등기가 아니라 주등기로 한다.|이해관계 있는 제3자의 승낙 없는 권리변경등기를 부기등기 대상에 포함한 부분
15|ㄹ|O|신탁등기는 부기등기로 한다.|
15|ㅁ|X|가등기에 의한 본등기는 부기등기가 아니라 주등기로 한다.|가등기에 의한 본등기를 부기등기 대상에 포함한 부분
15|ㅂ|X|일부 등기사항이 말소된 경우의 말소회복등기는 부기등기가 아니라 주등기로 한다.|일부 등기사항 말소회복등기를 부기등기 대상에 포함한 부분
16|①|O|주민등록번호 없는 재외국민의 부동산등기용등록번호는 대법원 소재지 관할 등기소 등기관이 부여하고, 관할 외 등기소 접수 시에는 관할 등기소로 모사전송한다.|
16|②|O|이미 부동산등기용등록번호를 부여받은 재외국민이 관할 외 등기소에 다시 부여신청을 하면 등록번호증명서 발급신청으로 보아 처리할 수 있다.|
16|③|O|재외국민등록번호부와 재외국민 부동산등기용등록번호카드는 영구히 보존하여야 한다.|
16|④|X|재외국민 부동산등기용등록번호 부여신청에 가족관계증명서를 첨부하여야 하는 것은 아니다.|등록번호 부여신청서에 가족관계증명서를 첨부하여야 한다고 한 부분
16|⑤|O|재외국민의 부동산등기용등록번호 오류를 등기관이 정정한 경우 그 재외국민과 행정안전부장관 및 국세청장에게 정정 사실을 통지하여야 한다.|
17|①|X|피담보채권 확정 전에 기본계약상 채권자 지위 양도를 원인으로 근저당권이전등기를 신청하는 경우 물상보증인의 승낙정보를 첨부하여야 하는 것은 아니다.|물상보증인의 승낙정보가 반드시 필요하다고 한 부분
17|②|X|피담보채권 확정 전 계약양도 등을 원인으로 근저당권이전등기를 신청하는 경우 근저당권이전계약서에는 채무자의 표시와 날인이 필요하다.|근저당권이전계약서에 채무자의 표시와 날인이 반드시 필요하지 않다고 한 부분
17|③|X|확정채권의 대위변제를 원인으로 하는 근저당권이전등기에서는 대위변제증서 등 변제와 대위관계를 증명하는 정보가 필요하고 근저당권이전계약서가 당연히 필요한 것은 아니다.|확정채권 대위변제에 근저당권이전계약서까지 첨부하여야 한다고 한 부분
17|④|O|근저당권이전등기 신청에는 채무자에 대한 피담보채권 양도통지나 채무자의 승낙을 증명하는 정보를 제공할 필요가 없고, 대위변제의 경우에도 채무자의 변제동의서를 제공할 필요가 없다.|
17|⑤|X|근저당권의 피담보채권이 확정되기 전에는 피담보채권의 양도나 대위변제만을 원인으로 근저당권이전등기를 신청할 수 없다.|피담보채권 확정 전 채권양도나 대위변제만으로 근저당권이전등기를 신청할 수 있다고 한 부분
18|ㄱ|O|가압류등기의 말소등기는 등기권리자와 등기의무자의 공동신청으로 할 수 없다.|
18|ㄴ|X|공동신청으로 마쳐진 등기의 경정등기는 등기권리자와 등기의무자가 공동으로 신청할 수 있다.|공동신청에 의한 등기의 경정등기를 공동으로 신청할 수 없는 경우에 포함한 부분
18|ㄷ|O|미등기건물의 매수인은 매도인이 보존등기를 하지 않았다는 사정만으로 매도인과 공동으로 소유권보존등기를 신청할 수 없다.|
18|ㄹ|X|제한물권 등기가 불법말소된 뒤 소유권이전등기가 마쳐진 경우 제한물권의 말소회복등기는 등기권리자와 현재 등기의무자가 공동으로 신청할 수 있다.|제한물권 말소회복등기를 공동으로 신청할 수 없는 경우에 포함한 부분
19|①|O|전자신청은 접수절차가 전산정보처리조직으로 자동 처리되므로 접수담당자가 별도로 접수절차를 진행하지 않는다.|
19|②|O|같은 부동산에 관하여 동시에 여러 등기신청이 있으면 같은 접수번호를 부여한다.|
19|③|O|신청서를 접수담당자에게 제출했더라도 해당 부동산을 다른 부동산과 구별할 수 있는 정보가 전산정보처리조직에 저장되기 전에는 신청이 접수된 것이 아니다.|
19|④|X|출입사무원이 여러 건의 등기신청서를 동시에 제출하는 경우 모든 신청서 전면에 표시인을 찍고 제출자란에 사무원 성명을 각각 기재하여야 하는 것은 아니다.|여러 건 동시 제출 때에도 각 신청서마다 표시인과 제출자 성명 기재가 필요하다고 한 부분
19|⑤|O|자격자대리인의 명의대여나 사무원 부당 사건유치 등 비위사실이 인정되거나 출입사무원의 부적정 행위가 있으면 지방법원장은 출입사무원 허가를 취소할 수 있다.|
20|①|O|등기촉탁을 할 수 있는 관공서는 국가 또는 지방자치단체가 원칙이고, 공사 등은 특별규정이 있는 경우에만 등기촉탁을 할 수 있다.|
20|②|O|관공서가 등기를 촉탁하는 경우에는 등기기록과 대장상의 부동산표시가 부합하지 않더라도 그 촉탁을 수리할 수 있다.|
20|③|X|관공서가 등기권리자로서 등기를 촉탁하는 경우에도 등기의무자의 등기필정보를 제공할 필요가 없다.|관공서가 등기권리자로 촉탁하는 경우 등기의무자의 등기필정보를 제공하여야 한다고 한 부분
20|④|O|매각이나 공매처분 등을 원인으로 관공서가 소유권이전등기를 촉탁하는 경우에는 등기의무자의 주소를 증명하는 정보를 제공할 필요가 없다.|
20|⑤|O|수용에 의한 소유권이전등기 촉탁이나 환지처분으로 지방자치단체에 귀속된 도로의 소유권이전등기 촉탁에는 인감증명을 제출할 필요가 없다.|
21|①|X|등기필정보는 분실하더라도 재발급되지 않으므로 등기명의인 본인이 등기소에 출석하여 재발급받을 수 없다.|등기필정보를 분실하면 본인이 등기소에 출석하여 재발급받을 수 있다고 한 부분
21|②|O|하나의 등기에 관하여 등기필증과 등기필정보를 함께 발급하거나 통지하는 경우는 없다.|
21|③|O|등기필정보를 구성하는 비밀번호 중 한 번 사용한 비밀번호는 나머지를 모두 사용한 경우가 아니면 다시 사용할 수 없다.|
21|④|O|등기권리자가 등기필정보 통지를 원하지 않는 경우 등기관은 등기필정보를 작성·통지하지 않을 수 있다.|
21|⑤|O|근저당권 채권최고액 증액이나 전세금·전세기간 변경등기 때에는 등기필정보를 작성·통지하지 않으므로 말소등기 신청 시 설정 당시 등기필정보를 제공하면 충분하다.|
22|①|O|공동저당 대위등기는 후순위 이해관계인의 유무나 동의 여부와 관계없이 부기등기 형식으로 기록한다.|
22|②|O|공동저당 대위등기의 등기연월일은 선순위저당권자에 대한 경매대가 배당기일이고, 등기원인은 민법 제368조 제2항에 의한 대위로 한다.|
22|③|O|공동저당 대위등기에서 매각부동산이 소유권 외 권리인 경우에는 그 권리를 등기기록에 기록한다.|
22|④|X|공동저당 대위등기는 차순위저당권자가 법률상 대위취득한 권리를 공시하는 등기이므로 선순위저당권자를 등기의무자로 하는 공동신청으로 처리하지 않는다.|공동저당 대위등기를 선순위저당권자와 차순위저당권자의 공동신청으로 본 부분
22|⑤|O|공동저당 대위등기신청에는 배당표 정보를 첨부하고, 국민주택채권은 채권최고액과 관계없이 매입하지 않으며, 배당이의소송이 확정되지 않아도 신청할 수 있다.|
23|①|O|승역지와 요역지의 관할 등기소가 다르면 지역권설정등기신청은 승역지를 관할하는 등기소에 하여야 한다.|
23|②|O|요역지 소유자가 아닌 지상권자도 지역권설정등기의 등기권리자가 될 수 있다.|
23|③|O|요역지에 지상권이나 전세권 등 소유권 외 권리가 있으면 지역권 말소를 위하여 그 권리자의 동의정보를 제공하여야 한다.|
23|④|O|지역권설정등기의 등록면허세는 요역지의 시가표준액을 과세표준으로 한다.|
23|⑤|X|대지권이라는 뜻의 등기가 마쳐진 토지에 대하여도 지역권설정등기를 할 수 있다.|대지권 뜻의 등기가 마쳐진 토지에는 지역권설정등기를 할 수 없다고 한 부분
24|①|O|수익자 또는 신탁관리인이 변경되거나 위탁자·수익자·신탁관리인의 성명·주소가 변경되면 수탁자는 지체 없이 신탁원부 기록 변경등기를 신청하여야 한다.|
24|②|O|신탁행위에 위탁자 지위 이전 방법이 정해져 있지 않으면 수탁자와 수익자의 동의정보가 필요하고, 위탁자가 여러 명이면 다른 위탁자의 동의정보도 필요하다.|
24|③|O|법원이 수탁자 해임재판을 하거나 신탁관리인 선임·해임재판을 한 경우 등기관은 법원의 촉탁으로 신탁원부 기록을 변경하여야 한다.|
24|④|O|수탁자 경질로 인한 권리이전등기 또는 여러 수탁자 중 한 명의 임무종료로 인한 합유명의인변경등기를 한 경우 등기관은 직권으로 신탁원부 기록을 변경한다.|
24|⑤|X|신탁원부에 수익자변경권이 위탁자와 수탁자에게 유보되어 있으면 수익자 변경등기 신청에 종전수익자의 승낙정보를 제공할 필요가 없다.|수익자변경권이 유보되어 있어도 종전수익자의 승낙정보를 요구한 부분
25|①|O|합병으로 소멸한 회사 명의 부동산을 존속회사나 신설회사 명의로 하려면 등기명의인표시변경등기가 아니라 합병을 원인으로 한 소유권이전등기를 하여야 한다.|
25|②|O|회사가 흡수합병된 뒤 존속회사가 다시 흡수합병된 경우에는 최초 소멸회사 명의 부동산을 최종 존속회사 앞으로 바로 소유권이전등기할 수 있다.|
25|③|X|흡수합병 후 회사분할로 설립된 회사가 분할계획서상 이전재산이라는 이유만으로 흡수합병 전 소멸회사 명의 부동산의 소유권이전등기를 단독신청할 수는 없다.|분할신설회사가 흡수합병 전 소멸회사 명의 부동산을 단독으로 이전등기 신청할 수 있다고 한 부분
25|④|O|합병으로 소멸하는 회사의 명칭이 변경된 사실은 법인등기사항증명서로 증명하여 바로 합병을 원인으로 하는 소유권이전등기를 신청할 수 있다.|
25|⑤|O|회사분할을 원인으로 하는 소유권이전등기신청에는 토지거래허가증을 첨부정보로 제공할 필요가 없다.|
26|①|O|등기사무는 부동산 소재지를 관할하는 등기소가 담당하는 것이 원칙이지만, 대법원장은 어느 등기소 관할 사무를 다른 등기소에 위임하게 할 수 있다.|
26|②|X|이미 등기된 건물이 부속건물 신축으로 여러 등기소 관할에 걸치게 된 경우까지 항상 관할등기소 지정을 신청하여야 하는 것은 아니다.|부속건물 신축으로 이미 등기된 건물이 여러 관할에 걸치는 경우에도 관할등기소 지정을 항상 요구한 부분
26|③|O|관할등기소 지정신청서는 해당 부동산 소재지를 관할하는 등기소 중 어느 등기소에도 제출할 수 있고, 각 등기소를 관할하는 상급법원장이 관할을 지정한다.|
26|④|O|관할을 위반한 등기신청은 각하하여야 하고, 등기를 마친 뒤 관할위반이 발견되면 부동산등기법 제58조에 따른 직권말소 대상이 된다.|
26|⑤|O|행정구역 변경이나 등기소 신설·폐지 등으로 관할이 변경되면 종전 관할 등기소는 전산정보처리조직으로 등기기록 처리권한을 다른 등기소에 넘긴다.|
27|①|O|가등기는 권리이전청구권이 시기부 또는 정지조건부인 경우에도 할 수 있으므로 사인증여로 인한 소유권이전등기청구권 보전을 위하여도 할 수 있다.|
27|②|O|가등기는 가등기권리자와 가등기의무자의 공동신청이 원칙이지만, 가등기의무자의 승낙이 있으면 가등기권리자가 단독으로 신청할 수 있다.|
27|③|O|가등기를 명하는 법원의 가처분명령에 대하여 법원이 가등기촉탁을 하는 경우 등기관은 그 촉탁을 각하하여야 한다.|
27|④|X|배우자 명의로 명의신탁한 부동산에 관하여 장래 명의신탁해지 약정으로 생길 소유권이전청구권을 보전하기 위한 가등기는 할 수 있다.|배우자 명의신탁 부동산의 명의신탁해지 약정에 따른 소유권이전청구권 보전 가등기를 부정한 부분
27|⑤|O|형식상 매매예약을 원인으로 한 가등기라도 실제로 가등기권리자 요구 시 본등기를 해 주기로 약정한 경우에는 매매예약완결권 행사 없이 본등기를 신청할 수 있다.|
28|①|O|매매계약 시 환매권 유보 특약이 있으면 소유권이전등기와 동시에 별개의 신청정보로 환매특약등기를 신청하여야 한다.|
28|②|O|환매특약등기는 매도인을 등기권리자, 매수인을 등기의무자로 하여 공동신청하고, 제3자를 환매권리자로 하는 환매특약등기는 신청할 수 없다.|
28|③|O|환매권 행사로 인한 소유권이전등기는 원칙적으로 매도인이 등기권리자, 매수인이 등기의무자이지만 환매권 양수인이나 현재 소유명의인이 있으면 그 지위가 반영된다.|
28|④|O|환매권에 관한 가압류, 가처분, 가등기 등 부기등기가 말소되지 않아 환매특약등기를 말소할 수 없는 경우에는 환매권 행사로 인한 소유권이전등기를 할 수 없다.|
28|⑤|X|환매권 행사로 인한 소유권이전등기를 할 때 등기관이 환매특약등기 후 환매권 행사 전에 마쳐진 제3자 명의의 소유권 외 권리를 모두 직권말소하는 것은 아니다.|환매특약등기 이후 환매권 행사 전 제3자 권리를 환매권행사로 인한 실효를 원인으로 직권말소한다고 한 부분
29|①|O|전자신청에서 등기신청수수료를 과오납한 경우 신청인은 등기신청사건 처리완료 전에 기존 결제를 전액 취소한 뒤 다시 결제하여야 한다.|
29|②|O|부동산의 분할·구분·합병 및 멸실등기신청은 대지권에 관한 등기를 제외하고 등기신청수수료를 받지 않는다.|
29|③|O|공유하는 권리의 등기명의인표시변경등기를 전거를 원인으로 신청하는 경우 공유자의 주소가 동일하게 변경되어도 명의인 수만큼 수수료를 납부한다.|
29|④|X|집행법원이 등기를 전자촉탁하는 경우에도 그 사정만으로 등기신청수수료가 감액되는 것은 아니다.|집행법원의 전자촉탁이면 등기신청수수료가 감액된다고 한 부분
29|⑤|O|동일한 합유자가 별도 순위번호로 각 합유등기를 한 뒤 하나의 등기원인으로 전부에 대한 합유명의인변경등기를 신청하면 등기 수만큼 수수료를 납부한다.|
30|①|X|가처분채권자가 확정판결로 소유권이전등기를 신청하며 후행 소유권이전등기의 말소를 신청할 때에는 현재 유효한 등기기록만이 아니라 이기 전 등기기록도 조사 대상이 될 수 있다.|후행 소유권이전등기 말소 가능 여부를 현재 유효한 등기기록만으로 조사한다고 한 부분
30|②|O|가처분등기 후 마쳐진 경매개시결정등기는 가처분채권자의 소유권이전등기 신청과 함께 말소신청하여야 하지만, 그 경매개시결정등기가 가처분 전 가압류에 기한 경우에는 말소신청을 수리하지 않는다.|
30|③|X|가처분등기보다 뒤의 원인으로 경매개시결정등기가 마쳐졌다면 가처분채권자가 소유권이전등기 신청과 동시에 말소신청을 하지 않았더라도 나중에 말소등기신청을 할 수 있다.|후행 경매개시결정등기 말소신청을 동시에 하지 않으면 추후 말소등기를 할 수 없다고 한 부분
30|④|X|가처분등기 이후 말소할 후행등기가 없는 경우에도 가처분채권자가 가처분에 기한 소유권이전등기를 마치면 당해 가처분등기는 등기관이 직권말소한다.|후행 등기가 없는 경우의 가처분등기는 법원 촉탁으로만 말소된다고 한 부분
30|⑤|X|가처분채권자가 가처분에 기한 것임을 소명하여 가처분채무자와 공동으로 소유권이전등기를 신청한 경우에는 가처분에 대항할 수 없는 권리의 말소신청까지 할 수 있는 것은 아니다.|가처분채무자와 공동으로 소유권이전등기를 신청하면서 후행 권리 말소신청도 할 수 있다고 한 부분
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def parse_rep_rows() -> list[dict[str, str | int]]:
    rows = []
    for line in REP_ROWS.splitlines():
        no, label, verdict, rep, trap = (line.split("|", 4) + [""])[:5]
        no_int = int(no)
        rows.append(
            {
                "no": no_int,
                "label": label,
                "code": LABEL_CODE[label],
                "sourceVerdict": verdict,
                "rep": rep,
                "trap": trap or None,
                "unitType": "box" if label in {"ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ"} else "choice",
                "sourceQuestionType": QUESTION_TYPES.get(no_int, "single-best-false"),
                "officialAnswer": OFFICIAL_ANSWERS[no_int],
            }
        )
    return rows


UNITS = parse_rep_rows()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.rfind("【부동산등기법 30문】")
    if start == -1:
        raise ValueError("cannot locate 2024 real-estate-registry section")
    section = text[start:]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 1 <= int(m.group(1)) <= 30]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} real-estate-registry questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            tail = section[match.start() :]
            end_marker = re.search(r"【공탁법", tail)
            end = match.start() + end_marker.start() if end_marker else len(section)
        blocks[no] = section[match.start() : end]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    markers = list(re.finditer(r"[①②③④⑤]", block))
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in markers:
        label = marker.group(0)
        if label not in first_by_label:
            first_by_label[label] = marker
        if set(first_by_label) == {"①", "②", "③", "④", "⑤"}:
            break
    if set(first_by_label) != {"①", "②", "③", "④", "⑤"}:
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in ["①", "②", "③", "④", "⑤"]]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = block[start:end]
        statement = re.split(r"\s*제4과목\s*①책형\s*전체", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    before_choices = re.split(r"[①②③④⑤]", block, maxsplit=1)[0]
    parts = re.split(r"([ㄱㄴㄷㄹㅁㅂ]\.)", before_choices)
    out: dict[str, str] = {}
    for idx in range(1, len(parts), 2):
        label = parts[idx][0]
        statement = parts[idx + 1] if idx + 1 < len(parts) else ""
        out[label] = normalize_raw(statement)
    return out


def raw_statement_map() -> dict[tuple[int, str], str]:
    blocks = extract_question_blocks()
    raw: dict[tuple[int, str], str] = {}
    for no, block in blocks.items():
        split = split_box_units(block) if no in {11, 15, 18} else split_choice_units(block)
        expected = [row["label"] for row in UNITS if row["no"] == no]
        missing = [label for label in expected if label not in split]
        if missing:
            raise ValueError(f"missing raw statements for q{no}: {missing}")
        for label in expected:
            raw[(no, label)] = split[label]
    return raw


def grouped_units() -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    raw = raw_statement_map()
    for row in UNITS:
        row = dict(row)
        row["raw"] = raw[(row["no"], row["label"])]
        basis_type, basis_ref, why = BASIS[row["no"]]
        row["basisType"] = basis_type
        row["basisRef"] = basis_ref
        row["why"] = why
        grouped[row["no"]].append(row)
    return grouped


def build_source() -> dict:
    questions = []
    for no, rows in sorted(grouped_units().items()):
        questions.append(
            {
                "qid": f"{YEAR}-g4-reg-{no:02d}",
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 제1차",
                "group": GROUP,
                "groupLabel": "제4과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": rows[0]["sourceQuestionType"],
                "officialAnswer": rows[0]["officialAnswer"],
                "units": [
                    {
                        "unitId": f"{YEAR}-g4-reg-{no:02d}-{row['code']}",
                        "unitType": row["unitType"],
                        "unitLabel": row["label"],
                        "rawStatement": row["raw"],
                        "sourceVerdict": row["sourceVerdict"],
                    }
                    for row in rows
                ],
                "current": {
                    "changedByCurrentLaw": False,
                    "reviewedAt": today(),
                    "reviewNote": "2026-06-18 현행 부동산등기법·부동산등기규칙 및 관련 판례·예규·선례 기준으로 atom 작성",
                },
            }
        )
    return {
        "schema": "legal-scrivener/problem-original-current-by-subject/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "exam": {
            "examId": EXAM_ID,
            "year": YEAR,
            "round": ROUND,
            "series": "법무사 제1차",
            "booklet": "①책형",
            "date": "2024-08-31",
            "sourcePage": "https://0gichul.com/y2024/130881308",
        },
        "subject": SUBJECT_NAME,
        "subjectSummary": {"questionCount": len(questions), "atomQueueItemCount": len(UNITS)},
        "questions": questions,
    }


def build_queue(source: dict) -> dict:
    rows = [row for rows in grouped_units().values() for row in rows]
    unit_by_id = {f"{YEAR}-g4-reg-{row['no']:02d}-{row['code']}": row for row in rows}
    items = []
    for question in source["questions"]:
        for unit_row in question["units"]:
            row = unit_by_id[unit_row["unitId"]]
            items.append(
                {
                    "unitId": unit_row["unitId"],
                    "examId": EXAM_ID,
                    "sourceFamily": "법무사시험",
                    "source": source_label(question["no"]),
                    "year": YEAR,
                    "round": ROUND,
                    "group": GROUP,
                    "subject": SUBJECT_NAME,
                    "no": question["no"],
                    "unitType": unit_row["unitType"],
                    "unitLabel": unit_row["unitLabel"],
                    "rawStatement": unit_row["rawStatement"],
                    "sourceQuestionType": question["type"],
                    "officialQuestionAnswer": question["officialAnswer"],
                    "officialQuestionAnswerText": None,
                    "originalVerdict": row["sourceVerdict"],
                    "verdictDerivation": "manual-legal-basis-review",
                    "atomWork": {
                        "status": "completed",
                        "instruction": "원문 지문이 아니라 O/X 판단 근거인 조문·판례·예규·선례 지점을 자기완결식 atom으로 작성한다.",
                        "basisTypesAllowed": ["조문", "규칙", "예규", "선례", "판례", "특별법", "등기예규", "판례+예규·선례"],
                        "basisType": row["basisType"],
                        "basisRef": row["basisRef"],
                        "atomRep": row["rep"],
                        "xDependsOn": row["rep"] if row["sourceVerdict"] == "X" else None,
                        "reviewedAt": today(),
                        "currentLawVerdict": "O",
                    },
                }
            )
    return {
        "schema": "legal-scrivener/atom-queue-by-subject/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "subjectSummary": {"questionCount": len(source["questions"]), "atomQueueItemCount": len(items)},
        "queuePolicy": {
            "coverage": "일반 보기, 개수형, 조합형, 박스형의 모든 판단 지문을 atom 제작 대상으로 큐에 올린다.",
            "atomPrinciple": "atom은 지문 복사본이 아니라 O/X 판단 근거인 조문·판례·예규·선례 지점이다.",
            "xHandling": "X 지문은 독립 atom이 아니라 올바른 O atom 또는 근거 법리에 종속시킨다.",
        },
        "items": items,
    }


def atom_id(row: dict) -> str:
    return f"bupmusa-{YEAR}-real-estate-registry-q{int(row['no']):02d}-{row['code']}"


def build_atoms(queue: dict) -> list[dict]:
    queue_by_id = {item["unitId"]: item for item in queue["items"]}
    grouped = grouped_units()
    rows = [row for no in sorted(grouped) for row in grouped[no]]
    atoms = []
    checked_at = today()
    for row in rows:
        unit_id = f"{YEAR}-g4-reg-{row['no']:02d}-{row['code']}"
        item = queue_by_id[unit_id]
        atoms.append(
            {
                "atomId": atom_id(row),
                "sourceUnitId": item["unitId"],
                "sourceFamily": item["sourceFamily"],
                "source": item["source"],
                "year": YEAR,
                "round": ROUND,
                "subject": SUBJECT_NAME,
                "no": row["no"],
                "unitType": item["unitType"],
                "unitLabel": item["unitLabel"],
                "sourceQuestionType": item["sourceQuestionType"],
                "officialQuestionAnswer": item["officialQuestionAnswer"],
                "sourceVerdict": row["sourceVerdict"],
                "currentVerdict": "O",
                "rep": row["rep"],
                "a": "O",
                "basisType": row["basisType"],
                "basisRef": row["basisRef"],
                "why": row["why"],
                "sourceStatement": item["rawStatement"],
                "sourceTrap": row["trap"] if row["sourceVerdict"] == "X" else None,
                "xDependsOn": row["rep"] if row["sourceVerdict"] == "X" else None,
                "reviewedAt": checked_at,
                "currentLawCheckedAt": checked_at,
            }
        )
    validate(atoms, queue["items"])
    return atoms


def validate(atoms: list[dict], queue_items: list[dict]) -> None:
    if len(atoms) != EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {EXPECTED_ATOM_COUNT} atoms, got {len(atoms)}")
    if len(atoms) != len(queue_items):
        raise ValueError(f"atom count mismatch: atoms={len(atoms)} queue={len(queue_items)}")
    ids = [atom["atomId"] for atom in atoms]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    counts = Counter(atom["no"] for atom in atoms)
    if len(counts) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} questions, got {len(counts)}")
    bad_patterns = [
        r"\?",
        r"위\s*[①②③④⑤ㄱㄴㄷㄹㅁㅂ]",
        r"위의\s*[①②③④⑤ㄱㄴㄷㄹㅁㅂ]",
        r"옳은 것은",
        r"옳지 않은 것은",
        r"다음 중",
        r"몇 개인가",
        r"[①②③④⑤]",
    ]
    for atom in atoms:
        if not re.fullmatch(r"[a-z0-9-]+", atom["atomId"]):
            raise ValueError(f"non-ascii atom id: {atom['atomId']}")
        rep = atom["rep"]
        for pattern in bad_patterns:
            if re.search(pattern, rep):
                raise ValueError(f"bad rep pattern {pattern!r} in {atom['atomId']}: {rep}")
        longest = max((len(part) for part in re.split(r"\s+", rep)), default=0)
        if longest > 45:
            raise ValueError(f"suspicious spacing in {atom['atomId']}: {rep}")
        if atom["sourceVerdict"] == "X" and (not atom.get("sourceTrap") or not atom.get("xDependsOn")):
            raise ValueError(f"X source must have trap and dependency: {atom['atomId']}")
        if atom["sourceVerdict"] == "O" and atom.get("sourceTrap") is not None:
            raise ValueError(f"O source must not have trap: {atom['atomId']}")
        if atom["currentVerdict"] != "O" or atom["a"] != "O":
            raise ValueError(f"completed atom must be O: {atom['atomId']}")


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_subject_index(atom_count: int, queue_count: int) -> None:
    if SUBJECT_INDEX_PATH.exists():
        index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
        index["updatedAt"] = today()
        index.setdefault("subjects", {})
    else:
        index = {
            "schema": "legal-scrivener/subject-index/v1",
            "sourceFamily": "법무사시험",
            "updatedAt": today(),
            "examId": EXAM_ID,
            "year": YEAR,
            "round": ROUND,
            "subjects": {},
        }
    index["subjects"][SUBJECT_NAME] = {
        "source": str(SOURCE_PATH),
        "atomQueue": str(QUEUE_PATH),
        "completedAtoms": str(OUT_PATH),
        "questionCount": QUESTION_COUNT,
        "atomQueueItemCount": queue_count,
        "completedAtomCount": atom_count,
        "completedAtomsUpdatedAt": today(),
    }
    write_json(SUBJECT_INDEX_PATH, index)


def build() -> Path:
    source = build_source()
    queue = build_queue(source)
    atoms = build_atoms(queue)
    write_json(SOURCE_PATH, source)
    write_json(QUEUE_PATH, queue)
    write_json(
        OUT_PATH,
        {
            "schema": "legal-scrivener/completed-atoms-by-subject/v1",
            "sourceFamily": "법무사시험",
            "examId": EXAM_ID,
            "year": YEAR,
            "round": ROUND,
            "subject": SUBJECT_NAME,
            "updatedAt": today(),
            "atomPrinciple": "docs/atom_원칙_v001.md",
            "sourceQueue": str(QUEUE_PATH),
            "sourceCount": len(queue["items"]),
            "atomCount": len(atoms),
            "verificationSources": LEGAL_SOURCES,
            "policy": {
                "sourceStatement": "문제 원문 지문은 보존한다.",
                "rep": "화면 출력용 atom은 O인 자기완결형 법리 문장으로 작성한다.",
                "xHandling": "출제 원문이 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap에 함정을 기록한다.",
                "countAndCombination": "개수형·조합형·박스형도 각 항목을 모두 atom으로 분리한다.",
            },
            "items": atoms,
        },
    )
    update_subject_index(len(atoms), len(queue["items"]))
    return OUT_PATH


def main() -> None:
    out = build()
    data = json.loads(out.read_text(encoding="utf-8"))
    print(f"atoms={out}")
    print(f"atomCount={data['atomCount']}")
    print("sourceVerdict=" + ", ".join(f"{key}:{value}" for key, value in sorted(Counter(item["sourceVerdict"] for item in data["items"]).items())))
    print("basis=" + ", ".join(f"{key}:{value}" for key, value in sorted(Counter(item["basisType"] for item in data["items"]).items())))
    for sample in data["items"][:5]:
        print(f"{sample['atomId']} {sample['rep']}")


if __name__ == "__main__":
    main()
