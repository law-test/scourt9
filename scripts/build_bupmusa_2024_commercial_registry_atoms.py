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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_상업등기법_비송사건절차법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_상업등기법_비송사건절차법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_상업등기법_비송사건절차법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "상업등기법 및 비송사건절차법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 3
QUESTION_COUNT = 15
EXPECTED_ATOM_COUNT = 75

LEGAL_SOURCES = [
    {"title": "상업등기법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상업등기법"},
    {"title": "상업등기규칙", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상업등기규칙"},
    {"title": "비송사건절차법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/비송사건절차법"},
    {"title": "상법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/상법"},
    {"title": "2024 법무사 상업등기법 및 비송사건절차법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881278"},
    {"title": "30회 법무사시험 상업등기법 및 비송사건절차법 해설", "publisher": "법무사단기 공개 해설 PDF", "url": "https://file-bbs.conects.com/documents/files/287497/download?user_id="},
]

OFFICIAL_ANSWERS = {
    36: "⑤",
    37: "②",
    38: "③",
    39: "①",
    40: "②",
    41: "④",
    42: "④",
    43: "②",
    44: "⑤",
    45: "①",
    46: "④",
    47: "③",
    48: "⑤",
    49: "③",
    50: "④",
}

QUESTION_TYPES = {
    45: "single-best-true",
    47: "single-best-true",
    48: "single-best-true",
    49: "single-best-true",
    50: "single-best-true",
}

BASIS = {
    36: ("상법+상업등기예규", "상법 제363조 제4항·제6항, 상업등기선례 제201809-3호 및 투자조합 서면결의 관련 선례", "소규모 주식회사의 서면결의·서면동의에서 의사록, 주주명부, 인감, 투자조합의 업무집행조합원 첨부서면을 판단한다."),
    37: ("채무자회생법+상업등기예규", "채무자 회생 및 파산에 관한 법률, 회사의 회생·파산 관련 상업등기예규", "회생계획 수행, 관리인·파산관재인 등기, 파산 중 임원등기와 본점이전등기를 판단한다."),
    38: ("상법+상업등기예규", "상법 제418조, 제421조, 제422조, 신주발행 변경등기 관련 예규·선례", "신주발행에서 현물출자, 실권주 재배정, 주금상계와 첨부정보를 판단한다."),
    39: ("상법+상업등기규칙", "상법상 유한회사 설립·증자·본점이전 규정 및 상업등기규칙", "유한회사의 공고방법, 특별결의, 정관인증, 자본금 증가와 본점이전 등기를 판단한다."),
    40: ("상법+상업등기예규", "상법상 사채·전환사채·신주인수권부사채 등기와 관련 예규", "사채 모집 제한, 조건부자본증권 등기, 전환청구서, 사채상환완료증명 첨부정보를 판단한다."),
    41: ("상법+비송사건절차법", "상법 제635조, 비송사건절차법상 과태료재판 및 과태사항 통지 예규", "등기의무해태에 따른 과태사항 통지와 과태료재판의 관할, 즉시항고, 정당사유 판단을 정리한다."),
    42: ("상법+상업등기법", "상법 제37조·제38조, 상업등기법 및 법인등기 특례 규정", "상업등기사항의 변경등기, 지배인 등기, 외국회사 등기, 등기의 대항력과 공신력 부재를 판단한다."),
    43: ("상법+상업등기예규", "상법 제438조·제439조, 자본금 감소 변경등기 관련 예규", "자본금 감소의 결의요건, 채권자보호절차, 주권제출공고, 액면가와 발행예정주식총수 변경을 판단한다."),
    44: ("상법+상업등기예규", "상법 제368조 제4항·제386조, 대표이사 직무대행자 관련 판례·예규", "주식회사 이사, 퇴임등기 기간, 직무대행자의 주주총회 소집과 특별이해관계인의 의결권을 판단한다."),
    45: ("상법+상업등기규칙", "상법 제176조·제520조의2, 해산 및 청산인 등기 관련 상업등기규칙·선례", "휴면회사 해산, 정관상 해산사유, 해산명령, 일시이사와 회사계속 결의를 판단한다."),
    46: ("상법+상업등기규칙", "상법 제295조·제298조, 주식회사 설립등기 관련 상업등기규칙", "현물출자 이행, 모집설립 조사, 납입금보관증명서, 발기설립 조사보고와 의사록 공증 면제를 판단한다."),
    47: ("민법+비송사건절차법", "민법 제63조·제70조, 비송사건절차법상 임시이사 및 임시총회 소집허가 사건", "임시이사 선임신청권자, 특별대리인, 비법인사단 유추적용과 임시총회 결의범위를 판단한다."),
    48: ("민법+비송사건절차법", "민법 제404조·제405조, 비송사건절차법 제46조~제50조", "재판상 대위의 신청, 관할, 심문, 즉시항고와 채무자 고지 후 처분제한을 판단한다."),
    49: ("상업등기법+상업등기예규", "상업등기법 제15조, 제23조, 제25조, 대표권 공백과 일시대표이사 관련 예규·판례", "법인등록번호, 부속서류 열람, 일시대표이사와 대표자 직무대행자의 등기신청권을 판단한다."),
    50: ("상업등기법+상업등기규칙", "상업등기법·상업등기규칙의 전자증명서와 전자신청 첨부정보 규정", "전자증명서 발급권자, 변경발급, 자격자대리인의 전자신청 첨부정보와 금융기관 전자증명을 판단한다."),
}

LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}

REP_ROWS = """
36|①|O|소규모 주식회사에서 서면결의나 서면동의로 주주총회 결의를 갈음한 경우에도 주주총회에 관한 규정이 준용되므로 의사록을 작성하여야 한다.|
36|②|O|자기주식을 보유한 소규모 주식회사는 자기주식에 관하여 서면결의서 또는 서면동의서를 작성할 필요가 없다.|
36|③|O|소규모 주식회사의 서면결의 등기신청에는 주주 전원의 동의서, 결의요건을 충족하는 서면결의서, 주주 인감증명서와 대표자 인감이 날인된 주주명부가 필요하다.|
36|④|O|확정판결 등으로 등기관이 1인 주주임을 명백히 알 수 있는 경우에는 서면결의 당시 대표자 인감이 날인된 주주명부를 첨부하지 않을 수 있다.|
36|⑤|X|투자조합이 소규모 주식회사의 주주로 서면결의서나 서면동의서를 작성하는 경우 업무집행조합원의 지위 증명서면과 그 업무집행조합원의 개인 인감증명서를 첨부한다.|투자조합 업무집행조합원이 등기소에 제출한 인감을 날인하여야 한다고 한 부분
37|①|O|회생계획 인가 후 회생계획 수행에 따른 등기는 회생절차 종결 후에는 채무자인 법인 또는 새로운 법인의 신청으로 등기하여야 하고 법원사무관 등의 촉탁으로 할 수 없다.|
37|②|X|관리인·관리인대리와 파산관재인·파산관재인대리의 등기는 기타사항란에 하고, 그 등기를 하더라도 채무자의 임원등기와 지배인등기를 말소하지 않는다.|관리인과 파산관재인 등에 관한 등기를 임원란에 하고 기존 임원·지배인 등기를 말소한다고 한 부분
37|③|O|파산선고를 받은 채무자의 대표자가 새로운 이사 등의 취임등기를 신청하지 않으면 파산종결등기를 할 때까지 종전 이사 등의 퇴임등기를 할 수 없다.|
37|④|O|보전관리, 회생절차개시·종결 등 회생 관련 등기와 파산선고·파산종결 등 파산 관련 등기는 기타사항란에 등기한다.|
37|⑤|O|파산절차가 진행 중인 회사의 본점이전등기는 회사의 대표자가 신청하여야 한다.|
38|①|O|신주를 발행하는 회사에 대한 채권도 현물출자의 목적물이 될 수 있다.|
38|②|O|주주에게 신주인수기회를 주었으나 인수하지 않아 발생한 실권주를 제3자에게 재배정한 경우에는 제3자배정 신주발행 통지 또는 공고 증명서면을 첨부하지 않는다.|
38|③|X|주금납입채무와 회사에 대한 채권은 상계할 수 있고, 주금납입채무 전부뿐 아니라 일부 또는 일부 신주인수인의 채무에 대해서도 상계가 가능하다.|주금납입채무의 일부나 일부 신주인수인의 주금납입채무에 대한 상계를 부정한 부분
38|④|O|신주인수권을 가진 주주가 포기하여 생긴 실권주를 이사회결의로 배정한 경우 변경등기신청에는 실권주 배정 이사회의사록만 첨부하고 신주인수권포기서는 첨부하지 않는다.|
38|⑤|O|신주발행 시 현물출자를 하는 자가 있으면 회사와 현물출자자 사이의 현물출자 합의 증명서면도 주식 인수 증명서면에 해당한다.|
39|①|X|유한회사의 공고방법은 정관의 절대적 기재사항이 아니고 유한회사의 등기사항도 아니다.|유한회사가 공고방법을 둔 경우 이를 등기할 수 있다고 한 부분
39|②|O|유한회사의 사원총회 특별결의에서 의결권을 행사할 수 없는 사원과 그 의결권은 총사원 수와 의결권 수에 산입하지 않는다.|
39|③|O|유한회사 설립정관은 원칙적으로 공증인의 인증으로 효력이 생기지만, 자본금총액이 10억 원 미만이면 각 사원이 기명날인 또는 서명함으로써 효력이 생긴다.|
39|④|O|유한회사 자본금 증가등기는 출자전액 납입 또는 현물출자 이행 완료일부터 2주 안에 신청하고, 납입은 금융기관에 할 필요가 없으며 현물출자 검사도 필요하지 않다.|
39|⑤|O|유한회사가 정관상 독립한 최소행정구역 안에서 본점을 이전하는 경우 이사 과반수 결의가 원칙이나 사원총회 결의로도 본점이전을 할 수 있다.|
40|①|O|자본시장과 금융투자업에 관한 법률에 따라 인정되는 전환형 조건부자본증권은 등기사항이다.|
40|②|X|회사는 전에 모집한 사채 총액의 납입이 완료되기 전에도 다시 사채를 모집할 수 있고, 각 사채의 금액이 반드시 1만 원 이상이어야 하는 것도 아니다.|종전 사채 납입 완료 전에는 새 사채 모집을 못 하고 각 사채 금액이 1만 원 이상이어야 한다고 한 부분
40|③|O|한국예탁결제원에 예탁된 전환사채를 주식으로 전환하여 변경등기를 신청하는 경우 회사가 인증을 거쳐 온라인으로 발급받은 전환청구서를 첨부할 수 있다.|
40|④|O|비분리형 신주인수권부사채가 전부 상환되거나 전부 매입소각되면 그 등기를 말소하여야 하고, 말소등기신청에는 상환완료 또는 매입소각 증명서면을 첨부하여야 한다.|
40|⑤|O|신주인수권부사채총액 변경등기신청에 사채상환완료증명서를 첨부하는 경우 그 서면에 사채권자의 인감날인이나 인감증명서 첨부가 필요한 것은 아니다.|
41|①|O|본점소재지와 지점소재지 관할 등기소가 다르면 등기도 각각 신청하여야 하므로 등기해태 과태료도 본점소재지와 지점소재지의 등기해태에 따라 각각 부과된다.|
41|②|O|과태료사건의 관할법원은 특별한 규정이 없으면 과태료에 처할 사람인 회사 대표자 주소지의 지방법원이다.|
41|③|O|당사자의 진술을 듣고 한 과태료재판에는 즉시항고로 불복할 수 있고, 즉시항고에는 집행정지의 효력이 있다.|
41|④|X|등기기간 도과에 정당한 사유가 있는지 여부는 과태료재판에서 판단할 사항이므로 등기관은 등기해태 사실을 기준으로 과태사항을 통지한다.|정당한 사유가 있으면 등기관이 과태사항을 통지할 수 없다고 한 부분
41|⑤|O|회사의 지배인에 관한 등기에 대해서는 과태사항통지를 하지 않는다.|
42|①|O|개인상인의 상호등기에 관한 변경등기는 절대적 등기사항이다.|
42|②|O|지점의 지배인에 관한 등기사항은 지배인을 두지 않은 본점소재지에서는 등기할 수 없다.|
42|③|O|외국회사의 영업소에 대해서는 상법상 동종 또는 가장 유사한 회사의 지점과 같은 사항을 등기하므로 법인등기사항 특례 규정이 적용되지 않는다.|
42|④|X|상업등기사항은 등기 후에도 제3자가 정당한 사유로 알지 못한 때에는 그 제3자에게 대항하지 못한다.|등기 후에는 제3자가 정당한 사유로 알지 못한 경우에도 대항할 수 있다고 한 부분
42|⑤|O|상업등기에는 공신력이 인정되지 않으므로 허위등기를 믿고 거래한 제3자는 원칙적으로 보호받지 못하지만, 법률상 또는 사실상 추정력이 인정되는 경우가 있다.|
43|①|O|액면주식 회사가 주식 액면금액을 인하하거나 주식을 임의소각하는 방식으로 자본금을 감소하는 경우에는 주권제출공고 증명서면을 첨부할 필요가 없다.|
43|②|X|결손보전을 위한 자본금 감소는 채권자보호절차를 생략할 수 있지만, 회사의 재무제표상 채무가 없다는 사정만으로 그 절차를 생략하거나 간이하게 할 수는 없다.|결손보전 감자와 채무 없는 회사를 모두 채권자보호절차 생략 또는 간이절차 대상처럼 묶은 부분
43|③|O|자본금 감소는 원칙적으로 주주총회 특별결의가 필요하지만, 결손 보전을 위한 자본금 감소는 주주총회 보통결의로 할 수 있다.|
43|④|O|주식의 액면가는 균일하여야 하므로 일부 주식에 대해서만 액면가를 낮출 수 없고, 1주의 금액은 100원 이상이어야 하므로 그 미만으로 낮출 수 없다.|
43|⑤|O|주식 소각이나 병합으로 자본금을 감소하여도 발행예정주식총수가 당연히 감소하지 않으므로 정관 변경 없이는 발행예정주식총수 변경등기를 할 수 없다.|
44|①|O|상법상 주식회사의 이사로 법인이 될 수 있는 경우가 있다.|
44|②|O|임기만료 또는 사임 이사가 후임 취임 때까지 권리의무를 가지는 경우 퇴임등기기간은 후임이사 취임일부터 기산하고, 후임 취임등기 전에는 퇴임등기만 할 수 없다.|
44|③|O|법원 가처분결정으로 선임된 대표이사 직무대행자는 법원 허가 없이 새로운 이사 선임 승인 안건이 포함된 임시주주총회를 소집할 수 없다.|
44|④|O|등기사유인 주주총회결의에서 특별이해관계인의 주식 수는 발행주식총수에 산입하지만, 출석한 주주의 의결권 수에는 산입하지 않는다.|
44|⑤|X|특별이해관계인은 주주총회에서 의결권을 행사할 수 없고, 이해관계 없는 대리인을 통하여도 의결권을 행사할 수 없다.|특별이해관계인이 이해관계 없는 대리인을 통하면 의결권을 행사할 수 있다고 한 부분
45|①|O|최후 등기 후 5년이 지난 주식회사가 관보공고에도 신고하지 않아 해산한 것으로 의제되면 등기관은 직권으로 해산등기를 한다.|
45|②|X|정관에 기재된 해산사유는 회사의 등기사항이다.|정관에 기재된 해산사유가 등기사항이 아니라고 한 부분
45|③|X|회사의 해산명령은 이해관계인이나 검사의 청구에 의하여 할 수 있고, 검사의 신청 또는 법원의 직권에만 한정되지 않는다.|해산명령을 검사의 신청이나 법원의 직권으로만 할 수 있다고 한 부분
45|④|X|일시이사가 해산 당시 이사의 지위에 있으면 법정청산인이 될 수 있다.|일시이사는 법정청산인이 될 수 없다고 한 부분
45|⑤|X|존립기간 만료, 정관상 해산사유 발생 또는 주주총회 결의로 해산한 회사의 계속에는 상법상 회사계속 결의요건을 갖추어야 한다.|회사계속을 발행주식총수 과반수 결의로 할 수 있다고 한 부분
46|①|O|현물출자를 하기로 한 발기인은 납입기일에 지체 없이 출자재산을 인도하고, 등기·등록 등 권리 이전에 필요한 서류를 완비하여 교부하여야 한다.|
46|②|O|모집설립에서 현물출자 이행에 관한 사항은 검사인 조사나 공인된 감정인의 감정 대상에 포함되지 않고, 이사와 감사가 조사하여 창립총회에 보고한다.|
46|③|O|발기설립으로 자본금총액 10억 원 이상 주식회사를 설립하거나 모집설립을 하는 경우 설립등기신청서에는 금융기관의 납입금보관증명서면을 제출하여야 한다.|
46|④|X|발기설립에서 이사와 감사 중 발기인이었던 자는 설립경과 조사·보고에 참가하지 못한다.|발기인이었던 이사와 감사를 포함한 이사·감사 전원이 설립경과를 조사하여 보고하여야 한다고 한 부분
46|⑤|O|소규모 주식회사를 발기설립하는 경우 설립등기신청서에 첨부하는 이사회의사록은 공증인의 인증을 받을 필요가 없다.|
47|①|X|임시이사 선임을 신청할 수 있는 이해관계인에는 법인의 채권자도 포함될 수 있다.|임시이사 선임신청권자인 이해관계인에서 채권자를 제외한 부분
47|②|X|법인과 이사의 이익이 상반되고 그 이사 외에 대표권자가 없는 경우에는 임시이사가 아니라 특별대리인 선임이 문제된다.|이익상반 상황을 임시이사 선임사유로 본 부분
47|③|O|권리능력 없는 사단이나 재단에도 법인의 임시이사 선임에 관한 민법 제63조가 유추적용될 수 있다.|
47|④|X|법원의 소집허가로 열린 임시총회라도 소집허가결정과 소집통지서의 목적사항 및 그 관련사항 범위를 벗어난 사항은 결의할 수 없다.|법원 허가 임시총회에서 목적사항과 무관한 사항도 결의할 수 있다고 한 부분
47|⑤|X|법원의 허가를 받아 임시총회가 소집된 경우 대표자는 그 허가된 임시총회와 같은 기일에 별도의 임시총회를 소집하여 권한행사를 방해할 수 없다.|대표자가 법원 허가 임시총회와 같은 기일에 다른 임시총회를 소집할 수 있다고 한 부분
48|①|X|채권자는 자기 채권의 기한 전에 채무자의 권리를 행사하지 않으면 채권을 보전할 수 없거나 보전하기 곤란할 우려가 있을 때 재판상 대위를 신청할 수 있다.|재판상 대위신청 사유를 채권 보전이 불가능한 경우로만 제한한 부분
48|②|X|재판상 대위는 채무자의 보통재판적이 있는 곳의 지방법원이 관할하고, 대위신청에는 채무자와 제3채무자, 보전하려는 채권과 행사하려는 권리의 표시를 적어야 한다.|대위신청을 반드시 서면으로 하여야 한다고 한 부분
48|③|X|재판상 대위 절차에는 심문 공개 규정과 검사의 의견진술·심문참여 규정이 적용되지 않는다.|재판상 대위 절차에서 검사가 의견을 진술하거나 심문에 참여할 수 있다고 한 부분
48|④|X|대위신청을 각하한 재판에 대한 즉시항고기간은 채무자가 재판 고지를 받은 날부터 기산한다.|대위신청 각하 재판의 항고기간 기산점을 채권자가 고지받은 날이라고 한 부분
48|⑤|O|대위신청을 허가한 재판은 직권으로 채무자에게 고지하여야 하고, 고지를 받은 채무자는 그 권리를 처분할 수 없으며 즉시항고를 할 수 있다.|
49|①|X|법인의 명칭이 변경되더라도 기존 법인등록번호는 유지되고 새 법인등록번호를 다시 부여받지 않는다.|법인명칭 변경 시 법인등록번호를 다시 부여받아야 한다고 한 부분
49|②|X|등기기록의 부속서류는 누구든지 열람할 수 있는 것이 아니라 이해관계 있는 부분에 한하여 열람할 수 있다.|등기기록 부속서류를 누구든지 열람할 수 있다고 한 부분
49|③|O|대표이사의 원수를 결한 경우 법원이 선임한 일시대표이사는 상무에 속하는 행위로 제한되지 않으므로 회사를 대표하여 등기를 신청할 수 있다.|
49|④|X|가처분결정으로 선임된 대표자 직무대행자는 직무집행정지와 직무대행자선임 등기가 존속하는 동안 회사에 관한 등기를 신청할 수 있다.|새 대표자가 선임되면 직무대행자가 회사 등기를 신청할 수 없다고 한 부분
49|⑤|X|임기만료 대표이사가 퇴임으로 법률 또는 정관상 대표이사의 원수를 결하게 되면 후임 취임 전까지 권리의무가 있어 회사를 대표하여 등기를 신청할 수 있다.|임기만료 대표이사의 권리의무 유지 중 등기신청권을 부정한 부분
50|①|X|등기기록상 존립기간이 만료된 법인의 대표자는 전자증명서를 발급받을 수 없다.|존립기간이 만료된 법인의 대표자도 전자증명서를 발급받을 수 있다고 한 부분
50|②|X|회사의 등기된 지배인과 특수법인의 등기된 대리인도 전자증명서 발급을 청구할 수 있다.|등기된 지배인과 특수법인 대리인은 전자증명서 발급을 청구할 수 없다고 한 부분
50|③|X|변경등기로 등기기록 내용과 전자증명서 기록 내용이 달라지면 전자증명서를 변경발급받아야 한다.|등기기록과 전자증명서 내용이 달라져도 변경발급이 필요 없다고 한 부분
50|④|O|자격자대리인이 위임장을 전자적 이미지정보로 송신할 수 있는 등기신청에서는 그 위임장 첨부정보 송신 때 위임인의 전자증명서나 인증서를 함께 송신할 필요가 없다.|
50|⑤|X|주금납입금보관증명서뿐 아니라 잔고증명서도 신청인이 금융기관에 요청하여 수신한 정보를 송신하는 방식으로 제출할 수 있다.|잔고증명서는 금융기관 요청·수신 정보 송신 방식으로 제출할 수 없다고 한 부분
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
                "unitType": "choice",
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
    start = text.rfind("【상업등기법 및 비송사건절차법 15문】")
    if start == -1:
        raise ValueError("cannot locate 2024 third-subject section")
    end = text.find("【부동산등기법 30문】", start)
    section = text[start:end if end != -1 else len(text)]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 36 <= int(m.group(1)) <= 50]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} commercial-registry questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            tail = section[match.start() :]
            marker = re.search(r"\s*제3과목\s*①책형\s*전체", tail)
            end = match.start() + marker.start() if marker else len(section)
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
        statement = re.split(r"\s*제3과목\s*①책형\s*전체", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def raw_statement_map() -> dict[tuple[int, str], str]:
    blocks = extract_question_blocks()
    raw: dict[tuple[int, str], str] = {}
    for no, block in blocks.items():
        split = split_choice_units(block)
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
                "qid": f"{YEAR}-g3-cr-{no:02d}",
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 제1차",
                "group": GROUP,
                "groupLabel": "제3과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": rows[0]["sourceQuestionType"],
                "officialAnswer": rows[0]["officialAnswer"],
                "units": [
                    {
                        "unitId": f"{YEAR}-g3-cr-{no:02d}-{row['code']}",
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
                    "reviewNote": "2026-06-18 현행 상법·상업등기법·상업등기규칙·비송사건절차법 및 관련 판례·예규·선례 기준으로 atom 작성",
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
            "sourcePage": "https://0gichul.com/y2024/130881278",
        },
        "subject": SUBJECT_NAME,
        "subjectSummary": {"questionCount": len(questions), "atomQueueItemCount": len(UNITS)},
        "questions": questions,
    }


def build_queue(source: dict) -> dict:
    rows = [row for rows in grouped_units().values() for row in rows]
    unit_by_id = {f"{YEAR}-g3-cr-{row['no']:02d}-{row['code']}": row for row in rows}
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
                        "basisTypesAllowed": ["조문", "규칙", "예규", "선례", "판례", "상법", "상업등기법", "비송사건절차법"],
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
    return f"bupmusa-{YEAR}-commercial-registry-q{int(row['no']):02d}-{row['code']}"


def build_atoms(queue: dict) -> list[dict]:
    queue_by_id = {item["unitId"]: item for item in queue["items"]}
    rows = [row for no, rows in sorted(grouped_units().items()) for row in rows]
    atoms = []
    checked_at = today()
    for row in rows:
        unit_id = f"{YEAR}-g3-cr-{row['no']:02d}-{row['code']}"
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
        r"위\s*[①②③④⑤]",
        r"위의\s*[①②③④⑤]",
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
