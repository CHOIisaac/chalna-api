"""
📅 일정 모델

사용자의 개인 일정, 할 일, 리마인더 등을 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ScheduleType(enum.Enum):
    """일정 타입"""
    PERSONAL = "personal"           # 개인 일정
    WORK = "work"                   # 업무 일정
    STUDY = "study"                 # 학습 일정
    HEALTH = "health"               # 건강 관련
    SOCIAL = "social"               # 사회 활동
    OTHER = "other"                 # 기타


class SchedulePriority(enum.Enum):
    """일정 우선순위"""
    LOW = "low"                     # 낮음
    MEDIUM = "medium"               # 보통
    HIGH = "high"                   # 높음
    URGENT = "urgent"               # 긴급


class ScheduleStatus(enum.Enum):
    """일정 상태"""
    PENDING = "pending"             # 대기
    IN_PROGRESS = "in_progress"     # 진행중
    COMPLETED = "completed"         # 완료
    CANCELLED = "cancelled"         # 취소


class Schedule(Base):
    """
    일정 모델
    """
    __tablename__ = "schedules"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 📝 일정 정보
    title = Column(String(200), nullable=False, comment="일정 제목")
    description = Column(Text, comment="일정 상세 설명")
    schedule_type = Column(Enum(ScheduleType), nullable=False, default=ScheduleType.PERSONAL)
    
    # 📅 시간 정보
    start_time = Column(DateTime, nullable=False, comment="시작 시간")
    end_time = Column(DateTime, comment="종료 시간")
    all_day = Column(Boolean, default=False, comment="종일 일정 여부")
    
    # 🎯 우선순위 및 상태
    priority = Column(Enum(SchedulePriority), default=SchedulePriority.MEDIUM)
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.PENDING)
    
    # 🔔 알림 설정
    reminder_enabled = Column(Boolean, default=True, comment="알림 사용 여부")
    reminder_time = Column(DateTime, comment="알림 시간")
    reminder_type = Column(String(50), default="push", comment="알림 타입 (push, email, sms)")
    
    # 📍 위치 정보
    location = Column(String(200), comment="장소")
    
    # 🔗 관련 정보
    event_id = Column(Integer, ForeignKey("events.id"), comment="관련 경조사 이벤트")
    
    # 🏷️ 태그 및 분류
    tags = Column(String(500), comment="태그 (쉼표로 구분)")
    category = Column(String(100), comment="카테고리")
    
    # 🔄 반복 설정
    is_recurring = Column(Boolean, default=False, comment="반복 일정 여부")
    recurrence_rule = Column(String(200), comment="반복 규칙 (RRULE 형식)")
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 🔗 관계 설정
    user = relationship("User", back_populates="schedules")
    event = relationship("Event", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, title={self.title}, start_time={self.start_time})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "schedule_type": self.schedule_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "all_day": self.all_day,
            "priority": self.priority.value,
            "status": self.status.value,
            "reminder_enabled": self.reminder_enabled,
            "reminder_time": self.reminder_time,
            "reminder_type": self.reminder_type,
            "location": self.location,
            "event_id": self.event_id,
            "tags": self.tags,
            "category": self.category,
            "is_recurring": self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @property
    def duration_minutes(self):
        """일정 지속 시간 (분)"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def is_overdue(self):
        """일정이 지났는지 확인"""
        if self.status == ScheduleStatus.COMPLETED:
            return False
        return self.start_time < func.now()
    
    @property
    def is_today(self):
        """오늘 일정인지 확인"""
        from datetime import date
        return self.start_time.date() == date.today()
    
    @property
    def is_upcoming(self):
        """다가오는 일정인지 확인"""
        from datetime import datetime, timedelta
        now = datetime.now()
        future = now + timedelta(days=7)
        return self.start_time > now and self.start_time <= future
    
    def get_formatted_time(self):
        """포맷된 시간 문자열 반환"""
        if self.all_day:
            return f"{self.start_time.strftime('%Y-%m-%d')} (종일)"
        elif self.end_time:
            return f"{self.start_time.strftime('%Y-%m-%d %H:%M')} ~ {self.end_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"{self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def get_priority_color(self):
        """우선순위별 색상 반환"""
        colors = {
            SchedulePriority.LOW: "#28a745",      # 초록
            SchedulePriority.MEDIUM: "#ffc107",   # 노랑
            SchedulePriority.HIGH: "#fd7e14",     # 주황
            SchedulePriority.URGENT: "#dc3545"    # 빨강
        }
        return colors.get(self.priority, "#6c757d")
    
    @staticmethod
    def get_schedule_statistics(user_id: int, db):
        """사용자의 일정 통계"""
        total_schedules = db.query(Schedule).filter(Schedule.user_id == user_id).count()
        completed_schedules = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.status == ScheduleStatus.COMPLETED
        ).count()
        overdue_schedules = db.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.status.in_([ScheduleStatus.PENDING, ScheduleStatus.IN_PROGRESS]),
            Schedule.start_time < func.now()
        ).count()
        
        return {
            "total_schedules": total_schedules,
            "completed_schedules": completed_schedules,
            "overdue_schedules": overdue_schedules,
            "completion_rate": (completed_schedules / total_schedules * 100) if total_schedules > 0 else 0
        }
