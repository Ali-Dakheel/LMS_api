"""
Users app specific fixtures.

Provides:
- API client
- User fixtures (admin, dean, teacher, student)
- JWT token fixtures
- Authenticated client fixtures
- Factory functions
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User


# ============================================================================
# API CLIENT
# ============================================================================

@pytest.fixture
def api_client():
    """Provide DRF API client for testing."""
    return APIClient()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Create admin/superuser."""
    return User.objects.create_superuser(
        email='admin@slh.com',
        password='Admin@123',
        name='Admin User'
    )


@pytest.fixture
def dean_user(db):
    """Create dean user with optional teacher info."""
    user = User.objects.create_user(
        email='dean@slh.edu',
        password='Dean@2025',
        name='Dr. Dean Smith',
        role='dean',
        institution='Harvard University',
        department='Faculty of Engineering'
    )
    
    # Update teacher info (auto-created via signal)
    user.teacher_info.designation = 'Dean & Professor'
    user.teacher_info.specialization = 'Computer Science'
    user.teacher_info.academic_level = 'UNIV'
    user.teacher_info.save()
    
    return user


@pytest.fixture
def teacher_user(db):
    """Create university teacher user."""
    user = User.objects.create_user(
        email='teacher@slh.edu',
        password='Teacher@123',
        name='Dr. John Teacher',
        role='teacher',
        institution='MIT',
        department='Computer Science'
    )
    
    # Update teacher info
    user.teacher_info.designation = 'Associate Professor'
    user.teacher_info.specialization = 'Machine Learning'
    user.teacher_info.academic_level = 'UNIV'
    user.teacher_info.save()
    
    return user


@pytest.fixture
def school_teacher_user(db):
    """Create K-12 school teacher user."""
    user = User.objects.create_user(
        email='schoolteacher@slh.edu',
        password='Teacher@123',
        name='Sarah Teacher',
        role='teacher',
        institution='Lincoln High School',
        department='Mathematics'
    )
    
    # Update teacher info
    user.teacher_info.designation = 'Senior Teacher'
    user.teacher_info.specialization = 'Algebra'
    user.teacher_info.academic_level = 'SCHOOL'
    user.teacher_info.save()
    
    return user


@pytest.fixture
def student_user(db):
    """Create student user."""
    user = User.objects.create_user(
        email='student@slh.edu',
        password='Student@123',
        name='Alice Student',
        role='student',
        institution='MIT',
        department='Computer Science',
        major='Artificial Intelligence'
    )
    
    # Update student info
    user.student_info.enrollment_number = 'MIT2025001'
    user.student_info.status = 'active'
    user.student_info.save()
    
    return user


@pytest.fixture
def inactive_user(db):
    """Create inactive (deactivated) user."""
    user = User.objects.create_user(
        email='inactive@slh.edu',
        password='Inactive@123',
        name='Inactive User',
        role='student',
        institution='Test University',
        department='Test Department',
        major='Test Major'
    )
    user.deactivate(reason='Test deactivation')
    return user


@pytest.fixture
def unverified_user(db):
    """Create user with unverified email."""
    user = User.objects.create_user(
        email='unverified@slh.edu',
        password='Unverified@123',
        name='Unverified User',
        role='student',
        institution='Test University',
        department='Test Department',
        major='Test Major'
    )
    # email_verified is False by default
    return user


# ============================================================================
# TOKEN FIXTURES
# ============================================================================

@pytest.fixture
def admin_tokens(admin_user):
    """Generate JWT tokens for admin user."""
    refresh = RefreshToken.for_user(admin_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'refresh_obj': refresh,
        'user': admin_user
    }


@pytest.fixture
def dean_tokens(dean_user):
    """Generate JWT tokens for dean user."""
    refresh = RefreshToken.for_user(dean_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'refresh_obj': refresh,
        'user': dean_user
    }


@pytest.fixture
def teacher_tokens(teacher_user):
    """Generate JWT tokens for teacher user."""
    refresh = RefreshToken.for_user(teacher_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'refresh_obj': refresh,
        'user': teacher_user
    }


@pytest.fixture
def student_tokens(student_user):
    """Generate JWT tokens for student user."""
    refresh = RefreshToken.for_user(student_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'refresh_obj': refresh,
        'user': student_user
    }


# ============================================================================
# AUTHENTICATED CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def admin_client(api_client, admin_tokens):
    """API client authenticated as admin."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
    api_client.user = admin_tokens['user']
    return api_client


@pytest.fixture
def dean_client(api_client, dean_tokens):
    """API client authenticated as dean."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {dean_tokens["access"]}')
    api_client.user = dean_tokens['user']
    return api_client


@pytest.fixture
def teacher_client(api_client, teacher_tokens):
    """API client authenticated as teacher."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {teacher_tokens["access"]}')
    api_client.user = teacher_tokens['user']
    return api_client


@pytest.fixture
def student_client(api_client, student_tokens):
    """API client authenticated as student."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_tokens["access"]}')
    api_client.user = student_tokens['user']
    return api_client


# ============================================================================
# FACTORY FIXTURES
# ============================================================================

@pytest.fixture
def create_user(db):
    """
    Factory fixture for creating users dynamically.
    
    Usage:
        user = create_user('test@example.com', role='teacher', institution='MIT')
    """
    def _create_user(email, role='student', **kwargs):
        password = kwargs.pop('password', 'TestPass@123')
        name = kwargs.pop('name', f'Test {role.title()}')
        
        return User.objects.create_user(
            email=email,
            password=password,
            name=name,
            role=role,
            **kwargs
        )
    
    return _create_user


@pytest.fixture
def create_tokens():
    """
    Factory fixture for generating tokens for any user.
    
    Usage:
        tokens = create_tokens(user)
    """
    def _create_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'refresh_obj': refresh,
            'user': user
        }
    
    return _create_tokens


@pytest.fixture
def create_authenticated_client(api_client, create_tokens):
    """
    Factory fixture for creating authenticated client for any user.
    
    Usage:
        client = create_authenticated_client(user)
    """
    def _create_client(user):
        tokens = create_tokens(user)
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        api_client.user = user
        return api_client
    
    return _create_client


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_response_success():
    """
    Helper to assert successful API response format.
    
    Usage:
        assert_response_success(response, status_code=200)
    """
    def _assert(response, status_code=200, has_data=True):
        assert response.status_code == status_code, \
            f"Expected {status_code}, got {response.status_code}: {response.data}"
        
        data = response.json()
        assert data['success'] is True, f"Response not successful: {data}"
        assert 'message' in data
        
        if has_data:
            assert 'data' in data
        
        return data
    
    return _assert


@pytest.fixture
def assert_response_error():
    """
    Helper to assert error API response format.
    
    Usage:
        assert_response_error(response, status_code=400)
    """
    def _assert(response, status_code=400, has_errors=True):
        assert response.status_code == status_code, \
            f"Expected {status_code}, got {response.status_code}: {response.data}"
        
        data = response.json()
        assert data['success'] is False, f"Response should not be successful: {data}"
        assert 'message' in data
        
        if has_errors:
            assert 'errors' in data
        
        return data
    
    return _assert

@pytest.fixture
def auth_url():
    """Helper to get auth URLs."""
    def _url(endpoint):
        return f'/api/v1/auth/{endpoint}'
    return _url


@pytest.fixture
def users_url():
    """Helper to get users URLs."""
    def _url(endpoint=''):
        return f'/api/v1/users/{endpoint}'
    return _url