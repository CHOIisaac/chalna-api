"""
알림 서비스 - Firebase 알림 연동
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.notification import Notification
from app.models.user import User
from app.models.schedule import Schedule
from app.models.ledger import Ledger


class NotificationService:
    """알림 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        event_date: Optional[date] = None,
        event_time: Optional[time] = None,
        location: Optional[str] = None
    ) -> Notification:
        """알림 생성"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            event_type=notification_type,
            event_date=event_date,
            event_time=event_time,
            location=location
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Firebase 알림 전송 (실제 구현 시)
        # self._send_firebase_notification(notification)
        
        return notification
    
    def create_schedule_reminder(self, schedule: Schedule) -> Optional[Notification]:
        """일정 알림 생성"""
        if not schedule.user.should_receive_notifications():
            return None
        
        # 알림 시간 계산
        notification_time = schedule.user.get_notification_time(schedule.start_datetime_kst)
        if not notification_time:
            return None
        
        # 현재 시간이 알림 시간보다 이전이면 알림 생성
        if datetime.now() < notification_time:
            title = f"일정 알림: {schedule.event_name}"
            message = f"{schedule.event_name} 일정이 {schedule.start_datetime_kst.strftime('%m월 %d일 %H:%M')}에 예정되어 있습니다."
            
            return self.create_notification(
                user_id=schedule.user_id,
                title=title,
                message=message,
                notification_type="schedule",
                event_date=schedule.event_date,
                event_time=schedule.event_time,
                location=schedule.location
            )
        
        return None
    
    def create_ledger_notification(self, ledger: Ledger) -> Notification:
        """장부 알림 생성"""
        entry_type = "받음" if ledger.entry_type == "received" else "나눔"
        event_type = ledger.event_type or "기타"
        
        title = f"장부 {entry_type}: {event_type}"
        message = f"{ledger.counterparty_name}님의 {event_type}에 {entry_type} {ledger.amount:,}원이 기록되었습니다."
        
        return self.create_notification(
            user_id=ledger.user_id,
            title=title,
            message=message,
            notification_type="ledger",
            event_date=ledger.event_date
        )
    
    def create_system_notification(
        self,
        user_id: int,
        title: str,
        message: str
    ) -> Notification:
        """시스템 알림 생성"""
        return self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="system"
        )
    
    def get_upcoming_schedule_notifications(self, hours_ahead: int = 24) -> List[Notification]:
        """다가오는 일정 알림 조회"""
        now = datetime.now()
        future_time = now + timedelta(hours=hours_ahead)
        
        # 다가오는 일정들 조회
        upcoming_schedules = self.db.query(Schedule).filter(
            and_(
                Schedule.start_datetime_kst > now,
                Schedule.start_datetime_kst <= future_time
            )
        ).all()
        
        notifications = []
        for schedule in upcoming_schedules:
            notification = self.create_schedule_reminder(schedule)
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """알림 읽음 처리"""
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if notification:
            notification.read = True
            self.db.commit()
            return True
        
        return False
    
    def mark_all_notifications_read(self, user_id: int) -> int:
        """모든 알림 읽음 처리"""
        updated_count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        ).update({"read": True})
        
        self.db.commit()
        return updated_count
    
    def delete_old_notifications(self, days_old: int = 30) -> int:
        """오래된 알림 삭제"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = self.db.query(Notification).filter(
            and_(
                Notification.created_at < cutoff_date,
                Notification.read == True
            )
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    def _send_firebase_notification(self, notification: Notification):
        """Firebase 알림 전송 (실제 구현 필요)"""
        # TODO: Firebase Admin SDK를 사용한 실제 알림 전송 구현
        # 1. 사용자의 FCM 토큰 조회
        # 2. Firebase Admin SDK로 알림 전송
        # 3. 전송 결과 로깅
        pass
    
    def get_notification_stats(self, user_id: int) -> Dict[str, Any]:
        """알림 통계 조회"""
        total_count = self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).count()
        
        unread_count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        ).count()
        
        # 타입별 통계
        type_stats = self.db.query(
            Notification.type,
            self.db.func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.type).all()
        
        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": total_count - unread_count,
            "type_breakdown": {stat.type: stat.count for stat in type_stats}
        }
