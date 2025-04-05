document.addEventListener('DOMContentLoaded', function() {
    // 프로필 데이터 로드
    loadUserProfile();
    
    // 비밀번호 변경 버튼 이벤트
    document.getElementById('changePasswordBtn').addEventListener('click', function() {
        // 비밀번호 변경 모달 또는 페이지 열기
        alert('비밀번호 변경 기능은 아직 구현되지 않았습니다.');
    });
    
    // 프로필 수정 버튼 이벤트
    document.getElementById('editProfileBtn').addEventListener('click', function() {
        // 프로필 수정 모달 또는 페이지 열기
        alert('프로필 수정 기능은 아직 구현되지 않았습니다.');
    });
    
    // 사용자 프로필 로드 함수
    async function loadUserProfile() {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('토큰이 없습니다. 로그인 페이지로 이동합니다.');
                window.location.href = '/login';
                return;
            }

            const response = await fetch('/api/v1/auth/me', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                
                // 프로필 데이터 표시
                document.getElementById('fullName').textContent = userData.full_name;
                document.getElementById('userFullName').textContent = userData.full_name;
                document.getElementById('position').textContent = userData.position;
                document.getElementById('userPosition').textContent = userData.position;
                document.getElementById('department').textContent = userData.department;
                document.getElementById('userDepartment').textContent = userData.department;
                document.getElementById('employeeId').textContent = userData.employee_id;
                document.getElementById('userEmail').textContent = userData.email;
                document.getElementById('userLevel').textContent = getUserLevelKorean(userData.level);
                document.getElementById('totalPoints').textContent = userData.points;
                
                // 사용자 제안 목록 로드
                loadUserProposals();
            } else {
                console.error('Failed to load user profile');
                // 로그인 페이지로 리디렉션
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    // 사용자 제안 목록 로드 함수
    async function loadUserProposals() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/proposals/me', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const proposals = await response.json();
                const tableBody = document.getElementById('userProposalsTable');
                
                // 테이블 초기화
                tableBody.innerHTML = '';
                
                if (proposals.length === 0) {
                    // 제안이 없는 경우
                    const emptyRow = document.createElement('tr');
                    emptyRow.className = 'no-proposals-row';
                    emptyRow.innerHTML = '<td colspan="4" class="text-center py-3">아직 작성한 제안이 없습니다.</td>';
                    tableBody.appendChild(emptyRow);
                } else {
                    // 제안 목록 표시
                    proposals.forEach(proposal => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td><a href="/proposals/${proposal.id}">${proposal.title}</a></td>
                            <td>${getCategoryKorean(proposal.category)}</td>
                            <td><span class="badge ${getStatusBadgeClass(proposal.status)}">${getStatusKorean(proposal.status)}</span></td>
                            <td>${new Date(proposal.created_at).toLocaleDateString()}</td>
                        `;
                        tableBody.appendChild(row);
                    });
                }
                
                // 랭킹 정보 로드
                loadUserRanking();
                
            } else {
                console.error('Failed to load user proposals');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    // 사용자 랭킹 로드 함수
    async function loadUserRanking() {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/rankings/me', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const rankData = await response.json();
                document.getElementById('rank').textContent = rankData.rank || '-';
                document.getElementById('totalProposals').textContent = rankData.total_proposals || '0';
                document.getElementById('implementedProposals').textContent = rankData.implemented_proposals || '0';
            } else {
                console.error('Failed to load user ranking');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
    
    // 헬퍼 함수들
    function getUserLevelKorean(level) {
        const levels = {
            'ABSOLUTE_GOD': '절대신',
            'SUPREME': '지존',
            'HERO': '영웅',
            'MASTER': '고수',
            'INTERMEDIATE': '중수',
            'BEGINNER': '초수',
            'COMMONER': '평민'
        };
        return levels[level] || level;
    }
    
    function getCategoryKorean(category) {
        const categories = {
            'QUALITY': '품질 개선',
            'SAFETY': '안전 개선',
            'EFFICIENCY': '효율성 개선',
            'COST': '비용 절감',
            'ENVIRONMENT': '환경 개선',
            'OTHER': '기타'
        };
        return categories[category] || category;
    }
    
    function getStatusKorean(status) {
        const statuses = {
            'DRAFT': '임시저장',
            'SUBMITTED': '제출됨',
            'REVIEWING': '검토 중',
            'APPROVED': '승인됨',
            'REJECTED': '거부됨',
            'IMPLEMENTED': '구현됨'
        };
        return statuses[status] || status;
    }
    
    function getStatusBadgeClass(status) {
        const classes = {
            'DRAFT': 'bg-secondary',
            'SUBMITTED': 'bg-primary',
            'REVIEWING': 'bg-info',
            'APPROVED': 'bg-success',
            'REJECTED': 'bg-danger',
            'IMPLEMENTED': 'bg-dark'
        };
        return classes[status] || 'bg-secondary';
    }
}); 