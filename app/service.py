"""
service.py : 통계 계산 담당
- DB에서 숫자를 가져와 "화면/API가 그대로 쓸 수 있는 모양(dict)"으로 만든다
- main.py(라우터)와 템플릿에는 계산을 넣지 않는다 → v2에서 React로 바꿔도 이 파일은 그대로
"""
from app.db import get_connection            # 같은 app 폴더의 db.py에서 접속 함수 가져오기

# 화면에서 고를 수 있는 직무 목록 (etc는 "분류 안 됨"이라 통계에서 제외)
ROLES = ["backend", "frontend", "fullstack", "data", "devops"]

# 직무별 공고 수 (user_input = 사용자가 붙여넣은 공고라 시장 통계에서 제외)
# %s 자리에 값이 안전하게 들어간다 (f-string으로 SQL을 만들면 SQL 인젝션 위험)
COUNT_SQL = """
SELECT COUNT(*)
FROM job_posting
WHERE job_role = %s
  AND source <> 'user_input'
"""

# 직무별 기술 통계 (VIEW가 이미 공고 수/비율을 계산해 둠)
# 많이 요구되는 순 → 같으면 이름순, 상위 N개만
TECH_SQL = """
SELECT tech_name, category, posting_count, ratio
FROM v_role_tech_stat
WHERE job_role = %s
ORDER BY posting_count DESC, tech_name
LIMIT %s
"""


def get_role_stats(role, limit=15):
    """직무 하나의 공고 수와 기술 순위를 dict로 돌려준다"""
    if role not in ROLES:                    # 목록에 없는 값(오타, etc 등)이 들어오면
        role = "backend"                     # 기본값 backend로 대체

    # with 문: 블록이 끝나면 연결을 자동으로 닫아 준다 (닫는 걸 깜빡해도 안전)
    with get_connection() as conn:
        # execute(SQL, (값,)) : 값이 1개여도 튜플이라 끝에 쉼표가 필요하다
        # fetchone() → (숫자,) 한 줄, [0]으로 숫자만 꺼냄
        total = conn.execute(COUNT_SQL, (role,)).fetchone()[0]
        # fetchall() → [(이름, 분류, 공고수, 비율), ...] 여러 줄
        rows = conn.execute(TECH_SQL, (role, limit)).fetchall()

    techs = []                               # 결과를 담을 빈 리스트
    for name, category, count, ratio in rows:    # 한 줄(튜플)을 네 변수로 나눠 받기
        techs.append({
            "name": name,                    # 기술 이름 (예: python)
            "category": category,            # 기술 분류 (예: language)
            "count": count,                  # 이 기술을 요구한 공고 수
            "ratio": float(ratio),           # DB의 NUMERIC(Decimal)은 JSON으로 못 보내서 float로 변환
        })

    return {
        "role": role,                        # 실제로 사용된 직무 (대체됐을 수도 있음)
        "total_postings": total,             # 이 직무 전체 공고 수 (표본 크기)
        "techs": techs,                      # 기술 목록
    }


# ---------------------------------------------------------------------
# 테스트: 루트에서 python -m app.service
# (-m 으로 실행해야 "from app.db" 가 동작한다)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print(get_role_stats("backend", limit=5))