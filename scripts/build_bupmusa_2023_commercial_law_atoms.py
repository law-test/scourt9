from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2023" / "과목별"
RAW_PDF_PATH = PRIVATE_ROOT / "raw" / "2023" / "2023_법무사_상법.pdf"
TEXT_PATH = PRIVATE_ROOT / "text" / "2023" / "2023_법무사_상법.txt"
SOURCE_PATH = SUBJECT_DIR / "2023_법무사_상법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2023_법무사_상법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2023_법무사_상법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2023_법무사_과목별_index.json"

SUBJECT_NAME = "상법"
EXAM_ID = "2023_bupmusa_1st"
YEAR = 2023
ROUND = 29
GROUP = 1
QUESTION_COUNT = 30
EXPECTED_ATOM_COUNT = 150
LABELS = ["①", "②", "③", "④", "⑤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}
TRUE_QUESTIONS = {29, 46}

LEGAL_SOURCES = [
    {"title": "상법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상법"},
    {"title": "어음법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/어음법"},
    {"title": "수표법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/수표법"},
    {"title": "2023 법무사 상법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2023/111904881"},
    {"title": "2023 법무사 1차 최종정답 확정 보도", "publisher": "피앤피뉴스", "url": "https://www.gosiweek.com/article/179587666022018"},
]

OFFICIAL_ANSWERS = {
    21: "②", 22: "④", 23: "⑤", 24: "②", 25: "④",
    26: "③", 27: "④", 28: "①", 29: "⑤", 30: "③",
    31: "③", 32: "④", 33: "④", 34: "②", 35: "①",
    36: "①", 37: "⑤", 38: "②", 39: "⑤", 40: "④",
    41: "②", 42: "①", 43: "④", 44: "②", 45: "②",
    46: "②", 47: "②", 48: "④", 49: "③", 50: "①",
}

TOPICS = {
    21: "주주총회", 22: "대리상", 23: "영업양도인의 경업금지", 24: "전환사채", 25: "신주발행",
    26: "운송주선업", 27: "상인간 매매", 28: "합병", 29: "해상운송인", 30: "소수주주의 주주총회 소집",
    31: "보증보험", 32: "상업등기의 효력", 33: "이익배당청구권", 34: "회계장부 열람·등사권", 35: "보험계약",
    36: "보험료", 37: "회사와 법인격부인", 38: "상인과 상행위", 39: "손해보험", 40: "이사 직무집행정지가처분",
    41: "감사", 42: "지배주주의 소수주식 취득", 43: "유한회사", 44: "중간배당", 45: "지배인",
    46: "합명회사", 47: "이사 등과 회사 간 거래", 48: "주주평등의 원칙", 49: "어음", 50: "중복보험",
}

REP_ROWS = """
21|①|주주총회는 상법 또는 정관이 정한 사항에 한하여 결의할 수 있고, 주주총회 소집은 상법에 다른 규정이 있는 경우 외에는 이사회가 결정한다.|
21|②|정관 또는 주주총회에서 이사의 보수총액이나 한도액을 정한 뒤 구체적인 지급액을 이사회에 위임할 수는 있지만, 이사의 보수에 관한 사항을 이사회에 포괄적으로 위임할 수는 없다.|이사의 보수에 관한 사항을 이사회에 포괄적으로 위임할 수 있다고 한 부분
21|③|주주총회 소집권한이 없는 자가 이사회 소집결정도 없이 소집한 주주총회 결의는 특별한 사정이 없는 한 법률상 존재하지 않는 결의로 보아야 한다.|
21|④|주식회사가 영업 전부 또는 중요한 일부를 양도한 뒤 주주총회 특별결의가 없다는 이유로 스스로 무효를 주장하는 것이 특별한 사정 없이 곧바로 신의칙에 반한다고 할 수는 없다.|
21|⑤|1인 회사가 아닌 주식회사에서는 의결정족수를 충족하는 주주들이 동의하거나 승인하였다는 사정만으로 주주총회 결의가 있었던 것과 마찬가지라고 볼 수는 없다.|
22|①|대리상은 일정한 상인을 위하여 상업사용인이 아니면서 상시 그 영업부류에 속하는 거래의 대리 또는 중개를 영업으로 하는 자이다.|
22|②|대리점총판계약이라는 명칭만으로 곧바로 상법상 대리상이 되는 것은 아니고, 계약 내용을 실질적으로 살펴 대리상 해당 여부를 판단하여야 한다.|
22|③|대리상이 본인의 허락 없이 제3자 계산으로 본인의 영업부류에 속하는 거래를 하면 본인은 계약해지, 손해배상청구 및 이득양도청구를 할 수 있다.|
22|④|대리상의 유치권 목적물은 대리상이 본인을 위하여 점유하는 물건 또는 유가증권이면 충분하고 본인 소유물일 필요는 없다.|대리상 유치권의 목적물이 본인 소유의 물건 또는 유가증권이어야 한다고 한 부분
22|⑤|대리상의 활동으로 본인이 새 고객을 얻거나 영업상 거래가 현저히 증가하여 계약 종료 후에도 이익을 얻는 경우, 계약 종료가 대리상의 책임 있는 사유로 인한 것이 아니면 대리상은 상당한 보상을 청구할 수 있다.|
23|①|영업양도인은 다른 약정이 없으면 10년간 동일한 특별시·광역시·시·군과 인접 특별시·광역시·시·군에서 동종영업을 하지 못한다.|
23|②|경업금지 대상인 동종영업은 영업의 내용, 규모, 방식, 범위 등을 종합하여 양도된 영업과 경쟁관계가 발생할 수 있는 영업을 뜻한다.|
23|③|상인이 아닌 농업협동조합은 영업을 양도하더라도 상법상 영업양도인의 경업금지의무를 부담하지 않는다.|
23|④|경업금지청구권의 양도를 제한하는 특별한 사정이 없으면 영업이 동일성을 유지하여 전전양도될 때 경업금지청구권과 그 양도통지권한도 영업과 함께 이전된다.|
23|⑤|영업양도인의 경업금지지역은 양도된 물적 설비가 있던 지역만이 아니라 영업양도인의 통상적 영업활동이 이루어지던 지역을 기준으로 판단하여야 한다.|경업금지지역을 양도된 물적 설비가 있던 지역만을 기준으로 정하여야 한다고 한 부분
24|①|전환사채발행무효의 소로 더 이상 전환사채 발행의 무효를 다툴 수 없더라도, 전환권 행사로 인한 신주발행은 신주발행무효의 소로 다툴 수 있다.|
24|②|전환사채 발행의 실체가 없는데 등기 외관만 존재하는 경우, 이를 제거하기 위한 전환사채발행부존재확인의 소에는 상법 제429조의 6개월 제소기간 제한이 적용되지 않는다.|전환사채발행부존재확인의 소에 상법 제429조의 6개월 제소기간 제한이 적용된다고 한 부분
24|③|전환사채발행유지청구는 전환사채 발행의 효력이 생기기 전인 납입기일까지 행사하여야 한다.|
24|④|전환사채권자가 전환청구를 한 뒤에는 주식전환의 금지를 구할 법률상 이익이 없다.|
24|⑤|회사가 경영상 목적 없이 대주주 등의 경영권이나 지배권 방어 목적으로 제3자에게 전환사채를 발행하면 그 발행은 무효가 될 수 있다.|
25|①|신주발행무효의 소에서는 신주 발행일부터 6개월의 제소기간이 지난 뒤 새로운 무효사유를 추가하여 주장할 수 없다.|
25|②|경영권 분쟁 상황에서 경영권이나 지배권 방어 목적의 제3자 신주배정이 주주의 신주인수권을 침해하고 지배구조에 중대한 변화를 초래하면 그 신주발행은 무효가 될 수 있다.|
25|③|신주 등의 발행에서 주주배정방식과 제3자배정방식은 주주에게 지분비율에 따른 우선 인수기회를 부여하였는지에 따라 객관적으로 결정된다.|
25|④|주주배정방식 신주발행에서 실권주가 발생하면 회사는 특별한 사정이 없는 한 이사회 결의로 실권주를 제3자에게 처분할 수 있고, 정관에 제3자 발행 근거규정이 반드시 있어야 하는 것은 아니다.|실권주 제3자 처분에 관하여 정관에 반드시 근거규정이 있어야 한다고 한 부분
25|⑤|주식회사가 액면미달가액으로 주식을 발행하려면 설립등기 후 2년이 지나야 하고, 주주총회 특별결의와 법원의 인가가 필요하다.|
26|①|운송주선인은 자기 명의로 물건운송의 주선을 영업으로 하는 자이고, 여객운송의 주선은 운송주선업에 해당하지 않는다.|
26|②|운송주선인이 상법상 운송인의 지위를 취득하지 않는 한 운송인의 대리인으로 운송계약을 체결하였더라도 운송의뢰인과의 관계에서는 운송주선인의 지위에 있다.|
26|③|운송주선인의 책임에 관한 1년 소멸시효는 운송주선인이나 그 사용인이 악의인 경우에는 적용되지 않는다.|운송주선인이 악의인 경우에도 1년이 지나면 책임의 소멸시효가 완성된다고 한 부분
26|④|운송주선인은 물건운송계약 체결의 위탁 인수를 본래 영업목적으로 하지만, 통관, 검수, 보관, 부보, 운송물 수령·인도 등 부수 업무도 담당할 수 있다.|
26|⑤|운송주선인은 자기나 사용인이 운송물의 수령, 인도, 보관, 운송인 선택 기타 운송에 관하여 주의를 해태하지 않았음을 증명하지 못하면 손해배상책임을 면하지 못한다.|
27|①|상인간 매매에서 매수인이 목적물 수령을 거부하거나 수령할 수 없으면 매도인은 물건을 공탁하거나 상당한 기간을 정하여 최고한 뒤 경매할 수 있다.|
27|②|상인간 확정기매매에서는 당사자 일방이 이행시기를 경과하면 상대방은 이행최고나 해제 의사표시 없이 해제의 효력을 주장할 수 있다.|
27|③|상법 제69조의 목적물 검사와 하자통지 의무는 상인간 매매에 적용되므로 매수인만 상인이라는 사정만으로 적용되는 것은 아니다.|
27|④|상인간 매매 목적물에 즉시 발견할 수 없는 하자가 있으면 매수인은 6개월 내 그 하자를 발견하여 지체 없이 통지하여야 하고, 이를 하지 않으면 하자담보책임을 물을 수 없다.|6개월 내 하자 발견과 통지를 하지 않았더라도 매수인에게 과실이 없으면 하자담보책임을 물을 수 있다고 한 부분
27|⑤|상법 제69조에서 매수인이 계약을 해제한 경우에도 원칙적으로 매도인의 비용으로 목적물을 보관 또는 공탁하여야 하지만, 인도장소가 매도인의 영업소 또는 주소와 동일한 행정구역이면 그 의무가 없다.|
28|①|합병은 권리의무가 포괄승계되는 데 반해 영업양도는 특정승계가 원칙이므로, 합병과 영업양도는 법적 성질이 구별된다.|합병의 포괄승계 측면에서 영업양도와 유사하다고 한 부분
28|②|합병에서 적법한 최고를 받은 채권자가 기간 내 이의를 제출하지 않으면 합병을 승인한 것으로 보아 그 채권자는 합병무효의 소를 제기할 수 없다.|
28|③|회사의 합병은 존속회사 또는 신설회사가 본점소재지에서 합병등기를 마쳐야 소멸회사의 권리의무를 승계하는 효력이 생긴다.|
28|④|합병비율이 현저하게 불공정하면 합병계약은 신의성실원칙이나 공평원칙 등에 비추어 무효가 될 수 있고, 주주 등은 합병무효의 소로 다툴 수 있다.|
28|⑤|합병무효의 소는 합병등기가 있은 날부터 6개월 내에 제기하여야 한다.|
29|①|해상운송인의 송하인 또는 수하인에 대한 채권·채무는 그 청구원인과 관계없이 운송물을 인도한 날 또는 인도할 날부터 1년 내 재판상 청구가 없으면 소멸한다.|해상운송인의 권리·의무 소멸기간을 2년이라고 한 부분
29|②|상법 제814조 제1항의 해상운송인 소멸기간은 소멸시효가 아니라 제척기간으로 본다.|상법 제814조 제1항의 소멸기간을 소멸시효라고 한 부분
29|③|상법 제814조 제1항의 소멸기간은 해상운송인의 송하인 또는 수하인에 대한 채권·채무의 청구원인이 계약인지 불법행위인지와 관계없이 적용된다.|상법 제814조 제1항의 소멸기간이 계약상 청구에만 적용되고 불법행위 청구에는 적용되지 않는다고 한 부분
29|④|상법 제814조 제1항의 기간 경과는 권리소멸 사유일 뿐 그 기간이 지난 뒤 제기된 소를 당연히 부적법하게 하는 소송요건은 아니다.|상법 제814조 제1항의 기간이 지난 뒤 제기된 소가 부적법하다고 한 부분
29|⑤|상법 제814조 제1항의 소멸기간이 지난 뒤에도 그 이익을 받는 당사자가 기간 경과를 알면서 법적 이익을 받지 않겠다는 의사를 표시하면 권리소멸의 이익을 포기한 것으로 볼 수 있다.|
30|①|소수주주의 임시주주총회 소집청구에서 상법 제366조 제1항의 이사회는 원칙적으로 대표이사를 의미하고, 대표이사 없는 소규모회사에서는 각 이사를 의미한다.|
30|②|소수주주가 임시총회소집에 관한 법원 허가를 신청할 때 주주총회 권한에 속하지 않는 사항을 회의목적사항으로 삼을 수 없다.|
30|③|상법 제366조 제1항의 전자문서에는 전자우편뿐 아니라 휴대전화 문자메시지나 모바일 메시지도 포함될 수 있다.|전자문서에 휴대전화 문자메시지나 모바일 메시지가 포함되지 않는다고 한 부분
30|④|법원이 총회소집기간을 구체적으로 정하지 않았더라도 총회소집허가결정 후 상당한 기간이 지나도록 총회가 소집되지 않으면 특별한 사정이 없는 한 소집권한은 소멸한다.|
30|⑤|소수주주가 임시총회소집허가를 신청한 경우 법원은 직권으로 주주총회의 의장을 선임할 수 있다.|
31|①|하자보수보증계약의 보증기간이 주계약의 하자담보책임기간과 같고 그 기간 내 발생한 하자에 관하여 보증기간 종료 후 보증사고가 발생하면, 보증금청구권의 소멸시효는 보증사고 발생 때부터 진행한다.|
31|②|보증보험은 채무불이행으로 피보험자가 입을 손해의 전보를 인수하는 손해보험이면서 실질적으로 보증의 성격도 가지므로, 그 성질에 반하지 않는 범위에서 보험과 보증 규정이 모두 적용된다.|
31|③|보험금 지급 전 주계약상 채무의 존부와 범위에 다툼이 있으면 보험계약자는 피보험자를 상대로 주계약상 채무부존재확인을 구할 이익이 있다.|보험계약자가 피보험자를 상대로 주계약상 채무부존재확인을 구할 이익이 없다고 한 부분
31|④|보증보험계약에서 담보되는 주계약상 채무가 확정되기 전에 구상채무 보증인이 적법하게 보증계약을 해지하면, 구체적 보증채무 발생 전에 보증계약관계가 종료되어 보증책임을 면한다.|
31|⑤|보증보험회사는 일반적으로 주계약의 부존재나 무효 여부를 조사·확인할 의무가 없지만, 제출서류에서 주계약의 부존재나 무효를 의심할 특별한 사정이 있으면 조사·확인의무가 면제되지 않는다.|
32|①|등기신청권자가 불실등기 발생에 책임 있게 관여하거나 이를 알고도 방치하는 등 고의·과실로 불실등기를 한 것과 동일시할 특별한 사정이 있으면 상법 제39조의 불실등기책임을 질 수 있다.|
32|②|상업등기는 이미 존재하는 사실관계를 공시하여 대항력을 갖추게 하는 효력이 원칙이고, 등기된 대로의 효력을 부여하는 공신력은 인정되지 않는다.|
32|③|상법상 등기할 사항은 등기하지 않으면 선의의 제3자에게 대항하지 못하고, 등기한 뒤에도 정당한 사유로 이를 알지 못한 제3자에게 대항하지 못한다.|
32|④|회사설립등기처럼 창설적 효력이 있는 상업등기는 등기 자체로 법률효과를 발생시키므로 일반 공시등기의 대항력 제한과 동일하게 취급되지 않는다.|창설적 효력이 있는 등기도 선의의 제3자에게 대항하지 못하거나 정당한 사유로 알지 못한 제3자에게 주장할 수 없다고 한 부분
32|⑤|이사선임 주주총회결의 취소판결이 확정되어 선임결의가 소급하여 무효가 되더라도 그 대표이사와 거래한 상대방은 상법 제39조의 적용 또는 유추적용으로 보호될 수 있다.|
33|①|회사는 이익배당을 원칙적으로 이익배당 결의일부터 1개월 내 하여야 하고, 주주의 배당금지급청구권은 5년간 행사하지 않으면 소멸시효가 완성된다.|
33|②|이익잉여금처분계산서가 주주총회에서 승인되어 이익배당이 확정되기 전에는 주주에게 구체적이고 확정적인 배당금지급청구권이 인정되지 않는다.|
33|③|정관이 배당의무와 배당금 지급조건·산정방식을 구체적으로 정하여 개별 주주의 배당금이 일의적으로 산정되면, 지급조건 충족 때 주주에게 구체적 배당금지급청구권이 인정될 수 있다.|
33|④|상법 제467조의2 제1항에서 말하는 주주의 권리에는 의결권 등 공익권뿐 아니라 이익배당청구권, 잔여재산분배청구권, 신주인수권 등 자익권도 포함된다.|주주의 권리에 자익권이 포함되지 않는다고 한 부분
33|⑤|특정주주를 제외한 나머지 주주에게만 배당금을 지급하는 이익배당결의는 주주평등원칙에 반하여 무효이고, 제외된 주주가 주주평등원칙만으로 동일 비율의 배당금 지급을 구할 수는 없다.|
34|①|상법상 회계장부의 열람 또는 등사를 청구할 수 있는 자는 발행주식총수의 3% 이상에 해당하는 주식을 가진 주주이다.|
34|②|회계장부 열람·등사청구는 이유를 붙인 서면으로 하여야 하지만, 특별한 사정이 없는 한 그 이유를 뒷받침하는 자료까지 반드시 첨부하여야 하는 것은 아니다.|열람·등사청구 이유를 뒷받침하는 자료를 특별한 사정 없이도 첨부하여야 한다고 한 부분
34|③|주식매수청구권을 행사한 주주도 주식매매대금을 지급받지 않은 동안에는 특별한 사정이 없는 한 필요한 경우 회계장부 열람·등사권을 가진다.|
34|④|회계장부 열람·등사청구의 대상인 회계의 장부와 서류는 소수주주의 청구 이유와 실질적으로 관련 있는 회계장부와 그 근거자료가 되는 회계서류이다.|
34|⑤|자회사의 회계장부가 모회사에 보관되어 있고 모회사의 회계상황 파악을 위한 근거자료로 실질적으로 필요하면 모회사 소수주주의 열람·등사청구 대상이 될 수 있다.|
35|①|보험계약의 내용은 보험약관에 한정되지 않고, 당사자가 보험약관과 다른 사항에 관하여 특별히 합의한 내용도 그 효력이 인정될 수 있다.|보험계약 내용이 보험약관 규정에 국한되고 약관과 다른 특별합의의 효력이 인정되지 않는다고 한 부분
35|②|보험계약 존속 중 당사자 일방의 부당한 행위 등으로 신뢰관계가 파괴되어 계약존속을 기대할 수 없는 중대한 사유가 있으면 상대방은 계약을 해지할 수 있다.|
35|③|신뢰관계를 파괴하는 부당행위가 보험계약의 특약에 관한 것이더라도 그 행위가 중대하여 보험계약 전체에 영향을 주면 특별한 사정이 없는 한 해지효력은 보험계약 전부에 미친다.|
35|④|보험금청구권 소멸시효는 원칙적으로 보험사고 발생 때부터 진행하지만, 객관적으로 보험사고 발생사실을 확인할 수 없는 사정이 있으면 보험금청구권자가 이를 알았거나 알 수 있었던 때부터 진행한다.|
35|⑤|계약이행보증보험에서 보험사고가 구체적으로 무엇인지는 계약 내용에 편입된 보험약관, 보험증권, 주계약의 내용 등을 종합하여 결정하여야 한다.|
36|①|보험계약자가 보험료 전부 또는 제1회 보험료를 계약성립 후 2개월이 지나도록 지급하지 않으면 다른 약정이 없는 한 보험계약은 해제된 것으로 본다.|보험료 전부 또는 제1회 보험료 미지급 시 2개월 경과 후 보험자가 계약을 해지할 수 있다고 한 부분
36|②|계속보험료가 약정 시기에 지급되지 않으면 보험자는 상당한 기간을 정하여 보험계약자에게 최고하고 그 기간 내 지급되지 않을 때 계약을 해지할 수 있다.|
36|③|특정한 타인을 위한 보험에서 보험계약자가 보험료 지급을 지체하면 보험자는 그 타인에게도 상당한 기간을 정하여 보험료 지급을 최고한 뒤가 아니면 계약을 해제 또는 해지하지 못한다.|
36|④|보험자가 계속보험료 연체를 이유로 보험계약을 해지하였더라도 연체 이전에 발생한 보험사고에 관하여 지급한 보험금의 반환을 구할 수 없다.|
36|⑤|계속보험료 미지급 시 일정 유예기간 경과만으로 보험자의 최고나 해지 의사표시 없이 자동으로 계약 효력을 상실하게 하는 약관은 무효이다.|
37|①|회사는 본점소재지에서 설립등기를 함으로써 성립하고, 주식회사 설립등기 후 주식인수인은 주식청약서 요건 흠결, 사기, 강박 또는 착오를 이유로 인수의 무효나 취소를 주장하지 못한다.|
37|②|상법상 회사는 합명회사, 합자회사, 유한책임회사, 주식회사, 유한회사 다섯 종류이다.|
37|③|개인이 영업목적, 물적 설비, 인적 구성원이 동일한 회사를 설립하였으나 회사가 개인기업에 불과하거나 책임회피 수단으로 이용되는 예외적 경우에는 법인격을 부인하여 배후 개인에게 책임을 물을 수 있다.|
37|④|개인이 새로 설립한 회사를 지배적으로 이용하는 등 특별한 사정이 있고 별개 인격을 내세워 회사설립 전 개인 채무에 대한 회사 책임을 부인하는 것이 정의와 형평에 반하면 회사에 그 채무이행을 청구할 수 있다.|
37|⑤|회사의 법인격이 형해화되었는지는 원칙적으로 문제된 법률행위 또는 채무부담행위 당시를 기준으로 판단하여야 한다.|법인격 형해화 여부를 원칙적으로 회사 설립등기 시점만을 기준으로 판단한다고 한 부분
38|①|영업의 목적인 상행위를 개시하기 전에 한 영업 준비행위에도 상행위에 관한 상법 규정이 적용될 수 있다.|
38|②|개업준비행위에 상행위 규정이 적용되려면 영업의사가 상대방에게 인식될 수 있으면 충분하고, 일반적·대외적으로 표시되어야 하는 것은 아니다.|영업의사가 일반적·대외적으로 표시되어야 한다고 한 부분
38|③|회사는 상행위를 하지 아니하더라도 상인으로 본다.|
38|④|회사의 대표이사 개인이 회사 운영자금으로 사용할 의사로 돈을 빌리거나 투자를 받았다는 사정만으로 그 개인의 행위가 상행위가 되는 것은 아니다.|
38|⑤|상인이 영업과 상관없이 개인 자격에서 돈을 투자하는 행위는 상인의 기존 영업을 위한 보조적 상행위가 아니다.|
39|①|손해보험은 피보험자의 물건이나 재산에 생기는 사고에 대비하는 보험이고, 피보험자의 생명이나 신체에 생기는 사고에 대비하는 인보험과 구별된다.|
39|②|손해보험의 보험사고에 관하여 손해배상책임을 지는 제3자가 있으면 피보험자는 보험금으로 전보되지 않은 손해에 관하여 제3자에게 배상책임 이행을 청구할 수 있다.|
39|③|중복보험은 동일한 보험계약의 목적과 동일한 사고에 관하여 여러 보험계약이 체결되고 보험금액 총액이 보험가액을 초과하는 경우이므로, 피보험이익이 다르면 중복보험이 아니다.|
39|④|보험계약자와 피보험자가 고의 또는 중대한 과실로 손해방지의무를 위반하면 보험자는 그 위반과 상당인과관계 있는 손해액을 배상청구하거나 보험금에서 공제할 수 있다.|
39|⑤|상법 제682조의 보험자대위에서 제3자의 행위는 피보험이익에 손해를 일으키는 행위를 말하고, 고의 또는 과실에 의한 행위로 한정되지 않는다.|제3자의 행위를 고의 또는 과실에 의한 행위로만 한정한 부분
40|①|이사 직무집행정지가처분을 신청하기 위하여 이사의 지위를 다투는 본안소송이 반드시 제기되어 있어야 하는 것은 아니다.|
40|②|이사 직무집행정지가처분에서 피신청인이 될 수 있는 자는 그 성질상 해당 이사이고, 회사는 피신청인 적격이 없다.|
40|③|이사 직무집행정지가처분이 있으면 본점과 지점의 소재지에서 그 등기를 하여야 한다.|
40|④|직무대행자가 이사회 구성을 변경하는 안건의 주주총회를 소집하려면 임시주주총회인지 정기주주총회인지와 관계없이 법원의 허가가 필요하다.|정기주주총회라면 이사회 구성을 변경하는 안건도 법원 허가 없이 소집할 수 있다고 한 부분
40|⑤|대표이사 직무집행정지 및 직무대행자선임 가처분 후 새 대표이사가 선임되었더라도 가처분결정이 취소되지 않는 한 새 대표이사는 대표이사 권한을 가지지 못한다.|
41|①|감사 선임에서 의결권 없는 주식을 제외한 발행주식총수의 3%를 초과하는 주식을 가진 주주는 원칙적으로 그 초과주식에 관하여 의결권을 행사하지 못한다.|
41|②|주주총회의 감사 선임결의와 피선임자의 승낙이 있으면 회사와 감사 사이의 위임관계가 성립하고 피선임자는 감사 지위를 취득한다.|주주총회 선임결의와 피선임자의 동의가 있어도 대표기관의 청약과 피선임자의 승낙이 따로 있어야 감사 지위를 취득한다고 한 부분
41|③|주식회사의 감사는 필요적 상설기관으로서 회계감사와 이사의 업무집행 감시 권한을 가지며, 선량한 관리자의 주의의무를 위반하여 임무를 해태하면 회사 손해를 배상할 책임이 있다.|
41|④|감사의 소극적 직무수행만으로 감사 자격이나 보수청구권을 부정하기는 어렵지만, 보수가 현저히 과다하거나 회사 자금 지급 방편인 특별한 사정이 있으면 보수청구권 행사가 제한될 수 있다.|
41|⑤|감사는 필요하면 회의 목적사항과 소집이유를 서면에 적어 이사 또는 소집권자에게 제출하여 이사회 소집을 청구할 수 있고, 이사가 지체 없이 소집하지 않으면 그 감사가 이사회를 소집할 수 있다.|
42|①|지배주주에 의한 소수주식 전부 취득 제도에서 지배주주는 회사 발행주식총수의 95% 이상을 자기 계산으로 보유하여야 한다.|발행주식총수의 90% 이상 보유만으로 지배주주 매도청구를 할 수 있다고 한 부분
42|②|지배주주가 소수주주에게 주식 매도청구를 하려면 미리 주주총회의 승인을 받아야 한다.|
42|③|지배주주가 있는 회사의 소수주주는 언제든지 지배주주에게 그 보유주식의 매수를 청구할 수 있다.|
42|④|지배주주가 소수주주에 대한 매도청구에 따라 소수주주의 주식을 취득하는 경우, 지배주주가 매매가액을 지급한 때에 주식이 이전된 것으로 본다.|
42|⑤|자회사 소수주주가 모회사에 주식매수청구를 한 경우 모회사의 지배주주 해당 여부는 자회사가 보유한 자기주식을 발행주식총수와 모회사 보유주식에 각각 합산하여 판단하여야 한다.|
43|①|유한회사 정관에서 특정 이사의 보수액을 구체적으로 정하면 그 보수액은 임용계약 내용이 되어 회사와 이사를 구속하고, 특별한 사정 없이 사원총회 결의만으로 이미 편입된 보수청구권에 영향을 미치지 못한다.|
43|②|유한회사 이사가 명시적 또는 묵시적 약정에 따라 업무를 다른 이사 등에게 포괄적으로 위임하고 실질 업무를 수행하지 않았더라도 특별한 사정 없이 이사 자격이나 보수청구권을 부정하기는 어렵다.|
43|③|유한회사 성립 후 출자금액 납입 또는 현물출자 이행 미완료가 발견되면 회사성립 당시 사원, 이사와 감사는 회사에 연대책임을 지고, 사원의 책임은 면제하지 못하나 이사와 감사의 책임은 총사원 동의로 면제할 수 있다.|
43|④|유한회사 사원의 지분은 강제집행의 대상이 될 수 있지만 금전채권 자체는 아니므로, 출자지분 자체가 전부명령의 대상인 피전부채권이 되는 것은 아니다.|유한회사 사원의 지분이 피전부채권으로서 전부명령의 대상이 된다고 한 부분
43|⑤|유한회사 사원권 명의신탁이 해지되더라도 명의신탁자가 사원권을 회복하려면 사원총회의 특별결의가 있어야 하고, 해지 의사표시만으로 지분이 바로 복귀하지 않는다.|
44|①|연 2회 이상의 결산기를 정한 회사는 상법 제462조의3에 따른 중간배당을 할 수 없다.|
44|②|중간배당에 관한 이사회 결의가 있으면 같은 영업연도 중 다시 중간배당 결의를 하거나 중간배당지급청구권의 내용을 수정하는 이사회 결의를 할 수 없다.|같은 영업연도 중 중간배당지급청구권 내용을 수정하는 이사회 결의는 허용된다고 한 부분
44|③|배당가능이익이 없는데 중간배당이 실시된 경우 위법배당에 따른 부당이득반환청구권은 민법 제162조 제1항의 10년 소멸시효에 걸린다.|
44|④|상법 제462조의3에 따른 중간배당의 횟수는 영업연도 중 1회로 제한된다.|
44|⑤|결산기 대차대조표상 순자산액이 이익배당의 법정한도에 미치지 못하는데 중간배당을 하면 이사는 회사에 대하여 연대하여 그 차액 또는 배당액을 배상할 책임이 있다.|
45|①|지배인의 행위가 영업주의 영업에 관한 행위이면 제3자가 대리권 제한을 알았거나 중대한 과실로 알지 못한 경우 영업주는 그 제한으로 상대방에게 대항할 수 있고, 악의 또는 중과실은 영업주가 주장·증명하여야 한다.|
45|②|지배인의 행위가 영업주의 영업에 관한 것인지는 지배인의 주관적 의사와 관계없이 행위의 객관적 성질에 따라 추상적으로 판단하여야 한다.|지배인의 주관적 의사까지 함께 고려하여 영업 관련성을 판단한다고 한 부분
45|③|지배인이 대리권한 범위 내 행위를 하였더라도 영업주 이익이나 의사에 반하여 자기 또는 제3자의 이익을 도모할 목적으로 권한을 행사하고 상대방이 그 진의를 알았거나 알 수 있었으면 영업주는 책임을 지지 않는다.|
45|④|지배인이 내부적 대리권 제한을 위반하여 어음행위를 한 경우, 그 제한으로 대항할 수 있는 제3자에는 직접 어음을 취득한 상대방뿐 아니라 다시 배서양도받은 제3취득자도 포함된다.|
45|⑤|부분적 포괄대리권을 가진 사용인에게는 표현지배인에 관한 상법 제14조가 유추적용되지 않는다.|
46|①|합명회사의 업무집행권한은 상법 제205조 제1항에 따른 법원의 선고뿐 아니라, 상법 제195조가 준용하는 민법 제708조 등에 따른 총사원 일치 해임으로도 상실될 수 있다.|업무집행권한 상실이 법원의 선고 방법으로만 가능하다고 한 부분
46|②|합명회사 사원은 회사채권자에 대하여 직접·연대·무한책임을 부담하므로, 업무집행권한 상실제도로 부적합하거나 중대한 의무위반이 있는 사원 등을 업무집행에서 배제하여 자신의 책임 발생·증대를 막을 수 있다.|
46|③|합명회사 사원의 회사채권자에 대한 책임은 회사채무와 함께 발생하지만, 회사재산으로 완제할 수 없거나 회사재산에 대한 강제집행이 주효하지 못한 때에 보충적으로 추궁될 수 있다.|합명회사 사원의 책임이 회사재산 부족 또는 강제집행 불능 시에 비로소 발생한다고 한 부분
46|④|합명회사의 청산 중에는 사원의 퇴사가 허용되지 않는다.|합명회사의 청산 중 사원 퇴사가 허용된다고 한 부분
46|⑤|합명회사 사원이 아닌 자가 타인에게 자기를 사원으로 오인시키는 행위를 하고 그 오인으로 회사와 거래가 이루어지면 그 자는 사원과 같은 책임을 질 수 있다.|합명회사에는 표현책임 규정이 없어 사원이 아닌 자가 사원으로 오인시킨 경우에도 책임을 부담하지 않는다고 한 부분
47|①|상법 제398조의 이사회 승인이 있으려면 이사회에서 해당 거래의 중요사실이 밝혀지고 이익상반거래의 공정성에 관한 심의가 이루어져야 한다.|
47|②|타인 명의로 의결권 없는 주식을 제외한 발행주식총수의 10% 이상을 실질적으로 소유한 주요주주의 특수관계인이 회사와 거래하려면 미리 중요사실을 밝히고 이사회 승인을 받아야 할 수 있다.|실질 주요주주의 특수관계인이 회사와 거래할 때 이사회 승인이 필요 없다고 한 부분
47|③|자본금 총액 10억 원 미만으로 이사가 1명 또는 2명인 회사의 이사가 회사와 자기거래를 하려면 사전에 주주총회에서 중요사실을 밝히고 승인을 받아야 하며, 이를 거치지 않으면 특별한 사정이 없는 한 거래는 무효이다.|
47|④|이사 등이 자기 또는 제3자의 계산으로 회사와 거래하면서 사전에 상법 제398조의 승인을 받지 않았다면 특별한 사정이 없는 한 거래는 무효이고, 사후승인만으로 무효인 거래가 당연히 유효하게 되지는 않는다.|
47|⑤|이사가 회사에 대하여 담보를 제공하는 약정을 하는 경우에는 회사와 이익이 상반된다고 보기 어려워 이사회 승인을 거칠 필요가 없다.|
48|①|주주평등원칙에 위반하여 회사가 일부 주주에게만 우월한 권리나 이익을 부여하기로 하는 약정은 특별한 사정이 없는 한 무효이다.|
48|②|회사가 직원들을 유상증자에 참여시키면서 퇴직 시 출자손실금을 전액 보전해 주기로 한 약정은 단체협약이나 취업규칙 성격을 함께 가지더라도 무효이다.|
48|③|잔여재산은 원칙적으로 각 주주가 가진 주식수에 따라 분배하지만, 회사가 잔여재산분배 등에 관하여 내용이 다른 종류주식을 발행한 경우에는 달리 볼 수 있다.|
48|④|회사가 주주에게 투하자본 회수를 절대적으로 보장하는 약정은 주주 전원의 동의가 있더라도 특별한 사정이 없는 한 주주평등원칙 등에 반하여 무효이다.|주주 전원의 동의가 있으면 투하자본 회수 절대보장 약정이 유효하다고 한 부분
48|⑤|주주와 다른 주주 사이의 계약은 원칙적으로 회사가 주주에게 우월한 권리나 이익을 부여하는 것이 아니므로 주주평등원칙과 직접 관련이 없다.|
49|①|어음채무자는 어음채권을 지명채권양도 방법으로 양수한 자에게 양도인에 대한 인적항변으로 대항할 수 있다.|
49|②|발행인과 수취인이 채권추심이나 강제집행을 피하려고 통정하여 형식적으로만 약속어음 발행을 가장한 경우 그 어음발행행위는 통정허위표시로 무효이고, 무효사유는 이를 주장하는 자가 증명하여야 한다.|
49|③|특정인의 채무를 담보하기 위하여 약속어음을 발행하거나 배서하였다는 사정만으로 약속어음 발행인 또는 배서인과 채권자 사이에 민사상 보증계약이 성립한 것으로 추정되지는 않는다.|담보 목적 약속어음 발행 또는 배서만으로 민사상 보증계약 성립이 추정된다고 한 부분
49|④|매수인이 물품대금 지급을 위하여 지급기일이 물품공급일 이후인 약속어음을 발행·교부한 경우, 특별한 사정이 없는 한 물품대금채무 이행기는 약속어음 지급기일이다.|
49|⑤|수취인란이 기재되지 않은 미완성 표지어음의 지급제시만으로는 발행인을 이행지체에 빠뜨릴 수 없고, 지연손해금은 수취인란 보충 후 지급제시를 한 다음 날부터 기산한다.|
50|①|학교안전공제중앙회가 학교배상책임공제에 따라 피해자에게 공제금을 지급한 경우, 가해자인 피공제자의 책임보험자에게 피해자의 보험금 직접청구권을 대위행사할 수는 없다.|학교배상책임공제 공제금 지급 후 피해자의 보험금 직접청구권을 대위행사할 수 있다고 한 부분
50|②|임차인이 가입한 임차건물 화재보험과 소유자가 가입한 화재보험이 소유자를 피보험자로 하는 중복보험 관계에 있어도, 소유자 화재보험자가 중복보험분담금을 지급받았다는 사정만으로 임차인에 대한 보험자대위청구가 배제되지는 않는다.|
50|③|사용자의 보험자가 피해자에게 사용자와 피용자의 공동불법행위 손해배상금을 모두 지급하여 피용자의 보험자가 면책된 경우, 피용자의 보험자는 사용자의 보험자에게 구상권제한 법리를 주장할 수 없다.|
50|④|하나의 사고에 관하여 여러 무보험자동차 상해담보특약이 체결되고 보험금액 총액이 손해액을 초과하면 상법 제672조 제1항이 준용되어 보험자는 각자의 보험금액 한도에서 연대책임을 지고, 보험자 사이에서는 보험금액 비율에 따라 보상책임을 진다.|
50|⑤|제2 책임보험계약의 보험자가 공동불법행위 피해자에게 보험금을 지급하여 제1 책임보험계약 피보험자도 면책된 경우, 제2 보험자가 제1 보험자에게 행사할 수 있는 구상권은 제1 보험자의 중복보험 부담 부분 중 해당 피보험자의 과실비율 상당액이다.|
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def unit_source_label(no: int, label: str) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {label} 기출"


def source_question_type(no: int) -> str:
    return "single-best-true" if no in TRUE_QUESTIONS else "single-best-false"


def source_verdict(no: int, label: str) -> str:
    answer = OFFICIAL_ANSWERS[no]
    if no in TRUE_QUESTIONS:
        return "O" if label == answer else "X"
    return "X" if label == answer else "O"


def basis(no: int) -> tuple[str, str, str]:
    topic = TOPICS[no]
    if no == 49:
        return ("어음법+판례", f"{topic} 관련 어음법 조문 및 대법원 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    if no in {35, 36, 39, 50}:
        return ("상법 보험편+판례", f"{topic} 관련 상법 보험편 조문 및 대법원 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    return ("상법+판례", f"{topic} 관련 상법 조문 및 대법원 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")


def ensure_raw_text() -> str:
    if not RAW_PDF_PATH.exists():
        raise FileNotFoundError(f"missing source PDF: {RAW_PDF_PATH}")
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(RAW_PDF_PATH)).pages)
    if not text.strip():
        raise ValueError("source PDF text extraction returned empty text")
    TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEXT_PATH.write_text(text, encoding="utf-8")
    return text


def extract_question_blocks(text: str) -> dict[int, str]:
    matches = [m for m in re.finditer(r"문\s*(\d+)", text) if 21 <= int(m.group(1)) <= 50]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} commercial-law questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        blocks[no] = text[match.start():end]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in re.finditer(r"[①②③④⑤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == set(LABELS):
            break
    if set(first_by_label) != set(LABELS):
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in LABELS]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = block[start:end]
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def parse_rep_rows() -> list[dict[str, str | int | None]]:
    rows: list[dict[str, str | int | None]] = []
    for line in REP_ROWS.splitlines():
        no_text, label, rep, *rest = line.split("|")
        no = int(no_text)
        verdict = source_verdict(no, label)
        trap = rest[0].strip() if rest and rest[0].strip() else None
        if verdict == "X" and not trap:
            raise ValueError(f"X source row without trap: {line}")
        if verdict == "O" and trap:
            raise ValueError(f"O source row has trap: {line}")
        rows.append(
            {
                "no": no,
                "label": label,
                "code": LABEL_CODE[label],
                "sourceVerdict": verdict,
                "rep": rep.strip(),
                "trap": trap,
            }
        )
    return rows


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    needed: dict[int, list[str]] = defaultdict(list)
    for row in parse_rep_rows():
        needed[int(row["no"])].append(str(row["label"]))
    for no, labels in needed.items():
        split = split_choice_units(blocks[no])
        for label in labels:
            raw[(no, label)] = split[label]
    return raw


def grouped_rows(raws: dict[tuple[int, str], str]) -> dict[int, list[dict[str, object]]]:
    grouped: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in parse_rep_rows():
        no = int(row["no"])
        label = str(row["label"])
        basis_type, basis_ref, why = basis(no)
        grouped[no].append({**row, "raw": raws[(no, label)], "basisType": basis_type, "basisRef": basis_ref, "why": why})
    return grouped


def build_source(grouped: dict[int, list[dict[str, object]]]) -> dict[str, object]:
    questions = []
    for no in range(21, 51):
        rows = grouped[no]
        qid = f"{YEAR}-g1-commercial-law-{no:02d}"
        units = []
        for row in rows:
            units.append(
                {
                    "unitId": f"{qid}-{row['code']}",
                    "unitType": "choice",
                    "label": row["label"],
                    "rawStatement": row["raw"],
                    "originalVerdict": row["sourceVerdict"],
                }
            )
        questions.append(
            {
                "qid": qid,
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 1차",
                "group": GROUP,
                "groupLabel": "제1과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": source_question_type(no),
                "officialAnswer": OFFICIAL_ANSWERS[no],
                "units": units,
            }
        )
    return {
        "schema": "legal-scrivener/problem-original-current-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "questionCount": len(questions),
        "verificationSources": LEGAL_SOURCES,
        "questions": questions,
    }


def build_queue(source: dict[str, object]) -> dict[str, object]:
    items = []
    for question in source["questions"]:
        q = question
        for unit in q["units"]:
            items.append(
                {
                    "unitId": unit["unitId"],
                    "sourceFamily": "법무사시험",
                    "source": unit_source_label(q["no"], unit["label"]),
                    "examId": EXAM_ID,
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "no": q["no"],
                    "unitType": unit["unitType"],
                    "unitLabel": unit["label"],
                    "sourceQuestionType": q["type"],
                    "officialQuestionAnswer": q["officialAnswer"],
                    "rawStatement": unit["rawStatement"],
                    "originalVerdict": unit["originalVerdict"],
                }
            )
    return {
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "source": str(SOURCE_PATH),
        "itemCount": len(items),
        "items": items,
    }


def build_atoms(queue: dict[str, object], rows: list[dict[str, str | int | None]]) -> list[dict[str, object]]:
    rows_by_key = {(int(row["no"]), str(row["label"])): row for row in rows}
    checked_at = today()
    atoms = []
    for item in queue["items"]:
        row = rows_by_key[(item["no"], item["unitLabel"])]
        basis_type, basis_ref, why = basis(item["no"])
        source_is_x = row["sourceVerdict"] == "X"
        rep = str(row["rep"])
        atoms.append(
            {
                "atomId": f"bupmusa-2023-commercial-law-q{item['no']:02d}-{row['code']}",
                "sourceUnitId": item["unitId"],
                "sourceFamily": item["sourceFamily"],
                "source": item["source"],
                "year": item["year"],
                "round": item["round"],
                "subject": SUBJECT_NAME,
                "topic": TOPICS[item["no"]],
                "no": item["no"],
                "unitType": item["unitType"],
                "unitLabel": item["unitLabel"],
                "sourceQuestionType": item["sourceQuestionType"],
                "officialQuestionAnswer": item["officialQuestionAnswer"],
                "sourceVerdict": row["sourceVerdict"],
                "currentVerdict": "O",
                "rep": rep,
                "a": "O",
                "basisType": basis_type,
                "basisRef": basis_ref,
                "why": why,
                "sourceStatement": item["rawStatement"],
                "sourceTrap": row["trap"] if source_is_x else None,
                "xDependsOn": rep if source_is_x else None,
                "reviewedAt": checked_at,
                "currentLawCheckedAt": checked_at,
            }
        )
    validate_atoms(atoms)
    return atoms


def validate_atoms(atoms: list[dict[str, object]]) -> None:
    if len(atoms) != EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {EXPECTED_ATOM_COUNT} atoms, got {len(atoms)}")
    if len({atom["atomId"] for atom in atoms}) != len(atoms):
        raise ValueError("duplicate atomId")
    counts = Counter(atom["no"] for atom in atoms)
    if set(counts) != set(range(21, 51)) or any(count != 5 for count in counts.values()):
        raise ValueError(f"question coverage mismatch: {dict(counts)}")
    banned = ["?", "？", "①", "②", "③", "④", "⑤", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "옳은 것은", "옳지 않은 것은"]
    for atom in atoms:
        rep = str(atom["rep"])
        if any(pattern in rep for pattern in banned):
            raise ValueError(f"non-atomic wording in {atom['atomId']}: {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in {atom['atomId']}: {rep}")
        if len(rep) >= 20 and " " not in rep:
            raise ValueError(f"spacing suspect in {atom['atomId']}: {rep}")
        if not rep.endswith("."):
            raise ValueError(f"rep must be complete sentence in {atom['atomId']}: {rep}")
        if atom["sourceVerdict"] == "X":
            if not atom["sourceTrap"] or atom["xDependsOn"] != rep:
                raise ValueError(f"bad X dependency: {atom['atomId']}")
        elif atom["sourceTrap"] is not None or atom["xDependsOn"] is not None:
            raise ValueError(f"unexpected X metadata: {atom['atomId']}")
        if atom["currentVerdict"] != "O" or atom["a"] != "O":
            raise ValueError(f"completed atom must be O: {atom['atomId']}")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_subject_index(atom_count: int) -> None:
    if SUBJECT_INDEX_PATH.exists():
        index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
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
    index["updatedAt"] = today()
    index.setdefault("subjects", {})[SUBJECT_NAME] = {
        "source": str(SOURCE_PATH),
        "atomQueue": str(QUEUE_PATH),
        "completedAtoms": str(OUT_PATH),
        "questionCount": QUESTION_COUNT,
        "atomQueueItemCount": atom_count,
        "completedAtomCount": atom_count,
        "completedAtomsUpdatedAt": today(),
    }
    write_json(SUBJECT_INDEX_PATH, index)


def build() -> Path:
    text = ensure_raw_text()
    blocks = extract_question_blocks(text)
    raws = raw_statement_map(blocks)
    grouped = grouped_rows(raws)
    source = build_source(grouped)
    queue = build_queue(source)
    atoms = build_atoms(queue, parse_rep_rows())
    write_json(SOURCE_PATH, source)
    write_json(QUEUE_PATH, queue)
    doc = {
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
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "xHandling": "출제 원문상 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형 문제는 선택지 조합이 아니라 ㄱ·ㄴ·ㄷ 등 개별 근거명제로 atom화한다.",
        },
        "items": atoms,
    }
    write_json(OUT_PATH, doc)
    update_subject_index(len(atoms))
    return OUT_PATH


def main() -> None:
    out = build()
    data = json.loads(out.read_text(encoding="utf-8"))
    by_verdict = Counter(item["sourceVerdict"] for item in data["items"])
    print(f"atoms={out}")
    print(f"atomCount={data['atomCount']}")
    print("sourceVerdict=" + ", ".join(f"{key}:{value}" for key, value in sorted(by_verdict.items())))
    for sample in data["items"][:5]:
        print(f"{sample['atomId']} {sample['rep']}")


if __name__ == "__main__":
    main()
