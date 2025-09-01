#!/usr/bin/env python3
"""
🗄️ 데이터베이스 테이블 생성 스크립트

찰나(Chalna) API의 모든 테이블을 생성합니다.
"""

import sys
import os
from sqlalchemy import create_engine, text

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import Base, engine
from app.models import User, Event, CeremonialMoney, Schedule  # 모든 모델 임포트


def create_database_if_not_exists():
    """데이터베이스가 없으면 생성"""
    try:
        # PostgreSQL의 경우 데이터베이스 생성 확인
        if settings.DATABASE_URL.startswith("postgresql"):
            # 기본 postgres 데이터베이스에 연결
            admin_url = settings.DATABASE_URL.replace(f"/{settings.POSTGRES_DB}", "/postgres")
            admin_engine = create_engine(admin_url)
            
            with admin_engine.connect() as conn:
                # 자동 커밋 모드로 설정
                conn = conn.execution_options(autocommit=True)
                
                # 데이터베이스 존재 확인
                result = conn.execute(text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ), {"db_name": settings.POSTGRES_DB})
                
                if not result.fetchone():
                    print(f"🗄️ 데이터베이스 '{settings.POSTGRES_DB}' 생성 중...")
                    conn.execute(text(f'CREATE DATABASE "{settings.POSTGRES_DB}"'))
                    print(f"✅ 데이터베이스 '{settings.POSTGRES_DB}' 생성 완료")
                else:
                    print(f"📋 데이터베이스 '{settings.POSTGRES_DB}' 이미 존재")
            
            admin_engine.dispose()
        
    except Exception as e:
        print(f"⚠️ 데이터베이스 생성 확인 중 오류: {e}")
        print("🔄 계속 진행합니다...")


def create_all_tables():
    """모든 테이블 생성"""
    try:
        print("🏗️ 데이터베이스 테이블 생성 시작...")
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
        
        # 생성된 테이블 목록 출력
        print("\n📋 생성된 테이블 목록:")
        with engine.connect() as conn:
            if settings.DATABASE_URL.startswith("postgresql"):
                result = conn.execute(text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
                ))
            else:  # SQLite
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ))
            
            tables = result.fetchall()
            for table in tables:
                print(f"  📄 {table[0]}")
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {e}")
        return False
    
    return True


def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        print("🔌 데이터베이스 연결 테스트 중...")
        
        with engine.connect() as conn:
            if settings.DATABASE_URL.startswith("postgresql"):
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ PostgreSQL 연결 성공: {version.split(',')[0]}")
            else:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.fetchone()[0]
                print(f"✅ SQLite 연결 성공: 버전 {version}")
            
            return True
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False


def create_sample_data():
    """샘플 데이터 생성 (선택적)"""
    try:
        from sqlalchemy.orm import sessionmaker
        from app.core.security import get_password_hash
        from datetime import datetime
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("🌱 샘플 데이터 생성 중...")
        
        # 샘플 사용자 생성
        if not db.query(User).filter(User.email == "admin@chalna.com").first():
            admin_user = User(
                email="admin@chalna.com",
                hashed_password=get_password_hash("admin123"),
                full_name="관리자",
                nickname="어드민",
                is_active=True,
                is_verified=True
            )
            db.add(admin_user)
            db.commit()
            print("👤 관리자 계정 생성 완료: admin@chalna.com / admin123")
        
        # 테스트 사용자 생성
        if not db.query(User).filter(User.email == "test@chalna.com").first():
            test_user = User(
                email="test@chalna.com",
                hashed_password=get_password_hash("test123"),
                full_name="테스트 사용자",
                nickname="테스터",
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            print("👤 테스트 계정 생성 완료: test@chalna.com / test123")
        
        db.close()
        print("✅ 샘플 데이터 생성 완료")
        
    except Exception as e:
        print(f"⚠️ 샘플 데이터 생성 중 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🎯 찰나(Chalna) API 데이터베이스 초기화")
    print("=" * 50)
    
    # 현재 설정 정보 출력
    print(f"📍 데이터베이스 URL: {settings.DATABASE_URL}")
    print(f"🔧 디버그 모드: {settings.DEBUG}")
    print("")
    
    # 1. 데이터베이스 연결 테스트
    if not test_connection():
        print("❌ 데이터베이스 연결에 실패했습니다. 설정을 확인해주세요.")
        sys.exit(1)
    
    # 2. 데이터베이스 생성 (PostgreSQL인 경우)
    create_database_if_not_exists()
    
    # 3. 테이블 생성
    if not create_all_tables():
        print("❌ 테이블 생성에 실패했습니다.")
        sys.exit(1)
    
    # 4. 샘플 데이터 생성 (선택적)
    if len(sys.argv) > 1 and sys.argv[1] == "--with-samples":
        create_sample_data()
    else:
        print("\n💡 샘플 데이터를 생성하려면 '--with-samples' 옵션을 사용하세요:")
        print("   python create_tables.py --with-samples")
    
    print("\n🎉 데이터베이스 초기화가 완료되었습니다!")
    print("\n🚀 이제 FastAPI 서버를 시작할 수 있습니다:")
    print("   uv run fastapi dev main.py")
    print("   또는")
    print("   make dev")


if __name__ == "__main__":
    main()
