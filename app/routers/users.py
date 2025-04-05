from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_active_user,
    get_current_admin_user
)
from app.crud.user import (
    get_user,
    get_users,
    get_users_by_department,
    get_top_users,
    update_user,
    admin_update_user,
    delete_user
)
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate, AdminUserUpdate

router = APIRouter(prefix="/users", tags=["사용자"])


@router.get("/", response_model=List[UserSchema])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    사용자 목록 조회
    """
    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/department/{department}", response_model=List[UserSchema])
def read_users_by_department(
    department: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    부서별 사용자 목록 조회
    """
    users = get_users_by_department(db, department=department, skip=skip, limit=limit)
    return users


@router.get("/top", response_model=List[UserSchema])
def read_top_users(
    limit: int = 10,
    db: Session = Depends(get_db)
) -> Any:
    """
    포인트 기준 상위 사용자 조회
    """
    users = get_top_users(db, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    특정 사용자 정보 조회
    """
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    return user


@router.put("/me", response_model=UserSchema)
def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    현재 로그인한 사용자 정보 업데이트
    """
    user = update_user(db, user_id=current_user.id, user=user_in)
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user_by_admin(
    user_id: int,
    user_in: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    관리자 권한으로 사용자 정보 업데이트
    """
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    user = admin_update_user(db, user_id=user_id, user=user_in)
    return user


@router.delete("/{user_id}", response_model=UserSchema)
def delete_user_by_admin(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    관리자 권한으로 사용자 삭제
    """
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 자기 자신은 삭제할 수 없음
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신을 삭제할 수 없습니다"
        )
    
    user = delete_user(db, user_id=user_id)
    return user 