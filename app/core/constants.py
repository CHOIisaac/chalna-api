"""
공통 상수 정의
"""

from enum import Enum


class EventType(str, Enum):
    """경조사 이벤트 타입"""

    WEDDING = "결혼식"
    FUNERAL = "장례식"
    BIRTHDAY = "생일"
    FIRST_BIRTHDAY = "돌잔치"
    GRADUATION = "졸업식"
    RETIREMENT = "정년퇴임"
    OPENING = "개업식"
    ANNIVERSARY = "기념일"
    OTHER = "기타"


class EntryType(str, Enum):
    """장부 기록 타입"""

    GIVEN = "given"      # 준 금액
    RECEIVED = "received"  # 받은 금액


class RelationshipType(str, Enum):
    """관계 타입"""

    FAMILY = "가족"
    FRIEND = "친구"
    COLLEAGUE = "직장동료"
    ACQUAINTANCE = "지인"
    NEIGHBOR = "이웃"
    RELATIVE = "친척"
    TEACHER = "선생님"
    OTHER = "기타"


class ScheduleType(str, Enum):
    """일정 타입"""

    CEREMONIAL = "ceremonial"  # 경조사
    PERSONAL = "personal"  # 개인
    WORK = "work"  # 업무


class StatusType(str, Enum):
    """상태 타입"""

    PENDING = "예정"
    COMPLETED = "완료"


class NotificationType(str, Enum):
    """알림 타입"""

    PUSH = "push"  # 푸시 알림
    EMAIL = "email"  # 이메일
    SMS = "sms"  # SMS
