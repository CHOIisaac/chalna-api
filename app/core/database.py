"""
🗃️ 데이터베이스 연결 및 세션 관리

SQLAlchemy를 사용한 데이터베이스 설정
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    # PostgreSQL 연결 풀 설정
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    echo=settings.DEBUG,  # 개발 환경에서 SQL 쿼리 로깅
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 생성
Base = declarative_base()

# 메타데이터 설정
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 주입
    
    Yields:
        Session: 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    데이터베이스 테이블 생성
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    데이터베이스 테이블 삭제 (개발용)
    """
    Base.metadata.drop_all(bind=engine)


# 데이터베이스 초기화 함수
def init_db():
    """
    데이터베이스 초기화
    """
    # 테이블 생성
    create_tables()
    
    # 초기 데이터 삽입 (필요한 경우)
    db = SessionLocal()
    try:
        # 여기에 초기 데이터 삽입 로직 추가
        # 예: 관리자 계정 생성, 기본 카테고리 생성 등
        pass
    finally:
        db.close()


# 데이터베이스 연결 테스트
def test_db_connection():
    """
    데이터베이스 연결 테스트
    
    Returns:
        bool: 연결 성공 여부
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return False


# 개발용 데이터베이스 리셋 함수
def reset_db():
    """
    개발용 데이터베이스 리셋
    주의: 모든 데이터가 삭제됩니다!
    """
    if settings.DEBUG:
        drop_tables()
        create_tables()
        print("🔄 데이터베이스가 리셋되었습니다.")
    else:
        print("⚠️  프로덕션 환경에서는 데이터베이스 리셋이 허용되지 않습니다.")


# 데이터베이스 상태 확인
def get_db_info():
    """
    데이터베이스 정보 조회
    
    Returns:
        dict: 데이터베이스 정보
    """
    return {
        "database_url": settings.DATABASE_URL,
        "engine": str(engine.url),
        "is_connected": test_db_connection(),
        "tables": list(Base.metadata.tables.keys()),
    } 