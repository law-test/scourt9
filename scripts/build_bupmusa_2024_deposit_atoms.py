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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_공탁법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_공탁법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_공탁법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "공탁법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 4
QUESTION_COUNT = 20

LEGAL_SOURCES = [
    {
        "title": "공탁법",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/법령/공탁법",
    },
    {
        "title": "공탁규칙",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/법령/공탁규칙",
    },
    {
        "title": "민사집행법",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/법령/민사집행법",
    },
    {
        "title": "민법",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/법령/민법",
    },
    {
        "title": "2024 법무사 공탁법 문제 정답",
        "publisher": "공기출",
        "url": "https://0gichul.com/y2024/130881323",
    },
]

OFFICIAL_ANSWERS = {
    31: "①",
    32: "③",
    33: "④",
    34: "④",
    35: "⑤",
    36: "④",
    37: "④",
    38: "②",
    39: "①",
    40: "⑤",
    41: "②",
    42: "①",
    43: "③",
    44: "③",
    45: "③",
    46: "②",
    47: "④",
    48: "①",
    49: "⑤",
    50: "④",
}

QUESTION_TYPES = {
    42: "single-best-true",
    45: "multi-select-true",
}

QUESTION_BASIS = {
    31: {
        "basisType": "예규·선례",
        "basisRef": "공탁규칙 제23조·제29조, 공탁사무 처리예규·선례",
        "why": "공탁통지서와 공탁사실통지서는 공탁의 성격과 통지 상대방별 실무 기준에 따라 발송된다.",
    },
    32: {
        "basisType": "예규·선례",
        "basisRef": "민사집행법 제291조·제248조 제1항, 가압류 관련 집행공탁 실무선례",
        "why": "일부 가압류 관련 전액 공탁에서는 가압류효력 존속 부분과 초과 부분의 지급·회수 절차가 구별된다.",
    },
    33: {
        "basisType": "조문+규칙",
        "basisRef": "공탁법 제5조의2, 공탁규칙 제82조~제84조",
        "why": "형사공탁 특례는 피해자 인적사항 비실명 처리, 동일인 확인, 통지서 송부 방식을 따로 정한다.",
    },
    34: {
        "basisType": "판례+예규·선례",
        "basisRef": "민법 제487조, 민사집행법 제291조·제248조 제1항, 혼합공탁 관련 대법원 판례·공탁선례",
        "why": "혼합공탁은 변제공탁과 집행공탁의 요건이 함께 존재할 때 허용되고, 출급·회수에는 양쪽 이해관계가 모두 반영된다.",
    },
    35: {
        "basisType": "조문+판례",
        "basisRef": "공익사업을 위한 토지 등의 취득 및 보상에 관한 법률 제40조, 수용공탁 관련 대법원 판례",
        "why": "수용보상금 공탁은 보상금 지급, 제한물권의 물상대위, 재결 실효 여부에 관한 판례 기준에 따른다.",
    },
    36: {
        "basisType": "판례+예규·선례",
        "basisRef": "민법 제487조, 민사집행법 제248조, 공탁 종류 판단 관련 대법원 판례·공탁선례",
        "why": "공탁의 종류는 피공탁자 지정, 공탁근거, 원인사실, 사유신고 여부를 종합하여 판단한다.",
    },
    37: {
        "basisType": "판례+예규·선례",
        "basisRef": "민법 제487조, 민사집행법 제291조·제248조 제1항, 혼합공탁 출급 관련 대법원 판례·공탁선례",
        "why": "혼합공탁에서 출급청구권자는 채권 귀속관계와 집행채권자에 대한 관계를 모두 증명하여야 한다.",
    },
    38: {
        "basisType": "조문+판례",
        "basisRef": "민사집행법상 가압류해방공탁 규정 및 가압류해방공탁 관련 대법원 판례",
        "why": "가압류해방공탁은 공탁금 자체가 아니라 채무자의 회수청구권에 가압류효력이 이전되는 구조를 따른다.",
    },
    39: {
        "basisType": "판례",
        "basisRef": "민사소송법 제122조·제126조, 재판상 담보공탁 관련 대법원 판례",
        "why": "재판상 담보공탁의 피담보채권은 담보제공명령의 목적과 집행정지로 생긴 손해 범위에 따라 정해진다.",
    },
    40: {
        "basisType": "판례+예규·선례",
        "basisRef": "공탁서 정정 관련 대법원 판례·공탁선례",
        "why": "공탁서 정정은 공탁의 동일성을 해하지 않는 범위에서만 허용된다.",
    },
    41: {
        "basisType": "판례+예규·선례",
        "basisRef": "민법 제487조, 채권자불확지공탁 관련 대법원 판례·공탁선례",
        "why": "채권자불확지공탁은 객관적으로 채권 귀속이나 수령권자가 불명확한 경우에 허용된다.",
    },
    42: {
        "basisType": "조문+예규·선례",
        "basisRef": "공탁법 제8조·제9조, 공탁규칙 및 공탁금 회수청구 첨부서면 관련 공탁예규",
        "why": "공탁금 회수청구에는 공탁서, 승낙서, 회수청구권 취득 증명서면 등 지급청구 유형별 첨부서면 기준이 적용된다.",
    },
    43: {
        "basisType": "판례+예규·선례",
        "basisRef": "민법 제489조, 공탁금 출급·회수 관련 대법원 판례·공탁선례",
        "why": "변제공탁의 출급·회수 효과는 공탁수락, 반대급부 조건, 회수청구권 집행 여부에 따라 달라진다.",
    },
    44: {
        "basisType": "예규·선례",
        "basisRef": "공탁금 지급청구권 양도 관련 공탁예규·선례",
        "why": "공탁금 지급청구권 양도는 양도통지, 양도증서, 인감증명 또는 공증 등 양수사실 증명 방식에 따라 심사된다.",
    },
    45: {
        "basisType": "조문+판례",
        "basisRef": "민사집행법 제248조 제2항·제3항 및 제3채무자 의무공탁 관련 판례",
        "why": "제3채무자의 의무공탁액은 압류 범위 제한, 배당요구, 다른 압류와의 경합 여부에 따라 정해진다.",
    },
    46: {
        "basisType": "판례+예규·선례",
        "basisRef": "공탁금 출급청구권자 판단 관련 대법원 판례·공탁선례",
        "why": "공동 피공탁자, 전부채권자, 조합재산, 상대적 불확지공탁의 출급권자는 권리 귀속관계와 승계관계에 따라 판단된다.",
    },
    47: {
        "basisType": "조문+예규·선례",
        "basisRef": "민사집행법 제248조, 공탁사유신고 관련 공탁예규·선례",
        "why": "사유신고는 배당절차 개시가 필요한 압류경합 등이 있는 경우에 이루어지고, 신고 후 추가 압류는 별도 기준으로 처리된다.",
    },
    48: {
        "basisType": "조문+판례",
        "basisRef": "민사소송법 제125조·제126조, 재판상 담보취소 관련 대법원 판례",
        "why": "담보취소는 담보사유 소멸, 담보권리자 동의, 권리행사최고 절차에 따라 판단된다.",
    },
    49: {
        "basisType": "판례",
        "basisRef": "민법 제487조 및 수령거절 변제공탁 관련 대법원 판례",
        "why": "수령거절을 이유로 한 변제공탁은 채권자의 수령거절 의사와 변제제공 필요성의 예외 기준에 따라 판단된다.",
    },
    50: {
        "basisType": "조문+판례",
        "basisRef": "민법 제489조, 공탁법 제9조, 수용보상금공탁·공탁금 회수 관련 대법원 판례·공탁선례",
        "why": "공탁금 회수는 반대급부 조건, 착오공탁, 공탁원인 소멸, 수용보상금공탁의 특수한 회수 제한에 따라 처리된다.",
    },
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
}

REP_ROWS = """
31|①|X|금전채권 일부 압류와 관련하여 제3채무자가 전액을 공탁한 경우 압류효력이 미치는 부분은 집행공탁으로, 초과 부분은 변제공탁으로 나누어 통지 절차를 판단한다.|일부 압류 관련 전액 공탁을 순수 집행공탁처럼 보아 압류채무자에게 공탁통지서를 발송한다고 한 부분
31|②|O|금전채권 가압류를 원인으로 제3채무자가 집행공탁을 하면 공탁관은 피공탁자에게 공탁통지서를 발송하고 가압류채권자에게 공탁사실을 통지한다.|
31|③|O|형사공탁이 이루어지면 공탁관은 해당 형사사건이 계속 중인 법원과 검찰에 형사공탁사실통지서를 송부하여야 한다.|
31|④|O|금전채권 가압류 후 채권양도통지를 받아 제3채무자가 혼합공탁을 한 경우 공탁관은 피공탁자에게 공탁통지서를 발송하고 가압류채권자에게 공탁사실을 통지한다.|
31|⑤|O|금전채권 가압류와 체납처분압류가 경합하여 제3채무자가 집행공탁을 하면 공탁관은 피공탁자에게 공탁통지서를 발송하고 가압류채권자와 체납처분권자에게 공탁사실을 통지한다.|
32|①|O|금전채권 일부 가압류와 관련된 전액 집행공탁은 민사집행법 제291조와 제248조 제1항을 근거로 하고, 제3채무자는 공탁 후 가압류발령법원에 사유신고를 하여야 한다.|
32|②|O|가압류집행된 금전채권액이 공탁되면 가압류의 효력은 청구채권액에 해당하는 공탁금 출급청구권에 존속한다.|
32|③|X|가압류효력이 미치지 않는 초과 공탁금 부분은 변제공탁 성격을 가지므로 피공탁자의 출급청구뿐 아니라 공탁자의 회수청구도 요건에 따라 가능하다.|가압류효력이 미치지 않는 초과 부분에 대하여 공탁자의 회수청구를 전면 부정한 부분
32|④|O|가압류효력이 미치는 공탁금 부분은 가압류채권자가 본압류 이전 압류명령을 얻은 뒤 집행법원의 지급위탁으로 출급청구할 수 있다.|
32|⑤|O|가압류효력이 미치는 공탁금 부분도 공탁 후 가압류가 취소되거나 취하로 실효되면 피공탁자가 실효 증명서면을 첨부하여 출급청구할 수 있다.|
33|①|O|형사공탁은 해당 형사사건이 계속 중인 법원 소재지의 공탁소에 할 수 있다.|
33|②|O|공탁관은 형사공탁물 납입사실을 확인하면 피공탁자별 형사공탁사실통지서를 작성하여 사건 계속 법원과 검찰에 송부하고 사본을 공탁기록에 편철한다.|
33|③|O|형사공탁의 피공탁자 동일인 확인은 법원 또는 검찰이 피공탁자 동일인 확인 증명서를 발급하여 공탁소에 송부하는 방식으로 한다.|
33|④|X|사망한 피해자를 피공탁자로 한 형사공탁에서 법원 또는 검찰의 동일인 확인 증명서에 상속인 인적사항까지 함께 기재되어야 하는 것은 아니다.|사망 피해자 동일인 확인 증명서에 상속인 인적사항 기재를 필수로 본 부분
33|⑤|O|형사공탁 공탁서에는 피공탁자 인적사항 대신 사건 법원, 사건번호, 사건명, 조서나 공소장상 피해자 특정 명칭을 적고 피해발생시점과 채무 성질로 공탁원인을 특정할 수 있다.|
34|①|O|양도금지특약 있는 채권의 양도통지와 가압류가 순차 도달한 경우 혼합공탁서에는 양도인 또는 양수인을 피공탁자로 적고 가압류 사실은 공탁원인사실에 적는다.|
34|②|O|채권양도와 가압류가 함께 문제 되는 혼합공탁에서 제3채무자는 가압류결정문 사본과 공탁통지서를 첨부하고 통지서 발송 우편료를 납부하여야 한다.|
34|③|O|혼합공탁의 양수인이 출급하려면 양도인에 대한 출급권 증명 외에 가압류채권자에 대한 승낙서 또는 출급청구권확인 승소확정판결도 제출하여야 한다.|
34|④|X|혼합공탁 후 양수인이 제3채무자의 다른 책임재산에서 채권 전부를 만족받으면 제3채무자는 공탁원인 소멸을 이유로 공탁금 회수를 청구할 수 있다.|양수인이 다른 책임재산에서 만족을 얻어도 제3채무자의 공탁금 회수청구가 불가능하다고 한 부분
34|⑤|O|혼합공탁 후 공탁금 출급청구권에 압류경합이 생기거나 본압류 이전 압류명령이 있으면 공탁관은 혼합해소문서 제출 후 압류명령 법원에 사유신고를 하여야 한다.|
35|①|O|공탁자를 상대로 한 전부금소송에서 공탁유가증권 직접 출급 조정결정을 받았더라도 그 조정조서만으로 공탁된 수용보상금채권을 직접 출급할 수는 없다.|
35|②|O|수용보상금 지급과 수용으로 인한 소유권이전등기는 동시이행관계가 아니므로 등기서류 교부나 제한물권 말소를 공탁서의 반대급부로 적을 수 없다.|
35|③|O|수용재결 후 보상금채권에 압류가 있으면 사업시행자는 지급금지를 이유로 보상금을 공탁하되, 물상대위를 하지 않은 근저당권자를 압류권자로 취급하지 않는다.|
35|④|O|사업시행자의 수용보상금 공탁이 무효이면 수용개시일까지 보상금 지급이나 적법한 공탁이 없는 것이므로 수용재결은 실효된다.|
35|⑤|X|수용 전 토지에 대한 체납처분압류청이 보상금채권을 다시 압류하더라도 수용 전 토지압류의 종전 우선순위가 보상금 배당절차에 그대로 유지되는 것은 아니다.|수용 전 토지의 체납처분압류 순위가 보상금채권 배당절차에 그대로 승계된다고 한 부분
36|①|O|공탁자는 자기 책임으로 변제공탁, 집행공탁, 혼합공탁 중 어느 공탁을 할 것인지 선택할 수 있다.|
36|②|O|제3채무자가 한 공탁의 성격은 피공탁자 지정, 근거조문, 공탁사유, 사유신고 여부 등을 종합하여 합리적으로 판단한다.|
36|③|O|민사집행법 제248조 제1항에 따른 전액 공탁에서 일부압류인 경우 압류효력이 미치는 부분은 집행공탁이고 초과 부분은 변제공탁이다.|
36|④|X|금전채권 처분금지가처분은 민사집행법 제248조의 집행공탁 사유가 아니므로 제3채무자는 처분금지가처분만을 이유로 집행공탁을 할 수 없다.|금전채권 처분금지가처분을 집행공탁 사유로 본 부분
36|⑤|O|민사집행법 제247조 제1항의 배당가입차단효는 배당을 전제로 하는 집행공탁 부분에 생기고, 혼합공탁의 변제공탁 부분에는 그 효력이 생기지 않는다.|
37|①|O|채권양도통지와 채권가압류결정정본이 동시에 송달된 경우 제3채무자는 양도인 또는 양수인을 피공탁자로 하여 변제공탁과 집행공탁을 결합한 혼합공탁을 할 수 있다.|
37|②|O|근저당권부채권 압류 등이 경합된 부동산의 제3취득자는 근저당권 소멸을 위하여 변제공탁과 집행공탁이 결합된 혼합공탁을 할 수 있다.|
37|③|O|처분금지가처분등기 토지의 수용에서 상대적 불확지공탁과 채권가압류 집행공탁이 결합된 경우 토지소유자는 가처분 패소확정판결과 가압류 실효증명서면으로 출급청구할 수 있다.|
37|④|X|혼합공탁에서 가압류채권자가 가압류효력이 미치는 공탁금을 받으려면 본압류 이전 후에도 집행법원의 지급위탁절차를 거쳐야 한다.|가압류채권자가 집행법원 지급위탁 없이 공탁소에 직접 출급청구할 수 있다고 한 부분
37|⑤|O|하도급대금 직접청구권과 원사업자 채권자의 압류 또는 가압류가 경합하여 우열을 알 수 없으면 발주자는 채권자불확지 변제공탁과 집행공탁이 결합된 혼합공탁을 할 수 있다.|
38|①|O|가압류해방공탁이 이루어지면 가압류효력은 공탁금 자체가 아니라 채무자인 공탁자의 공탁금회수청구권에 미친다.|
38|②|X|가압류채권자는 해방공탁금 자체에 직접 우선변제권을 가지는 것이 아니라 채무자의 공탁금회수청구권에 대한 권리행사로 만족을 얻어야 한다.|가압류채권자에게 해방공탁금 자체에 대한 우선변제권을 인정한 부분
38|③|O|가압류채권자가 해방공탁금을 지급받으려면 본안승소확정판결 등을 집행권원으로 하여 공탁금회수청구권에 대한 별도 현금화명령을 받아야 한다.|
38|④|O|본안승소확정 가압류채권자가 해방공탁금 회수청구권에 전부명령을 받아 지급청구를 하는 경우 본압류 이전 압류가 아니면 피보전권리와 집행채권의 동일성을 소명하여야 한다.|
38|⑤|O|채무자인 공탁자가 가압류해방공탁금을 회수하려면 가압류취소 확정서면이나 취하·해제증명서 등 공탁원인소멸 증명서면을 첨부하여야 한다.|
39|①|X|강제집행정지를 위한 담보공탁의 담보권 효력은 집행정지로 인한 손해에 미치고 근저당권설정등기말소소송의 소송비용에 당연히 미치는 것은 아니다.|경매절차 정지 담보가 본안 소송비용까지 담보한다고 한 부분
39|②|O|보전처분채무자가 가압류해방공탁과 집행취소를 한 뒤 보전처분채권자가 본안에서 패소확정되면 법정이율 상당 이자와 공탁금이율 상당 이자의 차액이 손해로 인정될 수 있다.|
39|③|O|심급별 강제집행정지를 위하여 각각 담보공탁을 한 경우 뒤 심급의 담보제공만으로 앞 심급 담보의 담보사유가 소멸하지 않는다.|
39|④|O|금전지급 또는 명도와 차임상당액 지급 가집행선고부판결의 집행정지 담보는 정지효력 기간에 발생한 지연손해금이나 차임상당 손해를 담보할 수 있다.|
39|⑤|O|강제집행정지를 위하여 법원 명령으로 제공된 공탁금은 채권자가 강제집행정지 자체로 입은 손해배상채권을 담보한다.|
40|①|O|공탁서 정정은 공탁이 수리된 뒤 착오기재가 발견된 경우 공탁의 동일성을 해하지 않는 범위에서 허용된다.|
40|②|O|집행공탁을 혼합공탁으로 바꾸는 정정은 공탁의 동일성을 해하므로 허용되지 않는다.|
40|③|O|공탁 수리 후 공탁물수령자를 추가하는 정정은 공탁의 동일성을 해하므로 원칙적으로 허용되지 않는다.|
40|④|O|선행채무자가 반대급부 조건으로 변제공탁한 뒤 반대급부 없는 것으로 적법하게 정정되면 정정된 때부터 반대급부 없는 변제공탁의 효력이 생긴다.|
40|⑤|X|채권자불확지를 이유로 한 변제공탁에 채권자의 수령불능 사유를 추가하는 정정은 공탁원인사실을 바꾸어 공탁의 동일성을 해할 수 있어 허용되지 않는다.|채권자불확지 공탁에 수령불능 사유를 추가하는 정정을 같은 조문 근거라는 이유로 허용한 부분
41|①|O|수용토지에 처분금지가처분등기가 있고 피보전권리의 내용이 공시되지 않으면 사업시행자는 소유권 귀속 다툼으로 보아 상대적 불확지공탁을 할 수 있다.|
41|②|X|양도금지특약 있는 채권의 전부명령에서 전부채권자가 특약의 존재를 알았다면 전부채권자는 채권을 취득하지 못하므로 채무자는 채권자불확지공탁을 할 수 없다.|양도금지특약을 안 전부채권자를 두고 채권자불확지공탁이 가능하다고 한 부분
41|③|O|채권양도통지 후 통지 철회 등으로 양도의 적법 여부가 객관적으로 의문인 경우 채무자는 채권자불확지공탁을 할 수 있다.|
41|④|O|보상금 총액은 확정되었으나 수령권자와 배분금액에 다툼이 있으면 사업시행자는 다투는 자 전원을 피공탁자로 지정하여 불확지공탁을 할 수 있다.|
41|⑤|O|예금주 사망 후 상속인 사이에 수령권이나 지분 다툼이 있으면 은행은 상속인들을 피공탁자로 지정하고 지분 불명 사유를 적어 채권자불확지공탁을 할 수 있다.|
42|①|O|공탁물을 회수하려는 사람은 회수청구서에 공탁서를 첨부하여야 하지만 이해관계인의 승낙서를 첨부한 경우에는 공탁서를 첨부하지 않을 수 있다.|
42|②|X|비법인재단이 공탁물회수청구를 하는 경우 공탁금액이 5천만 원 이하라는 사정만으로 공탁서 첨부가 면제되는 것은 아니다.|비법인재단의 소액 회수청구에 공탁서 첨부 생략을 인정한 부분
42|③|X|공탁금회수청구권에 대한 추심명령 또는 전부명령을 얻은 채권자가 회수청구를 하는 경우에는 공탁서를 첨부하지 않을 수 있다.|회수청구권 집행채권자에게도 공탁서 첨부가 항상 필요하다고 한 부분
42|④|X|공탁금회수청구권에 대한 전부명령을 받은 사람도 회수청구권 취득을 증명하는 서면을 첨부하여야 한다.|전부명령을 받은 사람에게 회수청구권 취득 증명서면이 필요 없다고 한 부분
42|⑤|X|원인 없는 집행공탁의 공탁사유신고에 대하여 집행법원이 불수리 결정을 한 경우 공탁자는 그 결정을 제출하여 공탁금을 회수할 수 있다.|집행법원의 공탁사유신고 불수리 결정을 제출해도 회수할 수 없다고 한 부분
43|①|O|적법한 변제공탁으로 피공탁자의 출급청구권이 발생하면 피공탁자가 불수락 의사를 표시하더라도 그 출급청구권의 발생 자체가 소멸하지 않는다.|
43|②|O|부당한 반대급부 조건이 붙은 변제공탁도 피공탁자가 조건을 수락하여 출급받으려면 반대급부를 먼저 이행하고 그 증명서면을 첨부하여야 한다.|
43|③|X|공탁자의 회수청구권을 집행한 제3자가 공탁물을 회수한 경우에도 변제공탁으로 인한 채권소멸효는 소급하여 소멸한다.|제3자가 공탁자 회수청구권을 집행하여 회수한 경우를 공탁물 회수에서 제외한 부분
43|④|O|사업시행자가 보상금 산정 불복으로 차액을 공탁한 경우 보상받을 자는 불복절차가 종결될 때까지 그 공탁 보상금을 수령할 수 없다.|
43|⑤|O|합유자들과 가처분권자를 피공탁자로 한 상대적 불확지공탁에서 합유자들이 출급하려면 가처분권자의 승낙서 등 출급권 증명서면이 필요하다.|
44|①|O|공탁금지급청구권의 양수인이 지급을 청구하려면 지급청구권 요건사실과 양수사실을 증명하는 서면을 첨부하여야 한다.|
44|②|O|공탁금지급청구권 양도통지는 검찰청을 통하지 않고 공탁관에게 직접 도달하여도 효력이 있다.|
44|③|X|공탁금지급청구권 양도증서를 공증받아 제출하는 경우에는 양도인의 인감증명서 없이도 양수인이 지급청구를 할 수 있다.|공증받은 양도증서 제출에도 양도인 인감증명서를 반드시 요구한 부분
44|④|O|양도통지서에 날인된 양도인의 인감증명서가 첨부되지 않은 경우 양도인은 그 양도통지서만으로 공탁금을 지급청구할 수 없다.|
44|⑤|O|변제공탁의 출급청구권 양도통지서에 적극적 불수락 표시가 없으면 공탁수락 의사표시가 있는 것으로 보아 공탁자의 회수청구권이 소멸할 수 있다.|
45|ㄱ|X|다른 채권자가 있다는 사실을 제3채무자가 알게 되었다는 사정만으로 민사집행법 제248조 제2항의 공탁의무가 발생하지 않는다.|다른 채권자의 존재를 알게 된 사정만으로 피압류채권 전액 공탁의무를 인정한 부분
45|ㄴ|O|압류 범위가 600만 원으로 제한되고 다른 채권자가 배당요구를 한 경우 제3채무자의 의무공탁액은 압류 범위인 600만 원이다.|
45|ㄷ|X|압류 범위 제한이 없는 채권압류에 다른 채권자의 배당요구가 있으면 제3채무자의 의무공탁액은 압류채권자의 청구금액이 아니라 피압류채권 전액이다.|압류 범위 제한이 없는 경우에도 의무공탁액을 600만 원으로 본 부분
45|ㄹ|O|다른 채권자가 같은 대여금채권에 압류명령을 받은 후 공탁을 청구하면 제3채무자는 민사집행법 제248조 제3항에 따라 피압류채권 전액을 공탁하여야 한다.|
46|①|O|가분채권은 원칙적으로 각 채권자별 채무이행지 공탁소에 공탁하지만 공탁원인과 공탁소가 같으면 하나의 공탁으로 처리할 수 있고 각 채권자는 자기 지분을 출급한다.|
46|②|X|지분을 정하여 변제공탁된 공동피공탁자는 원칙적으로 자기 지분 범위의 출급청구권을 가질 뿐 상대방 지분에 관하여 당연히 출급청구권 확인을 구할 수 있는 것은 아니다.|각 공동피공탁자가 지분초과 부분에 대하여 상대방을 상대로 출급청구권 확인을 구할 수 있다고 한 부분
46|③|O|공탁금출급청구권에 대한 전부명령이 국가에 송달된 후 확정 전에 다른 압류가 송달되어도 선행 전부명령이 실효되지 않으면 전부채권자는 특정승계인으로 출급청구할 수 있다.|
46|④|O|조합재산 수용보상금이 합유자인 조합원 전체를 피공탁자로 공탁된 경우 지분이 특정되어도 출급청구는 조합원 전원이 하여야 한다.|
46|⑤|O|말소청구권 보전을 위한 처분금지가처분등기 때문에 상대적 불확지공탁이 된 경우 가처분권자가 본안에서 패소확정되면 토지소유자는 그 확정판결로 출급청구할 수 있다.|
47|①|O|재판상 담보공탁의 회수청구권에 압류경합이 있는 경우 공탁원인소멸 증명서면이 제출되면 공탁관은 먼저 송달된 압류명령의 집행법원에 사유신고를 한다.|
47|②|O|수용보상금에 대한 여러 물상대위 압류추심명령이 공탁관에게 송달되어 우열 판단이 곤란하면 공탁관은 사유신고를 할 수 있다.|
47|③|O|복수의 가압류가 있고 그 집행채권 총액이 지급청구권 총액을 초과하더라도 그 사정만으로 사유신고 대상이 되는 것은 아니다.|
47|④|X|공탁관이 압류경합으로 이미 사유신고를 한 뒤 다른 압류나 가압류가 송달되더라도 같은 공탁금지급청구권에 대하여 추가 사유신고를 할 필요는 없다.|사유신고 후 추가 압류나 가압류가 있으면 다시 사유신고를 하여야 한다고 한 부분
47|⑤|O|압류경합 등 사유신고 사정이 발생하면 공탁관은 사유신고를 하여야 하고 그 뒤 추심채권자 등에 대한 지급청구를 수리할 수 없다.|
48|①|X|권리행사최고기간 만료로 담보취소결정이 있더라도 그 결정 확정 전 담보권리자가 권리행사를 증명하면 법원은 담보취소결정을 취소하여야 한다.|담보취소결정 확정 전 권리행사 증명이 있어도 결정을 취소할 수 없다고 한 부분
48|②|O|담보제공자는 담보권리자의 동의를 얻은 사실을 증명하여 담보취소를 신청할 수 있다.|
48|③|O|가처분채무자의 이의신청에 따라 법원이 가처분을 취소하면서 담보제공을 명한 경우 그 담보는 가처분 취소 자체로 채권자가 입은 손해를 담보한다.|
48|④|O|가집행선고 있는 항소심판결이 상고심에서 파기환송되면 본안 확정 전이라도 그 판결의 집행정지를 위한 담보는 담보원인이 소멸한다.|
48|⑤|O|담보취소신청사건은 담보제공명령을 한 법원 또는 그 기록을 보관하고 있는 법원이 관할한다.|
49|①|O|채권자가 사망한 경우 수령거절을 원인으로 한 변제공탁을 하려면 상속인에게 변제제공을 하여야 한다.|
49|②|O|잔대금 수령권한이 있는 매도인의 대리인에게 최고하고 그 대리인을 공탁물수령자로 지정하여 잔대금을 변제공탁하면 매도인에 대한 지급효가 생길 수 있다.|
49|③|O|매수인이 소유권이전등기서류 교부를 요구한 경우 반대급부를 이행할 상대방은 매도인이므로 반대급부 조건 변제공탁이 적법할 수 있다.|
49|④|O|채권자가 미리 수령거절 의사를 명백히 표시한 경우 채무자는 현실제공 없이도 유효하게 변제공탁을 할 수 있다.|
49|⑤|X|채권자가 수령을 거절할 것이 명백히 예상되는 경우에는 채무자가 현실제공과 실제 수령거절을 거치지 않고도 변제공탁을 할 수 있다.|수령거절이 명백히 예상되는 경우에도 반드시 이행제공과 실제 거절을 거쳐야 한다고 한 부분
50|①|O|변제공탁의 반대급부 조건은 피공탁자의 출급청구를 제한할 뿐 공탁자가 회수청구를 하는 경우에는 공탁관의 지급제한사유가 되지 않는다.|
50|②|O|재판상 담보공탁에서 법원의 담보제공명령 없이 임의로 담보공탁을 한 경우 공탁자는 착오를 원인으로 공탁금을 회수할 수 있다.|
50|③|O|선행 채권양도 효력에 다툼이 없어 채권자불확지 사정이 없는데 후행 가압류 때문에 혼합공탁을 한 경우 공탁자는 착오를 원인으로 공탁금을 회수할 수 있다.|
50|④|X|수용보상금공탁이 부적법하여 수용재결 실효 판결이 확정된 경우 공탁금 회수청구에 사업시행자 명의 소유권이전등기 말소 후 등기사항증명서까지 첨부하여야 하는 것은 아니다.|수용재결 실효 확정판결에 따른 회수청구에 소유권이전등기 말소 등기사항증명서 첨부를 요구한 부분
50|⑤|O|수용보상금공탁에서는 민법 제489조에 따른 임의적 공탁금 회수청구가 인정되지 않는다.|
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def parse_rep_rows() -> list[dict[str, str | int]]:
    rows = []
    for line in REP_ROWS.splitlines():
        no, label, verdict, rep, trap = (line.split("|", 4) + [""])[:5]
        rows.append(
            {
                "no": int(no),
                "label": label,
                "code": LABEL_CODE[label],
                "sourceVerdict": verdict,
                "rep": rep,
                "trap": trap or None,
                "unitType": "box" if label in {"ㄱ", "ㄴ", "ㄷ", "ㄹ"} else "choice",
                "sourceQuestionType": QUESTION_TYPES.get(int(no), "single-best-false"),
                "officialAnswer": OFFICIAL_ANSWERS[int(no)],
            }
        )
    return rows


UNITS = parse_rep_rows()


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.rfind("【공탁법 20문】")
    if start == -1:
        raise ValueError("cannot locate 2024 deposit-law section")
    section = text[start:]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 31 <= int(m.group(1)) <= 50]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} deposit-law questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        if idx + 1 < len(matches):
            end = matches[idx + 1].start()
        else:
            tail = section[match.start() :]
            end_marker = re.search(r"\s*제4과목\s*①책형\s*전체", tail)
            end = match.start() + end_marker.start() if end_marker else len(section)
        blocks[no] = section[match.start() : end]
    return blocks


def split_choice_units(block: str) -> dict[str, str]:
    parts = re.split(r"([①②③④⑤])", block)
    out: dict[str, str] = {}
    for idx in range(1, len(parts), 2):
        label = parts[idx]
        statement = parts[idx + 1] if idx + 1 < len(parts) else ""
        out[label] = normalize_raw(statement)
    return out


def split_box_units(block: str) -> dict[str, str]:
    before_choices = re.split(r"[①②③④⑤]", block, maxsplit=1)[0]
    parts = re.split(r"([ㄱㄴㄷㄹ]\.)", before_choices)
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
        split = split_box_units(block) if no == 45 else split_choice_units(block)
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
        row.update(QUESTION_BASIS[row["no"]])
        grouped[row["no"]].append(row)
    return grouped


def build_source() -> dict:
    questions = []
    for no, rows in sorted(grouped_units().items()):
        questions.append(
            {
                "qid": f"{YEAR}-g4-{no:02d}",
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
                        "unitId": f"{YEAR}-g4-{no:02d}-{row['code']}",
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
                    "reviewNote": "2026-06-18 현행 공탁법·공탁규칙·민사집행법 및 관련 판례·예규·선례 기준으로 atom 작성",
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
            "sourcePage": "https://0gichul.com/y2024/130881323",
        },
        "subject": SUBJECT_NAME,
        "subjectSummary": {
            "questionCount": len(questions),
            "atomQueueItemCount": len(UNITS),
        },
        "questions": questions,
    }


def build_queue(source: dict) -> dict:
    unit_by_id = {f"{YEAR}-g4-{row['no']:02d}-{row['code']}": row for row in grouped_units().values() for row in row}
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
                        "basisTypesAllowed": ["조문", "규칙", "예규", "선례", "판례", "조문+규칙", "조문+판례", "예규·선례", "판례+예규·선례"],
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
        "subjectSummary": {
            "questionCount": len(source["questions"]),
            "atomQueueItemCount": len(items),
        },
        "queuePolicy": {
            "coverage": "일반 보기, 개수형, 조합형, 박스형의 모든 판단 지문을 atom 제작 대상으로 큐에 올린다.",
            "atomPrinciple": "atom은 지문 복사본이 아니라 O/X 판단 근거인 조문·판례·예규·선례 지점이다.",
            "xHandling": "X 지문은 독립 atom이 아니라 올바른 O atom 또는 근거 법리에 종속시킨다.",
        },
        "items": items,
    }


def atom_id(row: dict) -> str:
    return f"bupmusa-{YEAR}-deposit-q{int(row['no']):02d}-{row['code']}"


def build_atoms(queue: dict) -> list[dict]:
    queue_by_id = {item["unitId"]: item for item in queue["items"]}
    basis_by_no = QUESTION_BASIS
    atoms = []
    checked_at = today()
    for row in UNITS:
        unit_id = f"{YEAR}-g4-{row['no']:02d}-{row['code']}"
        item = queue_by_id[unit_id]
        basis = basis_by_no[row["no"]]
        atom = {
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
            "basisType": basis["basisType"],
            "basisRef": basis["basisRef"],
            "why": basis["why"],
            "sourceStatement": item["rawStatement"],
            "sourceTrap": row["trap"] if row["sourceVerdict"] == "X" else None,
            "xDependsOn": row["rep"] if row["sourceVerdict"] == "X" else None,
            "reviewedAt": checked_at,
            "currentLawCheckedAt": checked_at,
        }
        atoms.append(atom)
    validate(atoms, queue["items"])
    return atoms


def validate(atoms: list[dict], queue_items: list[dict]) -> None:
    if len(atoms) != 99:
        raise ValueError(f"expected 99 atoms, got {len(atoms)}")
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
        r"위\s*[①②③④⑤ㄱㄴㄷㄹ]",
        r"위의\s*[①②③④⑤ㄱㄴㄷㄹ]",
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
