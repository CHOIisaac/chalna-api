# 🐳 찰나(Chalna) API 도커 이미지
# 멀티스테이지 빌드로 최적화된 이미지 생성

# ========================================
# 🏗️ Stage 1: 의존성 설치 (Builder)
# ========================================
FROM python:3.11-slim as builder

# 메타데이터
LABEL maintainer="CHOIisaac <your.email@example.com>"
LABEL description="찰나(Chalna) - 경조사 관리 API"
LABEL version="0.1.0"

# 환경변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 Python 패키지 관리자)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY pyproject.toml uv.lock ./

# 의존성 설치 (프로덕션용)
RUN uv sync --frozen --no-dev --no-install-project

# ========================================
# 🚀 Stage 2: 프로덕션 이미지 (Runtime)
# ========================================
FROM python:3.11-slim

# 환경변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 앱 사용자 생성 (보안)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 작업 디렉토리 설정
WORKDIR /app

# 빌더 스테이지에서 가상환경 복사
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# 애플리케이션 코드 복사
COPY --chown=appuser:appuser . .

# 업로드 디렉토리 권한 설정
RUN mkdir -p uploads && chown -R appuser:appuser uploads

# 헬스체크 스크립트 추가
COPY --chown=appuser:appuser <<EOF /app/healthcheck.py
#!/usr/bin/env python3
"""도커 헬스체크 스크립트"""
import sys
import urllib.request
import urllib.error

try:
    with urllib.request.urlopen("http://localhost:8000/health", timeout=10) as response:
        if response.status == 200:
            sys.exit(0)
        else:
            sys.exit(1)
except urllib.error.URLError:
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

# 사용자 전환
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python /app/healthcheck.py

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
