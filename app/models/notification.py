"""
알림 모델
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Time, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Notification(Base):
    """알림 모델"""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False)  # "schedule", "ledger", "system", "reminder" 등
    read = Column(Boolean, default=False, nullable=False)
    event_date = Column(Date, nullable=True)  # 알림과 관련된 날짜
    event_time = Column(Time, nullable=True)  # 알림과 관련된 시간
    location = Column(String(255), nullable=True)  # 장소 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # 관계 설정
    user = relationship("User", back_populates="notifications")
    
    def to_dict(self):
        """딕셔너리로 변환"""
        return {
            "id": str(self.id),
            "title": self.title,
            "message": self.message,
            "time": self.created_at.strftime("%H:%M") if self.created_at else "",
            "type": self.event_type,
            "read": self.read,
            "date": self.event_date.isoformat() if self.event_date else "",
            "location": self.location or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else ""
        }
