"""
홈 화면용 API 엔드포인트
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ledger import Ledger
from app.models.schedule import Schedule

router = APIRouter()


@router.get("/monthly-stats", summary="이번 달 현황 조회", description="이번 달 총액, 증감률, 일정 개수, 완료율 조회")
async def get_monthly_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    이번 달 현황 조회
    
    - **total_amount**: 이번 달 총액 (원)
    - **total_amount_change**: 전월 대비 증감률 (%)
    - **event_count**: 이번 달 예정 일정 개수
    - **this_week_event_count**: 이번 주 예정 일정 개수
    - **completion_rate**: 이번 달 일정 완료율 (%)
    """
    try:
        # 날짜 계산 최적화 - 한 번만 계산
        now = datetime.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(seconds=1)
        this_month_end = (this_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        print(week_start.date())
        print(week_end)
        # 최적화: 단일 쿼리로 이번 달/전월 총액 조회 (나눈 것만) - 이벤트 날짜 기준
        amount_stats = db.query(
            func.sum(case(
                (and_(
                    Ledger.event_date >= this_month_start.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('this_month'),
            func.sum(case(
                (and_(
                    Ledger.event_date >= last_month_start.date(),
                    Ledger.event_date <= last_month_end.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('last_month')
        ).filter(Ledger.user_id == user_id).first()
        
        this_month_amount = amount_stats.this_month or 0
        last_month_amount = amount_stats.last_month or 0
        
        # 전월 대비 증감률 계산
        if last_month_amount > 0:
            total_amount_change = round(((this_month_amount - last_month_amount) / last_month_amount) * 100, 1)
        else:
            total_amount_change = 100.0 if this_month_amount > 0 else 0.0
        
        # 최적화: 단일 쿼리로 Schedule 통계 조회
        schedule_stats = db.query(
            func.count(case(
                (and_(
                    Schedule.event_date >= this_month_start.date(),
                    Schedule.event_date <= this_month_end.date()
                ), Schedule.id),
                else_=None
            )).label('this_month_total'),
            func.count(case(
                (and_(
                    Schedule.event_date >= this_month_start.date(),
                    Schedule.event_date <= this_month_end.date(),
                    Schedule.status == "completed"
                ), Schedule.id),
                else_=None
            )).label('this_month_completed'),
            func.count(case(
                (and_(
                    Schedule.event_date >= this_month_start.date(),
                    Schedule.event_date <= this_month_end.date(),
                    Schedule.status == "upcoming"
                ), Schedule.id),
                else_=None
            )).label('this_month_upcoming'),
            func.count(case(
                (and_(
                    Schedule.event_date >= week_start.date(),
                    Schedule.event_date <= week_end.date(),
                    Schedule.status == "upcoming"
                ), Schedule.id),
                else_=None
            )).label('this_week_total')
        ).filter(Schedule.user_id == user_id).first()
        
        event_count = schedule_stats.this_month_upcoming or 0  # 예정인 일정만 카운트
        this_week_event_count = schedule_stats.this_week_total or 0
        total_this_month_schedules = schedule_stats.this_month_total or 0
        completed_this_month_schedules = schedule_stats.this_month_completed or 0
        
        completion_rate = round((completed_this_month_schedules / total_this_month_schedules) * 100, 1) if total_this_month_schedules > 0 else 0.0
        
        return {
            "success": True,
            "data": {
                "total_amount": int(this_month_amount),
                "total_amount_change": total_amount_change,
                "event_count": event_count,
                "this_week_event_count": this_week_event_count,
                "completion_rate": completion_rate
            },
            "message": "이번 달 현황 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"월간 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/quick-stats", summary="퀵 스탯 조회", description="축의금, 조의금, 함께한 순간 통계 조회")
async def get_quick_stats(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    퀵 스탯 조회
    
    - **wedding_amount**: 축의금 총액 (원)
    - **wedding_change**: 축의금 전월 대비 증감률 (%)
    - **funeral_amount**: 조의금 총액 (원)
    - **funeral_change**: 조의금 전월 대비 증감률 (%)
    - **total_events**: 함께한 순간 총 건수
    - **total_events_change**: 함께한 순간 전월 대비 증감률 (건)
    - **avg_wedding_amount**: 평균 축의금 (원)
    - **avg_wedding_change**: 평균 축의금 전월 대비 증감률 (%)
    """
    try:
        # 날짜 계산 최적화 - 한 번만 계산
        now = datetime.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(seconds=1)
        
        # 최적화: 단일 쿼리로 축의금/조의금 통계 조회 (나눈 것만) - 이벤트 날짜 기준
        wedding_funeral_stats = db.query(
            func.sum(case(
                (and_(
                    Ledger.event_type != "장례식",
                    Ledger.event_date >= this_month_start.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('this_month_wedding'),
            func.sum(case(
                (and_(
                    Ledger.event_type != "장례식",
                    Ledger.event_date >= last_month_start.date(),
                    Ledger.event_date <= last_month_end.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('last_month_wedding'),
            func.sum(case(
                (and_(
                    Ledger.event_type == "장례식",
                    Ledger.event_date >= this_month_start.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('this_month_funeral'),
            func.sum(case(
                (and_(
                    Ledger.event_type == "장례식",
                    Ledger.event_date >= last_month_start.date(),
                    Ledger.event_date <= last_month_end.date(),
                    Ledger.entry_type == "given"
                ), Ledger.amount),
                else_=0
            )).label('last_month_funeral'),
            func.count(case(
                (and_(
                    Ledger.event_type != "장례식",
                    Ledger.event_date >= this_month_start.date(),
                    Ledger.entry_type == "given"
                ), Ledger.id),
                else_=None
            )).label('this_month_wedding_count'),
            func.count(case(
                (and_(
                    Ledger.event_type != "장례식",
                    Ledger.event_date >= last_month_start.date(),
                    Ledger.event_date <= last_month_end.date(),
                    Ledger.entry_type == "given"
                ), Ledger.id),
                else_=None
            )).label('last_month_wedding_count')
        ).filter(Ledger.user_id == user_id).first()
        
        this_month_wedding = wedding_funeral_stats.this_month_wedding or 0
        last_month_wedding = wedding_funeral_stats.last_month_wedding or 0
        this_month_funeral = wedding_funeral_stats.this_month_funeral or 0
        last_month_funeral = wedding_funeral_stats.last_month_funeral or 0
        this_month_wedding_count = wedding_funeral_stats.this_month_wedding_count or 0
        last_month_wedding_count = wedding_funeral_stats.last_month_wedding_count or 0
        
        # 최적화: 단일 쿼리로 Schedule 이벤트 통계 조회 (모든 일정)
        event_stats = db.query(
            func.count(case(
                (Schedule.event_date >= this_month_start.date(), Schedule.id),
                else_=None
            )).label('this_month_events'),
            func.count(case(
                (and_(
                    Schedule.event_date >= last_month_start.date(),
                    Schedule.event_date <= last_month_end.date()
                ), Schedule.id),
                else_=None
            )).label('last_month_events')
        ).filter(Schedule.user_id == user_id).first()
        
        this_month_events = event_stats.this_month_events or 0
        last_month_events = event_stats.last_month_events or 0
        
        # 증감률 계산
        wedding_change = round(((this_month_wedding - last_month_wedding) / last_month_wedding) * 100, 1) if last_month_wedding > 0 else (100.0 if this_month_wedding > 0 else 0.0)
        funeral_change = round(((this_month_funeral - last_month_funeral) / last_month_funeral) * 100, 1) if last_month_funeral > 0 else (100.0 if this_month_funeral > 0 else 0.0)
        total_events_change = this_month_events - last_month_events
        
        # 평균 축의금 계산
        avg_wedding_amount = round(this_month_wedding / this_month_wedding_count, 0) if this_month_wedding_count > 0 else 0
        avg_last_month_wedding = round(last_month_wedding / last_month_wedding_count, 0) if last_month_wedding_count > 0 else 0
        avg_wedding_change = round(((avg_wedding_amount - avg_last_month_wedding) / avg_last_month_wedding) * 100, 1) if avg_last_month_wedding > 0 else (100.0 if avg_wedding_amount > 0 else 0.0)
        
        return {
            "success": True,
            "data": {
                "wedding_amount": int(this_month_wedding),
                "wedding_change": wedding_change,
                "funeral_amount": int(this_month_funeral),
                "funeral_change": funeral_change,
                "total_events": this_month_events,
                "total_events_change": total_events_change,
                "avg_wedding_amount": int(avg_wedding_amount),
                "avg_wedding_change": avg_wedding_change
            },
            "message": "퀵 스탯 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"퀵 스탯 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/recent-ledgers", summary="최근 장부 조회", description="최근 장부 3개 조회")
async def get_recent_ledgers(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    최근 장부 3개 조회
    
    - **id**: 장부 ID
    - **name**: 상대방 이름
    - **relationship**: 관계
    - **amount**: 금액
    - **event_type**: 경조사 타입
    - **date**: 날짜
    - **type**: given/received
    - **memo**: 메모
    """
    try:
        # 최근 장부 3개 조회 (Ledger 모델에서 직접 조회)
        recent_ledgers = db.query(Ledger).filter(
            Ledger.user_id == user_id
        ).order_by(Ledger.event_date.desc()).limit(3).all()
        
        ledgers_data = []
        for ledger in recent_ledgers:
            ledgers_data.append({
                "id": ledger.id,
                "name": ledger.counterparty_name,
                "relationship_type": ledger.relationship_type,
                "amount": ledger.amount,
                "event_type": ledger.event_type,
                "event_date": ledger.event_date.isoformat() if ledger.event_date else None,
                "entry_type": ledger.entry_type,
                "memo": ledger.memo
            })
        
        return {
            "success": True,
            "data": ledgers_data,
            "message": "최근 장부 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최근 장부 조회 중 오류가 발생했습니다: {str(e)}")
