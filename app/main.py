"""
main.py : FastAPI 앱 (라우터)
- 주소(URL)와 service 함수를 연결만 한다. 계산은 service.py 가 한다
- 실행: 루트에서 uvicorn app.main:app --reload
"""
from pathlib import Path                     # 파일 경로를 다루는 표준 도구

import psycopg                               # DB 접속 에러 종류를 잡기 위해
from fastapi import FastAPI, HTTPException, Request   # 웹 서버 / 에러 응답 / 요청 정보
from fastapi.templating import Jinja2Templates        # HTML 템플릿 렌더링 도구

from app.service import ROLES, get_role_stats         # 통계 계산 함수와 직무 목록

app = FastAPI(title="job-trend-analyzer")    # 앱 객체. uvicorn이 이 이름(app)을 찾아 실행한다

# templates 폴더 위치를 이 파일 기준으로 지정 → 어느 폴더에서 실행해도 찾을 수 있음
# Path(__file__).parent = 이 파일(main.py)이 있는 폴더 = app/
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def load_stats(role):
    """service를 호출하고, DB 접속 실패면 503 에러로 바꿔 준다"""
    try:                                     # try: 에러가 날 수 있는 코드를 시도
        return get_role_stats(role)
    except psycopg.OperationalError:         # except: DB 접속 실패(타임아웃, 비밀번호 오류 등)일 때
        raise HTTPException(status_code=503, detail="DB에 접속할 수 없습니다")


# @app.get("주소") : 이 주소로 GET 요청이 오면 아래 함수를 실행하라는 표시 (데코레이터)
# role: str = "backend" : 주소의 ?role=... 값을 받는다. 없으면 "backend"
@app.get("/api/stats")
def api_stats(role: str = "backend"):
    """직무별 기술 통계를 JSON으로 돌려준다. 예: /api/stats?role=data"""
    return load_stats(role)                  # dict를 돌려주면 FastAPI가 JSON으로 바꿔 준다


@app.get("/")
def stats_page(request: Request, role: str = "backend"):
    """같은 service 결과를 HTML 화면(stats.html)으로 보여준다"""
    stats = load_stats(role)                 # API와 똑같은 함수 호출 → 결과가 항상 같음
    return templates.TemplateResponse(
        request,                             # 템플릿 렌더링에 필요한 요청 정보
        "stats.html",                        # app/templates/stats.html
        {"stats": stats, "roles": ROLES},    # 템플릿에서 쓸 값들 (이름: 값)
    )
