from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, get_current_admin_user
from app.crud.ranking import (
    get_user_rankings, 
    get_department_rankings, 
    get_factory_rankings,
    get_proposals_rankings
)
from app.models.user import User
from app.schemas.ranking import (
    UserRanking,
    DepartmentRanking,
    FactoryRanking,
    ProposalRanking
)

router = APIRouter(prefix="/rankings", tags=["순위"])


@router.get("/users", response_model=List[UserRanking])
def read_user_rankings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    사용자 순위 조회
    포인트 기준으로 정렬된 사용자 목록 반환
    """
    rankings = get_user_rankings(db, skip=skip, limit=limit)
    return rankings


@router.get("/departments", response_model=List[DepartmentRanking])
def read_department_rankings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    부서별 순위 조회
    제안서 제출 수와 구현된 제안서 수를 기준으로 정렬된 부서 목록 반환
    """
    rankings = get_department_rankings(db, skip=skip, limit=limit)
    return rankings


@router.get("/factories", response_model=List[FactoryRanking])
def read_factory_rankings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    공장별 순위 조회
    제안서 제출 수와 구현된 제안서 수를 기준으로 정렬된 공장 목록 반환
    """
    rankings = get_factory_rankings(db, skip=skip, limit=limit)
    return rankings


@router.get("/proposals", response_model=List[ProposalRanking])
def read_proposal_rankings(
    skip: int = 0,
    limit: int = 10,
    time_period: str = "all",  # all, week, month, year
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    제안서 순위 조회
    좋아요 수, 조회수, 댓글 수를 기준으로 정렬된 제안서 목록 반환
    time_period 파라미터로 특정 기간 필터링 가능 (all, week, month, year)
    """
    # time_period 값 검증
    if time_period not in ["all", "week", "month", "year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 시간 범위입니다. 'all', 'week', 'month', 'year' 중 하나를 선택하세요."
        )
    
    rankings = get_proposals_rankings(db, skip=skip, limit=limit, time_period=time_period)
    return rankings 