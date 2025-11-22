from django.urls import path, include
from api.v1.users import urls as users_urls

urlpatterns = [
    path('auth/', include((users_urls.auth_urlpatterns, 'auth'))),
    path('users/', include((users_urls.users_urlpatterns, 'users'))),
    path('academics/', include('api.v1.academics.urls')),
    path('courses/', include('api.v1.courses.urls')),
    path('content/', include('api.v1.content.urls')),
    path('assessments/', include('api.v1.assessments.urls')),
    path('tools/', include('api.v1.ai_tools.urls')),
    path('progress/', include('api.v1.progress.urls')),
    path('chat/', include('api.v1.communications.urls')),
    path('admin/', include('api.v1.administration.urls')),
]