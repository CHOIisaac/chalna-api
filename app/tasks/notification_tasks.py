"""
알림 관련 Celery 태스크
"""

from datetime import datetime, timedelta
from typing import List, Literal
from celery import Task
from celery.utils.log import get_task_logger
from zoneinfo import ZoneInfo

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.schedule import Schedule
from app.models.user import User
from app.services.notification_service import NotificationService

logger = get_task_logger(__name__)
KST = ZoneInfo("Asia/Seoul")


class DatabaseTask(Task):
    """데이터베이스 세션을 자동으로 관리하는 기본 태스크 클래스"""
    _db = None
    
    def after_return(self, *args, **kwargs):
        """태스크 완료 후 DB 세션 정리"""
        if self._db is not None:
            self._db.close()


# ❌ 기존 Polling 방식 코드 삭제됨
# ✅ 이벤트 기반 방식으로 대체 (schedule_notifications_for_event 사용)


@celery_app.task(name="app.tasks.notification_tasks.delete_notification_after_event")
def delete_notification_after_event(notification_id: int) -> dict:
    """
    일정 날짜 7일 후에 알림을 자동 삭제하는 태스크
    
    Args:
        notification_id: 삭제할 알림 ID
    
    Returns:
        삭제 결과 딕셔너리
    """
    db = SessionLocal()
    try:
        from app.models.notification import Notification
        
        # 알림 조회
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        
        if not notification:
            logger.warning(f"⚠️ 삭제할 알림을 찾을 수 없음: Notification ID {notification_id}")
            return {
                "success": False,
                "error": "Notification not found"
            }
        
        # 알림 삭제
        db.delete(notification)
        db.commit()
        
        logger.info(f"🗑️ 알림 자동 삭제 완료: Notification ID {notification_id}")
        
        return {
            "success": True,
            "notification_id": notification_id,
            "deleted_at": datetime.now(KST).isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 알림 삭제 중 오류: Notification {notification_id}, Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.send_immediate_notification")
def send_immediate_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "system"
) -> dict:
    """
    즉시 알림 전송 태스크 (API에서 호출 가능)
    
    Args:
        user_id: 사용자 ID
        title: 알림 제목
        message: 알림 내용
        notification_type: 알림 타입
    
    Returns:
        전송 결과 딕셔너리
    """
    db = SessionLocal()
    try:
        notification_service = NotificationService(db)
        
        notification = notification_service.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        
        logger.info(f"✅ 즉시 알림 전송 성공: User {user_id}, Notification {notification.id}")
        
        return {
            "success": True,
            "notification_id": notification.id,
            "sent_at": notification.created_at.isoformat() if notification.created_at else None
        }
        
    except Exception as e:
        logger.error(f"❌ 즉시 알림 전송 실패: User {user_id}, Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.notification_tasks.send_scheduled_notification")
def send_scheduled_notification(
    schedule_id: int,
    notification_label: str
) -> dict:
    """
    예약된 시간에 실행되는 알림 전송 태스크
    
    Args:
        schedule_id: 일정 ID
        notification_label: 알림 라벨 (예: "3일 전", "1일 전", "3시간 전")
    
    Returns:
        전송 결과 딕셔너리
    """
    db = SessionLocal()
    try:
        # 스케줄 조회
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            logger.warning(f"⚠️ 스케줄을 찾을 수 없음: Schedule ID {schedule_id}")
            return {"success": False, "error": "Schedule not found"}
        
        # 이미 완료된 일정이면 알림 안 보냄
        if schedule.status == "completed":
            logger.info(f"⏭️ 완료된 일정: Schedule ID {schedule_id}")
            return {"success": False, "error": "Schedule already completed"}
        
        # 사용자 조회
        user = db.query(User).filter(User.id == schedule.user_id).first()
        if not user:
            logger.warning(f"⚠️ 사용자를 찾을 수 없음: User ID {schedule.user_id}")
            return {"success": False, "error": "User not found"}
        
        # 알림 설정 확인
        if not user.should_receive_notifications():
            logger.debug(f"⏭️ 알림 비활성화: User {user.id}")
            return {"success": False, "error": "Notifications disabled"}
        
        if user.settings and not user.settings.event_reminders:
            logger.debug(f"⏭️ 일정 알림 비활성화: User {user.id}")
            return {"success": False, "error": "Event reminders disabled"}
        
        # FCM 토큰 확인
        if not user.fcm_token:
            logger.debug(f"⏭️ FCM 토큰 없음: User {user.id}")
            return {"success": False, "error": "No FCM token"}
        
        # 알림 생성
        notification_service = NotificationService(db)
        schedule_datetime = datetime.combine(
            schedule.event_date,
            schedule.event_time,
            tzinfo=KST
        )
        
        title = f"📅 {notification_label} 일정 알림"
        message = (
            f"{schedule.title} 일정이 {notification_label} 있습니다.\n"
            f"일시: {schedule_datetime.strftime('%m월 %d일 %H:%M')}\n"
            f"장소: {schedule.location or '미정'}"
        )
        
        notification = notification_service.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            notification_type="schedule",
            event_date=schedule.event_date,
            event_time=schedule.event_time,
            location=schedule.location
        )
        
        # 🗑️ 일정 날짜 7일 후에 알림 자동 삭제 예약
        delete_time = schedule_datetime + timedelta(days=7)
        delete_notification_after_event.apply_async(
            args=[notification.id],
            eta=delete_time
        )
        logger.info(f"🗑️ 알림 삭제 예약: {delete_time.isoformat()} (Notification {notification.id})")
        
        logger.info(
            f"✅ 예약 알림 전송 성공: User {user.id}, Schedule {schedule.id} ({notification_label})"
        )
        
        return {
            "success": True,
            "notification_id": notification.id,
            "schedule_id": schedule_id,
            "label": notification_label
        }
        
    except Exception as e:
        logger.error(f"❌ 예약 알림 전송 실패: Schedule {schedule_id}, Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()


def schedule_notifications_for_event(schedule_id: int, schedule_datetime: datetime, user_id: int):
    """
    일정에 대한 모든 알림을 예약하는 함수
    
    Args:
        schedule_id: 일정 ID
        schedule_datetime: 일정 시작 시간 (timezone-aware)
        user_id: 사용자 ID
    """
    from app.core.config import settings
    
    logger.info(f"📅 일정 알림 예약 시작: Schedule {schedule_id}, Time {schedule_datetime}")
    
    now = datetime.now(KST)
    scheduled_tasks = []
    
    # 1. 일 단위 알림 예약 (3일 전, 1일 전)
    for days in settings.SCHEDULE_NOTIFICATION_DAYS:
        notification_time = schedule_datetime - timedelta(days=days)
        
        # 이미 지난 시간이면 건너뜀
        if notification_time <= now:
            logger.debug(f"⏭️ 지난 시간: {days}일 전 ({notification_time})")
            continue
        
        # Celery 태스크 예약
        task = send_scheduled_notification.apply_async(
            args=[schedule_id, f"{days}일 전"],
            eta=notification_time
        )
        scheduled_tasks.append({
            "label": f"{days}일 전",
            "eta": notification_time.isoformat(),
            "task_id": task.id
        })
        logger.info(f"✅ {days}일 전 알림 예약: {notification_time} (Task ID: {task.id})")
    
    # 2. 시간 단위 알림 예약 (3시간 전)
    for hours in settings.SCHEDULE_NOTIFICATION_HOURS:
        notification_time = schedule_datetime - timedelta(hours=hours)
        
        # 이미 지난 시간이면 건너뜀
        if notification_time <= now:
            logger.debug(f"⏭️ 지난 시간: {hours}시간 전 ({notification_time})")
            continue
        
        # Celery 태스크 예약
        task = send_scheduled_notification.apply_async(
            args=[schedule_id, f"{hours}시간 전"],
            eta=notification_time
        )
        scheduled_tasks.append({
            "label": f"{hours}시간 전",
            "eta": notification_time.isoformat(),
            "task_id": task.id
        })
        logger.info(f"✅ {hours}시간 전 알림 예약: {notification_time} (Task ID: {task.id})")
    
    logger.info(f"🎉 총 {len(scheduled_tasks)}개 알림 예약 완료: Schedule {schedule_id}")
    
    return scheduled_tasks

