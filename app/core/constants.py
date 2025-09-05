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

    INCOME = "income"  # 수입
    EXPENSE = "expense"  # 지출


class ScheduleType(str, Enum):
    """일정 타입"""

    CEREMONIAL = "ceremonial"  # 경조사
    PERSONAL = "personal"  # 개인
    WORK = "work"  # 업무


class NotificationType(str, Enum):
    """알림 타입"""

    PUSH = "push"  # 푸시 알림
    EMAIL = "email"  # 이메일
    SMS = "sms"  # SMS


# 이벤트 타입별 설명
EVENT_TYPE_DESCRIPTIONS = {
    EventType.WEDDING: "신랑신부의 결혼식을 축하하는 행사",
    EventType.FUNERAL: "고인의 장례를 치르는 행사",
    EventType.BIRTHDAY: "생일을 축하하는 행사",
    EventType.FIRST_BIRTHDAY: "아기의 첫 번째 생일을 축하하는 행사",
    EventType.GRADUATION: "졸업을 축하하는 행사",
    EventType.RETIREMENT: "정년퇴임을 축하하는 행사",
    EventType.OPENING: "새로운 사업이나 시설의 개업을 축하하는 행사",
    EventType.ANNIVERSARY: "특별한 기념일을 축하하는 행사",
    EventType.OTHER: "기타 경조사 행사",
}

# 이벤트 타입별 기본 색상 (UI에서 사용)
EVENT_TYPE_COLORS = {
    EventType.WEDDING: "#FF6B6B",  # 빨간색
    EventType.FUNERAL: "#4ECDC4",  # 청록색
    EventType.BIRTHDAY: "#45B7D1",  # 파란색
    EventType.FIRST_BIRTHDAY: "#96CEB4",  # 초록색
    EventType.GRADUATION: "#FFEAA7",  # 노란색
    EventType.RETIREMENT: "#DDA0DD",  # 보라색
    EventType.OPENING: "#FF8C42",  # 주황색
    EventType.ANNIVERSARY: "#FF69B4",  # 분홍색
    EventType.OTHER: "#A9A9A9",  # 회색
}

# 이벤트 타입별 기본 축의금/조의금 금액 (참고용)
EVENT_TYPE_DEFAULT_AMOUNTS = {
    EventType.WEDDING: 100000,  # 10만원
    EventType.FUNERAL: 50000,  # 5만원
    EventType.BIRTHDAY: 30000,  # 3만원
    EventType.FIRST_BIRTHDAY: 50000,  # 5만원
    EventType.GRADUATION: 20000,  # 2만원
    EventType.RETIREMENT: 50000,  # 5만원
    EventType.OPENING: 50000,  # 5만원
    EventType.ANNIVERSARY: 30000,  # 3만원
    EventType.OTHER: 30000,  # 3만원
}
