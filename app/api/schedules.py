"""
📅 일정 API 라우터

일정 관리 엔드포인트 (할 일, 리마인더, 캘린더 연동)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, extract, func
from typing import List, Optional
from datetime import datetime, date, timedelta
import calendar

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schedule import Schedule, ScheduleType, SchedulePriority, ScheduleStatus
from app.models.user import User
from app.models.event import Event

from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleInDB,
    ScheduleSummary, DailySchedule, WeeklySchedule, ScheduleQuickAdd
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[ScheduleResponse],
    summary="📅 일정 목록 조회",
    description="사용자의 모든 일정을 조회합니다. 타입, 우선순위, 상태별 필터링과 검색을 지원합니다."
)
async def get_schedules(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    schedule_type: Optional[ScheduleType] = None,
    priority: Optional[SchedulePriority] = None,
    status: Optional[ScheduleStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """📅 일정 목록 조회"""
    query = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(Schedule.user_id == current_user.id)
    
    # 필터 적용
    if schedule_type:
        query = query.filter(Schedule.schedule_type == schedule_type)
    
    if priority:
        query = query.filter(Schedule.priority == priority)
    
    if status:
        query = query.filter(Schedule.status == status)
    
    if start_date:
        query = query.filter(Schedule.start_time >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(Schedule.start_time <= datetime.combine(end_date, datetime.max.time()))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Schedule.title.ilike(search_pattern),
                Schedule.description.ilike(search_pattern),
                Schedule.location.ilike(search_pattern),
                Schedule.tags.ilike(search_pattern)
            )
        )
    
    # 최신 순으로 정렬
    schedules = query.order_by(Schedule.start_time.desc()).offset(skip).limit(limit).all()
    
    # 응답 데이터 구성
    result = []
    for schedule in schedules:
        schedule_data = ScheduleResponse.from_orm(schedule)
        
        # 계산된 필드 추가
        schedule_data.duration_minutes = schedule.duration_minutes
        schedule_data.is_overdue = schedule.is_overdue
        schedule_data.is_today = schedule.is_today
        schedule_data.is_upcoming = schedule.is_upcoming
        schedule_data.formatted_time = schedule.get_formatted_time()
        schedule_data.priority_color = schedule.get_priority_color()
        
        # 이벤트 정보 추가
        if schedule.event:
            schedule_data.event_title = schedule.event.title
        
        result.append(schedule_data)
    
    return result


@router.get(
    "/today",
    response_model=List[ScheduleResponse],
    summary="📅 오늘 일정 조회",
    description="오늘 예정된 모든 일정을 조회합니다."
)
async def get_today_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📅 오늘 일정 조회"""
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    
    schedules = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time >= start_of_day,
        Schedule.start_time <= end_of_day
    ).order_by(Schedule.start_time).all()
    
    result = []
    for schedule in schedules:
        schedule_data = ScheduleResponse.from_orm(schedule)
        schedule_data.duration_minutes = schedule.duration_minutes
        schedule_data.is_overdue = schedule.is_overdue
        schedule_data.is_today = schedule.is_today
        schedule_data.is_upcoming = schedule.is_upcoming
        schedule_data.formatted_time = schedule.get_formatted_time()
        schedule_data.priority_color = schedule.get_priority_color()
        
        if schedule.event:
            schedule_data.event_title = schedule.event.title
        
        result.append(schedule_data)
    
    return result


@router.get(
    "/upcoming",
    response_model=List[ScheduleResponse],
    summary="📅 다가오는 일정 조회",
    description="지정된 기간 내에 예정된 일정들을 조회합니다."
)
async def get_upcoming_schedules(
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """📅 다가오는 일정 조회"""
    now = datetime.now()
    future_date = now + timedelta(days=days)
    
    schedules = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time > now,
        Schedule.start_time <= future_date,
        Schedule.status != ScheduleStatus.COMPLETED
    ).order_by(Schedule.start_time).all()
    
    result = []
    for schedule in schedules:
        schedule_data = ScheduleResponse.from_orm(schedule)
        schedule_data.duration_minutes = schedule.duration_minutes
        schedule_data.is_overdue = schedule.is_overdue
        schedule_data.is_today = schedule.is_today
        schedule_data.is_upcoming = schedule.is_upcoming
        schedule_data.formatted_time = schedule.get_formatted_time()
        schedule_data.priority_color = schedule.get_priority_color()
        
        if schedule.event:
            schedule_data.event_title = schedule.event.title
        
        result.append(schedule_data)
    
    return result


@router.get(
    "/calendar/daily",
    response_model=DailySchedule,
    summary="📅 일별 캘린더 조회",
    description="특정 날짜의 모든 일정을 캘린더 형태로 조회합니다."
)
async def get_daily_calendar(
    target_date: date = Query(..., description="조회할 날짜"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📅 일별 캘린더 조회"""
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    schedules = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time >= start_of_day,
        Schedule.start_time <= end_of_day
    ).order_by(Schedule.start_time).all()
    
    # 응답 데이터 구성
    schedule_responses = []
    for schedule in schedules:
        schedule_data = ScheduleResponse.from_orm(schedule)
        schedule_data.duration_minutes = schedule.duration_minutes
        schedule_data.is_overdue = schedule.is_overdue
        schedule_data.is_today = schedule.is_today
        schedule_data.is_upcoming = schedule.is_upcoming
        schedule_data.formatted_time = schedule.get_formatted_time()
        schedule_data.priority_color = schedule.get_priority_color()
        
        if schedule.event:
            schedule_data.event_title = schedule.event.title
        
        schedule_responses.append(schedule_data)
    
    completed_count = sum(1 for s in schedules if s.status == ScheduleStatus.COMPLETED)
    
    return DailySchedule(
        date=target_date,
        schedules=schedule_responses,
        total_count=len(schedules),
        completed_count=completed_count
    )


@router.get(
    "/calendar/weekly",
    response_model=WeeklySchedule,
    summary="📅 주별 캘린더 조회",
    description="특정 주의 모든 일정을 일별로 그룹화하여 조회합니다."
)
async def get_weekly_calendar(
    week_start: date = Query(..., description="주 시작일"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📅 주별 캘린더 조회"""
    week_end = week_start + timedelta(days=6)
    start_of_week = datetime.combine(week_start, datetime.min.time())
    end_of_week = datetime.combine(week_end, datetime.max.time())
    
    # 주간 일정 조회
    weekly_schedules = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time >= start_of_week,
        Schedule.start_time <= end_of_week
    ).order_by(Schedule.start_time).all()
    
    # 일별로 그룹화
    daily_schedules = []
    total_schedules = 0
    completed_schedules = 0
    
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())
        
        # 해당 날짜의 일정
        day_schedules = [s for s in weekly_schedules if day_start <= s.start_time <= day_end]
        
        # 응답 데이터 구성
        schedule_responses = []
        for schedule in day_schedules:
            schedule_data = ScheduleResponse.from_orm(schedule)
            schedule_data.duration_minutes = schedule.duration_minutes
            schedule_data.is_overdue = schedule.is_overdue
            schedule_data.is_today = schedule.is_today
            schedule_data.is_upcoming = schedule.is_upcoming
            schedule_data.formatted_time = schedule.get_formatted_time()
            schedule_data.priority_color = schedule.get_priority_color()
            
            if schedule.event:
                schedule_data.event_title = schedule.event.title
            
            schedule_responses.append(schedule_data)
        
        completed_count = sum(1 for s in day_schedules if s.status == ScheduleStatus.COMPLETED)
        daily_schedules.append(DailySchedule(
            date=current_date,
            schedules=schedule_responses,
            total_count=len(day_schedules),
            completed_count=completed_count
        ))
        
        total_schedules += len(day_schedules)
        completed_schedules += completed_count
    
    return WeeklySchedule(
        week_start=week_start,
        week_end=week_end,
        daily_schedules=daily_schedules,
        total_schedules=total_schedules,
        completed_schedules=completed_schedules
    )


@router.get(
    "/summary",
    response_model=ScheduleSummary,
    summary="📊 일정 요약 조회",
    description="사용자의 일정 현황을 요약하여 보여줍니다."
)
async def get_schedule_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """📊 일정 요약 조회"""
    # 기본 통계
    total_schedules = db.query(Schedule).filter(Schedule.user_id == current_user.id).count()
    completed_schedules = db.query(Schedule).filter(
        Schedule.user_id == current_user.id,
        Schedule.status == ScheduleStatus.COMPLETED
    ).count()
    
    overdue_schedules = db.query(Schedule).filter(
        Schedule.user_id == current_user.id,
        Schedule.status.in_([ScheduleStatus.PENDING, ScheduleStatus.IN_PROGRESS]),
        Schedule.start_time < datetime.now()
    ).count()
    
    # 오늘 일정
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_schedules = db.query(Schedule).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time >= today_start,
        Schedule.start_time <= today_end
    ).count()
    
    # 다가오는 일정 (7일)
    future_date = datetime.now() + timedelta(days=7)
    upcoming_schedules = db.query(Schedule).filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time > datetime.now(),
        Schedule.start_time <= future_date,
        Schedule.status != ScheduleStatus.COMPLETED
    ).count()
    
    # 타입별 통계
    schedules_by_type = {}
    type_counts = db.query(Schedule.schedule_type, func.count(Schedule.id)).filter(
        Schedule.user_id == current_user.id
    ).group_by(Schedule.schedule_type).all()
    
    for schedule_type, count in type_counts:
        schedules_by_type[schedule_type.value] = count
    
    # 우선순위별 통계
    schedules_by_priority = {}
    priority_counts = db.query(Schedule.priority, func.count(Schedule.id)).filter(
        Schedule.user_id == current_user.id
    ).group_by(Schedule.priority).all()
    
    for priority, count in priority_counts:
        schedules_by_priority[priority.value] = count
    
    completion_rate = (completed_schedules / total_schedules * 100) if total_schedules > 0 else 0
    
    return ScheduleSummary(
        total_schedules=total_schedules,
        completed_schedules=completed_schedules,
        overdue_schedules=overdue_schedules,
        completion_rate=round(completion_rate, 1),
        today_schedules=today_schedules,
        upcoming_schedules=upcoming_schedules,
        schedules_by_type=schedules_by_type,
        schedules_by_priority=schedules_by_priority
    )


@router.post(
    "/",
    response_model=ScheduleResponse,
    summary="➕ 새 일정 생성",
    description="새로운 일정을 생성합니다. 제목, 시작 시간, 타입 등의 정보를 입력하세요."
)
async def create_schedule(
    schedule_data: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """➕ 새 일정 생성"""
    # 이벤트 ID가 있는 경우 유효성 검사
    if schedule_data.event_id:
        event = db.query(Event).filter(
            Event.id == schedule_data.event_id,
            Event.user_id == current_user.id
        ).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="이벤트를 찾을 수 없습니다"
            )
    
    schedule = Schedule(
        user_id=current_user.id,
        **schedule_data.dict()
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # 응답 데이터 구성
    response_data = ScheduleResponse.from_orm(schedule)
    response_data.duration_minutes = schedule.duration_minutes
    response_data.is_overdue = schedule.is_overdue
    response_data.is_today = schedule.is_today
    response_data.is_upcoming = schedule.is_upcoming
    response_data.formatted_time = schedule.get_formatted_time()
    response_data.priority_color = schedule.get_priority_color()
    
    if schedule.event:
        response_data.event_title = schedule.event.title
    
    return response_data


@router.post(
    "/quick",
    response_model=ScheduleResponse,
    summary="⚡ 빠른 일정 생성",
    description="최소한의 정보로 빠르게 일정을 생성합니다."
)
async def create_quick_schedule(
    schedule_data: ScheduleQuickAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """⚡ 빠른 일정 생성"""
    schedule = Schedule(
        user_id=current_user.id,
        title=schedule_data.title,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time,
        priority=schedule_data.priority,
        location=schedule_data.location,
        description=schedule_data.memo,
        schedule_type=ScheduleType.PERSONAL
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # 응답 데이터 구성
    response_data = ScheduleResponse.from_orm(schedule)
    response_data.duration_minutes = schedule.duration_minutes
    response_data.is_overdue = schedule.is_overdue
    response_data.is_today = schedule.is_today
    response_data.is_upcoming = schedule.is_upcoming
    response_data.formatted_time = schedule.get_formatted_time()
    response_data.priority_color = schedule.get_priority_color()
    
    return response_data


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="🔍 특정 일정 조회",
    description="일정 ID로 특정 일정의 상세 정보를 조회합니다."
)
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔍 특정 일정 조회"""
    schedule = db.query(Schedule).options(
        joinedload(Schedule.event)
    ).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    # 응답 데이터 구성
    response_data = ScheduleResponse.from_orm(schedule)
    response_data.duration_minutes = schedule.duration_minutes
    response_data.is_overdue = schedule.is_overdue
    response_data.is_today = schedule.is_today
    response_data.is_upcoming = schedule.is_upcoming
    response_data.formatted_time = schedule.get_formatted_time()
    response_data.priority_color = schedule.get_priority_color()
    
    if schedule.event:
        response_data.event_title = schedule.event.title
    
    return response_data


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
    summary="✏️ 일정 정보 수정",
    description="기존 일정의 정보를 수정합니다."
)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """✏️ 일정 정보 수정"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    update_data = schedule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    
    # 응답 데이터 구성
    response_data = ScheduleResponse.from_orm(schedule)
    response_data.duration_minutes = schedule.duration_minutes
    response_data.is_overdue = schedule.is_overdue
    response_data.is_today = schedule.is_today
    response_data.is_upcoming = schedule.is_upcoming
    response_data.formatted_time = schedule.get_formatted_time()
    response_data.priority_color = schedule.get_priority_color()
    
    if schedule.event:
        response_data.event_title = schedule.event.title
    
    return response_data


@router.delete(
    "/{schedule_id}",
    summary="🗑️ 일정 삭제",
    description="일정을 완전히 삭제합니다."
)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🗑️ 일정 삭제"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "일정이 성공적으로 삭제되었습니다"}


@router.patch(
    "/{schedule_id}/status",
    response_model=ScheduleResponse,
    summary="🔄 일정 상태 변경",
    description="일정의 상태를 변경합니다 (대기 → 진행중 → 완료)."
)
async def update_schedule_status(
    schedule_id: int,
    new_status: ScheduleStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """🔄 일정 상태 변경"""
    schedule = db.query(Schedule).filter(
        Schedule.id == schedule_id,
        Schedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일정을 찾을 수 없습니다"
        )
    
    schedule.status = new_status
    db.commit()
    db.refresh(schedule)
    
    # 응답 데이터 구성
    response_data = ScheduleResponse.from_orm(schedule)
    response_data.duration_minutes = schedule.duration_minutes
    response_data.is_overdue = schedule.is_overdue
    response_data.is_today = schedule.is_today
    response_data.is_upcoming = schedule.is_upcoming
    response_data.formatted_time = schedule.get_formatted_time()
    response_data.priority_color = schedule.get_priority_color()
    
    if schedule.event:
        response_data.event_title = schedule.event.title
    
    return response_data
