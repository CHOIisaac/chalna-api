#!/usr/bin/env python3
"""
관리자 계정 생성 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user():
    """관리자 계정 생성"""
    print("🔐 관리자 계정을 생성합니다...")
    
    db = SessionLocal()
    
    try:
        # 기존 관리자 계정 확인
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("⚠️ 관리자 계정이 이미 존재합니다.")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            return
        
        # 관리자 계정 생성
        admin_user = User(
            username="admin",
            email="admin@chalna.com",
            full_name="관리자",
            phone="010-0000-0000",
            is_active=True,
            is_verified=True,
            push_notification_enabled=True,
            notification_advance_hours=2
        )
        
        # 비밀번호 설정
        admin_user.set_password("admin123")
        
        # 데이터베이스에 저장
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ 관리자 계정이 성공적으로 생성되었습니다!")
        print(f"   Username: {admin_user.username}")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: admin123")
        print(f"   ID: {admin_user.id}")
        
    except Exception as e:
        print(f"❌ 관리자 계정 생성 실패: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
