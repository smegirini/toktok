from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import func, desc

from app.models.user import User, UserLevel, UserAuth
from app.schemas.user import UserCreate, UserUpdate, AdminUserUpdate
from app.core.security import get_password_hash, verify_password


def get_user(db: Session, user_id: int) -> Optional[User]:
    """ID로 사용자 조회"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """유저명으로 사용자 조회"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_employee_id(db: Session, employee_id: str) -> Optional[User]:
    """사번으로 사용자 조회"""
    return db.query(User).filter(User.employee_id == employee_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """전체 사용자 조회"""
    return db.query(User).offset(skip).limit(limit).all()


def get_users_by_department(db: Session, department: str, skip: int = 0, limit: int = 100) -> List[User]:
    """부서별 사용자 조회"""
    return db.query(User).filter(User.department == department).offset(skip).limit(limit).all()


def get_top_users(db: Session, limit: int = 10) -> List[User]:
    """포인트 기준 상위 사용자 조회"""
    return db.query(User).order_by(User.points.desc()).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """사용자 생성"""
    # 기존 사용자 확인
    print(f"create_user 함수 시작: username={user.username}, email={user.email}")
    
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        print(f"create_user 중단: 이미 존재하는 username={user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사용자명입니다"
        )
    
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        print(f"create_user 중단: 이미 존재하는 email={user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일 주소입니다"
        )
    
    db_user = get_user_by_employee_id(db, employee_id=user.employee_id)
    if db_user:
        print(f"create_user 중단: 이미 존재하는 employee_id={user.employee_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 사번입니다"
        )
    
    # 패스워드 해싱
    hashed_password = get_password_hash(user.password)
    print(f"비밀번호 해싱 완료: username={user.username}")
    
    try:
        # 기본 사용자 정보 생성
        db_user = User(
            username=user.username,
            email=user.email,
            employee_id=user.employee_id,
            full_name=user.full_name,
            hashed_password=hashed_password,
            department=user.department,
            position=user.position,
            level=UserLevel.COMMONER,
            auth=UserAuth.USER
        )
        
        print(f"사용자 객체 생성 완료: {db_user}")
        db.add(db_user)
        db.commit()
        print(f"DB 저장 완료: username={user.username}")
        db.refresh(db_user)
        return db_user
    except Exception as e:
        print(f"create_user 예외 발생: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 생성 중 오류: {str(e)}"
        )


def update_user(db: Session, user_id: int, user: UserUpdate) -> User:
    """사용자 정보 수정"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    update_data = user.dict(exclude_unset=True)
    
    # 비밀번호가 있으면 해싱
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def admin_update_user(db: Session, user_id: int, user: AdminUserUpdate) -> User:
    """관리자 권한으로 사용자 정보 수정"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    update_data = user.dict(exclude_unset=True)
    
    # 비밀번호가 있으면 해싱
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> User:
    """사용자 삭제"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    db.delete(db_user)
    db.commit()
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """사용자 인증"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> User:
    """비밀번호 변경"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if not verify_password(current_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다"
        )
    
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_points(db: Session, user_id: int, points: int) -> User:
    """사용자 포인트 업데이트"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    db_user.points += points
    
    # 등급 자동 업데이트 로직
    update_user_level(db, db_user)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_level(db: Session, user: User) -> None:
    """사용자 등급 자동 업데이트"""
    points = user.points
    
    # 포인트에 따른 등급 결정
    if points >= 10000:
        user.level = UserLevel.ABSOLUTE_GOD
    elif points >= 5000:
        user.level = UserLevel.SUPREME
    elif points >= 2500:
        user.level = UserLevel.HERO
    elif points >= 1000:
        user.level = UserLevel.MASTER
    elif points >= 500:
        user.level = UserLevel.INTERMEDIATE
    elif points >= 100:
        user.level = UserLevel.BEGINNER
    else:
        user.level = UserLevel.COMMONER


def update_admin_status(db: Session) -> None:
    """admin 계정과 hankooktire 계정의 권한을 ADMIN으로 변경"""
    # admin 계정 권한 업데이트
    admin_user = get_user_by_username(db, username="admin")
    if admin_user:
        admin_user.auth = UserAuth.ADMIN
        db.commit()
        
    # hankooktire 계정 권한 업데이트
    hankook_user = get_user_by_username(db, username="hankooktire")
    if hankook_user:
        hankook_user.auth = UserAuth.ADMIN
        db.commit()
        print(f"hankooktire 계정 권한 업데이트 완료: {hankook_user.auth}")
    else:
        print("hankooktire 계정이 데이터베이스에 존재하지 않습니다.") 