from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

from app.models.user import UserLevel, UserAuth


# 기본 유저 스키마
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    department: str
    position: Optional[str] = None


# 유저 생성 스키마
class UserCreate(UserBase):
    employee_id: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v


# 유저 수정 스키마
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    password: Optional[str] = None


# 관리자 유저 업데이트 스키마
class AdminUserUpdate(UserUpdate):
    level: Optional[UserLevel] = None
    auth: Optional[UserAuth] = None
    is_active: Optional[bool] = None
    points: Optional[int] = None


# 비밀번호 변경 스키마
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v


# DB에서 가져온 유저 정보 스키마
class User(UserBase):
    id: int
    employee_id: str
    level: UserLevel
    auth: UserAuth
    points: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 토큰 스키마
class Token(BaseModel):
    access_token: str
    token_type: str


# 토큰 데이터 스키마
class TokenData(BaseModel):
    username: Optional[str] = None


# 로그인 스키마
class Login(BaseModel):
    username: str
    password: str 