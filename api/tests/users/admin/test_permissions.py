"""
Permission Tests 
"""

import pytest


@pytest.mark.api
@pytest.mark.security
class TestUserPermissions:
    """Critical permission and role-based access tests."""
    
    def test_teacher_can_view_students_list(self, teacher_client):
        """Test teacher can view students list."""
        response = teacher_client.get('/api/v1/users/students/')
        
        assert response.status_code == 200
    
    def test_teacher_can_view_teachers_list(self, teacher_client):
        """Test teacher can view other teachers."""
        response = teacher_client.get('/api/v1/users/teachers/')
        
        assert response.status_code == 200
    
    def test_teacher_cannot_view_deans_list(self, teacher_client):
        """Test teacher cannot view deans list."""
        response = teacher_client.get('/api/v1/users/deans/')
        
        assert response.status_code == 403
    
    def test_dean_can_view_all_lists(self, dean_client):
        """Test dean can view teachers, students, and deans."""
        endpoints = [
            '/api/v1/users/teachers/',
            '/api/v1/users/students/',
            '/api/v1/users/deans/'
        ]
        
        for endpoint in endpoints:
            response = dean_client.get(endpoint)
            assert response.status_code == 200, f"Dean should access {endpoint}"
    
    def test_student_cannot_access_any_user_lists(self, student_client):
        """Test students cannot access user management."""
        endpoints = [
            '/api/v1/users/',
            '/api/v1/users/teachers/',
            '/api/v1/users/students/',
            '/api/v1/users/deans/'
        ]
        
        for endpoint in endpoints:
            response = student_client.get(endpoint)
            assert response.status_code == 403, f"Student should not access {endpoint}"
    
    def test_only_admin_can_create_users(self, teacher_client, dean_client, student_client):
        """Test only admin can create users."""
        user_data = {
            'email': 'test@test.com',
            'name': 'Test',
            'role': 'student',
            'password': 'Pass@123'
        }
        
        # Teacher cannot
        assert teacher_client.post('/api/v1/users/', user_data).status_code == 403
        
        # Dean cannot
        assert dean_client.post('/api/v1/users/', user_data).status_code == 403
        
        # Student cannot
        assert student_client.post('/api/v1/users/', user_data).status_code == 403
    
    def test_only_admin_can_deactivate_users(self, teacher_client, student_user):
        """Test only admin can deactivate users."""
        response = teacher_client.delete(f'/api/v1/users/{student_user.id}/')
        
        assert response.status_code == 403
    
    def test_user_cannot_deactivate_self(self, admin_client, admin_user):
        """Test admin cannot deactivate their own account."""
        response = admin_client.delete(f'/api/v1/users/{admin_user.id}/')
        
        assert response.status_code == 400
        data = response.json()
        assert 'own' in str(data).lower() or 'self' in str(data).lower()