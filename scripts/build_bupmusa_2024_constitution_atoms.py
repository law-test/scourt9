from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2024" / "과목별"
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"
INTEGRATED_DIR = PRIVATE_ROOT / "current" / "통합본"
INTEGRATED_PATH = INTEGRATED_DIR / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
YEAR = 2024
ROUND = 30
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 145
LABELS = ["①", "②", "③", "④", "⑤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "국가인권위원회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국가인권위원회법"},
    {"title": "전기통신사업법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/전기통신사업법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "2024 법무사 헌법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881293"},
    {"title": "헌법재판소 결정례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/detcInfoP.do"},
]

TOPICS = {
    1: "헌법재판절차의 가처분",
    2: "대통령",
    3: "탄핵소추심판",
    4: "대통령의 국가긴급권",
    5: "헌법 제10조",
    6: "정당",
    7: "개성공단 전면중단 조치",
    8: "혼인과 가족생활",
    9: "공직선거법상 선거운동",
    10: "직업선택의 자유",
    11: "신체의 자유",
    12: "기본권의 효력",
    13: "국회",
    14: "조례",
    15: "평등원칙",
    16: "국가인권위원회",
    17: "기본권의 주체",
    18: "출생등록",
    19: "계약의 자유",
    20: "통신자료 취득",
}

BASIS: dict[int, tuple[str, str, str]] = {
    1: ("헌법재판소법+헌법재판소 결정례", "헌법재판절차의 가처분 관련 헌법재판소법 및 결정례", "헌법재판절차상 가처분의 허용요건과 한계에 관한 법리이다."),
    2: ("헌법", "헌법상 대통령의 지위·겸직금지·긴급명령·계엄 관련 조문", "대통령의 헌법상 권한과 제한에 관한 조문 지점이다."),
    3: ("헌법+헌법재판소 결정례", "헌법 제65조 및 탄핵심판 관련 헌법재판소 결정례", "탄핵소추사유, 탄핵심판의 계속요건과 법익형량 기준이다."),
    4: ("헌법+대법원 판례+헌법재판소 결정례", "국가긴급권과 긴급조치·계엄 관련 판례", "국가긴급권의 예외성, 사후심사, 긴급조치 위헌성 기준이다."),
    5: ("헌법+헌법재판소 결정례", "헌법 제10조 및 태아 성별고지·일반적 행동자유권·행복추구권 관련 결정례", "인간의 존엄, 행복추구권, 일반적 인격권과 자기결정권에 관한 법리이다."),
    6: ("헌법+정당법+헌법재판소 결정례", "헌법 제8조, 정당법 및 정당 관련 헌법재판소 결정례", "정당의 법적 지위, 등록요건, 제명, 해산 효과에 관한 기준이다."),
    7: ("헌법+헌법재판소 결정례", "개성공단 전면중단 조치 관련 헌법재판소 결정례", "고도의 정치적 결단과 기본권 제한 심사 가능성에 관한 법리이다."),
    8: ("헌법+헌법재판소 결정례", "헌법 제36조 제1항 및 혼인·가족생활 관련 헌법재판소 결정례", "혼인과 가족생활 보장, 성평등, 가족제도 보장에 관한 법리이다."),
    9: ("헌법+공직선거법+헌법재판소 결정례", "공직선거법상 선거운동 제한 관련 헌법재판소 결정례", "정치적 표현의 자유와 선거운동 제한의 한계이다."),
    10: ("헌법+헌법재판소 결정례", "헌법 제15조 및 직업의 자유 관련 헌법재판소 결정례", "직업의 자유 보호영역과 직업선택 제한의 심사 기준이다."),
    11: ("헌법+헌법재판소 결정례", "신체의 자유, 죄형법정주의, 영장주의, 진술거부권 관련 결정례", "신체의 자유 관련 절차보장과 형사절차 기본권의 적용 범위이다."),
    12: ("헌법+헌법재판소 결정례", "기본권 충돌·경합·제한 법률유보 관련 결정례", "기본권 충돌과 경합에서 적용되는 조정 기준이다."),
    13: ("헌법+국회법", "헌법개정안 표결, 해임건의안, 국회 본회의 재개, 국회의원 징계 관련 국회법", "국회 의사절차의 표결방식과 정족수에 관한 조문 지점이다."),
    14: ("헌법+지방자치법+대법원 판례", "헌법 제117조·제118조, 지방자치법 및 조례 관련 판례", "조례 제정범위와 지방자치권 보장의 한계에 관한 법리이다."),
    15: ("헌법+헌법재판소 결정례", "평등원칙 관련 헌법재판소 결정례", "보상·채용·복무기간 산입·형벌체계에서 차별취급의 합리성을 판단한다."),
    16: ("국가인권위원회법+헌법재판소 결정례", "국가인권위원회법 및 권한쟁의 당사자능력 관련 결정례", "국가인권위원회의 조직, 의결, 진정, 법률구조 요청 기준이다."),
    17: ("헌법+헌법재판소 결정례", "외국인·공법인·국가기관·지방자치단체의 기본권 주체성 관련 결정례", "기본권 주체가 될 수 있는지에 관한 법리이다."),
    18: ("헌법+헌법재판소 결정례", "출생등록될 권리와 평등권 관련 헌법재판소 결정례", "출생등록될 권리의 독자성과 실효적 보장 기준이다."),
    19: ("헌법+헌법재판소 결정례", "계약의 자유와 임대차·근로시간·대출규제 관련 결정례", "계약의 자유의 근거와 제한의 정당성 판단 기준이다."),
    20: ("헌법+전기통신사업법+헌법재판소 결정례", "전기통신사업법상 통신자료 제공요청 관련 결정례", "통신자료 취득의 공권력성, 개인정보자기결정권, 영장주의와 적법절차 기준이다."),
}

ATOM_ROWS = """
1|①|01|O|헌법재판소는 권한쟁의심판에서 직권 또는 청구인의 신청으로 종국결정 선고 때까지 피청구인 처분의 효력정지를 명할 수 있다.|
1|①|02|O|권한쟁의심판 가처분에는 행정소송법과 민사소송법의 가처분 관련 규정이 준용된다.|
1|②|01|O|권한쟁의심판 가처분은 본안심판이 부적법하거나 이유 없음이 명백하지 않아야 인용될 수 있다.|
1|②|02|O|권한쟁의심판 가처분은 회복하기 어려운 손해를 예방할 필요와 효력정지의 긴급한 필요가 있어야 인용될 수 있다.|
1|②|03|O|권한쟁의심판 가처분은 인용 후 본안 기각의 불이익과 기각 후 본안 인용의 불이익을 비교형량하여 판단한다.|
1|③|01|O|헌법소원심판에서도 명문 규정이 없더라도 가처분이 허용될 수 있다.|
1|③|02|O|헌법소원심판 가처분은 공권력 행사 또는 불행사의 현상 유지로 생길 회복하기 어려운 손해를 예방할 필요가 있어야 인용될 수 있다.|
1|③|03|O|헌법소원심판 가처분은 효력을 정지시켜야 할 긴급한 필요가 있어야 인용될 수 있다.|
1|④|01|O|법령 효력을 정지시키는 헌법소원 가처분은 파급효과가 클 수 있으므로 신중하게 판단하여야 한다.|
1|⑤|01|X|입국불허 외국인이 관련 구제절차에서 유리한 판단을 받고 장기간 변호인 접견을 하지 못한 경우 변호인 접견허가에 관한 임시지위를 정할 긴급한 필요가 인정될 수 있다.|관련 소송에서 유리한 판단이 있었고 장기간 변호인 접견이 제한되었는데도 가처분의 긴급한 필요를 부정한 부분
2|①|01|O|대통령은 국무총리, 국무위원, 행정각부의 장이나 법률이 정하는 공사의 직을 겸할 수 없다.|
2|①|02|O|대통령의 겸직금지는 비상계엄하에서도 유지된다.|
2|②|01|X|국가원로자문회의의 의장은 직전대통령이 되고, 직전대통령이 없으면 대통령이 지명한다.|국가원로자문회의 의장을 직전대통령이 아니라 전직대통령 일반으로 본 부분
2|③|01|O|대통령후보자가 1인인 경우 득표수가 선거권자 총수의 3분의 1 이상이어야 대통령으로 당선될 수 있다.|
2|④|01|O|대통령의 긴급명령이 국회의 승인을 얻지 못하면 그 명령은 그때부터 효력을 상실한다.|
2|⑤|01|O|국회가 재적의원 과반수 찬성으로 계엄해제를 요구하면 대통령은 계엄을 해제하여야 한다.|
3|①|01|O|탄핵소추사유에서 직무는 법제상 소관 고유업무를 포함한다.|
3|①|02|O|탄핵소추사유에서 직무는 사회통념상 관련 업무와 국정수행 관련 행위까지 포괄할 수 있다.|
3|②|01|O|탄핵소추사유인 헌법·법률 위반에서 헌법은 명문 헌법규정과 확립된 불문헌법을 포함한다.|
3|②|02|O|탄핵소추사유인 법률 위반에서 법률은 형식적 법률과 동등 효력의 조약 및 일반적으로 승인된 국제법규를 포함한다.|
3|③|01|O|행정각부의 장은 국무회의 구성원이자 소관 사무 통할기관이다.|
3|③|02|O|행정각부의 장에 대한 파면 결정은 국정공백과 정치적 혼란을 초래할 수 있으므로 그 효과를 경미하다고 보기 어렵다.|
3|④|01|O|행정각부의 장 탄핵심판에서는 법위반의 중대성과 파면 효과를 형량하여야 한다.|
3|④|02|O|행정각부의 장 탄핵심판에서는 대통령과의 민주적 정당성, 정치적 기능, 직무계속성 차이를 고려할 수 있다.|
3|⑤|01|X|탄핵소추를 받은 공직자가 임기만료로 퇴직하더라도 그 사정만으로 탄핵심판에서 피청구인 자격이 당연히 소멸하여 절차가 종료되는 것은 아니다.|임기만료 퇴직만으로 탄핵심판의 피청구인 자격이 상실되어 절차가 종료된다고 단정한 부분
4|①|01|O|국가긴급권은 법치주의의 예외이다.|
4|①|02|O|국가긴급권은 위기극복이라는 소극적 목적 범위에서 기간과 범위를 목적달성에 필요한 최소한으로 한정하여야 한다.|
4|②|01|O|헌법재판소와 법원은 국가긴급권 발동의 위헌·위법 여부를 사후 심사할 수 있다.|
4|②|02|O|국가긴급권 발동에는 고도의 정치성이 있어 사법심사의 한계가 문제될 수 있다.|
4|③|01|X|대통령 긴급조치 제1호는 발동 당시의 유신헌법상 요건도 갖추지 못하고 기본권을 침해하여 위헌·무효라고 판시되었다.|대통령 긴급조치 제1호가 발동 당시 유신헌법에는 위배되지 않았다고 본 부분
4|④|01|O|대통령의 긴급재정·경제명령은 법률과 마찬가지로 위헌법률심판의 대상이 될 수 있다.|
4|④|02|O|대통령의 긴급재정·경제명령은 법률과 마찬가지로 헌법소원심판의 대상이 될 수 있다.|
4|⑤|01|O|계엄상황이 해소되면 대통령은 국무회의 심의를 거쳐 계엄을 해제할 수 있다.|
5|①|01|O|임신 32주 이전 태아 성별고지를 금지한 의료법 조항은 부모의 태아 성별정보 접근권을 침해한다.|
5|②|01|X|타인의 금융거래정보 요구를 금지하고 위반 시 형사처벌하는 금융실명법 조항은 일반적 행동자유권을 침해한다.|타인의 금융거래정보 요구 금지·처벌 조항이 일반적 행동자유권을 침해하지 않는다고 본 부분
5|③|01|O|유족이 망인의 묘지에서 경배와 추모 등 예우를 취하려는 권리는 행복추구권으로 보호된다.|
5|③|02|O|유족이 시체·유골을 인수하여 봉제사를 하려는 권리는 행복추구권으로 보호된다.|
5|④|01|O|헌법 제10조의 인간의 존엄성은 일반적 인격권을 보장한다.|
5|④|02|O|개인의 자기결정권은 일반적 인격권에서 파생된다.|
5|⑤|01|O|회복불가능한 사망 단계에서 무의미한 연명치료 중단에 관한 환자의 의사결정은 존중될 수 있다.|
5|⑤|02|O|무의미한 연명치료 중단에 관한 환자의 의사결정을 존중하는 것은 인간의 존엄과 행복추구권 보호에 부합한다.|
6|①|01|X|정당은 국민의 정치적 의사형성에 참여하는 단체이지만 그 이유만으로 공권력 행사의 주체가 되는 것은 아니다.|정당을 헌법상 기관이라는 이유로 공권력 행사 주체라고 본 부분
6|②|01|X|정당은 5개 이상의 시·도당을 가져야 한다.|시·도당별 법정당원 수를 500명으로 본 부분
6|②|02|X|정당의 각 시·도당은 1천 명 이상의 당원을 가져야 한다.|시·도당별 법정당원 수를 500명으로 본 부분
6|③|01|O|정당이 소속 국회의원을 제명하려면 당헌 절차를 거쳐야 한다.|
6|③|02|O|정당이 소속 국회의원을 제명하려면 그 소속 국회의원 전원의 2분의 1 이상 찬성이 필요하다.|
6|④|01|X|헌법재판소의 해산결정으로 해산된 정당의 잔여재산은 당헌에 따른 처분이 아니라 국고귀속으로 처리된다.|헌법재판소 해산결정 정당의 잔여재산을 당헌에 따라 처분한다고 본 부분
6|⑤|01|X|정당 등록취소의 효력을 다투는 경우 등록취소된 정당도 헌법소원심판의 청구인능력을 가질 수 있다.|등록취소 이후 정당의 헌법소원 청구인능력을 전면 부정한 부분
7|①|01|O|개성공단 전면중단 조치처럼 고도의 정치적 결단이 필요한 조치도 사법심사 대상에서 당연히 배제되는 것은 아니다.|
7|①|02|O|고도의 정치적 결단이 필요한 조치도 국민 기본권 제한과 직접 관련되면 그 한도에서 헌법소원심판의 대상이 될 수 있다.|
7|②|01|O|개성공단 전면중단 조치는 남북교류협력법상 조정명령을 근거로 한 조치로 볼 수 있다.|
7|②|02|O|개성공단 전면중단 조치는 대통령의 국가 계속성 보장 책무와 행정 지휘·감독권을 근거로 한 조치로 볼 수 있다.|
7|③|01|X|개성공단 전면중단 조치가 국무회의 심의나 이해관계자 의견청취를 거치지 않았다는 사정만으로 적법절차원칙에 위반되어 영업의 자유와 재산권을 침해한다고 볼 수는 없다.|국무회의 심의와 의견청취가 없었다는 이유만으로 적법절차 위반과 기본권 침해를 인정한 부분
7|④|01|O|개성공단 정상화 합의서에는 국내법과 동일한 법적 구속력을 인정하기 어렵다.|
7|④|02|O|개성공단 전면중단 가능성을 예상할 수 있었으면 개성공단 전면중단 조치는 신뢰보호원칙에 위반되지 않는다.|
7|⑤|01|O|개성공단 전면중단 조치는 구체적 재산권 이용을 제한하는 공용제한이 아니다.|
7|⑤|02|O|개성공단 전면중단 조치에서 정당보상 미지급만으로 헌법 제23조 제3항 위반이 되지 않는다.|
8|①|01|O|헌법 제36조 제1항은 혼인과 가족생활에서 양성평등을 명한다.|
8|①|02|O|성별에 따른 차별은 원칙적으로 금지되고 성질상 필요한 예외적 경우에만 정당화된다.|
8|②|01|X|1990년 개정 민법 시행 전 성립한 계모자 사이 법정혈족관계를 시행일부터 소멸시키는 민법 부칙은 헌법 제36조 제1항에 위반되지 않는다.|계모자 법정혈족관계 소멸 부칙을 헌법 제36조 제1항 위반으로 본 부분
8|③|01|O|헌법 제36조 제1항은 혼인과 가족을 지원하고 제3자 침해로부터 보호해야 할 국가과제를 포함한다.|
8|③|02|O|헌법 제36조 제1항은 혼인과 가족에 대한 차별금지 의무를 포함한다.|
8|④|01|O|혼인한 부부의 자산소득을 합산과세하는 소득세법 조항은 혼인한 부부를 정당한 이유 없이 차별하여 헌법 제36조 제1항에 위반된다.|
8|⑤|01|O|헌법 제36조 제1항은 혼인과 가족생활을 스스로 결정하고 형성할 자유를 기본권으로 보장한다.|
8|⑤|02|O|헌법 제36조 제1항은 혼인과 가족에 관한 제도를 보장한다.|
9|①|01|O|선거운동기간 전에 개별적으로 대면하여 말로 하는 선거운동을 금지하는 것은 정치적 표현의 자유를 침해한다.|
9|②|01|X|선거운동을 위한 확성장치 사용을 공개장소 연설·대담 등 일정한 경우로 제한하는 공직선거법 조항은 정치적 표현의 자유를 침해하지 않는다.|선거운동용 확성장치 사용 제한이 정치적 표현의 자유를 침해한다고 본 부분
9|③|01|O|선거일 전 180일부터 선거일까지 선거에 영향을 미치기 위한 벽보 게시와 인쇄물 배부·게시를 금지하는 조항은 정치적 표현의 자유를 침해한다.|
9|④|01|O|선거기간 중 선거에 영향을 미치게 하기 위한 집회나 모임 개최를 금지하는 조항은 집회의 자유를 침해한다.|
9|④|02|O|선거기간 중 선거에 영향을 미치게 하기 위한 집회나 모임 개최를 금지하는 조항은 정치적 표현의 자유를 침해한다.|
9|⑤|01|O|선거일 전 180일부터 선거일까지 선거에 영향을 미치기 위한 광고물 설치·게시나 표시물 착용을 금지하는 조항은 정치적 표현의 자유를 침해한다.|
10|①|01|X|학원설립·운영자가 관련 법 위반으로 벌금형을 선고받은 경우 등록효력을 잃도록 하는 조항은 직업선택의 자유를 침해한다.|벌금형 선고에 따른 학원 등록효력 상실 조항이 직업선택의 자유를 침해하지 않는다고 본 부분
10|②|01|O|직업선택의 자유에는 직업에 필요한 전문지식을 습득할 직업교육장을 임의로 선택할 자유도 포함된다.|
10|③|01|O|읍·면의 이장은 직업의 자유에서 말하는 직업에 해당한다고 보기 어렵다.|
10|④|01|O|새마을금고법 위반죄로 벌금형을 선고받은 임원을 당연퇴임시키는 조항은 직업선택의 자유를 침해하지 않는다.|
10|⑤|01|O|제1종 운전면허 취득요건으로 양쪽 눈 시력을 각각 0.5 이상 요구하는 조항은 직업선택의 자유를 침해하지 않는다.|
11|①|01|O|수형자의 민사재판 출정 중 법정대기실 쇠창살 격리시설 안에서 양손수갑 1개를 앞으로 사용한 행위는 신체의 자유를 침해하지 않는다.|
11|②|01|O|과태료 등 행정질서벌은 죄형법정주의의 규율대상에 해당하지 않는다.|
11|③|01|O|선거범죄 조사에서 선거관리위원회가 피조사자에게 자료제출을 요구하는 것은 영장주의 적용대상이 아니다.|
11|④|01|O|정당 회계책임자를 허위보고로 형사처벌하여 보고의무를 부과하는 것은 진술거부권이 금지하는 진술강요에 해당한다.|
11|⑤|01|X|변호인이 되려는 자의 접견교통권도 피의자·피고인의 변호인 조력을 받을 권리 보장을 위한 헌법상 기본권으로 인정된다.|변호인이 되려는 자의 접견교통권을 헌법상 기본권이 아니라고 본 부분
12|①|01|O|흡연권은 사생활의 자유를 실질적 핵으로 한다.|
12|①|02|O|혐연권은 사생활의 자유뿐만 아니라 생명권에도 연결되므로 흡연권보다 상위의 기본권이다.|
12|②|01|O|근로자의 단결하지 않을 자유와 노동조합의 적극적 단결권이 충돌하면 노동조합의 적극적 단결권이 더 중시된다.|
12|③|01|X|교사의 수업권과 학생의 수학권이 충돌하는 경우 학생의 수학권은 교사의 수업권보다 우월한 지위에 있다.|교사의 수업권과 학생의 수학권을 규범조화적으로 동등 조정한다고 본 부분
12|④|01|O|기본권제한 법률유보원칙은 기본권 제한에 법률의 근거를 요구한다.|
12|④|02|O|기본권제한 법률유보원칙에서 기본권 제한의 형식이 반드시 형식적 의미의 법률이어야 하는 것은 아니다.|
12|⑤|01|O|여러 기본권이 동시에 제약되는 기본권경합에서는 사안과 가장 밀접하고 침해 정도가 큰 주된 기본권을 중심으로 제한 한계를 심사한다.|
13|①|01|O|헌법개정안은 기명투표로 표결한다.|
13|②|01|O|국무총리 또는 국무위원 해임건의안은 본회의 보고 후 24시간 이후 72시간 이내에 표결한다.|
13|②|02|O|국무총리 또는 국무위원 해임건의안은 무기명투표로 표결한다.|
13|③|01|O|본회의 표결은 전자투표에 의한 기록표결이 원칙이다.|
13|③|02|O|국회 본회의 표결은 일정한 경우 기명투표·호명투표 또는 무기명투표로 할 수 있다.|
13|④|01|X|국회 휴회 중에도 대통령 요구, 국회의장의 긴급 필요 인정 또는 재적의원 4분의 1 이상의 요구가 있으면 본회의를 재개한다.|휴회 중 본회의 재개 요구 정족수를 재적의원 3분의 1 이상으로 본 부분
13|⑤|01|O|국회의원이 징계대상자 징계를 요구하려면 의원 20명 이상의 찬성으로 사유를 적은 요구서를 국회의장에게 제출하여야 한다.|
14|①|01|O|법령이 조례로 정하도록 위임한 사항은 하위법령이 그 위임의 내용과 범위를 제한하거나 직접 규정할 수 없다.|
14|②|01|O|조례는 고유사무와 단체위임사무에 관하여 제정할 수 있다.|
14|②|02|O|기관위임사무 같은 국가사무에는 원칙적으로 조례를 제정할 수 없다.|
14|③|01|O|지방자치단체장의 재량으로 주민투표 실시 여부를 결정하도록 한 사항에 대해 반드시 투표를 실시하도록 한 조례안은 단체장의 고유권한을 침해한다.|
14|④|01|O|주민은 지방세·사용료·수수료·부담금의 부과·징수 또는 감면에 관한 사항에 대해 조례 제정을 청구할 수 없다.|
14|⑤|01|X|헌법 제117조와 제118조는 지방자치단체의 자치권을 제도적으로 보장하지만 지역주민 개인의 자치권을 직접 도출하는 규정은 아니다.|지방자치 규정에서 지역주민 개인의 자치권까지 제도적으로 보장된다고 본 부분
15|①|01|O|보훈보상대상자 부모의 유족보상금 수급권자를 1인으로 한정하고 나이가 많은 자를 우선하도록 한 조항은 나이가 적은 부모 일방을 합리적 이유 없이 차별한다.|
15|②|01|O|국·공립대학교 졸업생을 교사 신규채용에서 우선시키는 교육공무원법 조항은 사립사범대 졸업자의 채용기회를 제한·박탈하여 평등원칙에 위반된다.|
15|③|01|X|산업기능요원의 군복무기간을 공무원 재직기간에 산입하지 않는 것은 공익근무요원과 달리 취급하더라도 헌법에 위반되지 않는다.|산업기능요원 군복무기간 미산입 조항을 헌법 위반으로 본 부분
15|④|01|O|시체등오욕죄와 달리 분묘발굴죄에 벌금형 없이 5년 이하 징역만 둔 것은 평등원칙에 위배되지 않는다.|
15|⑤|01|O|공익신고 보상금 신청권자를 내부공익신고자로 한정하고 외부공익신고자를 배제한 조항은 평등원칙에 위배되지 않는다.|
16|①|01|X|국가인권위원회는 위원장 1명과 상임위원 3명을 포함한 11명의 인권위원으로 구성된다.|국가인권위원회 상임위원 수를 4명으로 본 부분
16|②|01|O|국가인권위원회는 법률상 국가기관이지 헌법상 국가기관이 아니다.|
16|②|02|O|국가인권위원회는 권한쟁의심판의 당사자능력이 인정되지 않는다.|
16|③|01|O|국가인권위원회는 재적위원 과반수 찬성으로 의결한다.|
16|③|02|O|국가인권위원회의 의사는 공개한다.|
16|④|01|O|사인으로부터 차별행위를 당한 경우에도 국가인권위원회에 진정할 수 있다.|
16|⑤|01|O|국가인권위원회는 피해자 권리구제를 위하여 법률구조를 요청할 수 있다.|
16|⑤|02|O|국가인권위원회는 피해자의 명시한 의사에 반하여 법률구조를 요청할 수 없다.|
17|①|01|O|불법체류 중인 외국인도 원칙적으로 기본권의 주체가 된다.|
17|②|01|O|면허된 의료행위 외 의료행위를 금지·처벌하는 의료법 규정에 대해서는 외국인의 직업의 자유 기본권주체성이 인정되지 않는다.|
17|②|02|O|면허된 의료행위 외 의료행위를 금지·처벌하는 의료법 규정에 대해서는 외국인의 평등권 기본권주체성이 인정되지 않는다.|
17|③|01|O|국회의 일부조직인 국회노동위원회는 기본권의 주체가 될 수 없다.|
17|④|01|O|직장의료보험조합은 공법인으로서 기본권의 주체가 될 수 없다.|
17|⑤|01|X|혁신도시 입지선정에서 제외된 지방자치단체는 선정기준의 합리성과 타당성을 다투는 평등권 주체가 될 수 없다.|입지선정에서 제외된 지방자치단체의 평등권 주체성을 인정한 부분
18|①|01|O|태어난 즉시 출생등록될 권리는 헌법에 명시되지 않은 독자적 기본권이다.|
18|①|02|O|태어난 즉시 출생등록될 권리는 자유권적 성격과 사회적 기본권 성격을 함께 가진다.|
18|②|01|X|혼인 중인 여자와 남편 아닌 남자 사이에서 출생한 자녀에 대해 생부에게 출생신고를 허용하지 않은 것은 생부의 평등권을 침해하지 않는다.|생부의 출생신고 불허를 생부의 평등권 침해로 본 부분
18|③|01|O|혼인 중인 여자와 남편 아닌 남자 사이에서 출생한 자녀에 대한 생부의 출생신고를 허용하지 않은 것은 혼인외출생자의 즉시 출생등록될 권리를 침해한다.|
18|④|01|O|태어난 즉시 출생등록될 권리는 입법자가 출생등록제도를 통해 형성하고 구체화하여야 할 권리이다.|
18|④|02|O|입법자는 출생등록제도를 형성할 때 출생등록의 이론적 가능성에 그치지 않고 실효적으로 출생등록될 권리를 보장하여야 한다.|
18|⑤|01|O|평등권은 본질적으로 같은 것을 자의적으로 다르게 취급하는 것을 금지한다.|
18|⑤|02|O|평등권은 본질적으로 다른 것을 자의적으로 같게 취급하는 것을 금지한다.|
19|①|01|X|임대차 존속기간을 20년으로 제한한 민법 조항은 과잉금지원칙에 위반하여 계약의 자유를 침해한다.|임대차 존속기간 20년 제한 조항이 계약의 자유를 침해하지 않는다고 본 부분
19|②|01|O|계약의 자유는 헌법 제10조의 행복추구권에 포함된 일반적 행동자유권에서 파생된다.|
19|②|02|O|계약의 자유에는 계약체결 여부, 계약 상대방, 계약 방식과 내용을 자유롭게 결정할 자유가 포함된다.|
19|③|01|O|실제거주를 이유로 갱신거절한 임대인이 정당한 사유 없이 제3자에게 임대한 경우 손해배상책임과 손해액을 정한 조항은 임대인의 계약의 자유를 침해하지 않는다.|
19|③|02|O|실제거주를 이유로 갱신거절한 임대인이 정당한 사유 없이 제3자에게 임대한 경우 손해배상책임과 손해액을 정한 조항은 임대인의 재산권을 침해하지 않는다.|
19|④|01|O|주 52시간 상한제를 정한 근로기준법 조항은 사업주의 계약의 자유와 직업의 자유를 침해하지 않는다.|
19|④|02|O|주 52시간 상한제를 정한 근로기준법 조항은 근로자의 계약의 자유를 침해하지 않는다.|
19|⑤|01|O|초고가아파트 주택구입용 주택담보대출 금지 조치는 해당 대출을 받으려는 사람의 재산권을 침해하지 않는다.|
19|⑤|02|O|초고가아파트 주택구입용 주택담보대출 금지 조치는 해당 대출을 받으려는 사람의 계약의 자유를 침해하지 않는다.|
20|①|01|O|수사기관 등의 통신자료 제공요청은 임의수사에 해당한다.|
20|①|02|O|전기통신사업자가 통신자료 제공요청에 응하지 않아도 법적 불이익이 없으면 그 요청 자체는 헌법소원의 대상인 공권력 행사에 해당하지 않는다.|
20|②|01|O|전기통신사업자가 수사기관 등에 제공하는 이용자의 성명, 주민등록번호, 주소, 전화번호, 아이디, 가입일 또는 해지일은 개인정보에 해당한다.|
20|③|01|O|헌법상 영장주의는 체포·구속·압수·수색 등 기본권을 제한하는 강제처분에 적용된다.|
20|③|02|O|강제력이 개입되지 않은 임의수사인 통신자료 취득에는 헌법상 영장주의가 적용되지 않는다.|
20|④|01|X|통신자료 제공요청 사유가 지나치게 광범위·포괄적이라는 이유만으로 통신자료 제공요청 조항이 과잉금지원칙에 위반된다고 볼 수는 없다.|통신자료 제공요청 사유가 지나치게 광범위하여 과잉금지원칙 위반이라고 본 부분
20|⑤|01|O|통신자료 제공요청 조항은 사후통지절차를 두지 않아 적법절차원칙에 위배된다.|
20|⑤|02|O|통신자료 제공요청 조항은 사후통지절차를 두지 않아 개인정보자기결정권을 침해한다.|
""".strip()


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def complete_sentence(rep: str) -> str:
    rep = rep.strip()
    return rep if rep.endswith(".") else rep.rstrip(".") + "."


def load_atom_rows() -> dict[tuple[int, str], list[dict[str, str | None]]]:
    rows: dict[tuple[int, str], list[dict[str, str | None]]] = {}
    for line in ATOM_ROWS.splitlines():
        no_text, label, atom_index, verdict, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        if label not in LABELS:
            raise ValueError(f"bad label: {line}")
        if verdict not in {"O", "X"}:
            raise ValueError(f"bad verdict: {line}")
        if verdict == "X" and not trap:
            raise ValueError(f"X atom without trap: {line}")
        if verdict == "O" and trap:
            raise ValueError(f"O atom with trap: {line}")
        rows.setdefault((int(no_text), label), []).append(
            {
                "atomIndex": atom_index.strip(),
                "sourceVerdict": verdict,
                "rep": complete_sentence(rep),
                "trap": trap,
            }
        )
    return rows


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_atoms(queue: dict[str, object]) -> list[dict[str, object]]:
    row_map = load_atom_rows()
    queue_items = queue["items"]
    if len(queue_items) != SOURCE_UNIT_COUNT:
        raise ValueError(f"unexpected source unit count: {len(queue_items)}")

    checked_at = today()
    items: list[dict[str, object]] = []
    for queue_item in queue_items:
        key = (int(queue_item["no"]), str(queue_item["unitLabel"]))
        if key not in row_map:
            raise ValueError(f"missing atom rows for {key}")
        basis_type, basis_ref, why = BASIS[key[0]]
        for row in row_map[key]:
            rep = str(row["rep"])
            source_is_x = row["sourceVerdict"] == "X"
            items.append(
                {
                    "atomId": f"bupmusa-2024-constitution-q{key[0]:02d}-{LABEL_CODE[key[1]]}-{row['atomIndex']}",
                    "sourceUnitId": queue_item["unitId"],
                    "sourceAtomIndex": row["atomIndex"],
                    "sourceFamily": "법무사시험",
                    "source": f"{YEAR} 법무사 {ROUND}회 헌법 {queue_item['no']}번 {queue_item['unitLabel']} 기출",
                    "year": YEAR,
                    "round": ROUND,
                    "subject": SUBJECT_NAME,
                    "no": queue_item["no"],
                    "unitType": queue_item["unitType"],
                    "unitLabel": queue_item["unitLabel"],
                    "sourceQuestionType": queue_item["sourceQuestionType"],
                    "officialQuestionAnswer": queue_item["officialQuestionAnswer"],
                    "sourceUnitVerdict": queue_item["originalVerdict"],
                    "sourceVerdict": row["sourceVerdict"],
                    "currentVerdict": "O",
                    "rep": rep,
                    "a": "O",
                    "basisType": basis_type,
                    "basisRef": basis_ref,
                    "why": why,
                    "sourceStatement": queue_item["rawStatement"],
                    "sourceTrap": row["trap"],
                    "xDependsOn": rep if source_is_x else None,
                    "reviewedAt": checked_at,
                    "currentLawCheckedAt": checked_at,
                }
            )
    return items


def normalize_key(text: str) -> str:
    cleaned = re.sub(r"\s+", "", text)
    cleaned = cleaned.replace("ㆍ", "·").replace("․", "·")
    return cleaned.lower()


def year_to_exam_date(year: int) -> float:
    return year + 8.0 / 12.0


def weight_for_sources(sources: list[dict[str, object]], today_year: float = 2026.46, half_life: float = 4.0) -> float:
    total = 0.0
    for src in sources:
        year = int(src.get("year", YEAR))
        source_weight = float(src.get("s", 1.0))
        age = max(0.0, today_year - year_to_exam_date(year))
        total += source_weight * (0.5 ** (age / half_life))
    return round(math.log1p(total), 4)


def grade_items(items: list[dict[str, object]]) -> None:
    sorted_items = sorted(items, key=lambda item: (-float(item["weight"]), str(item["rep"])))
    cuts = [(0.04, "S"), (0.11, "A+"), (0.23, "A"), (0.40, "B+"), (0.60, "B"), (0.77, "C+"), (0.89, "C"), (0.96, "D+"), (1.00, "D")]
    n = len(sorted_items)
    for rank, item in enumerate(sorted_items, start=1):
        p = rank / n
        item["grade"] = next(grade for cut, grade in cuts if p <= cut)
        item["rank"] = rank


def source_label(atom: dict[str, object]) -> str:
    return f"{atom['year']} 법무사 {atom['round']}회 헌법 {atom['no']}번 {atom['unitLabel']}"


def new_integrated_item(atom: dict[str, object], source: dict[str, object]) -> dict[str, object]:
    return {
        "primary": "법무사시험",
        "sourceFamilies": ["법무사시험"],
        "subject": SUBJECT_NAME,
        "topic": TOPICS.get(int(atom["no"]), SUBJECT_NAME),
        "rep": atom["rep"],
        "a": atom["a"],
        "why": atom["why"],
        "basisType": atom["basisType"],
        "basisRef": atom["basisRef"],
        "sources": [source],
        "refs": [source["source"]],
        "sourceIds": [atom["atomId"]],
        "sourceAtomCount": 1,
        "quality": {"statementType": "declarative", "displayable": True, "normalizers": [], "changed": False},
        "verification": {"status": "needs-legal-review", "lawAsOf": today(), "legalVerifiedAt": None, "statuteCitationStatus": "pending"},
    }


def source_from_atom(atom: dict[str, object]) -> dict[str, object]:
    return {
        "family": "법무사시험",
        "s": 1.0,
        "year": atom["year"],
        "round": atom["round"],
        "subject": SUBJECT_NAME,
        "source": source_label(atom),
        "sourceId": atom["atomId"],
        "sourceUnitId": atom["sourceUnitId"],
        "sourceVerdict": atom["sourceVerdict"],
        "sourceTrap": atom["sourceTrap"],
        "sourceStatement": atom["sourceStatement"],
    }


def rebuild_integrated(new_atoms: list[dict[str, object]]) -> dict[str, object]:
    existing = load_json(INTEGRATED_PATH) if INTEGRATED_PATH.exists() else None
    buckets: dict[tuple[str, str], dict[str, object]] = {}
    if existing:
        for old_item in existing.get("items", []):
            item = dict(old_item)
            item["sources"] = [src for src in item.get("sources", []) if not str(src.get("sourceId", "")).startswith("bupmusa-2024-constitution-")]
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
        else:
            item = buckets[key]
            if source["sourceId"] not in item["sourceIds"]:
                item["sources"].append(source)
                item["refs"].append(source["source"])
                item["sourceIds"].append(source["sourceId"])
                item["sourceAtomCount"] = int(item["sourceAtomCount"]) + 1

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
    return {
        "title": "법무사_헌법 통합 atom",
        "subject": SUBJECT_NAME,
        "schema": "bupmusa/constitution-integrated-atom/v1",
        "version": "bupmusa_constitution_v002_2024_integrated",
        "builtAt": today(),
        "sourceFiles": {str(year): str(SUBJECT_DIR.parent.parent / str(year) / "과목별" / f"{year}_법무사_헌법_atoms.json") for year in years},
        "weighting": {"H": 4.0, "today": 2026.46, "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0", "gradeScope": "법무사 헌법 통합 atom 내 상대평가"},
        "integration": {"method": "exact-normalized-text", "scope": "법무사시험 헌법 누적"},
        "stats": {"sourceYears": years, "inputAtoms": input_atoms, "items": len(items), "duplicatesMerged": max(0, input_atoms - len(items)), "gradeCounts": dict(Counter(item["grade"] for item in items))},
        "items": items,
    }


def validate_atoms(items: list[dict[str, object]], queue: dict[str, object]) -> None:
    if len(items) < MIN_ATOM_COUNT:
        raise ValueError(f"atom count too low: {len(items)}")
    ids = [str(item["atomId"]) for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    queue_units = {str(item["unitId"]) for item in queue["items"]}
    atom_units = {str(item["sourceUnitId"]) for item in items}
    if queue_units != atom_units:
        raise ValueError(f"source unit coverage mismatch: {sorted(queue_units - atom_units)[:5]}")
    banned = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "옳지 않은"]
    for item in items:
        rep = str(item["rep"])
        if any(token in rep for token in banned):
            raise ValueError(f"non-atom wording: {item['atomId']} {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or item["xDependsOn"] != rep:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        elif item["sourceTrap"] is not None or item["xDependsOn"] is not None:
            raise ValueError(f"unexpected X metadata: {item['atomId']}")
        if item["sourceUnitVerdict"] == "O" and item["sourceVerdict"] == "X":
            raise ValueError(f"X atom under true source unit: {item['atomId']}")
        if item["currentVerdict"] != "O" or item["a"] != "O":
            raise ValueError(f"completed atom must be O: {item['atomId']}")


def validate_integrated(doc: dict[str, object]) -> None:
    items = doc["items"]
    if not items:
        raise ValueError("empty integrated atom")
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate integrated ids")


def update_index(atom_count: int) -> None:
    if not SUBJECT_INDEX_PATH.exists():
        return
    index = load_json(SUBJECT_INDEX_PATH)
    index["updatedAt"] = today()
    subject = index.setdefault("subjects", {}).setdefault(SUBJECT_NAME, {"subject": SUBJECT_NAME})
    subject["source"] = str(SOURCE_PATH)
    subject["atomQueue"] = str(QUEUE_PATH)
    subject["completedAtoms"] = str(OUT_PATH)
    subject["completedAtomCount"] = atom_count
    subject["completedAtomsUpdatedAt"] = today()
    write_json(SUBJECT_INDEX_PATH, index)


def build_completed_doc(queue: dict[str, object], atoms: list[dict[str, object]]) -> dict[str, object]:
    source = load_json(SOURCE_PATH)
    return {
        "schema": "legal-scrivener/completed-atoms-by-subject/v2",
        "sourceFamily": "법무사시험",
        "examId": queue["examId"],
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "atomPrinciple": "docs/atom_원칙_v001.md",
        "source": str(SOURCE_PATH),
        "sourceQueue": str(QUEUE_PATH),
        "sourceCount": len(queue["items"]),
        "questionCount": len(source["questions"]),
        "atomCount": len(atoms),
        "verificationSources": LEGAL_SOURCES,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "atomSplit": "원문 보기 하나가 여러 조문·판례·학설 판단 지점을 포함하면 여러 atom으로 분해한다.",
            "xHandling": "원문상 틀린 판단 지점은 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "integration": "회차별 atom을 법리 동일성 기준으로 법무사_헌법_통합_atom에 누적한다.",
        },
        "items": atoms,
    }


def main() -> None:
    queue = load_json(QUEUE_PATH)
    atoms = build_atoms(queue)
    validate_atoms(atoms, queue)
    completed = build_completed_doc(queue, atoms)
    write_json(OUT_PATH, completed)
    integrated = rebuild_integrated(atoms)
    validate_integrated(integrated)
    write_json(INTEGRATED_PATH, integrated)
    update_index(len(atoms))
    verdict_counts = Counter(item["sourceVerdict"] for item in atoms)
    per_question = Counter(item["no"] for item in atoms)
    print(f"wrote {OUT_PATH}")
    print(f"wrote {INTEGRATED_PATH}")
    print(f"sourceUnits={len(queue['items'])} atoms={len(atoms)} O={verdict_counts['O']} X={verdict_counts['X']}")
    print("perQuestion=" + ", ".join(f"{key}:{value}" for key, value in sorted(per_question.items())))
    print(f"integratedItems={integrated['stats']['items']} merged={integrated['stats']['duplicatesMerged']}")


if __name__ == "__main__":
    main()
