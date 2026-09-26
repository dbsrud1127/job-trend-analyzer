import re                                   # 정규식: 글자 패턴 검색 (직무 키워드 찾기)
from collections import Counter             # 같은 값이 몇 번 나오는지 세는 도구
from bs4 import BeautifulSoup               # HTML 에서 태그를 걷어내고 글자만 뽑는 도구

# ---------------------------------------------------------------------
# 설정값 (데이터 분포를 보고 조정)
# ---------------------------------------------------------------------
TAG_MAX = 15            # 태그가 이보다 많으면 믿지 않음
BUNDLE_REPEAT = 5       # 똑같은 태그 묶음이 이 개수 이상 공고에 반복되면 믿지 않음

DESC_TECH_MAX = 10      # 본문에서 찾은 기술이 이보다 많으면 "전부 나열한 템플릿"으로 보고 버림

# 제목이 모호할 때(Software Engineer 등) 기술로 직무를 판단하기 위한 묶음
# javascript/typescript 는 프론트·백엔드 양쪽에서 쓰여서 판단에 사용하지 않음
GENERIC_DEV_WORDS = ["developer", "software engineer", "programmer"]
FRONT_TECHS = {"react", "vue", "angular", "svelte", "nextjs"}
BACK_TECHS = {"java", "spring", "python", "django", "flask", "fastapi", "go", "nodejs",
              "express", "nestjs", ".net", "c#", "ruby", "rails", "php", "laravel",
              "scala", "rust"}

# 본문(description) 검색에서 제외할 모호한 별칭 (일반 영어 단어/글자와 겹침)
# 예: "go to market", "express interest", "spark curiosity", "Series C"
DESC_EXCLUDE = {"go", "c", "r", "express", "swift", "elastic", "spark"}

# 직무 분류 키워드. 위에서부터 차례로 검사해서 처음 걸리는 직무로 정함
# (fullstack 을 먼저 봐야 "React Full-stack" 이 frontend 로 가지 않음)
ROLE_KEYWORDS = [
    ("fullstack", ["full stack", "full-stack", "fullstack"]),
    ("devops",    ["devops", "sre", "site reliability", "platform engineer",
                   "infrastructure engineer", "cloud engineer"]),
    ("data",      ["data engineer", "data scientist", "data analyst", "machine learning",
                   "ml engineer", "ai engineer", "analytics engineer"]),
    ("frontend",  ["frontend", "front-end", "front end", "ui engineer", "ui developer",
                   "react", "vue", "angular"]),
    ("backend",   ["backend", "back-end", "back end", "api", "java", "python", "golang",
                   ".net", "node", "ruby", "rails", "php", "django", "spring"]),
]

# 본문을 단어로 자를 때 단어 앞뒤에서 떼어낼 문장부호
STRIP_CHARS = ",;:!?()[]{}\"'*|<>"


# ---------------------------------------------------------------------
# 작은 도구 함수들
# ---------------------------------------------------------------------
def normalize(text):
    """공백을 전부 없애고 소문자로. 'React JS' → 'reactjs'"""
    return "".join(text.split()).lower()          # split() 으로 공백 기준 자르고 붙이면 공백이 사라짐


def fix_mojibake(text):
    """깨진 글자 복구. 'MecÃ¡nico' → 'Mecánico' (UTF-8 을 latin-1 로 잘못 읽은 경우)"""
    if not text:                                  # None 이거나 빈 글자면 그대로
        return text
    try:
        return text.encode("latin-1").decode("utf-8")   # 잘못 읽은 과정을 거꾸로 되돌림
    except (UnicodeEncodeError, UnicodeDecodeError):    # 원래 멀쩡한 글자면 여기서 실패함
        return text                                     # → 원본 그대로 돌려줌


def clean_html(html):
    """HTML 태그를 걷어내고 글자만 남김. 여러 칸 공백/줄바꿈은 한 칸으로."""
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(" ")   # 태그 사이는 공백 한 칸으로 이어 붙임
    return " ".join(text.split())                             # 연속 공백 정리


def cut(text, max_len):
    """DB 컬럼 길이(VARCHAR)를 넘지 않게 자름. 비어 있으면 None."""
    if not text:
        return None
    return text[:max_len]


def has_keyword(text, keyword):
    """keyword 가 '단어로서' 들어있는지. 'java' 는 'javascript' 안에서는 안 걸림."""
    # (?<![a-z0-9]) : 바로 앞이 영문/숫자가 아니어야 함
    # (?![a-z0-9])  : 바로 뒤가 영문/숫자가 아니어야 함
    pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def classify_role(title):
    """제목 키워드로 직무 분류. 아무것도 안 걸리면 'etc'"""
    lower = title.lower()
    for role, keywords in ROLE_KEYWORDS:          # 정해진 순서대로 직무를 하나씩
        for keyword in keywords:                  # 그 직무의 키워드를 하나씩
            if has_keyword(lower, keyword):
                return role                       # 처음 걸린 직무로 확정
    return "etc"


def classify_by_techs(title, techs):
    """제목으로 직무를 못 정했을 때: 개발 공고로 보이면 요구 기술로 판단"""
    lower = title.lower()
    # 제목에 developer / software engineer / programmer 가 하나도 없으면 개발 공고가 아님
    if not any(has_keyword(lower, word) for word in GENERIC_DEV_WORDS):
        return "etc"
    has_front = any(tech in FRONT_TECHS for tech in techs)   # 프론트 기술이 하나라도 있나
    has_back = any(tech in BACK_TECHS for tech in techs)     # 백엔드 기술이 하나라도 있나
    if has_front and has_back:
        return "fullstack"
    if has_front:
        return "frontend"
    if has_back:
        return "backend"
    return "etc"                                             # 판단할 기술이 없으면 etc


def find_in_text(text, alias_map, exclude=None):
    """글에서 1~3단어 묶음을 만들어 사전에 있는 기술명을 찾음."""
    exclude = exclude or set()                                 # 제외 목록이 없으면 빈 집합
    words = text.lower().replace("/", " ").split()            # 'React/Redux' → 'react', 'redux'
    words = [w.strip(STRIP_CHARS).rstrip(".") for w in words] # 'node.js,' → 'node.js' / 'aws.' → 'aws'
    found = set()                                              # 찾은 기술 (중복 없이)
    for i in range(len(words)):                                # 단어 위치마다
        for size in (1, 2, 3):                                 # 1단어, 2단어, 3단어 묶음
            chunk = "".join(words[i:i + size])                 # 'spring','boot' → 'springboot'
            if chunk in exclude:                               # 모호한 별칭이면 건너뜀
                continue
            if chunk in alias_map:                             # 사전에 있으면
                found.add(alias_map[chunk])                    # 정식 기술명으로 저장
    return found


# ---------------------------------------------------------------------
# 메인: 공통 모양 공고 리스트 → 저장할 준비가 된 공고 리스트
# ---------------------------------------------------------------------
def transform_all(jobs, alias_map):
    """
    jobs      : 수집 파일들의 to_common() 결과 리스트
    alias_map : {'reactjs': 'react', '자바': 'java', ...}  별칭 → 정식명
    돌려주는 값: (정제된 공고 리스트, 사전에 없는 태그 Counter)
    """
    # 1) 태그 묶음이 몇 개 공고에 반복되는지 먼저 전체를 세어 둠
    bundle_counter = Counter()
    for job in jobs:
        tags = [normalize(t) for t in job["raw_tags"] if t]
        if tags:
            bundle_counter[tuple(sorted(tags))] += 1          # 순서 상관없이 같은 묶음이면 같은 키

    results = []
    unknown_tags = Counter()                                   # 사전에 없는 태그 (별칭 보강용)

    for job in jobs:
        # 2) 글자 정리
        title = fix_mojibake(job["title"]).strip()
        description = clean_html(fix_mojibake(job["description_html"]))
        tags = [normalize(t) for t in job["raw_tags"] if t]

        # 3) 태그를 믿을 수 있는지 판단
        bundle = tuple(sorted(tags))
        reliable = len(tags) <= TAG_MAX and bundle_counter[bundle] < BUNDLE_REPEAT
        # RemoteOK는 공고와 무관한 태그(golang 등)를 자동으로 붙이므로 태그를 믿지 않는다
        if job["source"] == "remoteok":    # 출처가 remoteok이면
            reliable = False               # 태그 신뢰 X → 제목+본문에서 기술을 추출하게 됨

        # 4) 기술 추출. techs = {정식명: 어디서 찾았는지}
        #    setdefault: 이미 있으면 안 바꿈 → 먼저 찾은 곳이 우선 (tag > title > description)
        techs = {}
        if reliable and tags:                                  # 태그 신뢰 O → tag + title
            for tag in tags:
                if tag in alias_map:
                    techs.setdefault(alias_map[tag], "tag")
                else:
                    unknown_tags[tag] += 1                     # 믿을 만한 태그 중 사전에 없는 것만 셈
            for tech in find_in_text(title, alias_map):
                techs.setdefault(tech, "title")
        else:                                                  # 태그 신뢰 X 또는 태그 없음 → title + description
            for tech in find_in_text(title, alias_map):
                techs.setdefault(tech, "title")
            desc_techs = find_in_text(description, alias_map, DESC_EXCLUDE)
            if len(desc_techs) <= DESC_TECH_MAX:               # 너무 많으면 템플릿 문단 → 버림
                for tech in desc_techs:
                    techs.setdefault(tech, "description")

        # 직무 분류: 제목 키워드 먼저, 안 되면 요구 기술로 한 번 더
        job_role = classify_role(title)
        if job_role == "etc":
            job_role = classify_by_techs(title, techs)

        # 5) job_posting 컬럼에 맞춘 모양으로 정리
        results.append({
            "source": job["source"],
            "source_id": job["source_id"],
            "title": cut(title, 300) or "(제목 없음)",          # title 은 NOT NULL 이라 기본값
            "company_name": cut(fix_mojibake(job["company_name"]), 200),
            "category_raw": cut(job["category_raw"], 100),
            "job_role": job_role,
            "job_type": cut(job["job_type"], 30),
            "location": job["location"],
            "salary_text": cut(job["salary_text"], 100),
            "description": description,
            "raw_tags": job["raw_tags"],                        # 원본 태그 그대로 (재처리용)
            "tags_reliable": reliable,
            "url": job["url"],
            "published_at": job["published_at"],
            "techs": techs,                                     # posting_tech 에 넣을 기술들
        })

    return results, unknown_tags


# ---------------------------------------------------------------------
# 직접 실행했을 때만: 샘플 파일 2개로 정제 결과 확인 (API 호출 없음)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import os
    import psycopg
    from dotenv import load_dotenv
    import remotive
    import remoteok

    # 테스트용으로 DB 에서 별칭 사전만 읽어옴 (저장 기능은 5단계 db.py 에서)
    load_dotenv()
    with psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
    ) as conn:
        rows = conn.execute(
            "SELECT a.alias, t.name FROM tech_alias a JOIN tech_stack t ON t.id = a.tech_stack_id"
        ).fetchall()
    alias_map = {alias: name for alias, name in rows}          # [(별칭, 정식명), ...] → 딕셔너리
    print("별칭 사전:", len(alias_map), "개")

    # 샘플 파일 읽어서 공통 모양으로 변환
    with open("collector/sample_jobs.json", encoding="utf-8") as f:
        jobs = [remotive.to_common(j) for j in json.load(f)]
    with open("collector/sample_remoteok.json", encoding="utf-8") as f:
        jobs += [remoteok.to_common(j) for j in json.load(f)]

    results, unknown = transform_all(jobs, alias_map)

    print("공고 수:", len(results))
    print("직무 분포:", Counter(r["job_role"] for r in results))
    print("태그 신뢰 X:", sum(1 for r in results if not r["tags_reliable"]), "개")
    # 모든 공고의 기술을 한 줄로 펼쳐서 셈
    tech_counter = Counter(tech for r in results for tech in r["techs"])
    print("기술 상위 15:", tech_counter.most_common(15))
    print("사전에 없는 태그 상위 20:", unknown.most_common(20))
    print()

    for source in ("remotive", "remoteok"):                     # 출처별 앞 6개 공고 미리보기
        for r in [r for r in results if r["source"] == source][:6]:
            print(f"- [{source}] {r['title'][:45]} → {r['job_role']} | 신뢰 {r['tags_reliable']} | {r['techs']}")