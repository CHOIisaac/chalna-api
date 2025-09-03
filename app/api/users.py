"""
User API - 사용자 관리
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserPasswordChange,
    NotificationSettings, NotificationSettingsUpdate
)

router = APIRouter(tags=["사용자 관리"])


@router.post("/", response_model=UserResponse, summary="사용자 생성", description="새로운 사용자를 생성합니다.")
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """새로운 사용자 생성"""
    # 사용자명 중복 확인
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")
    
    # 이메일 중복 확인
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")
    
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone
    )
    db_user.set_password(user.password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/me", response_model=UserResponse, summary="내 정보 조회", description="현재 로그인한 사용자의 정보를 조회합니다.")
def get_current_user(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """현재 사용자 정보 조회"""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user


@router.put("/me", response_model=UserResponse, summary="내 정보 수정", description="현재 로그인한 사용자의 정보를 수정합니다.")
def update_current_user(
    user_update: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """현재 사용자 정보 수정"""
    db_user = db.query(User).filter(User.id == current_user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    update_data = user_update.dict(exclude_unset=True)
    
    # 사용자명 중복 확인
    if "username" in update_data:
        existing_user = db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")
    
    # 이메일 중복 확인
    if "email" in update_data:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.patch("/me/password", summary="비밀번호 변경", description="현재 로그인한 사용자의 비밀번호를 변경합니다.")
def change_password(
    password_change: UserPasswordChange,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    db_user = db.query(User).filter(User.id == current_user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 현재 비밀번호 확인
    if not db_user.verify_password(password_change.current_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다")
    
    # 새 비밀번호 설정
    db_user.set_password(password_change.new_password)
    db.commit()
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}


@router.get("/me/notification-settings", response_model=NotificationSettings, summary="알림 설정 조회", description="현재 사용자의 알림 설정을 조회합니다.")
def get_notification_settings(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """알림 설정 조회"""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return NotificationSettings(
        push_notification_enabled=user.push_notification_enabled,
        notification_advance_hours=user.notification_advance_hours
    )


@router.patch("/me/notification-settings", response_model=NotificationSettings, summary="알림 설정 변경", description="현재 사용자의 알림 설정을 변경합니다.")
def update_notification_settings(
    notification_update: NotificationSettingsUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """알림 설정 변경"""
    db_user = db.query(User).filter(User.id == current_user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    update_data = notification_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return NotificationSettings(
        push_notification_enabled=db_user.push_notification_enabled,
        notification_advance_hours=db_user.notification_advance_hours
    )


@router.get("/me/stats", summary="내 통계", description="현재 사용자의 통계 정보를 조회합니다.")
def get_current_user_stats(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """현재 사용자 통계 조회"""
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return user.update_stats()


@router.get("/", response_model=List[UserResponse], summary="사용자 목록 조회", description="모든 사용자의 목록을 조회합니다.")
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """사용자 목록 조회"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse, summary="사용자 상세 조회", description="특정 사용자의 상세 정보를 조회합니다.")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """사용자 상세 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user


@router.delete("/{user_id}", summary="사용자 삭제", description="사용자를 삭제합니다.")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """사용자 삭제"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    db.delete(user)
    db.commit()
    
    return {"message": "사용자가 삭제되었습니다"} 