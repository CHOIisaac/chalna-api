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
from app.core.firebase_config import get_firebase_service


class NotificationService:
    """알림 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.firebase = get_firebase_service()
    
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
        
        # Firebase 알림 전송
        self._send_firebase_notification(notification)
        
        return notification
    
    def create_schedule_reminder(self, schedule: Schedule) -> Optional[Notification]:
        """일정 알림 생성"""
        if not schedule.user.should_receive_schedule_notifications():
            return None
        
        # 알림 시간 계산 (event_date와 event_time을 datetime으로 결합)
        if schedule.event_date and schedule.event_time:
            from datetime import datetime, time
            schedule_datetime = datetime.combine(schedule.event_date, schedule.event_time)
            notification_time = schedule.user.get_notification_time(schedule_datetime)
            
            if not notification_time:
                return None
            
            # 현재 시간이 알림 시간보다 이전이면 알림 생성
            if datetime.now() < notification_time:
                title = f"일정 알림: {schedule.title}"
                message = f"{schedule.title} 일정이 {schedule_datetime.strftime('%m월 %d일 %H:%M')}에 예정되어 있습니다."
                
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
    
    def create_ledger_notification(self, ledger: Ledger) -> Optional[Notification]:
        """장부 알림 생성"""
        # 사용자가 장부 알림을 받도록 설정했는지 확인
        if not ledger.user.should_receive_notifications():
            return None
            
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
    ) -> Optional[Notification]:
        """시스템 알림 생성"""
        # 사용자 조회 및 알림 설정 확인
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.should_receive_notifications():
            return None
            
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
        """Firebase 알림 전송"""
        try:
            # 1. 사용자의 FCM 토큰 조회
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            
            if not user or not user.fcm_token:
                print(f"⚠️ 사용자 {notification.user_id}의 FCM 토큰이 없습니다.")
                return
            
            # 2. Firebase Admin SDK로 알림 전송
            data = {
                "notification_id": str(notification.id),
                "type": notification.event_type,
                "event_date": notification.event_date.isoformat() if notification.event_date else "",
                "event_time": notification.event_time.isoformat() if notification.event_time else "",
                "location": notification.location or ""
            }
            
            success = self.firebase.send_notification(
                token=user.fcm_token,
                title=notification.title,
                body=notification.message,
                data=data
            )
            
            # 3. 전송 결과 로깅
            if success:
                print(f"✅ 알림 전송 성공: 사용자 {notification.user_id}, 알림 ID {notification.id}")
            else:
                print(f"❌ 알림 전송 실패: 사용자 {notification.user_id}, 알림 ID {notification.id}")
                
        except Exception as e:
            print(f"❌ Firebase 알림 전송 중 오류: {e}")
    
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
