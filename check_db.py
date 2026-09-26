# DB 연결 확인용 스크립트
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# 이 파일과 같은 폴더의 .env를 읽는다
load_dotenv(Path(__file__).parent / ".env")

with psycopg.connect(
    host=os.environ["DB_HOST"],
    port=os.environ.get("DB_PORT", "5432"),
    dbname=os.environ.get("DB_NAME", "postgres"),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    sslmode="require",
) as conn:
    row = conn.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    ).fetchone()
    print(f"연결 성공! 테이블 {row[0]}개")