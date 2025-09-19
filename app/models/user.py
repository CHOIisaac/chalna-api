"""
User 모델 - 사용자 정보 관리
"""

from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(50), unique=True, index=True, nullable=False, comment="사용자명"
    )
    email = Column(
        String(100), unique=True, index=True, nullable=False, comment="이메일"
    )
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")
    full_name = Column(String(100), nullable=False, comment="실명")
    phone = Column(String(20), comment="전화번호")

    # 사용자 상태
    is_active = Column(Boolean, default=True, comment="활성 상태")
    is_verified = Column(Boolean, default=False, comment="이메일 인증 상태")


    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    ledgers = relationship(
        "Ledger", back_populates="user", cascade="all, delete-orphan"
    )
    schedules = relationship(
        "Schedule", back_populates="user", cascade="all, delete-orphan"
    )
    settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan", uselist=False)  # 추가

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_stats(self):
        """사용자 통계 업데이트"""
        # 장부 통계
        total_income = sum(ledger.amount for ledger in self.ledgers if ledger.is_income)
        total_expense = sum(
            ledger.amount for ledger in self.ledgers if ledger.is_expense
        )
        total_events = len(self.events)
        total_schedules = len(self.schedules)

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "total_events": total_events,
            "total_schedules": total_schedules,
        }

    def should_receive_notifications(self) -> bool:
        """알림을 받아야 하는지 확인"""
        if not self.is_active:
            return False

        # UserSettings에서 알림 설정 확인
        if self.settings:
            return self.settings.notifications_enabled

        return True  # 설정이 없으면 기본적으로 알림 받음

    def get_notification_time(self, schedule_start_time):
        """일정에 대한 알림 시간 계산"""
        if not schedule_start_time or not self.should_receive_notifications():
            return None

        from datetime import timedelta

        # UserSettings에서 알림 시간 가져오기
        hours_before = 24  # 기본값
        if self.settings:
            hours_before = self.settings.reminder_hours_before

        return schedule_start_time - timedelta(hours=hours_before)