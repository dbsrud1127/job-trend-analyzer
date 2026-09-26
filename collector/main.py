"""
main.py : 수집 → 변환 → 저장 전체 실행 (GitHub Actions도 이 파일을 실행)
실행: 루트에서 python collector/main.py
"""
import sys                                   # 실패 시 종료 코드를 남기기 위해
from collections import Counter              # 사전에 없는 태그 개수 합치기

import remotive                              # Remotive 수집 (fetch_jobs, to_common)
import remoteok                              # RemoteOK 수집 (fetch_jobs, to_common)
from transform import transform_all          # 정제/분류/기술 추출
import db                                    # DB 접속과 저장 함수

# 수집할 출처 목록: (이름, 모듈). 출처가 늘면 여기에 한 줄만 추가
SOURCES = [
    ("remotive", remotive),
    ("remoteok", remoteok),
]


def run_source(conn, name, module, alias_map):
    """출처 하나를 수집 → 변환 → 저장하고, 사전에 없는 태그 Counter를 돌려준다"""
    raw = module.fetch_jobs()                            # 1) 외부 API 호출 → 원본 공고 리스트
    jobs = [module.to_common(j) for j in raw]            # 2) 출처마다 다른 모양 → 공통 모양
    results, unknown = transform_all(jobs, alias_map)    # 3) 정제 + 직무 분류 + 기술 추출

    for p in results:                                    # 4) 공고를 하나씩 저장
        posting_id = db.save_posting(conn, p)            #    upsert 후 공고 id 받기
        db.save_posting_tech(conn, posting_id, p["techs"])   # 기술 연결 지우고 다시 넣기

    db.save_collect_log(conn, name, len(raw), len(results), "success")   # 5) 성공 기록
    conn.commit()                                        # 6) 여기까지를 DB에 확정
    print(f"[{name}] 수집 {len(raw)} → 저장 {len(results)}")
    return unknown


def main():
    total_unknown = Counter()                            # 출처별 '사전에 없는 태그'를 합칠 곳
    has_failure = False                                  # 하나라도 실패했는지 표시

    with db.get_connection() as conn:                    # DB 접속 (끝나면 자동으로 닫힘)
        alias_map = db.load_alias(conn)                  # 별칭 사전은 한 번만 읽음
        print("별칭 사전:", len(alias_map), "개")

        for name, module in SOURCES:                     # 출처를 하나씩 처리
            try:
                total_unknown += run_source(conn, name, module, alias_map)
            except Exception as e:                       # 이 출처에서 어떤 에러든 나면
                conn.rollback()                          # 이 출처가 저장하던 것만 취소
                db.save_collect_log(conn, name, 0, 0, "failed", str(e)[:1000])  # 실패 기록
                conn.commit()                            # 실패 기록은 확정
                print(f"[{name}] 실패: {e}")
                has_failure = True                       # 다음 출처는 계속 진행

    print("사전에 없는 태그 상위 20:", total_unknown.most_common(20))

    if has_failure:                                      # 실패가 있었으면
        sys.exit(1)                                      # 종료 코드 1 → GitHub Actions에서 빨간색 표시


if __name__ == "__main__":
    main()