from __future__ import annotations

import json
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
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2023" / "과목별"
SOURCE_PDF = WORKSPACE / "0gichul_법과목_기출" / "헌법" / "2023_법무사_헌법.pdf"
RAW_DIR = PRIVATE_ROOT / "raw" / "2023"
TEXT_DIR = PRIVATE_ROOT / "text" / "2023"
RAW_PDF_PATH = RAW_DIR / "2023_법무사_1차_1교시_문제.pdf"
RAW_TEXT_PATH = TEXT_DIR / "2023_법무사_1차_1교시_문제.txt"
SOURCE_PATH = SUBJECT_DIR / "2023_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2023_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2023_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2023_법무사_과목별_index.json"

SUBJECT_NAME = "헌법"
EXAM_ID = "2023_bupmusa_1st"
YEAR = 2023
ROUND = 29
GROUP = 1
QUESTION_COUNT = 20
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 140
LABELS = ["①", "②", "③", "④", "⑤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "국가공무원법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국가공무원법"},
    {"title": "2023 법무사 헌법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2023/111904821"},
    {"title": "2023 법무사 헌법 해설", "publisher": "아쉽공 기출해설", "url": "https://ebssir.tistory.com/entry/2023%EB%85%84-%EB%B2%95%EB%AC%B4%EC%82%AC-%ED%97%8C%EB%B2%95-%ED%95%B4%EC%84%A41-%EC%95%84%EC%89%BD%EA%B3%B5-%EA%B8%B0%EC%B6%9C%ED%95%B4%EC%84%A4"},
    {"title": "2023 법무사 헌법 해설(2)", "publisher": "아쉽공 기출해설", "url": "https://ebssir.tistory.com/entry/2023%EB%85%84-%EB%B2%95%EB%AC%B4%EC%82%AC-%ED%97%8C%EB%B2%95-%ED%95%B4%EC%84%A42-%EC%95%84%EC%89%BD%EA%B3%B5-%EA%B8%B0%EC%B6%9C%ED%95%B4%EC%84%A4"},
    {"title": "2023 법무사 1차 최종정답 확정 보도", "publisher": "피앤피뉴스", "url": "https://www.gosiweek.com/article/179587666022018"},
]

OFFICIAL_ANSWERS = {
    1: "②",
    2: "③",
    3: "④",
    4: "②",
    5: "⑤",
    6: "②",
    7: "④",
    8: "④",
    9: "②",
    10: "③",
    11: "⑤",
    12: "②",
    13: "①",
    14: "②",
    15: "④",
    16: "②",
    17: "④",
    18: "④",
    19: "②",
    20: "②",
}

QUESTION_TYPES = {no: "single-best-false" for no in range(1, 21)}
FALSE_LABELS = {no: {answer} for no, answer in OFFICIAL_ANSWERS.items()}

TOPICS = {
    1: "국가배상과 형사보상",
    2: "재산권",
    3: "사면권",
    4: "민사소송법상 재심제도",
    5: "변호사 광고 금지",
    6: "평등원칙",
    7: "헌법 제10조",
    8: "권한쟁의심판",
    9: "개인정보자기결정권",
    10: "헌법재판소 위헌결정의 효력",
    11: "탄핵심판",
    12: "직업공무원제도",
    13: "적법절차원칙과 개인정보자기결정권",
    14: "국회",
    15: "공무담임권",
    16: "지방자치제도",
    17: "입법부작위",
    18: "법원",
    19: "표현의 자유와 종교단체 자율권",
    20: "집회·결사의 자유",
}

ATOM_ROWS = """
1|①|01|O|국가배상법상 공무원에는 공무원 신분자가 아닌 공무 위탁 실질 종사자도 포함된다.|
1|②|01|X|형사보상청구기간을 무죄재판 확정일부터 1년으로 제한한 구 형사보상법 조항은 형사보상청구권을 침해한다.|형사보상청구의 1년 제척기간이 형사보상청구권을 침해하지 않는다고 한 부분
1|②|02|X|형사보상결정에 불복을 허용하지 않은 구 형사보상법 조항은 재판청구권을 침해한다.|형사보상결정에 대한 불복금지가 재판청구권을 침해하지 않는다고 한 부분
1|③|01|O|국회의원의 입법행위는 입법내용이 헌법 문언에 명백히 위반되는데도 굳이 입법한 특수한 경우가 아닌 한 국가배상법상 위법행위로 볼 수 없다.|
1|④|01|O|국가나 지방자치단체가 사경제 주체로 활동한 경우 손해배상책임에는 국가배상법이 아니라 민법상 사용자책임 등이 적용될 수 있다.|
1|⑤|01|O|검사의 무혐의 불기소처분에 대한 헌법소원에서 재판절차진술권 침해를 주장하려면 헌법 제27조 제5항의 형사피해자에 해당하여야 한다.|
2|①|01|O|헌법상 정당한 보상은 원칙적으로 피수용재산의 객관적 재산가치를 완전하게 보상하는 것을 뜻한다.|
2|①|02|O|공용수용에서 개발이익은 완전보상의 범위에 포함되지 않는다.|
2|②|01|O|헌법 제23조 제3항은 재산권 수용의 주체를 국가 등 공적 기관으로 한정하지 않는다.|
2|②|02|O|공공필요와 정당보상 요건을 충족하면 민간개발자에게도 수용권한을 부여할 수 있다.|
2|③|01|X|사회부조처럼 국가가 일방적으로 지급하는 금전급부에 대한 기대는 금전급부라는 이유만으로 헌법상 재산권 보호대상에 포함되지는 않는다.|사회부조와 같은 국가의 일방적 금전급부 권리가 원칙적으로 재산권 보호대상에 포함된다고 한 부분
2|④|01|O|진정소급입법은 이미 과거에 완성된 사실 또는 법률관계를 사후적으로 규율하는 입법이다.|
2|④|02|O|헌법 제13조 제2항이 금지하는 소급입법에 의한 재산권 박탈은 진정소급입법에 의한 재산권 박탈을 말한다.|
2|⑤|01|O|공익성이 낮은 고급골프장사업에 행정기관의 실시계획 승인·고시만으로 민간개발자에게 수용권한을 부여하는 법률조항은 헌법 제23조 제3항에 위반된다.|
3|①|01|O|헌법은 대통령의 사면·감형·복권 권한을 인정하면서 그 구체적 사항을 법률로 정하도록 한다.|
3|①|02|O|사면의 종류, 대상, 범위, 절차와 효과는 범죄의 죄질, 보호법익, 법감정, 국가이익과 권력분립 원칙을 고려하여 입법자가 형성할 사항이다.|
3|②|01|O|사면은 형 선고의 효력이나 공소권을 상실시키거나 형 집행을 면제하는 국가원수의 권한이다.|
3|②|02|O|사면은 사법부 판단을 변경하는 제도이므로 권력분립 원리의 예외에 해당한다.|
3|③|01|O|특별사면은 이미 형의 선고를 받은 특정인을 대상으로 한다.|
3|③|02|O|특별사면은 형 집행을 면제하거나 특별한 사정이 있으면 선고의 효력을 상실하게 할 수 있다.|
3|④|01|X|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|대통령의 일반사면권 행사에도 국회의 동의가 필요 없다고 한 부분
3|⑤|01|O|복권은 형 선고로 상실되거나 정지된 법령상 자격을 회복시키는 것이다.|
3|⑤|02|O|형 집행이 끝나지 않았거나 집행이 면제되지 않은 사람에 대해서는 복권을 할 수 없다.|
4|①|01|O|민사소송법상 재심사유의 범위는 확정판결의 법적 안정성, 재판의 신속·적정성, 법원 업무부담 등을 고려하여 입법자가 정할 사항이다.|
4|②|01|O|판결주문에 영향이 없는 공격방어방법 판단누락은 재심으로 확정판결 효력을 배제할 만큼 정의의 요청이 절박하다고 볼 수 없다.|
4|②|02|O|판결주문과 간접적으로만 관련되는 판단이유 누락은 재심으로 확정판결 효력을 배제할 만큼 정의의 요청이 절박하다고 볼 수 없다.|
4|②|03|X|판결주문에 영향이 없는 공격방어방법 판단누락과 판결주문에 간접적으로만 관련되는 판단이유 누락은 재심 허용 필요성에서 달리 취급되지 않는다.|두 유형을 달리 취급하여 한쪽만 재심 허용 필요성이 절박한 것처럼 본 부분
4|③|01|O|재심사유 규정의 위헌성은 입법자가 재판의 적정성을 현저히 희생하여 재판청구권의 본질을 심각하게 훼손한 경우에 인정될 수 있다.|
4|③|02|O|재심사유 규정이 입법형성권의 한계를 일탈하여 현저히 자의적인 경우에는 위헌성이 문제될 수 있다.|
4|④|01|O|재심은 확정판결에 대한 불복방법이다.|
4|④|02|O|재심은 미확정판결에 대한 상소보다 법적 안정성 요청이 크므로 상소보다 예외적으로 인정된다.|
4|⑤|01|O|민사소송법상 판단누락 재심사유는 확립된 판례에 의해 의미와 적용 기준을 예측할 수 있어 명확성원칙에 위배되지 않는다.|
5|①|01|O|대한변호사협회의 변호사 광고규정은 헌법소원의 대상이 되는 공권력 행사에 해당할 수 있다.|
5|②|01|O|대한변호사협회의 유권해석에 반하는 광고를 금지하는 변호사 광고규정은 법률유보원칙에 위반될 수 있다.|
5|②|02|O|대한변호사협회 유권해석 위반행위를 목적 또는 수단으로 한 법률상담 관련 광고 금지는 변호사의 표현의 자유와 직업의 자유를 침해할 수 있다.|
5|③|01|O|무료 또는 부당한 염가의 수임료를 내세운 변호사 광고 금지는 공정한 수임질서 확립을 위한 것으로 과잉금지원칙에 위배되지 않는다.|
5|③|02|O|무료 또는 부당한 염가의 법률상담 방식을 내세운 변호사 광고 금지는 법률소비자와 정당한 수임질서를 보호하기 위한 적합한 수단이다.|
5|④|01|O|비변호사의 변호사 직무 관련 서비스 표시행위에 대한 광고 의뢰·참여·협조 금지는 변호사자격제도 유지와 소비자 보호를 위한 적합한 수단이다.|
5|④|02|O|소비자를 변호사 등으로 오인하게 할 수 있는 행위에 대한 광고 의뢰·참여·협조 금지는 소비자 피해 방지를 위한 적합한 수단이다.|
5|⑤|01|X|변호사 또는 소비자로부터 대가를 받고 변호사 등을 광고·홍보·소개하는 행위를 금지하는 변호사 광고규정 부분은 과잉금지원칙에 위반되어 표현의 자유와 직업의 자유를 침해할 수 있다.|대가수수 변호사 광고·홍보·소개 금지규정이 과잉금지원칙에 위배되지 않는다고 한 부분
6|①|01|O|공무원이 지위를 이용하여 범한 공직선거법위반죄의 공소시효를 해당 선거일 후 10년으로 정한 것은 합리적 이유 있는 차별로서 평등원칙에 위반되지 않는다.|
6|②|01|X|반복 절도범 가중처벌규정이 형법상 절도죄, 야간주거침입절도죄, 특수절도죄를 함께 규율하더라도 그 사정만으로 평등원칙에 위반된다고 단정할 수 없다.|반복 절도범 가중처벌규정이 여러 절도범죄를 동등취급하여 평등원칙에 위반된다고 한 부분
6|③|01|O|선거와 무관하게 후원회를 설치·운영할 수 있는 자를 중앙당과 국회의원으로 한정하여 지방의회의원을 제외하는 것은 불합리한 차별에 해당할 수 있다.|
6|④|01|O|군형법상 강제추행죄와 항거불능상태 이용 준강제추행죄에 벌금형 선택형을 두지 않았더라도 평등원칙에 위반된다고 볼 수는 없다.|
6|⑤|01|O|동일한 밀수입 예비행위에서 물품원가 2억 원 미만과 2억 원 이상을 관세법과 특정범죄가중처벌법으로 달리 처벌하는 것은 합리적 이유가 있다고 보기 어렵다.|
7|①|01|O|부모가 자녀의 이름을 지을 자유는 자녀 양육과 가족생활의 핵심 요소이다.|
7|①|02|O|부모가 자녀의 이름을 지을 자유는 헌법 제36조 제1항과 헌법 제10조에 의하여 보호된다.|
7|②|01|O|초등학교 정규교과에서 영어를 배제하거나 영어교육 시수를 제한하는 것은 학생의 인격발현권을 제한할 수 있다.|
7|②|02|O|초등학교 영어교육 제한은 균형 있는 교육과 사교육 폐단 방지를 위한 것으로 학생의 인격발현권을 침해하지 않는다고 볼 수 있다.|
7|③|01|O|부정한 수단으로 운전면허를 받은 경우 부정취득하지 않은 운전면허까지 필요적으로 취소하게 하는 것은 일반적 행동의 자유를 침해한다.|
7|④|01|X|사자에 대한 친일반민족행위결정은 그 사자와의 관계에서 인격상과 명예를 형성해 온 후손의 인격권을 제한할 수 있다.|사자에 대한 친일반민족행위결정이 후손의 법적 지위에 영향이 없어 후손의 인격권을 제한하지 않는다고 한 부분
7|⑤|01|O|헌법 제10조의 개인의 인격권과 행복추구권은 자기운명결정권을 전제로 한다.|
7|⑤|02|O|자기운명결정권에는 성행위 여부와 상대방을 결정할 성적 자기결정권이 포함된다.|
8|①|01|O|국가기관의 법률상 권한은 국회의 입법행위로 형성·부여된 권한이므로 국회의 입법행위를 구속하는 기준이 될 수 없다.|
8|①|02|O|국회 입법행위가 침해 원인인 경우 법률상 권한 침해를 이유로 한 권한쟁의심판청구는 권한침해가능성이 인정되지 않는다.|
8|②|01|O|국가기관과 지방자치단체 간 권한쟁의심판에서 헌법재판소법상 정부는 예시적 개념이다.|
8|②|02|O|정부의 부분기관, 국회, 법원도 국가기관과 지방자치단체 간 권한쟁의심판의 당사자가 될 수 있다.|
8|③|01|O|국가기관과 지방자치단체 간 또는 지방자치단체 상호 간 권한쟁의심판에서 헌법재판소법상 지방자치단체는 예시적 개념이 아니다.|
8|③|02|O|지방자치단체의 기관인 지방의회나 교육감은 원칙적으로 권한쟁의심판의 당사자능력이 인정되지 않는다.|
8|④|01|O|중앙행정기관이나 광역지방자치단체가 지방자치단체의 자치사무 감사에 착수하려면 감사대상이 사전에 특정되어야 한다.|
8|④|02|X|연간 감사계획에 포함되지 않은 자치사무 감사라도 특정된 감사대상을 사전에 통보하는 것이 항상 감사의 개시요건은 아니다.|특정된 감사대상의 사전 통보가 언제나 자치사무 감사의 개시요건이라고 한 부분
8|⑤|01|O|권한쟁의심판을 청구하려면 피청구인의 처분 또는 부작위가 있어야 한다.|
8|⑤|02|O|정부의 법률안 제출행위, 행정기관의 단순한 견해표명이나 업무연락은 권한쟁의심판의 대상이 되는 처분에 해당하지 않는다.|
9|①|01|O|형제자매는 언제나 본인과 이해관계를 같이한다고 볼 수 없다.|
9|①|02|O|형제자매가 본인의 친족·상속 관련 증명서를 편리하게 발급받도록 하는 법률조항은 개인정보자기결정권을 침해할 수 있다.|
9|②|01|X|강제추행죄 유죄판결 확정자를 신상정보 등록대상자로 정한 조항은 재범위험성을 별도로 요구하지 않더라도 개인정보자기결정권을 침해한다고 볼 수 없다.|강제추행죄 등록대상자 조항이 재범위험성을 요구하지 않아 개인정보자기결정권을 침해한다고 한 부분
9|③|01|O|변호사시험 합격자 명단 공고는 법률서비스 수요자에게 전문직 정보 접근 기회를 제공하기 위한 것이다.|
9|③|02|O|변호사시험 합격자 명단을 공고하도록 한 조항은 응시자의 개인정보자기결정권을 침해한다고 볼 수 없다.|
9|④|01|O|선거운동기간 중 인터넷언론사 게시판의 실명확인 기술조치 의무는 익명표현의 자유를 제한한다.|
9|④|02|O|선거운동기간 중 인터넷언론사 게시판의 실명확인 기술조치 의무는 개인정보자기결정권을 침해할 수 있다.|
9|⑤|01|O|성적목적공공장소침입죄는 공공화장실 등 일정한 장소 침입의 경우에 한하여 성립한다.|
9|⑤|02|O|성적목적공공장소침입죄 유죄확정자를 신상정보 등록대상자로 정한 조항은 등록대상 범위가 제한되어 개인정보자기결정권을 침해한다고 볼 수 없다.|
10|①|01|O|형사재판 유죄확정판결 후 처벌 근거조항에 위헌결정이 내려지면 유죄판결을 받은 사람은 재심청구로 그 확정판결을 다툴 수 있다.|
10|②|01|O|헌법재판소법은 법률의 위헌결정에 대한 기속력을 명문으로 규정한다.|
10|②|02|O|헌법재판소법은 권한쟁의심판 결정에 대한 기속력을 명문으로 규정한다.|
10|②|03|O|헌법재판소법은 헌법소원 인용결정에 대한 기속력을 명문으로 규정한다.|
10|③|01|O|형벌에 관한 법률 또는 법률조항이 위헌으로 결정되면 원칙적으로 소급하여 효력을 상실한다.|
10|③|02|X|종전에 합헌으로 결정한 형벌조항이 위헌으로 결정되면 그 합헌결정이 있는 날의 다음 날로 소급하여 효력을 상실한다.|종전 합헌결정이 있는 경우 그 합헌결정일 자체로 소급하여 효력을 상실한다고 한 부분
10|④|01|O|헌법불합치결정은 법률조항에 대한 위헌결정에 해당한다.|
10|④|02|O|형벌조항에 대한 헌법불합치결정에 잠정적용명령이 붙은 경우에도 헌법재판소법상 형벌조항 위헌결정의 소급효가 문제될 수 있다.|
10|⑤|01|O|법률조항의 위헌결정으로 당해 법률 전부를 시행할 수 없다고 인정되면 그 법률 전부에 대해서도 위헌결정을 할 수 있다.|
11|①|01|O|탄핵심판절차는 고위공직자의 헌법위반이나 법률위반을 사전에 경고하고 방지하는 기능을 한다.|
11|①|02|O|탄핵심판절차는 국가기관이 권한을 남용하여 헌법이나 법률에 위반한 경우 그 권한을 박탈하는 기능을 한다.|
11|①|03|O|탄핵심판절차는 공직자의 헌법위반에 대한 법적 책임을 추궁하여 헌법의 규범력을 확보하는 기능을 한다.|
11|②|01|O|국회의 탄핵소추 의사절차에 명백한 헌법·법률 위반이 없는 한 국회의 의사절차 자율권은 존중되어야 한다.|
11|②|02|O|국회법은 탄핵소추사유에 대한 조사 여부를 국회의 재량으로 규정한다.|
11|②|03|O|국회가 별도 조사 없이 탄핵소추안을 의결하였다는 사정만으로 탄핵소추의결이 위법하다고 볼 수 없다.|
11|③|01|O|대통령 외 탄핵대상 공무원에 대한 탄핵소추는 국회재적의원 3분의 1 이상의 발의와 재적의원 과반수 찬성이 필요하다.|
11|③|02|O|대통령에 대한 탄핵소추는 국회재적의원 과반수의 발의와 재적의원 3분의 2 이상의 찬성이 필요하다.|
11|④|01|O|국가기관이 국민에게 공권력을 행사할 때의 법원칙인 적법절차원칙은 탄핵소추절차에 그대로 직접 적용된다고 볼 수 없다.|
11|⑤|01|X|탄핵심판청구와 동일한 사유로 형사소송이 진행 중인 경우 재판부는 심판절차를 정지할 수 있지만 반드시 정지하여야 하는 것은 아니다.|탄핵심판과 동일한 사유로 형사소송이 진행되면 재판부가 반드시 심판절차를 정지하여야 한다고 한 부분
12|①|01|O|헌법 제7조 제2항의 직업공무원제도는 엽관제를 지양하여 정치와 공직을 분리하려는 제도이다.|
12|①|02|O|직업공무원제도는 공무수행의 안정성과 전문성을 확보하려는 제도이다.|
12|②|01|O|공무원은 원칙적으로 정당의 발기인 및 당원이 될 수 없다.|
12|②|02|X|정당법상 정당가입 허용 예외 공무원에는 교육감이 포함되지 않는다.|정당가입 허용 예외 공무원에 교육감까지 포함된다고 한 부분
12|③|01|O|직업공무원의 신분보장은 국민 전체를 위한 소신 있는 직무수행을 가능하게 하기 위한 것이다.|
12|③|02|O|직업공무원의 신분보장은 생계보호와 직업보호의 의미를 가지며 공무담임권의 보호영역에 포함된다.|
12|④|01|O|직무 내외를 불문하고 체면이나 위신을 손상하는 행위를 징계사유로 정한 국가공무원법 규정은 명확성원칙에 위배되지 않는다.|
12|④|02|O|직무 내외를 불문하고 품위손상행위를 징계사유로 정한 국가공무원법 규정은 과잉금지원칙에 반한다고 볼 수 없다.|
12|⑤|01|O|직업공무원제도에서는 직위분류제와 성적주의에 따른 인사 공정성 장치가 중요하다.|
12|⑤|02|O|직업공무원제도의 중추적 요소는 공무원의 정치적 중립과 신분보장이다.|
13|①|01|X|헌법상 적법절차원칙은 형사절차에 한정되지 않고 기본권 제한과 관련되는 행정작용 등 국가작용에도 적용될 수 있다.|적법절차원칙이 형사절차상의 제한된 범위에만 적용되고 행정작용에는 적용되지 않는다고 한 부분
13|②|01|O|개인정보자기결정권은 자신에 관한 정보가 언제 누구에게 어느 범위까지 알려지고 이용되도록 할지 정보주체가 스스로 결정할 권리이다.|
13|②|02|O|개인정보자기결정권은 헌법 제10조의 일반적 인격권과 헌법 제17조의 사생활의 비밀과 자유에 의하여 보장된다.|
13|③|01|O|헌법은 체포·구속·압수·수색에 관하여 영장주의를 보장한다.|
13|③|02|O|형사절차상 체포·구속·압수·수색 같은 강제처분은 독립한 법관이 발부한 영장에 의하여야 한다.|
13|④|01|O|변호사업무 정지명령에서 변호사에게 유리한 사실진술이나 증거제출의 청문 기회를 보장하지 않으면 적법절차원칙에 반할 수 있다.|
13|⑤|01|O|피고인이 스스로 치료감호를 청구할 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|
13|⑤|02|O|피고인이 법원으로부터 직권으로 치료감호를 선고받을 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|
13|⑤|03|O|검사에게만 치료감호청구권한을 부여한 것은 적법절차원칙에 반하지 않는다.|
14|①|01|O|국회의 정기회는 법률이 정하는 바에 따라 매년 1회 집회된다.|
14|①|02|O|국회의 임시회는 대통령 또는 국회재적의원 4분의 1 이상의 요구로 집회된다.|
14|②|01|O|국회에서 의결된 법률안은 정부에 이송되어 15일 이내에 대통령이 공포한다.|
14|②|02|X|대통령은 이의가 있는 법률안 전체를 국회로 환부하여 재의를 요구하여야 하며 일부 조항만 환부할 수 없다.|대통령이 법률안의 일부에 관해서도 환부와 재의요구를 할 수 있다고 한 부분
14|③|01|O|국회나 그 위원회의 요구가 있으면 국무총리·국무위원 또는 정부위원은 출석·답변하여야 한다.|
14|③|02|O|국무총리 또는 국무위원이 국회 출석요구를 받으면 국무위원 또는 정부위원으로 하여금 출석·답변하게 할 수 있다.|
14|④|01|O|국회는 직무집행에서 헌법이나 법률을 위반한 검사에 대하여 탄핵소추를 의결할 수 있다.|
14|④|02|O|국회는 직무집행에서 헌법이나 법률을 위반한 고위공직자범죄수사처 검사에 대하여 탄핵소추를 의결할 수 있다.|
14|⑤|01|O|국회는 정부의 동의 없이 정부가 제출한 지출예산 각항의 금액을 증가하거나 새 비목을 설치할 수 없다.|
14|⑤|02|O|국회는 예산 변경이 필요하더라도 직접 추가경정예산안을 제출할 수 없다.|
15|①|01|O|공무담임권은 모든 국민이 현실적으로 공직을 담당할 수 있음을 보장하는 권리가 아니다.|
15|①|02|O|공무담임권은 공직취임 기회를 자의적으로 배제당하지 않을 기회를 보장한다.|
15|①|03|O|공무담임권의 보호영역에는 공직취임 기회의 자의적 배제와 공무원 신분의 부당한 박탈이 포함된다.|
15|②|01|O|직업공무원의 공직진출 규율은 정치적 중립성과 효율적 업무수행 능력을 고려하여야 한다.|
15|②|02|O|직업공무원의 공직진출 규율은 능력주의를 바탕으로 이루어져야 한다.|
15|③|01|O|교육의원 후보자에게 일정한 교육경력 또는 교육행정경력을 요구하는 것은 교육의 자주성·전문성·정치적 중립성을 보장하기 위한 것이다.|
15|③|02|O|교육의원 후보자에게 일정한 교육경력 또는 교육행정경력을 요구하는 것은 공무담임권을 침해하지 않는다.|
15|④|01|X|금고 이상의 형의 선고유예를 받은 군무원을 군무원직에서 당연퇴직시키는 조항은 공무담임권을 침해한다.|금고 이상의 형의 선고유예를 받은 군무원의 당연퇴직 조항이 공무담임권을 침해하지 않는다고 한 부분
15|⑤|01|O|후보자가 되고자 하는 사람의 기부행위를 처벌하는 공직선거법 조항 자체는 공무담임권을 직접 제한하는 것이 아니다.|
15|⑤|02|O|기부행위 처벌에 따른 당선무효·피선거권 제한은 별도 공직선거법 조항 적용으로 나타나는 결과이다.|
16|①|01|O|지방자치법상 지방자치단체의 기관에는 대의기관인 지방의회가 있다.|
16|①|02|O|지방자치법상 지방자치단체의 기관에는 집행기관인 지방자치단체장이 있다.|
16|②|01|O|지방의회는 조례의 제정·개정·폐지, 예산의 심의·확정, 결산 승인, 행정사무감사 및 조사권을 가진다.|
16|②|02|X|지방자치단체 규칙의 제정·개정·폐지 권한은 지방자치단체장에게 속한다.|지방의회가 조례뿐 아니라 지방자치단체 규칙의 제정·개정·폐지 권한도 가진다고 한 부분
16|③|01|O|지방자치단체는 사무처리를 위한 행정기구를 설치할 수 있다.|
16|③|02|O|지방자치단체는 소속 공무원에 관한 임용과 징계 등 인사를 스스로 할 수 있다.|
16|④|01|O|기관위임사무는 국가사무이므로 지방자치단체가 기관위임사무에 관한 권한쟁의심판을 청구하는 것은 허용되지 않는다.|
16|⑤|01|O|감사원은 지방자치단체에 대하여 합목적성 감사도 할 수 있다.|
16|⑤|02|O|중앙행정기관의 지방자치단체 자치사무 감사는 합법성 감사에 한정된다.|
17|①|01|O|양육비대지급제 등 양육비 이행의 실효성을 높이는 법률을 제정할 헌법의 명시적 입법위임은 인정되기 어렵다.|
17|①|02|O|양육비대지급제 등 구체적 제도에 관한 입법의무가 헌법해석상 새롭게 발생한다고 보기 어렵다.|
17|②|01|O|진정입법부작위 헌법소원은 헌법의 명시적 입법위임이 있는데도 입법자가 이를 이행하지 않은 경우에 허용된다.|
17|②|02|O|진정입법부작위 헌법소원은 헌법해석상 구체적 기본권 보장을 위한 국가의 행위의무가 명백한데도 입법자가 아무런 조치를 하지 않은 경우에 허용된다.|
17|③|01|O|의료인이 아닌 사람의 문신시술업 자격과 요건을 법률로 정하라는 명시적 헌법위임은 존재하지 않는다.|
17|③|02|O|문신시술을 위한 별도 자격제도를 마련할지 여부는 사회적·경제적 사정을 고려하여 입법부가 결정할 사항이다.|
17|③|03|O|문신시술업 자격제도에 관한 입법의무가 헌법해석상 도출된다고 보기 어렵다.|
17|④|01|O|가정폭력 가해자인 전 배우자의 자녀 가족관계증명서 및 기본증명서 교부청구를 제한하지 않은 것은 개인정보자기결정권을 침해할 수 있다.|
17|④|02|X|가정폭력 가해자의 증명서 교부청구 제한규정 부재는 이미 관련 교부청구 제도를 둔 법률의 불완전·불충분 규율에 관한 부진정입법부작위 문제이다.|가정폭력 가해자의 증명서 교부청구 제한규정 부재가 진정입법부작위에 해당한다고 한 부분
17|⑤|01|O|북한인권법 미제정 입법부작위 헌법소원 계속 중 국회가 북한인권법을 제정하면 권리보호이익이 소멸할 수 있다.|
17|⑤|02|O|북한인권법 미제정 입법부작위 헌법소원에서 권리보호이익과 헌법적 해명의 필요성이 없으면 심판청구는 부적법하다.|
18|①|01|O|대법원이 법관 징계처분 취소청구소송을 단심으로 재판하더라도 사실확정이 대법원의 권한에 속하면 법관에 의한 사실확정 기회가 박탈되었다고 볼 수 없다.|
18|①|02|O|법관 징계처분 취소청구소송을 대법원 단심재판으로 정한 것은 재판청구권을 침해하지 않는다고 볼 수 있다.|
18|②|01|O|단독판사와 합의부의 심판권 분배 등 재판사무 범위 배분은 입법자가 정할 사법정책의 영역이다.|
18|②|02|O|입법자는 국민의 권리보호와 재판제도의 적정 운용을 고려하여 법원조직에 따른 재판사무 범위를 배분할 수 있다.|
18|③|01|O|재판의 심리와 판결은 공개한다.|
18|③|02|O|재판의 심리는 국가안전보장·안녕질서 방해나 선량한 풍속을 해할 염려가 있으면 법원의 결정으로 공개하지 않을 수 있다.|
18|④|01|X|명령·규칙 또는 처분이 헌법이나 법률에 위반되는지가 재판의 전제가 된 경우 그 최종 심사권은 대법원에 있다.|명령·규칙 또는 처분의 위헌·위법 여부가 재판 전제가 되면 법원이 헌법재판소에 제청하여 심판받아야 한다고 한 부분
18|⑤|01|O|형사재판에서 사법권의 독립은 심판기관인 법원과 소추기관인 검찰청의 분리를 요구한다.|
18|⑤|02|O|형사재판에서 사법권의 독립은 법관이 검사와 피고인으로부터 부당한 간섭 없이 독립하여야 함을 요구한다.|
19|①|01|O|특정 정당이나 정치인에 대한 정치자금 기부는 정치활동 또는 정치적 의사표현의 성격을 가진다.|
19|①|02|O|단체 관련 자금의 정치자금 기부금지는 정치활동의 자유와 정치적 표현의 자유를 제한한다.|
19|②|01|X|상업광고도 사상·지식·정보 등을 불특정 다수에게 전파하는 표현행위에 해당하므로 언론·출판의 자유 보호대상이 될 수 있다.|광고물은 상업적 목적으로 제작되어 언론·출판의 자유 보호대상이 아니라고 한 부분
19|③|01|O|청소년이용음란물도 의사표현·전파의 형식 중 하나이다.|
19|③|02|O|청소년이용음란물은 언론·출판의 자유에 의하여 보호되는 의사표현의 매개체에 해당할 수 있다.|
19|④|01|O|헌법 제21조의 표현의 자유는 사상 또는 의견의 자유로운 표명과 전달의 자유를 뜻한다.|
19|④|02|O|표현의 자유는 인간의 존엄과 국민주권 실현에 필수적인 정신적 자유의 외부적 표현을 보장한다.|
19|⑤|01|O|종교활동은 종교의 자유와 정교분리 원칙에 의하여 국가의 간섭으로부터 보호된다.|
19|⑤|02|O|종교단체 내부관계가 일반 국민의 권리의무나 법률관계를 규율하는 것이 아니면 법원은 원칙적으로 실체적 심리판단을 자제하여야 한다.|
19|⑤|03|O|종교단체가 교리와 신앙질서 유지를 위하여 교인을 종교적 방법으로 제재하는 것은 종교단체 내부 규제로서 종교의 자유 영역에 속한다.|
19|⑤|04|O|법원은 구체적 권리 또는 법률관계 분쟁의 전제 판단이 아닌 한 종교단체 징계의 효력 자체를 사법심사 대상으로 삼을 수 없다.|
20|①|01|O|집회의 자유는 개인의 인격발현 요소이다.|
20|①|02|O|집회의 자유는 민주주의를 구성하는 요소이다.|
20|①|03|O|집회의 자유는 집단적 의견표명을 통하여 여론 형성에 영향을 미치므로 민주적 공동체에 필수적인 기본권이다.|
20|②|01|X|집회의 자유에 의하여 헌법적으로 보호되는 집회는 평화적 또는 비폭력적 집회에 한정된다.|폭력을 사용한 의견 강요에 해당하는 집회도 헌법적으로 보호될 수 있다고 한 부분
20|③|01|O|집회 장소는 집회의 목적과 효과에 중요한 의미를 가진다.|
20|③|02|O|집회 장소 선택의 자유는 집회의 자유가 효과적으로 보장되기 위한 요소이다.|
20|③|03|O|다른 법익 보호로 정당화되지 않는 한 집회 장소를 항의 대상에서 분리시키는 것은 집회의 자유에 의하여 제한된다.|
20|④|01|O|집회의 자유는 집회의 시간, 장소, 방법과 목적을 스스로 결정할 권리를 보장한다.|
20|④|02|O|집회의 자유는 집회의 준비, 조직, 지휘, 참가와 집회장소·시간의 선택을 보호한다.|
20|④|03|O|집회의 자유는 집회 참가를 방해하거나 집회 참가를 강요하는 국가행위를 금지한다.|
20|④|04|O|집회의 자유는 집회장소로의 이동이나 집회장소에서의 귀가를 방해하는 국가행위를 금지한다.|
20|⑤|01|O|결사의 자유에서 말하는 결사는 자유의사에 따라 결합하고 조직화된 의사형성이 가능한 단체를 말한다.|
20|⑤|02|O|공법상 결사는 헌법 제21조의 결사의 자유에서 말하는 결사에 포함되지 않는다.|
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
    start = text.find("【헌 법 20문】")
    if start == -1:
        raise ValueError("cannot locate 2023 constitution section")
    end = text.find("【상 법 30문】", start)
    section = text[start : end if end != -1 else len(text)]
    matches = list(re.finditer(r"【문\s*(\d+)】", section))
    if len(matches) < QUESTION_COUNT:
        raise ValueError(f"expected {QUESTION_COUNT} constitution questions, got {len(matches)}")
    blocks: dict[int, str] = {}
    for idx, match in enumerate(matches[:QUESTION_COUNT]):
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
        statement = re.split(r"\s*제1과목\s*①책형\s*전체|\s*【\s*제1과목|\s*【\s*상 법", statement)[0]
        out[marker.group(0)] = normalize_raw(statement)
    return out


def raw_statement_map(blocks: dict[int, str]) -> dict[tuple[int, str], str]:
    raw: dict[tuple[int, str], str] = {}
    for no in range(1, QUESTION_COUNT + 1):
        split = split_choice_units(blocks[no])
        for label in LABELS:
            raw[(no, label)] = split[label]
    return raw


def source_verdict(no: int, label: str) -> str:
    return "X" if label in FALSE_LABELS[no] else "O"


def load_atom_rows() -> dict[tuple[int, str], list[dict[str, str | None]]]:
    rows: dict[tuple[int, str], list[dict[str, str | None]]] = {}
    for line in ATOM_ROWS.splitlines():
        no_text, label, atom_index, verdict, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        if verdict not in {"O", "X"}:
            raise ValueError(f"bad atom verdict: {line}")
        if verdict == "X" and not trap:
            raise ValueError(f"X atom without trap: {line}")
        if verdict == "O" and trap:
            raise ValueError(f"O atom with trap: {line}")
        rows.setdefault((int(no_text), label), []).append(
            {
                "atomIndex": atom_index.strip(),
                "sourceVerdict": verdict,
                "rep": rep.strip(),
                "trap": trap,
            }
        )
    return rows


def complete_sentence(rep: str) -> str:
    rep = rep.strip()
    return rep if rep.endswith(".") else rep.rstrip(".") + "."


def source_label(no: int) -> str:
    return f"{YEAR} 법무사 {ROUND}회 {SUBJECT_NAME} {no}번 {OFFICIAL_ANSWERS[no]} 기출"


def basis(no: int) -> tuple[str, str, str]:
    topic = TOPICS[no]
    return (
        "헌법+헌법재판소 결정례+대법원 판례",
        f"{topic} 관련 헌법·헌법재판소법·개별 법령 및 헌법재판소 결정례·대법원 판례",
        f"{topic}의 출제 지점을 독립 명제로 정리한다.",
    )


def build_source(raws: dict[tuple[int, str], str]) -> dict[str, object]:
    questions = []
    for no in range(1, QUESTION_COUNT + 1):
        qid = f"2023-g1-constitution-{no:02d}"
        units = []
        for label in LABELS:
            units.append(
                {
                    "unitId": f"{qid}-{LABEL_CODE[label]}",
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
                    "source": q["sourceLabel"],
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


def build_completed(queue: dict[str, object]) -> dict[str, object]:
    atom_rows = load_atom_rows()
    items = []
    for item in queue["items"]:
        key = (item["no"], item["unitLabel"])
        if key not in atom_rows:
            raise ValueError(f"missing atom rows: {key}")
        basis_type, basis_ref, why = basis(item["no"])
        for row in atom_rows[key]:
            rep = complete_sentence(str(row["rep"]))
            trap = row["trap"]
            source_is_x = row["sourceVerdict"] == "X"
            atom = {
                "atomId": f"bupmusa-2023-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}-{row['atomIndex']}",
                "sourceUnitId": item["unitId"],
                "sourceAtomIndex": row["atomIndex"],
                "sourceFamily": "법무사시험",
                "source": item["source"],
                "year": YEAR,
                "round": ROUND,
                "subject": SUBJECT_NAME,
                "no": item["no"],
                "unitType": item["unitType"],
                "unitLabel": item["unitLabel"],
                "sourceQuestionType": item["sourceQuestionType"],
                "officialQuestionAnswer": item["officialQuestionAnswer"],
                "sourceUnitVerdict": item["originalVerdict"],
                "sourceVerdict": row["sourceVerdict"],
                "currentVerdict": "O",
                "rep": rep,
                "a": "O",
                "basisType": basis_type,
                "basisRef": basis_ref,
                "why": why,
                "sourceStatement": item["rawStatement"],
                "sourceTrap": trap,
                "xDependsOn": rep if source_is_x else None,
                "reviewedAt": today(),
                "currentLawCheckedAt": today(),
            }
            items.append(atom)
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
            "atomSplit": "원문 보기 하나가 여러 조문·판례·학설 판단 지점을 포함하면 여러 atom으로 분해한다.",
            "xHandling": "원문상 틀린 판단 지점은 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
            "countAndCombination": "조합형 문제는 선택지 조합이 아니라 ㄱ·ㄴ·ㄷ 등 개별 근거명제로 atom화한다.",
        },
        "items": items,
    }


def validate_atom_text(items: list[dict[str, object]]) -> None:
    banned_tokens = ["?", "？", "위 ①", "위 ②", "위 ③", "위 ④", "위 ⑤", "다음 설명", "가장 옳", "옳지 않은"]
    for item in items:
        rep = item["rep"]
        if any(token in rep for token in banned_tokens):
            raise ValueError(f"non-atom wording in rep: {item['atomId']} {rep}")
        if re.search(r"\s{2,}", rep):
            raise ValueError(f"double whitespace in rep: {item['atomId']} {rep}")
        if item["sourceVerdict"] == "X":
            if not item["sourceTrap"] or item["xDependsOn"] != rep:
                raise ValueError(f"missing X dependency: {item['atomId']}")
        elif item["sourceTrap"] is not None or item["xDependsOn"] is not None:
            raise ValueError(f"unexpected X metadata: {item['atomId']}")


def validate(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    if source["questionCount"] != QUESTION_COUNT:
        raise ValueError("unexpected question count")
    if queue["itemCount"] != SOURCE_UNIT_COUNT:
        raise ValueError("source unit count mismatch")
    if completed["atomCount"] < MIN_ATOM_COUNT:
        raise ValueError(f"atom count too low for legal-point split: {completed['atomCount']}")
    ids = [item["atomId"] for item in completed["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
    source_unit_ids = {item["unitId"] for item in queue["items"]}
    covered_unit_ids = {item["sourceUnitId"] for item in completed["items"]}
    if source_unit_ids != covered_unit_ids:
        missing = sorted(source_unit_ids - covered_unit_ids)
        raise ValueError(f"missing atom coverage for source units: {missing[:5]}")
    false_units = {
        f"2023-g1-constitution-{no:02d}-{LABEL_CODE[label]}"
        for no, labels in FALSE_LABELS.items()
        for label in labels
    }
    false_atom_units = {
        item["sourceUnitId"] for item in completed["items"] if item["sourceVerdict"] == "X"
    }
    if not false_units.issubset(false_atom_units):
        missing = sorted(false_units - false_atom_units)
        raise ValueError(f"false source units without X atom: {missing}")
    true_atom_errors = [
        item["atomId"]
        for item in completed["items"]
        if item["sourceUnitVerdict"] == "O" and item["sourceVerdict"] == "X"
    ]
    if true_atom_errors:
        raise ValueError(f"X atoms under true source units: {true_atom_errors[:5]}")
    validate_atom_text(completed["items"])


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_index(source: dict[str, object], queue: dict[str, object], completed: dict[str, object]) -> None:
    index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8")) if SUBJECT_INDEX_PATH.exists() else {
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
        "questionCount": source["questionCount"],
        "atomQueueItemCount": queue["itemCount"],
        "completedAtomCount": completed["atomCount"],
        "completedAtomsUpdatedAt": completed["updatedAt"],
    }
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
    update_index(source, queue, completed)
    counts = Counter(item["sourceVerdict"] for item in completed["items"])
    print(f"wrote {OUT_PATH}")
    print(f"questions={source['questionCount']} atoms={completed['atomCount']} O={counts['O']} X={counts['X']}")


if __name__ == "__main__":
    main()
