from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.schemas.user_settings import UserSettingsUpdate

router = APIRouter(tags=["설정 관리"])


@router.get("/", summary="설정 조회")
def get_settings(
        current_user_id = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """사용자 설정 조회"""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return {
        "notifications_enabled": user.notifications_enabled,
        "event_reminders": user.event_reminders,
        "reminder_hours_before": user.reminder_hours_before
    }


@router.put("/", summary="설정 업데이트")
def update_settings(
        settings_update: UserSettingsUpdate,
        current_user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db),
):
    """사용자 설정 업데이트"""
    # 한 번의 쿼리로 업데이트
    update_data = settings_update.dict(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="업데이트할 데이터가 없습니다")

    # 직접 업데이트 (가장 효율적)
    db.query(User).filter(User.id == current_user_id).update(update_data)
    db.commit()

    # 업데이트된 사용자 조회
    user = db.query(User).filter(User.id == current_user_id).first()

    # 간단한 응답
    return {
        "notifications_enabled": user.notifications_enabled,
        "event_reminders": user.event_reminders,
        "reminder_hours_before": user.reminder_hours_before
    }