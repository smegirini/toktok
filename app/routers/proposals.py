from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_active_user,
    get_current_admin_user,
    get_current_factory_user,
    get_current_department_user
)
from app.crud.proposal import (
    get_proposal,
    get_proposals,
    get_user_proposals,
    get_department_proposals,
    get_factory_proposals,
    create_proposal,
    update_proposal,
    delete_proposal,
    approve_proposal,
    reject_proposal,
    implement_proposal,
    upload_attachment
)
from app.models.user import User as UserModel
from app.models.proposal import ProposalCategory
from app.schemas.proposal import (
    Proposal,
    ProposalCreate,
    ProposalUpdate,
    ProposalOut,
    ProposalList,
    ProposalStatusUpdate
)

router = APIRouter(prefix="/proposals", tags=["제안서"])


@router.get("/", response_model=List[ProposalList])
def read_proposals(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    모든 제안서 목록 조회 (관리자용)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 부족합니다"
        )
    proposals = get_proposals(db, skip=skip, limit=limit, status=status)
    return proposals


@router.get("/me", response_model=List[ProposalList])
def read_my_proposals(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    현재 사용자의 제안서 목록 조회
    """
    proposals = get_user_proposals(db, user_id=current_user.id, skip=skip, limit=limit, status=status)
    return proposals


@router.get("/department", response_model=List[ProposalList])
def read_department_proposals(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: UserModel = Depends(get_current_department_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    부서 담당자용 제안서 목록 조회
    """
    proposals = get_department_proposals(db, department=current_user.department, skip=skip, limit=limit, status=status)
    return proposals


@router.get("/factory", response_model=List[ProposalList])
def read_factory_proposals(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    current_user: UserModel = Depends(get_current_factory_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    공장 담당자용 제안서 목록 조회
    """
    proposals = get_factory_proposals(db, factory=current_user.factory, skip=skip, limit=limit, status=status)
    return proposals


@router.get("/{proposal_id}", response_model=ProposalOut)
def read_proposal(
    proposal_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    특정 제안서 조회
    """
    proposal = get_proposal(db, proposal_id=proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안서를 찾을 수 없습니다"
        )
    
    # 권한 검사: 작성자 또는 관리자/담당자만 볼 수 있음
    if (proposal.user_id != current_user.id and 
        not current_user.is_admin and 
        not (current_user.is_department_manager and proposal.department == current_user.department) and
        not (current_user.is_factory_manager and proposal.factory == current_user.factory)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 제안서를 볼 권한이 없습니다"
        )
    
    return proposal


@router.post("/", response_model=Proposal)
async def create_new_proposal(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    expected_effect: Optional[str] = Form(None),
    benefit_amount: Optional[float] = Form(None),
    before_image: Optional[UploadFile] = File(None),
    after_image: Optional[UploadFile] = File(None),
    attachments: Optional[List[UploadFile]] = File(None),
    status: Optional[str] = Form("DRAFT"),  # 기본값은 임시저장
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    새 제안 생성 (이미지 첨부 포함)
    """
    # 디버깅 로그 추가
    print(f"새 제안 생성 요청: user={current_user.username}, title={title}")
    print(f"이미지 첨부 확인: before_image={before_image}, after_image={after_image}")
    
    try:
        # 관리자 사용자 확인
        if current_user.is_admin:
            print(f"관리자 권한으로 제안 생성 시도: {current_user.username}")
        
        # 제출 시에만 이미지 필수 검사 (임시저장은 필수 아님)
        if status == "SUBMITTED" and (not before_image or not after_image):
            print(f"이미지 누락: before_image={before_image is not None}, after_image={after_image is not None}")
            # 이미지가 필수이지만 없는 경우 경고만 하고 계속 진행 (클라이언트에서 검증하도록 함)
            print("이미지가 누락되었지만 제출 허용")
        
        # 카테고리 유효성 검사
        try:
            proposal_category = ProposalCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 카테고리입니다: {category}"
            )
        
        # 제안서 데이터 생성
        proposal_data = ProposalCreate(
            title=title,
            content=content,
            category=proposal_category,
            expected_effect=expected_effect,
            benefit_amount=float(benefit_amount) if benefit_amount else 0.0
        )
        
        # 제안 상태 설정
        proposal_status = status
        
        # 제안서 생성
        proposal = create_proposal(
            db=db, 
            proposal=proposal_data, 
            user_id=current_user.id,
            before_image=before_image,
            after_image=after_image,
            status=proposal_status
        )
        
        # 추가 첨부파일 업로드 처리
        if attachments:
            for file in attachments:
                if file and file.filename:  # 파일명이 있는 경우만 처리
                    upload_attachment(db, proposal_id=proposal.id, file=file)
        
        print(f"제안 생성 성공: proposal_id={proposal.id}")
        return proposal
        
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        print(f"HTTP 예외 발생: {e.status_code}, {e.detail}")
        raise
    except Exception as e:
        # 그 외 예외는 500 에러로 변환
        print(f"예외 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제안 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/{proposal_id}/attachments", response_model=Proposal)
def upload_proposal_attachment(
    proposal_id: int,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    제안서에 첨부파일 업로드
    """
    proposal = get_proposal(db, proposal_id=proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안서를 찾을 수 없습니다"
        )
    
    # 권한 검사: 작성자만 첨부파일 업로드 가능
    if proposal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 제안서에 첨부파일을 업로드할 권한이 없습니다"
        )
    
    # 제안서 상태가 draft 또는 submitted 상태일 때만 첨부파일 업로드 가능
    if proposal.status not in ["draft", "submitted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 처리 중인 제안서에는 첨부파일을 추가할 수 없습니다"
        )
    
    updated_proposal = upload_attachment(db, proposal_id=proposal_id, file=file)
    return updated_proposal


@router.put("/{proposal_id}", response_model=Proposal)
async def update_existing_proposal(
    proposal_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    expected_effect: Optional[str] = Form(None),
    benefit_amount: Optional[float] = Form(None),
    before_image: Optional[UploadFile] = File(None),
    after_image: Optional[UploadFile] = File(None),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    기존 제안서 수정 (이미지 포함)
    """
    # 디버깅 로그 추가
    print(f"제안서 수정 - ID: {proposal_id}, 받은 데이터: title={title}, category={category}")
    print(f"이미지 데이터: before_image={before_image}, after_image={after_image}")
    
    proposal = get_proposal(db, proposal_id=proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안서를 찾을 수 없습니다"
        )
    
    # 권한 검사: 작성자만 수정 가능
    if proposal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 제안서를 수정할 권한이 없습니다"
        )
    
    # 제안서 상태가 draft 또는 submitted 상태일 때만 수정 가능
    if proposal.status not in ["DRAFT", "SUBMITTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 처리 중인 제안서는 수정할 수 없습니다"
        )
    
    # 카테고리 유효성 검사
    proposal_category = None
    if category:
        try:
            proposal_category = ProposalCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"유효하지 않은 카테고리입니다: {category}"
            )
    
    # 업데이트할 데이터 준비
    proposal_update = ProposalUpdate(
        title=title,
        content=content,
        category=proposal_category,
        expected_effect=expected_effect,
        benefit_amount=benefit_amount
    )
    
    # 제안서 업데이트
    updated_proposal = update_proposal(
        db=db, 
        proposal_id=proposal_id, 
        proposal=proposal_update,
        user_id=current_user.id,
        before_image=before_image,
        after_image=after_image
    )
    
    return updated_proposal


@router.put("/{proposal_id}/status", response_model=Proposal)
def update_proposal_status(
    proposal_id: int,
    status_update: ProposalStatusUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    제안서 상태 업데이트 (승인/거부/구현)
    """
    proposal = get_proposal(db, proposal_id=proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안서를 찾을 수 없습니다"
        )
    
    # 상태 변경에 따른 권한 및 상태 검사
    if status_update.status == "approved":
        # 부서 담당자만 승인 가능
        if not current_user.is_department_manager or proposal.department != current_user.department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="제안서를 승인할 권한이 없습니다"
            )
        # 제출된 상태만 승인 가능
        if proposal.status != "submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="제출된 상태의 제안서만 승인할 수 있습니다"
            )
        proposal = approve_proposal(db, proposal_id=proposal_id, feedback=status_update.feedback)
    
    elif status_update.status == "rejected":
        # 부서 담당자 또는 공장 담당자만 거부 가능
        if ((not current_user.is_department_manager or proposal.department != current_user.department) and
            (not current_user.is_factory_manager or proposal.factory != current_user.factory)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="제안서를 거부할 권한이 없습니다"
            )
        # 제출/승인 상태만 거부 가능
        if proposal.status not in ["submitted", "approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="제출/승인된 상태의 제안서만 거부할 수 있습니다"
            )
        proposal = reject_proposal(db, proposal_id=proposal_id, feedback=status_update.feedback)
    
    elif status_update.status == "implemented":
        # 공장 담당자만 구현 확인 가능
        if not current_user.is_factory_manager or proposal.factory != current_user.factory:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="제안서를 구현 확인할 권한이 없습니다"
            )
        # 승인 상태만 구현 확인 가능
        if proposal.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="승인된 상태의 제안서만 구현 확인할 수 있습니다"
            )
        proposal = implement_proposal(db, proposal_id=proposal_id, feedback=status_update.feedback)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 상태 변경입니다"
        )
    
    return proposal


@router.delete("/{proposal_id}", response_model=Proposal)
def delete_existing_proposal(
    proposal_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    제안서 삭제
    """
    proposal = get_proposal(db, proposal_id=proposal_id)
    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="제안서를 찾을 수 없습니다"
        )
    
    # 관리자이거나 작성자이면서 draft 상태인 경우만 삭제 가능
    if not current_user.is_admin and (proposal.user_id != current_user.id or proposal.status != "draft"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 제안서를 삭제할 권한이 없습니다"
        )
    
    proposal = delete_proposal(db, proposal_id=proposal_id)
    return proposal 