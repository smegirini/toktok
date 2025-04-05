from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 요청 시작 시간
        start_time = time.time()
        
        # 인증 헤더 로깅
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # 토큰 값 자체는 보안상 로그에 남기지 않음
            logger.info(f"인증 헤더 존재: {auth_header[:15]}...")
        else:
            logger.info("인증 헤더 없음")
        
        # 요청 경로 및 메소드 로깅
        logger.info(f"요청: {request.method} {request.url.path}")
        
        # 다음 미들웨어 또는 엔드포인트 실행
        response = await call_next(request)
        
        # 응답 시간 계산
        process_time = time.time() - start_time
        logger.info(f"응답: {response.status_code} (처리 시간: {process_time:.4f}초)")
        
        return response


def setup_middlewares(app: FastAPI) -> None:
    """애플리케이션에 미들웨어 설정"""
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 로깅 미들웨어 추가
    app.add_middleware(LoggingMiddleware)
    
    # 여기에 다른 미들웨어 추가 가능 