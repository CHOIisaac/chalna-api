"""
🎯 찰나(Chalna) API 설정 관리

환경 변수와 애플리케이션 설정을 관리합니다.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


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
    SECRET_KEY: str = "your-super-secret-key-here-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 🗃️ 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./chalna.db"  # 개발용 SQLite
    DATABASE_URL_ASYNC: Optional[str] = None
    
    # PostgreSQL 설정 (프로덕션용)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "chalna_db"
    POSTGRES_PORT: int = 5432
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        """
        PostgreSQL 연결 URL 생성
        """
        if isinstance(v, str) and v.startswith("postgresql"):
            return v
        
        # 개발 환경에서는 SQLite 사용
        if values.get("DEBUG", True):
            return "sqlite:///./chalna.db"
        
        # 프로덕션 환경에서는 PostgreSQL 사용
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    # 🌐 CORS 설정
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: List[str]) -> List[str]:
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
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 🔗 외부 API 설정
    KAKAO_API_KEY: Optional[str] = None
    NAVER_API_KEY: Optional[str] = None
    
    # 🎯 경조사 관련 설정
    DEFAULT_GIFT_AMOUNTS: dict = {
        "family": {"wedding": 100000, "funeral": 50000, "birthday": 30000},
        "friend": {"wedding": 50000, "funeral": 30000, "birthday": 20000},
        "colleague": {"wedding": 30000, "funeral": 20000, "birthday": 10000},
        "acquaintance": {"wedding": 20000, "funeral": 10000, "birthday": 5000},
    }
    
    # 🔔 알림 설정
    NOTIFICATION_DAYS_BEFORE: List[int] = [7, 3, 1]  # 며칠 전에 알림
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()

# 업로드 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True) 