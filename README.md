# 한국타이어 제안 관리 시스템

한국타이어 제안 관리 시스템은 직원들의 아이디어와 제안을 관리하고 평가하는 웹 기반 애플리케이션입니다.

## 기능

- 사용자 인증 (로그인/회원가입)
- 제안 등록 및 관리
- 제안 검색 및 필터링
- 댓글 기능
- 관리자 대시보드
- 제안 승인 및 반려 처리
- 알림 시스템
- 통계 분석

## 설치 및 실행 방법

### 환경 설정

1. 필수 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 데이터베이스 설정:
`.env` 파일에 데이터베이스 연결 정보가 포함되어 있습니다.

### 어플리케이션 실행

다음 명령어로 서버를 실행합니다:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

서버는 http://localhost:8001 에서 실행됩니다.

## 관리자 계정

- 아이디: admin
- 비밀번호: 12345

## 기술 스택

- Backend: FastAPI
- Database: SQLAlchemy(MariaDB)
- Frontend: HTML, CSS, JavaScript, Bootstrap
- Template Engine: Jinja2
- Authentication: JWT

## 디렉토리 구조

- `/app`: 메인 애플리케이션 코드
  - `/api`: API 엔드포인트
  - `/models`: 데이터 모델
  - `/templates`: HTML 템플릿
  - `/static`: 정적 파일 (CSS, JS, 이미지)
- `/uploads`: 업로드된 파일 저장 위치
