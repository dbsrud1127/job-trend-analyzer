-- =====================================================================
-- 001 : job_posting.source 허용 값에 'remoteok' 추가
-- 실행 위치 : Supabase > SQL Editor > 붙여넣기 > Run
-- =====================================================================
BEGIN;

-- 기존 규칙 삭제 (CREATE TABLE 때 PostgreSQL이 자동으로 붙인 이름: 테이블명_컬럼명_check)
ALTER TABLE job_posting DROP CONSTRAINT job_posting_source_check;

-- 'remoteok' 를 넣어서 같은 이름으로 다시 만들기
ALTER TABLE job_posting ADD CONSTRAINT job_posting_source_check
    CHECK (source IN ('remotive','remoteok','saramin','public_data','user_input'));

COMMIT;