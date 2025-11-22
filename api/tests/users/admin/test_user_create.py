"""
User List Tests 
"""

import pytest


@pytest.mark.api
class TestUserList:
    """Essential user list tests."""
    
    def test_admin_can_list_users(self, admin_client):
        """Test admin can list all users."""
        response = admin_client.get('/api/v1/users/')
        
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data or 'results' in data
    
    def test_non_admin_cannot_list_users(self, student_client):
        """Test students cannot list users."""
        response = student_client.get('/api/v1/users/')
        
        assert response.status_code == 403
    
    def test_list_users_with_filters(self, admin_client, db):
        """Test filtering users by role."""
        response = admin_client.get('/api/v1/users/?role=student')
        
        assert response.status_code == 200
    
    def test_list_users_with_search(self, admin_client):
        """Test searching users."""
        response = admin_client.get('/api/v1/users/?search=student')
        
        assert response.status_code == 200