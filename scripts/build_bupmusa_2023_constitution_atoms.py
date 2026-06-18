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
EXPECTED_ATOM_COUNT = 100
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

REP_ROWS = """
1|①|국가배상법상 공무원은 국가공무원법이나 지방공무원법상 공무원 신분을 가진 사람에 한정되지 않고, 공무를 위탁받아 실질적으로 공무에 종사하는 사람을 포함한다.|
1|②|형사보상청구 제척기간을 무죄재판 확정일부터 1년으로 제한하거나 형사보상결정에 대한 불복을 허용하지 않는 것은 형사보상청구권 또는 재판청구권을 침해할 수 있다.|형사보상청구의 1년 제척기간과 형사보상결정 불복금지가 형사보상청구권을 침해하지 않는다고 한 부분
1|③|국회의원의 입법행위는 입법내용이 헌법 문언에 명백히 위반되는데도 국회가 굳이 입법한 특수한 경우가 아닌 한 국가배상법상 위법행위로 볼 수 없다.|
1|④|국가나 지방자치단체가 공권력 행사가 아니라 사경제 주체로 활동한 경우 그 손해배상책임에는 국가배상법이 아니라 민법상 사용자책임 등이 적용될 수 있다.|
1|⑤|검사의 무혐의 불기소처분으로 재판절차진술권을 침해받았다고 주장하여 헌법소원을 제기하려면 헌법 제27조 제5항이 보장하는 형사피해자에 해당하여야 한다.|
2|①|헌법상 정당한 보상은 원칙적으로 피수용재산의 객관적 재산가치를 완전하게 보상하는 것을 뜻하고, 개발이익은 완전보상의 범위에 포함되지 않는다.|
2|②|헌법 제23조 제3항은 재산권 수용의 주체를 국가 등 공적 기관으로 한정하지 않으므로, 공공필요와 정당보상 요건을 충족하면 민간개발자에게도 수용권한을 부여할 수 있다.|
2|③|사회부조처럼 국가가 일방적으로 지급하는 금전급부에 대한 기대는 사적 재산권과 같지 않으므로, 단순히 금전급부라는 이유만으로 헌법상 재산권 보호대상에 포함되지는 않는다.|사회부조와 같은 국가의 일방적 금전급부 권리가 원칙적으로 재산권 보호대상에 포함된다고 한 부분
2|④|헌법 제13조 제2항이 금지하는 소급입법에 의한 재산권 박탈은 이미 완성된 사실 또는 법률관계를 사후적으로 규율하는 진정소급입법을 말한다.|
2|⑤|공익성이 낮은 고급골프장사업에 관하여 행정기관의 실시계획 승인·고시만으로 민간개발자에게 수용권한을 부여하는 법률조항은 헌법 제23조 제3항에 위반된다.|
3|①|사면의 종류, 대상, 범위, 절차와 효과는 범죄의 죄질, 보호법익, 국민 법감정, 국가이익과 권력분립 원칙 등을 종합하여 입법자가 형성할 사항이다.|
3|②|사면은 형 선고의 효력이나 공소권을 상실시키거나 형 집행을 면제하는 국가원수의 권한으로서, 사법부 판단을 변경하는 권력분립 원리의 예외에 해당한다.|
3|③|특별사면은 이미 형의 선고를 받은 특정인에 대하여 형의 집행을 면제하거나 특별한 사정이 있으면 선고의 효력을 상실하게 하는 사면이다.|
3|④|대통령이 일반사면을 명하려면 국회의 동의를 얻어야 한다.|대통령의 사면권 행사는 국회의 동의를 받을 필요가 없다고 한 부분
3|⑤|복권은 형 선고로 상실되거나 정지된 자격을 회복시키는 것이며, 형 집행이 끝나지 않았거나 집행이 면제되지 않은 사람에 대해서는 할 수 없다.|
4|①|민사소송법상 재심사유를 어떻게 정할지는 확정판결의 법적 안정성, 재판의 신속·적정성, 법원의 업무부담 등을 고려하여 입법자가 정할 입법정책의 영역이다.|
4|②|판결주문에 영향이 없는 공격방어방법에 대한 판단누락이나 판결주문과 간접적으로만 관련되는 판단이유 누락은 재심으로 확정판결의 효력을 배제할 만큼 정의의 요청이 절박하다고 볼 수 없다.|판결주문에 영향이 없는 공격방어방법 판단누락은 판단이유 누락과 달리 재심으로 확정판결 효력을 배제할 만큼 정의 요청이 절박하다고 한 부분
4|③|재심사유의 위헌성은 입법자가 재판의 적정성을 현저히 희생하여 재판청구권의 본질을 심각하게 훼손하는 등 입법형성권 한계를 일탈한 경우에 인정될 수 있다.|
4|④|재심은 확정판결에 대한 불복방법이므로 미확정판결에 대한 상소보다 훨씬 큰 법적 안정성 요청을 받으며, 상소보다 예외적으로 인정된다.|
4|⑤|민사소송법상 판단누락 재심사유는 확립된 판례에 의해 의미와 적용 기준을 예측할 수 있어 명확성원칙에 위배되지 않는다.|
5|①|대한변호사협회의 변호사 광고에 관한 규정 중 변호사 광고·홍보·소개 행위를 금지하는 규정은 헌법소원의 대상이 되는 공권력 행사에 해당할 수 있다.|
5|②|대한변호사협회의 유권해석에 반하는 광고를 금지하고 그 위반행위를 목적 또는 수단으로 하는 법률상담 관련 광고를 금지하는 변호사 광고규정은 법률유보원칙에 위반될 수 있다.|
5|③|무료 또는 부당한 염가의 수임료나 법률상담 방식을 내세운 변호사 광고를 금지하는 것은 공정한 수임질서 확립을 위한 것으로 과잉금지원칙에 위배되지 않는다.|
5|④|변호사 등이 아닌 사람의 직무 관련 서비스 표시나 소비자를 변호사 등으로 오인하게 할 수 있는 행위에 대한 광고 의뢰·참여·협조를 금지하는 것은 변호사자격제도 유지와 소비자 보호를 위한 적합한 수단이다.|
5|⑤|변호사 또는 소비자로부터 대가를 받고 변호사 등을 광고·홍보·소개하는 행위를 금지하는 변호사 광고규정 부분은 과잉금지원칙에 위반되어 표현의 자유와 직업의 자유를 침해할 수 있다.|대가수수 변호사 광고·홍보·소개 금지규정이 과잉금지원칙에 위배되지 않는다고 한 부분
6|①|공무원이 지위를 이용하여 범한 공직선거법위반죄의 공소시효를 해당 선거일 후 10년으로 정한 것은 합리적 이유가 있는 차별로서 평등원칙에 위반되지 않는다.|
6|②|반복 절도범 가중처벌규정이 형법상 절도죄, 야간주거침입절도죄, 특수절도죄를 함께 규율하더라도 그 사정만으로 불법성이 다른 범죄를 자의적으로 동등취급하여 평등원칙에 위반된다고 단정할 수 없다.|특정범죄가중처벌법상 반복 절도범 가중처벌규정이 여러 절도범죄를 동등취급하여 평등원칙에 위반된다고 한 부분
6|③|선거와 무관하게 후원회를 설치·운영할 수 있는 자를 중앙당과 국회의원으로 한정하여 국회의원과 지방의회의원을 달리 취급하는 것은 불합리한 차별에 해당할 수 있다.|
6|④|군형법이 강제추행죄와 항거불능상태 이용 준강제추행죄에 벌금형을 선택형으로 두지 않았더라도 형벌체계의 균형성을 상실하여 평등원칙에 위반된다고 볼 수는 없다.|
6|⑤|동일한 밀수입 예비행위라도 물품원가 2억 원 미만에는 관세법상 감경이 적용되고 2억 원 이상에는 특정범죄가중처벌법상 본죄에 준한 가중처벌이 적용되는 것은 합리적 이유가 있다고 보기 어렵다.|
7|①|부모가 자녀의 이름을 지을 자유는 자녀 양육과 가족생활의 핵심 요소로서 헌법 제36조 제1항과 헌법 제10조에 의하여 보호된다.|
7|②|초등학교 정규교과에서 영어를 배제하거나 영어교육 시수를 제한하는 것은 균형 있는 교육과 사교육 폐단 방지를 위한 것으로 학생의 인격발현권을 침해하지 않는다.|
7|③|거짓이나 부정한 수단으로 운전면허를 받은 경우 부정취득하지 않은 운전면허까지 필요적으로 취소하게 하는 것은 일반적 행동의 자유를 침해한다.|
7|④|사자에 대한 친일반민족행위결정은 그 사자와의 관계에서 인격상과 명예를 형성해 온 후손의 인격권, 유족의 명예 또는 경애추모의 정을 제한할 수 있다.|사자에 대한 친일반민족행위결정은 후손의 법적 지위에 아무 영향이 없어 후손의 인격권도 제한하지 않는다고 한 부분
7|⑤|헌법 제10조가 보장하는 개인의 인격권과 행복추구권은 자기운명결정권을 전제로 하며, 그 안에는 성행위 여부와 상대방을 결정할 성적 자기결정권이 포함된다.|
8|①|국가기관의 법률상 권한은 국회의 입법행위로 형성·부여된 권한이므로, 국회의 입법행위가 침해 원인인 경우 법률상 권한 침해를 이유로 한 권한쟁의심판청구는 권한침해가능성이 인정되지 않는다.|
8|②|국가기관과 지방자치단체 간 권한쟁의심판에서 헌법재판소법상 정부는 예시적 개념이므로 정부의 부분기관도 당사자가 될 수 있다.|
8|③|국가기관과 지방자치단체 간 또는 지방자치단체 상호 간 권한쟁의심판에서 지방자치단체의 기관인 지방의회나 교육감은 원칙적으로 당사자능력이 인정되지 않는다.|
8|④|광역지방자치단체가 자치사무 감사에 착수하려면 감사대상을 특정하여야 하지만, 연간 감사계획에 포함되지 않고 사전조사가 없는 감사라고 하여 특정된 감사대상을 사전에 통보할 것까지 항상 요구되는 것은 아니다.|특정된 감사대상의 사전 통보가 언제나 자치사무 감사의 개시요건이라고 한 부분
8|⑤|권한쟁의심판의 대상인 처분은 법적 중요성이 있는 행위이어야 하므로 정부의 법률안 제출행위, 단순한 견해표명이나 업무연락은 권한쟁의심판의 대상이 되지 않는다.|
9|①|형제자매가 본인과 항상 이해관계를 같이하지 않는데도 본인의 친족·상속 관련 증명서를 편리하게 발급받도록 하는 법률조항은 개인정보자기결정권을 침해한다.|
9|②|강제추행죄 유죄판결 확정자를 신상정보 등록대상자로 정한 조항은 재범위험성을 별도로 요구하지 않더라도 개인정보자기결정권을 침해한다고 볼 수 없다.|강제추행죄 등록대상자 조항이 재범위험성을 요구하지 않아 개인정보자기결정권을 침해한다고 한 부분
9|③|변호사시험 합격자가 결정되면 법무부장관이 즉시 명단을 공고하도록 하는 것은 법률서비스 수요자에게 필요한 정보를 제공하기 위한 것으로 응시자의 개인정보자기결정권을 침해하지 않는다.|
9|④|선거운동기간 중 인터넷언론사 게시판 등에 정당·후보자 지지·반대 정보를 게시할 때 실명확인 기술조치를 요구하는 조항은 익명표현과 개인정보자기결정권을 침해한다.|
9|⑤|성적목적공공장소침입죄 유죄판결 확정자를 신상정보 등록대상자로 정한 조항은 범죄 성립 장소와 등록대상 범위가 제한되므로 개인정보자기결정권을 침해한다고 볼 수 없다.|
10|①|형사재판 유죄확정판결 후 처벌 근거조항에 위헌결정이 내려진 경우 유죄판결을 받은 사람은 재심청구로 그 확정판결을 다툴 수 있다.|
10|②|헌법재판소법은 법률의 위헌결정, 권한쟁의심판 결정, 헌법소원 인용결정에 대한 기속력을 명문으로 규정하고 있다.|
10|③|형벌조항이 위헌으로 결정되면 소급하여 효력을 상실하되, 종전에 합헌으로 결정한 사건이 있으면 그 합헌결정이 있는 날의 다음 날로 소급하여 효력을 상실한다.|종전 합헌결정이 있는 경우 그 합헌결정일 자체로 소급하여 효력을 상실한다고 한 부분
10|④|형벌조항에 대하여 헌법불합치결정과 잠정적용명령이 선고된 경우에도 헌법재판소법상 형벌조항 위헌결정의 소급효가 문제될 수 있다.|
10|⑤|법률조항의 위헌결정으로 당해 법률 전부를 시행할 수 없다고 인정될 때에는 그 법률 전부에 대해서도 위헌결정을 할 수 있다.|
11|①|탄핵심판절차는 고위공직자의 헌법위반을 사전에 경고하고, 국가기관이 권한을 남용하여 헌법이나 법률에 위반한 경우 그 권한을 박탈함으로써 헌법의 규범력을 확보하는 기능을 한다.|
11|②|국회의 탄핵소추 절차에 명백한 헌법·법률 위반이 없는 한 국회의 의사절차 자율권은 존중되어야 하며, 별도 조사 없이 탄핵소추안을 의결했다는 사정만으로 위법하다고 볼 수 없다.|
11|③|대통령 외 공무원에 대한 탄핵소추는 국회재적의원 3분의 1 이상의 발의와 재적의원 과반수 찬성이 필요하고, 대통령 탄핵소추는 재적의원 과반수 발의와 3분의 2 이상의 찬성이 필요하다.|
11|④|국가기관이 국민에게 공권력을 행사할 때 준수하여야 할 법원칙으로 형성된 적법절차원칙은 헌법수호를 위한 탄핵소추절차에 그대로 직접 적용된다고 볼 수 없다.|
11|⑤|탄핵심판청구와 동일한 사유로 형사소송이 진행 중인 경우 재판부는 심판절차를 정지할 수 있지만 반드시 정지하여야 하는 것은 아니다.|탄핵심판과 동일한 사유로 형사소송이 진행되면 재판부가 반드시 심판절차를 정지하여야 한다고 한 부분
12|①|헌법 제7조 제2항의 직업공무원제도는 엽관제를 지양하여 정치와 공직을 분리하고 공무수행의 안정성과 전문성을 확보하려는 제도이다.|
12|②|공무원은 원칙적으로 정당의 발기인 및 당원이 될 수 없지만, 정당법상 예외에는 대통령, 국무총리, 국무위원, 국회의원, 지방의회의원과 선거로 취임하는 지방자치단체장 등이 포함되고 교육감은 포함되지 않는다.|정당가입 허용 예외 공무원에 교육감까지 포함된다고 한 부분
12|③|직업공무원의 신분보장은 국민 전체를 위한 소신 있는 직무수행을 가능하게 하기 위한 것이며, 생계보호와 직업보호의 의미도 있어 공무담임권의 보호영역에 포함된다.|
12|④|직무 내외를 불문하고 체면이나 위신을 손상하는 행위를 징계사유로 정한 국가공무원법 규정은 명확성원칙이나 과잉금지원칙에 위반된다고 볼 수 없다.|
12|⑤|직업공무원제도에서는 직위분류제나 성적주의에 따른 인사 공정성 장치도 중요하지만, 그 중추적 요소는 공무원의 정치적 중립과 신분보장이다.|
13|①|헌법상 적법절차원칙은 형사절차에 한정되지 않고, 기본권 제한과 관련되는 행정작용 등 국가작용에도 적용될 수 있다.|적법절차원칙이 형사절차상의 제한된 범위에만 적용되고 행정작용에는 적용되지 않는다고 한 부분
13|②|개인정보자기결정권은 자신에 관한 정보가 언제 누구에게 어느 범위까지 알려지고 이용되도록 할지 정보주체가 스스로 결정할 권리로서 헌법 제10조와 제17조에서 보장된다.|
13|③|헌법상 영장주의는 형사절차에서 체포·구속·압수·수색 같은 강제처분을 할 때 독립한 법관이 발부한 영장에 의하여야 한다는 원칙이다.|
13|④|법무부장관의 일방적 명령으로 변호사업무를 정지시키면서 변호사에게 유리한 사실진술이나 증거제출의 청문 기회를 보장하지 않으면 적법절차원칙에 반할 수 있다.|
13|⑤|피고인이 스스로 치료감호를 청구할 권리나 법원으로부터 직권으로 치료감호를 선고받을 권리는 헌법상 재판청구권의 보호범위에 포함되지 않는다.|
14|①|국회의 정기회는 법률이 정하는 바에 따라 매년 1회 집회되고, 임시회는 대통령 또는 국회재적의원 4분의 1 이상의 요구로 집회된다.|
14|②|국회에서 의결된 법률안에 이의가 있으면 대통령은 이송 후 15일 이내에 이의서를 붙여 법률안 전체를 국회로 환부하여 재의를 요구할 수 있고, 일부 조항에 대한 부분적 재의요구는 허용되지 않는다.|대통령이 법률안의 전부 또는 일부에 관한 이의서를 붙여 재의를 요구할 수 있다고 한 부분
14|③|국회나 그 위원회의 요구가 있으면 국무총리·국무위원 또는 정부위원은 출석·답변하여야 하며, 국무총리 또는 국무위원은 국무위원 또는 정부위원으로 하여금 출석·답변하게 할 수 있다.|
14|④|국회는 직무집행에서 헌법이나 법률을 위반한 검사뿐만 아니라 고위공직자범죄수사처 검사에 대해서도 탄핵소추를 의결할 수 있다.|
14|⑤|국회는 정부의 동의 없이 정부가 제출한 지출예산 각항의 금액을 증가하거나 새 비목을 설치할 수 없고, 직접 추가경정예산안을 제출할 수도 없다.|
15|①|공무담임권은 모든 국민이 현실적으로 공직을 담당할 수 있다는 의미가 아니라 공직취임 기회를 자의적으로 배제당하지 않을 기회를 보장한다.|
15|②|직업공무원의 공직진출 규율은 정치적 중립성과 효율적 업무수행 능력을 고려하여 능력주의를 바탕으로 이루어져야 한다.|
15|③|교육의원 후보자에게 일정한 교육경력 또는 교육행정경력을 요구하는 것은 교육의 자주성·전문성·정치적 중립성과 지방자치 이념 구현을 위한 것으로 공무담임권을 침해하지 않는다.|
15|④|금고 이상의 형의 선고유예를 받은 군무원을 군무원직에서 당연퇴직시키는 조항은 공무담임권을 침해한다.|금고 이상의 형의 선고유예를 받은 군무원의 당연퇴직 조항이 공무담임권을 침해하지 않는다고 한 부분
15|⑤|후보자가 되고자 하는 사람의 기부행위를 처벌하는 공직선거법 조항 자체는 공무담임권을 직접 제한하는 것이 아니라, 일정 형 선고에 따른 당선무효·피선거권 제한 등이 별도 조항 적용으로 나타나는 결과이다.|
16|①|지방자치법상 지방자치단체의 기관으로는 대의기관인 지방의회와 집행기관인 지방자치단체장이 있다.|
16|②|지방의회는 조례의 제정·개정·폐지, 예산의 심의·확정, 결산 승인, 행정사무감사 및 조사권을 가지지만 지방자치단체 규칙의 제정·개정·폐지 권한은 지방자치단체장에게 속한다.|지방의회가 조례뿐 아니라 지방자치단체 규칙의 제정·개정·폐지 권한도 가진다고 한 부분
16|③|지방자치단체는 사무처리를 위한 행정기구를 설치할 수 있고, 소속 공무원에 관한 임용과 징계 등 인사를 스스로 할 수 있다.|
16|④|기관위임사무는 국가사무이므로 지방자치단체가 기관위임사무에 관한 권한쟁의심판을 청구하는 것은 허용되지 않는다.|
16|⑤|감사원은 지방자치단체에 대하여 합목적성 감사도 할 수 있지만, 중앙행정기관의 자치사무 감사는 합법성 감사에 한정된다.|
17|①|양육비대지급제 등 양육비 이행의 실효성을 더 높이는 법률을 제정할 명시적 헌법위임이나 구체적 입법의무는 인정되기 어렵다.|
17|②|진정입법부작위 헌법소원은 명시적 입법위임이 있는데도 입법자가 이행하지 않았거나, 헌법해석상 구체적 행위의무가 명백한데도 아무런 입법조치를 하지 않은 경우에 한하여 허용된다.|
17|③|의료인이 아닌 사람의 문신시술업 자격과 요건을 법률로 정하라는 명시적 헌법위임은 없고, 별도 자격제도를 마련할지 여부는 입법부가 결정할 사항이다.|
17|④|가정폭력 가해자인 전 배우자의 자녀 가족관계증명서 및 기본증명서 교부청구를 제한하지 않은 것은 개인정보자기결정권을 침해할 수 있으나, 이는 이미 관련 교부청구 제도를 둔 법률의 불완전·불충분 규율에 관한 부진정입법부작위 문제이다.|가정폭력 가해자의 증명서 교부청구 제한규정 부재가 진정입법부작위에 해당한다고 한 부분
17|⑤|북한인권법 미제정 입법부작위에 관한 헌법소원 계속 중 국회가 북한인권법을 제정하였다면 권리보호이익이 소멸하고 헌법적 해명의 필요성도 없으면 심판청구는 부적법하다.|
18|①|대법원이 법관 징계처분 취소청구소송을 단심으로 재판하더라도 대법원이 사실확정까지 담당하므로 법관에 의한 사실확정 기회가 박탈되었다고 볼 수 없다.|
18|②|단독판사와 합의부의 심판권 분배 등 재판사무 범위 배분은 국민의 권리보호와 재판제도의 적정 운용을 고려하여 입법자가 정할 사법정책의 영역이다.|
18|③|재판의 심리와 판결은 공개하되, 심리는 국가안전보장·안녕질서 방해나 선량한 풍속을 해할 염려가 있으면 법원의 결정으로 공개하지 않을 수 있다.|
18|④|명령·규칙 또는 처분이 헌법이나 법률에 위반되는지가 재판의 전제가 된 경우 그 최종 심사권은 대법원에 있다.|명령·규칙 또는 처분의 위헌·위법 여부가 재판 전제가 되면 법원이 헌법재판소에 제청하여 심판받아야 한다고 한 부분
18|⑤|형사재판에서 사법권의 독립은 심판기관인 법원과 소추기관인 검찰청의 분리와 함께 법관이 검사와 피고인으로부터 부당한 간섭 없이 독립하여야 함을 요구한다.|
19|①|특정 정당이나 정치인에 대한 정치자금 기부는 정치활동 또는 정치적 의사표현의 성격을 가지므로, 단체 관련 자금의 정치자금 기부금지는 정치활동의 자유와 정치적 표현의 자유를 제한한다.|
19|②|상업광고도 사상·지식·정보 등을 불특정 다수에게 전파하는 표현행위에 해당하므로 언론·출판의 자유에 의한 보호대상이 될 수 있다.|광고물은 상업적 목적으로 제작되어 언론·출판의 자유 보호대상이 아니라고 한 부분
19|③|청소년이용음란물도 의사표현·전파의 형식 중 하나이므로 언론·출판의 자유에 의해 보호되는 의사표현의 매개체에 해당한다.|
19|④|헌법 제21조의 표현의 자유는 사상 또는 의견의 발표와 전달의 자유를 뜻하며, 인간의 존엄과 국민주권 실현에 필수적인 정신적 자유의 외부적 표현을 보장한다.|
19|⑤|법원은 종교단체 내부관계가 일반 국민의 권리의무나 법률관계를 규율하는 것이 아닌 한 원칙적으로 실체적 심리판단을 자제하여 종교단체 자율권을 보장하여야 한다.|
20|①|집회의 자유는 개인의 인격발현 요소이자 민주주의 구성요소이고, 집단적 의견표명을 통하여 여론 형성에 영향을 미치므로 민주적 공동체에 필수적인 기본권이다.|
20|②|집회의 자유가 헌법적으로 보호하는 집회는 평화적 또는 비폭력적 집회이고, 폭력을 사용한 의견 강요는 집회의 자유 보호영역에 포함되지 않는다.|폭력을 사용한 의견 강요에 해당하는 집회도 헌법적으로 보호될 수 있다고 한 부분
20|③|집회 장소는 집회의 목적과 효과에 중요한 의미를 가지므로, 다른 법익 보호로 정당화되지 않는 한 집회 장소를 항의 대상에서 분리시키는 것은 제한된다.|
20|④|집회의 자유는 집회의 시간, 장소, 방법과 목적을 스스로 결정할 권리를 보장하며, 집회 참가·이동·귀가를 방해하거나 참가를 강요하는 국가행위를 금지한다.|
20|⑤|결사의 자유에서 말하는 결사는 자유의사에 따라 결합하고 조직화된 의사형성이 가능한 단체를 말하며, 공법상 결사는 이에 포함되지 않는다.|
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


def load_rep_rows() -> dict[tuple[int, str], dict[str, str | None]]:
    rows: dict[tuple[int, str], dict[str, str | None]] = {}
    for line in REP_ROWS.splitlines():
        no_text, label, rep, *rest = line.split("|")
        trap = rest[0].strip() if rest and rest[0].strip() else None
        rows[(int(no_text), label)] = {"rep": rep.strip(), "trap": trap}
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
    reps = load_rep_rows()
    items = []
    for item in queue["items"]:
        key = (item["no"], item["unitLabel"])
        if key not in reps:
            raise ValueError(f"missing rep row: {key}")
        rep = complete_sentence(str(reps[key]["rep"]))
        trap = reps[key]["trap"]
        basis_type, basis_ref, why = basis(item["no"])
        source_is_x = item["originalVerdict"] == "X"
        atom = {
            "atomId": f"bupmusa-2023-constitution-q{item['no']:02d}-{LABEL_CODE[item['unitLabel']]}",
            "sourceUnitId": item["unitId"],
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
            "sourceVerdict": item["originalVerdict"],
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
        if source_is_x and not trap:
            raise ValueError(f"X item without sourceTrap: {key}")
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
            "xHandling": "출제 원문상 X인 경우에도 rep는 올바른 O 법리로 정규화하고 sourceTrap과 xDependsOn을 기록한다.",
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
    if queue["itemCount"] != EXPECTED_ATOM_COUNT or completed["atomCount"] != EXPECTED_ATOM_COUNT:
        raise ValueError("atom count mismatch")
    verdict_counts = Counter(item["sourceVerdict"] for item in completed["items"])
    if verdict_counts != Counter({"O": 80, "X": 20}):
        raise ValueError(f"unexpected verdict counts: {verdict_counts}")
    ids = [item["atomId"] for item in completed["items"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomId")
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
