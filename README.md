# 🎯 찰나(Chalna) - 경조사 관리 API

> **"돈 관리에서 관계 관리로"** - 인간관계 중심의 경조사 생활 도우미

## 🚀 프로젝트 소개

찰나(Chalna)는 기존 가계부의 한계를 뛰어넘는 혁신적인 경조사 관리 플랫폼입니다.
단순한 금액 기록이 아닌, **인간관계 네트워크 관리**를 통해 더 의미 있는 관계를 만들어갑니다.

## 🎯 주요 기능

### 🔐 **인증 시스템**
- JWT 토큰 기반 인증
- 사용자 로그인/회원가입
- 보안 토큰 관리

### 👤 **사용자 관리**
- 사용자 정보 CRUD
- 비밀번호 변경
- 알림 설정 관리
- 사용자 통계

### 💰 **장부 관리**
- 경조사비 수입/지출 기록
- 상대방 정보 관리
- 검색 및 필터링
- 통계 및 분석

### 📅 **일정 관리**
- 경조사 일정 등록
- 월별/일별 조회
- 빠른 일정 추가
- 일정 통계

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.11+
- **Package Manager**: uv (빠른 패키지 관리)
- **Database**: SQLAlchemy, PostgreSQL
- **Authentication**: JWT
- **Documentation**: Swagger UI, ReDoc
- **Code Quality**: Ruff, Black, MyPy
- **Migration**: Alembic

## 📁 프로젝트 구조

```
chalna-api/
├── app/
│   ├── api/              # API 라우터
│   │   ├── auth.py       # 인증 관련
│   │   ├── users.py      # 사용자 관리
│   │   ├── ledgers.py    # 장부 관리
│   │   └── schedules.py  # 일정 관리
│   ├── core/             # 핵심 설정
│   │   ├── config.py     # 환경 설정
│   │   ├── database.py   # 데이터베이스 연결
│   │   ├── security.py   # 보안 관련
│   │   └── constants.py  # 상수 정의
│   ├── models/           # SQLAlchemy 모델
│   │   ├── user.py       # 사용자 모델
│   │   ├── ledger.py     # 장부 모델
│   │   └── schedule.py   # 일정 모델
│   ├── schemas/          # Pydantic 스키마
│   │   ├── auth.py       # 인증 스키마
│   │   ├── user.py       # 사용자 스키마
│   │   ├── ledger.py     # 장부 스키마
│   │   └── schedule.py   # 일정 스키마
│   └── services/         # 비즈니스 로직
├── alembic/              # 데이터베이스 마이그레이션
├── main.py               # 앱 엔트리포인트
├── pyproject.toml        # 프로젝트 설정
├── Makefile              # 개발 편의 명령어
└── README.md
```

## 🚀 빠른 시작

### 1. 클론 및 설치
```bash
git clone https://github.com/CHOIisaac/chalna-api.git
cd chalna-api

# uv 사용 (권장 - 빠르고 현대적)
uv sync
```

### 2. 개발 환경 설정
```bash
# 로컬 개발 환경 (인프라는 Docker, 서버는 로컬)
make dev-local

# 또는 전체 Docker 환경
make docker-dev
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc

## 📊 데이터 모델

### 👤 User (사용자)
- 개인 정보, 앱 설정, 통계 정보
- 알림 설정, 비밀번호 관리

### 💰 Ledger (장부)
- 경조사비 수입/지출 기록
- 상대방 정보, 관계 타입, 메모
- 통계 및 분석 기능

### 📅 Schedule (일정)
- 경조사 일정 관리
- 날짜/시간 분리로 쿼리 최적화
- 월별/일별 조회 지원

## 🔐 API 엔드포인트

### 인증
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/token` - OAuth2 토큰 (Swagger UI용)

### 사용자 관리
- `POST /api/v1/users/` - 사용자 생성
- `GET /api/v1/users/me` - 내 정보 조회
- `PUT /api/v1/users/me` - 내 정보 수정
- `PATCH /api/v1/users/me/password` - 비밀번호 변경
- `GET /api/v1/users/me/notification-settings` - 알림 설정 조회
- `PATCH /api/v1/users/me/notification-settings` - 알림 설정 변경
- `GET /api/v1/users/me/stats` - 내 통계 조회

### 장부 관리
- `POST /api/v1/ledgers/` - 장부 기록 생성
- `GET /api/v1/ledgers/` - 장부 목록 조회
- `GET /api/v1/ledgers/{id}` - 장부 상세 조회
- `PUT /api/v1/ledgers/{id}` - 장부 기록 수정
- `DELETE /api/v1/ledgers/{id}` - 장부 기록 삭제
- `GET /api/v1/ledgers/income` - 수입 내역 조회
- `GET /api/v1/ledgers/expense` - 지출 내역 조회
- `GET /api/v1/ledgers/balance` - 수지 잔액 조회
- `POST /api/v1/ledgers/search` - 장부 검색
- `GET /api/v1/ledgers/stats` - 장부 통계
- `POST /api/v1/ledgers/quick-add` - 빠른 장부 추가
- `GET /api/v1/ledgers/event-type/{event_type}` - 경조사 타입별 조회
- `GET /api/v1/ledgers/relationships` - 관계별 통계

### 일정 관리
- `POST /api/v1/schedules/` - 일정 생성
- `GET /api/v1/schedules/` - 일정 목록 조회
- `GET /api/v1/schedules/{id}` - 일정 상세 조회
- `PUT /api/v1/schedules/{id}` - 일정 수정
- `DELETE /api/v1/schedules/{id}` - 일정 삭제
- `GET /api/v1/schedules/calendar/daily` - 일별 일정 조회
- `GET /api/v1/schedules/calendar/weekly` - 주별 일정 조회
- `GET /api/v1/schedules/summary/stats` - 일정 통계
- `POST /api/v1/schedules/quick-add` - 빠른 일정 추가
- `GET /api/v1/schedules/upcoming` - 다가오는 일정
- `GET /api/v1/schedules/today` - 오늘 일정

## 🛠️ 개발 도구

### Makefile 명령어
```bash
make help              # 사용 가능한 명령어 표시
make dev               # 개발 서버 실행
make dev-local         # 로컬 개발 환경 (인프라는 Docker)
make docker-dev        # Docker 개발 환경
make test              # 테스트 실행
make lint              # 코드 검사
make format            # 코드 포매팅
make clean             # 캐시 정리
make db-create         # 데이터베이스 테이블 생성
make db-reset          # 데이터베이스 초기화
make create-admin      # 관리자 계정 생성
```

### 코드 품질 도구
- **Ruff**: 빠른 린터 및 코드 포매터
- **Black**: 코드 포매터
- **MyPy**: 타입 체크
- **Pytest**: 테스트 프레임워크

## 🔧 환경 설정

### 환경 변수
```bash
# JWT 토큰 설정
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24시간

# 데이터베이스 설정
DATABASE_URL=postgresql://chalna_user:chalna_password@localhost:5434/chalna

# 보안 설정
SECRET_KEY=your-super-secret-key-change-in-production
```

### Docker Compose
```bash
# 로컬 개발용 인프라 (PostgreSQL + Redis)
make docker-local

# 전체 개발 환경
make docker-dev
```

## 🌟 주요 기능

### 📊 통계 및 분석
- 월별/일별 경조사비 통계
- 관계별 지출 분석
- 이벤트 타입별 통계

### 🔍 검색 및 필터링
- 장부 기록 검색
- 날짜 범위 필터링
- 관계 타입별 필터링

### ⚡ 빠른 입력
- 빠른 장부 추가
- 빠른 일정 추가
- 기본값 자동 설정

### 📱 사용자 경험
- JWT 토큰 인증
- Swagger UI 문서화
- RESTful API 설계

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

- 프로젝트 링크: [https://github.com/CHOIisaac/chalna-api](https://github.com/CHOIisaac/chalna-api)

---

**💡 "관계가 돈보다 소중합니다. 찰나로 더 의미 있는 관계를 만들어보세요!"** 🎯