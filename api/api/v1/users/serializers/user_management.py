"""
User Management Serializers (Admin Only)

Handles:
- User list view (minimal fields)
- User detail view (full fields)
- User creation and updates with role-based validation
"""

import logging
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.users.models import User, TeacherInfo, StudentInfo
from .profile import TeacherInfoSerializer, StudentInfoSerializer

logger = logging.getLogger(__name__)


class UserListSerializer(serializers.ModelSerializer):
    """
    Minimal user list serializer (K-12 Focus).

    Used for: GET /users/ (paginated list)

    Includes role-specific status for quick filtering:
    - student_status for students
    """

    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )
    student_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'role_display',
            'is_active',
            'email_verified',
            'created_at',
            'last_login_at',
            'student_status'
        ]

    def get_student_status(self, obj):
        """Get student status if applicable."""
        if obj.role == 'student' and hasattr(obj, 'student_info'):
            return obj.student_info.status
        return None


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Full user detail serializer (admin view).
    
    Used for: GET /users/{id}/
    
    Includes all user fields and nested role-specific info.
    """
    
    teacher_info = TeacherInfoSerializer(read_only=True)
    student_info = StudentInfoSerializer(read_only=True)
    role_display = serializers.CharField(
        source='get_role_display',
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'role_display',
            'profile_image',
            'institution',
            'department',
            'major',
            'is_active',
            'email_verified',
            'email_verified_at',
            'deactivated_at',
            'deactivation_reason',
            'last_login_at',
            'last_seen_at',
            'last_page_path',
            'last_ip_address',
            'last_user_agent',
            'created_at',
            'updated_at',
            'teacher_info',
            'student_info'
        ]


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """
    User creation and update serializer (admin only).
    
    Role-based validation:
    - Admin: No academic fields, no role-specific info
    - Dean: Optional academic fields, optional teacher_info
    - Teacher: Required institution/department, required teacher_info
    - Student: Required institution/department/major, optional student_info
    
    Features:
    - Atomic transactions for data consistency
    - Automatic profile creation via signals
    - Fallback profile creation if signal fails
    """
    
    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'}
    )
    
    # Nested serializers for role-specific info
    teacher_info = TeacherInfoSerializer(required=False, allow_null=True)
    student_info = StudentInfoSerializer(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'password',
            'institution',
            'department',
            'major',
            'is_active',
            'teacher_info',
            'student_info'
        ]
        read_only_fields = ['id']
    
    def validate_email(self, value):
        """Validate email uniqueness (case-insensitive)."""
        value = value.lower()
        user_id = self.instance.id if self.instance else None
        
        if User.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError(
                "User with this email already exists",
                code='email_exists'
            )
        
        return value
    
    def validate_password(self, value):
        """Validate password strength using Django validators."""
        if value:
            try:
                validate_password(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(
                    list(e.messages),
                    code='weak_password'
                )
        return value
    
    def validate(self, attrs):
        """
        Role-based field validation.
        
        Enforces business rules for each role:
        1. Admin: No academic fields or role info
        2. Dean: Optional academic fields, optional teacher_info
        3. Teacher: Required academic fields and teacher_info
        4. Student: Required academic fields and optional student_info
        """
        role = attrs.get('role') or (self.instance.role if self.instance else None)
        is_create = not self.instance
        
        # Password required on create
        if is_create and not attrs.get('password'):
            raise serializers.ValidationError(
                {"password": "Password is required"},
                code='password_required'
            )
        
        errors = {}
        
        # ADMIN VALIDATION
        if role == 'admin':
            errors.update(self._validate_admin_fields(attrs))
        
        # DEAN VALIDATION
        elif role == 'dean':
            errors.update(self._validate_dean_fields(attrs))
        
        # TEACHER VALIDATION
        elif role == 'teacher':
            errors.update(self._validate_teacher_fields(attrs, is_create))
        
        # STUDENT VALIDATION
        elif role == 'student':
            errors.update(self._validate_student_fields(attrs, is_create))
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
    
    # =========================================================================
    # ROLE-SPECIFIC VALIDATION HELPERS
    # =========================================================================
    
    def _validate_admin_fields(self, attrs):
        """Validate admin cannot have academic fields or role info."""
        errors = {}
        
        # Check academic fields
        forbidden_academic = {
            'institution': attrs.get('institution'),
            'department': attrs.get('department'),
            'major': attrs.get('major'),
        }
        
        provided_academic = [f for f, v in forbidden_academic.items() if v]
        if provided_academic:
            errors['non_field_errors'] = (
                f"Admin users cannot have academic fields: "
                f"{', '.join(provided_academic)}"
            )
        
        # Check role-specific info
        if attrs.get('teacher_info'):
            errors['teacher_info'] = "Admin cannot have teacher_info"
        if attrs.get('student_info'):
            errors['student_info'] = "Admin cannot have student_info"
        
        return errors
    
    def _validate_dean_fields(self, attrs):
        """Validate dean optional fields (K-12 Focus)."""
        errors = {}

        # Academic fields are optional for deans
        # If teacher_info provided, validate it
        teacher_info = attrs.get('teacher_info')
        if teacher_info:
            if not teacher_info.get('designation'):
                errors.setdefault('teacher_info', {})['designation'] = (
                    "Designation is required if providing teacher_info"
                )
            if not teacher_info.get('specialization'):
                errors.setdefault('teacher_info', {})['specialization'] = (
                    "Specialization is required if providing teacher_info"
                )

        # Deans cannot have student_info
        if attrs.get('student_info'):
            errors['student_info'] = "Dean cannot have student_info"

        return errors
    
    def _validate_teacher_fields(self, attrs, is_create):
        """Validate teacher required fields (K-12 Focus)."""
        errors = {}

        if is_create:
            # Required academic fields
            if not attrs.get('institution'):
                errors['institution'] = "Institution is required for teachers"
            if not attrs.get('department'):
                errors['department'] = "Department is required for teachers"

            # Required teacher_info
            teacher_info = attrs.get('teacher_info')
            if not teacher_info:
                errors['teacher_info'] = (
                    "Teacher info is required "
                    "(designation, specialization)"
                )
            else:
                # Validate required fields
                if not teacher_info.get('designation'):
                    errors.setdefault('teacher_info', {})['designation'] = (
                        "Designation is required"
                    )
                if not teacher_info.get('specialization'):
                    errors.setdefault('teacher_info', {})['specialization'] = (
                        "Specialization is required"
                    )

        # Teachers cannot have student_info
        if attrs.get('student_info'):
            errors['student_info'] = "Teachers cannot have student_info"

        return errors
    
    def _validate_student_fields(self, attrs, is_create):
        """Validate student required fields."""
        errors = {}
        
        if is_create:
            # Required academic fields
            required_fields = {
                'institution': 'Institution is required for students',
                'department': 'Department is required for students',
                'major': 'Major/Program is required for students'
            }
            
            for field, message in required_fields.items():
                if not attrs.get(field):
                    errors[field] = message
            
            # Validate student_info if provided
            student_info = attrs.get('student_info')
            if student_info:
                # Check enrollment number uniqueness
                enrollment_num = student_info.get('enrollment_number')
                if enrollment_num:
                    if StudentInfo.objects.filter(
                        enrollment_number=enrollment_num
                    ).exclude(user=self.instance).exists():
                        errors.setdefault('student_info', {})['enrollment_number'] = (
                            "Enrollment number already exists"
                        )
                
                # Validate status
                status = student_info.get('status')
                if status and status not in ['active', 'inactive', 'graduated', 'suspended']:
                    errors.setdefault('student_info', {})['status'] = (
                        "Invalid status. Must be: active, inactive, graduated, or suspended"
                    )
        
        # Students cannot have teacher_info
        if attrs.get('teacher_info'):
            errors['teacher_info'] = "Students cannot have teacher_info"
        
        return errors
    
    # =========================================================================
    # CREATE & UPDATE METHODS
    # =========================================================================
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create user with role-specific info (atomic transaction).
        
        Steps:
        1. Extract nested data
        2. Clear academic fields for admin
        3. Create user
        4. Update role-specific info (with fallback creation)
        """
        teacher_info_data = validated_data.pop('teacher_info', None)
        student_info_data = validated_data.pop('student_info', None)
        password = validated_data.pop('password')
        role = validated_data['role']
        
        # Clear academic fields for admin
        if role == 'admin':
            validated_data.update({
                'institution': '',
                'department': '',
                'major': ''
            })
        
        # Create user
        user = User.objects.create_user(password=password, **validated_data)
        logger.info(f"Created user {user.id} ({user.email}) with role {user.role}")
        
        # Update role-specific info
        self._update_role_info(user, teacher_info_data, student_info_data)
        
        return user
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update user with role-specific info (atomic transaction).
        
        Steps:
        1. Extract nested data
        2. Clear academic fields if admin
        3. Update user fields
        4. Update password if provided
        5. Update role-specific info
        """
        teacher_info_data = validated_data.pop('teacher_info', None)
        student_info_data = validated_data.pop('student_info', None)
        password = validated_data.pop('password', None)
        
        # Get role
        role = validated_data.get('role', instance.role)
        
        # Clear academic fields if admin
        if role == 'admin':
            validated_data.update({
                'institution': '',
                'department': '',
                'major': ''
            })
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        logger.info(f"Updated user {instance.id} ({instance.email})")
        
        # Update role-specific info
        self._update_role_info(instance, teacher_info_data, student_info_data)
        
        return instance
    
    def _update_role_info(self, user, teacher_info_data, student_info_data):
        """
        Update teacher/student info with fallback creation.
        
        Features:
        - Creates profile if signal failed
        - Logs warnings for missing profiles
        - Updates only provided fields
        """
        # Teachers and Deans can have teacher_info
        if user.role in ['teacher', 'dean'] and teacher_info_data:
            try:
                teacher_info = user.teacher_info
            except TeacherInfo.DoesNotExist:
                # Create if doesn't exist (signal failed)
                teacher_info = TeacherInfo.objects.create(user=user)
                logger.warning(
                    f"TeacherInfo missing for {user.role} {user.id}, created manually"
                )
            
            # Update provided fields
            for attr, value in teacher_info_data.items():
                setattr(teacher_info, attr, value)
            teacher_info.save()
            
            logger.info(
                f"Updated TeacherInfo for {user.role} {user.id}: "
                f"{list(teacher_info_data.keys())}"
            )
        
        # Students have student_info
        elif user.role == 'student' and student_info_data:
            try:
                student_info = user.student_info
            except StudentInfo.DoesNotExist:
                # Create if doesn't exist (signal failed)
                student_info = StudentInfo.objects.create(user=user)
                logger.warning(
                    f"StudentInfo missing for student {user.id}, created manually"
                )
            
            # Update provided fields
            for attr, value in student_info_data.items():
                setattr(student_info, attr, value)
            student_info.save()
            
            logger.info(
                f"Updated StudentInfo for student {user.id}: "
                f"{list(student_info_data.keys())}"
            )