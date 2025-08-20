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
	uv run python -c "from app.core.database import create_tables; create_tables(); print('✅ 테이블 생성 완료!')"

db-reset:  ## 🔄 데이터베이스 초기화 (주의: 모든 데이터 삭제!)
	uv run python -c "from app.core.database import reset_db; reset_db()"

db-info:  ## 📊 데이터베이스 정보 확인
	uv run python -c "from app.core.database import get_db_info; import json; print(json.dumps(get_db_info(), indent=2, ensure_ascii=False))"

db-test:  ## 🔍 데이터베이스 연결 테스트
	uv run python -c "from app.core.database import test_db_connection; print('✅ 연결 성공!' if test_db_connection() else '❌ 연결 실패!')"

# 🐳 도커 관리
docker-build:  ## 🏗️ 도커 이미지 빌드
	docker build -t chalna-api .

docker-run:  ## 🚀 도커 컨테이너 실행 (프로덕션)
	docker-compose up -d

docker-dev:  ## 🛠️ 도커 개발 환경 실행 (로그 출력)
	docker-compose up

docker-stop:  ## ⏹️ 도커 컨테이너 중지
	docker-compose down

docker-clean:  ## 🧹 도커 리소스 정리
	docker-compose down -v --remove-orphans
	docker system prune -f

docker-logs:  ## 📋 도커 로그 확인
	docker-compose logs -f api

docker-shell:  ## 🐚 도커 컨테이너에 쉘 접속
	docker-compose exec api /bin/bash

docker-admin:  ## 🛠️ PgAdmin 포함 전체 실행
	docker-compose --profile admin up

.DEFAULT_GOAL := help
