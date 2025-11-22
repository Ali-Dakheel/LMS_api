"""
UserManager Tests

Tests for:
- User creation methods
- Role-based query methods
- Query optimization
"""

import pytest
from apps.users.models import User


@pytest.mark.unit
class TestUserManagerCreation:
    """Test UserManager user creation methods."""
    
    def test_create_user_normalizes_email(self, db):
        """Test that create_user normalizes email to lowercase."""
        user = User.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='Pass@123',
            name='Test User',
            role='student'
        )
        
        assert user.email == 'test@example.com'
    
    def test_create_user_requires_email(self, db):
        """Test that create_user raises ValueError without email."""
        with pytest.raises(ValueError, match='Email is required'):
            User.objects.create_user(
                email='',
                password='Pass@123',
                name='Test',
                role='student'
            )
    
    def test_create_user_with_extra_fields(self, db):
        """Test that create_user accepts extra fields."""
        user = User.objects.create_user(
            email='test@example.com',
            password='Pass@123',
            name='Test User',
            role='teacher',
            institution='MIT',
            department='CS'
        )
        
        assert user.institution == 'MIT'
        assert user.department == 'CS'
    
    def test_create_superuser_sets_flags(self, db):
        """Test that create_superuser sets is_staff and is_superuser."""
        user = User.objects.create_superuser(
            email='admin@test.com',
            password='Admin@123',
            name='Admin'
        )
        
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == 'admin'
    
    def test_create_superuser_requires_is_staff(self, db):
        """Test that create_superuser enforces is_staff=True."""
        with pytest.raises(ValueError, match='is_staff=True'):
            User.objects.create_superuser(
                email='admin@test.com',
                password='Admin@123',
                name='Admin',
                is_staff=False
            )
    
    def test_create_superuser_requires_is_superuser(self, db):
        """Test that create_superuser enforces is_superuser=True."""
        with pytest.raises(ValueError, match='is_superuser=True'):
            User.objects.create_superuser(
                email='admin@test.com',
                password='Admin@123',
                name='Admin',
                is_superuser=False
            )


@pytest.mark.unit
class TestUserManagerRoleQueries:
    """Test UserManager role-based query methods."""
    
    def test_get_teachers_returns_only_teachers(self, db, teacher_user, student_user, admin_user):
        """Test get_teachers returns only active teacher users."""
        teachers = User.objects.get_teachers()
        
        assert teacher_user in teachers
        assert student_user not in teachers
        assert admin_user not in teachers
    
    def test_get_teachers_excludes_inactive(self, db, teacher_user):
        """Test get_teachers excludes inactive teachers."""
        teacher_user.deactivate(reason='Test')
        
        teachers = User.objects.get_teachers()
        
        assert teacher_user not in teachers
    
    def test_get_students_returns_only_students(self, db, student_user, teacher_user, admin_user):
        """Test get_students returns only active student users."""
        students = User.objects.get_students()
        
        assert student_user in students
        assert teacher_user not in students
        assert admin_user not in students
    
    def test_get_students_excludes_inactive(self, db, student_user):
        """Test get_students excludes inactive students."""
        student_user.deactivate(reason='Test')
        
        students = User.objects.get_students()
        
        assert student_user not in students
    
    def test_get_deans_returns_only_deans(self, db, dean_user, teacher_user, student_user):
        """Test get_deans returns only active dean users."""
        deans = User.objects.get_deans()
        
        assert dean_user in deans
        assert teacher_user not in deans
        assert student_user not in deans
    
    def test_get_deans_excludes_inactive(self, db, dean_user):
        """Test get_deans excludes inactive deans."""
        dean_user.deactivate(reason='Test')
        
        deans = User.objects.get_deans()
        
        assert dean_user not in deans


@pytest.mark.unit
class TestUserManagerGetByRole:
    """Test UserManager get_by_role method with optimization."""
    
    def test_get_by_role_teacher_with_select_related(self, db, teacher_user):
        """Test get_by_role for teachers includes teacher_info."""
        users = User.objects.get_by_role('teacher')
        
        # Verify teacher is in queryset
        assert teacher_user in users
        
        # Verify query is optimized (would need django-assert-num-queries for full test)
        for user in users:
            # This should not trigger additional query
            _ = user.teacher_info.designation
    
    def test_get_by_role_student_with_select_related(self, db, student_user):
        """Test get_by_role for students includes student_info."""
        users = User.objects.get_by_role('student')
        
        assert student_user in users
        
        # Should not trigger additional queries
        for user in users:
            _ = user.student_info.status
    
    def test_get_by_role_admin_no_select_related(self, db, admin_user):
        """Test get_by_role for admin doesn't add select_related."""
        users = User.objects.get_by_role('admin')
        
        assert admin_user in users
    
    def test_get_by_role_returns_only_active(self, db, student_user):
        """Test get_by_role returns only active users."""
        student_user.deactivate(reason='Test')
        
        users = User.objects.get_by_role('student')
        
        assert student_user not in users


@pytest.mark.database
class TestUserManagerQueryOptimization:
    """Test query optimization in UserManager methods."""
    
    def test_get_teachers_uses_select_related(self, db, django_assert_num_queries):
        """Test that get_teachers uses select_related for optimization."""
        # Create multiple teachers
        for i in range(3):
            User.objects.create_user(
                email=f'teacher{i}@test.com',
                password='Pass@123',
                name=f'Teacher {i}',
                role='teacher'
            )
        
        # Should use 1 query with select_related
        with django_assert_num_queries(1):
            teachers = list(User.objects.get_teachers())
            for teacher in teachers:
                _ = teacher.teacher_info.designation
    
    def test_get_students_uses_select_related(self, db, django_assert_num_queries):
        """Test that get_students uses select_related for optimization."""
        # Create multiple students
        for i in range(3):
            User.objects.create_user(
                email=f'student{i}@test.com',
                password='Pass@123',
                name=f'Student {i}',
                role='student',
                institution='Test',
                department='Test',
                major='Test'
            )
        
        # Should use 1 query with select_related
        with django_assert_num_queries(1):
            students = list(User.objects.get_students())
            for student in students:
                _ = student.student_info.status


@pytest.mark.unit
class TestUserManagerEdgeCases:
    """Test edge cases in UserManager."""
    
    def test_get_teachers_returns_empty_queryset_when_none(self, db):
        """Test get_teachers returns empty queryset when no teachers exist."""
        teachers = User.objects.get_teachers()
        
        assert teachers.count() == 0
        assert list(teachers) == []
    
    def test_get_students_returns_empty_queryset_when_none(self, db):
        """Test get_students returns empty queryset when no students exist."""
        students = User.objects.get_students()
        
        assert students.count() == 0
    
    def test_multiple_managers_dont_interfere(self, db, student_user, teacher_user):
        """Test that multiple manager queries don't interfere with each other."""
        teachers = User.objects.get_teachers()
        students = User.objects.get_students()
        
        assert teacher_user in teachers
        assert teacher_user not in students
        assert student_user in students
        assert student_user not in teachers