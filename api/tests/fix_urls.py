"""
Script to show correct URLs for each endpoint
"""

# Correct URL mappings
CORRECT_URLS = {
    # Auth endpoints (under /api/v1/auth/)
    'login': '/api/v1/auth/login/',
    'logout': '/api/v1/auth/logout/',
    'refresh': '/api/v1/auth/refresh/',
    'register': '/api/v1/auth/register/',
    'password_reset_request': '/api/v1/auth/password/reset-request/',
    'password_reset_confirm': '/api/v1/auth/password/reset-confirm/',
    'password_change': '/api/v1/auth/password/change/',
    'email_verify': '/api/v1/auth/email/verify/',
    'email_resend': '/api/v1/auth/email/resend/',
    
    # User management (under /api/v1/users/)
    'profile': '/api/v1/users/me/',
    'avatar': '/api/v1/users/me/avatar/',
    'users_list': '/api/v1/users/',
    'user_detail': '/api/v1/users/{id}/',
    'user_reactivate': '/api/v1/users/{id}/reactivate/',
    'teachers': '/api/v1/users/teachers/',
    'students': '/api/v1/users/students/',
    'deans': '/api/v1/users/deans/',
}

print("Correct URL mappings:")
for key, url in CORRECT_URLS.items():
    print(f"  {key}: {url}")