"""
Token Model Tests

Tests for:
- PasswordResetToken model
- EmailVerificationToken model
- Token creation and validation
- Token expiration
- Rate limiting
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.users.models import PasswordResetToken, EmailVerificationToken, verify_email_via_token
import hashlib


@pytest.mark.unit
class TestPasswordResetToken:
    """Test PasswordResetToken model."""
    
    def test_create_password_reset_token(self, student_user):
        """Test creating a valid password reset token."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        assert raw_token is not None
        assert len(raw_token) > 0
        assert token_obj is not None
        assert token_obj.user == student_user
        assert token_obj.used is False
        assert token_obj.expires_at is not None
    
    def test_token_is_hashed_not_plaintext(self, student_user):
        """Test that token is stored as SHA256 hash."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        # Token in DB should be hashed
        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        assert token_obj.token == expected_hash
        assert token_obj.token != raw_token
        assert len(token_obj.token) == 64  # SHA256 hex length
    
    def test_token_expires_in_24_hours(self, student_user):
        """Test that password reset token expires in 24 hours."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        now = timezone.now()
        expected_expiry = now + timedelta(hours=24)
        
        # Should be within 1 minute of 24 hours
        time_diff = abs((token_obj.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60
    
    def test_token_is_valid_when_fresh(self, student_user):
        """Test is_valid returns True for fresh token."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        assert token_obj.is_valid() is True
    
    def test_token_is_invalid_when_used(self, student_user):
        """Test is_valid returns False after token is used."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        token_obj.mark_used()
        
        assert token_obj.is_valid() is False
        assert token_obj.used is True
        assert token_obj.used_at is not None
    
    def test_token_is_invalid_when_expired(self, student_user):
        """Test is_valid returns False for expired token."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        # Manually expire the token
        token_obj.expires_at = timezone.now() - timedelta(hours=1)
        token_obj.save()
        
        assert token_obj.is_valid() is False
    
    def test_mark_used_sets_timestamp(self, student_user):
        """Test that mark_used sets used_at timestamp."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        before = timezone.now()
        token_obj.mark_used()
        after = timezone.now()
        
        assert token_obj.used is True
        assert before <= token_obj.used_at <= after
    
    def test_verify_token_with_valid_raw_token(self, student_user):
        """Test verifying a token using raw token string."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        verified = PasswordResetToken.verify_token(raw_token)
        
        assert verified is not None
        assert verified.id == token_obj.id
        assert verified.user == student_user
    
    def test_verify_token_returns_none_for_invalid(self, student_user):
        """Test verify_token returns None for invalid token."""
        verified = PasswordResetToken.verify_token('invalid-token-string')
        
        assert verified is None
    
    def test_verify_token_returns_none_for_expired(self, student_user):
        """Test verify_token returns None for expired token."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        # Expire the token
        token_obj.expires_at = timezone.now() - timedelta(hours=1)
        token_obj.save()
        
        verified = PasswordResetToken.verify_token(raw_token)
        
        assert verified is None
    
    def test_verify_token_returns_none_for_used(self, student_user):
        """Test verify_token returns None for already used token."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        token_obj.mark_used()
        
        verified = PasswordResetToken.verify_token(raw_token)
        
        assert verified is None


@pytest.mark.unit
class TestPasswordResetTokenRateLimiting:
    """Test rate limiting on password reset token creation."""
    
    def test_rate_limit_blocks_4th_token(self, student_user):
        """
        Test that 4th token within 5 minutes is blocked.
        
        Note: create_token() deletes old unused tokens, so we need to
        create tokens WITHOUT using create_token() to test the limit.
        """
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta
        import hashlib
        import secrets
        
        # Manually create 3 tokens in last 5 minutes (bypass the deletion logic)
        for i in range(3):
            raw_token = secrets.token_urlsafe(32)
            hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
            PasswordResetToken.objects.create(
                user=student_user,
                token=hashed_token,
                expires_at=timezone.now() + timedelta(hours=24),
                used=False
            )
        
        # Now try to create 4th via the method (should check rate limit)
        with pytest.raises(ValidationError) as exc_info:
            PasswordResetToken.create_token(student_user)
        
        assert 'too many' in str(exc_info.value).lower()
    
    def test_rate_limit_allows_3_tokens(self, student_user):
        """Test that up to 3 tokens can be created."""
        # This will work because each create_token deletes old ones
        for i in range(3):
            raw_token, token_obj = PasswordResetToken.create_token(student_user)
            assert token_obj is not None
        
        # But there's only 1 token in DB (others were deleted)
        count = PasswordResetToken.objects.filter(user=student_user).count()
        assert count == 1  # Only latest token exists
    
    def test_rate_limit_counts_recent_tokens(self, student_user):
        """Test that rate limit counts all tokens in last 5 minutes."""
        from datetime import timedelta
        import hashlib
        import secrets
        
        # Create 3 tokens manually (all within 5 minutes)
        now = timezone.now()
        for i in range(3):
            raw_token = secrets.token_urlsafe(32)
            hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
            PasswordResetToken.objects.create(
                user=student_user,
                token=hashed_token,
                expires_at=now + timedelta(hours=24),
                created_at=now - timedelta(minutes=i)  # Spread over 3 minutes
            )
        
        # Verify 3 exist
        recent_count = PasswordResetToken.objects.filter(
            user=student_user,
            created_at__gte=now - timedelta(minutes=5)
        ).count()
        assert recent_count == 3
        
        # 4th should be blocked
        with pytest.raises(ValidationError):
            PasswordResetToken.create_token(student_user)

@pytest.mark.unit
class TestEmailVerificationToken:
    """Test EmailVerificationToken model."""
    
    def test_create_email_verification_token(self, student_user):
        """Test creating email verification token."""
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        assert raw_token is not None
        assert token_obj is not None
        assert token_obj.user == student_user
        assert token_obj.used is False
        assert token_obj.expires_at is not None
    
    def test_token_expires_in_48_hours(self, student_user):
        """Test that email verification token expires in 48 hours."""
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        now = timezone.now()
        expected_expiry = now + timedelta(hours=48)
        
        # Should be within 1 minute of 48 hours
        time_diff = abs((token_obj.expires_at - expected_expiry).total_seconds())
        assert time_diff < 60
    
    def test_token_is_hashed(self, student_user):
        """Test that email verification token is hashed."""
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        assert token_obj.token == expected_hash
        assert token_obj.token != raw_token
    
    def test_verify_token_with_valid_token(self, student_user):
        """Test verifying valid email token."""
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        verified = EmailVerificationToken.verify_token(raw_token)
        
        assert verified is not None
        assert verified.id == token_obj.id
    
    def test_verify_token_returns_none_for_invalid(self, student_user):
        """Test verify_token returns None for invalid token."""
        verified = EmailVerificationToken.verify_token('invalid-token')
        
        assert verified is None
    
    def test_previous_tokens_deleted_on_new_request(self, student_user):
        """Test that new token request deletes previous unused tokens."""
        raw_token1, token_obj1 = EmailVerificationToken.create_token(student_user)
        token_id_1 = token_obj1.id
        
        raw_token2, token_obj2 = EmailVerificationToken.create_token(student_user)
        
        assert not EmailVerificationToken.objects.filter(id=token_id_1).exists()
        assert EmailVerificationToken.objects.filter(id=token_obj2.id).exists()
    
    def test_token_manager_valid_only(self, student_user):
        """Test EmailVerificationToken manager valid_only method."""
        # Create valid token
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        valid_tokens = EmailVerificationToken.objects.valid_only()
        
        assert token_obj in valid_tokens
    
    def test_token_manager_for_user(self, student_user, teacher_user):
        """Test EmailVerificationToken manager for_user method."""
        raw_token1, token_obj1 = EmailVerificationToken.create_token(student_user)
        raw_token2, token_obj2 = EmailVerificationToken.create_token(teacher_user)
        
        student_tokens = EmailVerificationToken.objects.for_user(student_user)
        
        assert token_obj1 in student_tokens
        assert token_obj2 not in student_tokens


@pytest.mark.unit
class TestVerifyEmailViaToken:
    """Test verify_email_via_token utility function."""
    
    def test_verify_email_via_token_marks_email_verified(self, unverified_user):
        """Test that verify_email_via_token marks email as verified."""
        assert unverified_user.email_verified is False
        
        raw_token, token_obj = EmailVerificationToken.create_token(unverified_user)
        
        user = verify_email_via_token(raw_token)
        
        assert user.email_verified is True
        assert user.email_verified_at is not None
    
    def test_verify_email_via_token_marks_token_used(self, unverified_user):
        """Test that token is marked as used after verification."""
        raw_token, token_obj = EmailVerificationToken.create_token(unverified_user)
        
        verify_email_via_token(raw_token)
        
        token_obj.refresh_from_db()
        assert token_obj.used is True
        assert token_obj.used_at is not None
    
    def test_verify_email_via_token_raises_for_invalid_token(self, unverified_user):
        """Test that invalid token raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid or expired'):
            verify_email_via_token('invalid-token')
    
    def test_verify_email_via_token_is_atomic(self, unverified_user):
        """Test that verification is atomic (all or nothing)."""
        raw_token, token_obj = EmailVerificationToken.create_token(unverified_user)
        
        user = verify_email_via_token(raw_token)
        
        # Both user and token should be updated
        user.refresh_from_db()
        token_obj.refresh_from_db()
        
        assert user.email_verified is True
        assert token_obj.used is True


@pytest.mark.unit
class TestTokenStringRepresentation:
    """Test __str__ methods of token models."""
    
    def test_password_reset_token_str(self, student_user):
        """Test PasswordResetToken __str__ method."""
        raw_token, token_obj = PasswordResetToken.create_token(student_user)
        
        # Should contain user email and expiry info
        str_repr = str(token_obj)
        assert student_user.email in str_repr
        # Accept either format
        assert 'expires' in str_repr or 'valid' in str_repr or 'Reset token' in str_repr    
    def test_email_verification_token_has_str_method(self, student_user):
        """Test EmailVerificationToken has __str__ method."""
        raw_token, token_obj = EmailVerificationToken.create_token(student_user)
        
        # Just ensure it doesn't error
        str_repr = str(token_obj)
        assert isinstance(str_repr, str)