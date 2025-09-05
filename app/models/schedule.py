"""
Schedule 모델 - 경조사 일정 관리
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.constants import EventType
from app.core.database import Base


class Schedule(Base):
    """경조사 일정 모델"""

    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # event_id = Column(Integer, ForeignKey("events.id"), comment="연관된 이벤트 ID")

    # 일정 기본 정보
    title = Column(String(200), nullable=False, comment="일정 제목")
    start_time = Column(DateTime, nullable=False, comment="시작 시간")
    end_time = Column(DateTime, comment="종료 시간")
    location = Column(String(500), comment="장소")

    # 일정 상세 정보
    description = Column(Text, comment="일정 설명")
    event_type = Column(String(50), comment="경조사 타입")
    memo = Column(Text, comment="메모")

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="schedules")
    # event = relationship("Event", back_populates="schedules")

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "description": self.description,
            "event_type": self.event_type,
            "memo": self.memo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_upcoming(self):
        """다가오는 일정인지 확인"""
        if not self.start_time:
            return False
        return self.start_time > datetime.now()

    @property
    def is_past(self):
        """과거 일정인지 확인"""
        if not self.start_time:
            return False
        return self.start_time < datetime.now()

    @property
    def is_today(self):
        """오늘 일정인지 확인"""
        if not self.start_time:
            return False
        today = datetime.now().date()
        return self.start_time.date() == today

    @property
    def days_until_schedule(self):
        """일정까지 남은 일수"""
        if not self.start_time:
            return None
        delta = self.start_time - datetime.now()
        return delta.days

    @property
    def should_send_notification(self):
        """알림을 보내야 하는지 확인"""
        if not self.user or not self.start_time:
            return False

        # 사용자가 알림을 받기로 설정했는지 확인
        if not self.user.should_receive_notifications():
            return False

        # 알림 시간이 지났는지 확인
        notification_time = self.notification_time
        if not notification_time:
            return False

        return notification_time <= datetime.now() < self.start_time

    @property
    def notification_time(self):
        """알림 시간 계산"""
        if not self.user or not self.start_time:
            return None

        return self.user.get_notification_time(self.start_time)

    @property
    def event_type_korean(self):
        """한국어 이벤트 타입"""
        try:
            return EventType(self.event_type).value
        except ValueError:
            return self.event_type

    @property
    def event_type_description(self):
        """이벤트 타입 설명"""
        from app.core.constants import EVENT_TYPE_DESCRIPTIONS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_DESCRIPTIONS.get(event_type, "설명 없음")
        except ValueError:
            return "설명 없음"

    @property
    def event_type_color(self):
        """이벤트 타입 색상"""
        from app.core.constants import EVENT_TYPE_COLORS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_COLORS.get(event_type, "#A9A9A9")
        except ValueError:
            return "#A9A9A9"

    @property
    def duration_minutes(self):
        """일정 지속 시간 (분)"""
        if not self.start_time or not self.end_time:
            return None

        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def is_long_event(self):
        """긴 일정인지 확인 (2시간 이상)"""
        duration = self.duration_minutes
        return duration and duration >= 120

    @staticmethod
    def get_today_schedules(user_id: int):
        """오늘 일정 조회"""
        from app.core.database import get_db

        db = next(get_db())

        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())

        return (
            db.query(Schedule)
            .filter(
                Schedule.user_id == user_id,
                Schedule.start_time >= start_of_day,
                Schedule.start_time <= end_of_day,
            )
            .order_by(Schedule.start_time)
            .all()
        )

    @staticmethod
    def get_upcoming_schedules(user_id: int, limit: int = 10):
        """다가오는 일정 조회"""
        from app.core.database import get_db

        db = next(get_db())

        return (
            db.query(Schedule)
            .filter(Schedule.user_id == user_id, Schedule.start_time > datetime.now())
            .order_by(Schedule.start_time)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_schedules_by_event_type(user_id: int, event_type: str):
        """특정 이벤트 타입의 일정 조회"""
        from app.core.database import get_db

        db = next(get_db())

        return (
            db.query(Schedule)
            .filter(Schedule.user_id == user_id, Schedule.event_type == event_type)
            .order_by(Schedule.start_time)
            .all()
        )
