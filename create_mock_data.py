"""
목 데이터 생성 스크립트
현재 날짜부터 1년 전까지의 기간으로 일정, 장부, 알림 데이터를 생성합니다.
"""

import random
import calendar
from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.models.schedule import Schedule
from app.models.ledger import Ledger
from app.models.notification import Notification
from app.core.security import get_password_hash

# 샘플 데이터
NAMES = [
    "김민수", "박지영", "이철수", "최영희", "정민호", "한소영", "윤태호", "강미영",
    "조성민", "임수진", "오준호", "서현정", "배지훈", "신예린", "권동현", "문소희",
    "홍길동", "김영희", "박철수", "이미영", "최민수", "정지영", "한철수", "윤영희",
    "송민준", "강서연", "임도현", "박하늘", "정우진", "김나연", "이준호", "최수빈",
    "윤지훈", "한예린", "조민재", "오서윤", "배현우", "신지원", "권태민", "문채원",
    "김동현", "박서아", "이준영", "최민지", "정하늘", "한지우", "윤서준", "강예은"
]

RELATIONSHIPS = [
    "가족", "친구", "직장동료", "친척", "지인", "동기", "선배", "후배", "이웃",
]

EVENT_TYPES = [
    "결혼식", "장례식", "생일", "돌잔치", "졸업식", "정년퇴임", "개업식", "기념일", "기타"
]

EVENT_LOCATIONS = [
    "롯데호텔", "신라호텔", "그랜드하얏트", "웨딩홀", "교회", "절", "상조회관", "집",
    "컨벤션센터", "문화회관", "호텔", "레스토랑", "카페", "공원", "학교", "회사",
    "병원", "장례식장", "웨딩홀", "컨벤션홀", "스카이라운지", "가든파티", "야외", "실내"
]

MEMOS = [
    "축하합니다!", "건강하세요", "행복하세요", "고생하셨습니다", "감사합니다",
    "오래오래 행복하세요", "건강한 아이로 태어나길", "평안히 가세요",
    "즐거운 하루 되세요", "좋은 하루 보내세요", "건강하게 지내세요", "화이팅!",
    "응원합니다", "힘내세요", "좋은 일만 있으시길", "건강한 모습으로 뵙길",
    "항상 행복하세요", "좋은 결과 있으시길", "건강 관리 잘하세요", "성공하세요",
    None, None, None, None, None, None  # 더 많은 None 추가로 메모 없는 경우 증가
]

def create_mock_data():
    """목 데이터 생성"""
    # 매번 다른 랜덤 시드 설정
    random.seed()
    
    db = SessionLocal()
    
    try:
        # 사용자 조회 (ID 3 사용자 사용)
        user = db.query(User).filter(User.id == 3).first()
        if not user:
            print("ID 3인 사용자가 없습니다. 먼저 사용자를 생성해주세요.")
            return
        

        # 현재 날짜부터 1년 전까지의 기간 (과거) + 현재부터 3개월 후까지 (미래)
        end_date = datetime.now() + timedelta(days=90)  # 3개월 후
        start_date = datetime.now() - timedelta(days=365)  # 1년 전
        
        # 일정과 장부 데이터 생성
        schedules_created = 0
        ledgers_created = 0
        
        # 전체 기간에서 랜덤하게 일정 생성
        total_days = (end_date - start_date).days
        total_events = random.randint(50, 80)  # 총 50-80개 이벤트 (더 다양하게)
        
        for _ in range(total_events):
            # 전체 기간에서 랜덤한 날짜 선택
            random_days = random.randint(0, total_days)
            event_date = start_date + timedelta(days=random_days)
            
            # 이벤트 타입과 시간 설정
            event_type = random.choice(EVENT_TYPES)
            if event_type == "장례식":
                # 장례식은 아침 시간대
                event_time = time(random.randint(6, 10), random.choice([0, 15, 30, 45]))
            elif event_type == "결혼식":
                # 결혼식은 오후 시간대
                event_time = time(random.randint(12, 16), random.choice([0, 15, 30, 45]))
            elif event_type in ["생일", "돌잔치", "기념일"]:
                # 생일, 돌잔치, 기념일은 점심/저녁 시간대
                event_time = time(random.randint(11, 19), random.choice([0, 15, 30, 45]))
            else:
                # 기타 이벤트는 다양한 시간대
                event_time = time(random.randint(9, 18), random.choice([0, 15, 30, 45]))
            
            # 일정 생성
            counterparty_name = random.choice(NAMES)
            
            # 상태 결정: 과거는 completed, 미래는 upcoming
            today = datetime.now().date()
            event_date_only = event_date.date()
            
            if event_date_only < today:
                status = "completed"
            else:
                status = "upcoming"

            schedule = Schedule(
                user_id=user.id,
                title=f"{counterparty_name}의 {event_type}",
                event_type=event_type,
                event_date=event_date_only,
                event_time=event_time,
                location=random.choice(EVENT_LOCATIONS),
                status=status,
                memo=random.choice(MEMOS)
            )
            db.add(schedule)
            schedules_created += 1
            
            # 장부 생성 (일정과 연관) - 같은 상대방 이름 사용
            relationship_type = random.choice(RELATIONSHIPS)
            entry_type = random.choice(["given", "received"])
            
            # 금액 설정 (이벤트 타입별)
            if event_type == "결혼식":
                amount = random.choice([50000, 100000, 150000, 200000, 300000, 500000])
            elif event_type == "장례식":
                amount = random.choice([30000, 50000, 100000, 200000])
            elif event_type == "돌잔치":
                amount = random.choice([30000, 50000, 100000])
            elif event_type == "생일":
                amount = random.choice([10000, 20000, 30000, 50000])
            elif event_type == "졸업식":
                amount = random.choice([20000, 30000, 50000, 100000])
            elif event_type == "정년퇴임":
                amount = random.choice([50000, 100000, 150000, 200000])
            elif event_type == "개업식":
                amount = random.choice([30000, 50000, 100000, 150000])
            elif event_type == "기념일":
                amount = random.choice([10000, 20000, 30000, 50000])
            else:  # 기타
                amount = random.choice([10000, 20000, 30000, 50000, 100000])
            
            ledger = Ledger(
                user_id=user.id,
                counterparty_name=counterparty_name,
                relationship_type=relationship_type,
                amount=amount,
                event_type=event_type,
                event_date=event_date_only,
                entry_type=entry_type,
                memo=random.choice(MEMOS)
            )
            db.add(ledger)
            ledgers_created += 1
        
        # 다양한 알림 데이터 생성 (최근 30일간)
        notifications_created = 0
        
        # 알림 타입과 메시지 템플릿
        notification_templates = {
            "schedule": {
                "titles": ["일정 알림", "경조사 일정", "이벤트 알림", "일정 안내"],
                "messages": [
                    "{name}의 {event_type}이 {days}일 후에 있습니다.",
                    "{event_type} 일정이 {days}일 남았습니다.",
                    "{name}님의 {event_type}을 잊지 마세요!",
                    "{event_type} 일정이 다가왔습니다."
                ]
            },
            "ledger": {
                "titles": ["장부 기록", "경조사비 기록", "장부 알림", "기록 완료"],
                "messages": [
                    "{name}님의 {event_type}에 {amount}원을 기록했습니다.",
                    "{event_type} 경조사비가 기록되었습니다.",
                    "장부에 새로운 기록이 추가되었습니다.",
                    "{name}님과의 {event_type} 기록이 완료되었습니다."
                ]
            },
            "system": {
                "titles": ["시스템 알림", "앱 업데이트", "새로운 기능", "알림 설정"],
                "messages": [
                    "새로운 기능이 추가되었습니다.",
                    "앱이 업데이트되었습니다.",
                    "알림 설정을 확인해보세요.",
                    "데이터 백업이 완료되었습니다."
                ]
            }
        }
        
        # 최근 7일간 랜덤한 알림 생성
        notification_count = 7  # 7개의 알림 생성
        
        for _ in range(notification_count):
            # 랜덤한 날짜 (최근 7일 내)
            days_ago = random.randint(0, 7)
            notification_date = datetime.now() - timedelta(days=days_ago)
            
            # 알림 타입 선택
            notification_type = random.choice(["schedule", "ledger", "system"])
            template = notification_templates[notification_type]
            
            # 제목과 메시지 생성
            title = random.choice(template["titles"])
            message_template = random.choice(template["messages"])
            
            if notification_type == "schedule":
                # 일정 관련 알림
                name = random.choice(NAMES)
                event_type = random.choice(EVENT_TYPES)
                days = random.randint(1, 7)
                message = message_template.format(
                    name=name, 
                    event_type=event_type, 
                    days=days
                )
                event_date = notification_date.date() + timedelta(days=days)
                event_time = time(random.randint(9, 18), random.choice([0, 15, 30, 45]))
                location = random.choice(EVENT_LOCATIONS)
            elif notification_type == "ledger":
                # 장부 관련 알림
                name = random.choice(NAMES)
                event_type = random.choice(EVENT_TYPES)
                amount = random.choice([50000, 100000, 150000, 200000, 300000])
                message = message_template.format(
                    name=name, 
                    event_type=event_type, 
                    amount=f"{amount:,}"
                )
                event_date = notification_date.date()
                event_time = time(random.randint(9, 18), random.choice([0, 15, 30, 45]))
                location = random.choice(EVENT_LOCATIONS)
            else:
                # 시스템 알림
                message = message_template
                event_date = None
                event_time = None
                location = None
            
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                event_type=notification_type,
                read=random.choice([True, False, False, False]),  # 25% 확률로 읽음
                event_date=event_date,
                event_time=event_time,
                location=location,
                created_at=notification_date
            )
            db.add(notification)
            notifications_created += 1
        
        # 데이터베이스에 저장
        db.commit()
        
        print(f"목 데이터 생성 완료!")
        print(f"- 일정: {schedules_created}개")
        print(f"- 장부: {ledgers_created}개")
        print(f"- 알림: {notifications_created}개")
        
    except Exception as e:
        print(f"목 데이터 생성 중 오류 발생: {str(e)}")
        db.rollback()
    finally:
        db.close()

def clear_mock_data():
    """목 데이터 삭제"""
    db = SessionLocal()
    
    try:
        # 사용자 조회 (ID 3 사용자 사용)
        user = db.query(User).filter(User.id == 3).first()
        if not user:
            print("ID 3인 사용자가 없습니다.")
            return
        
        # 해당 사용자의 데이터 삭제
        db.query(Notification).filter(Notification.user_id == user.id).delete()
        db.query(Ledger).filter(Ledger.user_id == user.id).delete()
        db.query(Schedule).filter(Schedule.user_id == user.id).delete()
        
        db.commit()
        print("목 데이터가 삭제되었습니다.")
        
    except Exception as e:
        print(f"목 데이터 삭제 중 오류 발생: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and (sys.argv[1] == "clear" or sys.argv[1] == "--clear"):
        clear_mock_data()
    else:
        create_mock_data()
