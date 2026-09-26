"""
db.py : DB 접속과 저장 함수 모음
- 수집/변환은 모르고, "받은 공고를 DB에 넣는 일"만 담당한다
- commit(확정)은 여기서 하지 않고, 부르는 쪽(main.py)이 결정한다
"""
import os                                    # 환경변수(.env 값) 읽기
import psycopg                               # PostgreSQL 접속 라이브러리
from psycopg.types.json import Jsonb         # 파이썬 리스트를 JSONB 컬럼에 넣을 때 감싸는 도구
from dotenv import load_dotenv               # .env 파일 내용을 환경변수로 불러오기

load_dotenv()                                # 이 파일이 import될 때 .env를 한 번 읽음


def get_connection():
    """Supabase(Session pooler)에 접속한 연결을 돌려준다"""
    return psycopg.connect(
        host=os.getenv("DB_HOST"),           # .env의 DB_HOST
        port=os.getenv("DB_PORT"),           # .env의 DB_PORT
        dbname=os.getenv("DB_NAME"),         # .env의 DB_NAME
        user=os.getenv("DB_USER"),           # .env의 DB_USER
        password=os.getenv("DB_PASSWORD"),   # .env의 DB_PASSWORD
    )


def load_alias(conn):
    """{별칭: 정식명} 사전을 돌려준다. 예: {'reactjs': 'react'}"""
    rows = conn.execute(
        "SELECT a.alias, t.name FROM tech_alias a "
        "JOIN tech_stack t ON t.id = a.tech_stack_id"
    ).fetchall()                             # [(별칭, 정식명), ...] 형태로 전부 가져옴
    return {alias: name for alias, name in rows}   # 리스트 → 딕셔너리


def cut(value, max_len):
    """문자열이 컬럼 길이보다 길면 잘라서 에러를 막는다. None은 그대로 둔다"""
    if value is None:                        # 값이 없으면
        return None                          # 그대로 None
    return str(value)[:max_len]              # 앞에서부터 max_len 글자까지만


# 같은 (source, source_id)가 이미 있으면 INSERT 대신 UPDATE 하는 SQL (= upsert)
UPSERT_POSTING_SQL = """
INSERT INTO job_posting (
    source, source_id, title, company_name, category_raw, job_role, job_type,
    location, salary_text, description, raw_tags, tags_reliable, url,
    published_at, last_seen_at
) VALUES (
    %(source)s, %(source_id)s, %(title)s, %(company_name)s, %(category_raw)s,
    %(job_role)s, %(job_type)s, %(location)s, %(salary_text)s, %(description)s,
    %(raw_tags)s, %(tags_reliable)s, %(url)s, %(published_at)s, now()
)
ON CONFLICT (source, source_id) DO UPDATE SET
    title         = EXCLUDED.title,
    company_name  = EXCLUDED.company_name,
    category_raw  = EXCLUDED.category_raw,
    job_role      = EXCLUDED.job_role,
    job_type      = EXCLUDED.job_type,
    location      = EXCLUDED.location,
    salary_text   = EXCLUDED.salary_text,
    description   = EXCLUDED.description,
    raw_tags      = EXCLUDED.raw_tags,
    tags_reliable = EXCLUDED.tags_reliable,
    url           = EXCLUDED.url,
    published_at  = EXCLUDED.published_at,
    last_seen_at  = now()
RETURNING id
"""


def save_posting(conn, p):
    """공고 1개를 저장(없으면 추가, 있으면 갱신)하고 공고 id를 돌려준다"""
    params = {
        "source":        p["source"],                       # 'remotive' / 'remoteok'
        "source_id":     str(p["source_id"]),               # 원본 공고 ID (숫자여도 문자로)
        "title":         cut(p["title"], 300),              # VARCHAR(300)
        "company_name":  cut(p.get("company_name"), 200),   # VARCHAR(200)
        "category_raw":  cut(p.get("category_raw"), 100),   # VARCHAR(100)
        "job_role":      p["job_role"],                     # transform이 정한 직무
        "job_type":      cut(p.get("job_type"), 30),        # VARCHAR(30)
        "location":      p.get("location"),                 # TEXT라 길이 제한 없음
        "salary_text":   cut(p.get("salary_text"), 100),    # VARCHAR(100)
        "description":   p.get("description"),              # HTML 제거된 본문
        "raw_tags":      Jsonb(p.get("raw_tags") or []),    # 리스트를 JSONB로 감쌈
        "tags_reliable": p["tags_reliable"],                # 태그 신뢰 여부
        "url":           p.get("url"),                      # 원문 링크
        "published_at":  p.get("published_at"),             # 게시일
    }
    row = conn.execute(UPSERT_POSTING_SQL, params).fetchone()   # 실행 후 RETURNING 결과 1줄
    return row[0]                                               # (id,) 에서 id만 꺼냄


def save_posting_tech(conn, posting_id, techs):
    """공고의 기술 연결을 지우고 다시 넣는다. techs 예: {'python': 'tag', 'react': 'title'}"""
    conn.execute("DELETE FROM posting_tech WHERE posting_id = %s", (posting_id,))  # 기존 연결 삭제
    for name, extracted_from in techs.items():                  # (정식명, 추출 위치)를 하나씩
        conn.execute(
            "INSERT INTO posting_tech (posting_id, tech_stack_id, extracted_from) "
            "SELECT %s, id, %s FROM tech_stack WHERE name = %s",    # 정식명으로 기술 id를 찾아 넣음
            (posting_id, extracted_from, name),
        )


def save_collect_log(conn, source, fetched_count, inserted_count, status, error_message=None):
    """수집 1회 결과를 collect_log에 1줄 기록한다. status: success / partial / failed"""
    conn.execute(
        "INSERT INTO collect_log (source, fetched_count, inserted_count, status, error_message) "
        "VALUES (%s, %s, %s, %s, %s)",
        (source, fetched_count, inserted_count, status, error_message),
    )


# ---------------------------------------------------------------------
# 테스트: python collector/db.py
# 가짜 공고를 저장해 보고, 마지막에 rollback 해서 DB에는 아무것도 남기지 않는다
# ---------------------------------------------------------------------
if __name__ == "__main__":
    test = {                                                    # transform 결과와 같은 모양의 가짜 공고
        "source": "remotive", "source_id": "TEST-0001",
        "title": "테스트 공고", "company_name": "테스트회사",
        "job_role": "backend", "description": "테스트 본문",
        "raw_tags": ["python"], "tags_reliable": True,
        "techs": {"python": "tag", "react": "title"},
    }

    with get_connection() as conn:                              # 접속 (블록이 끝나면 자동으로 닫힘)
        print("별칭 사전:", len(load_alias(conn)), "개")

        id1 = save_posting(conn, test)                          # 1차 저장 → INSERT
        save_posting_tech(conn, id1, test["techs"])             # 기술 2개 연결

        test["title"] = "테스트 공고 (수정됨)"                     # 같은 공고가 제목만 바뀌어 다시 들어왔다고 가정
        id2 = save_posting(conn, test)                          # 2차 저장 → UPDATE 되어야 함
        save_posting_tech(conn, id2, {"python": "tag"})         # 기술을 1개로 바꿔서 다시 넣기

        print("id 비교:", id1, id2, "→ 같으면 upsert 성공")

        row = conn.execute(
            "SELECT title, last_seen_at FROM job_posting WHERE id = %s", (id2,)
        ).fetchone()
        print("제목:", row[0], "| last_seen_at:", row[1])

        rows = conn.execute(
            "SELECT t.name FROM posting_tech pt JOIN tech_stack t ON t.id = pt.tech_stack_id "
            "WHERE pt.posting_id = %s", (id2,)
        ).fetchall()
        print("연결된 기술:", [r[0] for r in rows], "→ python 하나면 지우고 다시 넣기 성공")

        save_collect_log(conn, "remotive", 1, 1, "success")     # 로그 저장도 에러 없이 되는지 확인
        print("collect_log 저장 OK")

        conn.rollback()                                         # 지금까지 한 일을 전부 취소 → DB는 깨끗
        print("테스트 끝: rollback으로 전부 취소함")