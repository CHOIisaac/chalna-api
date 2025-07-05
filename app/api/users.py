"""
👤 사용자 API 라우터

사용자 정보 관리 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    👥 사용자 목록 조회 (관리자용)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    👤 특정 사용자 정보 조회
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return user.to_dict()


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    full_name: str = None,
    nickname: str = None,
    phone: str = None,
    db: Session = Depends(get_db)
):
    """
    ✏️ 사용자 정보 수정
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 정보 업데이트
    if full_name is not None:
        user.full_name = full_name
    if nickname is not None:
        user.nickname = nickname
    if phone is not None:
        user.phone = phone
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "사용자 정보가 업데이트되었습니다",
        "user": user.to_dict()
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    🗑️ 사용자 계정 삭제
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "사용자 계정이 삭제되었습니다"} 