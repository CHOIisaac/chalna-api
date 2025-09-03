"""
Schedule 모델 - 경조사 일정 관리 (MVP)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Schedule(Base):
    """경조사 일정 모델"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False, comment="일정 제목")
    start_time = Column(DateTime, nullable=False, comment="시작 시간")
    location = Column(String(500), comment="위치 (경조사 장소)")
    event_id = Column(Integer, ForeignKey("events.id"), comment="경조사 ID (선택적)")
    event_type = Column(String(50), comment="경조사 타입 (결혼식, 장례식 등)")
    memo = Column(Text, comment="간단한 메모")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="schedules")
    event = relationship("Event", back_populates="schedules")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "location": self.location,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "memo": self.memo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_today(self):
        """오늘 일정인지 확인"""
        if not self.start_time:
            return False
        today = datetime.now().date()
        return self.start_time.date() == today

    @property
    def is_upcoming(self):
        """앞으로의 일정인지 확인"""
        if not self.start_time:
            return False
        now = datetime.now()
        return self.start_time > now

    @property
    def is_overdue(self):
        """지난 일정인지 확인"""
        if not self.start_time:
            return False
        now = datetime.now()
        return self.start_time < now

    @property
    def should_send_notification(self):
        """알림을 보내야 하는지 확인"""
        if not self.user or not self.start_time:
            return False
        
        # 사용자 알림 설정 확인
        if not self.user.should_receive_notifications():
            return False
        
        # 알림 시간 계산
        notification_time = self.user.get_notification_time(self.start_time)
        if not notification_time:
            return False
        
        now = datetime.now()
        # 알림 시간이 지났고, 시작 시간이 아직 지나지 않았을 때
        return notification_time <= now < self.start_time

    @property
    def notification_time(self):
        """알림 시간 계산 (사용자 설정 기반)"""
        if not self.user or not self.start_time:
            return None
        return self.user.get_notification_time(self.start_time)

    @staticmethod
    def get_schedule_statistics(user_id: int):
        """사용자의 일정 통계 반환"""
        from app.core.database import get_db
        db = next(get_db())
        
        total = db.query(Schedule).filter(Schedule.user_id == user_id).count()
        today = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            func.date(Schedule.start_time) == func.date(func.now())
        ).count()
        upcoming = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.start_time > func.now()
        ).count()
        
        return {
            "total": total,
            "today": today,
            "upcoming": upcoming
        }
