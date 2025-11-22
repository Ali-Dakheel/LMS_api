"""
Pytest fixtures for courses app tests.
"""

import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.courses.models import (
    Subject,
    Course,
    CoursePath,
    PathModule,
    ModuleDetail,
    ModuleImage,
    Resource,
    ModulePackage,
    ModuleToolOverride,
)

User = get_user_model()


# ============================================================================
# SUBJECT FIXTURES
# ============================================================================

@pytest.fixture
def subject():
    """Create a school-level subject."""
    return Subject.objects.create(
        name="Mathematics",
        code="MATH",
        level="SCHOOL",
        description="School mathematics curriculum",
        ppt_generator=True,
        flashcard_creator=True,
        quiz_generator=True,
        lesson_plan_generator=True,
        worksheet_generator=True,
        mind_map_generator=True,
        simulation=False,
        practice_problems=True,
        step_by_step_solver=True,
        is_active=True
    )


@pytest.fixture
def subject_university():
    """Create a university-level subject."""
    return Subject.objects.create(
        name="Computer Science",
        code="CS",
        level="UNIV",
        description="University CS curriculum",
        ppt_generator=True,
        flashcard_creator=True,
        quiz_generator=True,
        simulation=True,
        is_active=True
    )


@pytest.fixture
def subject_english():
    """Create English subject for language tests."""
    return Subject.objects.create(
        name="English Language",
        code="ENG",
        level="SCHOOL",
        ppt_generator=True,
        flashcard_creator=True,
        quiz_generator=True,
        is_active=True
    )


# ============================================================================
# COURSE FIXTURES
# ============================================================================

@pytest.fixture
def course(subject):
    """Create a course linked to subject."""
    return Course.objects.create(
        subject=subject,
        title="Mathematics Grade 5",
        code="MATH5",
        slug="mathematics-grade-5",
        description="Grade 5 mathematics course",
        level="SCHOOL",
        outcomes="Students will learn basic arithmetic and geometry",
        is_active=True
    )


@pytest.fixture
def course_university(subject_university):
    """Create university course."""
    return Course.objects.create(
        subject=subject_university,
        title="Data Structures",
        code="CS101",
        slug="data-structures",
        description="Fundamental data structures and algorithms",
        level="UNIV",
        credit_hours=3,
        outcomes="Master fundamental data structures",
        is_active=True
    )


@pytest.fixture
def course_with_syllabus(subject, tmp_path):
    """Create course with uploaded syllabus."""
    # Create a dummy PDF file
    pdf_path = tmp_path / "syllabus.pdf"
    pdf_path.write_text("Dummy syllabus content")
    
    return Course.objects.create(
        subject=subject,
        title="English 101",
        code="ENG101",
        slug="english-101",
        level="SCHOOL",
        is_active=True
    )


# ============================================================================
# COURSE PATH FIXTURES
# ============================================================================

@pytest.fixture
def course_path(course):
    """Create a course-scoped path."""
    return CoursePath.objects.create(
        course=course,
        scope="course",
        label="Week 1: Introduction to Algebra",
        slug="week-1-intro-algebra",
        description="Introduction to algebraic concepts",
        objectives="- Understand variables\n- Learn basic equations",
        outcomes="Students can solve basic equations",
        start_date=datetime(2024, 9, 1).date(),
        end_date=datetime(2024, 9, 7).date(),
        source_kind="manual",
        generation_status="not_generated",
        is_published=True,
        published_at=timezone.now(),
        order=1
    )


@pytest.fixture
def teacher_path(course, teacher_user):
    """Create teacher-scoped path."""
    return CoursePath.objects.create(
        course=course,
        scope="teacher",
        teacher=teacher_user,
        label="Teacher Prep: Week 1",
        slug="teacher-prep-week-1",
        description="Teacher preparation notes",
        source_kind="manual",
        is_published=False,
        order=1
    )


@pytest.fixture
def student_path(course, student_user):
    """Create student-scoped path."""
    return CoursePath.objects.create(
        course=course,
        scope="student",
        student=student_user,
        label="Remedial: Fractions",
        slug="remedial-fractions",
        description="Personalized remedial content",
        source_kind="manual",
        is_published=True,
        published_at=timezone.now(),
        order=1
    )


@pytest.fixture
def offering_path(course, course_offering):
    """Create offering-scoped path."""
    return CoursePath.objects.create(
        course=course,
        scope="offering",
        offering=course_offering,
        label="Week 1: Section A",
        slug="week-1-section-a",
        description="Section-specific content",
        start_date=course_offering.term.start_date,
        end_date=course_offering.term.start_date + timedelta(days=7),
        source_kind="manual",
        is_published=True,
        published_at=timezone.now(),
        order=1
    )


# ============================================================================
# MODULE FIXTURES
# ============================================================================

@pytest.fixture
def module(course_path):
    """Create a module in course path."""
    return PathModule.objects.create(
        path=course_path,
        title="Variables and Expressions",
        slug="variables-expressions",
        category="Algebra",
        description="Introduction to variables",
        outcomes="Understand variable notation",
        order=1,
        is_published=True,
        published_at=timezone.now()
    )


@pytest.fixture
def module_unpublished(course_path):
    """Create unpublished module."""
    return PathModule.objects.create(
        path=course_path,
        title="Advanced Topics",
        slug="advanced-topics",
        category="Algebra",
        description="Advanced algebraic topics",
        order=2,
        is_published=False
    )


@pytest.fixture
def multiple_modules(course_path):
    """Create multiple modules for testing."""
    modules = []
    for i in range(1, 4):
        module = PathModule.objects.create(
            path=course_path,
            title=f"Module {i}",
            slug=f"module-{i}",
            category="Algebra",
            order=i,
            is_published=True,
            published_at=timezone.now()
        )
        modules.append(module)
    return modules


# ============================================================================
# MODULE DETAIL FIXTURES
# ============================================================================

@pytest.fixture
def module_detail(module):
    """Create module detail with text content."""
    return ModuleDetail.objects.create(
        module=module,
        content_type="text",
        text_content="<p>Variables are symbols that represent values.</p>",
        objectives="- Define variables\n- Use variables in expressions",
        is_ai_generated=False
    )


@pytest.fixture
def module_detail_ai(module):
    """Create AI-generated module detail."""
    return ModuleDetail.objects.create(
        module=module,
        content_type="text",
        text_content="<p>AI-generated content about variables.</p>",
        is_ai_generated=True
    )


# ============================================================================
# MODULE IMAGE FIXTURES
# ============================================================================

@pytest.fixture
def module_image(module):
    """Create module image."""
    return ModuleImage.objects.create(
        module=module,
        title="Variable Diagram",
        image="module_images/variable_diagram.png",
        alt_text="Diagram showing variable x",
        order=1
    )


# ============================================================================
# RESOURCE FIXTURES
# ============================================================================

@pytest.fixture
def resource_pdf(module):
    """Create PDF resource."""
    return Resource.objects.create(
        module=module,
        type="pdf",
        title="Variables Worksheet",
        description="Practice worksheet for variables",
        file="resources/variables_worksheet.pdf",
        order=1,
        is_required=True
    )


@pytest.fixture
def resource_url(module):
    """Create URL resource."""
    return Resource.objects.create(
        module=module,
        type="url",
        title="Khan Academy - Variables",
        description="External learning resource",
        url="https://www.khanacademy.org/math/algebra/variables",
        order=2,
        is_required=False
    )


@pytest.fixture
def multiple_resources(module):
    """Create multiple resources."""
    resources = []
    
    resources.append(Resource.objects.create(
        module=module,
        type="pdf",
        title="PDF Resource",
        file="resources/test.pdf",
        order=1
    ))
    
    resources.append(Resource.objects.create(
        module=module,
        type="url",
        title="URL Resource",
        url="https://example.com",
        order=2
    ))
    
    return resources


# ============================================================================
# MODULE PACKAGE FIXTURES
# ============================================================================

@pytest.fixture
def module_package(module):
    """Create module package."""
    return ModulePackage.objects.create(
        module=module,
        title="Introduction Package",
        description="Basic concepts package",
        order=1
    )


# ============================================================================
# MODULE TOOL OVERRIDE FIXTURES
# ============================================================================

@pytest.fixture
def tool_override(module):
    """Create tool override for module."""
    return ModuleToolOverride.objects.create(
        module=module,
        ppt_generator=False,  # Override: disable PPT
        flashcard_creator=True,  # Override: enable
        quiz_student_visible=False  # Students can't see quizzes
    )


# ============================================================================
# COMBINED FIXTURES
# ============================================================================

@pytest.fixture
def complete_course_setup(
    course,
    course_path,
    module,
    module_detail,
    module_image,
    resource_pdf,
    resource_url
):
    """
    Complete course setup with all components.
    
    Returns dict with all fixtures for convenience.
    """
    return {
        'course': course,
        'path': course_path,
        'module': module,
        'detail': module_detail,
        'image': module_image,
        'pdf': resource_pdf,
        'url': resource_url,
    }