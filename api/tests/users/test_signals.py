"""
Signal Tests

Tests for:
- Profile auto-creation signals
- Password history tracking
- User deletion logging
- Counter update signals (mocked)
"""

import pytest
from unittest.mock import patch, MagicMock
from apps.users.models import User, TeacherInfo, StudentInfo, PasswordHistory


@pytest.mark.signal
class TestProfileCreationSignals:
    """Test profile auto-creation via signals."""
    
    def test_teacher_info_created_for_teacher(self, db):
        """Test that TeacherInfo is auto-created when teacher user is created."""
        user = User.objects.create_user(
            email='newteacher@test.com',
            password='Pass@123',
            name='New Teacher',
            role='teacher'
        )
        
        # TeacherInfo should exist
        assert hasattr(user, 'teacher_info')
        assert TeacherInfo.objects.filter(user=user).exists()
    
    def test_teacher_info_created_for_dean(self, db):
        """Test that TeacherInfo is auto-created for dean users."""
        user = User.objects.create_user(
            email='newdean@test.com',
            password='Pass@123',
            name='New Dean',
            role='dean'
        )
        
        assert hasattr(user, 'teacher_info')
        assert TeacherInfo.objects.filter(user=user).exists()
    
    def test_student_info_created_for_student(self, db):
        """Test that StudentInfo is auto-created when student user is created."""
        user = User.objects.create_user(
            email='newstudent@test.com',
            password='Pass@123',
            name='New Student',
            role='student',
            institution='Test',
            department='Test',
            major='Test'
        )
        
        assert hasattr(user, 'student_info')
        assert StudentInfo.objects.filter(user=user).exists()
    
    def test_no_profile_created_for_admin(self, db):
        """Test that no profile is created for admin users."""
        user = User.objects.create_superuser(
            email='newadmin@test.com',
            password='Admin@123',
            name='New Admin'
        )
        
        # Should not have any profile
        assert not TeacherInfo.objects.filter(user=user).exists()
        assert not StudentInfo.objects.filter(user=user).exists()
    
    def test_signal_handles_race_condition(self, db):
        """Test that signal handles race condition if profile already exists."""
        # Create user
        user = User.objects.create_user(
            email='test@test.com',
            password='Pass@123',
            name='Test',
            role='teacher'
        )
        
        # Profile should already exist from signal
        assert TeacherInfo.objects.filter(user=user).exists()
        
        # Manually trigger signal again (shouldn't error)
        from apps.users.signals.profile_signals import create_user_profile
        create_user_profile(User, user, created=True)
        
        # Should still only have one profile
        assert TeacherInfo.objects.filter(user=user).count() == 1


@pytest.mark.signal
class TestPasswordHistorySignals:
    """Test password history tracking via signals."""
    
    def test_password_history_created_on_password_change(self, student_user):
        """Test that password change creates history entry via signal."""
        old_password = 'Student@123'
        new_password = 'NewPass@456'
        
        # Should start with 0 history entries
        initial_count = PasswordHistory.objects.filter(user=student_user).count()
        assert initial_count == 0, f"Expected 0 initial entries, got {initial_count}"
        
        # Change password (signal should fire)
        student_user.change_password(old_password, new_password)
        
        # Should now have 1 entry
        new_count = PasswordHistory.objects.filter(user=student_user).count()
        assert new_count == 1, \
            f"Expected 1 history entry after change, got {new_count}"
    
    def test_password_history_not_created_on_user_creation(self, db):
        """Test that creating user doesn't create password history."""
        user = User.objects.create_user(
            email='new@test.com',
            password='Pass@123',
            name='New User',
            role='student',
            institution='Test',
            department='Test',
            major='Test'
        )
        
        # Should have no password history yet
        count = PasswordHistory.objects.filter(user=user).count()
        assert count == 0, f"New user should have 0 history, got {count}"
    
    def test_password_history_records_old_password(self, student_user):
        """Test that history records the OLD password, not new one."""
        old_password = 'Student@123'
        new_password = 'NewPass@456'
        
        # Get old hash before change
        old_hash = student_user.password
        
        # Change password
        student_user.change_password(old_password, new_password)
        
        # Get history
        history = PasswordHistory.objects.filter(user=student_user).first()
        assert history is not None, "History entry should exist"
        
        # Verify it's the OLD password
        assert history.hashed_password == old_hash, \
            "History should store OLD password hash"
        
        # Should be able to check against old password
        assert history.check_password(old_password), \
            "History should verify old password"
        
        # Should NOT match new password
        assert not history.check_password(new_password), \
            "History should not verify new password"

@pytest.mark.signal
class TestUserDeletionSignals:
    """Test user deletion logging signals."""
    
    @patch('apps.users.signals.profile_signals.logger')
    def test_user_deletion_logged(self, mock_logger, student_user):
        """Test that user deletion is logged."""
        user_email = student_user.email
        user_id = student_user.id
        user_role = student_user.role
        
        student_user.delete()
        
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        call_args = str(mock_logger.warning.call_args)
        assert user_email in call_args
        assert str(user_id) in call_args
        assert user_role in call_args


@pytest.mark.signal
class TestProfileUpdateSignals:
    """Test profile update logging signals."""
    
    @patch('apps.users.signals.profile_signals.logger')
    def test_teacher_profile_creation_logged(self, mock_logger, db):
        """Test that teacher profile creation is logged."""
        user = User.objects.create_user(
            email='teacher@test.com',
            password='Pass@123',
            name='Teacher',
            role='teacher'
        )
        
        # Verify info log was called
        mock_logger.info.assert_any_call(f"Teacher profile created for user {user.id}")
    
    @patch('apps.users.signals.profile_signals.logger')
    def test_student_profile_creation_logged(self, mock_logger, db):
        """Test that student profile creation is logged."""
        user = User.objects.create_user(
            email='student@test.com',
            password='Pass@123',
            name='Student',
            role='student',
            institution='Test',
            department='Test',
            major='Test'
        )
        
        # Verify info log was called
        mock_logger.info.assert_any_call(f"Student profile created for user {user.id}")


@pytest.mark.signal
@pytest.mark.slow
class TestCounterUpdateSignals:
    """Test denormalized counter update signals (mocked)."""
    
    def test_teacher_course_count_signal_exists(self):
        """Test that teacher course count signal is registered."""
        from django.db.models.signals import post_save, post_delete
        from apps.users.signals.counter_signals import update_teacher_course_count
        
        # Verify signal is connected
        receivers = post_save.receivers
        assert any('update_teacher_course_count' in str(r) for r in receivers)
    
    def test_student_enrollment_count_signal_exists(self):
        """Test that student enrollment count signal is registered."""
        from django.db.models.signals import post_save
        from apps.users.signals.counter_signals import update_student_enrollment_count
        
        receivers = post_save.receivers
        assert any('update_student_enrollment_count' in str(r) for r in receivers)


@pytest.mark.signal
class TestSignalErrorHandling:
    """Test signal error handling and recovery."""
    
    @patch('apps.users.signals.profile_signals.mail_admins')
    @patch('apps.users.signals.profile_signals.TeacherInfo.objects.get_or_create')
    def test_profile_creation_error_notifies_admins(self, mock_get_or_create, mock_mail_admins, db):
        """Test that profile creation errors notify admins."""
        # Make signal fail
        mock_get_or_create.side_effect = Exception('Database error')
        
        try:
            User.objects.create_user(
                email='test@test.com',
                password='Pass@123',
                name='Test',
                role='teacher'
            )
        except Exception:
            pass
        
        # Admins should be notified
        assert mock_mail_admins.called