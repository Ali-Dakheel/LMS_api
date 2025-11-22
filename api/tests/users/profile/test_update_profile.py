"""
Update Profile Tests (Essential)
"""

import pytest


@pytest.mark.api
class TestUpdateProfile:
    """Essential update profile tests."""
    
    def test_update_profile_name(self, student_client, student_user):
        """Test updating profile name."""
        response = student_client.patch('/api/v1/users/me/', {
            'name': 'Updated Name'
        })
        
        assert response.status_code == 200
        
        student_user.refresh_from_db()
        assert student_user.name == 'Updated Name'
    
    def test_update_profile_academic_fields(self, student_client, student_user):
        """Test student can update academic fields."""
        response = student_client.patch('/api/v1/users/me/', {
            'institution': 'Harvard University',
            'department': 'Physics',
            'major': 'Quantum Computing'
        })
        
        assert response.status_code == 200
        
        student_user.refresh_from_db()
        assert student_user.institution == 'Harvard University'
        assert student_user.department == 'Physics'
        assert student_user.major == 'Quantum Computing'
    
    def test_admin_cannot_update_academic_fields(self, admin_client, admin_user):
        """Test admin cannot set academic fields."""
        response = admin_client.patch('/api/v1/users/me/', {
            'institution': 'MIT'
        })
        
        assert response.status_code == 400
        data = response.json()
        assert 'academic' in str(data).lower() or 'admin' in str(data).lower()
    
    def test_cannot_update_readonly_fields(self, student_client, student_user):
        """Test that readonly fields are ignored."""
        response = student_client.patch('/api/v1/users/me/', {
            'email': 'newemail@test.com',  # Should be readonly
            'role': 'admin'  # Should be readonly
        })
        
        student_user.refresh_from_db()
        
        # Email and role should not change
        assert student_user.email == 'student@slh.edu'
        assert student_user.role == 'student'