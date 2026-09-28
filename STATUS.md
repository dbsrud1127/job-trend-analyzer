# STATUS (마지막 수정: 2026-09-28)

## 완료
- ERD 확정, Supabase 생성, schema.sql 실행, check_db.py 연결 성공 (테이블 10개)
- GitHub 레포 생성 + 첫 커밋 (.env 제외 확인), CLAUDE.md / .claude/rules FastAPI 기준으로 갱신
- db/seed_tech.sql 실행: tech_stack 55개, tech_alias 106개
- requirements.txt (영어만 사용, 한글 주석 시 Windows pip cp949 에러)
- remotive.py: 공개 API가 카테고리 필터 무시 + 고정 18개만 반환 → category 파라미터 제거
- db/001_add_remoteok_source.sql 실행: source에 'remoteok' 추가 (schema.sql도 반영)
- remoteok.py: 최신 약 99개, 첫 원소(약관)는 제외
- 두 수집 파일에 to_common() → 공통 모양으로 변환
- transform.py: 글자깨짐 복구, HTML 제거, 태그 신뢰 판단, 기술 추출, 직무 분류
  - A: 본문 기술 10개 초과면 템플릿으로 보고 버림
  - B: 제목이 모호하면(developer/software engineer/programmer) 요구 기술로 직무 판단
- 7단계 확인 결과: 사전에 없는 태그 상위 20개가 전부 비기술 → 별칭 보강 불필요
- transform.py A·B 확인 완료. go 22개 원인 = RemoteOK가 무관한 공고에 golang 태그 자동 부착
    → RemoteOK는 태그 전부 신뢰 X (제목+본문으로 추출). go 22 → 6
- etc 중 개발 공고 일부 누락은 v1에서 수용 (대부분 기술 없음, 통계 비율 영향 작음)
- db.py: get_connection, load_alias, save_posting(upsert + last_seen_at), save_posting_tech(지우고 다시), save_collect_log
- main.py: 출처별 수집→변환→저장, 출처별 commit, 실패 시 rollback + failed 로그, 실패 있으면 exit 1
- 실제 수집 1회 성공: remotive 18, remoteok 99, VIEW 통계 확인

## 남은 일 (마감: 09-28 23:00 / 09-26·27 컨디션 문제로 작업 못 함)
### 반드시 (이것까지 되면 "돌아가는 결과물")
1. collect.yml : GitHub Actions 하루 1회 수집, Secrets로 DB 정보 (Claude Code)
2. FastAPI 통계 : service 함수 + /api/stats + Jinja2 통계 화면 (공고 수 함께 표시, etc 제외, 0개 직무 안내)
3. 익명 프로필 + 내 스택 입력 → 격차 계산 (service 함수 + /api + 화면)
4. Render 배포 : 여기까지 되면 배포 링크 확보

### 시간 남으면 (배포 후 순서대로)
5. Claude 분석 (ai_analysis 캐시)
6. README (Remotive·RemoteOK 출처 표기 + 원문 링크, 해외 데이터 한계 명시)

### 컷 라인 아래 (못 하면 v2로 이동)
7. 붙여넣기 공고 추출 (user_input)

## 막힌 것 / 메모
- Remotive 공개 API 권장 호출 하루 4회 이하. 테스트는 collector/sample_*.json 사용 (gitignore)
- 샘플 파일 사용 테스트: python collector/transform.py
- collector/inspect_sample.py 는 임시 확인용 (삭제 가능)
- 표본 작음 (frontend 3개 → 100%) → 화면에 공고 수 함께 표시, 직무 선택에서 etc 제외, 0개 직무 안내