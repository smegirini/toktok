from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc, cast, Date, Integer

from app.models.ranking import UserRanking, DepartmentRanking, ProposalStatistic, Badge, UserBadge
from app.models.user import User
from app.models.proposal import Proposal, ProposalStatus, Vote, Comment
from app.crud.user import get_user, get_top_users


def get_user_rankings(db: Session, period: str = "weekly", limit: int = 10) -> List[UserRanking]:
    """사용자 랭킹 조회"""
    return db.query(UserRanking).filter(
        UserRanking.ranking_period == period
    ).order_by(UserRanking.rank).limit(limit).all()


def get_department_rankings(db: Session, period: str = "weekly", limit: int = 10) -> List[DepartmentRanking]:
    """부서 랭킹 조회"""
    return db.query(DepartmentRanking).filter(
        DepartmentRanking.ranking_period == period
    ).order_by(DepartmentRanking.rank).limit(limit).all()


def get_factory_rankings(db: Session, period: str = "weekly", limit: int = 10) -> List[DepartmentRanking]:
    """공장 랭킹 조회"""
    # 이 예시에서는 DepartmentRanking 모델을 공장 랭킹에도 재사용
    return db.query(DepartmentRanking).filter(
        DepartmentRanking.ranking_period == period
    ).order_by(DepartmentRanking.rank).limit(limit).all()


def get_proposals_rankings(db: Session, skip: int = 0, limit: int = 10, time_period: str = "all") -> List[Proposal]:
    """제안서 랭킹 조회
    
    랭킹 기준:
    - 좋아요 수 (Vote 테이블에서 vote_value=1인 레코드 수)
    - 댓글 수
    """
    # 시간 필터링을 위한 날짜 범위 계산
    today = datetime.now().date()
    if time_period == "week":
        start_date = today - timedelta(days=7)
    elif time_period == "month":
        start_date = today - timedelta(days=30)
    elif time_period == "year":
        start_date = today - timedelta(days=365)
    else:  # "all"
        start_date = None
    
    # 좋아요 수와 댓글 수 집계 쿼리
    upvotes_subq = db.query(
        Vote.proposal_id,
        func.count(Vote.id).label("upvotes")
    ).filter(
        Vote.vote_value == 1
    ).group_by(Vote.proposal_id).subquery()
    
    comments_subq = db.query(
        Comment.proposal_id,
        func.count(Comment.id).label("comment_count")
    ).group_by(Comment.proposal_id).subquery()
    
    # 메인 쿼리
    query = db.query(Proposal)
    
    # 시간 필터 적용
    if start_date:
        query = query.filter(Proposal.created_at >= start_date)
    
    # 승인된 제안만 포함
    query = query.filter(Proposal.status.in_([ProposalStatus.APPROVED, ProposalStatus.IMPLEMENTED]))
    
    # 좋아요 수와 댓글 수로 정렬 (좋아요 수 우선, 그 다음 댓글 수)
    query = query.outerjoin(upvotes_subq, Proposal.id == upvotes_subq.c.proposal_id)
    query = query.outerjoin(comments_subq, Proposal.id == comments_subq.c.proposal_id)
    
    # NULL 값 처리를 위해 COALESCE 사용
    query = query.order_by(
        func.coalesce(upvotes_subq.c.upvotes, 0).desc(),
        func.coalesce(comments_subq.c.comment_count, 0).desc(),
        Proposal.created_at.desc()
    )
    
    return query.offset(skip).limit(limit).all()


def get_proposal_statistics(db: Session, period: str = "weekly") -> Optional[ProposalStatistic]:
    """제안 통계 조회"""
    return db.query(ProposalStatistic).filter(
        ProposalStatistic.reporting_period == period
    ).order_by(ProposalStatistic.created_at.desc()).first()


def get_badges(db: Session) -> List[Badge]:
    """배지 목록 조회"""
    return db.query(Badge).all()


def get_user_badges(db: Session, user_id: int) -> List[UserBadge]:
    """사용자 배지 목록 조회"""
    return db.query(UserBadge).filter(UserBadge.user_id == user_id).all()


def create_badge(db: Session, name: str, description: str, icon: str) -> Badge:
    """배지 생성"""
    db_badge = Badge(
        name=name,
        description=description,
        icon=icon
    )
    
    db.add(db_badge)
    db.commit()
    db.refresh(db_badge)
    return db_badge


def award_badge(db: Session, user_id: int, badge_id: int) -> UserBadge:
    """사용자에게 배지 수여"""
    # 이미 획득한 배지인지 확인
    existing_badge = db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.badge_id == badge_id
    ).first()
    
    if existing_badge:
        return existing_badge
    
    # 배지 수여
    db_user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge_id
    )
    
    db.add(db_user_badge)
    db.commit()
    db.refresh(db_user_badge)
    return db_user_badge


def update_user_rankings(db: Session, period: str = "weekly") -> List[UserRanking]:
    """사용자 랭킹 업데이트"""
    # 기간에 따른 날짜 범위 설정
    today = datetime.now().date()
    if period == "daily":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start_date = today.replace(day=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:
        start_date = today - timedelta(days=30)  # 기본값은 30일
    
    # 집계 쿼리 실행
    user_stats = db.query(
        User.id.label("user_id"),
        User.points.label("points"),
        func.count(Proposal.id).label("proposal_count"),
        func.sum(
            cast(Proposal.status == ProposalStatus.APPROVED, Integer)
        ).label("approved_count")
    ).outerjoin(
        Proposal, User.id == Proposal.user_id
    ).filter(
        Proposal.created_at >= start_date if period != "all" else True
    ).group_by(
        User.id
    ).order_by(
        desc("points")
    ).all()
    
    # 기존 랭킹 삭제
    db.query(UserRanking).filter(UserRanking.ranking_period == period).delete()
    
    # 새로운 랭킹 생성
    new_rankings = []
    for rank, stat in enumerate(user_stats, 1):
        user_ranking = UserRanking(
            user_id=stat.user_id,
            rank=rank,
            points=stat.points,
            proposal_count=stat.proposal_count or 0,
            approved_count=stat.approved_count or 0,
            ranking_period=period
        )
        db.add(user_ranking)
        new_rankings.append(user_ranking)
    
    db.commit()
    
    # 새로 생성한 랭킹 반환
    for ranking in new_rankings:
        db.refresh(ranking)
    
    return new_rankings


def update_department_rankings(db: Session, period: str = "weekly") -> List[DepartmentRanking]:
    """부서 랭킹 업데이트"""
    # 기간에 따른 날짜 범위 설정
    today = datetime.now().date()
    if period == "daily":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start_date = today.replace(day=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:
        start_date = today - timedelta(days=30)  # 기본값은 30일
    
    # 집계 쿼리 실행
    dept_stats = db.query(
        Proposal.department.label("department"),
        func.sum(User.points).label("points"),
        func.count(Proposal.id).label("proposal_count"),
        func.sum(
            cast(Proposal.status == ProposalStatus.APPROVED, Integer)
        ).label("approved_count")
    ).join(
        User, Proposal.user_id == User.id
    ).filter(
        Proposal.created_at >= start_date if period != "all" else True
    ).group_by(
        Proposal.department
    ).order_by(
        desc("points")
    ).all()
    
    # 기존 랭킹 삭제
    db.query(DepartmentRanking).filter(DepartmentRanking.ranking_period == period).delete()
    
    # 새로운 랭킹 생성
    new_rankings = []
    for rank, stat in enumerate(dept_stats, 1):
        dept_ranking = DepartmentRanking(
            department=stat.department,
            rank=rank,
            points=stat.points or 0,
            proposal_count=stat.proposal_count or 0,
            approved_count=stat.approved_count or 0,
            ranking_period=period
        )
        db.add(dept_ranking)
        new_rankings.append(dept_ranking)
    
    db.commit()
    
    # 새로 생성한 랭킹 반환
    for ranking in new_rankings:
        db.refresh(ranking)
    
    return new_rankings


def update_proposal_statistics(db: Session, period: str = "weekly") -> ProposalStatistic:
    """제안 통계 업데이트"""
    # 기간에 따른 날짜 범위 설정
    today = datetime.now().date()
    if period == "daily":
        start_date = today
    elif period == "weekly":
        start_date = today - timedelta(days=today.weekday())
    elif period == "monthly":
        start_date = today.replace(day=1)
    elif period == "yearly":
        start_date = today.replace(month=1, day=1)
    else:
        start_date = today - timedelta(days=30)  # 기본값은 30일
    
    # 총 제안 수
    total_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 승인된 제안 수
    approved_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.status == ProposalStatus.APPROVED,
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 거부된 제안 수
    rejected_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.status == ProposalStatus.REJECTED,
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 대기 중인 제안 수
    pending_proposals = db.query(func.count(Proposal.id)).filter(
        Proposal.status.in_([ProposalStatus.DRAFT, ProposalStatus.SUBMITTED, ProposalStatus.REVIEWING]),
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 평균 처리 시간 (일) - 제출에서 승인/거부까지
    avg_processing_time_subq = db.query(
        func.avg(
            func.julianday(Proposal.updated_at) - func.julianday(Proposal.created_at)
        )
    ).filter(
        Proposal.status.in_([ProposalStatus.APPROVED, ProposalStatus.REJECTED]),
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 총 효과 금액
    total_benefit_amount = db.query(func.sum(Proposal.benefit_amount)).filter(
        Proposal.status == ProposalStatus.APPROVED,
        Proposal.created_at >= start_date if period != "all" else True
    ).scalar() or 0
    
    # 기존 통계 삭제
    db.query(ProposalStatistic).filter(ProposalStatistic.reporting_period == period).delete()
    
    # 새로운 통계 생성
    db_statistic = ProposalStatistic(
        total_proposals=total_proposals,
        approved_proposals=approved_proposals,
        rejected_proposals=rejected_proposals,
        pending_proposals=pending_proposals,
        avg_processing_time=avg_processing_time_subq,
        total_benefit_amount=total_benefit_amount,
        reporting_period=period
    )
    
    db.add(db_statistic)
    db.commit()
    db.refresh(db_statistic)
    
    return db_statistic


def check_and_award_badges(db: Session, user_id: int) -> List[UserBadge]:
    """사용자 업적 배지 확인 및 수여"""
    # 사용자 정보 조회
    user = get_user(db, user_id)
    if not user:
        return []
    
    # 사용자의 제안 통계
    proposal_count = db.query(func.count(Proposal.id)).filter(
        Proposal.user_id == user_id
    ).scalar() or 0
    
    approved_count = db.query(func.count(Proposal.id)).filter(
        Proposal.user_id == user_id,
        Proposal.status == ProposalStatus.APPROVED
    ).scalar() or 0
    
    implemented_count = db.query(func.count(Proposal.id)).filter(
        Proposal.user_id == user_id,
        Proposal.status == ProposalStatus.IMPLEMENTED
    ).scalar() or 0
    
    # 새로 획득한 배지 목록
    new_badges = []
    
    # 배지 조건 확인 및 수여
    # 1. 첫 제안 작성
    if proposal_count >= 1:
        first_proposal_badge = db.query(Badge).filter(Badge.name == "첫 제안 작성").first()
        if first_proposal_badge:
            badge = award_badge(db, user_id, first_proposal_badge.id)
            new_badges.append(badge)
    
    # 2. 제안 마스터 (10개 이상 제안)
    if proposal_count >= 10:
        proposal_master_badge = db.query(Badge).filter(Badge.name == "제안 마스터").first()
        if proposal_master_badge:
            badge = award_badge(db, user_id, proposal_master_badge.id)
            new_badges.append(badge)
    
    # 3. 첫 승인 제안
    if approved_count >= 1:
        first_approved_badge = db.query(Badge).filter(Badge.name == "첫 승인 제안").first()
        if first_approved_badge:
            badge = award_badge(db, user_id, first_approved_badge.id)
            new_badges.append(badge)
    
    # 4. 구현 성공 (구현된 제안 1개 이상)
    if implemented_count >= 1:
        implemented_badge = db.query(Badge).filter(Badge.name == "구현 성공").first()
        if implemented_badge:
            badge = award_badge(db, user_id, implemented_badge.id)
            new_badges.append(badge)
    
    # 5. 포인트 획득자 (1000점 이상)
    if user.points >= 1000:
        points_badge = db.query(Badge).filter(Badge.name == "포인트 획득자").first()
        if points_badge:
            badge = award_badge(db, user_id, points_badge.id)
            new_badges.append(badge)
    
    return new_badges 