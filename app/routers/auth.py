from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    get_current_active_user,
    get_password_hash,
    verify_password
)
from app.crud.user import (
    authenticate_user,
    create_user,
    get_user_by_username,
    change_password as crud_change_password
)
from app.models.user import User as UserModel, UserAuth
from app.schemas.user import UserCreate, Token, PasswordChange, User as UserSchema

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/register", response_model=Any)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    새 사용자 등록
    """
    print(f"회원가입 요청 수신: username={user_in.username}, email={user_in.email}")
    print(f"요청 데이터: {user_in}")
    
    user = get_user_by_username(db, username=user_in.username)
    if user:
        print(f"회원가입 실패: 이미 존재하는 사용자명 - {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사용자입니다."
        )
    
    # 비밀번호 확인
    if user_in.password != user_in.confirm_password:
        print(f"회원가입 실패: 비밀번호 불일치 - {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )
    
    try:
        user = create_user(db, user_in)
        print(f"회원가입 성공: username={user.username}, id={user.id}")
        
        # 토큰 발급
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "full_name": user.full_name,
            "employee_id": user.employee_id
        }
    except Exception as e:
        print(f"회원가입 중 예외 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 호환 토큰 로그인, 액세스 토큰 획득
    """
    # 디버깅용 로그
    print(f"로그인 시도: username={form_data.username}")
    
    user = get_user_by_username(db, username=form_data.username)
    if not user:
        print(f"로그인 실패: 사용자를 찾을 수 없음 - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자명 또는 비밀번호입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        print(f"로그인 실패: 비밀번호 불일치 - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자명 또는 비밀번호입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7일
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    print(f"로그인 성공: {form_data.username}, 토큰 생성 완료")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/admin-login-direct", response_model=Any)
def admin_login_direct(username: str, password: str):
    """
    하드코딩된 관리자 계정 로그인 (admin/12345)
    """
    # 하드코딩된 관리자 계정 정보
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "12345"
    
    print(f"관리자 직접 로그인 시도: username={username}")
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # 액세스 토큰 생성 (실제 데이터베이스 사용자와 관계없이)
        access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7일
        access_token = create_access_token(
            subject="admin_hardcoded", expires_delta=access_token_expires
        )
        
        print("하드코딩된 관리자 로그인 성공")
        
        return {
            "success": True, 
            "message": "관리자 로그인 성공",
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    print(f"하드코딩된 관리자 로그인 실패: 잘못된 계정 정보")
    return {
        "success": False, 
        "message": "잘못된 관리자 계정 정보입니다"
    }


@router.post("/test-token", response_model=UserSchema)
def test_token(current_user: UserModel = Depends(get_current_active_user)) -> Any:
    """
    현재 사용자 테스트
    """
    print(f"토큰 테스트: user={current_user.username}, auth={current_user.auth}")
    return current_user


@router.post("/password", response_model=Any)
def change_password(
    password_in: PasswordChange,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    비밀번호 변경
    """
    # 비밀번호 확인
    if not verify_password(password_in.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    if password_in.new_password != password_in.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호가 일치하지 않습니다"
        )
    
    user = crud_change_password(
        db, 
        user_id=current_user.id, 
        current_password=password_in.current_password, 
        new_password=password_in.new_password
    )
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}


@router.get("/me", response_model=Any)
def get_me(current_user: UserModel = Depends(get_current_active_user)) -> Any:
    """
    현재 로그인한 사용자 정보 가져오기
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "employee_id": current_user.employee_id,
        "department": current_user.department,
        "position": current_user.position,
        "level": current_user.level,
        "auth": current_user.auth,
        "points": current_user.points
    } 