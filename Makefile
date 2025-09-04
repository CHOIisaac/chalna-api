# 🚀 찰나(Chalna) API - 개발 편의 명령어

.PHONY: help install dev prod test lint format clean db-create db-reset db-info db-test docker-build docker-run docker-dev docker-stop docker-clean docker-logs

help:  ## 📋 사용 가능한 명령어 표시
	@echo "🎯 찰나(Chalna) API 개발 명령어"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 📦 패키지 설치
	uv sync

dev:  ## 🚀 개발 서버 실행
	uv run fastapi dev main.py

dev-uvicorn:  ## 🚀 개발 서버 실행 (uvicorn 직접)
	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

prod:  ## 🏭 프로덕션 서버 실행
	uv run uvicorn main:app --host 0.0.0.0 --port 8000

test:  ## 🧪 테스트 실행
	uv run pytest

lint:  ## 🔍 코드 검사
	uv run ruff check .
	uv run mypy app/

format:  ## 🎨 코드 포매팅
	uv run black .
	uv run ruff check . --fix

clean:  ## 🧹 캐시 정리
	uv cache clean
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# 🗃️ 데이터베이스 관리
db-create:  ## 🏗️ 데이터베이스 테이블 생성
	uv run python create_tables.py

db-create-samples:  ## 🌱 데이터베이스 테이블 생성 + 샘플 데이터
	uv run python create_tables.py --with-samples

create-admin:  ## 👑 관리자 계정 생성
	uv run python create_admin.py

db-reset:  ## 🔄 데이터베이스 초기화 (주의: 모든 데이터 삭제!)
	uv run python -c "from app.core.database import Base, engine; Base.metadata.drop_all(bind=engine); print('🗑️ 모든 테이블 삭제 완료!')"
	uv run python create_tables.py

db-info:  ## 📊 데이터베이스 정보 확인
	uv run python -c "from app.core.config import settings; print(f'📍 Database: {settings.DATABASE_URL}'); print(f'🔧 Debug: {settings.DEBUG}')"

db-test:  ## 🔍 데이터베이스 연결 테스트
	uv run python -c "from app.core.database import engine; engine.connect().close(); print('✅ 데이터베이스 연결 성공!')"

# 🐳 도커 관리
docker-build:  ## 🏗️ 도커 이미지 빌드
	docker build -t chalna-api .

docker-run:  ## 🚀 도커 컨테이너 실행 (프로덕션)
	docker compose up -d

docker-dev:  ## 🛠️ 도커 개발 환경 실행 (로그 출력)
	docker compose up

docker-local:  ## 🛠️ 로컬 개발용 인프라만 실행 (DB + Redis)
	docker compose -f docker-compose.local.yml up -d

docker-local-logs:  ## 📋 로컬 개발용 도커 로그 확인
	docker compose -f docker-compose.local.yml logs -f

docker-local-stop:  ## ⏹️ 로컬 개발용 도커 컨테이너 중지
	docker compose -f docker-compose.local.yml down

docker-stop:  ## ⏹️ 도커 컨테이너 중지
	docker compose down

docker-clean:  ## 🧹 도커 리소스 정리
	docker compose down -v --remove-orphans
	docker compose -f docker-compose.local.yml down -v --remove-orphans
	docker system prune -f

docker-logs:  ## 📋 도커 로그 확인
	docker compose logs -f api

docker-shell:  ## 🐚 도커 컨테이너에 쉘 접속
	docker compose exec api /bin/bash

docker-admin:  ## 🛠️ PgAdmin 포함 전체 실행
	docker compose --profile admin up

dev-local:  ## 🚀 로컬 개발 환경 (인프라는 도커, 서버는 로컬)
	@echo "🐳 도커로 인프라 서비스 시작 중..."
	docker compose -f docker-compose.local.yml up -d
	@echo "⏳ 데이터베이스 준비 대기 중..."
	@sleep 10
	@echo "🚀 로컬 서버 시작..."
	uv run fastapi dev main.py

.DEFAULT_GOAL := help
