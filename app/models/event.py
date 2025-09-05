"""
Event 모델 - 경조사 이벤트 관리
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.constants import EventType
from app.core.database import Base


class Event(Base):
    """경조사 이벤트 모델"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 이벤트 기본 정보
    title = Column(String(200), nullable=False, comment="이벤트 제목")
    event_type = Column(String(50), nullable=False, comment="이벤트 타입")
    event_date = Column(DateTime, nullable=False, comment="이벤트 날짜")
    location = Column(String(500), comment="이벤트 장소")

    # 이벤트 상세 정보
    description = Column(Text, comment="이벤트 설명")
    memo = Column(Text, comment="메모")
    is_external = Column(Boolean, default=False, comment="외부 이벤트 여부")

    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    user = relationship("User", back_populates="events")
    # ledgers = relationship(
    #     "Ledger", back_populates="event", cascade="all, delete-orphan"
    # )
    # schedules = relationship(
    #     "Schedule", back_populates="event", cascade="all, delete-orphan"
    # )

    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "location": self.location,
            "description": self.description,
            "memo": self.memo,
            "is_external": self.is_external,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

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
    def default_amount(self):
        """기본 축의금/조의금 금액"""
        from app.core.constants import EVENT_TYPE_DEFAULT_AMOUNTS

        try:
            event_type = EventType(self.event_type)
            return EVENT_TYPE_DEFAULT_AMOUNTS.get(event_type, 30000)
        except ValueError:
            return 30000

    @property
    def is_upcoming(self):
        """다가오는 이벤트인지 확인"""
        if not self.event_date:
            return False
        return self.event_date > datetime.now()

    @property
    def days_until_event(self):
        """이벤트까지 남은 일수"""
        if not self.event_date:
            return None
        delta = self.event_date - datetime.now()
        return delta.days

    @staticmethod
    def get_events_by_type(user_id: int, event_type: str):
        """특정 타입의 이벤트 조회"""
        from app.core.database import get_db

        db = next(get_db())

        return (
            db.query(Event)
            .filter(Event.user_id == user_id, Event.event_type == event_type)
            .order_by(Event.event_date)
            .all()
        )

    @staticmethod
    def get_upcoming_events(user_id: int, limit: int = 10):
        """다가오는 이벤트 조회"""
        from app.core.database import get_db

        db = next(get_db())

        return (
            db.query(Event)
            .filter(Event.user_id == user_id, Event.event_date > datetime.now())
            .order_by(Event.event_date)
            .limit(limit)
            .all()
        )
