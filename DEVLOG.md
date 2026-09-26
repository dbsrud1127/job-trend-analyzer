# DEVLOG

> 각 작업 세션이 끝날 때마다 아래 형식으로 추가한다.
> Claude Code에게 "오늘 세션 요약해서 DEVLOG.md에 추가해줘"라고 시키면 자동으로 채워준다.

---
## 2026-09-23 (Day1) 기획 확정 + 데이터 출처 결정

### [블록 1] 도메인/방향 재정의
- 문제: "기술스택 트렌드 분석 서비스"라는 제안이 원래 의도와 어긋남
- 정리: 트렌드 = 서비스 주제(A)가 아니라 결과물에 담긴 실무 기술(B)이 목표
- 결정: 채용공고 도메인 유지, "구직자 맞춤형"으로 표현 변경
  - 직무별 요구 스택 분석 + 내 스택 비교 + AI 학습 가이드
  - 채용공고 도메인이 수집/정제/스케줄링/검색/AI 연동을 자연스럽게 보여줄 수 있어서 유지

### [블록 2] 데이터 출처 조사
- 수집 방식 3가지 비교: 공식 API / 파일 데이터 / 크롤링(약관 문제로 제외)
- SNS 구인글 자동 수집 제외 → 대신 "공고 텍스트 붙여넣기 → AI 추출" 기능으로 대체
- 결정:
  - Remotive 공개 API (키 불필요) → 개발용 메인
  - 사람인 API (승인 필요, 1일 500회) → 국내 데이터, 신청 진행
  - 공공데이터포털 파일 데이터 → 백업 샘플

### [블록 3] Remotive API 호출 테스트
- test.py로 공고 호출 성공, 응답 JSON 구조 확인
- 확인 필드: id, url, title, company_name, category, tags, job_type,
  publication_date, candidate_required_location, salary, description(HTML)

### [블록 4] 데이터 품질 분석 + ERD 초안
- 정제 규칙 초안 6개 작성 (아래 트러블슈팅 참고)
- ERD 초안: job_posting, tech_stack, tech_alias, posting_tech, ai_analysis, collect_log
- 미결정: 태그 과다 공고 처리 방식

### [블록 5] ERD 확정 및 스키마 생성
- 수집 파이프라인 중심 ERD에 구직자 도메인 추가: 익명 프로필(+로그인 연결용 auth_user_id), 내 스택, 격차 리포트(분석 기록), 학습 항목(진행 체크)
- 분석 기록은 당시 결과를 JSONB 스냅샷으로 저장해 스택 변경 후에도 과거 기록 유지
- 직무별 기술 통계는 VIEW로 계산 (user_input 공고, 오염 태그 제외)
- 수집 자동화는 무료 서버 슬립 문제로 GitHub Actions cron으로 분리 결정, collect_log에 실행 결과·에러 기록
- 전 테이블 RLS 활성화로 anon key 직접 접근 차단, 데이터 접근은 Spring API로 일원화



