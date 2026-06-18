# 법원직.com — 법원직 9급 기출 위키 (scourt9)

민법위키 하랑재(lawinus.org)와 **동일한 틀**의 자매 사이트. 조문 중심 위키 + CBT 게임센터.
상단 메뉴 = 시험과목 **헌법 · 민법 · 민사소송법 · 형법 · 형사소송법 · 상법 · 부동산등기법** + **CBT 게임센터 · 자유게시판 · 뉴스**, Google/Kakao 로그인.

## 데이터 (1차: 민사소송법)
- 통합본 **v022** (2007–2025 전 회차, 공식 확정정답표 검증완료)
- 조문 **310** · 통합 법리(atom) **1,730** · OX 문항 **2,382** (O 1,730 / X 함정 652) · ★빈출 217
- 조문 본문: 법제처 국가법령정보(시행 2025-07-12) — 최다 출제 조문 14건 우선 적재(`web/data/lawtext.js`)
- 나머지 6과목은 동일 틀로 확장 예정 (`subjects` 테이블에 row 추가)

## 설계 원칙
- **위키(조문 페이지)** = 조문 본문 + 출제 이력. (OX 지문/풀이는 노출하지 않음)
- **CBT 게임센터** = 모든 기출 OX(대표 O지문 + 함정 X지문)를 풀이. 과목/편/조문/빈출/오답노트 필터, O·X 채점, 콤보, 정답·근거·출처 공개.
- **Atom 제작 기준** = `docs/atom_원칙_v001.md`에 누적 관리.

## 구조
```
web/                 정적 프론트(민법위키와 동일 틀)
  index.html         셸(상단바·메뉴·로그인 모달)
  styles.css         보라 테마 #5b21a6
  app.js             해시 라우터 + 위키 + CBT + 게시판/뉴스
  config.js          Supabase URL/anonKey (비우면 데모 모드)
  data/
    civproc.js       민사소송법 데이터(window.CIVPROC) — build_data.py 산출
    civproc.json     동일 데이터(ETL 입력)
    lawtext.js       조문 본문(window.LAWTEXT)
supabase/
  migrations/0001_init.sql   스키마 + RLS + 가입 트리거
  seed.sql                   민소 v022 적재(INSERT) — etl_supabase.py 산출
scripts/
  build_data.py      통합본 v022 → web/data/civproc.js·json
  etl_supabase.py    civproc.json → supabase/seed.sql
```

## 로컬 실행 (데모 모드)
`web/index.html` 을 브라우저로 열면 됩니다. 로그인·게시판은 localStorage 데모로 동작.

## 배포
1. `web/` 를 정적 호스팅(Netlify/Vercel/Cloudflare Pages/Github Pages).
2. Supabase 프로젝트 생성 → SQL Editor에 `supabase/migrations/0001_init.sql` 실행 → `supabase/seed.sql` 실행.
3. Supabase Auth에서 Google·Kakao Provider 활성화.
4. `web/config.js` 에 프로젝트 URL/anonKey 입력. (index.html에 supabase-js CDN 추가 시 OAuth 활성화)
5. 도메인 `법원직.com` 연결.

## 데이터 갱신
새 회차 추가 후: `python3 scripts/build_data.py` → `python3 scripts/etl_supabase.py` → seed 재적용.
