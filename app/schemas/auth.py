"""
🔐 인증 관련 스키마

로그인, JWT 토큰 등
"""

from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    """사용자 로그인 스키마"""
    username: str
    password: str

class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str

class TokenData(BaseModel):
    """JWT 토큰 데이터 스키마"""
    user_id: int | None = None
