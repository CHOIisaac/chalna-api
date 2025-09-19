"""
Schedule API - 경조사 일정 관리 (MVP)
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, func

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
        "data": ScheduleResponse.from_schedule(db_schedule).dict(),
        "message": "일정이 생성되었습니다."
    }


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
        .options(selectinload(Schedule.user))  # 관계 미리 로딩
        .filter(Schedule.id == schedule_id, Schedule.user_id == current_user_id)
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다")

    return {
        "success": True,
        "data": ScheduleResponse.from_schedule(schedule).dict()
    }


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

    # 업데이트 데이터 적용
    update_data = schedule_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)

    return {
        "success": True,
        "data": ScheduleResponse.from_schedule(db_schedule).dict(),
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
        limit: int = Query(20, ge=1, le=100, description="가져올 항목 수"),

        # 필터링 파라미터 (프론트엔드 필터와 매칭)
        status: Optional[str] = Query(None, description="상태: upcoming, completed"),
        event_type: Optional[str] = Query(None, description="경조사 타입: 결혼식, 장례식, 돌잔치, 개업식"),
        sort_by: str = Query("latest", description="정렬: latest(최신순), oldest(오래된순)"),
        search: Optional[str] = Query(None, description="제목/장소 검색"),

        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """일정 목록 조회 - 필터링 완전 지원"""

    # 기본 쿼리
    query = (
        db.query(Schedule)
        .filter(Schedule.user_id == current_user_id)
        .options(selectinload(Schedule.user))
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
    if sort_by == "latest":
        query = query.order_by(Schedule.event_date.desc(), Schedule.event_time.desc())
    else:  # oldest
        query = query.order_by(Schedule.event_date.asc(), Schedule.event_time.asc())

    # 총 개수 및 페이징
    total_count = query.count()
    schedules = query.offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": [ScheduleResponse.from_schedule(schedule).dict() for schedule in schedules],
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
        "data": [ScheduleResponse.from_schedule(s).dict() for s in schedules]
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
        "data": [ScheduleResponse.from_schedule(s).dict() for s in schedules]
    }


@router.get("/stats/summary", summary="일정 통계 요약")
def get_schedule_stats(
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """대시보드용 통계 정보"""

    # 기본 통계
    total_count = db.query(Schedule).filter(Schedule.user_id == current_user_id).count()

    upcoming_count = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.status == StatusType.UPCOMING
        )
        .count()
    )

    completed_count = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.status == StatusType.COMPLETED
        )
        .count()
    )

    # 이번 달 일정
    this_month_start = datetime.now().replace(day=1).date()
    next_month_start = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).date()

    this_month_count = (
        db.query(Schedule)
        .filter(
            Schedule.user_id == current_user_id,
            Schedule.event_date >= this_month_start,
            Schedule.event_date < next_month_start
        )
        .count()
    )

    return {
        "success": True,
        "data": {
            "total": total_count,
            "upcoming": upcoming_count,
            "completed": completed_count,
            "this_month": this_month_count
        }
    }