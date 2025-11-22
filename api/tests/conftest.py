"""
Root conftest.py - Shared fixtures for all tests.

Provides:
- Django setup
- Database configuration
- Common utilities
- Global fixtures
"""

import pytest
from django.conf import settings
from django.core.management import call_command


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configure database for testing session.
    
    Runs migrations once per test session.
    """
    with django_db_blocker.unblock():
        call_command('migrate', '--noinput')


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    
    Ensures every test has database access without explicit db fixture.
    """
    pass


@pytest.fixture(autouse=True)
def reset_sequences(db):
    """Reset database sequences after each test."""
    yield
    # Sequences auto-reset by Django's test database teardown


@pytest.fixture
def settings_override(settings):
    """
    Override Django settings for testing.
    
    Usage:
        def test_something(settings_override):
            settings_override(DEBUG=True, ALLOWED_HOSTS=['*'])
    """
    original_settings = {}
    
    def _override(**kwargs):
        for key, value in kwargs.items():
            original_settings[key] = getattr(settings, key, None)
            setattr(settings, key, value)
    
    yield _override
    
    # Restore original settings
    for key, value in original_settings.items():
        setattr(settings, key, value)


@pytest.fixture
def mock_now():
    """
    Mock timezone.now() for consistent timestamp testing.
    
    Usage:
        def test_something(mock_now):
            fixed_time = datetime(2025, 1, 1, 12, 0, 0)
            with mock_now(fixed_time):
                # timezone.now() returns fixed_time
    """
    from unittest.mock import patch
    from django.utils import timezone
    
    def _mock(dt):
        return patch.object(timezone, 'now', return_value=dt)
    
    return _mock


# Register custom markers
def pytest_configure(config):
    """Register custom pytest markers."""
    markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "api: API endpoint tests",
        "auth: Authentication tests",
        "security: Security tests",
        "slow: Slow running tests",
        "smoke: Smoke/sanity tests",
        "database: Database tests",
        "signal: Signal handler tests",
        "performance: Performance tests",
    ]
    
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.
    
    - Mark all test_models.py as unit tests
    - Mark all test_*_api.py as api tests
    """
    for item in items:
        # Auto-mark model tests
        if "test_models" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark API tests
        if any(x in item.nodeid for x in ["auth/", "password/", "profile/", "admin/"]):
            item.add_marker(pytest.mark.api)
        
        # Auto-mark signal tests
        if "test_signals" in item.nodeid:
            item.add_marker(pytest.mark.signal)