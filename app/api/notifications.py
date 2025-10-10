"""
알림 API 엔드포인트
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import Notification
from app.schemas.notification import NotificationListResponse, NotificationListData, NotificationResponse, NotificationUpdate

router = APIRouter()


@router.get("/", response_model=NotificationListResponse, summary="알림 목록 조회", description="사용자의 알림 목록을 조회합니다")
async def get_notifications(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db),
    read: Optional[bool] = Query(None, description="읽음 상태 필터 (true: 읽음, false: 안읽음, null: 전체)"),
    event_type: Optional[str] = Query(None, description="알림 타입 필터")
) -> NotificationListResponse:
    """
    알림 목록 조회
    
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **read**: 읽음 상태 필터 (선택사항)
    - **type**: 알림 타입 필터 (선택사항)
    """
    try:
        # 기본 쿼리
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        # 읽음 상태 필터
        if read is not None:
            query = query.filter(Notification.read == read)
        
        # 타입 필터
        if event_type:
            query = query.filter(Notification.type == event_type)
        
        # 전체 개수 조회
        total_count = query.count()

        # 페이지네이션 적용
        notifications = query.order_by(desc(Notification.created_at)).all()

        # 응답 데이터 구성
        notification_list = []
        for notification in notifications:
            notification_list.append(NotificationResponse(
                id=str(notification.id),
                title=notification.title,
                message=notification.message,
                time=notification.created_at.strftime("%H:%M") if notification.created_at else "",
                event_type=notification.event_type,
                read=notification.read,
                date=notification.event_date.isoformat() if notification.event_date else "",
                location=notification.location or "",
                created_at=notification.created_at.isoformat() if notification.created_at else "",
                updated_at=notification.updated_at.isoformat() if notification.updated_at else ""
            ))
        
        data = NotificationListData(
            notifications=notification_list,
            total_count=total_count
        )
        
        return NotificationListResponse(
            success=True,
            data=data.dict(),
            message="알림 목록 조회 성공"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.patch("/{notification_id}/read", summary="알림 읽음 처리", description="특정 알림의 읽음 상태를 업데이트합니다")
async def mark_notification_read(
    notification_id: int,
    update_data: NotificationUpdate,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 읽음 처리
    
    - **notification_id**: 알림 ID
    - **read**: 읽음 상태 (true: 읽음, false: 안읽음)
    """
    try:
        # 알림 조회
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
        
        # 읽음 상태 업데이트
        notification.read = update_data.read
        db.commit()
        db.refresh(notification)
        
        status_text = "읽음" if update_data.read else "안읽음"
        return {
            "success": True,
            "message": f"알림이 {status_text}으로 처리되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 읽음 처리 중 오류가 발생했습니다: {str(e)}")


@router.patch("/read-all", summary="모든 알림 읽음 처리", description="사용자의 모든 알림을 읽음으로 처리합니다")
async def mark_all_notifications_read(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    모든 알림 읽음 처리
    """
    try:
        # 사용자의 모든 안읽음 알림을 읽음으로 처리
        updated_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).update({"read": True})
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{updated_count}개의 알림이 읽음으로 처리되었습니다"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 읽음 처리 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{notification_id}", summary="알림 삭제", description="특정 알림을 삭제합니다")
async def delete_notification(
    notification_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 삭제
    
    - **notification_id**: 알림 ID
    """
    try:
        # 알림 조회
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
        
        # 알림 삭제
        db.delete(notification)
        db.commit()
        
        return {
            "success": True,
            "message": "알림이 삭제되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 삭제 중 오류가 발생했습니다: {str(e)}")


@router.get("/unread-count", summary="안읽음 알림 개수 조회", description="사용자의 안읽음 알림 개수를 조회합니다")
async def get_unread_count(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    안읽음 알림 개수 조회
    """
    try:
        # 안읽음 알림 개수 조회
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False
        ).count()
        
        return {
            "success": True,
            "data": {
                "unread_count": unread_count
            },
            "message": "안읽음 알림 개수 조회 성공"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"안읽음 알림 개수 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/fcm-token", summary="FCM 토큰 등록", description="사용자의 FCM 토큰을 등록합니다")
async def register_fcm_token(
    fcm_token: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    FCM 토큰 등록
    
    - **fcm_token**: Firebase FCM 토큰
    """
    try:
        from app.models.user import User
        
        # 사용자 조회 및 FCM 토큰 업데이트
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user.fcm_token = fcm_token
        db.commit()
        
        return {
            "success": True,
            "message": "FCM 토큰이 등록되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FCM 토큰 등록 중 오류가 발생했습니다: {str(e)}")


@router.post("/test", summary="테스트 알림 전송", description="FCM 푸시알림 테스트를 위한 API")
async def send_test_notification(
    title: str = "테스트 알림",
    message: str = "FCM 푸시알림이 정상적으로 작동합니다!",
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    테스트 알림 전송
    
    - **title**: 알림 제목 (기본값: "테스트 알림")
    - **message**: 알림 메시지 (기본값: "FCM 푸시알림이 정상적으로 작동합니다!")
    """
    try:
        from app.services.notification_service import NotificationService
        
        # NotificationService를 사용하여 테스트 알림 생성 및 전송
        notification_service = NotificationService(db)
        
        notification = notification_service.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="system"
        )
        
        return {
            "success": True,
            "data": {
                "notification_id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "sent_at": notification.created_at.isoformat() if notification.created_at else None
            },
            "message": "테스트 알림이 전송되었습니다"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"테스트 알림 전송 중 오류가 발생했습니다: {str(e)}")
