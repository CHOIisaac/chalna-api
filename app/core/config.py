"""
🎯 찰나(Chalna) API 설정 관리

환경 변수와 애플리케이션 설정을 관리합니다.
"""

import os
from typing import Optional

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    """

    # 🚀 프로젝트 기본 정보
    PROJECT_NAME: str = "찰나(Chalna)"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "인간관계 중심의 경조사 관리 API"
    DEBUG: bool = True

    # 🔐 보안 설정
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 🗃️ 데이터베이스 설정
    DATABASE_URL: str = (
        "postgresql://chalna_user:chalna_password@localhost:5434/chalna"  # 로컬 개발용
    )
    DATABASE_URL_ASYNC: Optional[str] = None

    # PostgreSQL 설정
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_HOST: str  # 로컬 개발용
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """
        PostgreSQL 연결 URL 생성
        """
        if isinstance(v, str) and v.startswith("postgresql"):
            return v

        # 개발/프로덕션 모두 PostgreSQL 사용
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery 설정
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "Asia/Seoul"
    CELERY_ENABLE_UTC: bool = False

    # 알림 설정 - 스케줄 기반 알림 시간
    SCHEDULE_NOTIFICATION_DAYS: list[int] = [3, 1]  # 3일 전, 1일 전
    SCHEDULE_NOTIFICATION_HOURS: list[int] = [3]    # 3시간 전

    @validator("CELERY_BROKER_URL", pre=True)
    def assemble_celery_broker(cls, v: Optional[str], values: dict) -> str:
        """Celery Broker URL 생성"""
        if isinstance(v, str) and v.startswith("redis://"):
            return v

        redis_host = values.get("REDIS_HOST", "localhost")
        redis_port = values.get("REDIS_PORT", 6379)
        redis_db = values.get("REDIS_DB", 0)
        return f"redis://{redis_host}:{redis_port}/{redis_db}"

    @validator("CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_result_backend(cls, v: Optional[str], values: dict) -> str:
        """Celery Result Backend URL 생성"""
        if isinstance(v, str) and v.startswith("redis://"):
            return v

        redis_host = values.get("REDIS_HOST", "localhost")
        redis_port = values.get("REDIS_PORT", 6379)
        redis_db = values.get("REDIS_DB", 0)
        return f"redis://{redis_host}:{redis_port}/{redis_db}"

    # 🌐 서버 설정
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 🌐 CORS 설정
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"
    )

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: list[str]) -> list[str]:
        """
        CORS 오리진 설정
        """
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # 🤖 AI 설정
    OPENAI_API_KEY: Optional[str] = None

    # 📧 이메일 설정 (선택사항)
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # 📂 파일 업로드 설정
    UPLOAD_DIR: str = "./uploads"
    UPLOAD_PATH: str = "/app/uploads"  # Docker 컨테이너용 경로
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,pdf,doc,docx"

    # 🔗 외부 API 설정
    KAKAO_API_KEY: Optional[str] = None
    KAKAO_CLIENT_ID: Optional[str] = None
    KAKAO_CLIENT_SECRET: Optional[str] = None
    KAKAO_REDIRECT_URI: Optional[str] = None
    NAVER_API_KEY: Optional[str] = None

    # 🔴 Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # 📝 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # 🔒 보안 설정
    FORCE_HTTPS: bool = False
    TRUSTED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"

    # 🏥 헬스체크 설정
    ENABLE_HEALTHCHECK: bool = True
    ENABLE_METRICS: bool = True

    # 🌍 다국어 설정
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_TIMEZONE: str = "Asia/Seoul"

    # 🎯 경조사 관련 설정
    DEFAULT_GIFT_AMOUNTS: dict = {
        "family": {"wedding": 100000, "funeral": 50000, "birthday": 30000},
        "friend": {"wedding": 50000, "funeral": 30000, "birthday": 20000},
        "colleague": {"wedding": 30000, "funeral": 20000, "birthday": 10000},
        "acquaintance": {"wedding": 20000, "funeral": 10000, "birthday": 5000},
    }

    # 🔔 알림 설정
    NOTIFICATION_DAYS_BEFORE: list[int] = [7, 3, 1]  # 며칠 전에 알림

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()

# 업로드 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
