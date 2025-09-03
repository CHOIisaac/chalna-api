"""
User 모델 - 사용자 정보 관리
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

from app.core.database import Base

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="사용자명")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="이메일")
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")
    full_name = Column(String(100), nullable=False, comment="실명")
    phone = Column(String(20), comment="전화번호")
    
    # 사용자 상태
    is_active = Column(Boolean, default=True, comment="활성 상태")
    is_verified = Column(Boolean, default=False, comment="이메일 인증 상태")
    
    # 알림 설정 (사용자 전체)
    push_notification_enabled = Column(Boolean, default=True, comment="푸시 알림 활성화")
    notification_advance_hours = Column(Integer, default=2, comment="알림 시간 (시간 단위, 기본값: 2시간 전)")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    ceremonial_money_given = relationship("CeremonialMoney", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        """비밀번호 해싱"""
        self.hashed_password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(password, self.hashed_password)

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "push_notification_enabled": self.push_notification_enabled,
            "notification_advance_hours": self.notification_advance_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_stats(self):
        """사용자 통계 업데이트"""
        # 경조사비 통계
        total_given = sum(money.amount for money in self.ceremonial_money_given)
        total_events = len(self.events)
        total_schedules = len(self.schedules)
        
        return {
            "total_given": total_given,
            "total_events": total_events,
            "total_schedules": total_schedules
        }

    def should_receive_notifications(self) -> bool:
        """알림을 받아야 하는지 확인"""
        return self.is_active and self.push_notification_enabled

    def get_notification_time(self, schedule_start_time):
        """일정에 대한 알림 시간 계산"""
        if not schedule_start_time or not self.push_notification_enabled:
            return None
        
        from datetime import timedelta
        return schedule_start_time - timedelta(hours=self.notification_advance_hours) 