#!/usr/bin/env python3
"""
📅 일정 테이블 생성 스크립트

데이터베이스에 일정 관련 테이블을 생성합니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.schedule import Schedule, ScheduleType, SchedulePriority, ScheduleStatus
from app.models.user import User
from app.models.event import Event
from app.models.ceremonial_money import CeremonialMoney

def create_schedule_tables():
    """일정 테이블 생성"""
    print("📅 일정 테이블을 생성합니다...")
    
    try:
        # 일정 테이블 생성
        Schedule.__table__.create(engine, checkfirst=True)
        print("✅ 일정 테이블이 성공적으로 생성되었습니다!")
        
        # 기존 테이블들도 확인
        User.__table__.create(engine, checkfirst=True)
        Event.__table__.create(engine, checkfirst=True)
        CeremonialMoney.__table__.create(engine, checkfirst=True)
        print("✅ 모든 테이블이 준비되었습니다!")
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류가 발생했습니다: {e}")
        return False
    
    return True

def drop_schedule_tables():
    """일정 테이블 삭제 (개발용)"""
    print("🗑️ 일정 테이블을 삭제합니다...")
    
    try:
        Schedule.__table__.drop(engine, checkfirst=True)
        print("✅ 일정 테이블이 삭제되었습니다!")
        
    except Exception as e:
        print(f"❌ 테이블 삭제 중 오류가 발생했습니다: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="일정 테이블 관리")
    parser.add_argument("--drop", action="store_true", help="테이블 삭제")
    
    args = parser.parse_args()
    
    if args.drop:
        drop_schedule_tables()
    else:
        create_schedule_tables()
        
        print("\n🎉 일정 기능이 준비되었습니다!")
        print("📋 사용 가능한 API 엔드포인트:")
        print("  - GET    /api/v1/schedules/          - 일정 목록 조회")
        print("  - GET    /api/v1/schedules/today     - 오늘 일정 조회")
        print("  - GET    /api/v1/schedules/upcoming  - 다가오는 일정 조회")
        print("  - GET    /api/v1/schedules/calendar/daily  - 일별 캘린더")
        print("  - GET    /api/v1/schedules/calendar/weekly - 주별 캘린더")
        print("  - GET    /api/v1/schedules/summary   - 일정 요약")
        print("  - POST   /api/v1/schedules/          - 새 일정 생성")
        print("  - POST   /api/v1/schedules/quick     - 빠른 일정 생성")
        print("  - GET    /api/v1/schedules/{id}      - 특정 일정 조회")
        print("  - PUT    /api/v1/schedules/{id}      - 일정 수정")
        print("  - DELETE /api/v1/schedules/{id}      - 일정 삭제")
        print("  - PATCH  /api/v1/schedules/{id}/status - 상태 변경")
