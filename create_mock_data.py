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
    "홍길동", "김영희", "박철수", "이미영", "최민수", "정지영", "한철수", "윤영희"
]

RELATIONSHIPS = [
    "가족", "친구", "직장동료", "친척", "지인", "동기", "선배", "후배", "이웃"
]

EVENT_TYPES = [
    "결혼식", "출산", "돌잔치", "생일", "장례식", "기타"
]

EVENT_LOCATIONS = [
    "롯데호텔", "신라호텔", "그랜드하얏트", "웨딩홀", "교회", "절", "상조회관", "집"
]

MEMOS = [
    "축하합니다!", "건강하세요", "행복하세요", "고생하셨습니다", "감사합니다",
    "오래오래 행복하세요", "건강한 아이로 태어나길", "평안히 가세요",
    "즐거운 하루 되세요", "좋은 하루 보내세요", None, None, None
]

def create_mock_data():
    """목 데이터 생성"""
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
        total_events = random.randint(45, 60)  # 총 45-60개 이벤트
        
        for _ in range(total_events):
            # 전체 기간에서 랜덤한 날짜 선택
            random_days = random.randint(0, total_days)
            event_date = start_date + timedelta(days=random_days)
            
            # 이벤트 타입과 시간 설정
            event_type = random.choice(EVENT_TYPES)
            if event_type == "장례식":
                event_time = time(random.randint(6, 10), random.choice([0, 30]))
            else:
                event_time = time(random.randint(10, 18), random.choice([0, 30]))
            
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
            elif event_type == "출산":
                amount = random.choice([30000, 50000, 100000, 150000])
            elif event_type == "돌잔치":
                amount = random.choice([30000, 50000, 100000])
            elif event_type == "생일":
                amount = random.choice([10000, 20000, 30000, 50000])
            elif event_type == "장례식":
                amount = random.choice([30000, 50000, 100000, 200000])
            else:
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
        
        # 최근 7일간의 일정 알림 데이터 생성
        notifications_created = 0
        
        # 최근 7일간의 일정들을 조회하여 알림 생성 (과거 + 미래)
        recent_schedules = db.query(Schedule).filter(
            Schedule.user_id == user.id,
            Schedule.event_date >= (datetime.now() - timedelta(days=7)).date(),
            Schedule.event_date <= (datetime.now() + timedelta(days=7)).date()
        ).all()
        
        for schedule in recent_schedules:
            # 일정에 대한 알림 생성
            title = f"{schedule.event_type}"
            message = f"{schedule.title}이 있습니다."
            
            notification = Notification(
                user_id=user.id,
                title=title,
                message=message,
                event_type="schedule",
                read=random.choice([True, False]),
                event_date=schedule.event_date,
                event_time=schedule.event_time,
                location=schedule.location,
                created_at=schedule.event_date  # 일정 날짜로 생성일 설정
            )
            db.add(notification)
            notifications_created += 1
        
        # 일정이 부족하면 추가 알림 생성
        if notifications_created < 7:
            for i in range(7 - notifications_created):
                notification_date = datetime.now() - timedelta(days=i)
                
                title = f"{schedule.event_type}"
                message = f"{schedule.title}이 있습니다."
                
                notification = Notification(
                    user_id=user.id,
                    title=title,
                    message=message,
                    event_type="schedule",
                    read=random.choice([True, False]),
                    event_date=notification_date.date(),
                    event_time=time(random.randint(10, 18), random.choice([0, 30])),
                    location=random.choice(EVENT_LOCATIONS),
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
