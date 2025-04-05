document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // 관리자 계정인지 확인 (admin/12345)
            if (username === 'admin' && password === '12345') {
                console.log('관리자 계정으로 로그인 시도 - 직접 처리');
                
                // 관리자 로그인 직접 처리
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
                        console.log('관리자 로그인 성공:', data);
                        
                        // 토큰과 관리자 상태 저장
                        localStorage.setItem('is_admin', 'true');
                        localStorage.setItem('token', data.access_token);
                        localStorage.setItem('admin_token', data.access_token);
                        
                        // 쿠키에 토큰 저장 (서버에서 인증 확인용)
                        document.cookie = `auth_token=${data.access_token}; path=/`;
                        
                        // 성공 메시지 및 리디렉션
                        showAlert('관리자 로그인 성공! 관리자 페이지로 이동합니다.', 'success');
                        setTimeout(() => {
                            window.location.href = '/admin';
                        }, 1000);
                    } else {
                        console.log('관리자 로그인 실패:', data);
                        showAlert('관리자 로그인 실패: ' + (data.message || '인증 실패'), 'danger');
                    }
                })
                .catch(error => {
                    console.error('관리자 로그인 오류:', error);
                    showAlert('관리자 로그인 중 오류가 발생했습니다.', 'danger');
                });
                
                return;
            }
            
            // 일반 로그인 처리
            fetch('/api/v1/auth/login', {
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
                if (data.access_token) {
                    // 로그인 성공
                    localStorage.setItem('token', data.access_token);
                    
                    // 쿠키에 토큰 저장 (서버에서 인증 확인용)
                    document.cookie = `auth_token=${data.access_token}; path=/`;
                    
                    // 관리자 권한 확인
                    fetch('/api/v1/auth/me', {
                        headers: {
                            'Authorization': `Bearer ${data.access_token}`
                        }
                    })
                    .then(response => response.json())
                    .then(userData => {
                        console.log('사용자 정보:', userData);
                        if (userData.auth === 'ADMIN') {
                            console.log('[중요] 관리자 권한 감지됨, 관리자 상태 저장');
                            localStorage.setItem('is_admin', 'true');
                            
                            // 쿠키에도 관리자 정보 포함
                            const token = localStorage.getItem('token');
                            document.cookie = `auth_token=${token}; path=/`;
                            document.cookie = `is_admin=true; path=/`;
                            
                            // 관리자 UI 즉시 표시 시도
                            const adminElements = document.querySelectorAll('.admin-only');
                            console.log(`관리자 UI 요소 ${adminElements.length}개 발견, 표시 시도`);
                            adminElements.forEach(el => {
                                el.style.display = 'block';
                            });
                        } else {
                            console.log('일반 사용자 권한:', userData.auth);
                            localStorage.removeItem('is_admin');
                        }
                        
                        // 로그인 성공 메시지 표시
                        showAlert('로그인 성공! 메인 페이지로 이동합니다.', 'success');
                        
                        // 강제 새로고침을 위한 플래그 설정
                        sessionStorage.setItem('force_refresh', 'true');
                        console.log('강제 새로고침 플래그 설정됨:', sessionStorage.getItem('force_refresh'));
                        
                        // 토큰이 적용되는 데 시간이 걸릴 수 있으므로 약간 지연 후 리디렉션
                        setTimeout(() => {
                            console.log('메인 페이지로 리디렉션, 강제 새로고침 예정');
                            window.location.href = '/?t=' + new Date().getTime(); // 캐시 방지를 위한 타임스탬프 추가
                        }, 1000);
                    })
                    .catch(error => {
                        console.error('사용자 정보 가져오기 실패:', error);
                        window.location.href = '/';
                    });
                } else {
                    // 로그인 실패
                    showAlert('로그인 실패: ' + (data.detail || '사용자명 또는 비밀번호가 올바르지 않습니다.'), 'danger');
                }
            })
            .catch(error => {
                console.error('로그인 오류:', error);
                showAlert('로그인 중 오류가 발생했습니다.', 'danger');
            });
        });
    }
}); 