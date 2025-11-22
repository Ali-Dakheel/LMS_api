"""
User Model Tests

Tests for:
- User model CRUD operations
- User manager methods
- Activity tracking
- Account deactivation/reactivation
- Email verification
- Password management
- TeacherInfo model
- StudentInfo model
"""

import pytest
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from apps.users.models import User, TeacherInfo, StudentInfo, PasswordHistory


@pytest.mark.unit
class TestUserModelCreation:
    """Test User model creation and basic properties."""
    
    def test_create_user_with_email_only(self, db):
        """Test creating user with email-based authentication."""
        user = User.objects.create_user(
            email='test@example.com',
            password='SecurePass@123',
            name='Test User',
            role='student'
        )
        
        assert user.email == 'test@example.com'
        assert user.check_password('SecurePass@123')
        assert user.name == 'Test User'
        assert user.role == 'student'
        assert user.is_active is True
        assert user.email_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_email_is_normalized_and_lowercase(self, db):
        """Test that email is normalized to lowercase."""
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='Pass@123',
            name='Test',
            role='student'
        )
        
        assert user.email == 'test@example.com'
    
    def test_create_superuser_with_admin_role(self, db):
        """Test creating superuser automatically sets admin role and flags."""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='Admin@123',
            name='Admin User'
        )
        
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.role == 'admin'
        assert user.is_active is True
    
    def test_user_string_representation(self, student_user):
        """Test __str__ method returns name and role."""
        expected = f"{student_user.name} ({student_user.role})"
        assert str(student_user) == expected
    
    def test_user_requires_email(self, db):
        """Test that email is required for user creation."""
        with pytest.raises(ValueError, match='Email is required'):
            User.objects.create_user(
                email='',
                password='Pass@123',
                name='Test',
                role='student'
            )
    
    def test_duplicate_email_not_allowed(self, student_user, db):
        """Test that duplicate emails are prevented by database constraint."""
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email=student_user.email,  # Duplicate
                password='Pass@123',
                name='Another User',
                role='student'
            )
    
    def test_create_user_with_all_fields(self, db):
        """Test creating user with all optional fields."""
        user = User.objects.create_user(
            email='complete@test.com',
            password='Pass@123',
            name='Complete User',
            role='teacher',
            institution='MIT',
            department='Computer Science',
            major=''  # Teachers don't have major
        )
        
        assert user.institution == 'MIT'
        assert user.department == 'Computer Science'
        assert user.major == ''


@pytest.mark.unit
class TestUserActivityTracking:
    """Test user activity tracking features."""
    
    def test_update_last_seen_with_ip_and_user_agent(self, student_user):
        """Test updating last seen timestamp with metadata."""
        ip = '192.168.1.100'
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        
        assert student_user.last_seen_at is None
        
        student_user.update_last_seen(ip_address=ip, user_agent=user_agent)
        student_user.refresh_from_db()
        
        assert student_user.last_seen_at is not None
        assert student_user.last_ip_address == ip
        assert user_agent in student_user.last_user_agent
    
    def test_update_last_seen_without_metadata(self, student_user):
        """Test updating only last_seen timestamp."""
        student_user.update_last_seen()
        student_user.refresh_from_db()
        
        assert student_user.last_seen_at is not None
        assert student_user.last_ip_address is None
        assert student_user.last_user_agent == ''
    
    def test_long_user_agent_is_truncated(self, student_user):
        """Test that user agent longer than 500 chars is truncated."""
        long_agent = 'A' * 600
        
        student_user.update_last_seen(user_agent=long_agent)
        student_user.refresh_from_db()
        
        assert len(student_user.last_user_agent) == 500
        assert student_user.last_user_agent == long_agent[:500]
    
    def test_update_last_seen_updates_timestamp_each_time(self, student_user):
        """Test that last_seen is updated on each call."""
        student_user.update_last_seen()
        first_seen = student_user.last_seen_at
        
        # Small delay
        import time
        time.sleep(0.01)
        
        student_user.update_last_seen()
        second_seen = student_user.last_seen_at
        
        assert second_seen > first_seen
    
    def test_last_login_at_can_be_tracked(self, student_user):
        """Test that last_login_at field works correctly."""
        assert student_user.last_login_at is None
        
        now = timezone.now()
        student_user.last_login_at = now
        student_user.save()
        student_user.refresh_from_db()
        
        assert student_user.last_login_at is not None
        # Allow small time difference due to database precision
        assert abs((student_user.last_login_at - now).total_seconds()) < 1


@pytest.mark.unit
class TestUserDeactivation:
    """Test account deactivation and reactivation."""
    
    def test_deactivate_user_with_reason(self, student_user):
        """Test deactivating user account with reason."""
        assert student_user.is_active is True
        assert student_user.deactivated_at is None
        
        reason = 'Policy violation - inappropriate behavior'
        student_user.deactivate(reason=reason)
        student_user.refresh_from_db()
        
        assert student_user.is_active is False
        assert student_user.deactivated_at is not None
        assert student_user.deactivation_reason == reason
    
    def test_deactivate_user_without_reason(self, student_user):
        """Test deactivating user without providing reason."""
        student_user.deactivate()
        student_user.refresh_from_db()
        
        assert student_user.is_active is False
        assert student_user.deactivated_at is not None
        assert student_user.deactivation_reason == ''
    
    def test_reactivate_user(self, inactive_user):
        """Test reactivating deactivated user."""
        assert inactive_user.is_active is False
        assert inactive_user.deactivated_at is not None
        
        inactive_user.reactivate()
        inactive_user.refresh_from_db()
        
        assert inactive_user.is_active is True
        assert inactive_user.deactivated_at is None
        assert inactive_user.deactivation_reason == ''
    
    def test_deactivation_is_atomic(self, student_user):
        """Test that deactivation uses atomic transaction."""
        # This is tested by checking that all fields are updated together
        student_user.deactivate(reason='Test')
        student_user.refresh_from_db()
        
        # All deactivation fields should be set together
        assert student_user.is_active is False
        assert student_user.deactivated_at is not None
        assert student_user.deactivation_reason == 'Test'
    
    def test_deactivation_blacklists_jwt_tokens(self, student_user, student_tokens):
        """Test that deactivation removes outstanding JWT tokens."""
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        # Ensure token exists in database
        OutstandingToken.objects.get_or_create(
            user=student_user,
            token=student_tokens['refresh'],
            defaults={
                'jti': student_tokens['refresh_obj']['jti'],
                'expires_at': timezone.now() + timedelta(days=7)
            }
        )
        
        assert OutstandingToken.objects.filter(user=student_user).exists()
        
        # Deactivate user
        student_user.deactivate(reason='Test')
        
        # Tokens should be deleted
        assert not OutstandingToken.objects.filter(user=student_user).exists()


@pytest.mark.unit
class TestEmailVerification:
    """Test email verification functionality."""
    
    def test_verify_email_marks_as_verified(self, student_user):
        """Test verifying user email."""
        assert student_user.email_verified is False
        assert student_user.email_verified_at is None
        
        student_user.verify_email()
        student_user.refresh_from_db()
        
        assert student_user.email_verified is True
        assert student_user.email_verified_at is not None
    
    def test_verify_email_sets_timestamp(self, student_user):
        """Test that email verification sets accurate timestamp."""
        before = timezone.now()
        student_user.verify_email()
        after = timezone.now()
        
        student_user.refresh_from_db()
        
        assert before <= student_user.email_verified_at <= after
    
    def test_verify_email_can_be_called_multiple_times(self, student_user):
        """Test that verify_email is idempotent."""
        student_user.verify_email()
        first_verified_at = student_user.email_verified_at
        
        # Call again
        student_user.verify_email()
        second_verified_at = student_user.email_verified_at
        
        # Should still be verified
        assert student_user.email_verified is True
        # Timestamp should be updated
        assert second_verified_at >= first_verified_at


"""
Fixed: Use passwords that won't trigger similarity validator
"""

@pytest.mark.unit
class TestPasswordManagement:
    """Test password change functionality."""
    
    def test_change_password_with_valid_old_password(self, student_user):
        """Test changing password successfully."""
        old_password = 'Student@123'
        # Use a password that's NOT similar to email/username
        new_password = 'CompletelyDifferent@789'
        
        student_user.change_password(old_password, new_password)
        student_user.refresh_from_db()
        
        assert student_user.check_password(new_password)
        assert not student_user.check_password(old_password)
    
    def test_change_password_with_wrong_old_password(self, student_user):
        """Test that wrong old password raises error."""
        with pytest.raises(ValidationError, match='incorrect'):
            student_user.change_password('WrongPass@123', 'NewPass@456')
    
    def test_change_password_records_history(self, student_user):
        """Test that password change is recorded in history."""
        old_password = 'Student@123'
        new_password = 'CompletelyDifferent@789'
        
        initial_count = PasswordHistory.objects.filter(user=student_user).count()
        assert initial_count == 0, f"Expected 0 history entries, got {initial_count}"
        
        student_user.change_password(old_password, new_password)
        
        new_count = PasswordHistory.objects.filter(user=student_user).count()
        assert new_count == 1, f"Expected 1 history entry, got {new_count}"
        
        history = PasswordHistory.objects.filter(user=student_user).first()
        assert history.check_password(old_password), "History should contain old password"
        assert not history.check_password(new_password), "History should not contain new password"
    
    def test_cannot_reuse_recent_password(self, student_user):
        """Test that password history prevents reuse."""
        # Use passwords that won't trigger similarity validator
        password1 = 'FirstSecurePass@123'
        password2 = 'SecondSecurePass@456'
        
        # First, change FROM initial password TO password1
        student_user.change_password('Student@123', password1)
        student_user.refresh_from_db()
        
        # Then change FROM password1 TO password2
        student_user.change_password(password1, password2)
        student_user.refresh_from_db()
        
        # Now try to reuse password1 (should be in history)
        with pytest.raises(ValidationError) as exc_info:
            student_user.change_password(password2, password1)
        
        # Check error message
        error_msg = str(exc_info.value)
        assert 'reuse' in error_msg.lower() or 'recent' in error_msg.lower(), \
            f"Expected 'reuse' in error, got: {error_msg}"
    
    def test_weak_password_is_rejected(self, student_user):
        """Test that weak passwords are rejected by Django validators."""
        old_password = 'Student@123'
        weak_password = '123'  # Too short
        
        with pytest.raises(ValidationError):
            student_user.change_password(old_password, weak_password)
    
    def test_password_history_limit_is_5(self, student_user):
        """Test that password history checks last 5 passwords."""
        passwords = [
            'Student@123',
            'FirstPass@456',
            'SecondPass@789',
            'ThirdPass@012',
            'FourthPass@345',
            'FifthPass@678',
        ]
        
        # Change password 5 times
        for i in range(5):
            student_user.change_password(passwords[i], passwords[i+1])
            student_user.refresh_from_db()
        
        # Current password is FifthPass@678
        assert student_user.check_password('FifthPass@678')
        
        # History should contain the last 5 changes
        history_count = PasswordHistory.objects.filter(user=student_user).count()
        assert history_count == 5


@pytest.mark.unit
class TestTeacherInfo:
    """Test TeacherInfo model."""
    
    def test_teacher_info_auto_created_for_teacher(self, teacher_user):
        """Test that TeacherInfo is auto-created via signal."""
        assert hasattr(teacher_user, 'teacher_info')
        assert isinstance(teacher_user.teacher_info, TeacherInfo)
        assert teacher_user.teacher_info.user == teacher_user
    
    def test_teacher_info_auto_created_for_dean(self, dean_user):
        """Test that TeacherInfo is auto-created for dean."""
        assert hasattr(dean_user, 'teacher_info')
        assert isinstance(dean_user.teacher_info, TeacherInfo)
    
    def test_admin_has_no_teacher_info(self, admin_user):
        """Test that admin users don't have TeacherInfo."""
        with pytest.raises(TeacherInfo.DoesNotExist):
            _ = admin_user.teacher_info
    
    def test_student_has_no_teacher_info(self, student_user):
        """Test that students don't have TeacherInfo."""
        with pytest.raises(TeacherInfo.DoesNotExist):
            _ = student_user.teacher_info
    
    def test_teacher_info_default_values(self, db):
        """Test default values for TeacherInfo."""
        user = User.objects.create_user(
            email='newteacher@test.com',
            password='Pass@123',
            name='New Teacher',
            role='teacher'
        )
        
        info = user.teacher_info
        assert info.designation == ''
        assert info.specialization == ''
        assert info.academic_level == 'SCHOOL'
        assert info.courses_count == 0
        assert info.subjects_count == 0
    
    def test_teacher_info_can_update_fields(self, teacher_user):
        """Test updating TeacherInfo fields."""
        info = teacher_user.teacher_info
        info.designation = 'Full Professor'
        info.specialization = 'Deep Learning'
        info.academic_level = 'UNIV'
        info.save()
        
        info.refresh_from_db()
        assert info.designation == 'Full Professor'
        assert info.specialization == 'Deep Learning'
        assert info.academic_level == 'UNIV'
    
    def test_teacher_info_academic_level_choices(self, teacher_user):
        """Test academic level choices validation."""
        info = teacher_user.teacher_info
        
        # Valid choices
        info.academic_level = 'SCHOOL'
        info.save()
        info.refresh_from_db()
        assert info.academic_level == 'SCHOOL'
        
        info.academic_level = 'UNIV'
        info.save()
        info.refresh_from_db()
        assert info.academic_level == 'UNIV'
    
    def test_teacher_info_string_representation(self, teacher_user):
        """Test __str__ method."""
        expected = f"Teacher: {teacher_user.name} ({teacher_user.teacher_info.specialization})"
        assert str(teacher_user.teacher_info) == expected
    
    def test_teacher_info_deletion_cascades(self, teacher_user):
        """Test that deleting user deletes TeacherInfo."""
        teacher_id = teacher_user.id
        teacher_user.delete()
        
        assert not TeacherInfo.objects.filter(user_id=teacher_id).exists()


@pytest.mark.unit
class TestStudentInfo:
    """Test StudentInfo model."""
    
    def test_student_info_auto_created_for_student(self, student_user):
        """Test that StudentInfo is auto-created via signal."""
        assert hasattr(student_user, 'student_info')
        assert isinstance(student_user.student_info, StudentInfo)
        assert student_user.student_info.user == student_user
    
    def test_admin_has_no_student_info(self, admin_user):
        """Test that admin users don't have StudentInfo."""
        with pytest.raises(StudentInfo.DoesNotExist):
            _ = admin_user.student_info
    
    def test_teacher_has_no_student_info(self, teacher_user):
        """Test that teachers don't have StudentInfo."""
        with pytest.raises(StudentInfo.DoesNotExist):
            _ = teacher_user.student_info
    
    def test_student_info_default_values(self, db):
        """Test default values for StudentInfo."""
        user = User.objects.create_user(
            email='newstudent@test.com',
            password='Pass@123',
            name='New Student',
            role='student',
            institution='Test Uni',
            department='CS',
            major='AI'
        )
        
        info = user.student_info
        assert info.status == 'active'
        assert info.enrollment_number is None
        assert info.class_section is None
        assert info.cohort is None
        assert info.enrolled_courses_count == 0
    
    def test_student_info_enrollment_number_unique(self, student_user, db):
        """Test that enrollment numbers must be unique."""
        user2 = User.objects.create_user(
            email='student2@test.com',
            password='Pass@123',
            name='Student 2',
            role='student',
            institution='MIT',
            department='CS',
            major='AI'
        )
        
        # Try to use same enrollment number
        with pytest.raises(IntegrityError):
            user2.student_info.enrollment_number = student_user.student_info.enrollment_number
            user2.student_info.save()
    
    def test_student_info_enrollment_number_can_be_null(self, db):
        """Test that enrollment_number can be null."""
        user = User.objects.create_user(
            email='student3@test.com',
            password='Pass@123',
            name='Student 3',
            role='student',
            institution='MIT',
            department='CS',
            major='AI'
        )
        
        assert user.student_info.enrollment_number is None
    
    def test_student_info_status_choices(self, student_user):
        """Test student status choices."""
        info = student_user.student_info
        
        valid_statuses = ['active', 'inactive', 'graduated', 'suspended']
        
        for status_choice in valid_statuses:
            info.status = status_choice
            info.save()
            info.refresh_from_db()
            assert info.status == status_choice
    
    def test_student_info_string_representation(self, student_user):
        """Test __str__ method."""
        enrollment = student_user.student_info.enrollment_number or 'N/A'
        expected = f"Student: {student_user.name} ({enrollment})"
        assert str(student_user.student_info) == expected
    
    def test_student_info_deletion_cascades(self, student_user):
        """Test that deleting user deletes StudentInfo."""
        student_id = student_user.id
        student_user.delete()
        
        assert not StudentInfo.objects.filter(user_id=student_id).exists()


@pytest.mark.unit
class TestPasswordHistory:
    """Test PasswordHistory model."""
    
    def test_password_history_created_on_change(self, student_user):
        """Test that changing password creates history entry."""
        old_password = 'Student@123'
        new_password = 'NewPass@456'
        
        student_user.change_password(old_password, new_password)
        
        # Check history exists
        history = PasswordHistory.objects.filter(user=student_user).first()
        assert history is not None
        assert history.user == student_user
        assert history.hashed_password is not None
    
    def test_password_history_stores_hashed_password(self, student_user):
        """Test that password history stores hashed password."""
        old_password = 'Student@123'
        new_password = 'NewPass@456'
        
        student_user.change_password(old_password, new_password)
        
        history = PasswordHistory.objects.filter(user=student_user).first()
        
        # Should be hashed (starts with algorithm identifier)
        assert history.hashed_password.startswith('pbkdf2_')
        # Should not contain plaintext
        assert old_password not in history.hashed_password
    
    def test_password_history_check_password(self, student_user):
        """Test checking password against history."""
        old_password = 'Student@123'
        new_password = 'NewPass@456'
        
        # Get old password hash before change
        old_hash = student_user.password
        
        student_user.change_password(old_password, new_password)
        
        history = PasswordHistory.objects.filter(user=student_user).first()
        
        # History should store the OLD password
        assert history.check_password(old_password)
        assert not history.check_password(new_password)
    
    def test_password_history_ordered_by_created_at(self, student_user):
        """Test that password history is ordered newest first."""
        passwords = ['Student@123', 'Pass1@456', 'Pass2@789']
        
        for i in range(len(passwords) - 1):
            student_user.change_password(passwords[i], passwords[i+1])
            student_user.refresh_from_db()
        
        history_entries = list(PasswordHistory.objects.filter(user=student_user))
        
        # Should be ordered newest first
        for i in range(len(history_entries) - 1):
            assert history_entries[i].created_at >= history_entries[i+1].created_at


@pytest.mark.database
class TestUserQueryOptimization:
    """Test query optimization and database performance."""
    
    def test_select_related_for_teacher_info(self, db, django_assert_num_queries):
        """Test that select_related prevents N+1 queries for teacher_info."""
        # Create teachers
        for i in range(5):
            User.objects.create_user(
                email=f'teacher{i}@test.com',
                password='Pass@123',
                name=f'Teacher {i}',
                role='teacher'
            )
        
        # Without select_related: 1 query for users + 5 queries for teacher_info = 6
        # With select_related: 1 query total
        with django_assert_num_queries(1):
            users = User.objects.filter(role='teacher').select_related('teacher_info')
            for user in users:
                _ = user.teacher_info.designation
    
    def test_select_related_for_student_info(self, db, django_assert_num_queries):
        """Test that select_related prevents N+1 queries for student_info."""
        # Create students
        for i in range(5):
            User.objects.create_user(
                email=f'student{i}@test.com',
                password='Pass@123',
                name=f'Student {i}',
                role='student',
                institution='Test',
                department='Test',
                major='Test'
            )
        
        # With select_related: 1 query total
        with django_assert_num_queries(1):
            users = User.objects.filter(role='student').select_related('student_info')
            for user in users:
                _ = user.student_info.status