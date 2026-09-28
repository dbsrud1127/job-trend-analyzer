"""
db.py : 웹앱(FastAPI)용 DB 접속
- collector/db.py 와 같은 방식이지만, 웹앱은 수집기와 독립 프로그램이라 따로 둔다
- 여기는 "접속"만 담당한다. 조회 SQL은 service.py 에 있다
"""
import os                                    # 환경변수(.env 값) 읽기
import psycopg                               # PostgreSQL 접속 라이브러리
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
        connect_timeout=10,                  # 10초 안에 접속 못 하면 포기 (화면이 무한 로딩되는 것 방지)
    )
