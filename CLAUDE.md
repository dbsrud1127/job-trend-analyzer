# 프로젝트: job-trend-analyzer (IT 채용공고 기반 기술스택 격차 분석)

> 작업 시작 전 반드시 루트의 STATUS.md 를 먼저 읽고, "남은 일"을 위에서부터 하나씩 진행한다.

## 1. 목적
- 개발 학원 개인 결과물, 비전공 초보자의 첫 포트폴리오 (v1: 2026-09-23 ~ 09-28, 이후 v2)
- 흐름: 외부 데이터 수집 → 정제/분류 → DB 저장 → 통계/비교 → AI 분석 → 결과 제공
  (수집~저장은 자동, 이후는 사용자 요청 시)
- 최우선 목표: 끝까지 돌아가고, "왜 이렇게 만들었는지" 내가 면접에서 직접 설명할 수 있을 것

## 2. 기술 스택 (v1 확정)
- 언어: Python 3.11 통일 (루트 .venv, 루트 requirements.txt 하나)
- 웹: FastAPI + Jinja2 템플릿 (React는 v2)
- DB: Supabase PostgreSQL (Seoul). psycopg로 SQL 직접 작성, ORM 사용 안 함
  - 접속은 반드시 Session pooler (Direct는 IPv6 전용이라 Render/Actions에서 실패)
- 수집: Python 스크립트 + GitHub Actions cron (하루 1회)
- 데이터: Remotive 공개 API + RemoteOK 공개 API (Remotive는 category 필터가 동작하지 않아 파라미터 없이 호출) 사람인 승인 대기, 공공데이터 백업
- AI: Claude API, 결과는 ai_analysis 테이블에 캐시 (같은 입력이면 재호출 안 함)
- 배포: Render (Docker 없이)
- 제외: Kafka, Kubernetes, MSA, Redis, Agent, n8n, Docker, RAG
  → 제안하고 싶으면 "향후 확장 아이디어"로만 언급, 구현 제안 금지

## 3. 폴더 구조
```
db/
  schema.sql          # 테이블/VIEW/RLS (확정 ERD)
  seed_tech.sql       # 기술 사전 초기 데이터
  001_add_remoteok_source.sql  # source에 'remoteok' 추가
collector/            # 수집기 (실행: 루트에서 python collector/main.py)
  main.py             # 전체 흐름 실행
  remotive.py         # Remotive API 호출
  remoteok.py         # RemoteOK API 호출
  transform.py        # 정제/직무 분류/기술 추출
  db.py               # DB 저장
app/                  # FastAPI
.github/workflows/collect.yml
.claude/rules/        # backend.md, frontend.md, general.md
requirements.txt
STATUS.md             # 현재 진행 상황
CLAUDE.md
README.md
```

## 4. AI 사용 원칙 (중요)
AI가 전부 만들어서 내가 이해하지 못하는 상태가 되는 것을 원하지 않는다. 순서를 반드시 지킨다.

1. 분석: 요구사항/기존 코드를 분석만 하고 바로 코드 작성하지 않는다.
2. 계획: 만들/수정할 파일과 구조를 먼저 설명한다. 내가 확인한다.
3. 승인: 내가 승인한 범위만 구현한다. 범위를 넘지 않는다.
4. 구현: 파일 하나씩 작성 → 실행 확인 → 다음 파일.
5. 설명: 만든 파일 / 데이터 흐름 / 왜 이렇게 했는지(대안) / 핵심 코드.
6. 테스트: 실행 명령어와 "성공하면 이렇게 보인다"를 알려주고 같이 확인한다.
7. 오류: 원인을 먼저 설명하고 수정한다.
8. 기록(요청할 때만): DEVLOG.md(3~5줄), TROUBLESHOOTING.md(문제 → 원인 → 해결) 블록을 제공한다.

- AI = 구현 가속 / 반복 작업 / 디버깅 보조
- 나 = 요구사항·구조 결정 / 검토 / 테스트 / 최종 설명 책임자

## 5. 테스트 원칙
- 핵심 흐름(수집 → 저장 → 조회 → AI 분석)은 반드시 직접 한 번씩 실행해 결과를 확인한다.
- 자동화 테스트 코드는 v1 필수 아님.
