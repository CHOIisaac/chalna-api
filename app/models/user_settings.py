from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class UserSettings(Base):
    """사용자 설정 모델 - 미니멀 버전"""

    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # 알림 설정
    notifications_enabled = Column(Boolean, nullable=False, default=True, comment="전체 알림 켜기/끄기")
    event_reminders = Column(Boolean, nullable=False, default=True, comment="일정 알림")
    reminder_hours_before = Column(Integer, nullable=False, default=24, comment="몇 시간 전에 알림")

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="settings")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notifications_enabled": self.notifications_enabled,
            "event_reminders": self.event_reminders,
            "reminder_hours_before": self.reminder_hours_before,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_default_settings(cls, user_id: int):
        """기본 설정으로 사용자 설정 생성"""
        return cls(
            user_id=user_id,
            notifications_enabled=True,
            event_reminders=True,
            reminder_hours_before=24,
        )