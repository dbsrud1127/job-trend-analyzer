# STATUS (마지막 수정: 2026-09-26)

## 완료
- ERD 확정, Supabase 생성, schema.sql 실행, check_db.py 연결 성공 (테이블 10개)
- 수집기 계획 점검 완료, v2 범위 확정

## 지금 할 일 (승인된 계획)
0. GitHub 레포 생성 + 첫 커밋 (.env 안 올라갔는지 확인)
1. db/seed_tech.sql 작성·실행 → tech_stack 55개 확인
2. 루트 requirements.txt (psycopg[binary], python-dotenv, requests, beautifulsoup4)
3. remotive.py → 4. transform.py → 5. db.py → 6. main.py 전체 실행
7. 미등록 태그 상위 20개로 별칭 보강
8. collect.yml (GitHub Actions)

## 남은 일정
- 09-27: FastAPI 통계, 익명 프로필 + 내 스택 → 격차 계산 → Claude 분석, Jinja2 화면
- 09-28 오전: Render 배포 / 오후: 붙여넣기 공고 추출, README

## 막힌 것 / 메모
- (없음)
