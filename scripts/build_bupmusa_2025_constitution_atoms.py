from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PRIVATE_ROOT = WORKSPACE / "law-test-private" / "private_problem_banks" / "법무사"
SUBJECT_DIR = PRIVATE_ROOT / "current" / "2025" / "과목별"
SOURCE_PATH = SUBJECT_DIR / "2025_법무사_헌법_source.json"
QUEUE_PATH = SUBJECT_DIR / "2025_법무사_헌법_atom_queue.json"
OUT_PATH = SUBJECT_DIR / "2025_법무사_헌법_atoms.json"
SUBJECT_INDEX_PATH = SUBJECT_DIR / "2025_법무사_과목별_index.json"
INTEGRATED_DIR = PRIVATE_ROOT / "current" / "통합본"
INTEGRATED_PATH = INTEGRATED_DIR / "법무사_헌법_통합_atom.json"

SUBJECT_NAME = "헌법"
YEAR = 2025
ROUND = 31
SOURCE_UNIT_COUNT = 100
MIN_ATOM_COUNT = 145
LABELS = ["①", "②", "③", "④", "⑤"]
LABEL_CODE = {"①": "01", "②": "02", "③": "03", "④": "04", "⑤": "05"}

LEGAL_SOURCES = [
    {"title": "대한민국헌법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/대한민국헌법"},
    {"title": "헌법재판소법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/헌법재판소법"},
    {"title": "공직선거법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/공직선거법"},
    {"title": "정당법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/정당법"},
    {"title": "국회법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/국회법"},
    {"title": "지방자치법", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/법령/지방자치법"},
    {"title": "2025 법무사 헌법 문제 정답", "publisher": "공기출", "url": "https://0gichul.com/y2025/130911276"},
    {"title": "헌법재판소 결정례", "publisher": "국가법령정보센터", "url": "https://www.law.go.kr/LSW/detcInfoP.do"},
]

TOPICS = {
    1: "이중처벌금지원칙",
    2: "표현의 자유",
    3: "변호인의 조력을 받을 권리",
    4: "입법부작위",
    5: "헌법소원 권리보호이익",
    6: "평등원칙",
    7: "직업의 자유",
    8: "헌법소원 대상 공권력",
    9: "책임과 형벌의 비례 및 기본권 제한",
    10: "기본권 충돌",
    11: "선거원칙",
    12: "국방의 의무",
    13: "재산권",
    14: "장애인의 접근권과 행정입법부작위",
    15: "정당",
    16: "국회의원과 국회의장",
    17: "기본권 경합",
    18: "조례",
    19: "국무회의",
    20: "국회",
}

BASIS: dict[int, tuple[str, str, str]] = {
    1: ("헌법+헌법재판소 결정례", "헌법 제13조 제1항 및 이중처벌금지원칙 관련 헌법재판소 결정례", "이중처벌금지원칙의 처벌은 국가형벌권 행사를 중심으로 판단한다."),
    2: ("헌법+헌법재판소 결정례", "헌법 제21조 및 표현의 자유·검열금지원칙 관련 헌법재판소 결정례", "표현의 자유 보호영역과 사전검열 금지의 판단기준이다."),
    3: ("헌법+헌법재판소 결정례", "헌법 제12조 제4항·제5항 및 변호인 조력권 관련 헌법재판소 결정례", "변호인 조력권의 주체, 범위, 핵심 내용을 판단한다."),
    4: ("헌법재판소 결정례", "헌법재판소법 제68조 제2항 및 입법부작위 관련 헌법재판소 결정례", "진정입법부작위와 부진정입법부작위의 구별 기준이다."),
    5: ("헌법재판소 결정례", "헌법소원 권리보호이익 및 예외적 심판이익 관련 헌법재판소 결정례", "기본권 침해 종료 뒤 권리보호이익과 예외적 심판이익 인정 기준이다."),
    6: ("헌법재판소 결정례", "평등원칙 관련 헌법재판소 결정례", "차별취급과 합리적 이유 여부를 중심으로 평등원칙 위반을 판단한다."),
    7: ("헌법+헌법재판소 결정례", "헌법 제15조 및 직업의 자유 관련 헌법재판소 결정례", "직업선택의 자유와 직업수행의 자유 제한의 정당성을 판단한다."),
    8: ("헌법재판소 결정례", "헌법재판소법 제68조 제1항 및 공권력 행사·불행사 관련 헌법재판소 결정례", "헌법소원 대상인 공권력 행사·불행사의 요건이다."),
    9: ("헌법재판소 결정례", "책임과 형벌 간 비례원칙 및 과잉금지원칙 관련 헌법재판소 결정례", "형벌조항과 기본권 제한 조항의 위헌심사 기준이다."),
    10: ("헌법재판소 결정례+대법원 판례", "기본권 충돌과 법익형량 관련 헌법재판소·대법원 판례", "기본권 충돌 시 우열 또는 법익형량으로 조화롭게 해결한다."),
    11: ("헌법+헌법재판소 결정례", "헌법 제41조·제67조 및 선거원칙 관련 헌법재판소 결정례", "보통·평등·자유·비밀선거 원칙과 선거구 획정 기준이다."),
    12: ("헌법+헌법재판소 결정례", "헌법 제39조 및 국방의 의무 관련 헌법재판소 결정례", "국방의 의무와 병역의무 이행에 따른 불이익 금지를 구별한다."),
    13: ("헌법+헌법재판소 결정례", "헌법 제13조 제2항, 제23조 및 재산권 관련 헌법재판소 결정례", "재산권 보호영역과 사회적 제약 및 소급입법 제한 기준이다."),
    14: ("헌법+헌법재판소 결정례", "헌법 제10조·제34조 및 장애인 접근권·행정입법부작위 관련 헌법재판소 결정례", "장애인 접근권의 기본권성과 행정입법의무 위반 기준이다."),
    15: ("헌법+헌법재판소법+정당법", "헌법 제8조, 제111조 제1항 제4호, 헌법재판소법 제62조 및 정당법", "정당의 헌법상 지위와 정당해산·권한쟁의 당사자능력 기준이다."),
    16: ("헌법+국회법+헌법재판소 결정례", "헌법 제44조, 국회법 및 국회의원 권한 관련 헌법재판소 결정례", "국회의원 석방요구, 국회의장 지위와 의원의 심의·표결권 기준이다."),
    17: ("헌법재판소 결정례", "기본권 경합과 심사기준 관련 헌법재판소 결정례", "복수 기본권이 문제될 때 중심 기본권을 정하는 기준이다."),
    18: ("지방자치법+주민조례발안법+대법원 판례", "지방자치법, 주민조례발안법 및 조례안 재의결무효확인소송 관련 대법원 판례", "조례 제정·재의·재의결무효확인 및 교육감 조례안 제출 절차 기준이다."),
    19: ("헌법+국무회의 규정+상훈법", "헌법 제89조, 국무회의 규정, 상훈법 및 국가안전보장회의법", "국무회의의 구성·의결·대리출석과 관련 심의 절차 기준이다."),
    20: ("헌법+국회법", "헌법 제47조·제50조·제53조, 국회법 및 인사청문회 관련 법령", "국회 회기, 회의공개, 법률안 재의결, 인사청문회 관할 기준이다."),
}

ATOM_ROWS = """
1|①|01|O|헌법 제13조 제1항의 이중처벌금지원칙은 거듭된 국가형벌권 행사를 금지한다.|
1|①|02|O|이중처벌금지원칙은 형벌권 행사에 덧붙이는 모든 제재나 불이익처분을 금지하는 것은 아니다.|
1|②|01|O|형벌과 보호감호를 함께 부과하더라도 그 성질과 목적이 다르면 이중처벌금지원칙에 위반되지 않는다.|
1|③|01|O|행정질서벌인 과태료와 형사처벌은 성질과 목적이 다른 별개의 제재이다.|
1|③|02|O|행정질서벌인 과태료 납부 후 형사처벌을 하더라도 일사부재리원칙에 반하지 않는다.|
1|④|01|X|행정처분에 제재와 억지의 성격이 있더라도 그것만으로 헌법 제13조 제1항의 처벌에 해당한다고 단정할 수 없다.|제재와 억지 성격만 있으면 국가형벌권 행사와 같은 처벌이라고 본 부분
1|⑤|01|O|부동산실명법상 과징금은 부당 또는 불법의 이득 환수와 위반행위자 제재의 성격을 함께 가진다.|
1|⑤|02|O|부동산실명법상 과징금을 형사처벌과 병과하는 문제는 이중처벌금지원칙보다 과잉금지원칙으로 심사한다.|
2|①|01|O|음란표현은 인간존엄이나 인간성을 왜곡하는 노골적 성표현으로서 문학적·예술적·과학적·정치적 가치를 결여한 표현을 말한다.|
2|①|02|X|엄격한 의미의 음란표현도 언론·출판의 자유 보호영역에는 속하지만, 헌법 제37조 제2항에 따라 제한될 수 있다.|음란표현이 언론·출판의 자유에 의해 보호되지 않는다고 단정한 부분
2|②|01|O|표현의 자유는 사상 또는 의견의 자유로운 표명과 전파의 자유를 포함한다.|
2|②|02|O|익명 또는 가명으로 사상이나 견해를 표명하고 전파할 자유도 표현의 자유에 포함된다.|
2|③|01|O|인터넷 게시판은 인터넷에서 의사를 형성하고 전파하는 매체이므로 표현의 자유에서 인정되는 의사표현·전파 형식에 해당한다.|
2|④|01|O|헌법 제21조 제2항의 검열금지는 사전검열 금지를 뜻한다.|
2|④|02|O|공개된 뒤 헌법상 보호되지 않는 표현에 대해 국가기관이 개입하는 것은 헌법상 검열금지에 당연히 포함되지 않는다.|
2|⑤|01|O|영화 상영 여부를 허가절차로 종국 결정하게 하는 것은 검열에 해당한다.|
2|⑤|02|O|유통단계 관리를 위한 영화 등급분류는 사전검열에 해당하지 않는다.|
3|①|01|O|체포·구속된 사람은 헌법상 변호인의 조력을 받을 권리를 가진다.|
3|①|02|O|불구속 피의자와 피고인도 법치국가원리와 적법절차원칙에 따라 변호인의 조력을 받을 권리를 가진다.|
3|②|01|O|피의자와 피고인의 변호인 조력권이 실질적으로 보장되려면 변호인이 조력할 권리의 핵심 부분도 헌법상 기본권으로 보호되어야 한다.|
3|③|01|O|변호인선임권은 변호인의 조력을 받을 권리의 출발점이다.|
3|③|02|O|변호인선임권은 변호인의 조력을 받을 권리의 기초적 구성부분으로서 법률로도 제한할 수 없다.|
3|④|01|X|출입국관리법상 보호 또는 강제퇴거 절차에서도 신체의 자유 제한과 방어권 보장이 문제되면 변호인의 조력을 받을 권리가 적용될 수 있다.|변호인 조력권이 출입국관리법상 보호 또는 강제퇴거 절차에 적용되기 어렵다고 본 부분
3|⑤|01|O|신체구속을 당한 사람의 변호인과 자유로운 접견은 변호인 조력권의 핵심 내용이다.|
3|⑤|02|O|신체구속을 당한 사람의 변호인 접견교통권은 국가안전보장, 질서유지, 공공복리 등의 명분으로도 제한될 수 없는 성질을 가진다.|
4|①|01|O|헌법재판소법 제68조 제2항 헌법소원은 법률의 위헌성을 다투는 제도이다.|
4|①|02|O|헌법재판소법 제68조 제2항 헌법소원으로 진정입법부작위 자체를 다투는 것은 허용되지 않는다.|
4|①|03|O|법률이 불완전·불충분하게 규정되었음을 주장하는 헌법소원은 그 법률의 재판전제성이 인정될 때 허용될 수 있다.|
4|②|01|O|행정절차상 위법하거나 부당한 구금 피해자에 대한 형사보상법상 보상규정 부재는 진정입법부작위에 해당한다.|
4|③|01|X|기소유예 취소결정 뒤 혐의없음 불기소처분을 받은 피의자에 대한 비용보상 규정 부재는 기존 비용보상 조항의 불완전 규율이 아니라 진정입법부작위에 해당한다.|피의자 비용보상 배제를 불완전·불충분한 규율로 본 부분
4|④|01|O|70세 이상 불구속피의자에 대한 국선변호인 선정제도 부재는 헌법소원 대상이 될 수 없는 입법부작위이다.|
4|⑤|01|O|6·25전쟁 중 강제납북자와 그 가족에 대한 보상입법 부작위는 헌법소원 대상이 될 수 없다.|
5|①|01|O|헌법소원 심판청구 당시 권리보호이익이 있어도 심판 계속 중 기본권 침해가 종료되면 원칙적으로 권리보호이익이 없다.|
5|②|01|O|한자 성의 한글표기에 두음법칙을 일률 적용하던 예규가 합리적 예외를 인정하도록 개정되면 그 예규의 위헌확인을 구할 권리보호이익은 상실된다.|
5|③|01|O|헌법소원이 주관적 권리구제에는 도움이 되지 않아도 침해 반복위험이 있으면 예외적 심판이익이 인정될 수 있다.|
5|③|02|O|분쟁 해결이 헌법질서 수호·유지를 위해 긴요하고 헌법적 해명의 중대한 의미가 있으면 예외적 심판이익이 인정될 수 있다.|
5|④|01|X|방위사업청의 행정5급 일반임기제 경력경쟁채용시험에서 변호사 자격등록을 요구한 공고에 대한 헌법소원은 예외적 심판이익을 인정할 수 있다.|예외적 심판이익을 인정하기 어렵다고 본 부분
5|⑤|01|O|구치소장이 변호인접견실에 CCTV를 설치하여 접견장면을 관찰하는 행위는 반복 위험이 있다.|
5|⑤|02|O|변호인접견실 CCTV 관찰행위는 미결수용자의 기본적 처우와 관련되어 헌법적 해명의 중대성이 인정될 수 있다.|
6|①|01|X|주택법상 주택건설사업에 가구수 증가와 무관하게 전체 가구수 기준으로 학교용지부담금을 부과하는 규정은 평등원칙에 위반되지 않는다.|학교용지부담금 부과 규정이 평등원칙에 위반된다고 본 부분
6|②|01|O|국가유공자 유족 중 보상받을 자녀의 순위에서 협의 지정자나 주부양자가 없으면 나이가 많은 자녀를 선순위로 삼는 규정은 평등원칙에 위반된다.|
6|③|01|O|성폭력범죄 피해자가 국민참여재판을 원하지 않는 경우 법원이 국민참여재판 배제결정을 할 수 있도록 한 규정은 합리적 근거가 있다.|
6|③|02|O|성폭력범죄 피해자의 의사에 따른 국민참여재판 배제결정 규정은 평등원칙에 위반되지 않는다.|
6|④|01|O|일정한 법무법인에 변리사 업무 수행을 허용한 변호사법 규정은 평등원칙에 위반되지 않는다.|
6|⑤|01|O|일정한 친족 간 권리행사방해죄를 친고죄로 정한 형법 규정은 합리적 이유가 있어 평등원칙에 위반되지 않는다.|
7|①|01|X|안경사의 전자상거래 등 방법에 의한 콘택트렌즈 판매를 금지한 규정은 안경사의 직업수행의 자유를 침해하지 않는다.|콘택트렌즈 전자상거래 금지가 직업수행의 자유를 침해한다고 본 부분
7|②|01|O|의료인의 의료기관 중복개설을 금지하고 처벌하는 의료법 규정은 의료인의 직업수행의 자유를 침해하지 않는다.|
7|③|01|O|직업의 자유는 생활의 기본 수요와 개성 신장을 위한 주관적 공권의 성격을 가진다.|
7|③|02|O|직업의 자유는 사회적 시장경제질서라는 객관적 법질서의 구성요소이기도 하다.|
7|④|01|O|학원법 위반으로 벌금형을 선고받은 뒤 1년이 지나지 않은 사람에게 학원 설립·운영 등록을 제한하는 규정은 직업선택의 자유를 침해하지 않는다.|
7|⑤|01|O|법인 임원이 학원법 위반으로 벌금형을 선고받은 경우 법인의 학원 설립·운영 등록이 효력을 잃도록 한 규정은 학원법인의 직업수행의 자유를 침해한다.|
8|①|01|O|헌법재판소법 제68조 제1항의 공권력은 국가기관 또는 공공단체 등의 고권적 작용을 말한다.|
8|①|02|O|헌법소원의 대상인 공권력 행사는 국민의 법률관계나 법적 지위를 불리하게 변화시키는 것이어야 한다.|
8|②|01|O|권력적 사실행위 해당 여부는 행정주체와 상대방의 관계, 상대방의 관여 정도와 태도, 행위 목적과 경위, 명령·강제수단 가능성 등을 종합하여 판단한다.|
8|③|01|O|행정권력의 부작위가 헌법소원 대상인 공권력 불행사가 되려면 헌법에서 유래하는 구체적 작위의무가 인정되어야 한다.|
8|③|02|O|공권력 불행사에 대한 헌법소원은 기본권 주체가 행정행위나 공권력 행사를 청구할 수 있는데도 공권력 주체가 의무를 해태한 경우에 가능하다.|
8|④|01|O|개성공단 전면중단조치는 개성공단 투자기업들에 대한 일방적 권력적 사실행위로서 공권력 행사에 해당한다.|
8|⑤|01|X|검찰수사관이 피의자신문 참여 변호인에게 변호인참여신청서 작성을 요구한 행위는 권력적 사실행위에 해당하지 않아 헌법소원 대상이 되지 않는다.|변호인참여신청서 작성 요구를 헌법소원 대상인 권력적 사실행위로 본 부분
9|①|01|X|강도상해죄 또는 강도치상죄의 법정형 하한을 징역 7년으로 정한 형법 규정은 책임과 형벌 간 비례원칙에 위반되지 않는다.|강도상해·강도치상 법정형 하한이 비례원칙에 위반된다고 본 부분
9|②|01|X|야간주거침입절도 미수범이 준강제추행죄를 범한 경우 무기징역 또는 7년 이상 징역에 처하는 규정은 책임과 형벌 사이의 비례원칙에 위반되지 않는다.|야간주거침입절도 미수범의 준강제추행 가중처벌이 비례원칙에 위반된다고 본 부분
9|③|01|X|보안관찰처분대상자가 출소 후 신고한 거주예정지 등 정보 변동을 7일 이내 신고하도록 하고 위반 시 처벌하는 규정은 사생활의 비밀과 자유 및 개인정보자기결정권을 침해한다.|보안관찰 신고의무·처벌 규정이 기본권을 침해하지 않는다고 본 부분
9|④|01|X|대형트롤어업 허가 시 동경 128도 이동수역 조업금지 조건을 붙이도록 한 규정은 직업수행의 자유를 침해하지 않는다.|대형트롤어업 조업금지 조건이 직업수행의 자유를 침해한다고 본 부분
9|⑤|01|O|상속개시 후 인지 또는 재판확정으로 공동상속인이 된 사람의 상속분가액지급청구권에 상속회복청구권의 10년 제척기간을 적용하는 민법 규정은 재산권을 침해한다.|
9|⑤|02|O|상속분가액지급청구권에 상속회복청구권의 10년 제척기간을 적용하는 민법 규정은 재판청구권을 침해한다.|
10|①|01|O|상하 위계가 있는 기본권이 충돌하면 상위기본권 우선 원칙에 따라 하위기본권이 제한될 수 있다.|
10|①|02|O|흡연권은 혐연권을 침해하지 않는 범위에서 인정된다.|
10|②|01|O|노동조합의 적극적 단결권은 근로자 개인의 단결하지 않을 자유보다 중시될 수 있다.|
10|②|02|O|노동조합에 조직강제권을 부여하는 것만으로 곧바로 근로자의 단결하지 않을 자유의 본질을 침해한다고 볼 수 없다.|
10|③|01|X|학생의 소극적 종교행위의 자유와 소극적 신앙고백의 자유가 학교법인의 종교교육의 자유보다 당연히 상위기본권이라고 볼 수는 없고, 구체적 사안에서 조화롭게 형량하여야 한다.|학생의 소극적 종교 자유를 학교법인의 종교교육 자유보다 상위기본권으로 단정한 부분
10|④|01|O|교원의 수업권은 학생의 학습권 실현을 위하여 인정되는 교육상 직무권한이다.|
10|④|02|O|학생의 학습권은 교원의 수업권에 대하여 우월한 지위에 있다.|
10|⑤|01|O|명예보호와 표현의 자유가 충돌할 때에는 표현의 자유로 얻는 가치와 인격권 보호로 달성되는 가치를 비교형량하여야 한다.|
10|⑤|02|O|명예보호와 표현의 자유가 충돌할 때 규제의 폭과 방법은 구체적 사안의 법익형량으로 정하여야 한다.|
11|①|01|O|보통선거원칙은 선거권자의 능력, 재산, 사회적 지위 등 실질적 요소를 배제한다.|
11|①|02|O|보통선거원칙에 반하는 선거권 제한 입법은 헌법 제37조 제2항의 한계를 엄격히 준수하여야 한다.|
11|②|01|O|평등선거원칙은 1인 1표 원칙과 투표가치 평등을 포함한다.|
11|②|02|O|평등선거원칙은 특정 집단 의사를 정치과정에서 배제하는 게리맨더링을 부정한다.|
11|③|01|X|신체장애로 직접 기표할 수 없는 선거인에게 가족이 아닌 투표보조인 2인을 동반하도록 한 공직선거법 규정은 선거권과 비밀선거원칙을 침해하지 않는다.|가족 아닌 투표보조인 2인 동반 요건이 과잉금지원칙에 위반된다고 본 부분
11|④|01|O|자유선거원칙은 헌법 명문에는 없지만 민주국가 선거제도에 내재하는 법원리이다.|
11|④|02|O|자유선거원칙은 국민주권원리, 의회민주주의원리 및 참정권 규정에서 근거를 찾을 수 있다.|
11|⑤|01|O|일부 선거구 획정에 위헌성이 있어도 선거구구역표가 불가분적 일체를 이루면 선거구구역표 전부에 대하여 위헌선언을 하여야 한다.|
12|①|01|O|헌법 제39조 제1항의 국방의 의무는 외부 적대세력의 직간접 침략에 대응하기 위한 의무이다.|
12|①|02|O|국방의 의무는 국가의 독립 유지와 영토 보전을 위한 의무이다.|
12|②|01|O|병역법에 따른 군복무는 국민이 부담하는 헌법상 의무의 이행이다.|
12|②|02|O|병역법에 따른 군복무는 국가나 공익을 위한 특별한 희생이라고 볼 수 없다.|
12|③|01|O|실역에 복무 중인 예비역에게 현역군인에 준하여 군형법을 적용하는 것은 국방의 의무에 근거한 병역의무 이행 확보 수단이다.|
12|④|01|X|헌법 제39조 제2항과 예비군 실비변상 규정만으로 교육훈련 소집 예비군에게 병력동원훈련 예비군과 같은 보상을 해야 한다고 볼 수 없다.|교육훈련 소집 예비군에게도 병력동원훈련에 준하는 보상이 이루어져야 한다고 본 부분
12|⑤|01|O|병역의무 자체를 이행하면서 받는 불이익은 헌법 제39조 제2항의 병역의무 이행으로 인한 불이익한 처우 금지와 구별된다.|
13|①|01|O|헌법상 재산권은 재산가치 있는 모든 사법상 권리와 공법상 권리를 포함한다.|
13|②|01|O|기초생활보장수급권은 공공부조로서 사회정책적 목적에서 주어지는 권리이다.|
13|②|02|O|기초생활보장수급권은 개인의 노력과 금전적 기여로 취득되는 재산권 보호대상으로 보기 어렵다.|
13|③|01|O|재산권 제한의 허용 정도는 재산권 객체의 사회적 기능과 사회적 연관성에 따라 달라진다.|
13|③|02|O|재산권 객체가 사회적 연관성과 사회적 기능을 강하게 가질수록 입법자에 의한 광범위한 제한이 허용된다.|
13|④|01|O|토지는 국민경제와 사회적 기능의 특수성 때문에 다른 재산권보다 공동체 이익을 더 강하게 관철할 필요가 있다.|
13|⑤|01|X|진정소급입법에 의한 재산권 제한도 국민이 소급입법을 예상할 수 있었거나 중대한 공익상 요청이 있는 예외적 경우에는 허용될 수 있다.|진정소급입법에 의한 재산권 제한은 예상 가능성이 있어도 허용되지 않는다고 본 부분
14|①|01|O|장애인의 접근권은 장애인에게 인간의 존엄과 가치 및 행복추구권을 동등하게 보장하기 위한 권리이다.|
14|①|02|O|장애인의 접근권은 사회적 약자인 장애인이 인간다운 생활을 하는 데 필수적인 전제가 되는 기본권적 지위를 가진다.|
14|②|01|O|장애인의 접근권이 특정 시설과 설비 설치를 국가나 사인에게 곧바로 요구할 수 있는 권리를 당연히 포함하는 것은 아니다.|
14|②|02|X|장애인의 접근권의 구체적 내용은 법률로 형성될 필요가 있다.|접근권 구체화 법률이 필요하지 않다고 본 부분
14|③|01|O|국가는 재정능력과 사회·경제적 발전수준 등을 고려하여 장애인의 접근권이 적절히 보장되도록 필요한 조치를 취할 의무가 있다.|
14|④|01|O|국회가 법률로 행정청에 특정 사항을 위임했는데 행정청이 정당한 이유 없이 이행하지 않으면 권력분립원칙과 법치행정원칙에 위배된다.|
14|⑤|01|O|행정청이 법률에서 대통령령으로 정하도록 위임받은 사항을 전혀 입법하지 않으면 위법·위헌이 될 수 있다.|
14|⑤|02|O|행정청이 법률에서 위임한 사항을 불충분하게 규정하여 행정입법의무를 제대로 이행하지 않은 경우에도 위법·위헌이 될 수 있다.|
15|①|01|O|정당은 권한쟁의심판에서 국가기관에 해당한다고 볼 수 없다.|
15|①|02|X|정당은 사적 결사와 국회 교섭단체의 이중적 지위를 이유로 권한쟁의심판 당사자능력이 인정되는 것은 아니다.|정당의 권한쟁의심판 당사자능력을 인정한 부분
15|②|01|O|정당의 목적이나 활동이 민주적 기본질서에 위배될 때 정부는 국무회의 심의를 거쳐 헌법재판소에 정당해산심판을 청구할 수 있다.|
15|③|01|O|복수당적 허용은 정당 간 위법·부당한 간섭이나 정체성 약화를 초래할 우려가 있다.|
15|③|02|O|복수당적 허용은 정당의 헌법적 과제 수행을 저해할 우려가 있다.|
15|④|01|O|정당등록제도는 정치적 결사가 정당법상 정당임을 법적으로 확인하는 제도이므로 정당의 자유에 대한 과도한 제한으로 보기 어렵다.|
15|⑤|01|O|헌법재판소는 정당해산심판 청구를 받으면 직권 또는 청구인 신청으로 종국결정 선고 때까지 피청구인 정당의 활동을 정지하는 결정을 할 수 있다.|
16|①|01|X|체포 또는 구금된 국회의원의 석방요구 발의는 재적의원 4분의 1 이상의 연서로 이유를 첨부한 요구서를 국회의장에게 제출하여야 한다.|재적의원 과반수의 연서가 필요하다고 본 부분
16|②|01|O|국회의장은 국회를 대표하는 헌법상 국가기관이다.|
16|②|02|O|국회의장은 국회를 대표하고 의사를 정리하며 질서를 유지하고 국회 사무를 감독한다.|
16|③|01|O|국회의원의 발의 의안 철회동의 여부에 관한 심의·표결권한은 일신전속적 권한이다.|
16|③|02|O|국회의원의 심의·표결권 침해 여부가 문제된 권한쟁의심판절차는 의원직 상실 후 수계될 수 없다.|
16|④|01|O|국회법상 국회의장은 위원회에 출석하여 발언할 수 있으나 표결에는 참가할 수 없다.|
16|⑤|01|O|무소속 국회의원이 교섭단체 소속 국회의원과 동등하게 대우받을 권리는 헌법상 일반 국민에게 보장된 기본권이 아니다.|
16|⑤|02|O|국회의원은 무소속 국회의원의 교섭단체 동등대우권 침해를 이유로 헌법재판소법 제68조 제1항 헌법소원심판을 청구할 수 없다.|
17|①|01|O|등록 출판사의 음란 또는 저속한 간행물 출판을 이유로 등록을 취소할 수 있게 한 규정은 언론·출판의 자유를 중심으로 위헌 여부를 판단한다.|
17|②|01|X|의료인이 아닌 사람의 문신시술업을 금지·처벌하는 규정은 예술의 자유가 아니라 직업선택의 자유를 중심으로 위헌 여부를 판단한다.|문신시술업 금지·처벌 규정을 예술의 자유 중심으로 판단한다고 본 부분
17|③|01|O|법무법인 구성원 지분을 압류한 채권자가 영업연도 말에 그 구성원을 퇴사시킬 수 있게 한 규정은 재산권을 중심으로 위헌 여부를 판단한다.|
17|④|01|O|여자대학 약학대학 정원을 동결한 대학 보건·의료계열 학생정원조정계획 부분은 직업선택의 자유를 중심으로 위헌 여부를 판단한다.|
17|⑤|01|O|변호사 징계결정정보를 인터넷 홈페이지에 공개하도록 한 규정은 일반적 인격권을 중심으로 위헌 여부를 판단한다.|
18|①|01|O|주민조례발안법상 주민은 공공시설 설치 반대에 대해서는 조례 제정·개정·폐지를 청구할 수 없다.|
18|①|02|O|주민조례발안법상 주민은 행정기구 설치·변경에 대해서는 조례 제정·개정·폐지를 청구할 수 없다.|
18|②|01|X|조례안 재의결무효확인소송의 심리대상은 지방의회에 재의를 요구할 당시 이의사항으로 지적되어 재의결에서 심의대상이 된 것에 국한된다.|재의결무효확인소송 심리대상이 재의요구 당시 이의사항에 국한되지 않는다고 본 부분
18|③|01|O|지방자치단체는 조례를 위반한 행위에 대하여 조례로 1천만 원 이하의 과태료를 정할 수 있다.|
18|④|01|O|지방자치단체장은 이송된 조례안에 이의가 있으면 재의요구를 할 수 있다.|
18|④|02|O|지방자치단체장은 조례안 일부에 대해서만 재의요구를 할 수 없다.|
18|⑤|01|O|교육감은 주민의 재정적 부담이나 의무 부과에 관한 교육·학예 조례안을 시·도의회에 제출하려면 미리 시·도지사와 협의하여야 한다.|
19|①|01|O|국무위원이 국무회의에 출석하지 못해 차관이 대리 출석한 경우 차관은 관계 의안에 관하여 발언할 수 있다.|
19|①|02|X|국무위원을 대리하여 국무회의에 출석한 차관은 표결에 참가할 수 없다.|대리출석한 차관이 표결에도 참가할 수 있다고 본 부분
19|②|01|O|서훈 추천이 있으면 행정안전부장관은 서훈 의안을 국무회의에 제출하여야 한다.|
19|②|02|O|대통령은 서훈 의안에 대해 국무회의 심의를 거쳐 서훈대상자를 결정한다.|
19|③|01|O|국무회의는 구성원 과반수 출석으로 개의한다.|
19|③|02|O|국무회의는 출석구성원 3분의 2 이상의 찬성으로 의결한다.|
19|④|01|O|국가안전보장회의는 국가안전보장 관련 대외정책·군사정책과 국내정책 수립에 관하여 국무회의 심의 전 대통령 자문에 응하기 위한 기관이다.|
19|⑤|01|O|국무회의 제출 의안은 긴급한 의안이 아닌 한 차관회의 심의를 먼저 거쳐야 한다.|
19|⑤|02|O|국무회의 의안의 긴급성 판단에는 원칙적으로 정부의 재량이 있다.|
20|①|01|X|국회의 임시회는 대통령 또는 국회 재적의원 4분의 1 이상의 요구에 따라 집회된다.|임시회 집회 요구 정족수를 재적의원 5분의 1 이상으로 본 부분
20|②|01|X|국회의 정기회 회기는 100일을, 임시회 회기는 30일을 초과할 수 없다.|임시회 회기를 50일로 본 부분
20|③|01|X|특정한 위원회 회의를 일률적으로 비공개하도록 정하는 법률은 헌법 제50조 제1항 단서의 회의별 비공개 요건을 대신할 수 없다.|더 엄격한 본회의 의결을 거친 법률 형식이면 위원회 회의를 비공개할 수 있다고 본 부분
20|④|01|X|대통령이 재의를 요구한 법률안은 국회가 재적의원 과반수 출석과 출석의원 3분의 2 이상의 찬성으로 전과 같이 의결하면 법률로 확정된다.|재적의원 3분의 2 이상 찬성이 필요하다고 본 부분
20|⑤|01|O|국회에서 선출하는 헌법재판소 재판관 후보자와 중앙선거관리위원회 위원 후보자는 인사청문특별위원회에서 인사청문회를 실시한다.|
20|⑤|02|O|대통령이 임명하거나 대법원장이 지명하는 헌법재판소 재판관 후보자와 중앙선거관리위원회 위원 후보자는 소관 상임위원회에서 인사청문회를 실시한다.|
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


def load_queue() -> dict[str, object]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def load_source() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


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
                    "atomId": f"bupmusa-2025-constitution-q{key[0]:02d}-{LABEL_CODE[key[1]]}-{row['atomIndex']}",
                    "sourceUnitId": queue_item["unitId"],
                    "sourceAtomIndex": row["atomIndex"],
                    "sourceFamily": "법무사시험",
                    "source": queue_item["source"],
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
    cuts = [
        (0.04, "S"),
        (0.11, "A+"),
        (0.23, "A"),
        (0.40, "B+"),
        (0.60, "B"),
        (0.77, "C+"),
        (0.89, "C"),
        (0.96, "D+"),
        (1.00, "D"),
    ]
    n = len(sorted_items)
    for rank, item in enumerate(sorted_items, start=1):
        p = rank / n
        item["grade"] = next(grade for cut, grade in cuts if p <= cut)
        item["rank"] = rank


def build_integrated(atoms: list[dict[str, object]]) -> dict[str, object]:
    buckets: dict[tuple[str, str], dict[str, object]] = {}
    for atom in atoms:
        key = (str(atom["a"]), normalize_key(str(atom["rep"])))
        source_label = f"{YEAR} 법무사 {ROUND}회 헌법 {atom['no']}번 {atom['unitLabel']}"
        source = {
            "family": "법무사시험",
            "s": 1.0,
            "year": YEAR,
            "round": ROUND,
            "subject": SUBJECT_NAME,
            "source": source_label,
            "sourceId": atom["atomId"],
            "sourceUnitId": atom["sourceUnitId"],
            "sourceVerdict": atom["sourceVerdict"],
            "sourceTrap": atom["sourceTrap"],
            "sourceStatement": atom["sourceStatement"],
        }
        if key not in buckets:
            buckets[key] = {
                "primary": "법무사시험",
                "sourceFamilies": ["법무사시험"],
                "subject": SUBJECT_NAME,
                "topic": TOPICS[int(atom["no"])],
                "rep": atom["rep"],
                "a": atom["a"],
                "why": atom["why"],
                "basisType": atom["basisType"],
                "basisRef": atom["basisRef"],
                "sources": [source],
                "refs": [source_label],
                "sourceIds": [atom["atomId"]],
                "sourceAtomCount": 1,
                "quality": {
                    "statementType": "declarative",
                    "displayable": True,
                    "normalizers": [],
                    "changed": False,
                },
                "verification": {
                    "status": "needs-legal-review",
                    "lawAsOf": today(),
                    "legalVerifiedAt": None,
                    "statuteCitationStatus": "pending",
                },
            }
        else:
            bucket = buckets[key]
            bucket["sources"].append(source)
            bucket["refs"].append(source_label)
            bucket["sourceIds"].append(atom["atomId"])
            bucket["sourceAtomCount"] = int(bucket["sourceAtomCount"]) + 1

    items = list(buckets.values())
    for index, item in enumerate(items, start=1):
        item["freq"] = len(item["sources"])
        item["weightedSourceSum"] = round(
            sum(float(src["s"]) * (0.5 ** (max(0.0, 2026.46 - year_to_exam_date(int(src["year"]))) / 4.0)) for src in item["sources"]),
            6,
        )
        item["weight"] = weight_for_sources(item["sources"])
        item["id"] = f"bupmusa-constitution-integrated-{index:05d}"
    grade_items(items)
    items.sort(key=lambda item: (int(item["rank"]), str(item["id"])))

    return {
        "title": "법무사_헌법 통합 atom",
        "subject": SUBJECT_NAME,
        "schema": "bupmusa/constitution-integrated-atom/v1",
        "version": "bupmusa_constitution_v001_2025_seed",
        "builtAt": today(),
        "sourceFiles": {
            "2025": str(OUT_PATH),
        },
        "weighting": {
            "H": 4.0,
            "today": 2026.46,
            "formula": "W=ln(1+Σ s·0.5^(age/H)); 법무사시험 s=1.0",
            "gradeScope": "법무사 헌법 통합 atom 내 상대평가",
        },
        "integration": {
            "method": "exact-normalized-text",
            "scope": "법무사시험 헌법 2025 seed",
        },
        "stats": {
            "sourceYears": [YEAR],
            "inputAtoms": len(atoms),
            "items": len(items),
            "duplicatesMerged": len(atoms) - len(items),
            "gradeCounts": dict(Counter(item["grade"] for item in items)),
        },
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
    if doc["stats"]["inputAtoms"] < len(items):
        raise ValueError("integrated stats mismatch")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_index(atom_count: int) -> None:
    if not SUBJECT_INDEX_PATH.exists():
        return
    index = json.loads(SUBJECT_INDEX_PATH.read_text(encoding="utf-8"))
    index["updatedAt"] = today()
    subject = index.setdefault("subjects", {}).setdefault(SUBJECT_NAME, {"subject": SUBJECT_NAME})
    subject["source"] = str(SOURCE_PATH)
    subject["atomQueue"] = str(QUEUE_PATH)
    subject["completedAtoms"] = str(OUT_PATH)
    subject["completedAtomCount"] = atom_count
    subject["completedAtomsUpdatedAt"] = today()
    write_json(SUBJECT_INDEX_PATH, index)


def build_completed_doc(queue: dict[str, object], atoms: list[dict[str, object]]) -> dict[str, object]:
    source = load_source()
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
    queue = load_queue()
    atoms = build_atoms(queue)
    validate_atoms(atoms, queue)
    completed = build_completed_doc(queue, atoms)
    integrated = build_integrated(atoms)
    validate_integrated(integrated)
    write_json(OUT_PATH, completed)
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
