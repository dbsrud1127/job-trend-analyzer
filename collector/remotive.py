import json        # 파이썬 데이터를 JSON 파일로 저장할 때 사용
import requests    # 인터넷으로 API를 호출하는 라이브러리

# Remotive 공개 API 주소
API_URL = "https://remotive.com/api/remote-jobs"


def fetch_jobs(category="software-development"):
    """Remotive에서 공고 목록을 가져와 리스트로 돌려준다."""
    #params = {"category": category}                    # 주소 뒤에 ?category=software-dev 로 붙음
    headers = {"User-Agent": "job-trend-analyzer"}     # 누가 호출하는지 알려주는 이름표
    response = requests.get(API_URL, headers=headers, timeout=30)  # 30초 넘으면 포기
    response.raise_for_status()                        # 응답이 에러(404, 500 등)면 여기서 바로 멈춤
    data = response.json()                             # 응답 글자를 파이썬 딕셔너리로 변환
    return data.get("jobs", [])                        # "jobs" 키의 공고 리스트 (없으면 빈 리스트)

def to_common(job):
    """Remotive 공고 1개를 수집기 공통 모양으로 바꾼다."""
    return {
        "source": "remotive",                                   # 어디서 왔는지
        "source_id": str(job.get("id")),                        # 원본 사이트의 공고 ID (문자로 통일)
        "title": job.get("title") or "",                        # 제목 (없으면 빈 글자)
        "company_name": job.get("company_name"),
        "category_raw": job.get("category"),                    # 원본 카테고리 (참고용)
        "job_type": job.get("job_type"),
        "location": job.get("candidate_required_location"),
        "salary_text": job.get("salary") or None,               # 빈 글자면 None 으로
        "description_html": job.get("description") or "",      # HTML 그대로 (정제는 transform 에서)
        "raw_tags": job.get("tags") or [],                      # 원본 태그 리스트
        "url": job.get("url"),
        "published_at": job.get("publication_date"),
    }

# 이 파일을 직접 실행했을 때만 아래가 동작 (다른 파일에서 import 할 때는 실행 안 됨)
if __name__ == "__main__":
    jobs = fetch_jobs()                                # 공고 가져오기
    print(f"가져온 공고 수: {len(jobs)}")               # 몇 개 받았는지 출력

    if jobs:                                           # 1개 이상 받았으면
        first = jobs[0]                                # 첫 번째 공고
        print("필드 목록:", list(first.keys()))         # 공고에 어떤 항목들이 있는지
        print("제목:", first.get("title"))
        print("카테고리:", first.get("category"))
        print("태그:", first.get("tags"))
        print("게시일:", first.get("publication_date"))

        # 4단계(transform) 테스트용으로 파일에 저장 → API를 반복 호출하지 않기 위해
        with open("collector/sample_jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)   # 한글 깨짐 방지, 보기 좋게 들여쓰기
        print("collector/sample_jobs.json 저장 완료")