from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2024" / "과목별"
RAW_TEXT_PATH = PRIVATE_ROOT / "text" / "2024" / "2024_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 1
QUESTION_COUNT = 20
EXPECTED_ATOM_COUNT = 100

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "국가인권위원회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국가인권위원회법"},
    {"title": "전기통신사업법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/전기통신사업법"},
    {"title": "헌법재판소 결정례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/detcInfoP.do"},
    {"title": "2024 법무사 헌법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2024/130881293"},
]

OFFICIAL_ANSWERS = {
    1: "⑤",
    2: "②",
    3: "⑤",
    4: "③",
    5: "②",
    6: "③",
    7: "③",
    8: "②",
    9: "②",
    10: "①",
    11: "⑤",
    12: "③",
    13: "④",
    14: "⑤",
    15: "③",
    16: "①",
    17: "⑤",
    18: "②",
    19: "①",
    20: "④",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
QUESTION_TYPES[6] = "single-best-true"

LABELS = ["①", "②", "③", "④", "⑤"]

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
    20: "수사기관 등의 통신자료 취득",
}


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def o(rep: str) -> dict[str, str | None]:
    return {"rep": rep, "trap": None}


def x(rep: str, trap: str) -> dict[str, str | None]:
    return {"rep": rep, "trap": trap}


REPS: dict[int, list[dict[str, str | None]]] = {
    1: [
        o("헌법재판소는 권한쟁의심판에서 직권 또는 청구인의 신청으로 종국결정 선고 때까지 피청구인 처분의 효력정지를 명할 수 있다."),
        o("권한쟁의심판 가처분은 본안의 명백한 부적법·이유 없음이 없고, 회복하기 어려운 손해와 긴급한 필요 및 법익형량상 필요성이 있을 때 인용될 수 있다."),
        o("헌법소원심판에서도 명문 규정이 없더라도 공권력 행사 또는 불행사의 현상 유지가 필요한 경우 가처분이 허용될 수 있다."),
        o("법령의 효력을 정지시키는 헌법소원 가처분은 파급효과가 클 수 있으므로 사인간 법률관계나 구체적 처분 효력정지보다 신중하게 판단하여야 한다."),
        x("입국불허 외국인이 장기간 변호인을 접견하지 못하고 관련 구제절차가 진행 중인 경우 변호인 접견허가에 관한 임시지위를 정할 긴급한 필요가 인정될 수 있다.", "관련 소송에서 외국인에게 유리한 판단이 있었고 장기간 변호인 접견이 제한되었는데도 가처분의 긴급한 필요를 부정한 부분"),
    ],
    2: [
        o("대통령은 국무총리, 국무위원, 행정각부의 장이나 법률이 정하는 공사의 직을 겸할 수 없고, 비상계엄하에서도 겸직금지는 유지된다."),
        x("국가원로자문회의의 의장은 직전대통령이 되고, 직전대통령이 없으면 대통령이 지명한다.", "국가원로자문회의 의장을 직전대통령이 아니라 전직대통령 일반으로 본 부분"),
        o("대통령후보자가 1인인 경우 득표수가 선거권자 총수의 3분의 1 이상이어야 대통령으로 당선될 수 있다."),
        o("대통령의 긴급명령이 국회의 승인을 얻지 못하면 그 명령은 그때부터 효력을 상실한다."),
        o("국회가 재적의원 과반수 찬성으로 계엄해제를 요구하면 대통령은 계엄을 해제하여야 한다."),
    ],
    3: [
        o("탄핵소추사유에서 직무는 법제상 소관 고유업무뿐 아니라 사회통념상 관련 업무와 국정수행 관련 행위까지 포괄한다."),
        o("탄핵소추사유인 헌법·법률 위반에서 헌법은 명문 헌법규정과 확립된 불문헌법을 포함하고, 법률은 형식적 법률과 동등 효력의 조약·일반적으로 승인된 국제법규를 포함한다."),
        o("행정각부의 장은 국무회의 구성원이자 소관 사무 통할기관이므로 파면 결정으로 인한 국정공백과 정치적 혼란을 경미하다고 보기 어렵다."),
        o("행정각부의 장 탄핵심판에서는 법위반의 중대성과 파면 효과를 형량할 때 대통령과의 민주적 정당성·정치적 기능·직무계속성 차이를 고려하여야 한다."),
        x("탄핵소추를 받은 공직자가 임기만료로 퇴직하더라도 그 사정만으로 탄핵심판에서 피청구인 자격이 당연히 소멸하여 절차가 종료되는 것은 아니다.", "임기만료 퇴직만으로 탄핵심판의 피청구인 자격이 상실되어 절차가 종료된다고 단정한 부분"),
    ],
    4: [
        o("국가긴급권은 법치주의의 예외이므로 위기극복이라는 소극적 목적 범위에서 기간과 범위를 목적달성에 필요한 최소한으로 한정하여야 한다."),
        o("헌법재판소와 법원은 국가긴급권 발동의 위헌·위법 여부를 사후 심사할 수 있지만, 고도의 정치성이 심사의 한계로 작용할 수 있다."),
        x("대통령 긴급조치 제1호는 발동 당시의 유신헌법상 요건도 갖추지 못하고 기본권을 침해하여 위헌·무효라고 판시되었다.", "대통령 긴급조치 제1호가 발동 당시 유신헌법에는 위배되지 않았다고 본 부분"),
        o("대통령의 긴급재정·경제명령은 법률과 마찬가지로 위헌법률심판이나 헌법소원심판의 대상이 될 수 있다."),
        o("계엄상황이 해소되면 대통령은 국무회의 심의를 거쳐 계엄을 해제할 수 있다."),
    ],
    5: [
        o("임신 32주 이전 태아 성별고지를 금지한 의료법 조항은 부모의 태아 성별정보 접근권을 침해한다."),
        x("타인의 금융거래정보 요구를 금지하고 위반 시 형사처벌하는 금융실명법 조항은 일반적 행동자유권을 침해한다.", "타인의 금융거래정보 요구 금지·처벌 조항이 일반적 행동자유권을 침해하지 않는다고 본 부분"),
        o("유족이 일정 기간 망인의 묘지에서 경배와 추모 등 예우를 취하거나 시체·유골을 인수하여 봉제사를 하려는 권리는 행복추구권으로 보호된다."),
        o("헌법 제10조의 인간의 존엄성은 일반적 인격권을 보장하고, 개인의 자기결정권은 일반적 인격권에서 파생된다."),
        o("회복불가능한 사망 단계에서 무의미한 연명치료 중단에 관한 환자의 의사결정을 존중하는 것은 인간의 존엄과 행복추구권 보호에 부합한다."),
    ],
    6: [
        x("정당은 국민의 정치적 의사형성에 참여하는 단체이지만 그 이유만으로 공권력 행사의 주체가 되는 것은 아니다.", "정당을 헌법상 기관이라는 이유로 공권력 행사 주체라고 본 부분"),
        x("정당은 5개 이상의 시·도당을 가져야 하고, 각 시·도당은 1천 명 이상의 당원을 가져야 한다.", "시·도당별 법정당원 수를 500명으로 본 부분"),
        o("정당이 소속 국회의원을 제명하려면 당헌 절차 외에 그 소속 국회의원 전원의 2분의 1 이상 찬성이 필요하다."),
        x("헌법재판소의 해산결정으로 해산된 정당의 잔여재산은 당헌에 따른 처분이 아니라 국고귀속으로 처리된다.", "헌법재판소 해산결정 정당의 잔여재산을 당헌에 따라 처분한다고 본 부분"),
        x("정당 등록취소의 효력을 다투는 경우 등록취소된 정당도 헌법소원심판의 청구인능력을 가질 수 있다.", "등록취소 이후 정당의 헌법소원 청구인능력을 전면 부정한 부분"),
    ],
    7: [
        o("개성공단 전면중단 조치처럼 고도의 정치적 결단이 필요한 조치도 국민 기본권 제한과 직접 관련되면 그 한도에서 헌법소원심판의 대상이 될 수 있다."),
        o("개성공단 전면중단 조치는 남북교류협력법상 조정명령, 대통령의 국가 계속성 보장 책무, 행정 지휘·감독권 등을 근거로 한 헌법과 법률에 근거한 조치로 볼 수 있다."),
        x("개성공단 전면중단 조치가 국무회의 심의나 이해관계자 의견청취를 거치지 않았다는 사정만으로 적법절차원칙에 위반되어 영업의 자유와 재산권을 침해한다고 볼 수는 없다.", "국무회의 심의와 의견청취가 없었다는 이유만으로 적법절차 위반과 기본권 침해를 인정한 부분"),
        o("개성공단 정상화 합의서에는 국내법과 동일한 법적 구속력을 인정하기 어렵고 중단 가능성도 예상할 수 있었으므로 개성공단 전면중단 조치는 신뢰보호원칙에 위반되지 않는다."),
        o("개성공단 전면중단 조치는 구체적 재산권 이용을 제한하는 공용제한이 아니므로 정당보상 미지급만으로 헌법 제23조 제3항 위반이 되지 않는다."),
    ],
    8: [
        o("헌법 제36조 제1항은 혼인과 가족생활에서 양성평등을 명하므로 성별 차별은 원칙적으로 금지되고 예외적으로 필요한 경우에만 정당화된다."),
        x("1990년 개정 민법 시행 전 성립한 계모자 사이 법정혈족관계를 시행일부터 소멸시키는 민법 부칙은 헌법 제36조 제1항에 위반되지 않는다.", "계모자 법정혈족관계 소멸 부칙을 헌법 제36조 제1항 위반으로 본 부분"),
        o("헌법 제36조 제1항은 혼인과 가족을 지원·보호할 국가과제와 혼인·가족에 대한 차별금지 의무를 포함한다."),
        o("혼인한 부부의 자산소득을 합산과세하는 소득세법 조항은 혼인한 부부를 정당한 이유 없이 차별하여 헌법 제36조 제1항에 위반된다."),
        o("헌법 제36조 제1항은 혼인과 가족생활을 스스로 결정·형성할 자유와 혼인·가족에 관한 제도보장을 포함한다."),
    ],
    9: [
        o("선거운동기간 전에 개별적으로 대면하여 말로 하는 선거운동을 금지하는 것은 정치적 표현의 자유를 침해한다."),
        x("선거운동을 위한 확성장치 사용을 공개장소 연설·대담 등 일정한 경우로 제한하는 공직선거법 조항은 정치적 표현의 자유를 침해하지 않는다.", "선거운동용 확성장치 사용 제한이 정치적 표현의 자유를 침해한다고 본 부분"),
        o("선거일 전 180일부터 선거일까지 선거에 영향을 미치기 위한 벽보 게시와 인쇄물 배부·게시를 금지하는 조항은 정치적 표현의 자유를 침해한다."),
        o("선거기간 중 선거에 영향을 미치게 하기 위한 집회나 모임 개최를 금지하는 조항은 집회의 자유와 정치적 표현의 자유를 침해한다."),
        o("선거일 전 180일부터 선거일까지 선거에 영향을 미치기 위한 광고물 설치·게시나 표시물 착용을 금지하는 조항은 정치적 표현의 자유를 침해한다."),
    ],
    10: [
        x("학원설립·운영자가 관련 법 위반으로 벌금형을 선고받은 경우 등록효력을 잃도록 하는 조항은 직업선택의 자유를 침해한다.", "벌금형 선고에 따른 학원 등록효력 상실 조항이 직업선택의 자유를 침해하지 않는다고 본 부분"),
        o("직업선택의 자유에는 직업에 필요한 전문지식을 습득할 직업교육장을 임의로 선택할 자유도 포함된다."),
        o("읍·면의 이장은 직업의 자유에서 말하는 직업에 해당한다고 보기 어렵다."),
        o("새마을금고법 위반죄로 벌금형을 선고받은 임원을 당연퇴임시키는 조항은 직업선택의 자유를 침해하지 않는다."),
        o("제1종 운전면허 취득요건으로 양쪽 눈 시력을 각각 0.5 이상 요구하는 도로교통법 시행령 조항은 직업선택의 자유를 침해하지 않는다."),
    ],
    11: [
        o("수형자의 민사재판 출정 중 법정대기실 쇠창살 격리시설 안에서 양손수갑 1개를 앞으로 사용한 행위는 신체의 자유를 침해하지 않는다."),
        o("과태료 등 행정질서벌은 죄형법정주의의 규율대상에 해당하지 않는다."),
        o("선거범죄 조사에서 선거관리위원회가 피조사자에게 자료제출을 요구하는 것은 영장주의 적용대상이 아니다."),
        o("정당 회계책임자를 허위보고로 형사처벌하여 보고의무를 부과하는 것은 진술거부권이 금지하는 진술강요에 해당한다."),
        x("변호인이 되려는 자의 접견교통권도 피의자·피고인의 변호인 조력을 받을 권리 보장을 위한 헌법상 기본권으로 인정된다.", "변호인이 되려는 자의 접견교통권을 헌법상 기본권이 아니라고 본 부분"),
    ],
    12: [
        o("흡연권은 사생활의 자유를 핵으로 하고 혐연권은 사생활의 자유와 생명권에 연결되므로 혐연권이 흡연권보다 상위의 기본권이다."),
        o("근로자의 단결하지 않을 자유와 노동조합의 적극적 단결권이 충돌하면 노동조합의 적극적 단결권이 더 중시된다."),
        x("교사의 수업권과 학생의 수학권이 충돌하는 경우 학생의 수학권이 교사의 수업권보다 우월한 지위에 있다.", "교사의 수업권과 학생의 수학권을 규범조화적으로 동등 조정한다고 본 부분"),
        o("기본권제한 법률유보원칙은 법률 근거를 요구하지만 제한 형식이 반드시 형식적 의미의 법률이어야 하는 것은 아니다."),
        o("여러 기본권이 동시에 제약되는 기본권경합에서는 사안과 가장 밀접하고 침해 정도가 큰 주된 기본권을 중심으로 제한 한계를 심사한다."),
    ],
    13: [
        o("헌법개정안은 기명투표로 표결한다."),
        o("국무총리 또는 국무위원 해임건의안은 본회의 보고 후 24시간 이후 72시간 이내에 무기명투표로 표결한다."),
        o("본회의 표결은 전자투표에 의한 기록표결이 원칙이나, 일정한 경우 기명투표·호명투표 또는 무기명투표로 할 수 있다."),
        x("국회 휴회 중에도 대통령 요구, 의장의 긴급 필요 인정 또는 재적의원 4분의 1 이상의 요구가 있으면 본회의를 재개한다.", "휴회 중 본회의 재개 요구 정족수를 재적의원 3분의 1 이상으로 본 부분"),
        o("국회의원이 징계대상자 징계를 요구하려면 의원 20명 이상의 찬성으로 사유를 적은 요구서를 의장에게 제출하여야 한다."),
    ],
    14: [
        o("법령이 조례로 정하도록 위임한 사항은 하위법령이 그 위임의 내용과 범위를 제한하거나 직접 규정할 수 없다."),
        o("조례는 고유사무와 단체위임사무에 관하여 제정할 수 있고, 기관위임사무 같은 국가사무에는 원칙적으로 조례를 제정할 수 없다."),
        o("지방자치단체장의 재량으로 주민투표 실시 여부를 결정하도록 한 사항에 대해 반드시 투표를 실시하도록 한 조례안은 단체장의 고유권한을 침해한다."),
        o("주민은 지방세·사용료·수수료·부담금의 부과·징수 또는 감면에 관한 사항에 대해 조례 제정을 청구할 수 없다."),
        x("헌법 제117조와 제118조는 지방자치단체의 자치권을 제도적으로 보장하지만, 지역주민 개인의 자치권을 직접 도출하는 규정은 아니다.", "지방자치 규정에서 지역주민 개인의 자치권까지 제도적으로 보장된다고 본 부분"),
    ],
    15: [
        o("보훈보상대상자 부모의 유족보상금 수급권자를 1인으로 한정하고 나이가 많은 자를 우선하도록 한 조항은 나이가 적은 부모 일방을 합리적 이유 없이 차별한다."),
        o("국·공립대학교 졸업생을 교사 신규채용에서 우선시키는 교육공무원법 조항은 사립사범대 졸업자의 채용기회를 제한·박탈하여 평등원칙에 위반된다."),
        x("산업기능요원의 군복무기간을 공무원 재직기간에 산입하지 않는 것은 공익근무요원과 달리 취급하더라도 헌법에 위반되지 않는다.", "산업기능요원 군복무기간 미산입 조항을 헌법 위반으로 본 부분"),
        o("시체등오욕죄와 달리 분묘발굴죄에 벌금형 없이 5년 이하 징역만 둔 것은 평등원칙에 위배되지 않는다."),
        o("공익신고 보상금 신청권자를 내부공익신고자로 한정하고 외부공익신고자를 배제한 조항은 평등원칙에 위배되지 않는다."),
    ],
    16: [
        x("국가인권위원회는 위원장 1명과 상임위원 3명을 포함한 11명의 인권위원으로 구성된다.", "국가인권위원회 상임위원 수를 4명으로 본 부분"),
        o("국가인권위원회는 법률상 국가기관이지 헌법상 국가기관이 아니므로 권한쟁의심판의 당사자능력이 인정되지 않는다."),
        o("국가인권위원회는 재적위원 과반수 찬성으로 의결하고, 의사는 공개한다."),
        o("사인으로부터 차별행위를 당한 경우에도 국가인권위원회에 진정할 수 있다."),
        o("국가인권위원회는 피해자 권리구제를 위해 법률구조를 요청할 수 있지만 피해자의 명시한 의사에 반하여 요청할 수 없다."),
    ],
    17: [
        o("불법체류 중인 외국인도 원칙적으로 기본권의 주체가 된다."),
        o("면허된 의료행위 외 의료행위를 금지·처벌하는 의료법 규정에 대해서는 외국인의 직업의 자유와 평등권 기본권주체성이 인정되지 않는다."),
        o("국회의 일부조직인 국회노동위원회는 기본권의 주체가 될 수 없다."),
        o("직장의료보험조합은 공법인으로서 기본권의 주체가 될 수 없다."),
        x("혁신도시 입지선정에서 제외된 지방자치단체는 선정기준의 합리성과 타당성을 다투는 평등권 주체가 될 수 없다.", "입지선정에서 제외된 지방자치단체의 평등권 주체성을 인정한 부분"),
    ],
    18: [
        o("태어난 즉시 출생등록될 권리는 헌법에 명시되지 않은 독자적 기본권으로서 자유권적 성격과 사회적 기본권 성격을 함께 가진다."),
        x("혼인 중인 여자와 남편 아닌 남자 사이에서 출생한 자녀에 대해 생부에게 출생신고를 허용하지 않은 것은 생부의 평등권을 침해하지 않는다.", "생부의 출생신고 불허를 생부의 평등권 침해로 본 부분"),
        o("혼인 중인 여자와 남편 아닌 남자 사이에서 출생한 자녀에 대한 생부의 출생신고를 허용하지 않은 가족관계등록법 조항은 혼인외출생자의 즉시 출생등록될 권리를 침해한다."),
        o("태어난 즉시 출생등록될 권리는 입법자가 출생등록제도를 통해 형성·구체화하고 실효적으로 보장하여야 할 권리이다."),
        o("평등권은 본질적으로 같은 것을 자의적으로 다르게, 본질적으로 다른 것을 자의적으로 같게 취급하는 것을 금지한다."),
    ],
    19: [
        x("임대차 존속기간을 20년으로 제한한 민법 조항은 과잉금지원칙에 위반하여 계약의 자유를 침해한다.", "임대차 존속기간 20년 제한 조항이 계약의 자유를 침해하지 않는다고 본 부분"),
        o("계약의 자유는 헌법 제10조의 행복추구권에 포함된 일반적 행동자유권에서 파생된다."),
        o("실제거주를 이유로 갱신거절한 임대인이 정당한 사유 없이 제3자에게 임대한 경우 손해배상책임과 손해액을 정한 조항은 계약의 자유와 재산권을 침해하지 않는다."),
        o("주 52시간 상한제를 정한 근로기준법 조항은 사업주의 계약의 자유·직업의 자유와 근로자의 계약의 자유를 침해하지 않는다."),
        o("초고가아파트 주택구입용 주택담보대출 금지 조치는 해당 대출을 받으려는 사람의 재산권과 계약의 자유를 침해하지 않는다."),
    ],
    20: [
        o("수사기관 등의 통신자료 제공요청은 임의수사로서 사업자가 불응해도 법적 불이익이 없으므로 그 요청 자체는 헌법소원의 대상이 되는 공권력 행사에 해당하지 않는다."),
        o("전기통신사업자가 수사기관 등에 제공하는 이용자의 성명, 주민등록번호, 주소, 전화번호, 아이디, 가입일 또는 해지일은 개인정보에 해당한다."),
        o("강제력이 개입되지 않은 임의수사인 통신자료 취득에는 헌법상 영장주의가 적용되지 않는다."),
        x("통신자료 제공요청 사유가 지나치게 광범위·포괄적이라는 이유만으로 통신자료 제공요청 조항이 과잉금지원칙에 위반된다고 볼 수는 없다.", "통신자료 제공요청 사유가 지나치게 광범위하여 과잉금지원칙 위반이라고 본 부분"),
        o("통신자료 제공요청 조항은 사후통지절차를 두지 않아 적법절차원칙에 위배되고 개인정보자기결정권을 침해한다."),
    ],
}


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def basis(no: int) -> tuple[str, str, str]:
    topic = TOPICS[no]
    if no == 16:
        return ("헌법+국가인권위원회법+판례", f"{topic} 관련 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    if no in {6, 9, 13, 14, 20}:
        return ("헌법+관련 법령+판례", f"{topic} 관련 헌법·법률 조문 및 판례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")
    return ("헌법+헌재판례", f"{topic} 관련 헌법 조문 및 헌법재판소 결정례", f"{topic}의 출제 지점을 독립 명제로 정리한다.")


def normalize_raw(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def extract_question_blocks() -> dict[int, str]:
    text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="replace")
    start = text.find("【헌 법 20문】")
    if start == -1:
        raise ValueError("cannot locate 2024 constitution section")
    end = text.find("【상 법 30문】", start)
    section = text[start : end if end != -1 else len(text)]
    matches = [m for m in re.finditer(r"【문\s*(\d+)】", section) if 1 <= int(m.group(1)) <= 20]
    if len(matches) != QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} constitution questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches):
        no = int(match.group(1))
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        blocks[no] = section[match.start() : end_pos]
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
        statement = re.split(r"\s*제1과목\s*①책형|\s*【\s*제1과목", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in range(1, 21):
        split = split_choice_units(blocks[no])
        for label in LABELS:
            raw[(no, label)] = split[label]
    return raw


def source_verdict(no: int, label: str) -> str:
    qtype = QUESTION_TYPES[no]
    answer = OFFICIAL_ANSWERS[no]
    if qtype == "single-best-false":
        return "X" if label == answer else "O"
    if qtype == "single-best-true":
        return "O" if label == answer else "X"
    raise ValueError(f"unknown qtype: {qtype}")


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in range(1, 21):
        qid = f"2024-g1-constitution-{no:02d}"
        units = []
        for idx, label in enumerate(LABELS, start=1):
            units.append(
                {
                    "unitId": f"{qid}-{idx:02d}",
                    "unitType": "choice",
                    "label": label,
                    "rawStatement": raws[(no, label)],
                    "originalVerdict": source_verdict(no, label),
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
                "type": QUESTION_TYPES[no],
                "officialAnswer": OFFICIAL_ANSWERS[no],
                "units": units,
            }
        )
    return {
        "schema": "legal-scrivener/source-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subject": SUBJECT_NAME,
        "updatedAt": today(),
        "questionCount": QUESTION_COUNT,
        "verificationSources": LEGAL_SOURCES,
        "questions": questions,
    }


def build_queue(source: dict[str, object]) -> dict[str, object]:
    items = []
    for question in source["questions"]:
        for unit in question["units"]:
            items.append(
                {
                    "unitId": unit["unitId"],
                    "sourceFamily": "법무사시험",
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


def build_completed(queue: dict[str, object]) -> dict[str, object]:
    items = []
    for idx, qitem in enumerate(queue["items"], start=1):
        no = qitem["no"]
        label = qitem["unitLabel"]
        label_idx = LABELS.index(label)
        rep_row = REPS[no][label_idx]
        source_verdict_value = qitem["originalVerdict"]
        if (source_verdict_value == "X") != (rep_row["trap"] is not None):
            raise ValueError(f"rep trap mismatch for q{no} {label}")
        basis_type, basis_ref, why = basis(no)
        rep = rep_row["rep"]
        items.append(
            {
                "atomId": f"bupmusa-2024-constitution-q{no:02d}-{label_idx + 1:02d}",
                "sourceUnitId": qitem["unitId"],
                "sourceFamily": "법무사시험",
                "source": qitem["source"],
                "year": YEAR,
                "round": ROUND,
                "subject": SUBJECT_NAME,
                "no": no,
                "unitType": qitem["unitType"],
                "unitLabel": label,
                "sourceQuestionType": qitem["sourceQuestionType"],
                "officialQuestionAnswer": qitem["officialQuestionAnswer"],
                "sourceVerdict": source_verdict_value,
                "currentVerdict": "O",
                "rep": rep,
                "a": "O",
                "basisType": basis_type,
                "basisRef": basis_ref,
                "why": why,
                "sourceStatement": qitem["rawStatement"],
                "sourceTrap": rep_row["trap"],
                "xDependsOn": rep if source_verdict_value == "X" else None,
                "reviewedAt": today(),
                "currentLawCheckedAt": today(),
            }
        )
    return {
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
        "atomCount": len(items),
        "verificationSources": LEGAL_SOURCES,
        "policy": {
            "sourceStatement": "문제 원문 지문은 보존한다.",
            "rep": "화면 출력용 atom은 O인 자기완결 법리 문장으로 작성한다.",
            "xHandling": "출제 원문상 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형 문제는 선택지 조합이 아니라 ㄱ·ㄴ·ㄷ 등 개별 근거명제로 atom화한다.",
        },
        "items": items,
    }


def validate(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if source["questionCount"] != QUESTION_COUNT:
        raise ValueError("question count mismatch")
    if queue["itemCount"] != EXPECTED_ATOM_COUNT or completed["atomCount"] != EXPECTED_ATOM_COUNT:
        raise ValueError("atom count mismatch")
    counts = Counter(item["no"] for item in completed["items"])
    if counts != Counter({no: 5 for no in range(1, 21)}):
        raise ValueError(f"question atom counts mismatch: {counts}")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 77, "X": 23}):
        raise ValueError(f"verdict counts mismatch: {verdict_counts}")
    for item in completed["items"]:
        rep = item["rep"]
        if any(token in rep for token in ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "위 설명", "다음 설명", "가장 옳"]):
            raise ValueError(f"non-atomic wording detected: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or not item["xDependsOn"]:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        else:
            if item["sourceTrap"] is not None or item["xDependsOn"] is not None:
                raise ValueError(f"unexpected X metadata: {item['atomId']}")


def update_index(completed: dict[str, object], queue: dict[str, object], source: dict[str, object]) -> None:
    if SUBJECT_INDEX_PATH.exists():
        index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
    else:
        index = {
            "schema": "legal-scrivener/subject-index/v1",
            "sourceFamily": "법무사시험",
            "examId": EXAM_ID,
            "year": YEAR,
            "round": ROUND,
            "subjects": {},
        }
    index["updatedAt"] = today()
    index["subjects"][SUBJECT_NAME] = {
        "source": str(SOURCE_PATH),
        "atomQueue": str(QUEUE_PATH),
        "completedAtoms": str(OUT_PATH),
        "questionCount": source["questionCount"],
        "atomQueueItemCount": queue["itemCount"],
        "completedAtomCount": completed["atomCount"],
        "completedAtomsUpdatedAt": completed["updatedAt"],
    }
    SUBJECT_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = extract_question_blocks()
    raws = raw_statement_map(blocks)
    source = build_source(raws)
    queue = build_queue(source)
    completed = build_completed(queue)
    validate(source, queue, completed)

    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_PATH.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_index(completed, queue, source)

    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    print(
        json.dumps(
            {
                "subject": SUBJECT_NAME,
                "source": str(SOURCE_PATH),
                "queue": str(QUEUE_PATH),
                "completed": str(OUT_PATH),
                "questions": source["questionCount"],
                "atoms": completed["atomCount"],
                "verdictCounts": dict(verdict_counts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
