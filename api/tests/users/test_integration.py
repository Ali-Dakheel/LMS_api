"""
Integration Tests
"""

import pytest
from apps.users.models import User


@pytest.mark.integration
class TestCompleteUserWorkflows:
    """Test complete end-to-end user workflows."""
        
    def test_complete_password_reset_flow(self, api_client, student_user, db):
        """Test: Request reset → Reset password → Login with new password."""
        from apps.users.models import PasswordResetToken
        
        # 1. Request password reset (✅ FIXED URL)
        reset_request = api_client.post('/api/v1/auth/password/reset-request/', {
            'email': 'student@slh.edu'
        })
        assert reset_request.status_code == 200
        
        # 2. Create token for testing
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        # 3. Reset password (✅ FIXED URL)
        reset_confirm = api_client.post('/api/v1/auth/password/reset-confirm/', {
            'token': raw_token,
            'new_password': 'NewPassword@123',
            'new_password_confirm': 'NewPassword@123'
        })
        assert reset_confirm.status_code == 200
        
        # 4. Login with new password (✅ FIXED URL)
        login_response = api_client.post('/api/v1/auth/login/', {
            'email': 'student@slh.edu',
            'password': 'NewPassword@123'
        })
        assert login_response.status_code == 200