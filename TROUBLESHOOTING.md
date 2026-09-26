## 트러블슈팅

### 1. 수집 데이터에 개발과 무관한 공고 혼입
- 문제: 고객상담, 작가, 영업 공고가 섞여 들어옴
- 원인: category 필터 미적용 + Remotive의 category 자체도 부정확
  (프론트엔드 개발 공고가 "Design"으로 분류됨)
- 해결: 원본 category는 category_raw로 보관, 제목 키워드로 직무(job_role) 재분류

### 2. 특정 회사의 보일러플레이트 태그로 통계 왜곡
- 문제: Lemon.io 공고는 직무와 상관없이 동일한 40여 개 태그가 붙음
  (QA 공고에도 Ethereum, flutter 등)
- 원인: 채용 플랫폼이 공고별이 아닌 회사 단위 태그를 일괄 적용
- 해결(검토 중): 태그 수가 기준치를 넘으면 tags_reliable=false 처리

### 3. 같은 기술의 표기 불일치
- 문제: "Typescript "(공백), react / react js, go / golang, ror / ruby/rails
- 원인: 입력자마다 표기 방식이 다름
- 해결: 공백 제거 + 소문자화 + tech_alias 테이블로 정규화

### 4. 기술이 아닌 태그 혼입
- 문제: diversity, insurance, startup 등 / 작가 공고에 REST 태그
- 해결: 화이트리스트 방식 (tech_alias에 등록된 기술만 저장)

### 5. 중복 수집 위험
- 문제: 스케줄러로 매일 수집 시 같은 공고 중복 저장 가능
- 해결: (source, source_id) UNIQUE 제약

### 6. API 승인 대기로 인한 일정 리스크
- 문제: 사람인 API는 승인 후에만 사용 가능, 소요 기간 불확실
- 해결: 키 불필요한 Remotive로 파이프라인 먼저 개발, 승인 후 source만 추가

### 7. 외부 환경에서 Supabase DB 접속 실패 우려
- 문제: Supabase Direct connection 주소로는 Render/GitHub Actions에서 DB 연결이 안 됨
- 원인: Direct connection은 IPv6 전용인데, 해당 실행 환경은 IPv6를 지원하지 않음
- 해결: Session pooler 주소(IPv4 지원)를 .env에 사용하도록 통일, check_db.py로 연결 확인

### 8. 원본 category를 믿을 수 없음
- 문제: Remotive의 category가 부정확하고, 개발과 무관한 공고가 섞여 들어옴
- 원인: 원본 사이트의 분류 기준이 직무 분석 목적과 다름
- 해결: category_raw는 참고용으로만 보관하고, 제목 키워드로 직무를 재분류 (fullstack → devops → data → frontend → backend → etc 순서)