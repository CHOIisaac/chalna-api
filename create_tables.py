#!/usr/bin/env python3
"""
데이터베이스 테이블 생성 스크립트
"""
from app.core.database import engine, Base
from app.models import User, Event, Ledger, Schedule
from app.core.constants import EntryType

def create_tables():
    """모든 테이블 생성"""
    print("🗄️ 데이터베이스 테이블을 생성합니다...")
    
    # 모든 모델의 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
    print("\n📋 생성된 테이블:")
    print("- users (사용자)")
    print("- events (경조사 이벤트)")
    print("- ledgers (경조사비 수입지출 장부)")
    print("- schedules (경조사 일정)")
    
    # 테이블 정보 출력
    from sqlalchemy import inspect
    inspector = inspect(engine)
    
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        print(f"\n📊 {table_name} 테이블:")
        for column in columns:
            nullable = "NULL" if column['nullable'] else "NOT NULL"
            default = f" (기본값: {column['default']})" if column['default'] else ""
            print(f"  - {column['name']}: {column['type']} {nullable}{default}")

def create_sample_data():
    """샘플 데이터 생성"""
    print("\n🌱 샘플 데이터를 생성합니다...")
    
    from app.core.database import SessionLocal
    from datetime import datetime, timedelta, date
    
    db = SessionLocal()
    
    try:
        # 사용자 생성
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="테스트 사용자",
            phone="010-1234-5678",
            push_notification_enabled=True,
            notification_advance_hours=2
        )
        user.set_password("testpass123")
        db.add(user)
        db.commit()
        db.refresh(user)
        print("✅ 테스트 사용자 생성 완료")
        
        # 경조사 이벤트 생성
        event = Event(
            user_id=user.id,
            title="김철수 결혼식",
            event_type="결혼식",
            event_date=datetime.now() + timedelta(days=30),
            location="그랜드 호텔 3층 그랜드볼룸",
            description="대학 동기 김철수 결혼식",
            memo="축의금 10만원 준비"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        print("✅ 테스트 경조사 이벤트 생성 완료")
        
        # 경조사비 지출 기록
        expense_ledger = Ledger(
            user_id=user.id,
            amount=100000,
            entry_type=EntryType.EXPENSE,
            event_type="결혼식",
            event_name="김철수 결혼식",
            event_date=date.today() + timedelta(days=30),
            location="그랜드 호텔 3층 그랜드볼룸",
            counterparty_name="김철수",
            counterparty_phone="010-9876-5432",
            relationship_type="대학동기",
            memo="축의금 10만원"
        )
        db.add(expense_ledger)
        print("✅ 테스트 경조사비 지출 기록 생성 완료")
        
        # 경조사비 수입 기록 (돌잔치)
        income_ledger = Ledger(
            user_id=user.id,
            amount=50000,
            entry_type=EntryType.INCOME,
            event_type="돌잔치",
            event_name="내 돌잔치",
            event_date=date.today() - timedelta(days=10),
            location="우리집",
            counterparty_name="이민수",
            counterparty_phone="010-1111-2222",
            relationship_type="직장동료",
            memo="돌잔치 축하금"
        )
        db.add(income_ledger)
        print("✅ 테스트 경조사비 수입 기록 생성 완료")
        
        # 경조사 일정 생성
        schedule = Schedule(
            user_id=user.id,
            title="김철수 결혼식",
            start_time=datetime.now() + timedelta(days=30, hours=14),  # 오후 2시
            location="그랜드 호텔 3층 그랜드볼룸",
            event_id=event.id,
            event_type="결혼식",
            memo="축의금 10만원 준비, 정장 차림"
        )
        db.add(schedule)
        print("✅ 테스트 경조사 일정 생성 완료")
        
        # 장례식 일정도 추가
        funeral_schedule = Schedule(
            user_id=user.id,
            title="박영희 장례식",
            start_time=datetime.now() + timedelta(days=15, hours=10),  # 오전 10시
            location="서울추모공원",
            event_type="장례식",
            memo="조의금 5만원, 검은색 정장"
        )
        db.add(funeral_schedule)
        print("✅ 테스트 장례식 일정 생성 완료")
        
        db.commit()
        print("\n🎉 모든 샘플 데이터가 성공적으로 생성되었습니다!")
        
    except Exception as e:
        print(f"❌ 샘플 데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--with-samples":
        create_tables()
        create_sample_data()
    else:
        create_tables()
        print("\n💡 샘플 데이터도 생성하려면: python create_tables.py --with-samples")
