"""
👤 사용자 모델

경조사 관리 앱의 사용자 정보를 관리합니다.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class UserStatus(enum.Enum):
    """사용자 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    """
    사용자 모델
    """
    __tablename__ = "users"
    
    # 🔑 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 👤 개인 정보
    full_name = Column(String(100), nullable=False)
    nickname = Column(String(50), index=True)
    phone = Column(String(20))
    birth_date = Column(DateTime)
    
    # 🏠 주소 정보
    address = Column(Text)
    city = Column(String(50))
    region = Column(String(50))  # 시/도
    
    # 🎯 앱 설정
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    # 🔔 알림 설정
    notification_enabled = Column(Boolean, default=True)
    email_notification = Column(Boolean, default=True)
    sms_notification = Column(Boolean, default=False)
    
    # 📱 앱 사용 설정
    language = Column(String(10), default="ko")
    timezone = Column(String(50), default="Asia/Seoul")
    currency = Column(String(10), default="KRW")
    
    # 📊 통계 정보
    total_events = Column(Integer, default=0)
    total_gifts_given = Column(Integer, default=0)
    total_gifts_received = Column(Integer, default=0)
    
    # 🕐 타임스탬프
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # 🔗 관계 설정
    # 내가 생성한 이벤트들
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    
    # 내가 기록한 경조사비들
    ceremonial_money_given = relationship("CeremonialMoney", back_populates="user", cascade="all, delete-orphan")
    
    # 내가 생성한 일정들
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"
    
    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "nickname": self.nickname,
            "phone": self.phone,
            "city": self.city,
            "region": self.region,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "status": self.status.value if self.status else None,
            "language": self.language,
            "timezone": self.timezone,
            "currency": self.currency,
            "total_events": self.total_events,
            "total_gifts_given": self.total_gifts_given,
            "total_gifts_received": self.total_gifts_received,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
        }
    
    @property
    def is_premium(self):
        """프리미엄 사용자 여부 (추후 구현)"""
        return False
    
    @property
    def gift_balance(self):
        """선물 수지 (받은 것 - 준 것)"""
        return self.total_gifts_received - self.total_gifts_given
    
    def update_stats(self, db):
        """통계 정보 업데이트"""
        from app.models.event import Event
        from app.models.ceremonial_money import CeremonialMoney
        
        # 이벤트 수 업데이트
        self.total_events = db.query(Event).filter(Event.user_id == self.id).count()
        
        # 경조사비 통계 업데이트
        ceremonial_money_given = db.query(CeremonialMoney).filter(CeremonialMoney.giver_id == self.id).count()
        ceremonial_money_received = db.query(CeremonialMoney).filter(CeremonialMoney.receiver_id == self.id).count()
        
        self.total_gifts_given = ceremonial_money_given
        self.total_gifts_received = ceremonial_money_received
        
        db.commit() 