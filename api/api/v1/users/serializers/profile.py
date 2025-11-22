"""
User Profile Serializers

Handles:
- Teacher/Student info (nested serializers)
- User profile viewing
- Profile updates (current user)
"""

from rest_framework import serializers
from apps.users.models import User, TeacherInfo, StudentInfo

# Profile image validation constants
MAX_PROFILE_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']


class TeacherInfoSerializer(serializers.ModelSerializer):
    """
    Teacher-specific information serializer (K-12 Focus).

    Read-only fields:
    - courses_count: Updated via signals
    - subjects_count: Updated via signals
    """

    class Meta:
        model = TeacherInfo
        fields = [
            'designation',
            'specialization',
            'courses_count',
            'subjects_count'
        ]
        read_only_fields = ['courses_count', 'subjects_count']


class StudentInfoSerializer(serializers.ModelSerializer):
    """
    Student-specific information serializer (K-12 Focus).

    Dynamic read-only fields based on user role:
    - Admin: Can edit all fields
    - Dean/Teacher: Read-only access
    - Student: Read-only access (admin edits only)
    """

    class_section_name = serializers.CharField(
        source='class_section.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = StudentInfo
        fields = [
            'status',
            'enrollment_number',
            'class_section',
            'class_section_name',
            'enrolled_courses_count'
        ]
        read_only_fields = ['enrolled_courses_count']

    def get_fields(self):
        """
        Dynamically set read-only fields based on user role.

        Business rules:
        - Admin: Full write access
        - Dean/Teacher: Read-only (can view but not edit)
        - Student: Read-only (cannot edit own status/enrollment)
        """
        fields = super().get_fields()
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            user = request.user

            # Non-admin users have read-only access to sensitive fields
            if user.role != 'admin':
                sensitive_fields = [
                    'status',
                    'enrollment_number',
                    'class_section'
                ]

                for field_name in sensitive_fields:
                    if field_name in fields:
                        fields[field_name].read_only = True

        return fields


class UserProfileSerializer(serializers.ModelSerializer):
    """
    User profile serializer (read-only).
    
    Used for:
    - Current user profile (GET /users/me/)
    - User details in responses
    
    Includes nested teacher_info or student_info based on role.
    """
    
    teacher_info = TeacherInfoSerializer(read_only=True)
    student_info = StudentInfoSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'role',
            'profile_image',
            'institution',
            'department',
            'major',
            'email_verified',
            'is_active',
            'last_login_at',
            'last_seen_at',
            'created_at',
            'updated_at',
            'teacher_info',
            'student_info'
        ]
        read_only_fields = [
            'id',
            'email',
            'role',
            'email_verified',
            'is_active',
            'last_login_at',
            'last_seen_at',
            'created_at',
            'updated_at'
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Profile update serializer for current user (PATCH /users/me/).
    
    Role-based restrictions:
    - Admin: Cannot modify academic fields
    - Dean/Teacher/Student: Can modify academic fields
    """
    
    class Meta:
        model = User
        fields = ['name', 'profile_image', 'institution', 'department', 'major']
    
    def validate(self, attrs):
        """
        Validate role-based field restrictions.
        
        Business rule: Admins cannot have academic affiliations.
        """
        user = self.context['request'].user
        
        # Admin cannot modify academic fields
        if user.role == 'admin':
            academic_fields = ['institution', 'department', 'major']
            provided = [f for f in academic_fields if f in attrs and attrs.get(f)]
            
            if provided:
                raise serializers.ValidationError(
                    {
                        'non_field_errors': (
                            f"Admins cannot modify academic fields: "
                            f"{', '.join(provided)}"
                        )
                    },
                    code='admin_academic_fields'
                )
        
        return attrs
    
    def validate_profile_image(self, value):
        """
        Validate profile image file.
        
        Rules:
        - Max size: 5MB
        - Allowed formats: jpg, jpeg, png, gif
        """
        if not value:
            return value
        
        # Check file size
        max_size = MAX_PROFILE_IMAGE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image size cannot exceed {MAX_PROFILE_IMAGE_SIZE_MB}MB",
                code='file_too_large'
            )

        # Check file extension
        ext = value.name.split('.')[-1].lower()

        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise serializers.ValidationError(
                f"Only {', '.join(ALLOWED_IMAGE_EXTENSIONS)} files are allowed",
                code='invalid_file_type'
            )
        
        return value