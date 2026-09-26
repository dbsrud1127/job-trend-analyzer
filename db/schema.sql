-- =====================================================================
-- job-trend-analyzer : DB 스키마 (확정 ERD)
-- 실행 위치 : Supabase > SQL Editor > New query > 전체 붙여넣기 > Run
-- 레포 위치 권장 : db/schema.sql
-- BEGIN ~ COMMIT : 중간에 하나라도 실패하면 전부 취소 (반쯤 만들어진 상태 방지)
-- =====================================================================
BEGIN;

-- ---------------------------------------------------------------------
-- [정제] 기술 사전 : 모든 통계/비교의 기준이 되는 "정식 기술명"
-- ---------------------------------------------------------------------
CREATE TABLE tech_stack (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,              -- 정식명: 'typescript', 'react'
    category    VARCHAR(20)  NOT NULL
                CHECK (category IN ('language','framework','database','infra','tool','etc')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- 별칭 → 정식명 매핑 ('react js' → react, '자바' → java)
CREATE TABLE tech_alias (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alias          VARCHAR(100) NOT NULL UNIQUE,           -- 공백 제거 + 소문자화된 값
    tech_stack_id  BIGINT       NOT NULL REFERENCES tech_stack(id) ON DELETE CASCADE
);
CREATE INDEX idx_tech_alias_tech ON tech_alias (tech_stack_id);

-- ---------------------------------------------------------------------
-- [도메인] 구직자 프로필 : 익명으로 시작, 로그인하면 auth_user_id 연결
-- ---------------------------------------------------------------------
CREATE TABLE seeker_profile (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),  -- 브라우저 localStorage에 저장
    auth_user_id  UUID         UNIQUE
                  REFERENCES auth.users(id) ON DELETE SET NULL,       -- NULL = 익명 사용자
    nickname      VARCHAR(30),
    target_role   VARCHAR(20)
                  CHECK (target_role IN ('backend','frontend','fullstack','data','devops','etc')),
    career_level  VARCHAR(20)
                  CHECK (career_level IN ('new','junior','mid','senior')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- [수집] 채용공고
-- ---------------------------------------------------------------------
CREATE TABLE job_posting (
    id                    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source                VARCHAR(20)  NOT NULL
                          CHECK (source IN ('remotive','saramin','public_data','user_input')),
    source_id             VARCHAR(100),                    -- 원본 사이트의 공고 ID (user_input은 NULL)
    title                 VARCHAR(300) NOT NULL,
    company_name          VARCHAR(200),
    category_raw          VARCHAR(100),                    -- 원본 category (참고용, 신뢰 X)
    job_role              VARCHAR(20)  NOT NULL DEFAULT 'etc'
                          CHECK (job_role IN ('backend','frontend','fullstack','data','devops','etc')),
    job_type              VARCHAR(30),
    location              TEXT,
    salary_text           VARCHAR(100),
    description           TEXT,                            -- HTML 제거 후 텍스트
    raw_tags              JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 원본 태그 보관 (재처리용)
    tags_reliable         BOOLEAN      NOT NULL DEFAULT true,         -- 태그 과다 공고면 false
    url                   TEXT,
    submitted_profile_id  UUID         REFERENCES seeker_profile(id) ON DELETE SET NULL,
    published_at          TIMESTAMPTZ,
    collected_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_seen_at          TIMESTAMPTZ,                     -- (선택) 마지막으로 수집에서 확인된 시각
    CONSTRAINT uq_job_posting_source UNIQUE (source, source_id)       -- 중복 수집 방지
);
CREATE INDEX idx_job_posting_role_published ON job_posting (job_role, published_at DESC);
CREATE INDEX idx_job_posting_published      ON job_posting (published_at DESC);
CREATE INDEX idx_job_posting_submitter      ON job_posting (submitted_profile_id)
    WHERE submitted_profile_id IS NOT NULL;

-- 공고 ↔ 기술 (N:M)
CREATE TABLE posting_tech (
    posting_id      BIGINT      NOT NULL REFERENCES job_posting(id) ON DELETE CASCADE,
    tech_stack_id   BIGINT      NOT NULL REFERENCES tech_stack(id)  ON DELETE CASCADE,
    extracted_from  VARCHAR(20) NOT NULL
                    CHECK (extracted_from IN ('tag','title','description','ai')),
    PRIMARY KEY (posting_id, tech_stack_id)
);
CREATE INDEX idx_posting_tech_tech ON posting_tech (tech_stack_id);

-- 자동 수집 실행 기록 (GitHub Actions가 돌 때마다 1줄)
CREATE TABLE collect_log (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source          VARCHAR(20) NOT NULL,
    fetched_count   INT         NOT NULL DEFAULT 0 CHECK (fetched_count  >= 0),
    inserted_count  INT         NOT NULL DEFAULT 0 CHECK (inserted_count >= 0),
    status          VARCHAR(20) NOT NULL CHECK (status IN ('success','partial','failed')),
    error_message   TEXT,
    run_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_collect_log_source_run ON collect_log (source, run_at DESC);

-- ---------------------------------------------------------------------
-- [도메인] 내 기술스택
-- ---------------------------------------------------------------------
CREATE TABLE profile_skill (
    profile_id     UUID        NOT NULL REFERENCES seeker_profile(id) ON DELETE CASCADE,
    tech_stack_id  BIGINT      NOT NULL REFERENCES tech_stack(id)     ON DELETE CASCADE,
    level          SMALLINT    NOT NULL DEFAULT 1 CHECK (level BETWEEN 1 AND 3),  -- 1 입문 2 사용 3 능숙
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (profile_id, tech_stack_id)
);

-- ---------------------------------------------------------------------
-- [AI] Claude API 응답 캐시 (같은 입력이면 재호출하지 않음)
-- ---------------------------------------------------------------------
CREATE TABLE ai_analysis (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_hash  CHAR(64)    NOT NULL UNIQUE,             -- 입력의 SHA-256 (hex 64자)
    input         JSONB       NOT NULL,
    result        JSONB       NOT NULL,
    model         VARCHAR(50),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- [도메인] 격차 분석 결과 = "분석 기록 다시보기"
-- ---------------------------------------------------------------------
CREATE TABLE gap_report (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id      UUID         NOT NULL REFERENCES seeker_profile(id) ON DELETE CASCADE,
    job_role        VARCHAR(20)  NOT NULL
                    CHECK (job_role IN ('backend','frontend','fullstack','data','devops','etc')),
    match_rate      NUMERIC(5,2) NOT NULL CHECK (match_rate BETWEEN 0 AND 100),
    matched_skills  JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 분석 당시 스냅샷
    missing_skills  JSONB        NOT NULL DEFAULT '[]'::jsonb,  -- 분석 당시 스냅샷
    ai_analysis_id  BIGINT       REFERENCES ai_analysis(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_gap_report_profile_created ON gap_report (profile_id, created_at DESC);

-- ---------------------------------------------------------------------
-- [도메인] 학습 항목 = "학습 진행 체크"
-- ---------------------------------------------------------------------
CREATE TABLE learning_item (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gap_report_id  BIGINT       NOT NULL REFERENCES gap_report(id) ON DELETE CASCADE,
    tech_stack_id  BIGINT       REFERENCES tech_stack(id) ON DELETE SET NULL,
    title          VARCHAR(200) NOT NULL,                  -- 화면에 보여줄 학습 제목
    reason         TEXT,                                   -- AI가 제안한 이유
    priority       SMALLINT     NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),  -- 1이 가장 먼저
    status         VARCHAR(10)  NOT NULL DEFAULT 'todo'
                   CHECK (status IN ('todo','doing','done')),
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT chk_learning_done_has_time
        CHECK (status <> 'done' OR completed_at IS NOT NULL)          -- done이면 완료시각 필수
);
CREATE INDEX idx_learning_item_report ON learning_item (gap_report_id);

-- ---------------------------------------------------------------------
-- [통계] 직무별 기술 등장 빈도 = 비교분석의 기준
-- ---------------------------------------------------------------------
CREATE VIEW v_role_tech_stat AS
SELECT
    p.job_role,
    t.id        AS tech_stack_id,
    t.name      AS tech_name,
    t.category,
    COUNT(*)    AS posting_count,
    ROUND(100.0 * COUNT(*) / total.cnt, 1) AS ratio      -- 해당 직무 공고 중 몇 %가 요구하는지
FROM job_posting p
JOIN posting_tech pt ON pt.posting_id   = p.id
JOIN tech_stack  t   ON t.id            = pt.tech_stack_id
JOIN (
    SELECT job_role, COUNT(*) AS cnt
    FROM job_posting
    WHERE source <> 'user_input'
    GROUP BY job_role
) total ON total.job_role = p.job_role
WHERE p.source <> 'user_input'                            -- 개인 붙여넣기 공고는 시장 통계에서 제외
  AND (p.tags_reliable OR pt.extracted_from <> 'tag')     -- 오염된 태그는 통계에서 제외
GROUP BY p.job_role, t.id, t.name, t.category, total.cnt;

-- ---------------------------------------------------------------------
-- [보안] RLS 켜기 : 브라우저의 anon key로 테이블 직접 접근 차단
-- FastAPI/수집기는 DB 소유자 계정으로 접속하므로 영향 없음
-- ---------------------------------------------------------------------
ALTER TABLE tech_stack     ENABLE ROW LEVEL SECURITY;
ALTER TABLE tech_alias     ENABLE ROW LEVEL SECURITY;
ALTER TABLE seeker_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_posting    ENABLE ROW LEVEL SECURITY;
ALTER TABLE posting_tech   ENABLE ROW LEVEL SECURITY;
ALTER TABLE collect_log    ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_skill  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis    ENABLE ROW LEVEL SECURITY;
ALTER TABLE gap_report     ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_item  ENABLE ROW LEVEL SECURITY;

-- VIEW도 브라우저에서 직접 못 보게 (조회는 FastAPI를 거쳐서만)
REVOKE ALL ON v_role_tech_stat FROM anon, authenticated;

COMMIT;
