from datetime import datetime, timedelta
from typing import Any, Optional, Union

from passlib.context import CryptContext
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User as UserModel, UserAuth

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 인증 스키마
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """평문 비밀번호와 해시된 비밀번호 비교"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> UserModel:
    """현재 인증된 사용자 조회"""
    try:
        # 디버깅용 로그
        print(f"토큰 인증 시도: {token[:10]}...")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"토큰 디코딩 성공: username={username}")
    except jwt.JWTError as e:
        print(f"JWT 토큰 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 외부에서 import 하면 순환 참조가 발생할 수 있어 내부에서 임포트
    from app.crud.user import get_user_by_username
    
    user = get_user_by_username(db, username=username)
    if user is None:
        print(f"사용자를 찾을 수 없음: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        print(f"비활성화된 사용자: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"사용자 인증 성공: {username}, 권한={user.auth}")
    return user


def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """현재 활성화된 사용자 조회"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 사용자입니다"
        )
    return current_user


def get_current_admin_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """현재 관리자 사용자 조회"""
    if current_user.auth != UserAuth.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


def get_current_factory_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """현재 공장장 이상 권한 사용자 조회"""
    if current_user.auth not in [UserAuth.ADMIN, UserAuth.FACTORY]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="공장장 이상 권한이 필요합니다"
        )
    return current_user


def get_current_department_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """현재 부서장 이상 권한 사용자 조회"""
    if current_user.auth not in [UserAuth.ADMIN, UserAuth.FACTORY, UserAuth.DEPARTMENT]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="부서장 이상 권한이 필요합니다"
        )
    return current_user 