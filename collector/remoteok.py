import json        # 샘플을 JSON 파일로 저장할 때 사용
import requests    # API 호출

# RemoteOK 공개 API 주소 (출처 표기 + 원문 링크 필수 → README에 명시)
API_URL = "https://remoteok.com/api"


def fetch_jobs():
    """RemoteOK에서 최신 공고 목록을 가져와 리스트로 돌려준다."""
    headers = {"User-Agent": "job-trend-analyzer"}                    # 이름표가 없으면 차단될 수 있음
    response = requests.get(API_URL, headers=headers, timeout=30)     # 30초 넘으면 포기
    response.raise_for_status()                                       # 에러 응답이면 여기서 멈춤
    data = response.json()                                            # 응답 전체 (리스트)
    # 첫 칸은 약관 안내문이라 제외 → 'position' 키가 있는 것만 공고로 인정
    return [item for item in data if "position" in item]

def to_common(job):
    """RemoteOK 공고 1개를 수집기 공통 모양으로 바꾼다."""
    salary_min = job.get("salary_min") or 0                     # 최소 연봉 (없으면 0)
    salary_max = job.get("salary_max") or 0                     # 최대 연봉 (없으면 0)
    salary_text = None                                          # 기본은 연봉 정보 없음
    if salary_min and salary_max:                               # 둘 다 있으면 글자로 만들기
        salary_text = f"${salary_min:,} - ${salary_max:,}"     # :, 는 천 단위 쉼표 (120000 → 120,000)

    return {
        "source": "remoteok",
        "source_id": str(job.get("id")),
        "title": job.get("position") or "",                     # RemoteOK 는 제목이 position
        "company_name": job.get("company"),                     # 회사명은 company
        "category_raw": None,                                   # RemoteOK 는 카테고리 없음
        "job_type": None,
        "location": job.get("location") or None,
        "salary_text": salary_text,
        "description_html": job.get("description") or "",
        "raw_tags": job.get("tags") or [],
        "url": job.get("url"),                                  # 원문 링크 (출처 표기용)
        "published_at": job.get("date"),
    }

# 직접 실행했을 때만 동작하는 확인용 코드
if __name__ == "__main__":
    jobs = fetch_jobs()
    print(f"가져온 공고 수: {len(jobs)}")

    if jobs:
        print("필드 목록:", list(jobs[0].keys()))                     # 어떤 항목이 있는지
        print("게시일 예시:", jobs[0].get("date"))
        print()
        # 앞 15개만 제목, 태그 개수, 태그 앞 8개 출력
        for job in jobs[:15]:
            tags = job.get("tags") or []                              # 태그가 없으면 빈 리스트
            print(f"- {job.get('position')} | 태그 {len(tags)}개 | {tags[:8]}")

        # transform 테스트용 샘플 저장 (API를 반복 호출하지 않기 위해)
        with open("collector/sample_remoteok.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print()
        print("collector/sample_remoteok.json 저장 완료")