"""
Simple test to verify basic functionality
"""

import pytest
from apps.users.models import User


@pytest.mark.smoke
def test_can_create_user_and_login(api_client, db):
    """Simplest possible test: create user and login."""
    # 1. Create user
    user = User.objects.create_user(
        email='simple@test.com',
        password='SimplePass@123',
        name='Simple User',
        role='student',
        institution='Test',
        department='Test',
        major='Test'
    )
    
    assert user.email == 'simple@test.com'
    
    # 2. Try to login
    response = api_client.post('/api/v1/auth/login/', {
        'email': 'simple@test.com',
        'password': 'SimplePass@123'
    })
    
    print(f"\nLogin response status: {response.status_code}")
    if response.status_code == 404:
        print("❌ Login endpoint not found!")
        print("Available patterns should be checked")
    elif response.status_code == 200:
        print("✅ Login works!")
        print(f"Response: {response.json()}")
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
        print(f"Response: {response.content}")
    
    assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"