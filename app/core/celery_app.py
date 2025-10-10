"""
Celery 앱 설정 - 비동기 작업 스케줄링
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Celery 앱 생성
celery_app = Celery(
    "chalna",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notification_tasks",
    ]
)

# Celery 설정
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
    task_soft_time_limit=25 * 60,  # 25분
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Celery Beat 스케줄 설정
celery_app.conf.beat_schedule = {
    # 🎯 완전한 이벤트 기반 시스템
    # 
    # 1. 알림 예약: 일정 생성/수정 시 → schedule_notifications_for_event()
    #    - 3일 전, 1일 전, 3시간 전 알림을 정확한 시간에 예약
    # 
    # 2. 알림 삭제: 알림 전송 시 → 일정 날짜 7일 후 자동 삭제 예약
    #    - delete_notification_after_event() 자동 실행
    # 
    # ✅ 주기적 스케줄 불필요! (완전히 비어있음)
}

# 자동 작업 탐색 설정
celery_app.autodiscover_tasks(["app.tasks"])


def get_celery_app():
    """Celery 앱 인스턴스 반환"""
    return celery_app