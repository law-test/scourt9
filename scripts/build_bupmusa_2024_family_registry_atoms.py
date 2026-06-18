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
SOURCE_PATH = SUBJECT_DIR / "2024_법무사_가족관계등록법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2024_법무사_가족관계등록법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2024_법무사_가족관계등록법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2024_법무사_과목별_index.json"

SUBJECT_NAME = "가족관계의 등록 등에 관한 법률"
EXAM_ID = "2024_bupmusa_1st"
YEAR = 2024
ROUND = 30
GROUP = 2

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
        "title": "2024 법무사 전과목 문제 정답",
        "publisher": "공기출",
        "url": "https://0gichul.com/y2024/130881278",
    },
]


def unit(
    no: int,
    code: str,
    label: str,
    raw: str,
    source_verdict: str,
    rep: str,
    basis_type: str,
    basis_ref: str,
    why: str,
    *,
    trap: str | None = None,
    source_question_type: str | None = None,
    official_answer: str | None = None,
    unit_type: str = "choice",
) -> dict[str, str | int | None]:
    return {
        "no": no,
        "code": code,
        "label": label,
        "raw": raw,
        "sourceVerdict": source_verdict,
        "rep": rep,
        "basisType": basis_type,
        "basisRef": basis_ref,
        "why": why,
        "trap": trap,
        "sourceQuestionType": source_question_type,
        "officialAnswer": official_answer,
        "unitType": unit_type,
    }


UNITS = [
    unit(
        41,
        "01",
        "①",
        "혼인은 가족관계의 등록 등에 관한 법률에 정한 바에 의하여 신고함으로써 그 효력이 생기며, 그 신고는 당사자 쌍방과 성년자인 증인 2인의 연서한 서면으로 하여야 한다.",
        "O",
        "혼인은 가족관계등록법에 따른 신고로 효력이 생기며, 신고는 당사자 쌍방과 성년자인 증인 2인의 연서한 서면으로 하여야 한다.",
        "조문",
        "민법 제812조",
        "혼인신고는 창설적 신고이고 증인 2인의 연서가 요구된다.",
        source_question_type="single-best-false",
        official_answer="③",
    ),
    unit(
        41,
        "02",
        "②",
        "협의상이혼 신고서에 가정법원의 이혼의사확인서등본을 첨부한 경우에는 증인 2인의 연서가 있는 것으로 본다.",
        "O",
        "협의이혼신고서에 가정법원의 이혼의사확인서등본을 첨부하면 민법상 증인 2인의 연서가 있는 것으로 본다.",
        "조문",
        "가족관계등록법 제76조",
        "가족관계등록법은 협의이혼신고의 확인서등본 첨부를 증인 연서로 의제한다.",
        source_question_type="single-best-false",
        official_answer="③",
    ),
    unit(
        41,
        "03",
        "③",
        "입양은 가족관계의 등록 등에 관한 법률에서 정한 바에 따라 신고함으로써 그 효력이 생기며, 그 신고는 당사자 쌍방과 성년자인 증인 2인의 연서한 서면으로 하여야 한다.",
        "X",
        "미성년자를 양자로 하는 입양은 가정법원의 허가가 있어야 하므로, 모든 입양이 신고만으로 곧바로 효력을 발생하는 것은 아니다.",
        "조문",
        "민법 제867조, 제878조",
        "입양은 신고가 원칙적 효력요건이나 미성년자 입양에는 가정법원 허가요건이 추가된다.",
        trap="미성년자 입양의 가정법원 허가요건을 누락하고 모든 입양이 신고만으로 효력을 발생한다고 한 부분",
        source_question_type="single-best-false",
        official_answer="③",
    ),
    unit(
        41,
        "04",
        "④",
        "증인을 필요로 하는 사건의 신고에서 증인은 신고서에 주민등록번호 및 주소를 기재하고 서명하거나 기명날인하여야 하며, 서명 또는 기명날인을 할 수 없을 때에는 무인할 수 있다.",
        "O",
        "증인이 필요한 신고에서 증인은 신고서에 주민등록번호와 주소를 적고 서명하거나 기명날인하여야 하며, 서명·날인이 어려우면 무인할 수 있다.",
        "조문+규칙",
        "가족관계등록법 제28조, 가족관계등록규칙 제33조",
        "증인의 인적사항과 서명·기명날인 또는 무인 방식은 법과 규칙에서 정한다.",
        source_question_type="single-best-false",
        official_answer="③",
    ),
    unit(
        41,
        "05",
        "⑤",
        "성년자인 증인 2인의 연서 없는 혼인신고가 수리된 경우 그 위반은 민법상 혼인무효 또는 취소사유가 아니지만 수리 당시 발견되면 수리를 거부하여야 한다.",
        "O",
        "성년자인 증인 2인의 연서 없는 혼인신고가 수리된 경우 그 흠은 민법상 혼인무효·취소사유가 아니나, 수리 전에 발견되면 수리를 거부하여야 한다.",
        "조문+예규",
        "민법 제813조, 가족관계등록 실무선례",
        "증인 연서 흠은 수리 전 심사단계에서는 거부사유가 되지만 이미 성립한 혼인의 무효·취소사유와는 구별된다.",
        source_question_type="single-best-false",
        official_answer="③",
    ),
    unit(
        42,
        "01",
        "①",
        "인터넷에 의한 등록사항별 증명서의 발급은 본인 또는 배우자, 부모, 자녀가 신청할 수 있고, 친양자입양관계증명서는 친양자가 성년이 되어 신청하는 경우에 한한다.",
        "O",
        "인터넷 등록사항별 증명서 발급은 본인 또는 배우자·부모·자녀가 신청할 수 있고, 친양자입양관계증명서의 인터넷 발급은 친양자가 성년이 되어 신청하는 경우로 제한된다.",
        "조문",
        "가족관계등록법 제14조의2",
        "인터넷 발급 신청권자와 친양자입양관계증명서 발급제한은 법률에서 별도로 정한다.",
        source_question_type="single-best-false",
        official_answer="④",
    ),
    unit(
        42,
        "02",
        "②",
        "가정폭력피해자 또는 그 대리인은 일정한 교부제한대상자를 지정하여 피해자 본인의 등록사항별 증명서 교부를 제한하도록 신청할 수 있다.",
        "O",
        "가정폭력피해자 또는 그 대리인은 피해자의 배우자 또는 직계혈족을 교부제한대상자로 지정하여 피해자 본인의 등록사항별 증명서 교부제한을 신청할 수 있다.",
        "조문",
        "가족관계등록법 제14조 제8항",
        "가정폭력피해자 보호를 위하여 일정한 가족관계자에 대한 증명서 교부제한 제도가 인정된다.",
        source_question_type="single-best-false",
        official_answer="④",
    ),
    unit(
        42,
        "03",
        "③",
        "인터넷에 의한 등록사항별 증명서의 발급수수료는 무료로 한다.",
        "O",
        "인터넷에 의한 등록사항별 증명서 발급수수료는 무료이다.",
        "규칙",
        "가족관계등록규칙 제28조",
        "인터넷 발급수수료는 방문·무인발급 수수료와 달리 무료로 처리된다.",
        source_question_type="single-best-false",
        official_answer="④",
    ),
    unit(
        42,
        "04",
        "④",
        "무인증명서발급기에 의한 등록사항별 증명서의 발급은 본인 또는 배우자, 부모, 자녀가 신청할 수 있다.",
        "X",
        "무인증명서발급기에 의한 등록사항별 증명서 발급은 본인확인절차를 거쳐 본인만 신청할 수 있다.",
        "조문",
        "가족관계등록법 제14조의3",
        "무인증명서발급기는 신청인 본인확인을 전제로 하므로 인터넷 발급의 신청권자 범위와 다르다.",
        trap="무인증명서발급기 신청권자를 배우자·부모·자녀까지 확대한 부분",
        source_question_type="single-best-false",
        official_answer="④",
    ),
    unit(
        42,
        "05",
        "⑤",
        "우편으로 등록사항별 증명서의 송부를 청구하는 경우 신청서 기재사항과 법률상 정당한 청구권자의 신분증명서 사본을 첨부하여야 한다.",
        "O",
        "우편으로 등록사항별 증명서 송부를 청구할 때에는 신청서에 정해진 사항을 적고 법률상 정당한 청구권자의 신분증명서 사본을 첨부하여야 한다.",
        "규칙",
        "가족관계등록규칙 제19조",
        "우편청구는 출석 확인을 대신하여 신분증명서 사본 등 청구권 소명이 요구된다.",
        source_question_type="single-best-false",
        official_answer="④",
    ),
    unit(
        43,
        "01",
        "①",
        "친권자지정신고에서 유언녹음을 기재한 서면 첨부가 가능하다.",
        "X",
        "친권자지정신고는 가족관계등록법상 유언녹음을 기재한 서면 첨부 대상 신고가 아니다.",
        "조문",
        "가족관계등록법 제57조, 제79조",
        "유언에 의한 인지와 달리 친권자지정신고에는 유언녹음 기재서면 첨부 규정이 없다.",
        trap="친권자지정신고를 유언녹음 기재서면 첨부 대상이라고 본 부분",
        source_question_type="single-best-true",
        official_answer="②",
    ),
    unit(
        43,
        "02",
        "②",
        "인지신고에서 유언녹음을 기재한 서면 첨부가 가능하다.",
        "O",
        "유언에 의한 인지신고에는 유언녹음을 기재한 서면을 첨부할 수 있다.",
        "조문",
        "가족관계등록법 제57조",
        "유언에 의한 인지신고는 유언 방식에 따른 첨부서면을 인정한다.",
        source_question_type="single-best-true",
        official_answer="②",
    ),
    unit(
        43,
        "03",
        "③",
        "친양자입양신고에서 유언녹음을 기재한 서면 첨부가 가능하다.",
        "X",
        "친양자입양신고는 가족관계등록법상 유언녹음을 기재한 서면 첨부 대상 신고가 아니다.",
        "조문",
        "가족관계등록법 제67조",
        "친양자입양은 재판에 따른 신고절차로 처리되고 유언녹음 기재서면 첨부 대상이 아니다.",
        trap="친양자입양신고를 유언녹음 기재서면 첨부 대상이라고 본 부분",
        source_question_type="single-best-true",
        official_answer="②",
    ),
    unit(
        43,
        "04",
        "④",
        "사망신고에서 유언녹음을 기재한 서면 첨부가 가능하다.",
        "X",
        "사망신고는 가족관계등록법상 유언녹음을 기재한 서면 첨부 대상 신고가 아니다.",
        "조문",
        "가족관계등록법 제84조, 제85조",
        "사망신고에는 사망사실을 증명하는 서면이 문제될 뿐 유언녹음 기재서면 첨부 규정은 없다.",
        trap="사망신고를 유언녹음 기재서면 첨부 대상이라고 본 부분",
        source_question_type="single-best-true",
        official_answer="②",
    ),
    unit(
        43,
        "05",
        "⑤",
        "입양신고에서 유언녹음을 기재한 서면 첨부가 가능하다.",
        "X",
        "입양신고는 가족관계등록법상 유언녹음을 기재한 서면 첨부 대상 신고가 아니다.",
        "조문",
        "가족관계등록법 제61조",
        "입양신고에는 입양 당사자 신고와 필요한 동의·허가가 문제되고 유언녹음 기재서면 첨부 규정은 없다.",
        trap="입양신고를 유언녹음 기재서면 첨부 대상이라고 본 부분",
        source_question_type="single-best-true",
        official_answer="②",
    ),
    unit(
        44,
        "ga",
        "ㄱ",
        "한쪽 배우자의 가족관계등록부에 혼인의 기록이 있으나 다른 배우자의 가족관계등록부에는 혼인의 기록이 누락된 때",
        "O",
        "한쪽 배우자의 등록부에 혼인 기록이 있으나 다른 배우자의 등록부에는 혼인 기록이 누락된 경우 시·읍·면장은 감독법원 허가 없이 직권정정할 수 있다.",
        "규칙",
        "가족관계등록규칙 제60조 제2항",
        "혼인·이혼 기록 누락의 보정은 대법원규칙이 정한 경미한 직권정정 사항이다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        44,
        "na",
        "ㄴ",
        "신고서류에 의하여 이루어진 가족관계등록부의 기록에 오기나 누락된 부분이 있음이 해당 신고서류에 비추어 명백한 때",
        "O",
        "신고서류에 의한 등록부 기록의 오기나 누락이 해당 신고서류에 비추어 명백하면 시·읍·면장은 감독법원 허가 없이 직권정정할 수 있다.",
        "규칙",
        "가족관계등록규칙 제60조 제2항",
        "명백한 오기·누락은 대법원규칙상 경미한 직권정정 대상이다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        44,
        "da",
        "ㄷ",
        "도로명 또는 건물번호에 관한 가족관계등록부의 기록이 잘못 기재되었거나 빠뜨리게 된 것이 명백한 때",
        "O",
        "도로명 또는 건물번호에 관한 등록부 기록의 잘못이나 누락이 명백하면 시·읍·면장은 감독법원 허가 없이 직권정정할 수 있다.",
        "규칙",
        "가족관계등록규칙 제60조 제2항",
        "주소 표시의 경미한 오류는 직권정정과 감독법원 보고로 처리된다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        44,
        "ra",
        "ㄹ",
        "외국의 국호와 지명에 관한 가족관계등록부의 기록이 외래어표기법에 맞지 않는 때",
        "O",
        "외국의 국호와 지명에 관한 등록부 기록이 외래어표기법에 맞지 않는 경우 시·읍·면장은 감독법원 허가 없이 직권정정할 수 있다.",
        "규칙+예규",
        "가족관계등록규칙 제60조 제2항, 가족관계등록예규 제451호",
        "외국 국호·지명 표기는 외래어표기법에 맞추어 통일할 수 있는 직권정정 사항이다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        44,
        "ma",
        "ㅁ",
        "귀화 또는 국적회복한 외국인의 인명이 우리나라 방식의 성명배열이 아닌 해당 외국방식에 의하여 가족관계등록부에 기록된 때",
        "O",
        "귀화 또는 국적회복한 외국인의 인명이 외국방식 성명배열로 기록된 경우 시·읍·면장은 우리나라 방식 성명배열로 직권정정할 수 있다.",
        "규칙+예규",
        "가족관계등록규칙 제60조 제2항, 가족관계등록예규 제451호",
        "귀화·국적회복자의 인명 배열 정리는 대법원규칙상 경미한 직권정정 대상이다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "ga",
        "ㄱ",
        "관공서의 사망증명서 또는 매장인허증",
        "O",
        "사망신고서에 진단서나 검안서를 첨부할 수 없는 부득이한 사유가 있으면 관공서의 사망증명서 또는 매장인허증을 사망사실 증명서면으로 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "사망진단서·검안서가 없을 때 인정되는 대체 증명서면에 관공서의 사망증명서와 매장인허증이 포함된다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "na",
        "ㄴ",
        "진실화해위원회의 진실규명결정문",
        "O",
        "사망신고서에 진단서나 검안서를 첨부할 수 없는 부득이한 사유가 있으면 진실화해위원회의 진실규명결정문을 사망사실 증명서면으로 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "진실화해위원회의 진실규명결정문은 사망사실을 증명할 수 있는 대체 서면으로 인정된다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "da",
        "ㄷ",
        "정부기록보관소에 보존 중인 재무부 작성의 피수용자사망자연명부",
        "O",
        "사망신고서에 진단서나 검안서를 첨부할 수 없는 부득이한 사유가 있으면 정부기록보관소 보존 피수용자사망자연명부를 사망사실 증명서면으로 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "공적 보존문서인 피수용자사망자연명부는 사망사실을 증명할 수 있는 대체 서면이다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "ra",
        "ㄹ",
        "외국관공서 등에서 발행한 그 나라 방식에 의해 사망신고한 사실을 증명하는 서면",
        "O",
        "사망신고서에 진단서나 검안서를 첨부할 수 없는 부득이한 사유가 있으면 외국관공서 등이 발행한 사망신고 사실 증명서면을 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "외국 방식에 따른 사망신고 사실의 공적 증명서면도 대체 증명서면에 포함된다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "ma",
        "ㅁ",
        "군인이 전투 그 밖의 사변으로 사망한 경우에 부대장 등이 사망사실을 확인하여 그 명의로 작성한 전사확인서",
        "O",
        "군인이 전투 그 밖의 사변으로 사망한 경우 부대장 등이 작성한 전사확인서는 사망사실 증명서면으로 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "전투 등으로 사망한 군인의 사망사실은 부대장 등의 전사확인서로 증명할 수 있다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "ba",
        "ㅂ",
        "동장 및 통장 또는 인우인 2명 이상의 증명서",
        "O",
        "사망신고서에 진단서나 검안서를 첨부할 수 없는 부득이한 사유가 있으면 동장 및 통장 또는 인우인 2명 이상의 증명서를 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "진단서·검안서가 없는 경우 일정한 지역관계자 또는 인우인의 증명서가 대체 증명자료가 될 수 있다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        45,
        "sa",
        "ㅅ",
        "6·25사변으로 인한 사망을 목격한 사람 또는 사망을 확인한 사람 2명 이상의 증명서",
        "O",
        "6·25사변으로 인한 사망을 목격하거나 확인한 사람 2명 이상의 증명서는 사망사실 증명서면으로 첨부할 수 있다.",
        "예규",
        "가족관계등록예규 제276호",
        "6·25사변 관련 사망은 목격자 또는 확인자 2명 이상의 증명서로 사망사실을 증명할 수 있다.",
        source_question_type="multi-select-true",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        46,
        "01",
        "①-가족관계등록창설허가",
        "가족관계등록창설허가는 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "X",
        "가족관계등록창설허가는 원칙적으로 등록하려는 곳을 관할하는 가정법원의 허가사항이고, 주소지만으로 관할이 정해지는 것은 아니다.",
        "조문",
        "가족관계등록법 제101조",
        "가족관계등록창설허가의 관할은 등록기준지 기능과 연결된다.",
        trap="가족관계등록창설허가를 주소지 관할 가정법원 처리사항으로 본 부분",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        46,
        "02",
        "①-등록부정정허가",
        "등록부의 정정허가는 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "X",
        "가족관계등록부 정정허가는 사건본인의 등록기준지를 기준으로 관할을 정하는 것이 원칙이고, 주소지 관할 가정법원 처리사항으로 보지 않는다.",
        "조문",
        "가족관계등록법 제104조",
        "등록부 정정허가는 등록기준지 관할과 연결되는 가족관계등록 비송사항이다.",
        trap="등록부정정허가를 주소지 관할 가정법원 처리사항으로 본 부분",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        46,
        "03",
        "②-개명허가",
        "개명허가는 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "O",
        "개명허가는 주소지를 관할하는 가정법원이 처리하는 경우가 있다.",
        "조문",
        "가족관계등록법 제99조",
        "개명허가 관할에는 주소지 관할 가정법원이 포함된다.",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        46,
        "04",
        "②-귀화허가",
        "귀화허가는 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "X",
        "귀화허가는 가정법원의 가족관계등록 비송사항이 아니라 국적법상 법무부장관의 허가사항이다.",
        "조문",
        "국적법 제4조",
        "귀화허가의 주체와 절차는 가족관계등록 비송사건과 다르다.",
        trap="귀화허가를 주소지 관할 가정법원 처리사항으로 본 부분",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        46,
        "05",
        "③-국적취득자의성과본창설허가",
        "국적취득자의 성과 본 창설허가는 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "O",
        "국적취득자의 성과 본 창설허가는 등록기준지·주소지 또는 등록기준지로 하려는 곳을 관할하는 가정법원의 허가사항이다.",
        "조문",
        "가족관계등록법 제96조",
        "국적취득자의 성과 본 창설허가 관할에는 주소지 관할 가정법원이 포함된다.",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        46,
        "06",
        "④-협의상이혼의확인",
        "협의상이혼의 확인은 주소지 관할 가정법원이 처리하는 경우가 있다.",
        "O",
        "협의상이혼을 하려는 사람은 등록기준지 또는 주소지를 관할하는 가정법원의 확인을 받아 신고하여야 한다.",
        "조문",
        "가족관계등록법 제75조",
        "협의이혼의사확인 관할에는 주소지 관할 가정법원이 포함된다.",
        source_question_type="paired-choice",
        official_answer="④",
    ),
    unit(
        47,
        "ga",
        "ㄱ-A",
        "의료기관의 장은 출생일부터 일정 기간 이내에 출생정보를 건강보험심사평가원에 제출하여야 한다.",
        "O",
        "의료기관의 장은 출생일부터 14일 이내에 출생정보를 건강보험심사평가원에 제출하여야 한다.",
        "조문",
        "가족관계등록법 제44조의3 제2항",
        "출생통보제에서 의료기관의 출생정보 제출기간은 출생일부터 14일이다.",
        source_question_type="fill-blank",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        47,
        "na",
        "ㄴ-B",
        "출생신고가 되지 않은 경우 시·읍·면장은 신고의무자에게 일정 기간 이내에 출생신고를 할 것을 최고하여야 한다.",
        "O",
        "출생신고기간이 지나도록 출생신고가 되지 않은 경우 시·읍·면장은 신고의무자에게 7일 이내에 출생신고를 할 것을 최고하여야 한다.",
        "조문",
        "가족관계등록법 제44조의3 제5항",
        "출생통보 후 미신고 상태가 계속되면 최고기간은 7일로 정해진다.",
        source_question_type="fill-blank",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        47,
        "da",
        "ㄷ-C",
        "시·읍·면장의 최고기간 내에 정당한 사유 없이 신고 또는 신청을 하지 않은 사람에게는 일정 금액 이하의 과태료를 부과한다.",
        "O",
        "시·읍·면장이 정한 최고기간 안에 정당한 사유 없이 신고 또는 신청을 하지 않은 사람에게는 10만 원 이하의 과태료를 부과한다.",
        "조문",
        "가족관계등록법 제122조",
        "최고 이후의 신고해태는 일반 신고기간 해태보다 높은 10만 원 이하 과태료 대상이다.",
        source_question_type="fill-blank",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        48,
        "ga",
        "ㄱ",
        "등록사건을 처리한 시·읍·면의 명칭",
        "O",
        "등록사건을 처리한 시·읍·면의 명칭은 가족관계등록부에 기록될 수 있다.",
        "규칙",
        "가족관계등록규칙 제38조",
        "등록사무 처리기관의 명칭은 등록부 기록사항에 포함될 수 있다.",
        source_question_type="multi-select-false",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        48,
        "na",
        "ㄴ",
        "통보자의 성명",
        "X",
        "통보자의 성명은 가족관계등록부에 기록될 수 없는 사항이다.",
        "규칙",
        "가족관계등록규칙 제38조",
        "통보자의 성명은 등록부의 기록사항으로 열거되지 않는다.",
        trap="통보자의 성명이 등록부에 기록될 수 있다고 본 부분",
        source_question_type="multi-select-false",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        48,
        "da",
        "ㄷ",
        "가족관계등록에 관한 촉탁을 한 법원",
        "O",
        "가족관계등록에 관한 촉탁을 한 법원은 가족관계등록부에 기록될 수 있다.",
        "규칙",
        "가족관계등록규칙 제38조",
        "촉탁에 의한 기록에서는 촉탁법원이 등록부 기록사항이 될 수 있다.",
        source_question_type="multi-select-false",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        48,
        "ra",
        "ㄹ",
        "신고인이 사건본인과 다른 때에는 신고인의 자격",
        "O",
        "신고인이 사건본인과 다른 경우 신고인의 자격은 가족관계등록부에 기록될 수 있다.",
        "규칙",
        "가족관계등록규칙 제38조",
        "신고인과 사건본인이 다를 때 신고인의 자격은 등록부 기록사항에 포함될 수 있다.",
        source_question_type="multi-select-false",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        48,
        "ma",
        "ㅁ",
        "협의이혼의사의 확인일",
        "X",
        "협의이혼의사의 확인일은 가족관계등록부에 기록될 수 없는 사항이다.",
        "규칙",
        "가족관계등록규칙 제38조",
        "협의이혼의 확인일은 이혼신고의 효력요건 관련 자료일 뿐 등록부 기록사항으로 열거되지 않는다.",
        trap="협의이혼의사의 확인일이 등록부에 기록될 수 있다고 본 부분",
        source_question_type="multi-select-false",
        official_answer="⑤",
        unit_type="box",
    ),
    unit(
        49,
        "01",
        "①",
        "친생부인의 소를 제기한 때에는 그 재판의 확정일부터 1개월 이내에 출생신고를 하여야 한다.",
        "X",
        "친생부인의 소가 제기된 경우에도 출생신고는 원칙적으로 출생일부터 1개월 이내에 하여야 한다.",
        "조문",
        "가족관계등록법 제44조",
        "친생부인소송 제기만으로 출생신고기간의 기산점이 재판확정일로 바뀌지 않는다.",
        trap="친생부인 재판확정일부터 출생신고기간을 계산한 부분",
        source_question_type="single-best-true",
        official_answer="⑤",
    ),
    unit(
        49,
        "02",
        "②",
        "출생신고 전에 자녀가 사망한 때에는 출생신고 없이 사망신고를 하여야 한다.",
        "X",
        "출생신고 전에 자녀가 사망한 경우에도 출생신고를 한 뒤 사망신고를 하여야 한다.",
        "조문",
        "가족관계등록법 제51조, 제84조",
        "출생 후 사망한 사람은 출생사실과 사망사실을 각각 등록하여야 한다.",
        trap="출생신고 없이 사망신고만 하면 된다고 한 부분",
        source_question_type="single-best-true",
        official_answer="⑤",
    ),
    unit(
        49,
        "03",
        "③",
        "부 또는 모가 기아를 찾은 때에는 3개월 이내에 출생신고를 하고 등록부의 정정을 신청하여야 한다.",
        "X",
        "부 또는 모가 기아를 찾은 때에는 1개월 이내에 출생신고를 하고 등록부의 정정을 신청하여야 한다.",
        "조문",
        "가족관계등록법 제53조",
        "기아를 찾은 부모의 출생신고 및 등록부정정 신청기간은 3개월이 아니라 1개월이다.",
        trap="기아를 찾은 부모의 신고기간을 3개월로 본 부분",
        source_question_type="single-best-true",
        official_answer="⑤",
    ),
    unit(
        49,
        "04",
        "④",
        "시·읍·면의 장이 출생신고서류를 수리한 때에는 그 신고사건에 무효사유가 있더라도 즉시 등록부에 기록하여야 한다.",
        "X",
        "시·읍·면의 장은 출생신고사건에 무효사유가 있으면 가족관계등록부에 그대로 기록할 수 없다.",
        "조문",
        "가족관계등록법 제16조, 제18조",
        "신고가 수리되더라도 명백한 무효사유가 있으면 등록부 기록 또는 정정절차에서 통제된다.",
        trap="무효사유가 있어도 즉시 등록부에 기록하여야 한다고 한 부분",
        source_question_type="single-best-true",
        official_answer="⑤",
    ),
    unit(
        49,
        "05",
        "⑤",
        "출생신고의 수리증명서를 청구할 때에는 수수료를 납부하여야 한다.",
        "O",
        "출생신고의 수리증명서를 청구할 때에는 수수료를 납부하여야 한다.",
        "규칙",
        "가족관계등록규칙 제28조",
        "신고수리증명서 청구에는 규칙상 정해진 수수료가 부과된다.",
        source_question_type="single-best-true",
        official_answer="⑤",
    ),
    unit(
        50,
        "01",
        "①",
        "불복신청의 비용에 관하여는 민사소송법의 규정을 준용한다.",
        "X",
        "가족관계등록 불복신청 자체의 비용에 관하여 곧바로 민사소송법이 준용되는 것은 아니다.",
        "조문",
        "가족관계등록법 제109조부터 제112조",
        "민사소송법 준용은 비송사건절차법상 항고절차 등에서 문제되고 불복신청 비용 일반에 직접 준용되는 구조가 아니다.",
        trap="불복신청 비용에 민사소송법을 직접 준용한다고 한 부분",
        source_question_type="single-best-true",
        official_answer="④",
    ),
    unit(
        50,
        "02",
        "②",
        "가정법원은 신청이 이유 없는 때에는 기각하고 이유 있는 때에는 시·읍·면의 장에게 상당한 처분을 명하여야 한다.",
        "X",
        "가정법원은 가족관계등록 불복신청이 이유 없는 때에는 기각이 아니라 각하하고, 이유 있는 때에는 시·읍·면의 장에게 상당한 처분을 명한다.",
        "조문",
        "가족관계등록법 제111조 제1항",
        "법문은 이유 없는 불복신청의 재판결과를 각하로 규정한다.",
        trap="이유 없는 신청을 기각한다고 한 부분",
        source_question_type="single-best-true",
        official_answer="④",
    ),
    unit(
        50,
        "03",
        "③",
        "처분을 명하는 재판은 명령으로써 하고 시·읍·면의 장 및 신청인에게 송달하여야 한다.",
        "X",
        "가족관계등록 불복신청의 각하 또는 처분명령 재판은 명령이 아니라 결정으로써 한다.",
        "조문",
        "가족관계등록법 제111조 제2항",
        "불복신청 재판의 형식은 결정이고, 시·읍·면의 장 및 신청인에게 송달한다.",
        trap="처분명령 재판의 형식을 명령이라고 한 부분",
        source_question_type="single-best-true",
        official_answer="④",
    ),
    unit(
        50,
        "04",
        "④",
        "과태료 부과 시 위반사실과 과태료금액을 명시한 과태료납부통지서를 송부하되, 신고서 제출과 동시에 자진하여 납부하는 경우에는 그러하지 아니하다.",
        "O",
        "가족관계등록 과태료를 부과할 때에는 원칙적으로 위반사실과 과태료금액을 명시한 과태료납부통지서를 보내야 하지만, 신고서 제출과 동시에 자진납부하는 경우에는 통지서 송부가 필요 없다.",
        "규칙",
        "가족관계등록규칙 제50조",
        "과태료납부통지서 송부 원칙과 자진납부 예외가 규칙에 명시되어 있다.",
        source_question_type="single-best-true",
        official_answer="④",
    ),
    unit(
        50,
        "05",
        "⑤",
        "과태료의 부과는 신고를 수리한 가족관계등록관이 한다.",
        "X",
        "가족관계등록 신고해태 과태료 부과는 신고를 수리한 가족관계등록관이 아니라 관할 시·읍·면장의 처분으로 이루어진다.",
        "조문+규칙",
        "가족관계등록법 제122조, 가족관계등록규칙 제50조",
        "과태료 처분권자는 가족관계등록관이 아니라 법과 규칙이 정한 행정청이다.",
        trap="과태료 부과권자를 신고를 수리한 가족관계등록관으로 본 부분",
        source_question_type="single-best-true",
        official_answer="④",
    ),
]


def today() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def grouped_units() -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in UNITS:
        grouped[int(row["no"])].append(row)
    return dict(grouped)


def source_label(no: int) -> str:
    return f"법무사{ROUND}회 제2과목 {no}번"


def build_source() -> dict:
    questions = []
    for no, rows in sorted(grouped_units().items()):
        questions.append(
            {
                "qid": f"{YEAR}-g2-{no:02d}",
                "examId": EXAM_ID,
                "year": YEAR,
                "round": ROUND,
                "series": "법무사 제1차",
                "group": GROUP,
                "groupLabel": "제2과목",
                "subject": SUBJECT_NAME,
                "no": no,
                "sourceLabel": source_label(no),
                "type": rows[0]["sourceQuestionType"],
                "officialAnswer": rows[0]["officialAnswer"],
                "units": [
                    {
                        "unitId": f"{YEAR}-g2-{no:02d}-{row['code']}",
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
                    "reviewNote": "2026-06-18 현행 가족관계등록법·규칙 기준으로 atom 작성",
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
        "subjectSummary": {
            "questionCount": len(questions),
            "atomQueueItemCount": len(UNITS),
        },
        "questions": questions,
    }


def build_queue(source: dict) -> dict:
    items = []
    for question in source["questions"]:
        for unit_row in question["units"]:
            row = next(row for row in UNITS if f"{YEAR}-g2-{row['no']:02d}-{row['code']}" == unit_row["unitId"])
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
                        "instruction": "원문 지문이 아니라 O/X 판단 근거인 조문·예규·선례 지점을 자기완결식 atom으로 작성한다.",
                        "basisTypesAllowed": ["조문", "규칙", "예규", "선례", "판례"],
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
            "atomPrinciple": "atom은 지문 복사본이 아니라 O/X 판단 근거인 조문·예규·선례 지점이다.",
            "xHandling": "X 지문은 독립 atom이 아니라 올바른 O atom 또는 근거 법리에 종속시킨다.",
        },
        "items": items,
    }


def atom_id(row: dict) -> str:
    return f"bupmusa-{YEAR}-family-registry-q{int(row['no']):02d}-{row['code']}"


def build_atoms(queue: dict) -> list[dict]:
    queue_by_id = {item["unitId"]: item for item in queue["items"]}
    atoms = []
    checked_at = today()
    for row in UNITS:
        unit_id = f"{YEAR}-g2-{row['no']:02d}-{row['code']}"
        item = queue_by_id[unit_id]
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
            "basisType": row["basisType"],
            "basisRef": row["basisRef"],
            "why": row["why"],
            "sourceStatement": row["raw"],
            "sourceTrap": row["trap"] if row["sourceVerdict"] == "X" else None,
            "xDependsOn": row["rep"] if row["sourceVerdict"] == "X" else None,
            "reviewedAt": checked_at,
            "currentLawCheckedAt": checked_at,
        }
        atoms.append(atom)
    validate(atoms, queue["items"])
    return atoms


def validate(atoms: list[dict], queue_items: list[dict]) -> None:
    if len(atoms) != len(queue_items):
        raise ValueError(f"atom count mismatch: atoms={len(atoms)} queue={len(queue_items)}")
    ids = [atom["atomId"] for atom in atoms]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    bad_patterns = [
        r"\?",
        r"위\s*[①②③④⑤ㄱㄴㄷㄹㅁㅂㅅ]",
        r"위의\s*[①②③④⑤ㄱㄴㄷㄹㅁㅂㅅ]",
        r"옳은 것은",
        r"옳지 않은 것은",
        r"다음 중",
        r"몇 개인가",
        r"①|②|③|④|⑤",
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
    index = {
        "schema": "legal-scrivener/subject-index/v1",
        "sourceFamily": "법무사시험",
        "updatedAt": today(),
        "examId": EXAM_ID,
        "year": YEAR,
        "round": ROUND,
        "subjects": {
            SUBJECT_NAME: {
                "source": str(SOURCE_PATH),
                "atomQueue": str(QUEUE_PATH),
                "completedAtoms": str(OUT_PATH),
                "questionCount": 10,
                "atomQueueItemCount": queue_count,
                "completedAtomCount": atom_count,
                "completedAtomsUpdatedAt": today(),
            }
        },
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
    for sample in data["items"][:3]:
        print(f"{sample['atomId']} {sample['rep']}")


if __name__ == "__main__":
    main()
