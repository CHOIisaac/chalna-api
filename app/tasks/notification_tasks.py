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
            logger.warning(f"⚠️ FCM 토큰 없음: User {user.id}, 알림은 DB에만 저장")
            # logger.debug(f"⏭️ FCM 토큰 없음: User {user.id}")
            # return {"success": False, "error": "No FCM token"}
        
        # 알림 생성
        notification_service = NotificationService(db)
        schedule_datetime = datetime.combine(
            schedule.event_date,
            schedule.event_time,
            tzinfo=KST
        )
        
        title = schedule.title

        # 🎯 경조사 타입별 메시지 생성
        event_type = schedule.event_type
        date_str = schedule_datetime.strftime('%m월 %d일 %H:%M')
        day_of_week = ["월", "화", "수", "목", "금", "토", "일"][schedule_datetime.weekday()]
        location = schedule.location

        # 시간대별, 경조사 타입별 메시지 매핑
        event_messages = {
            "결혼식": {
                "3일 전": f"🎊 행복한 결혼식이 3일 앞으로 다가왔어요!\n\n💡 축의금 봉투와 예쁜 복장을 미리 준비해두시면 좋아요. 축하의 마음을 전할 준비를 천천히 해보세요! 😊",
                "1일 전": f"🎊 내일은 뜻깊은 결혼식 날이에요!\n\n✨ 축의금 봉투는 준비되셨나요? 참석하실 의상도 한번 더 확인해보세요. 내일 따뜻한 축하를 전해주세요! 💝",
                "3시간 전": f"🎊 3시간 후면 결혼식이 시작돼요!\n\n🚗 이제 출발 준비를 시작하실 시간이에요. 축의금과 짐을 챙기시고, 교통상황도 미리 확인해보세요. 안전하게 다녀오세요! 🌟"
            },
            "장례식": {
                "3일 전": f"🕯️ 3일 후 장례식 일정이 있으시군요.\n\n🙏 조문을 위해 부의금과 일정을 미리 준비해주세요. 고인과 유가족에게 위로를 전할 수 있도록 마음의 준비도 함께 해주세요.",
                "1일 전": f"🕯️ 내일 장례식 일정이 있어요.\n\n🙏 부의금과 검소한 복장을 준비해주세요. 조문 시간과 장소를 한번 더 확인하시고, 유가족분들께 따뜻한 위로를 전해주세요.",
                "3시간 전": f"🕯️ 3시간 후 장례식이 있어요.\n\n🙏 이제 조문 준비를 마무리하실 시간이에요. 부의금을 챙기시고, 여유있게 출발해주세요. 안전하게 다녀오세요."
            },
            "생일": {
                "3일 전": f"🎂 특별한 생일이 3일 남았어요!\n\n🎁 생일 선물은 어떤 걸 준비하시겠어요? 케이크나 축하 카드도 함께 준비하시면 더 특별한 순간이 될 거예요! 설레는 마음으로 준비해보세요! ✨",
                "1일 전": f"🎂 내일은 기다리던 생일이에요!\n\n🎁 선물은 예쁘게 포장하셨나요? 축하 카드에 진심을 담아 메시지도 적어보세요. 내일 함께 축하하며 즐거운 시간 보내세요! 🎉",
                "3시간 전": f"🎂 3시간 후면 생일 파티가 시작돼요!\n\n🎁 선물 잘 챙기셨죠? 이제 출발하실 시간이에요! 즐거운 파티 되시길 바라요! 행복한 시간 보내세요! 🎈✨"
            },
            "돌잔치": {
                "3일 전": f"🍼 귀여운 아기의 돌잔치가 3일 남았어요!\n\n🎁 아기를 위한 돌 선물을 미리 준비해보세요! 금반지, 옷, 장난감 등 아기에게 좋은 선물을 천천히 고르실 수 있어요. 😊",
                "1일 전": f"🍼 내일은 예쁜 아기의 돌잔치 날이에요!\n\n🎁 돌 선물과 축하 봉투는 준비되셨나요? 내일 건강하게 자란 아기에게 축복을 전해주세요! 행복한 자리가 될 거예요! 👶💕",
                "3시간 전": f"🍼 3시간 후 돌잔치가 시작돼요!\n\n🎁 아기에게 줄 선물 잘 챙기셨죠? 이제 출발 준비하세요! 귀여운 아기를 만나러 즐겁게 다녀오세요! 🎈"
            },
            "졸업식": {
                "3일 전": f"🎓 자랑스러운 졸업식이 3일 남았어요!\n\n🌹 축하 선물이나 꽃다발을 준비해보세요! 그동안의 노력을 축하하고 앞으로의 새로운 시작을 응원하는 메시지도 함께 준비하시면 좋아요! ✨",
                "1일 전": f"🎓 내일은 뜻깊은 졸업식이에요!\n\n🌹 축하 선물과 꽃다발은 준비되셨나요? 격려와 축하의 메시지도 잊지 마세요! 내일 자랑스러운 순간을 함께 축하해주세요! 🎉",
                "3시간 전": f"🎓 3시간 후면 졸업식이 시작돼요!\n\n🌹 꽃다발과 선물 챙기셨죠? 이제 출발하실 시간이에요! 새로운 시작을 함께 축하해주세요! 멋진 순간이 될 거예요! 🎊"
            },
            "정년퇴임": {
                "3일 전": f"🌸 의미있는 정년퇴임식이 3일 남았어요!\n\n💐 오랜 세월 수고하신 분께 감사의 선물을 준비해보세요. 그동안의 노고에 진심 어린 감사와 존경을 표현할 수 있는 좋은 기회예요.",
                "1일 전": f"🌸 내일은 정년퇴임식이에요!\n\n💐 꽃다발과 감사 선물은 준비되셨나요? 오랜 시간 함께한 분께 진심 어린 감사와 새로운 시작을 응원하는 마음을 전해주세요! 😊",
                "3시간 전": f"🌸 3시간 후 정년퇴임식이 있어요!\n\n💐 이제 출발 준비하실 시간이에요! 오랜 세월 수고하신 분께 존경과 감사의 마음을 꼭 전해주세요! 🙏✨"
            },
            "개업식": {
                "3일 전": f"🎉 축하할 개업식이 3일 남았어요!\n\n💐 화환이나 축하 선물을 준비해보세요! 새로운 시작을 응원하고 번창을 기원하는 마음을 전할 수 있어요. 멋진 출발을 함께 축하해주세요! 🌟",
                "1일 전": f"🎉 내일은 개업식이에요!\n\n💐 축하 화환 주문은 확인하셨나요? 새로운 시작을 응원하는 따뜻한 축하를 준비해주세요! 내일 함께 번창을 기원해요! 🍀",
                "3시간 전": f"🎉 3시간 후 개업식이 시작돼요!\n\n💐 이제 출발하실 시간이에요! 새로운 도전을 시작하는 분께 힘찬 응원을 전해주세요! 대박나실 거예요! 🎊✨"
            },
            "기념일": {
                "3일 전": f"💝 소중한 기념일이 3일 남았어요!\n\n🎁 특별한 선물과 이벤트를 계획해보세요! 레스토랑 예약도 미리 하시면 좋아요. 더 특별한 추억을 만들 수 있는 시간이 될 거예요! ✨",
                "1일 전": f"💝 내일은 특별한 기념일이에요!\n\n🎁 선물은 예쁘게 포장하셨나요? 레스토랑 예약도 다시 한번 확인해보세요! 내일 소중한 사람과 행복한 시간 보내세요! 💕",
                "3시간 전": f"💝 3시간 후 기념일 약속이에요!\n\n🎁 선물 챙기셨죠? 이제 설레는 마음으로 준비하세요! 소중한 사람과 함께하는 특별한 시간 되시길 바래요! 행복하세요! 💖✨"
            },
            "기타": {
                "3일 전": f"📅 중요한 일정이 3일 남았어요!\n\n💡 필요한 준비물이 있다면 미리 챙겨두세요. 여유있게 준비하시면 훨씬 수월하실 거예요! 😊",
                "1일 전": f"📅 내일 일정이 있으시네요!\n\n💡 준비물과 시간을 한번 더 확인해주세요! 내일 일정이 순조롭게 진행되길 바라요! 🌟",
                "3시간 전": f"📅 3시간 후 일정이 있어요!\n\n💡 이제 출발 준비를 시작하세요! 필요한 것들은 다 챙기셨죠? 안전하게 다녀오세요! 🚗"
            }
        }

        # 메시지 선택 (기본값: 기타)
        event_type_messages = event_messages.get(event_type)
        message = event_type_messages.get(notification_label)
        
        notification = notification_service.create_notification(
            user_id=user.id,
            title=title,
            message=message,
            notification_type=event_type,
            event_date=schedule.event_date,
            event_time=schedule.event_time,
            location=schedule.location
        )
        print(notification)
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

