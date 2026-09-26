# Backend Rules (Python: 수집기 + FastAPI)

## 공통
- DB 접근은 psycopg 로 SQL 을 직접 작성한다 (ORM 없음).
- SQL 에 값을 넣을 때는 반드시 %s 파라미터를 쓴다. f-string 으로 SQL 을 조립하지 않는다 (SQL 인젝션 방지).
- DB 접속 정보는 .env 의 DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD 를 python-dotenv 로 읽는다.
- 스키마 변경은 db/schema.sql 기준으로 먼저 설명하고, 승인 후 진행한다.

## 수집기 (collector/)
- 파일 역할을 섞지 않는다: remotive.py(호출) / transform.py(정제·분류·추출) / db.py(저장) / main.py(순서대로 실행)
- 직무는 제목 키워드로 재분류. 검사 순서: fullstack → devops → data → frontend → backend → etc
- 기술명 정규화: 공백 제거 + 소문자 → tech_alias 에 있는 것만 인정 (화이트리스트)
- tags_reliable=false 조건: 같은 태그 묶음이 5개 이상 공고에 반복, 또는 태그 15개 초과
- 추출: 태그 신뢰 O → tag + title / 신뢰 X → title + description. 우선순위 tag > title > description
- 본문 검색: 1~3단어 묶음을 공백 제거 후 사전과 비교. go, c, r 등 모호한 별칭은 본문 검색에서 제외
- 저장: (source, source_id) 기준 upsert, last_seen_at 갱신, posting_tech 는 지우고 다시 넣기
- 실행이 끝나면 collect_log 에 1줄 기록, 사전에 없는 태그 상위 20개를 콘솔에 출력

## FastAPI (app/)
- 계산 로직은 service 함수로 분리한다. 라우터 함수에는 로직을 넣지 않는다.
- /api/... (JSON) 와 Jinja2 페이지가 같은 service 함수를 호출한다 → v2 에서 React 로 바꿔도 service 는 그대로.
- 구조는 단순하게: 라우터 / service / db 접근 정도. 불필요한 계층 분리 금지.
- 에러는 HTTPException 으로 처리한다.
- API 문서는 FastAPI 자동 문서(/docs)를 사용한다.
- 통계는 VIEW v_role_tech_stat 을 조회한다. 전 테이블 RLS 이므로 브라우저 직접 접근 없이 FastAPI 를 통해서만 조회한다.
- Claude API 호출 전 입력의 SHA-256 으로 ai_analysis 를 먼저 조회하고, 있으면 재호출하지 않는다.
