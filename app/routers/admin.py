from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserAuth
from app.models.proposal import Proposal, ProposalStatus, ProposalCategory

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# 관리자 권한 확인 함수
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.auth != UserAuth.ADMIN:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    return current_user

@router.get("/dashboard")
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    관리자 대시보드 통계 데이터 조회
    """
    from sqlalchemy import func, distinct
    from datetime import datetime, timedelta
    
    # 전체 제안 수
    total_proposals = db.query(func.count(Proposal.id)).scalar()
    
    # 승인된 제안 수
    approved_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.status == ProposalStatus.APPROVED
    ).scalar()
    
    # 구현된 제안 수
    implemented_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.status == ProposalStatus.IMPLEMENTED
    ).scalar()
    
    # 전체 사용자 수
    total_users = db.query(func.count(User.id)).scalar()
    
    # 카테고리별 제안 수
    category_stats = []
    for category in ProposalCategory:
        count = db.query(func.count(Proposal.id)).filter(
            Proposal.category == category
        ).scalar()
        category_stats.append({"category": category.value, "count": count})
    
    # 부서별 제안 수
    department_stats = db.query(
        Proposal.department,
        func.count(Proposal.id).label('count')
    ).group_by(Proposal.department).all()
    department_stats = [{"department": dept, "count": count} for dept, count in department_stats]
    
    # 월별 제안 추세 (최근 6개월)
    today = datetime.now()
    six_months_ago = today - timedelta(days=180)
    
    # SQLite와 호환되는 방식으로 변경
    monthly_trends = db.query(
        func.strftime('%Y-%m', Proposal.created_at).label('month'),
        func.count(Proposal.id).label('count')
    ).filter(
        Proposal.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()
    monthly_trends = [{"month": month, "count": count} for month, count in monthly_trends]
    
    return {
        "total_proposals": total_proposals,
        "approved_proposals": approved_proposals,
        "implemented_proposals": implemented_proposals,
        "total_users": total_users,
        "category_stats": category_stats,
        "department_stats": department_stats,
        "monthly_trends": monthly_trends
    }

@router.get("/users")
async def get_users(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    모든 사용자 목록 조회 (관리자 전용)
    """
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.full_name.contains(search)) |
            (User.employee_id.contains(search))
        )
    
    if department:
        query = query.filter(User.department == department)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": users
    }

@router.get("/proposals")
async def get_all_proposals(
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    모든 제안 목록 조회 (관리자 전용)
    """
    query = db.query(Proposal).join(User)
    
    if status:
        query = query.filter(Proposal.status == status)
    
    if category:
        query = query.filter(Proposal.category == category)
    
    if department:
        query = query.filter(Proposal.department == department)
    
    if search:
        query = query.filter(
            (Proposal.title.contains(search)) |
            (Proposal.content.contains(search)) |
            (User.full_name.contains(search))
        )
    
    total = query.count()
    proposals = query.order_by(Proposal.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": proposals
    }

@router.put("/proposals/{proposal_id}/status")
async def update_proposal_status(
    proposal_id: int,
    status: ProposalStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    제안 상태 업데이트 (관리자 전용)
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="제안을 찾을 수 없습니다")
    
    proposal.status = status
    db.commit()
    db.refresh(proposal)
    return proposal 