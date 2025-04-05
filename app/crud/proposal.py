from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import func, desc, asc, and_
import os
import shutil
from uuid import uuid4

from app.models.proposal import Proposal, ProposalStatus, ProposalCategory, Vote, Comment, Attachment
from app.models.user import User
from app.schemas.proposal import ProposalCreate, ProposalUpdate, AdminProposalUpdate, CommentCreate, CommentUpdate, VoteCreate
from app.crud.user import get_user, update_user_points
from app.core.config import settings


def get_proposal(db: Session, proposal_id: int) -> Optional[Proposal]:
    """ID로 제안 조회"""
    return db.query(Proposal).filter(Proposal.id == proposal_id).first()


def get_proposals(
    db: Session, 
    skip: int = 0, 
    limit: int = 20,
    status: Optional[ProposalStatus] = None,
    category: Optional[ProposalCategory] = None,
    user_id: Optional[int] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True
) -> Tuple[List[Proposal], int]:
    """제안 목록 조회 (필터링 포함)"""
    query = db.query(Proposal)
    
    # 필터 적용
    if status:
        query = query.filter(Proposal.status == status)
    if category:
        query = query.filter(Proposal.category == category)
    if user_id:
        query = query.filter(Proposal.user_id == user_id)
    if department:
        query = query.filter(Proposal.department == department)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Proposal.title.ilike(search_term) | 
            Proposal.content.ilike(search_term)
        )
    
    # 전체 카운트
    total = query.count()
    
    # 정렬 적용
    sort_column = getattr(Proposal, sort_by, Proposal.created_at)
    if sort_desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # 페이징 적용
    proposals = query.offset(skip).limit(limit).all()
    
    return proposals, total


def create_proposal(db: Session, proposal: ProposalCreate, user_id: int, before_image: UploadFile = None, after_image: UploadFile = None, status: str = "DRAFT") -> Proposal:
    """제안 생성 (이미지 첨부 포함)"""
    # 사용자 확인
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 이미지 처리 디버깅 로그
    print(f"이미지 처리 시작: before_image={before_image}, after_image={after_image}")
    print(f"제안 상태: {status}")
    
    # 제안 생성
    db_proposal = Proposal(
        title=proposal.title,
        content=proposal.content,
        category=proposal.category,
        status=ProposalStatus(status),  # 매개변수로 받은 상태로 설정
        user_id=user_id,
        department=user.department,  # 사용자의 부서로 설정
        expected_effect=proposal.expected_effect,
        benefit_amount=proposal.benefit_amount
    )
    
    # DB에 제안 먼저 저장 (이미지 저장을 위해 ID 필요)
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    
    # 개선 전/후 이미지 처리
    if before_image and after_image:
        try:
            # 업로드 디렉토리 설정
            upload_dir = os.path.join(settings.UPLOAD_DIR, f"proposal_{db_proposal.id}")
            os.makedirs(upload_dir, exist_ok=True)
            print(f"업로드 디렉토리 생성: {upload_dir}")
            
            # 개선 전 이미지 저장
            before_filename = before_image.filename
            before_ext = os.path.splitext(before_filename)[1]
            before_safe_filename = f"before_{uuid4().hex}{before_ext}"
            before_filepath = os.path.join(upload_dir, before_safe_filename)
            
            print(f"개선 전 이미지 저장 경로: {before_filepath}")
            with open(before_filepath, "wb") as f:
                shutil.copyfileobj(before_image.file, f)
            print("개선 전 이미지 저장 완료")
            
            # 개선 후 이미지 저장
            after_filename = after_image.filename
            after_ext = os.path.splitext(after_filename)[1]
            after_safe_filename = f"after_{uuid4().hex}{after_ext}"
            after_filepath = os.path.join(upload_dir, after_safe_filename)
            
            print(f"개선 후 이미지 저장 경로: {after_filepath}")
            with open(after_filepath, "wb") as f:
                shutil.copyfileobj(after_image.file, f)
            print("개선 후 이미지 저장 완료")
            
            # 이미지 경로 저장
            db_proposal.before_image = os.path.join(f"uploads/proposal_{db_proposal.id}", before_safe_filename)
            db_proposal.after_image = os.path.join(f"uploads/proposal_{db_proposal.id}", after_safe_filename)
            print(f"DB에 저장된 이미지 경로: before={db_proposal.before_image}, after={db_proposal.after_image}")
            
            db.commit()
            db.refresh(db_proposal)
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {str(e)}")
            # 오류가 있더라도 제안서는 저장
    else:
        print("이미지가 제공되지 않았습니다.")
    
    # 포인트 부여 (제안 작성: 10 포인트)
    update_user_points(db, user_id, 10)
    
    return db_proposal


def update_proposal(db: Session, proposal_id: int, proposal: ProposalUpdate, user_id: int, before_image: UploadFile = None, after_image: UploadFile = None) -> Proposal:
    """제안 수정 (이미지 포함)"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 권한 확인 (작성자만 수정 가능)
    if db_proposal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="제안을 수정할 권한이 없습니다"
        )
    
    # 상태 확인 (임시저장 상태만 수정 가능)
    if db_proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="임시저장 상태의 제안만 수정 가능합니다"
        )
    
    # 기본 데이터 업데이트
    print(f"기본 데이터 업데이트 시작: proposal_id={proposal_id}")
    update_data = proposal.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_proposal, key, value)
    
    # 개선 전/후 이미지 처리
    if before_image or after_image:
        try:
            print(f"이미지 업데이트 시작: before_image={before_image}, after_image={after_image}")
            
            # 업로드 디렉토리 설정
            upload_dir = os.path.join(settings.UPLOAD_DIR, f"proposal_{db_proposal.id}")
            os.makedirs(upload_dir, exist_ok=True)
            print(f"업로드 디렉토리 확인: {upload_dir}")
            
            # 개선 전 이미지 업데이트
            if before_image:
                # 기존 파일 삭제 (있을 경우)
                if db_proposal.before_image and os.path.exists(db_proposal.before_image):
                    try:
                        os.remove(db_proposal.before_image)
                        print(f"기존 before_image 삭제: {db_proposal.before_image}")
                    except Exception as e:
                        print(f"기존 before_image 삭제 실패: {str(e)}")
                
                # 새 이미지 저장
                before_filename = before_image.filename
                before_ext = os.path.splitext(before_filename)[1]
                before_safe_filename = f"before_{uuid4().hex}{before_ext}"
                before_filepath = os.path.join(upload_dir, before_safe_filename)
                
                print(f"새 before_image 저장 경로: {before_filepath}")
                with open(before_filepath, "wb") as f:
                    shutil.copyfileobj(before_image.file, f)
                print("새 before_image 저장 완료")
                
                # 이미지 경로 업데이트
                db_proposal.before_image = os.path.join(f"uploads/proposal_{db_proposal.id}", before_safe_filename)
                print(f"DB에 before_image 경로 업데이트: {db_proposal.before_image}")
            
            # 개선 후 이미지 업데이트
            if after_image:
                # 기존 파일 삭제 (있을 경우)
                if db_proposal.after_image and os.path.exists(db_proposal.after_image):
                    try:
                        os.remove(db_proposal.after_image)
                        print(f"기존 after_image 삭제: {db_proposal.after_image}")
                    except Exception as e:
                        print(f"기존 after_image 삭제 실패: {str(e)}")
                
                # 새 이미지 저장
                after_filename = after_image.filename
                after_ext = os.path.splitext(after_filename)[1]
                after_safe_filename = f"after_{uuid4().hex}{after_ext}"
                after_filepath = os.path.join(upload_dir, after_safe_filename)
                
                print(f"새 after_image 저장 경로: {after_filepath}")
                with open(after_filepath, "wb") as f:
                    shutil.copyfileobj(after_image.file, f)
                print("새 after_image 저장 완료")
                
                # 이미지 경로 업데이트
                db_proposal.after_image = os.path.join(f"uploads/proposal_{db_proposal.id}", after_safe_filename)
                print(f"DB에 after_image 경로 업데이트: {db_proposal.after_image}")
        except Exception as e:
            print(f"이미지 업데이트 중 오류 발생: {str(e)}")
            # 이미지 업데이트 실패해도 기본 데이터는 업데이트
    else:
        print("이미지 업데이트 없음")
    
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


def admin_update_proposal(db: Session, proposal_id: int, proposal: AdminProposalUpdate) -> Proposal:
    """관리자 권한으로 제안 수정"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    update_data = proposal.dict(exclude_unset=True)
    
    # 상태 변경이 있을 경우 처리
    old_status = db_proposal.status
    new_status = update_data.get("status", old_status)
    
    # 상태가 변경되었고, 승인 상태로 변경된 경우 포인트 부여
    if old_status != new_status and new_status == ProposalStatus.APPROVED:
        # 제안 승인: 100 포인트
        update_user_points(db, db_proposal.user_id, 100)
    
    for key, value in update_data.items():
        setattr(db_proposal, key, value)
    
    db.commit()
    db.refresh(db_proposal)
    return db_proposal


def delete_proposal(db: Session, proposal_id: int, user_id: int) -> Proposal:
    """제안 삭제"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 권한 확인 (작성자만 삭제 가능)
    if db_proposal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="제안을 삭제할 권한이 없습니다"
        )
    
    # 상태 확인 (임시저장 상태만 삭제 가능)
    if db_proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="임시저장 상태의 제안만 삭제 가능합니다"
        )
    
    db.delete(db_proposal)
    db.commit()
    return db_proposal


def admin_delete_proposal(db: Session, proposal_id: int) -> Proposal:
    """관리자 권한으로 제안 삭제"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    db.delete(db_proposal)
    db.commit()
    return db_proposal


def submit_proposal(db: Session, proposal_id: int, user_id: int) -> Proposal:
    """제안 제출"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 권한 확인 (작성자만 제출 가능)
    if db_proposal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="제안을 제출할 권한이 없습니다"
        )
    
    # 상태 확인 (임시저장 상태만 제출 가능)
    if db_proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="임시저장 상태의 제안만 제출 가능합니다"
        )
    
    db_proposal.status = ProposalStatus.SUBMITTED
    db.commit()
    db.refresh(db_proposal)
    
    # 포인트 부여 (제안 제출: 20 포인트)
    update_user_points(db, user_id, 20)
    
    return db_proposal


# 댓글 관련 CRUD 기능
def get_comments(db: Session, proposal_id: int) -> List[Comment]:
    """제안의 댓글 목록 조회"""
    return db.query(Comment).filter(Comment.proposal_id == proposal_id).all()


def create_comment(db: Session, proposal_id: int, comment: CommentCreate, user_id: int) -> Comment:
    """댓글 생성"""
    # 제안 확인
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 사용자 확인
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 부모 댓글 확인 (있을 경우)
    if comment.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부모 댓글을 찾을 수 없습니다"
            )
    
    # 댓글 생성
    db_comment = Comment(
        content=comment.content,
        user_id=user_id,
        proposal_id=proposal_id,
        parent_id=comment.parent_id
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    # 포인트 부여 (댓글 작성: 5 포인트)
    update_user_points(db, user_id, 5)
    
    return db_comment


def update_comment(db: Session, comment_id: int, comment: CommentUpdate, user_id: int) -> Comment:
    """댓글 수정"""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다"
        )
    
    # 권한 확인 (작성자만 수정 가능)
    if db_comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="댓글을 수정할 권한이 없습니다"
        )
    
    db_comment.content = comment.content
    db_comment.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: int, user_id: int) -> Comment:
    """댓글 삭제"""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다"
        )
    
    # 권한 확인 (작성자만 삭제 가능)
    if db_comment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="댓글을 삭제할 권한이 없습니다"
        )
    
    db.delete(db_comment)
    db.commit()
    return db_comment


# 투표 관련 CRUD 기능
def get_vote(db: Session, proposal_id: int, user_id: int) -> Optional[Vote]:
    """사용자의 제안에 대한 투표 조회"""
    return db.query(Vote).filter(
        Vote.proposal_id == proposal_id,
        Vote.user_id == user_id
    ).first()


def get_votes(db: Session, proposal_id: int) -> List[Vote]:
    """제안의 모든 투표 조회"""
    return db.query(Vote).filter(Vote.proposal_id == proposal_id).all()


def create_or_update_vote(db: Session, proposal_id: int, vote: VoteCreate, user_id: int) -> Vote:
    """투표 생성 또는 수정"""
    # 제안 확인
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 제안 상태 확인 (제출됨, 검토 중 상태만 투표 가능)
    if db_proposal.status not in [ProposalStatus.SUBMITTED, ProposalStatus.REVIEWING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="투표가 가능한 상태의 제안이 아닙니다"
        )
    
    # 자기 자신의 제안에는 투표 불가
    if db_proposal.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 제안에는 투표할 수 없습니다"
        )
    
    # 이미 투표한 경우 업데이트
    db_vote = get_vote(db, proposal_id, user_id)
    if db_vote:
        old_vote_value = db_vote.vote_value
        db_vote.vote_value = vote.vote_value
        
        # 제안 작성자에게 포인트 부여/차감 (기존 반대에서 찬성으로 변경: +2, 기존 찬성에서 반대로 변경: -2)
        if old_vote_value == -1 and vote.vote_value == 1:
            update_user_points(db, db_proposal.user_id, 2)
        elif old_vote_value == 1 and vote.vote_value == -1:
            update_user_points(db, db_proposal.user_id, -2)
    else:
        # 새로운 투표 생성
        db_vote = Vote(
            user_id=user_id,
            proposal_id=proposal_id,
            vote_value=vote.vote_value
        )
        db.add(db_vote)
        
        # 제안 작성자에게 포인트 부여/차감 (찬성: +1, 반대: -1)
        if vote.vote_value == 1:
            update_user_points(db, db_proposal.user_id, 1)
        elif vote.vote_value == -1:
            update_user_points(db, db_proposal.user_id, -1)
    
    db.commit()
    db.refresh(db_vote)
    return db_vote


def delete_vote(db: Session, proposal_id: int, user_id: int) -> Vote:
    """투표 삭제"""
    db_vote = get_vote(db, proposal_id, user_id)
    if not db_vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="투표를 찾을 수 없습니다"
        )
    
    # 제안 작성자에게 포인트 차감 (찬성 취소: -1, 반대 취소: +1)
    if db_vote.vote_value == 1:
        update_user_points(db, get_proposal(db, proposal_id).user_id, -1)
    elif db_vote.vote_value == -1:
        update_user_points(db, get_proposal(db, proposal_id).user_id, 1)
    
    db.delete(db_vote)
    db.commit()
    return db_vote


# 첨부 파일 관련 CRUD 기능
def get_attachment(db: Session, attachment_id: int) -> Optional[Attachment]:
    """첨부 파일 조회"""
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()


def get_attachments(db: Session, proposal_id: int) -> List[Attachment]:
    """제안의 모든 첨부 파일 조회"""
    return db.query(Attachment).filter(Attachment.proposal_id == proposal_id).all()


def create_attachment(
    db: Session, 
    proposal_id: int, 
    filename: str, 
    filepath: str, 
    filesize: int, 
    file_type: str
) -> Attachment:
    """첨부 파일 생성"""
    # 제안 확인
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 첨부 파일 생성
    db_attachment = Attachment(
        proposal_id=proposal_id,
        filename=filename,
        filepath=filepath,
        filesize=filesize,
        file_type=file_type
    )
    
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def delete_attachment(db: Session, attachment_id: int, user_id: int) -> Attachment:
    """첨부 파일 삭제"""
    db_attachment = get_attachment(db, attachment_id)
    if not db_attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부 파일을 찾을 수 없습니다"
        )
    
    # 제안 확인
    db_proposal = get_proposal(db, db_attachment.proposal_id)
    
    # 권한 확인 (제안 작성자만 삭제 가능)
    if db_proposal.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="첨부 파일을 삭제할 권한이 없습니다"
        )
    
    db.delete(db_attachment)
    db.commit()
    return db_attachment


def get_user_proposals(
    db: Session, 
    user_id: int,
    skip: int = 0, 
    limit: int = 20,
    status: Optional[ProposalStatus] = None
) -> List[Proposal]:
    """특정 사용자의 제안 목록 조회"""
    query = db.query(Proposal).filter(Proposal.user_id == user_id)
    
    if status:
        query = query.filter(Proposal.status == status)
    
    return query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()


def get_department_proposals(
    db: Session, 
    department: str,
    skip: int = 0, 
    limit: int = 20,
    status: Optional[ProposalStatus] = None
) -> List[Proposal]:
    """부서 제안 목록 조회"""
    query = db.query(Proposal).filter(Proposal.department == department)
    
    if status:
        query = query.filter(Proposal.status == status)
    
    return query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()


def get_factory_proposals(
    db: Session, 
    factory: str,
    skip: int = 0, 
    limit: int = 20,
    status: Optional[ProposalStatus] = None
) -> List[Proposal]:
    """공장 제안 목록 조회"""
    query = db.query(Proposal).filter(Proposal.factory == factory)
    
    if status:
        query = query.filter(Proposal.status == status)
    
    return query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()


def approve_proposal(db: Session, proposal_id: int, feedback: Optional[str] = None) -> Proposal:
    """제안 승인"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 상태 확인 (제출 상태만 승인 가능)
    if db_proposal.status != ProposalStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="제출된 상태의 제안만 승인 가능합니다"
        )
    
    db_proposal.status = ProposalStatus.APPROVED
    
    # 피드백이 있으면 저장 (구현 시 추가 필드가 필요할 수 있음)
    if feedback:
        # 이 예제에서는 Comment로 피드백을 저장한다고 가정
        feedback_comment = Comment(
            content=feedback,
            user_id=1,  # 시스템 사용자 ID 또는 승인자 ID
            proposal_id=proposal_id
        )
        db.add(feedback_comment)
    
    db.commit()
    db.refresh(db_proposal)
    
    # 포인트 부여 (제안 승인: 50 포인트)
    update_user_points(db, db_proposal.user_id, 50)
    
    return db_proposal


def reject_proposal(db: Session, proposal_id: int, feedback: Optional[str] = None) -> Proposal:
    """제안 거부"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 상태 확인 (제출 또는 승인 상태만 거부 가능)
    if db_proposal.status not in [ProposalStatus.SUBMITTED, ProposalStatus.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="제출 또는 승인된 상태의 제안만 거부 가능합니다"
        )
    
    db_proposal.status = ProposalStatus.REJECTED
    
    # 피드백이 있으면 저장
    if feedback:
        feedback_comment = Comment(
            content=feedback,
            user_id=1,  # 시스템 사용자 ID 또는 거부자 ID
            proposal_id=proposal_id
        )
        db.add(feedback_comment)
    
    db.commit()
    db.refresh(db_proposal)
    
    return db_proposal


def implement_proposal(db: Session, proposal_id: int, feedback: Optional[str] = None) -> Proposal:
    """제안 구현 완료"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 상태 확인 (승인 상태만 구현 완료 가능)
    if db_proposal.status != ProposalStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="승인된 상태의 제안만 구현 완료 처리 가능합니다"
        )
    
    db_proposal.status = ProposalStatus.IMPLEMENTED
    
    # 피드백이 있으면 저장
    if feedback:
        feedback_comment = Comment(
            content=feedback,
            user_id=1,  # 시스템 사용자 ID 또는 구현 담당자 ID
            proposal_id=proposal_id
        )
        db.add(feedback_comment)
    
    db.commit()
    db.refresh(db_proposal)
    
    # 포인트 부여 (제안 구현 완료: 100 포인트)
    update_user_points(db, db_proposal.user_id, 100)
    
    return db_proposal


def upload_attachment(db: Session, proposal_id: int, file: UploadFile) -> Proposal:
    """제안에 첨부 파일 업로드"""
    db_proposal = get_proposal(db, proposal_id)
    if not db_proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안을 찾을 수 없습니다"
        )
    
    # 파일 저장 경로 설정
    upload_dir = os.path.join(settings.UPLOAD_DIR, f"proposal_{proposal_id}")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 안전한 파일명 생성
    filename = file.filename
    file_ext = os.path.splitext(filename)[1]
    safe_filename = f"{uuid4().hex}{file_ext}"
    filepath = os.path.join(upload_dir, safe_filename)
    
    # 파일 저장
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # 첨부 파일 레코드 생성
    filesize = os.path.getsize(filepath)
    file_type = file.content_type
    
    db_attachment = Attachment(
        proposal_id=proposal_id,
        filename=filename,
        filepath=filepath,
        filesize=filesize,
        file_type=file_type
    )
    
    db.add(db_attachment)
    db.commit()
    db.refresh(db_proposal)
    
    return db_proposal 