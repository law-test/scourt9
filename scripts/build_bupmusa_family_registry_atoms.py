from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2025" / "과목별"
QUEUE_PATH = SUBJECT_DIR / "2025_법무사_가족관계등록법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2025_법무사_가족관계등록법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2025_법무사_과목별_index.json"

SUBJECT_NAME = "가족관계의 등록 등에 관한 법률"

LEGAL_SOURCES = [
    {
        "title": "가족관계의 등록 등에 관한 법률",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/LSW/lsInfoP.do?lsId=010444",
    },
    {
        "title": "가족관계의 등록 등에 관한 규칙",
        "publisher": "국가법령정보센터",
        "url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=188000",
    },
    {
        "title": "2025년 제31회 법무사 1차 가족관계등록법 해설",
        "publisher": "박문각 공개 해설 PDF",
        "url": "https://att.pmg.co.kr/EtcData/board/5123/2025%EB%85%84%2031%ED%9A%8C%20%EB%B2%95%EB%AC%B4%EC%82%AC1%EC%B0%A8%20%EA%B0%80%EC%A1%B1%EA%B4%80%EA%B3%84%EC%9D%98%20%EB%93%B1%EB%A1%9D%20%EB%93%B1%EC%97%90%20%EA%B4%80%ED%95%9C%20%EB%B2%95%EB%A5%A0%20%EB%AC%B8%EC%A0%9C%2C%20%ED%95%B4%EC%84%A4.pdf",
    },
]


def row(
    rep: str,
    basis_type: str,
    basis_ref: str,
    why: str,
    *,
    trap: str | None = None,
    source_verdict: str | None = None,
) -> dict[str, str | None]:
    return {
        "rep": rep,
        "basisType": basis_type,
        "basisRef": basis_ref,
        "why": why,
        "trap": trap,
        "sourceVerdict": source_verdict,
    }


ROWS: dict[int, list[dict[str, str | None]]] = {
    41: [
        row(
            "등록기준지 변경신고는 새롭게 변경하고자 하는 등록기준지를 관할하는 시·읍·면장에게 하여야 한다.",
            "규칙",
            "가족관계등록규칙 제4조 제3항",
            "등록기준지는 자유롭게 변경할 수 있으나 신고 관할은 새 등록기준지 시·읍·면장으로 정해져 있다.",
            trap="현재지 시·읍·면장에게 변경신고를 할 수 있다는 부분",
        ),
        row(
            "가족관계등록창설허가를 받은 사람이 등록창설신고를 하지 않으면 배우자 또는 직계혈족이 신고할 수 있고, 허가 후 신고 전에 사망한 사람에 대해서도 배우자 또는 직계혈족이 신고한다.",
            "조문",
            "가족관계등록법 제102조",
            "등록창설허가를 받은 사람이 신고하지 않은 경우 배우자 또는 직계혈족의 보충적 신고가 인정된다.",
        ),
        row(
            "이혼이 무효 또는 취소된 경우 미성년 자녀의 친권자 지정·신고 기록은 별도 정정허가 없이 이혼무효 또는 이혼취소 판결·심판에 따라 말소할 수 있다.",
            "예규",
            "가족관계등록예규 제254호",
            "이혼무효·취소로 정리되는 등록부 기록에는 그 이혼을 전제로 한 친권자 지정·신고 기록도 포함된다.",
        ),
        row(
            "한자 성의 한글표기 정정 효력은 사건본인에게만 미치지만, 직계비속이 있으면 규칙 제55조 제3항과 제60조 제2항 제4호를 준용하여 직계비속의 한글표기도 직권정정한다.",
            "예규+규칙",
            "가족관계등록예규 제588호, 가족관계등록규칙 제55조 제3항, 제60조 제2항 제4호",
            "성 표기 정정 효력은 원칙적으로 사건본인에게 한정되지만 직계비속 표기는 직권정정 절차로 맞춘다.",
        ),
        row(
            "가족관계등록부를 정정할 때 그 사항이 기재된 제적부도 필요최소한으로 정정하지만, 가족관계등록부 정정허가결정만으로 제적부를 정정할 수는 없다.",
            "예규",
            "가족관계등록예규 제297호 제2조",
            "가족관계등록부와 제적부 정정은 연결되지만 제적부 정정에는 별도의 근거가 필요하다.",
        ),
    ],
    42: [
        row(
            "미성년후견인이 경질된 경우 후임자는 취임일부터 1개월 이내에 경질 취지를 신고하여야 한다.",
            "조문",
            "가족관계등록법 제81조",
            "미성년후견인 경질신고의 신고의무자는 전임자가 아니라 후임자이고, 기산점은 취임일이다.",
            trap="전임자가 경질일부터 1개월 이내 신고한다는 부분",
        ),
        row(
            "미성년자가 성년이 되어 미성년후견감독이 종료된 경우에는 미성년후견감독 종료신고를 하지 않는다.",
            "조문",
            "가족관계등록법 제83조의5",
            "미성년후견감독 종료신고는 원칙적으로 감독인이 하지만, 미성년자의 성년 도달로 종료된 경우는 예외이다.",
            trap="성년 도달로 종료된 경우에도 감독인이 1개월 이내 종료신고를 해야 한다는 부분",
        ),
        row(
            "미성년후견에 관한 사항은 미성년자의 등록부 일반등록사항란에 기록하고, 미성년후견인의 등록부에는 기록하지 않는다.",
            "규칙",
            "가족관계등록규칙 제53조",
            "친권·관리권·미성년후견 사항은 미성년자 등록부에 기록하는 사항이다.",
            trap="미성년자와 미성년후견인 양쪽 등록부에 모두 기록한다는 부분",
        ),
        row(
            "신고의무자가 미성년후견인인 경우에는 미성년자가 법 제26조에 따라 대신 신고할 수 없다.",
            "조문",
            "가족관계등록법 제26조, 제80조, 제81조, 제83조",
            "법 제26조는 신고할 사람이 미성년자인 경우의 보충 규정이고, 신고의무자가 후견인인 경우에는 적용되지 않는다.",
            trap="미성년자가 미성년후견인의 신고를 대신할 수 있다는 부분",
        ),
        row(
            "미성년후견인 또는 미성년후견감독인이 개명하여도 미성년자의 일반등록사항란에 기록된 후견인·감독인 성명은 정정할 필요가 없다.",
            "예규",
            "가족관계등록예규 제369호",
            "후견인·후견감독인의 개명은 미성년자 등록부 일반등록사항란의 성명 정정 사유가 아니다.",
        ),
    ],
    43: [
        row(
            "가족관계등록법 제16조의 등록부 기록절차에는 통보가 포함된다.",
            "조문",
            "가족관계등록법 제16조",
            "등록부는 신고, 통보, 신청, 증서의 등본, 항해일지의 등본 또는 재판서에 의하여 기록한다.",
        ),
        row(
            "가족관계등록법 제16조의 등록부 기록절차에는 재판서가 포함된다.",
            "조문",
            "가족관계등록법 제16조",
            "등록부는 신고, 통보, 신청, 증서의 등본, 항해일지의 등본 또는 재판서에 의하여 기록한다.",
        ),
        row(
            "가족관계등록법 제16조의 등록부 기록절차에는 촉탁이 포함되지 않는다.",
            "조문",
            "가족관계등록법 제16조",
            "제16조가 열거한 기록절차에는 촉탁이 들어 있지 않다.",
            trap="촉탁을 제16조의 기록절차로 본 부분",
        ),
        row(
            "가족관계등록법 제16조의 등록부 기록절차에는 항해일지의 등본이 포함된다.",
            "조문",
            "가족관계등록법 제16조",
            "등록부는 신고, 통보, 신청, 증서의 등본, 항해일지의 등본 또는 재판서에 의하여 기록한다.",
        ),
        row(
            "가족관계등록법 제16조의 등록부 기록절차에는 보고가 포함되지 않는다.",
            "조문",
            "가족관계등록법 제16조",
            "제16조가 열거한 기록절차에는 보고가 들어 있지 않다.",
            trap="보고를 제16조의 기록절차로 본 부분",
        ),
    ],
    44: [
        row(
            "협의이혼의사확인 절차에서 확인기일, 보정명령, 불확인결과는 전화나 팩시밀리 등 간이한 방법으로 통지할 수 있다.",
            "규칙",
            "가족관계등록규칙 제73조 제6항",
            "협의이혼의사확인 절차상 일정한 통지는 간이한 방법으로 할 수 있다.",
        ),
        row(
            "협의이혼의사확인서등본을 분실한 경우 당사자 쌍방은 언제든지 관할 가정법원에 다시 협의이혼의사확인신청을 할 수 있다.",
            "예규",
            "가족관계등록예규 제613호 제19조",
            "확인서등본 분실은 당사자 쌍방의 재신청으로 해결한다.",
        ),
        row(
            "양육비부담조서의 집행문은 그 조서가 작성된 협의이혼의사확인사건의 확인서에 따라 이혼신고를 하였음을 소명한 경우에만 내어준다.",
            "규칙",
            "가족관계등록규칙 제78조 제5항",
            "양육비부담조서는 협의이혼신고가 실제로 이루어진 때 집행문 부여가 가능하다.",
        ),
        row(
            "부부 양쪽이 재외국민인 경우 두 사람이 서로 같은 국가에 거주하면 그 거주지를 관할하는 재외공관장에게 함께 이혼의사확인신청을 할 수 있다.",
            "규칙",
            "가족관계등록규칙 제75조 제1항",
            "재외국민 부부의 특례는 같은 국가 거주와 거주지 관할 재외공관을 기준으로 한다.",
            trap="현재지 관할 재외공관장에게 신청할 수 있다는 부분",
        ),
        row(
            "협의이혼의사확인을 받은 재외국민이 이혼의사를 철회하려면 이혼신고 접수 전에 등록기준지 시·읍·면장 또는 가족관계등록관에게 확인서등본 첨부 철회서를 제출하여야 한다.",
            "규칙",
            "가족관계등록규칙 제80조 제1항",
            "재외국민의 이혼의사 철회서는 등록기준지 시·읍·면장 또는 가족관계등록관에게 제출한다.",
        ),
    ],
    45: [
        row(
            "시·읍·면장은 수리한 신고에 흠이 있어 등록부에 기록할 수 없을 때 신고인 또는 신고의무자에게 보완하게 하여야 한다.",
            "조문",
            "가족관계등록법 제39조",
            "신고의 추후 보완 대상자는 신고인 또는 신고의무자이다.",
            trap="신고인으로만 한정한 부분",
        ),
        row(
            "시·읍·면장은 수리한 신고에 흠이 있어 등록부에 기록할 수 없을 때 신고인 또는 신고의무자에게 보완하게 하여야 한다.",
            "조문",
            "가족관계등록법 제39조",
            "신고의 추후 보완 대상자는 신고인 또는 신고의무자이다.",
            trap="신고사건의 본인에게 보완하게 한다는 부분",
        ),
        row(
            "시·읍·면장은 수리한 신고에 흠이 있어 등록부에 기록할 수 없을 때 신고인 또는 신고의무자에게 보완하게 하여야 한다.",
            "조문",
            "가족관계등록법 제39조",
            "신고의 추후 보완 대상자는 신고인 또는 신고의무자이다.",
            trap="신고의무자로만 한정한 부분",
        ),
        row(
            "시·읍·면장은 수리한 신고에 흠이 있어 등록부에 기록할 수 없을 때 신고인 또는 신고의무자에게 보완하게 하여야 한다.",
            "조문",
            "가족관계등록법 제39조",
            "신고의 추후 보완 대상자는 신고인 또는 신고의무자이다.",
        ),
        row(
            "시·읍·면장은 수리한 신고에 흠이 있어 등록부에 기록할 수 없을 때 신고인 또는 신고의무자에게 보완하게 하여야 한다.",
            "조문",
            "가족관계등록법 제39조",
            "신고의 추후 보완 대상자는 신고인 또는 신고의무자이다.",
            trap="신고인 또는 신고사건의 본인에게 보완하게 한다는 부분",
        ),
    ],
    46: [
        row(
            "국적상실신고는 배우자 또는 4촌 이내 친족이 그 사실을 안 날부터 1개월 이내에 하여야 한다.",
            "조문",
            "가족관계등록법 제97조 제1항",
            "국적상실신고의 기산점은 국적상실 사실을 안 날이다.",
        ),
        row(
            "인지된 태아가 사체로 분만된 경우 출생신고의무자는 그 사실을 안 날부터 1개월 이내에 신고하여야 한다.",
            "조문",
            "가족관계등록법 제60조",
            "인지된 태아의 사산 신고도 사실을 안 날을 기산점으로 한다.",
        ),
        row(
            "등록불명자·무등록자 등에 관한 신고가 수리된 뒤 등록되어 있음이 판명되거나 등록할 수 있게 된 때에는 신고인 또는 신고사건 본인이 그 사실을 안 날부터 1개월 이내에 신고하여야 한다.",
            "조문",
            "가족관계등록법 제22조",
            "신고 후 등록 가능성이 판명된 경우의 신고기한은 그 사실을 안 날부터 계산한다.",
        ),
        row(
            "유언에 의한 인지의 경우 유언집행자는 그 취임일부터 1개월 이내에 신고하여야 한다.",
            "조문",
            "가족관계등록법 제59조",
            "유언에 의한 인지는 유언집행자의 취임일을 기산점으로 한다.",
            trap="그 사실을 안 날을 기산점으로 본 부분",
        ),
    ],
    47: [
        row(
            "동사무소에는 가족관계등록신고서류편철장을 비치하여야 하고 그 보존기간은 3년이다.",
            "규칙",
            "가족관계등록규칙 제82조 제4항 제10호",
            "동사무소에 비치하는 가족관계등록신고서류편철장의 보존기간은 3년이다.",
        ),
        row(
            "신고를 게을리한 사람을 안 때 신고의무자에게 신고를 최고하는 기관은 동장이 아니라 시·읍·면장이다.",
            "조문",
            "가족관계등록법 제38조 제1항",
            "신고의 최고 권한은 시·읍·면장에게 있다.",
            trap="동장이 신고 최고를 한다는 부분",
        ),
        row(
            "증서의 등본 제출방식에 의한 가족관계등록부 기록은 재외공관장, 등록기준지 시·구·읍·면장 또는 가족관계등록관에게 제출하는 절차이고, 동장에게 제출하는 절차가 아니다.",
            "예규",
            "가족관계등록예규 제486호",
            "외국 거주 한국인의 증서 등본 제출은 재외공관장 등 정해진 기관을 통하여 한다.",
            trap="신분행위 당사자 1명이 동장에게 제출할 수 있다는 부분",
        ),
        row(
            "친족·동거자, 사망장소를 관리하는 사람, 사망장소의 동장 또는 통·이장도 사망신고를 할 수 있다.",
            "조문",
            "가족관계등록법 제85조 제2항",
            "사망장소의 동장은 사망신고를 할 수 있는 사람에 포함된다.",
            trap="사망장소의 동장은 사망신고를 할 수 없다는 부분",
        ),
        row(
            "동사무소에서 수리한 신고서류 부본은 접수순서에 따라 편철하고 1개월마다 목록을 붙여 보존한다.",
            "규칙",
            "가족관계등록규칙 제68조 제4항",
            "동사무소 수리 신고서류 부본의 편철 목록 주기는 1개월이다.",
            trap="3개월마다 목록을 붙여 보존한다는 부분",
        ),
    ],
    48: [
        row(
            "등록불명자 등의 사망에서 경찰 통보 후 제85조의 신고의무자가 사망자의 신원을 안 때에는 그 날부터 10일 이내에 사망신고를 하여야 한다.",
            "조문",
            "가족관계등록법 제90조 제3항",
            "등록불명자 등의 사망 후 신원을 안 경우의 신고기간은 10일이다.",
            trap="1개월 이내로 본 부분",
        ),
        row(
            "등록불명자 등의 사망에서 경찰 통보 후 제85조의 신고의무자가 사망자의 신원을 안 때에는 그 날부터 10일 이내에 사망신고를 하여야 한다.",
            "조문",
            "가족관계등록법 제90조 제3항",
            "등록불명자 등의 사망 후 신원을 안 경우의 신고기간은 10일이다.",
            trap="20일 이내로 본 부분",
        ),
        row(
            "등록불명자 등의 사망에서 경찰 통보 후 제85조의 신고의무자가 사망자의 신원을 안 때에는 그 날부터 10일 이내에 사망신고를 하여야 한다.",
            "조문",
            "가족관계등록법 제90조 제3항",
            "등록불명자 등의 사망 후 신원을 안 경우의 신고기간은 10일이다.",
        ),
        row(
            "등록불명자 등의 사망에서 경찰 통보 후 제85조의 신고의무자가 사망자의 신원을 안 때에는 그 날부터 10일 이내에 사망신고를 하여야 한다.",
            "조문",
            "가족관계등록법 제90조 제3항",
            "등록불명자 등의 사망 후 신원을 안 경우의 신고기간은 10일이다.",
            trap="7일 이내로 본 부분",
        ),
        row(
            "등록불명자 등의 사망에서 경찰 통보 후 제85조의 신고의무자가 사망자의 신원을 안 때에는 그 날부터 10일 이내에 사망신고를 하여야 한다.",
            "조문",
            "가족관계등록법 제90조 제3항",
            "등록불명자 등의 사망 후 신원을 안 경우의 신고기간은 10일이다.",
            trap="5일 이내로 본 부분",
        ),
    ],
    49: [
        row(
            "제적부를 정정할 때에는 제적부를 부활하지 않고 정정한다.",
            "예규",
            "가족관계등록예규 제297호 제3조",
            "제적부 정정은 제적부 부활 없이 해당사항을 정정하는 방식으로 한다.",
            trap="제적부를 부활한 후 정정한다는 부분",
        ),
        row(
            "혼인 등 신고로 효력이 발생하는 행위는 등록부 기록 후 실체상 흠결이 발견되어도 가족관계등록법 제18조 제2항에 따라 정정할 수 없다.",
            "예규",
            "가족관계등록예규 제57호",
            "신고로 효력이 발생한 신분행위의 실체상 흠결은 가족관계등록법 제18조 제2항 직권정정 대상이 아니다.",
        ),
        row(
            "판결에 의해서만 할 수 있는 가족관계등록부 기록정정을 법원의 정정허가만으로 한 경우에는 위법하여 정정 효력이 발생하지 않는다.",
            "예규",
            "가족관계등록예규 제423호",
            "판결정정 사항과 허가정정 사항은 구별되며, 판결정정 사항을 허가만으로 정정할 수 없다.",
            trap="정정허가를 받으면 적법한 정정 효력이 발생한다는 부분",
        ),
        row(
            "법원의 허가에 의한 가족관계등록부정정은 재판 주문에 나타난 사항에 한하여 허용된다.",
            "예규",
            "가족관계등록예규 제422호",
            "허가에 의한 등록부정정의 허용범위는 재판 주문에 나타난 사항으로 제한된다.",
            trap="재판 이유에 나타난 사항까지 허용된다는 부분",
        ),
        row(
            "등록부 기록사항을 정정하는 경우에는 정정할 부분에 새로운 사항을 기록하고 정정내용과 사유를 해당 사항란에 기록한다.",
            "규칙",
            "가족관계등록규칙 제66조 제1항",
            "일반 정정은 새로운 사항과 정정내용·사유를 기록하는 방식이고, 선을 긋는 방식은 사건 자체 말소에 관한 규정이다.",
            trap="일반등록사항란 정정 시 정정할 부분에 하나의 선을 긋는다는 부분",
        ),
    ],
    50: [
        row(
            "친양자 파양 재판 확정의 경우에는 소의 상대방도 재판서 등본과 확정증명서를 첨부하여 신고할 수 있다.",
            "조문",
            "가족관계등록법 제69조 제3항",
            "친양자 파양 재판 확정 신고에는 소의 상대방 신고적격이 명시되어 있다.",
            source_verdict="O",
        ),
        row(
            "사실상 혼인관계 존재확인 재판 확정의 경우에는 소를 제기한 사람이 신고의무자이고, 소의 상대방에게 별도 신고적격이 인정되지 않는다.",
            "조문",
            "가족관계등록법 제72조",
            "사실상 혼인관계 존재확인 재판의 신고자는 소를 제기한 사람으로 규정된다.",
            trap="소의 상대방도 신고할 수 있다고 본 부분",
            source_verdict="X",
        ),
        row(
            "혼인취소 재판 확정의 경우에는 제58조가 준용되므로 소의 상대방도 신고할 수 있다.",
            "조문",
            "가족관계등록법 제73조, 제58조 제3항",
            "혼인취소 재판에는 제58조의 상대방 신고 규정이 준용된다.",
            source_verdict="O",
        ),
        row(
            "입양취소 재판 확정의 경우에는 제58조가 준용되므로 소의 상대방도 신고할 수 있다.",
            "조문",
            "가족관계등록법 제65조 제2항, 제58조 제3항",
            "입양취소 재판에는 제58조의 상대방 신고 규정이 준용된다.",
            source_verdict="O",
        ),
        row(
            "미성년후견인 선임재판 확정은 소의 상대방에게 신고적격이 인정되는 경우가 아니다.",
            "조문",
            "가족관계등록법 제80조",
            "미성년후견 개시신고는 미성년후견인이 취임일부터 1개월 이내에 하는 신고이다.",
            trap="소의 상대방도 신고할 수 있다고 본 부분",
            source_verdict="X",
        ),
    ],
}

BOX_CODES = ["ga", "na", "da", "ra", "ma"]


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def atom_id(no: int, idx: int, unit_type: str) -> str:
    code = BOX_CODES[idx] if unit_type == "box" else f"{idx + 1:02d}"
    return f"bupmusa-2025-family-registry-q{no:02d}-{code}"


def group_items(items: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for item in items:
        grouped[int(item["no"])].append(item)
    return dict(grouped)


def source_verdict(item: dict, spec: dict[str, str | None]) -> str:
    verdict = spec.get("sourceVerdict") or item.get("originalVerdict")
    if verdict not in {"O", "X"}:
        raise ValueError(f"source verdict is required for {item['unitId']}")
    return verdict


def validate(atoms: list[dict], queue_items: list[dict]) -> None:
    if len(atoms) != len(queue_items):
        raise ValueError(f"atom count mismatch: atoms={len(atoms)} queue={len(queue_items)}")

    ids = [item["atomId"] for item in atoms]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")

    bad_patterns = [
        r"\?",
        r"위\s*[①②③④⑤ㄱㄴㄷㄹㅁ]",
        r"위의\s*[①②③④⑤ㄱㄴㄷㄹㅁ]",
        r"옳은 것은",
        r"옳지 않은 것은",
        r"다음 중",
        r"몇 개인가",
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
        if atom["sourceVerdict"] == "X":
            if not atom.get("sourceTrap") or not atom.get("xDependsOn"):
                raise ValueError(f"X source must have trap and dependency: {atom['atomId']}")
        if atom["currentVerdict"] != "O" or atom["a"] != "O":
            raise ValueError(f"completed atom must be O: {atom['atomId']}")


def build_atoms(queue: dict) -> list[dict]:
    grouped = group_items(queue["items"])
    if set(grouped) != set(ROWS):
        raise ValueError(f"question coverage mismatch: queue={sorted(grouped)} rows={sorted(ROWS)}")

    atoms: list[dict] = []
    checked_at = today()
    for no in sorted(grouped):
        specs = ROWS[no]
        items = grouped[no]
        if len(items) != len(specs):
            raise ValueError(f"row count mismatch for question {no}: queue={len(items)} rows={len(specs)}")
        for idx, (item, spec) in enumerate(zip(items, specs)):
            verdict = source_verdict(item, spec)
            atom = {
                "atomId": atom_id(no, idx, item["unitType"]),
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
                "sourceVerdict": verdict,
                "currentVerdict": "O",
                "rep": spec["rep"],
                "a": "O",
                "basisType": spec["basisType"],
                "basisRef": spec["basisRef"],
                "why": spec["why"],
                "sourceStatement": item["rawStatement"],
                "sourceTrap": spec["trap"] if verdict == "X" else None,
                "xDependsOn": spec["rep"] if verdict == "X" else None,
                "reviewedAt": checked_at,
                "currentLawCheckedAt": checked_at,
            }
            atoms.append(atom)
    validate(atoms, queue["items"])
    return atoms


def update_subject_index(atom_count: int) -> None:
    if not SUBJECT_INDEX_PATH.exists():
        return
    index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
    subjects = index.setdefault("subjects", {})
    target = None
    for key, value in subjects.items():
        text = f"{key} {value.get('subject', '')} {value.get('atomQueue', '')}"
        if "가족관계" in text or "가족관계등록법" in text:
            target = value
            break
    if target is None:
        target = subjects.setdefault(SUBJECT_NAME, {"subject": SUBJECT_NAME})
    target["completedAtoms"] = str(OUT_PATH)
    target["completedAtomCount"] = atom_count
    target["completedAtomsUpdatedAt"] = today()
    SUBJECT_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build() -> Path:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    atoms = build_atoms(queue)
    doc = {
        "schema": "legal-scrivener/completed-atoms-by-subject/v1",
        "sourceFamily": "법무사시험",
        "examId": queue["examId"],
        "year": queue["year"],
        "round": queue["round"],
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
    }
    OUT_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_subject_index(len(atoms))
    return OUT_PATH


def main() -> None:
    out = build()
    data = json.loads(out.read_text(encoding="utf-8"))
    by_verdict: dict[str, int] = {}
    by_basis: dict[str, int] = {}
    for item in data["items"]:
        by_verdict[item["sourceVerdict"]] = by_verdict.get(item["sourceVerdict"], 0) + 1
        by_basis[item["basisType"]] = by_basis.get(item["basisType"], 0) + 1
    print(f"atoms={out}")
    print(f"atomCount={data['atomCount']}")
    print("sourceVerdict=" + ", ".join(f"{key}:{value}" for key, value in sorted(by_verdict.items())))
    print("basis=" + ", ".join(f"{key}:{value}" for key, value in sorted(by_basis.items())))
    for sample in data["items"][:3]:
        print(f"{sample['atomId']} {sample['rep']}")


if __name__ == "__main__":
    main()
