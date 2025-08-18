# 🎯 찰나(Chalna) - 경조사 관리 API

> **"돈 관리에서 관계 관리로"** - 인간관계 중심의 경조사 생활 도우미

## 🚀 프로젝트 소개

찰나(Chalna)는 기존 가계부의 한계를 뛰어넘는 혁신적인 경조사 관리 플랫폼입니다.
단순한 금액 기록이 아닌, **인간관계 네트워크 관리**를 통해 더 의미 있는 관계를 만들어갑니다.

## 🎯 핵심 차별화 포인트

### 🤝 **1. 인간관계 네트워크 관리**
- 친밀도 점수 시스템 (0-100점)
- 관계 유형별 맞춤 관리
- 상호작용 기록 및 분석

### 💰 **2. 스마트 축의금 추천**
- 관계 깊이 + 이벤트 유형 분석
- 과거 기록 기반 개인화
- 사회적 예의 가이드

### 🎁 **3. 완벽한 답례 관리**
- 주고받은 선물 추적
- 자동 답례 알림
- 감사 메시지 생성

### ⏰ **4. 프로액티브 관리**
- 중요 날짜 자동 알림
- 관계 관리 제안
- 이벤트 준비 체크리스트

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.9+
- **Package Manager**: uv (빠른 패키지 관리)
- **Database**: SQLAlchemy, PostgreSQL (개발: SQLite)
- **Authentication**: JWT
- **Documentation**: Swagger UI, ReDoc
- **Code Quality**: Ruff, Black, MyPy

## 📁 프로젝트 구조

```
chalna-api/
├── app/
│   ├── api/              # API 라우터
│   ├── core/             # 핵심 설정
│   ├── models/           # 데이터 모델
│   ├── schemas/          # Pydantic 스키마
│   └── services/         # 비즈니스 로직
├── main.py               # 앱 엔트리포인트
├── requirements.txt      # 패키지 의존성
└── README.md
```

## 🚀 빠른 시작

### 1. 클론 및 설치
```bash
git clone https://github.com/CHOIisaac/chalna-api.git
cd chalna-api

# uv 사용 (권장 - 빠르고 현대적)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. 개발 서버 실행
```bash
# uv 사용 (권장)
uv run fastapi dev main.py

# 또는 직접 실행
uv run uvicorn main:app --reload

# 또는 기존 방식
fastapi dev main.py
uvicorn main:app --reload
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc

## 📊 데이터 모델

### 👤 User (사용자)
- 개인 정보, 앱 설정, 통계 정보

### 🤝 Relationship (관계)
- 인간관계 네트워크의 핵심
- 친밀도 점수, 연락 빈도, 상호작용 기록

### 🎉 Event (이벤트)
- 경조사 이벤트 관리
- 일정, 장소, 참석 정보, 비용

### 🎁 Gift (선물)
- 주고받은 선물 및 축의금 관리
- 답례 추적, 평가, 리마인더

## 🔐 API 엔드포인트

### 인증
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/register` - 회원가입
- `GET /api/v1/auth/me` - 현재 사용자 정보

### 사용자 관리
- `GET /api/v1/users/` - 사용자 목록
- `GET /api/v1/users/{id}` - 사용자 정보 조회
- `PUT /api/v1/users/{id}` - 사용자 정보 수정

### 이벤트 관리
- `GET /api/v1/events/` - 이벤트 목록
- `GET /api/v1/events/upcoming` - 다가오는 이벤트
- `POST /api/v1/events/` - 이벤트 생성
- `PUT /api/v1/events/{id}` - 이벤트 수정

## 🌟 향후 계획

- [ ] AI 기반 개인화 추천
- [ ] 모바일 앱 개발 (React Native)
- [ ] 소셜 기능 (커뮤니티)
- [ ] 비즈니스 연동 (배송, 선물 추천)
- [ ] 추억 아카이브 (사진, 메모)

## 📄 라이선스

MIT License

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 연락처

- 프로젝트 링크: [https://github.com/[your-username]/chalna-api](https://github.com/[your-username]/chalna-api)

---

**💡 "관계가 돈보다 소중합니다. 찰나로 더 의미 있는 관계를 만들어보세요!"** 🎯 