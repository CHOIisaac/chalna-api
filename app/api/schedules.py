"""
Schedule API - 경조사 일정 관리 (MVP)
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
    response_model=ScheduleResponse,
    summary="일정 생성",
    description="새로운 경조사 일정을 생성합니다.",
)
def create_schedule(
    schedule: ScheduleCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """새로운 일정 생성"""
    db_schedule = Schedule(**schedule.dict(), user_id=current_user_id)

    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return ScheduleResponse.from_orm(db_schedule)


@router.get(
    "/",
    response_model=list[ScheduleResponse],
    summary="일정 목록 조회",
    description="사용자의 모든 일정을 조회합니다.",
)
def get_schedules(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="가져올 항목 수"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """일정 목록 조회"""
    schedules = (
        db.query(Schedule)
        .filter(Schedule.user_id == current_user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [ScheduleResponse.from_orm(schedule) for schedule in schedules]


@router.get(
    "/{schedule_id}",
    response_model=ScheduleResponse,
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

    return ScheduleResponse.from_orm(schedule)


@router.put(
    "/{schedule_id}",
    response_model=ScheduleResponse,
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

    update_data = schedule_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)

    return ScheduleResponse.from_orm(db_schedule)


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

    return {"message": "일정이 삭제되었습니다"}


@router.get(
    "/calendar/daily",
    response_model=list[DailySchedule],
    summary="일별 일정 조회",
    description="특정 날짜의 일정을 조회합니다.",
)
def get_daily_schedules(
    date: str = Query(..., description="조회할 날짜 (YYYY-MM-DD)"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """일별 일정 조회"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)"
        )

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= target_date,
            Schedule.start_time < target_date + timedelta(days=1),
        )
        .all()
    )

    # 일정을 요약 정보로 변환
    schedule_summaries = []
    for schedule in schedules:
        schedule_summaries.append(
            ScheduleSummary(
                id=schedule.id,
                title=schedule.title,
                start_time=schedule.start_time,
                location=schedule.location,
                event_type=schedule.event_type,
                is_today=schedule.is_today,
                is_upcoming=schedule.is_upcoming,
            )
        )

    return [DailySchedule(date=date, schedules=schedule_summaries)]


@router.get(
    "/calendar/weekly",
    response_model=WeeklySchedule,
    summary="주별 일정 조회",
    description="특정 주의 일정을 조회합니다.",
)
def get_weekly_schedules(
    week_start: str = Query(..., description="주 시작일 (YYYY-MM-DD)"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """주별 일정 조회"""
    try:
        start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=6)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)"
        )

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= start_date,
            Schedule.start_time <= end_date,
        )
        .all()
    )

    # 일별로 일정 그룹화
    daily_schedules = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        current_date_str = current_date.strftime("%Y-%m-%d")

        day_schedules = [s for s in schedules if s.start_time.date() == current_date]

        schedule_summaries = []
        for schedule in day_schedules:
            schedule_summaries.append(
                ScheduleSummary(
                    id=schedule.id,
                    title=schedule.title,
                    start_time=schedule.start_time,
                    location=schedule.location,
                    event_type=schedule.event_type,
                    is_today=schedule.is_today,
                    is_upcoming=schedule.is_upcoming,
                )
            )

        daily_schedules.append(
            DailySchedule(date=current_date_str, schedules=schedule_summaries)
        )

    return WeeklySchedule(
        week_start=week_start,
        week_end=end_date.strftime("%Y-%m-%d"),
        daily_schedules=daily_schedules,
    )


@router.get(
    "/summary/stats",
    summary="일정 통계",
    description="사용자의 일정 통계를 조회합니다.",
)
def get_schedule_statistics(
    current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """일정 통계 조회"""
    # 기본 통계 계산
    total_schedules = (
        db.query(Schedule).filter(Schedule.user_id == current_user_id).count()
    )

    # 오늘 일정 수
    today = datetime.now().date()
    today_schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= today,
            Schedule.start_time < today + timedelta(days=1),
        )
        .count()
    )

    # 다가오는 일정 수 (7일)
    future_date = datetime.now() + timedelta(days=7)
    upcoming_schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time > datetime.now(),
            Schedule.start_time <= future_date,
        )
        .count()
    )

    return {
        "total_schedules": total_schedules,
        "today_schedules": today_schedules,
        "upcoming_schedules": upcoming_schedules,
    }


@router.post(
    "/quick-add",
    response_model=ScheduleResponse,
    summary="빠른 일정 추가",
    description="간단한 정보로 일정을 빠르게 추가합니다.",
)
def create_quick_schedule(
    schedule: ScheduleQuickAdd,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """빠른 일정 추가"""
    db_schedule = Schedule(
        title=schedule.title,
        start_time=schedule.start_time,
        location=schedule.location,
        event_type=schedule.event_type,
        memo=schedule.memo,
        user_id=current_user_id,
    )

    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)

    return ScheduleResponse.from_orm(db_schedule)


@router.get(
    "/upcoming",
    response_model=list[ScheduleResponse],
    summary="다가오는 일정",
    description="앞으로의 일정을 조회합니다.",
)
def get_upcoming_schedules(
    days: int = Query(7, ge=1, le=30, description="몇 일 후까지의 일정을 조회할지"),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """다가오는 일정 조회"""
    now = datetime.now()
    end_date = now + timedelta(days=days)

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time > now,
            Schedule.start_time <= end_date,
        )
        .order_by(Schedule.start_time)
        .all()
    )

    return [ScheduleResponse.from_orm(schedule) for schedule in schedules]


@router.get(
    "/today",
    response_model=list[ScheduleResponse],
    summary="오늘 일정",
    description="오늘의 일정을 조회합니다.",
)
def get_today_schedules(
    current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    """오늘 일정 조회"""
    today = datetime.now().date()

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.start_time >= today,
            Schedule.start_time < today + timedelta(days=1),
        )
        .order_by(Schedule.start_time)
        .all()
    )

    return [ScheduleResponse.from_orm(schedule) for schedule in schedules]
