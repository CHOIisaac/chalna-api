"""
Pydantic 전역 설정
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator


class BaseModelWithDatetime(BaseModel):
    """datetime 파싱이 개선된 기본 모델"""
    
    @field_validator('*', mode='before')
    @classmethod
    def parse_datetime_fields(cls, v: Any) -> Any:
        """datetime 필드 자동 파싱"""
        if v is None:
            return None
        
        # 문자열이고 datetime 형식인 경우
        if isinstance(v, str) and any(keyword in v for keyword in ['-', ':', '+', 'Z']):
            try:
                # PostgreSQL datetime 형식 파싱
                if '+' in v or 'Z' in v:
                    # 타임존 정보가 있는 경우
                    return datetime.fromisoformat(v.replace('Z', '+00:00'))
                else:
                    # 타임존 정보가 없는 경우
                    return datetime.fromisoformat(v)
            except (ValueError, TypeError):
                # 파싱 실패 시 원본 반환
                return v
        
        return v
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
