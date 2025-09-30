"""
Schedule API - 경조사 일정 관리 (MVP)
"""

from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, extract, and_, case

from app.core.constants import StatusType
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.schedule import Schedule
from app.schemas.schedule import (
    DailySchedule,
    ScheduleCreate,
    ScheduleQuickAdd,
    ScheduleResponse,
    ScheduleSummary,
    ScheduleUpdate,
    WeeklySchedule,
)

router = APIRouter(tags=["일정 관리"])


@router.post(
    "/",
    summary="일정 생성",
    description="새로운 경조사 일정을 생성합니다.",
)
def create_schedule(
    schedule: ScheduleCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """새로운 일정 생성"""

    # 기본값 설정
    schedule_data = schedule.dict()
    schedule_data['user_id'] = current_user_id

    # status가 없으면 기본값 설정
    if 'status' not in schedule_data or not schedule_data['status']:
        schedule_data['status'] = StatusType.UPCOMING

    db_schedule = Schedule(**schedule_data)

    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return {
        "success": True,
        "data": db_schedule,  # ✅ 직접 반환 (최고 성능)
        "message": "일정이 생성되었습니다."
    }


@router.get(
    "/{schedule_id}",
    summary="일정 상세 조회",
    description="특정 일정의 상세 정보를 조회합니다.",
)
def get_schedule(
    schedule_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """일정 상세 조회"""

    schedule = (
        db.query(Schedule)
        .filter(Schedule.id == schedule_id, Schedule.user_id == current_user_id)
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    return {
        "success": True,
        "data": schedule  # ✅ 직접 반환 (최고 성능)
    }


@router.put(
    "/{schedule_id}",
    summary="일정 수정",
    description="기존 일정을 수정합니다.",
)
def update_schedule(
        schedule_id: int,
        schedule_update: ScheduleUpdate,
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """일정 수정"""

    db_schedule = (
        db.query(Schedule)
        .filter(Schedule.id == schedule_id, Schedule.user_id == current_user_id)
        .first()
    )

    if not db_schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    # 업데이트 데이터 적용
    update_data = schedule_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)

    return {
        "success": True,
        "data": db_schedule,  # ✅ 직접 반환 (최고 성능)
        "message": "일정이 수정되었습니다."
    }


@router.delete("/{schedule_id}", summary="일정 삭제", description="일정을 삭제합니다.")
def delete_schedule(
        schedule_id: int,
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """일정 삭제"""

    db_schedule = (
        db.query(Schedule)
        .filter(Schedule.id == schedule_id, Schedule.user_id == current_user_id)
        .first()
    )

    if not db_schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    db.delete(db_schedule)
    db.commit()

    return {
        "success": True,
        "message": "일정이 삭제되었습니다."
    }


@router.get("/", summary="일정 목록 조회 (필터링 지원)")
def get_schedules(
        # 기본 파라미터
        skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
        limit: int = Query(10, ge=1, le=100, description="가져올 항목 수"),

        # 필터링 파라미터 (프론트엔드 필터와 매칭)
        status: Optional[str] = Query(None, description="상태: upcoming, completed"),
        event_type: Optional[str] = Query(None, description="경조사 타입: 결혼식, 장례식, 돌잔치, 개업식"),
        sort_by: str = Query("latest", description="정렬: latest(최신순), oldest(오래된순)"),
        search: Optional[str] = Query(None, description="제목/장소 검색"),

        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """일정 목록 조회 - 필터링 완전 지원"""

    # 기본 쿼리 (user 관계 로딩 불필요 - 성능 최적화)
    query = (
        db.query(Schedule)
        .filter(Schedule.user_id == current_user_id)
    )

    # 🔍 상태 필터링
    if status == "upcoming":
        query = query.filter(Schedule.status == StatusType.UPCOMING)
    elif status == "completed":
        query = query.filter(Schedule.status == StatusType.COMPLETED)

    # 🎭 경조사 타입 필터링
    if event_type and event_type != "전체":
        query = query.filter(Schedule.event_type == event_type)

    # 🔍 검색
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Schedule.title.ilike(search_pattern),
                Schedule.location.ilike(search_pattern)
            )
        )

    # 📊 정렬
    if sort_by == "latest" or sort_by == "date_asc":
        query = query.order_by(Schedule.event_date.asc(), Schedule.event_time.asc())
    else:  # oldest
        query = query.order_by(Schedule.event_date.desc(), Schedule.event_time.desc())

    # 총 개수 및 페이징
    total_count = query.count()
    schedules = query.offset(skip).limit(limit).all()

    # 이번 달 통계 계산 (최적화: 단일 쿼리)
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    
    # 단일 쿼리로 모든 통계 계산
    stats_result = db.query(
        func.count(Schedule.id).label('total_count'),
        func.sum(case(
            (Schedule.status == StatusType.UPCOMING, 1),
            else_=0
        )).label('upcoming_count')
    ).filter(
        and_(
            Schedule.user_id == current_user_id,
            Schedule.event_date >= this_month_start
        )
    ).first()
    
    this_month_total_count = stats_result.total_count or 0
    this_month_upcoming_count = stats_result.upcoming_count or 0

    return {
        "success": True,
        "data": schedules,  # ✅ 직접 반환 (최고 성능)
        "meta": {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "has_next": (skip + limit) < total_count,
            "filters_applied": {
                "status": status,
                "event_type": event_type,
                "sort_by": sort_by,
                "search": search
            }
        },
        "this_month_stats": {
            "this_month_total_count": this_month_total_count,
            "this_month_upcoming_count": this_month_upcoming_count
        }
    }


@router.get("/filters/options", summary="필터 옵션 목록")
def get_filter_options(
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """프론트엔드 필터 드롭다운용 옵션들"""

    # 상태별 개수
    status_counts = (
        db.query(
            Schedule.status,
            func.count(Schedule.id).label('count')
        )
        .filter(Schedule.user_id == current_user_id)
        .group_by(Schedule.status)
        .all()
    )

    # 경조사 타입별 개수
    event_type_counts = (
        db.query(
            Schedule.event_type,
            func.count(Schedule.id).label('count')
        )
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.event_type.isnot(None)
        )
        .group_by(Schedule.event_type)
        .all()
    )

    total_count = sum(s.count for s in status_counts)

    return {
        "success": True,
        "data": {
            "status_options": [
                {"value": "", "label": "전체", "count": total_count},
                {"value": "upcoming", "label": "예정",
                 "count": next((s.count for s in status_counts if s.status == StatusType.UPCOMING), 0)},
                {"value": "completed", "label": "완료",
                 "count": next((s.count for s in status_counts if s.status == StatusType.COMPLETED), 0)},
            ],
            "event_type_options": [
                                      {"value": "", "label": "전체", "count": total_count}
                                  ] + [
                                      {"value": etc.event_type, "label": etc.event_type, "count": etc.count}
                                      for etc in event_type_counts
                                  ],
            "sort_options": [
                {"value": "latest", "label": "최신순"},
                {"value": "oldest", "label": "오래된순"}
            ]
        }
    }


@router.get("/quick/upcoming", summary="예정된 일정 빠른 조회")
def get_upcoming_quick(
        limit: int = Query(5, ge=1, le=20),
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """홈 대시보드용 - 예정된 일정만 빠르게"""

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.status == StatusType.UPCOMING
        )
        .order_by(Schedule.event_date.asc(), Schedule.event_time.asc())
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "data": schedules  # ✅ 직접 반환 (최고 성능)
    }


@router.get("/quick/today", summary="오늘 일정 빠른 조회")
def get_today_quick(
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """오늘 일정만 빠르게"""

    today = datetime.now().date()

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.event_date == today
        )
        .order_by(Schedule.event_time.asc())
        .all()
    )

    return {
        "success": True,
        "data": schedules  # ✅ 직접 반환 (최고 성능)
    }


@router.get("/stats/summary", summary="일정 통계 요약 (최적화)")
def get_schedule_stats(
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """대시보드용 통계 정보 (한 번의 쿼리로 모든 통계 조회)"""

    # 🚀 단일 쿼리로 모든 통계를 한 번에 조회 (성능 최적화)
    this_month_start = datetime.now().replace(day=1).date()
    next_month_start = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date()
    
    # 조건별 집계를 한 번의 쿼리로 처리
    stats_result = (
        db.query(
            func.count(Schedule.id).label('total'),
            func.sum(func.case(
                (Schedule.status == StatusType.UPCOMING, 1),
                else_=0
            )).label('upcoming'),
            func.sum(func.case(
                (Schedule.status == StatusType.COMPLETED, 1), 
                else_=0
            )).label('completed'),
            func.sum(func.case(
                ((Schedule.event_date >= this_month_start) & 
                 (Schedule.event_date < next_month_start), 1),
                else_=0
            )).label('this_month')
        )
        .filter(Schedule.user_id == current_user_id)
        .first()
    )
    
    # 결과 추출 (None 방지)
    total_count = stats_result.total or 0
    upcoming_count = int(stats_result.upcoming or 0)
    completed_count = int(stats_result.completed or 0)
    this_month_count = int(stats_result.this_month or 0)

    return {
        "success": True,
        "data": {
            "total": total_count,
            "upcoming": upcoming_count,
            "completed": completed_count,
            "this_month": this_month_count
        }
    }


@router.get("/calendar/monthly", summary="월별 일정 달력 데이터 (최적화)")
def get_monthly_calendar(
    year: int = Query(..., description="연도 (예: 2025)"),
    month: int = Query(..., ge=1, le=12, description="월 (1-12)"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """월별 달력 표시용 - 날짜별 일정 개수와 함께 (인덱스 최적화)"""
    
    # 🚀 인덱스 최적화: 날짜 범위로 필터링 (extract 대신 범위 사용)
    try:
        # 해당 월의 시작일과 마지막일 계산
        month_start = datetime(year, month, 1).date()
        if month == 12:
            month_end = datetime(year + 1, 1, 1).date()
        else:
            month_end = datetime(year, month + 1, 1).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 년/월 값입니다")
    
    # 인덱스를 활용한 범위 쿼리로 성능 최적화
    calendar_data = (
        db.query(
            Schedule.event_date,
            func.count(Schedule.id).label('count')
        )
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.event_date >= month_start,
            Schedule.event_date < month_end
        )
        .group_by(Schedule.event_date)
        .order_by(Schedule.event_date)  # 정렬 추가로 일관성 보장
        .all()
    )
    
    # 날짜별 데이터 정리
    calendar_dates = []
    for date_record in calendar_data:
        calendar_dates.append({
            "date": date_record.event_date.strftime("%Y-%m-%d"),
            "count": date_record.count,
            "has_schedules": True
        })
    
    return {
        "success": True,
        "data": {
            "year": year,
            "month": month,
            "dates": calendar_dates
        }
    }


@router.get("/calendar/daily", summary="특정 날짜 일정 목록 (최적화)")
def get_daily_schedules(
    date: str = Query(..., description="조회할 날짜 (YYYY-MM-DD)"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """특정 날짜의 모든 일정 조회 - 시간순 정렬 (N+1 쿼리 방지)"""
    
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)"
        )
    
    # 🚀 인덱스 최적화 (user 데이터 불필요하므로 제거)
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.event_date == target_date
        )
        .order_by(Schedule.event_time.asc())
        .all()
    )
    
    return {
        "success": True,
        "data": {
            "date": date,
            "schedules": schedules,  # ✅ 직접 반환 (최고 성능)
            "total_count": len(schedules)
        }
    }