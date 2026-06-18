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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_상법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_상법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_상법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "상법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_COUNT = 30
EXPECTED_ATOM_COUNT = 147

LEGAL_SOURCES = [
    {"title": "상법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상법"},
    {"title": "어음법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/어음법"},
    {"title": "수표법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/수표법"},
    {"title": "2024 법무사 상법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881303"},
]

OFFICIAL_ANSWERS = {
    21: "②", 22: "①", 23: "②", 24: "③", 25: "⑤",
    26: "⑤", 27: "④", 28: "②", 29: "③", 30: "②",
    31: "정답없음", 32: "④", 33: "⑤", 34: "⑤", 35: "①",
    36: "②", 37: "②", 38: "②", 39: "③", 40: "④",
    41: "①", 42: "①", 43: "⑤", 44: "③", 45: "②",
    46: "④", 47: "①", 48: "③", 49: "①", 50: "④",
}

QUESTION_TYPES = {
    26: "multi-select-true",
    30: "multi-select-false",
    31: "multi-select-false-answerless",
    34: "multi-select-true",
    38: "single-best-true",
    39: "multi-select-true",
    41: "multi-select-false",
    42: "single-best-true",
}

BOX_QUESTIONS = {26, 30, 31, 34, 39, 41}
LABEL_CODE = {
    "①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05",
    "ㄱ": "ga", "ㄴ": "na", "ㄷ": "da", "ㄹ": "ra", "ㅁ": "ma",
}

TOPICS = {
    21: "금융리스계약", 22: "주주명부와 명의개서", 23: "1인 회사", 24: "주주총회 소집절차 하자", 25: "자본금 감소",
    26: "지배인", 27: "보험계약자의 고지의무", 28: "어음 및 수표", 29: "부분적 포괄대리권을 가진 사용인", 30: "주주총회결의 하자",
    31: "이사회 결의와 자기거래", 32: "위탁매매업", 33: "청산 및 해산", 34: "자기주식과 공유주식", 35: "어음과 사고신고담보금",
    36: "주식매수선택권", 37: "해상운송과 운송주선", 38: "익명조합과 합자조합", 39: "주주평등의 원칙", 40: "상사유치권과 유질계약",
    41: "손해보험", 42: "영업양도", 43: "대리상·조합·보세창고", 44: "신주발행", 45: "이사의 책임",
    46: "상업장부와 상업등기", 47: "보험계약", 48: "상사 소멸시효", 49: "이사의 보수", 50: "간이합병·소규모합병",
}

REP_ROWS = """
21|①|O|금융리스계약은 금융리스물건의 취득 또는 대여에 필요한 자금에 관한 금융편의를 제공하는 것을 본질적 내용으로 한다.|
21|②|X|금융리스업자는 금융리스이용자가 공급자로부터 적합한 금융리스물건을 수령할 수 있도록 협력할 의무를 부담하지만, 독자적인 인도의무나 검사·확인의무까지 부담하지는 않는다.|금융리스업자가 독자적인 금융리스물건 인도의무와 검사·확인의무를 부담한다고 한 부분
21|③|O|리스계약은 형식상 임대차와 유사하지만 실질은 물적 금융이므로 민법상 임대차 규정이 바로 적용되지 않는다.|
21|④|O|리스계약은 낙성계약이고, 리스이용자가 리스물건 수령증서를 발급하면 현실 인도 전이라도 리스기간과 리스료 지급의무가 시작될 수 있다.|
21|⑤|O|리스회사에 유보된 리스물건 소유권과 그 변환물인 보험금청구권은 리스이용자의 채무이행을 담보하는 기능을 가진다.|
22|①|X|주주 또는 회사채권자의 주주명부 열람·등사청구에 정당한 목적이 없다는 특별한 사정은 회사가 증명하여야 한다.|정당한 목적이 있다는 점을 청구자인 주주 또는 회사채권자가 증명하여야 한다고 한 부분
22|②|O|주주명부에 명의개서를 한 주식양수인은 회사에 권리자임을 따로 증명하지 않고도 주주권을 적법하게 행사할 수 있다.|
22|③|O|주식회사는 실제 주식 인수자나 양수자가 따로 있음을 알았더라도 주주명부상 주주의 주주권 행사를 부인할 수 없다.|
22|④|O|명의개서를 하지 않은 주식양수인에게 주주총회 소집통지를 하지 않았다는 사정만으로 주주총회결의에 절차상 하자가 생기지는 않는다.|
22|⑤|O|주권발행 주식을 양수한 자는 주권 제시로 양수사실을 증명하여 단독으로 명의개서를 청구할 수 있고, 회사는 원칙적으로 형식적 자격만 심사하면 된다.|
23|①|O|1인 회사에서는 실제 주주총회 개최가 없더라도 1인 주주의 의결이 있었던 것으로 의사록이 작성되면 특별한 사정이 없는 한 그 결의가 있었던 것으로 볼 수 있다.|
23|②|X|한 사람이 다른 사람 명의를 빌려 주주로 등재하였더라도 총주식을 실질적으로 그 한 사람이 모두 소유하면 1인 회사 결의 법리가 적용될 수 있다.|명의차용 주주 등재의 경우에는 1인 회사 결의 법리가 적용되지 않는다고 한 부분
23|③|O|주식 소유가 실질적으로 분산되어 있으면 1인이 대다수 주식을 보유하고 그 지배주주 의결로 의사록이 작성되어도 결의가 있었다고 볼 수 없다.|
23|④|O|실질상 1인 회사의 대표이사이자 1인 주주가 회사의 유일한 영업재산을 처분한 경우 주주총회 특별결의가 없더라도 그 처분은 유효할 수 있다.|
23|⑤|O|사실상 1인 회사에서 퇴직금이 실질적 1인 주주의 결재·승인을 거쳐 관행적으로 지급되었다면 임원퇴직금 지급규정에 대한 주주총회 결의가 있었던 것으로 볼 수 있다.|
24|①|O|대표이사가 아닌 이사가 이사회 소집결의에 따라 주주총회를 소집한 경우 그 하자는 원칙적으로 주주총회결의 취소사유에 그친다.|
24|②|O|정당한 소집권자가 소집한 주주총회에서 정족수와 전원찬성 결의가 있으면 일부 소집통지 하자는 원칙적으로 결의취소사유에 그친다.|
24|③|X|주주총회 개회시각 지연이 사회통념상 참석 곤란하지 않을 정도이면 결의 부존재·무효사유뿐 아니라 취소사유도 되지 않는다.|개회시각 지연이 곤란하지 않은 경우에도 단순한 취소사유라고 한 부분
24|④|O|주주는 자신이 아닌 다른 주주에 대한 소집절차 하자를 이유로 주주총회결의 취소의 소를 제기할 수 있다.|
24|⑤|O|미리 통지되지 않은 목적사항 결의에 가담한 주주가 결의취소를 구한다는 사정만으로 곧바로 신의칙이나 금반언 원칙에 반하지는 않는다.|
25|①|O|주식병합을 통한 자본금 감소에 이의가 있는 주주 등과 승인하지 않은 채권자는 변경등기일부터 6개월 내에 감자무효의 소를 제기할 수 있다.|
25|②|O|자본감소 효력 발생 후에는 결의 하자가 극히 중대하여 자본감소 부존재에 이를 정도가 아닌 한 감자무효의 소로만 다툴 수 있다.|
25|③|O|자본금 감소의 방법이나 절차가 주주평등원칙, 법령·정관 또는 신의성실원칙에 반하여 현저히 불공정하면 감자무효의 소를 제기할 수 있다.|
25|④|O|주식수에 따라 다른 비율로 주식을 병합하는 차등감자나 현저히 불공정한 주식병합 감자는 자본금 감소무효의 원인이 될 수 있다.|
25|⑤|X|자본금 감소를 위한 주식소각 과정에서 이사가 법령을 위반하여 회사에 손해를 끼치면 감자무효판결 확정과 관계없이 손해배상책임을 부담할 수 있다.|감자무효판결이 확정되어야만 이사의 손해배상책임을 부담한다고 한 부분
26|ㄱ|O|지배인은 영업주에 갈음하여 그 영업에 관한 재판상 또는 재판 외의 모든 행위를 할 수 있는 상업사용인이다.|
26|ㄴ|O|상인은 수인의 지배인에게 공동으로 대리권을 행사하게 할 수 있고, 이 경우 지배인 1인에 대한 의사표시만으로도 영업주에게 효력이 있다.|
26|ㄷ|X|표현지배인은 재판 외 행위에 관하여 지배인과 동일한 권한이 있는 것으로 보지만, 재판상 행위에 관하여까지 지배인과 동일하게 보지는 않는다.|표현지배인의 동일권한을 재판상 행위에까지 인정한 부분
26|ㄹ|O|지배인의 행위가 영업주의 영업에 관한 것인지는 지배인의 주관적 의사와 관계없이 행위의 객관적 성질에 따라 추상적으로 판단한다.|
26|ㅁ|O|상법상 지배인에 관한 규정은 소상인에게 적용되지 않는다.|
27|①|O|일반적으로 보험모집인은 독자적으로 보험자를 대리하여 보험계약을 체결하거나 고지·통지를 수령할 권한이 없다.|
27|②|O|보험자가 생명보험계약 청약서에서 다른 보험계약 존재 여부를 질문하였다면 그 존재 여부는 고지의무 대상이 될 수 있다.|
27|③|O|다른 보험계약 존재 여부의 고지의무 위반으로 해지하려면 보험자는 보험계약자 또는 피보험자의 인식이나 중대한 과실을 증명하여야 한다.|
27|④|X|중복보험 체결 사실이 있다는 사정만으로 그 사실이 상법 제651조의 고지의무 대상인 중요한 사항이 되는 것은 아니다.|중복보험 통지의무 규정 때문에 중복보험 체결 사실이 곧 고지의무 대상이 된다고 한 부분
27|⑤|O|보험자가 약관 명시·설명의무를 위반하면 보험계약자 등이 그 약관상 고지의무를 위반했더라도 이를 이유로 보험계약을 해지할 수 없다.|
28|①|O|지급제시기간 경과로 수표상 권리가 소멸되어 취득하는 자기앞수표 이득상환청구권은 지명채권에 해당한다.|
28|②|X|자기앞수표 이득상환청구권 양도는 확정일자 있는 양도통지나 승낙이 없으면 압류채권자 등 제3자에게 대항할 수 없다.|확정일자 있는 통지나 승낙 없이도 압류채권자 등에게 대항할 수 있다고 한 부분
28|③|O|지급제시기간이 지난 자기앞수표는 이득상환청구권이 화체된 유가증권이 아니라 그 권리 취득을 뒷받침하는 증거증권의 의미를 가진다.|
28|④|O|일부 어음요건이 백지인 약속어음 소지인이 백지를 보충하지 않은 상태에서 어음금을 청구하여도 어음상 청구권의 소멸시효 중단 효과가 있다.|
28|⑤|O|만기를 백지로 하여 발행된 약속어음의 백지보충권 소멸시효기간은 보충권을 행사할 수 있는 때부터 3년으로 본다.|
29|①|O|일반적으로 건설회사 현장소장에게 회사 부담의 채무보증·채무인수 또는 공사 관련 채권의 무상포기 권한이 위임되어 있다고 볼 수 없다.|
29|②|O|부분적 포괄대리권을 가진 상업사용인이 권한 밖 행위를 한 경우 영업주 책임에는 민법상 표현대리 법리에 따른 정당한 이유가 필요하다.|
29|③|X|상무이사라는 지위를 가진 사람도 회사의 사용인 지위에서 상법 제15조의 부분적 포괄대리권을 가질 수 있다.|상무이사는 회사의 기관이므로 부분적 포괄대리권을 가진 사용인을 겸임할 수 없다고 한 부분
29|④|O|일반적으로 주식회사의 경리부장에게 경리사무 일체에 관한 권한은 인정되지만 독자적인 자금차용 권한까지 위임되었다고 볼 수 없다.|
29|⑤|O|부분적 포괄대리권을 가진 상업사용인이 권한 범위 내에서 권한을 남용한 경우에도 상대방이 진의를 알았거나 알 수 있었을 때에는 영업주에게 무효가 될 수 있다.|
30|ㄱ|X|주주총회결의 취소판결에는 소급효가 있으므로, 취소된 이사선임결의에 기초한 이사회에서 선정된 대표이사의 행위가 당연히 유효하다고 할 수 없다.|주주총회결의 취소판결이 장래효만 가져 취소판결 확정 전 대표이사의 행위가 유효하다고 한 부분
30|ㄴ|X|대표이사 직무집행정지 및 직무대행자선임 가처분 후 새 대표이사가 선임되더라도 선임결의의 적법 여부와 관계없이 대표권이 생기는 것은 아니다.|새 대표이사가 선임결의의 적법 여부와 관계없이 대표이사 권한을 가진다고 한 부분
30|ㄷ|O|회사설립무효판결과 주주총회결의 취소판결은 제3자에 대하여도 효력이 미친다.|
30|ㄹ|O|동일한 결의에 관한 부존재확인의 소가 제소기간 내 제기되었다면, 같은 하자를 원인으로 한 결의취소소송 변경·추가는 제소기간을 준수한 것으로 볼 수 있다.|
31|ㄱ|X|이사가 상법 제398조의 사전 이사회 승인 없이 자기거래를 하여 무효인 경우, 특별한 사정이 없는 한 사후 이사회 승인만으로 그 거래가 유효하게 되지는 않는다.|사후 이사회 승인을 받으면 무효인 자기거래가 유효로 된다고 한 부분
31|ㄴ|X|대표이사의 이사회 결의 없는 대외적 거래는 상대방이 이사회 결의가 없음을 알았거나 중대한 과실로 알지 못한 경우에 무효가 될 수 있다.|상대방이 단순히 이사회 결의가 없음을 알 수 있었던 경우까지 거래가 무효라고 한 부분
31|ㄷ|O|대표권 제한을 알지 못한 제3자는 선의 외에 무과실까지 필요하지 않지만, 중대한 과실이 있으면 그 거래행위가 무효가 될 수 있다.|
31|ㄹ|X|일반적인 주식회사의 대표이사가 회사를 대표하여 파산신청을 하는 것은 중요한 업무에 해당하므로 원칙적으로 이사회 결의가 필요하다.|대표이사가 회사를 대표하여 파산신청을 할 때 원칙적으로 이사회 결의가 필요하지 않다고 한 부분
31|ㅁ|O|이사의 자기거래에 대한 이사회 승인은 이사 3분의 2 이상의 수로써 하여야 한다.|
32|①|O|채권매매거래 위탁계약은 권한 있는 직원이 위탁 의사로 고객에게 금원이나 채권을 수령하면 성립하고, 그 뒤 금원수납 처리는 성립에 영향을 주지 않는다.|
32|②|O|위탁매매인이 위탁매매로 취득한 채권을 자기 채무 담보로 양도하면 특별한 사정이 없는 한 위탁자에 대하여 효력이 없다.|
32|③|O|위탁매매는 자기 명의로 타인의 계산에 의하여 물품을 매수 또는 매도하고 보수를 받는 거래로서 명의와 계산의 분리를 본질로 한다.|
32|④|X|위탁자의 위탁매매인에 대한 이득상환청구권이나 이행담보책임 이행청구권은 민법 제163조 제6호의 3년 단기소멸시효 대상이 아니다.|위탁자의 관련 청구권을 상인이 판매한 상품의 대가로 보아 3년 단기소멸시효가 적용된다고 한 부분
32|⑤|O|위탁매매인이 위탁자로부터 받은 물건·유가증권이나 위탁매매로 취득한 물건·유가증권·채권은 위탁자와 위탁매매인 또는 그 채권자 사이에서는 위탁자의 소유 또는 채권으로 본다.|
33|①|O|청산인 직무대행자가 주주 요구에 따라 소집한 주주총회에서 회사계속과 새 이사·감사 선임 결의가 있어도 그 결의만으로 청산인 직무대행자의 권한이 당연히 소멸하지는 않는다.|
33|②|O|공동출자 동업계약에 따라 주식회사가 설립되어 실체를 갖추면 상법상 청산절차가 이루어지지 않는 한 일방 당사자가 잔여재산 분배를 받을 수 없다.|
33|③|O|의제해산·청산종결 회사라도 권리관계 정리 필요가 있으면 해산 당시 이사 등이 청산인이 되고, 청산인이 없으면 법원이 이해관계인 청구로 청산인을 선임할 수 있다.|
33|④|O|청산법인에서는 이사에 갈음하여 청산인만이 청산사무를 집행하고 회사를 대표하는 기관이 된다.|
33|⑤|X|법원의 해산판결 확정과 적법한 청산인 선임·등기가 이루어진 경우 해산 당시 이사는 해산판결 전 회사 결의의 무효확인을 구할 법률상 이익이 없다.|해산판결 전 회사 결의 무효확인의 법률상 이익이 있다고 한 부분
34|ㄱ|X|주식회사의 주식 액면금액은 균일하여야 하므로 같은 회사 발행주식에 서로 다른 액면가를 둘 수 없다.|이미 액면가 5,000원 주식이 있는 회사가 액면가 10,000원 신주를 발행할 수 있다고 한 부분
34|ㄴ|X|주식회사는 배당가능이익이 없으면 약정상 주식매수청구권 행사에 따라 자기주식을 취득할 수 없다.|배당가능이익이 없는데도 약정상 주식매수청구권 행사에 따라 자기주식을 취득할 수 있다고 한 부분
34|ㄷ|O|주식회사는 주주로부터 자기주식을 무상으로 양수할 수 있다.|
34|ㄹ|X|주식회사가 취득한 자기주식은 의결권이 없으므로 대표이사가 주주총회에서 그 자기주식으로 의결권을 행사할 수 없다.|회사가 취득한 자기주식으로 의결권을 행사할 수 있다고 한 부분
34|ㅁ|O|공유주식의 권리행사자가 지정되지 않은 상황에서는 회사가 주소와 연락처를 아는 공유자에게 주주권 행사 관련 통지를 할 수 있다.|
35|①|X|약속어음 소지인이 자기의 전자에게 어음을 교부하여 전자가 패소한 뒤 다시 어음을 받아 청구하면, 발행인은 전자에 대한 인적항변으로 그 소지인에게 대항할 수 있다.|어음발행인이 전자에 대한 인적항변으로 다시 어음을 받은 소지인에게 대항할 수 없다고 한 부분
35|②|O|어음면상 국내어음으로 인정되면 발행지 기재가 없다는 사정만으로 무효의 어음이 되지는 않는다.|
35|③|O|어음발행인이 사고신고담보금을 지급은행에 예치하였다는 사정만으로 어음소지인에 대한 변제공탁의 효력이 생기지는 않는다.|
35|④|O|어음발행인 회생절차에서 어음상 권리가 회생계획에 따라 변경되어도 어음소지인의 사고신고담보금에 대한 권리에는 영향이 없다.|
35|⑤|O|사고신고담보금에 대한 채권압류 및 전부명령 송달만으로는 사고신고담보금 처리약정상 소송계속 중임을 증명하는 서면이 제출된 것으로 볼 수 없다.|
36|①|O|주식매수선택권은 회사에 기여하거나 기여할 수 있는 임직원에게 장래 주식매수 이득을 유인으로 직무충실을 유도하는 성과보상제도이다.|
36|②|X|주식매수선택권 부여에 관한 주주총회결의는 회사의 의사결정절차이고, 특정인에 대한 구체적 내용은 주주총회결의만으로 정해지는 것이 아니다.|주주총회결의가 의사결정절차에 그치지 않아 구체적 내용이 그 결의로 정해진다고 한 부분
36|③|O|귀책사유 없이 퇴임·퇴직하였더라도 퇴임·퇴직일까지 2년 이상 재임 또는 재직 요건을 충족하지 못하면 주식매수선택권을 행사할 수 없다.|
36|④|O|회사는 정관의 기본취지와 핵심내용을 해치지 않는 범위에서 주주총회결의와 개별계약으로 주식매수선택권 행사기간을 정할 수 있다.|
36|⑤|O|주식매수선택권 계약에서 행사기간 등을 일부 변경·조정하더라도 이해관계인 균형을 해치지 않고 본질적 내용을 훼손하지 않으면 유효할 수 있다.|
37|①|O|선박대리점이 운송물 점유를 이전받기 전에 실제 운송인이나 터미널 운영자의 과실로 화물이 소훼되면 선박대리점에게 운송물 멸실 불법행위책임을 물을 수 없다.|
37|②|X|화물 적부가 독립된 하역업자나 송하인의 지시에 따라 이루어진 경우에도 운송인은 손해방지를 위한 적절한 주의의무를 부담할 수 있다.|독립된 하역업자나 송하인의 지시가 있으면 운송인의 적부 관련 주의의무가 없다고 한 부분
37|③|O|운송주선인은 하주나 운송인의 대리인이 될 수 있고, 위탁자의 이름으로 운송계약을 체결하여도 운송주선인의 지위가 당연히 사라지지 않는다.|
37|④|O|운송주선인이 운송인의 지위를 취득하지 않는 한 운송인의 대리인으로 운송계약을 체결하였더라도 운송의뢰인에 대해서는 여전히 운송주선인이다.|
37|⑤|O|운송 관련 업무 의뢰에서 운송 인수 여부가 명확하지 않으면 당사자 의사와 선하증권 명의, 운임 지급형태 등 제반사정을 종합하여 판단한다.|
38|①|X|합자조합의 업무집행조합원은 다른 조합원 전원의 동의를 받지 않으면 지분 전부 또는 일부를 타인에게 양도하지 못한다.|업무집행조합원이 다른 조합원 과반수 동의만으로 지분을 양도할 수 있다고 한 부분
38|②|O|합자조합에서 둘 이상의 업무집행조합원이 있고 조합계약에 다른 정함이 없으면, 다른 업무집행조합원의 이의가 있는 업무집행행위는 중지하고 업무집행조합원 과반수 결의에 따라야 한다.|
38|③|X|익명조합원은 금전이나 그 밖의 재산으로 출자할 수 있을 뿐 신용이나 노무를 출자할 수 없다.|익명조합원이 신용이나 노무를 출자할 수 있다고 한 부분
38|④|X|영업 이익 여부와 관계없이 시설투자자에게 정기적으로 일정액을 지급하기로 한 동업관계는 상법상 익명조합으로 보기 어렵다.|이익 여부와 무관한 정기 지급 약정을 익명조합으로 본 부분
38|⑤|X|익명조합원은 손실로 출자금이 감소한 경우 그 손실을 보전한 뒤가 아니면 이익배당을 청구하지 못한다.|손실을 채우지 않고도 이익배당을 청구할 수 있다고 한 부분
39|ㄱ|O|주주 차등취급이 법률상 절차와 방식에 따르거나 정당화할 특별한 사정이 있으면 주주평등원칙에 반하지 않을 수 있다.|
39|ㄴ|X|일부 주주에게 사전동의권을 부여한 약정이 예외적으로 허용된다면, 그 위반으로 인한 손해배상 또는 이행확보 약정도 곧바로 주주평등원칙 위반이 되는 것은 아니다.|사전동의권 위반 손해배상 약정이 투하자본 회수를 절대 보장하여 주주평등원칙에 위배된다고 단정한 부분
39|ㄷ|X|주주평등의 원칙은 원칙적으로 회사와 주주 사이의 법률관계에 적용되고, 다른 주주나 이사 개인 사이의 법률관계에 직접 적용되는 것은 아니다.|주주와 다른 주주 또는 이사 개인 사이 법률관계에 주주평등원칙을 직접 적용할 수 있다고 한 부분
39|ㄹ|O|주주가 다른 주주나 이사 개인과 체결한 계약의 내용은 계약 형식·동기·목적·당사자 의사 등을 종합하여 일반 계약해석 원칙에 따라 해석할 수 있다.|
40|①|O|상행위로 인하여 생긴 채권을 담보하기 위한 질권설정계약에는 유질약정을 할 수 있다.|
40|②|O|유질약정이 포함된 질권설정계약에서는 질권 실행방법이나 절차가 원칙적으로 질권설정계약에서 정한 바에 따른다.|
40|③|O|상사유치권 배제특약은 묵시적 약정으로도 가능하다.|
40|④|X|상법 제59조의 유질약정이 유효하기 위하여 질권설정자와 질권자가 모두 상인이어야 하는 것은 아니다.|유질약정의 유효요건으로 질권설정자와 질권자 쌍방이 모두 상인이어야 한다고 한 부분
40|⑤|O|일방적 상행위로 생긴 채권을 담보하기 위한 질권에도 상법 제59조의 유질약정 규정이 적용될 수 있다.|
41|ㄱ|X|손해보험에서 당사자 사이에 보험가액을 정하지 않은 때에는 원칙적으로 사고 발생 때와 곳의 가액을 보험가액으로 한다.|보험가액을 정하지 않은 때 보험계약 체결시 가액을 보험가액으로 한다고 한 부분
41|ㄴ|O|초과보험인지 여부는 원칙적으로 보험계약 당시의 가액을 기준으로 판단한다.|
41|ㄷ|O|보험계약자의 사기로 초과보험계약이 체결되면 보험계약은 무효이나, 보험자는 그 사실을 안 때까지의 보험료를 청구할 수 있다.|
41|ㄹ|O|일부보험에서는 원칙적으로 보험금액의 보험가액에 대한 비율에 따라 보상하지만, 다른 약정이 있으면 보험금액 한도에서 손해를 보상할 수 있다.|
42|①|O|영업양도는 일정한 영업목적에 따라 조직화된 인적·물적 조직을 동일성을 유지하면서 일체로 이전하는 것으로, 영업 일부의 양도도 가능하다.|
42|②|X|영업재산 전부를 양도하였더라도 그 조직을 해체하여 양도하면 영업양도로 볼 수 없다.|영업재산 전부를 조직 해체 방식으로 양도해도 영업양도로 볼 수 있다고 한 부분
42|③|X|영업양도가 이루어지면 특별한 사정이 없는 한 해당 근로자들의 근로관계는 양수 기업에 포괄적으로 승계된다.|별도 특약이 있어야만 근로관계가 포괄승계된다고 한 부분
42|④|X|영업양도에서 다른 약정이 없으면 양도인은 10년간 동일하거나 인접한 특별시·광역시·시·군에서 동종영업을 하지 못한다.|다른 약정이 없는 경우 경업금지기간을 5년으로 본 부분
42|⑤|X|영업양도인이 동종영업을 하지 않을 것을 약정한 경우 그 약정은 20년을 넘지 않는 범위에서 효력이 있다.|경업금지약정의 유효기간을 10년을 초과하지 않는 범위로 본 부분
43|①|O|대리점계약이라는 명칭의 계약을 체결하였다는 사정만으로 곧바로 상법상 대리상이 되는 것은 아니다.|
43|②|O|내적조합과 익명조합의 구별은 공동사업 여부, 업무검사권 등 업무 관여 정도, 재산 처분·변경의 동의 필요성 등을 종합하여 판단한다.|
43|③|O|해상운송화물이 통관을 위하여 보세창고에 입고되면 운송인과 보세창고업자 사이에 해상운송화물에 관한 묵시적 임치계약이 성립할 수 있다.|
43|④|O|보세창고업자는 운송인의 이행보조자로서 정당한 수령인인 수하인 또는 그 지정자에게 화물을 인도할 의무를 부담한다.|
43|⑤|X|보세창고업자의 화물인도 관련 주의의무는 선하증권을 취득하지 못한 신용장개설은행에 대하여까지 당연히 부담되는 것은 아니다.|보세창고업자가 선하증권을 취득하지 못한 신용장개설은행에 대해서도 주의의무를 부담한다고 한 부분
44|①|O|비상장 주식회사가 발행할 신주의 종류와 수에 관하여 정관에 규정이 없으면 이사회가 이를 결정한다.|
44|②|O|신주의 인수인이 납입기일에 납입 또는 현물출자를 이행하지 않으면 그 권리를 잃는다.|
44|③|X|신주의 인수인은 납입 또는 현물출자의 이행을 하면 납입기일 다음 날부터 주주의 권리의무를 가진다.|신주인수인이 주권을 교부받은 날부터 주주의 권리의무를 가진다고 한 부분
44|④|O|신주인수권증서를 상실한 자는 주식청약서로 청약할 수 있으나, 신주인수권증서에 의한 청약이 있으면 그 청약은 효력을 잃는다.|
44|⑤|O|신주인수권증서가 발행되지 않은 경우 신주인수권 양도의 제3자 대항요건은 확정일자 있는 증서에 의한 양도통지 또는 회사 승낙으로 본다.|
45|①|O|주식회사 이사의 회사에 대한 상법 제399조 제1항 손해배상책임은 위임관계로 인한 채무불이행책임이다.|
45|②|X|이사의 회사에 대한 손해배상채무는 특별한 사정이 없는 한 회사가 이행청구를 한 때부터 지체책임이 발생한다.|임무해태로 손해가 발생한 시점부터 곧바로 지체책임을 진다고 한 부분
45|③|O|이사가 임무수행 과정에서 법령을 위반한 경우에는 원칙적으로 경영판단의 원칙이 적용되지 않는다.|
45|④|O|상법 제401조에 따른 이사의 제3자에 대한 손해배상책임의 소멸시효기간은 10년이다.|
45|⑤|O|이사의 법령·정관 위반행위나 임무해태가 이사회 결의에 따른 것이면 그 결의에 찬성한 이사도 연대하여 회사에 손해를 배상할 책임을 진다.|
46|①|O|상인은 영업상의 재산과 손익 상황을 명백히 하기 위하여 회계장부와 대차대조표를 작성하여야 한다.|
46|②|O|상인은 상업장부와 영업에 관한 중요서류를 10년간 보존하고, 전표 또는 유사서류는 5년간 보존하며, 상업장부 보존기간은 장부 폐쇄일부터 기산한다.|
46|③|O|상법상 등기할 사항을 등기하지 않으면 선의의 제3자에게 대항하지 못하고, 등기 후에도 정당한 사유로 알지 못한 제3자에게는 대항하지 못한다.|
46|④|X|법인등기부에 이사 또는 감사로 등재된 사람은 특별한 사정이 없는 한 적법하게 선임된 이사 또는 감사로 사실상 추정된다.|등기된 이사 또는 감사가 적법하게 선임된 것으로 추정되지 않는다고 한 부분
46|⑤|O|회사등기에는 공신력이 인정되지 않으므로 불실등기를 믿고 합자회사 사원지분을 양수하였다는 사정만으로 그 지분을 취득하지는 못한다.|
47|①|X|보험계약 체결 전에 보험사고가 이미 발생하였더라도 당사자 쌍방과 피보험자가 이를 알지 못한 경우에는 그 사정만으로 보험계약이 무효가 되지 않는다.|당사자 쌍방과 피보험자가 몰랐더라도 이미 발생한 보험사고에 관한 보험계약은 무효라고 한 부분
47|②|O|보험자가 위험변경·증가 통지를 받고 보험계약을 해지하는 경우 미경과기간 보험료를 반환하도록 정한 보험약관은 유효하다.|
47|③|O|보험회사의 설명의무 위반으로 고객이 중요사항에 착오를 일으켜 보험계약을 체결한 경우 그 착오는 보험계약 내용의 중요부분에 관한 것일 수 있다.|
47|④|O|거래상 일반적이고 공통되어 보험계약자가 예상할 수 있거나 법령 내용을 반복하는 정도의 사항까지 보험자에게 설명의무가 있는 것은 아니다.|
47|⑤|O|통신판매 상해보험에서 약관 개요와 면책사고 확인 안내문·청약서를 우송한 것만으로는 면책약관 설명의무를 다한 것으로 볼 수 없다.|
48|①|O|명의대여 영업에서 실제 영업자인 명의차용자의 채무승인으로 인한 시효중단 효력은 특별한 사정이 없는 한 명의대여자에게 미치지 않는다.|
48|②|O|영업양도 후 채권자가 영업양도인을 상대로 확정판결을 받았더라도 시효중단이나 시효연장의 효과는 상호속용 영업양수인에게 미치지 않는다.|
48|③|X|창고업자가 선하증권이나 화물인도지시서와 상환하지 않고 임치물을 인도한 경우, 소유자의 불법행위 손해배상청구에는 상법 제166조 제1항의 1년 소멸시효가 적용되지 않는다.|소유자의 불법행위 손해배상청구에 창고업자의 1년 소멸시효 항변을 인정한 부분
48|④|O|운송주선인이 자기 이름으로 운송계약을 체결한 경우 운송주선인에 대한 운송인의 채권은 1년의 단기소멸시효에 걸린다.|
48|⑤|O|기존회사가 채무면탈을 위해 실질적으로 동일한 신설회사를 설립한 경우, 신설회사가 별도 시효완성을 주장하는 것은 허용되지 않을 수 있다.|
49|①|X|주주총회에서 선임된 이사는 회사와 명시적 또는 묵시적 보수약정이 있으면 실질적 업무를 수행하지 않았다는 사정만으로 보수청구권이 당연히 부정되지는 않는다.|이사로서 실질 업무를 수행하지 않으면 주주총회결의에서 정한 보수를 청구할 수 없다고 한 부분
49|②|O|이사가 직무내용과 회사 재무상황 등에 비추어 현저히 과다한 보수지급기준을 마련하여 주주총회결의를 성립시킨 경우 회사에 대한 배임행위가 될 수 있다.|
49|③|O|정관 등이 이사 퇴직금 액수를 주주총회결의로 정한다고만 정한 경우 퇴직금 중간정산 결의가 없으면 중간정산금청구권을 행사할 수 없다.|
49|④|O|정관이 퇴직금 지급규정과 함께 퇴직 이사의 퇴직금 하한을 구체적으로 정하였다면 회사는 그 하한 범위 안의 퇴직금 지급을 거절할 수 없다.|
49|⑤|O|이사 해임 시 퇴직위로금과 별도로 해직보상금을 지급하기로 한 약정에도 상법 제388조가 준용 또는 유추적용될 수 있다.|
50|①|O|주식회사 간 흡수합병에서 소멸회사 총주주의 동의가 있거나 존속회사가 소멸회사 발행주식총수 90퍼센트 이상을 소유하면 소멸회사 주주총회 승인을 이사회 승인으로 갈음할 수 있다.|
50|②|O|소규모합병에서는 존속회사의 합병계약서에 주주총회 승인을 얻지 않고 합병한다는 뜻을 기재하여야 한다.|
50|③|O|소규모합병에서 존속회사는 합병계약서 작성일부터 2주 내에 소멸회사 상호·본점 소재지, 합병일, 주주총회 승인 없는 합병이라는 뜻을 공고하거나 주주에게 통지하여야 한다.|
50|④|X|소규모합병에서는 반대주주의 주식매수청구권이 배제되지만, 간이합병에서는 반대주주의 주식매수청구권이 인정될 수 있다.|소규모합병과 간이합병 모두에서 반대주주의 주식매수청구권이 인정되지 않는다고 한 부분
50|⑤|O|소멸회사 주주에게 지급할 금액이나 재산 가액이 존속회사 최종대차대조표상 순자산액의 5퍼센트를 초과하면 주주총회 특별결의를 거쳐야 한다.|
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def basis(no: int) -> tuple[str, str, str]:
    topic = TOPICS[no]
    return ("상법+판례" if no not in {28, 35} else "어음법·수표법+판례", f"{topic} 관련 조문 및 대법원 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.find("【상 법 30문】")
    if start == -1:
        raise ValueError("cannot locate 2024 commercial-law section")
    end = text.find("【 제2과목 50문제 】", start)
    section = text[start:end if end != -1 else len(text)]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 21 <= int(m.group(1)) <= 50]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} commercial-law questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        blocks[no] = section[match.start():end_pos]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    first_by_label: dict[str, re.Match[str]] = {}
    for marker in re.finditer(r"[①②③④⑤]", block):
        label = marker.group(0)
        first_by_label.setdefault(label, marker)
        if set(first_by_label) == {"①", "②", "③", "④", "⑤"}:
            break
    if set(first_by_label) != {"①", "②", "③", "④", "⑤"}:
        raise ValueError("cannot split five choices")
    ordered = [first_by_label[label] for label in ["①", "②", "③", "④", "⑤"]]
    out: dict[str, str] = {}
    for idx, marker in enumerate(ordered):
        start = marker.end()
        end = ordered[idx + 1].start() if idx + 1 < len(ordered) else len(block)
        statement = re.split(r"\s*제1과목\s*①책형\s*전체", block[start:end])[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    choice_start = re.search(r"[①②③④⑤]", block)
    stem = block[:choice_start.start()] if choice_start else block
    markers = list(re.finditer(r"([ㄱㄴㄷㄹㅁ])\.", stem))
    if not markers:
        raise ValueError("cannot split box statements")
    out: dict[str, str] = {}
    for idx, marker in enumerate(markers):
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(stem)
        out[marker.group(1)] = normalize_raw(stem[marker.end():end])
    return out


def raw_statement_map() -> dict[tuple[int, str], str]:
    blocks = extract_question_blocks()
    raw: dict[tuple[int, str], str] = {}
    needed = defaultdict(list)
    for row in parse_rep_rows():
        needed[row["no"]].append(row["label"])
    for no, labels in needed.items():
        split = split_box_units(blocks[no]) if no in BOX_QUESTIONS else split_choice_units(blocks[no])
        for label in labels:
            if label not in split:
                raise ValueError(f"missing raw statement for q{no} {label}")
            raw[(no, label)] = split[label]
    return raw


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
                "unitType": "box" if label in {"ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ"} else "choice",
                "sourceQuestionType": QUESTION_TYPES.get(no_int, "single-best-false"),
                "officialAnswer": OFFICIAL_ANSWERS[no_int],
            }
        )
    return rows


def grouped_units() -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    raw = raw_statement_map()
    for row in parse_rep_rows():
        row = dict(row)
        row["raw"] = raw[(row["no"], row["label"])]
        row["basisType"], row["basisRef"], row["why"] = basis(row["no"])
        grouped[row["no"]].append(row)
    return grouped


def build_source() -> dict:
    questions = []
    for no, rows in sorted(grouped_units().items()):
        questions.append(
            {
                "qid": f"{YEAR}-g1-commercial-law-{no:02d}",
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 1차",
                "group": GROUP,
                "groupLabel": "제1과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": rows[0]["sourceQuestionType"],
                "officialAnswer": rows[0]["officialAnswer"],
                "units": [
                    {
                        "unitId": f"{YEAR}-g1-commercial-law-{no:02d}-{row['code']}",
                        "unitType": row["unitType"],
                        "label": row["label"],
                        "rawStatement": row["raw"],
                        "originalVerdict": row["sourceVerdict"],
                    }
                    for row in rows
                ],
            }
        )
    return {
        "schema": "legal-scrivener/source-questions/v1",
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


def build_queue(source: dict) -> dict:
    items = []
    for question in source["questions"]:
        for unit in question["units"]:
            items.append(
                {
                    "unitId": unit["unitId"],
                    "sourceFamily": source["sourceFamily"],
                    "source": question["sourceLabel"],
                    "examId": EXAM_ID,
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "no": question["no"],
                    "unitType": unit["unitType"],
                    "unitLabel": unit["label"],
                    "sourceQuestionType": question["type"],
                    "officialQuestionAnswer": question["officialAnswer"],
                    "rawStatement": unit["rawStatement"],
                    "originalVerdict": unit["originalVerdict"],
                }
            )
    return {
        "schema": "legal-scrivener/atom-queue/v1",
        "sourceFamily": source["sourceFamily"],
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "source": str(SOURCE_PATH),
        "itemCount": len(items),
        "items": items,
    }


def build_atoms(queue: dict) -> list[dict]:
    rows_by_key = {(row["no"], row["label"]): row for row in parse_rep_rows()}
    checked_at = today()
    atoms = []
    for item in queue["items"]:
        row = rows_by_key[(item["no"], item["unitLabel"])]
        basis_type, basis_ref, why = basis(item["no"])
        atom = {
            "atomId": f"bupmusa-2024-commercial-law-q{item['no']:02d}-{row['code']}",
            "sourceUnitId": item["unitId"],
            "sourceFamily": item["sourceFamily"],
            "source": item["source"],
            "year": item["year"],
            "round": item["round"],
            "subject": SUBJECT_NAME,
            "no": item["no"],
            "unitType": item["unitType"],
            "unitLabel": item["unitLabel"],
            "sourceQuestionType": item["sourceQuestionType"],
            "officialQuestionAnswer": item["officialQuestionAnswer"],
            "sourceVerdict": row["sourceVerdict"],
            "currentVerdict": "O",
            "rep": row["rep"],
            "a": "O",
            "basisType": basis_type,
            "basisRef": basis_ref,
            "why": why,
            "sourceStatement": item["rawStatement"],
            "sourceTrap": row["trap"] if row["sourceVerdict"] == "X" else None,
            "xDependsOn": row["rep"] if row["sourceVerdict"] == "X" else None,
            "reviewedAt": checked_at,
            "currentLawCheckedAt": checked_at,
        }
        atoms.append(atom)
    validate(atoms)
    return atoms


def validate(atoms: list[dict]) -> None:
    if len(atoms) != EXPECTED_ATOM_COUNT:
        raise ValueError(f"expected {EXPECTED_ATOM_COUNT} atoms, got {len(atoms)}")
    if len({atom["atomId"] for atom in atoms}) != len(atoms):
        raise ValueError("duplicate atomId")
    counts = Counter(atom["no"] for atom in atoms)
    if set(counts) != set(range(21, 51)):
        raise ValueError(f"question coverage mismatch: {sorted(counts)}")
    banned = ["?", "？", "①", "②", "③", "④", "⑤", "위➀", "다음 설명", "옳은 것은", "옳지 않은 것은"]
    for atom in atoms:
        rep = atom["rep"]
        if any(pattern in rep for pattern in banned):
            raise ValueError(f"non-atomic wording in {atom['atomId']}: {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in {atom['atomId']}: {rep}")
        if len(rep) >= 20 and " " not in rep:
            raise ValueError(f"spacing suspect in {atom['atomId']}: {rep}")
        if atom["sourceVerdict"] == "X" and (not atom["sourceTrap"] or not atom["xDependsOn"]):
            raise ValueError(f"X source must have trap/dependency: {atom['atomId']}")
        if atom["sourceVerdict"] == "O" and atom["sourceTrap"] is not None:
            raise ValueError(f"O source must not have trap: {atom['atomId']}")
        if atom["currentVerdict"] != "O" or atom["a"] != "O":
            raise ValueError(f"completed atom must be normalized to O: {atom['atomId']}")


def update_subject_index(atom_count: int) -> None:
    if SUBJECT_INDEX_PATH.exists():
        index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
    else:
        index = {"schema": "legal-scrivener/subject-index/v1", "sourceFamily": "법무사시험", "updatedAt": today(), "examId": EXAM_ID, "year": YEAR, "round": ROUND, "subjects": {}}
    subjects = index.setdefault("subjects", {})
    subjects[SUBJECT_NAME] = {
        "source": str(SOURCE_PATH),
        "atomQueue": str(QUEUE_PATH),
        "completedAtoms": str(OUT_PATH),
        "questionCount": QUESTION_COUNT,
        "atomQueueItemCount": atom_count,
        "completedAtomCount": atom_count,
        "completedAtomsUpdatedAt": today(),
    }
    index["updatedAt"] = today()
    SUBJECT_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build() -> Path:
    source = build_source()
    queue = build_queue(source)
    atoms = build_atoms(queue)
    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    OUT_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_subject_index(len(atoms))
    return OUT_PATH


def main() -> None:
    out = build()
    data = json.loads(out.read_text(encoding="utf-8"))
    by_verdict = Counter(item["sourceVerdict"] for item in data["items"])
    by_unit = Counter(item["unitType"] for item in data["items"])
    print(f"atoms={out}")
    print(f"atomCount={data['atomCount']}")
    print("sourceVerdict=" + ", ".join(f"{key}:{value}" for key, value in sorted(by_verdict.items())))
    print("unitType=" + ", ".join(f"{key}:{value}" for key, value in sorted(by_unit.items())))
    for sample in data["items"][:5]:
        print(f"{sample['atomId']} {sample['rep']}")


if __name__ == "__main__":
    main()
