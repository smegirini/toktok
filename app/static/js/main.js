// 글로벌 JavaScript 함수들

// 페이지 로드 완료 시 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('한국타이어 제안 시스템이 로드되었습니다.');
    
    // 강제 새로고침 체크
    if(sessionStorage.getItem('force_refresh') === 'true') {
        console.log('강제 새로고침 플래그 감지됨, 페이지 새로고침 실행');
        // 무한 리프레시 방지를 위해 플래그 제거 먼저 수행
        sessionStorage.removeItem('force_refresh');
        
        // 페이지 강제 새로고침
        console.log('페이지 강제 새로고침 실행');
        window.location.reload(true);
        return;
    }
    
    // 툴팁 초기화 (Bootstrap)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // 관리자 로그인 상태 체크
    console.log('체크 1: DOMContentLoaded 이벤트에서 checkAdminStatus 호출');
    checkAdminStatus();
    
    // UI 업데이트 확인을 위한 추가 체크 (약간의 지연 후)
    setTimeout(function() {
        console.log('UI 업데이트 확인을 위한 추가 체크 실행');
        const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
        const isAdmin = localStorage.getItem('is_admin') === 'true';
        
        console.log('토큰 존재 여부 (확인):', !!token);
        console.log('관리자 상태 (확인):', isAdmin);
        
        // 로그인/로그아웃 메뉴 참조
        const loggedOutMenu = document.querySelector('.logged-out-menu');
        const loggedInMenu = document.querySelector('.logged-in-menu');
        const adminElements = document.querySelectorAll('.admin-only');
        
        if (token) {
            console.log('토큰 있음, UI 상태 확인:');
            console.log('로그인 메뉴 표시 상태:', loggedInMenu ? loggedInMenu.style.display : 'not found');
            console.log('로그아웃 메뉴 표시 상태:', loggedOutMenu ? loggedOutMenu.style.display : 'not found');
            
            // DOM에 변경이 반영되지 않았으면 강제로 업데이트
            if (loggedOutMenu && loggedInMenu && loggedOutMenu.style.display !== 'none') {
                console.log('UI 상태 불일치 감지, 강제 업데이트 실행');
                loggedOutMenu.style.display = 'none';
                loggedInMenu.style.display = 'block';
            }
            
            if (isAdmin) {
                console.log('관리자 UI 요소 표시 상태 확인');
                adminElements.forEach((el, index) => {
                    console.log(`관리자 요소 #${index} 표시 상태:`, el.style.display);
                    if (el.style.display !== 'block') {
                        console.log(`관리자 요소 #${index} 강제 표시`);
                        el.style.display = 'block';
                    }
                });
            }
        }
    }, 500);
    
    // 관리자 로그인 폼이 존재하면 이벤트 리스너 추가
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // 관리자 계정인지 확인 (admin/12345)
            if (username === 'admin' && password === '12345') {
                console.log('관리자 계정으로 로그인 시도');
                e.preventDefault();
                adminLogin(username, password);
            }
        });
    }
});

// 알림 생성 함수
function showAlert(message, type = 'info', duration = 3000) {
    const alertPlaceholder = document.getElementById('alert-placeholder');
    
    if (!alertPlaceholder) {
        // 알림 플레이스홀더가 없으면 생성
        const alertContainer = document.createElement('div');
        alertContainer.id = 'alert-placeholder';
        alertContainer.className = 'position-fixed top-0 end-0 p-3';
        alertContainer.style.zIndex = '5000';
        document.body.appendChild(alertContainer);
    }
    
    const id = 'alert-' + new Date().getTime();
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
        <div id="${id}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // 알림 추가
    alertPlaceholder.appendChild(wrapper);
    
    // 일정 시간 후 알림 제거
    setTimeout(() => {
        const alert = document.getElementById(id);
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, duration);
}

// 관리자 로그인 상태 확인
function checkAdminStatus() {
    console.log("관리자 상태 확인 실행 - checkAdminStatus()");
    
    // 로컬 스토리지에서 관리자 상태 확인
    const isAdmin = localStorage.getItem('is_admin') === 'true';
    
    // 로컬 스토리지에서 토큰 가져오기
    const token = localStorage.getItem('admin_token') || localStorage.getItem('token');
    
    console.log("[디버깅] 로컬 스토리지 is_admin:", localStorage.getItem('is_admin'));
    console.log("[디버깅] 토큰 존재 여부:", !!token);
    
    // 현재 URL이 /admin으로 시작하는지 확인
    const isAdminPage = window.location.pathname.startsWith('/admin');
    console.log("[디버깅] 현재 페이지가 관리자 페이지인가:", isAdminPage);
    
    // 로그인/로그아웃 메뉴 참조
    const loggedOutMenu = document.querySelector('.logged-out-menu');
    const loggedInMenu = document.querySelector('.logged-in-menu');
    const adminElements = document.querySelectorAll('.admin-only');
    
    if (!loggedOutMenu || !loggedInMenu) {
        console.log("[오류] 로그인/로그아웃 메뉴 요소를 찾을 수 없음");
        console.log("loggedOutMenu 존재 여부:", !!loggedOutMenu);
        console.log("loggedInMenu 존재 여부:", !!loggedInMenu);
    } else {
        console.log("[정보] 로그인/로그아웃 메뉴 요소 발견됨");
    }
    
    console.log("[정보] 관리자 요소 개수:", adminElements.length);
    
    if (isAdmin) {
        console.log("[중요] 관리자 권한 상태가 true로 설정되어 있어 메뉴 표시 시작");
        // 관리자 UI 표시를 먼저 수행하여 토큰 확인 전에 UI가 보이도록 함
        adminElements.forEach((el, index) => {
            console.log(`[정보] 관리자 UI 요소 #${index} 바로 표시 시작 (isAdmin 기반)`);
            el.style.display = 'block';
        });
    }
    
    // 쿠키에 토큰 저장 (항상 최신 상태 유지)
    if (token) {
        console.log("[정보] 로컬 스토리지에서 찾은 토큰을 쿠키에 저장함");
        document.cookie = `auth_token=${token}; path=/`;
        
        // 로그인 상태 UI 업데이트
        if (loggedOutMenu && loggedInMenu) {
            console.log("[정보] 로그인 상태 UI 업데이트: 로그인 메뉴 표시");
            loggedOutMenu.style.display = 'none';
            loggedInMenu.style.display = 'block';
        }
        
        // 토큰이 있는 경우 사용자 정보 확인 (추가 검증)
        console.log("[정보] 사용자 정보 확인 API 요청 시작");
        fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            console.log("[정보] API 응답 상태:", response.status);
            if (!response.ok) {
                throw new Error('사용자 정보 가져오기 실패: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            console.log("[정보] 사용자 정보:", data);
            console.log("[정보] 사용자 권한:", data.auth);
            
            // 관리자 권한인 경우
            if (data.auth === 'ADMIN') {
                console.log("[정보] 관리자 권한 감지됨, 관리자 메뉴 표시 및 상태 저장");
                localStorage.setItem('is_admin', 'true');
                
                // 관리자 UI 표시
                console.log("[정보] 관리자 UI 요소 표시 시작");
                adminElements.forEach((el, index) => {
                    console.log(`[정보] 관리자 UI 요소 #${index} 표시`);
                    el.style.display = 'block';
                });
                
                // 강제 새로고침 트리거 (필요한 경우)
                if (document.querySelector('.admin-only') && 
                    document.querySelector('.admin-only').style.display !== 'block') {
                    console.log("[중요] UI 상태 일관성 문제 감지, 페이지 강제 새로고침 시작");
                    window.location.reload(true);
                }
                
                // 로그인 메뉴 표시
                if (loggedOutMenu && loggedInMenu) {
                    loggedOutMenu.style.display = 'none';
                    loggedInMenu.style.display = 'block';
                    console.log("[정보] 로그인 상태 메뉴 업데이트 완료");
                } else {
                    console.log("[오류] 로그인/로그아웃 메뉴 요소를 찾을 수 없음");
                }
            } else {
                // 일반 사용자 (관리자 아님)
                console.log("[정보] 일반 사용자 권한 감지됨");
                localStorage.removeItem('is_admin');
                adminElements.forEach(el => {
                    el.style.display = 'none';
                });
            }
            
            // DOM 변경사항이 적용되었는지 확인
            setTimeout(() => {
                console.log("[검증] 로그인 메뉴 표시 상태:", loggedInMenu ? loggedInMenu.style.display : 'not found');
                console.log("[검증] 로그아웃 메뉴 표시 상태:", loggedOutMenu ? loggedOutMenu.style.display : 'not found');
                console.log("[검증] 관리자 요소 표시 상태 샘플:", adminElements.length > 0 ? adminElements[0].style.display : 'no elements');
            }, 100);
        })
        .catch(error => {
            console.error('[오류] 사용자 정보 가져오기 실패:', error);
            // 인증 실패 시 로컬 스토리지 정리
            if (error.message.includes('401')) {
                console.log("[정보] 인증 실패로 로컬 스토리지 정리");
                localStorage.removeItem('is_admin');
                localStorage.removeItem('admin_token');
                localStorage.removeItem('token');
                document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                
                // UI 업데이트
                if (loggedOutMenu && loggedInMenu) {
                    loggedOutMenu.style.display = 'block';
                    loggedInMenu.style.display = 'none';
                }
                
                adminElements.forEach(el => {
                    el.style.display = 'none';
                });
                
                // 관리자 페이지에 있는 경우 로그인 페이지로 리디렉션
                if (isAdminPage) {
                    console.log("[정보] 관리자 페이지에서 인증 실패 - 로그인 페이지로 리디렉션");
                    window.location.href = '/login';
                }
            }
        });
    } else {
        // 토큰이 없는 경우
        console.log("[정보] 인증 토큰 없음");
        // 로그인 상태 UI 업데이트
        if (loggedOutMenu && loggedInMenu) {
            loggedOutMenu.style.display = 'block';
            loggedInMenu.style.display = 'none';
        }
        
        // 관리자 메뉴 숨김
        adminElements.forEach(el => {
            el.style.display = 'none';
        });
        
        // 관리자 페이지 접근 시도인 경우 로그인으로 리디렉션
        if (isAdminPage) {
            console.log("[경고] 토큰 없이 관리자 페이지 접근 - 로그인 페이지로 리디렉션");
            window.location.href = '/login';
        }
    }
    
    // 로그아웃 버튼 이벤트 리스너 설정
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            console.log("[정보] 로그아웃 실행");
            localStorage.removeItem('is_admin');
            localStorage.removeItem('admin_token');
            localStorage.removeItem('token');
            // 쿠키 삭제
            document.cookie = "auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            
            showAlert('로그아웃 되었습니다.', 'success');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        });
    }
}

// 관리자 로그인 처리 함수
function adminLogin(username, password) {
    // 관리자 로그인 API 호출 - 새로운 엔드포인트 사용
    fetch('/api/v1/auth/admin-login-direct', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'username': username,
            'password': password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 관리자 로그인 성공
            localStorage.setItem('is_admin', 'true');
            localStorage.setItem('admin_token', data.access_token);
            
            // 쿠키에 토큰 저장 (서버에서 인증 확인용)
            document.cookie = `auth_token=${data.access_token}; path=/`;
            
            console.log("관리자 로그인 성공, 토큰 저장됨");
            
            showAlert('관리자 로그인 성공!', 'success');
            setTimeout(() => {
                window.location.href = '/admin';
            }, 1000);
        } else {
            // 일반 로그인 프로세스 계속 진행
            console.log('관리자 로그인 실패, 일반 로그인 진행');
        }
    })
    .catch(error => {
        console.error('관리자 로그인 오류:', error);
    });
}

// 페이지 제목 설정
function setPageTitle(title) {
    document.title = title + ' - 한국타이어 제안 시스템';
}

// 날짜 포맷팅 함수
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 숫자 포맷팅 함수 (천 단위 구분)
function formatNumber(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// URL 매개변수 가져오기
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// 페이지 로드 완료 후 실행
document.addEventListener('DOMContentLoaded', function() {
    // 현재 활성화된 메뉴 항목 표시
    highlightCurrentPage();
    
    // 로그아웃 버튼 이벤트 리스너 추가
    setupLogoutButton();
    
    // 폼 유효성 검사 설정
    setupFormValidation();
    
    // 모달 초기화
    setupModals();
});

// 현재 페이지에 해당하는 메뉴 항목 강조
function highlightCurrentPage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

// 로그아웃 버튼 설정
function setupLogoutButton() {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch('/api/v1/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    window.location.href = '/login';
                } else {
                    console.error('로그아웃 실패');
                }
            } catch (error) {
                console.error('로그아웃 중 오류 발생:', error);
            }
        });
    }
}

// 폼 유효성 검사 설정
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// 모달 초기화
function setupModals() {
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modalEl => {
        const modal = new bootstrap.Modal(modalEl);
        
        // 모달이 닫힌 후 폼 초기화
        modalEl.addEventListener('hidden.bs.modal', () => {
            const form = modalEl.querySelector('form');
            if (form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        });
    });
}

// API 요청 헬퍼 함수
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (response.ok) {
            return await response.json();
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || '요청 처리 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('API 요청 중 오류:', error);
        throw error;
    }
} 