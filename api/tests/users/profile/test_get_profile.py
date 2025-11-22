"""
Get Profile Tests 
"""

import pytest


@pytest.mark.api
class TestGetProfile:
    """Essential get profile tests."""
    
    def test_get_own_profile(self, student_client, student_user):
        """Test user can get their own profile."""
        response = student_client.get('/api/v1/users/me/')
        
        assert response.status_code == 200
        data = response.json()['data']
        
        assert data['email'] == student_user.email
        assert data['name'] == student_user.name
        assert data['role'] == 'student'
        assert 'student_info' in data
    
    def test_get_profile_requires_authentication(self, api_client):
        """Test profile endpoint requires authentication."""
        response = api_client.get('/api/v1/users/me/')
        
        assert response.status_code == 401
    
    def test_get_profile_updates_last_seen(self, student_client, student_user):
        """Test that accessing profile updates last_seen."""
        assert student_user.last_seen_at is None
        
        student_client.get('/api/v1/users/me/')
        
        student_user.refresh_from_db()
        assert student_user.last_seen_at is not None