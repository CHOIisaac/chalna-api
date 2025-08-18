# 🚀 찰나(Chalna) API - 개발 편의 명령어

.PHONY: help install dev prod test lint format clean

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

.DEFAULT_GOAL := help
