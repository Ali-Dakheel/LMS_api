"""
Unit tests for Courses app models.

Tests:
- Subject creation and tool configuration
- Course creation and slug generation
- CoursePath with 4 scopes
- PathModule creation and publishing
- ModuleDetail content types
- Resource validation
- Tool overrides
"""

import pytest
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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


# ============================================================================
# SUBJECT MODEL TESTS
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestSubjectModel:
    """Test Subject model."""
    
    def test_create_subject(self, db):
        """Test creating a subject."""
        subject = Subject.objects.create(
            name="Physics",
            code="PHY",
            level="SCHOOL",
            description="School physics curriculum",
            is_active=True
        )
        
        assert subject.name == "Physics"
        assert subject.code == "PHY"
        assert subject.level == "SCHOOL"
        assert subject.is_active is True
    
    def test_subject_unique_code(self, subject):
        """Test subject code must be unique."""
        with pytest.raises(IntegrityError):
            Subject.objects.create(
                name="Mathematics Duplicate",
                code="MATH",  # Duplicate
                level="SCHOOL"
            )
    
    def test_subject_tool_defaults(self, db):
        """Test subject has tool flags."""
        subject = Subject.objects.create(
            name="Chemistry",
            code="CHEM",
            level="UNIV"
        )
        
        # Check defaults
        assert subject.ppt_generator is True
        assert subject.flashcard_creator is True
        assert subject.quiz_generator is True
    
    def test_subject_stem_tools(self, db):
        """Test STEM-specific tools."""
        subject = Subject.objects.create(
            name="Mathematics",
            code="MATH2",
            level="SCHOOL",
            simulation=True,
            practice_problems=True,
            step_by_step_solver=True
        )
        
        assert subject.simulation is True
        assert subject.practice_problems is True
        assert subject.step_by_step_solver is True
    
    def test_subject_str_representation(self, subject):
        """Test __str__ method."""
        assert str(subject) == "Mathematics (MATH)"


# ============================================================================
# COURSE MODEL TESTS
# ============================================================================

@pytest.mark.unit
class TestCourseModel:
    """Test Course model."""
    
    def test_create_course(self, course):
        """Test creating a course."""
        assert course.title == "Mathematics Grade 5"
        assert course.code == "MATH5"
        assert course.slug == "mathematics-grade-5"
        assert course.subject.code == "MATH"
    
    def test_course_unique_code(self, course):
        """Test course code must be unique."""
        with pytest.raises(IntegrityError):
            Course.objects.create(
                subject=course.subject,
                title="Mathematics Grade 6",
                code="MATH5",  # Duplicate
                level="SCHOOL"
            )
    
    def test_course_slug_auto_generated(self, subject):
        """Test slug is auto-generated from title."""
        course = Course.objects.create(
            subject=subject,
            title="Advanced Calculus",
            code="CALC101",
            level="UNIV"
        )
        
        assert course.slug == "advanced-calculus"
    
    def test_course_with_credit_hours(self, subject_university):
        """Test university course with credit hours."""
        course = Course.objects.create(
            subject=subject_university,
            title="Algorithms",
            code="CS201",
            level="UNIV",
            credit_hours=4
        )
        
        assert course.credit_hours == 4
    
    def test_course_analysis_status(self, course):
        """Test syllabus analysis status tracking."""
        assert course.syllabus_analysis_status == "not_analyzed"
        
        course.syllabus_analysis_status = "analyzing"
        course.save()
        
        assert course.syllabus_analysis_status == "analyzing"


# ============================================================================
# COURSE PATH MODEL TESTS
# ============================================================================

@pytest.mark.unit
class TestCoursePathModel:
    """Test CoursePath model with 4 scopes."""
    
    def test_create_course_path(self, course_path):
        """Test creating course-scoped path."""
        assert course_path.scope == "course"
        assert course_path.label == "Week 1: Introduction to Algebra"
        assert course_path.slug == "week-1-intro-algebra"
        assert course_path.is_published is True
    
    def test_teacher_scoped_path(self, teacher_path, teacher_user):
        """Test teacher-scoped path."""
        assert teacher_path.scope == "teacher"
        assert teacher_path.teacher == teacher_user
        assert teacher_path.is_published is False
    
    def test_student_scoped_path(self, student_path, student_user):
        """Test student-scoped path."""
        assert student_path.scope == "student"
        assert student_path.student == student_user
    
    def test_offering_scoped_path(self, offering_path, course_offering):
        """Test offering-scoped path."""
        assert offering_path.scope == "offering"
        assert offering_path.offering == course_offering
    
    def test_path_slug_auto_generated(self, course):
        """Test slug auto-generation."""
        path = CoursePath.objects.create(
            course=course,
            scope="course",
            label="Week 2: Basic Geometry"
        )
        
        assert path.slug == "week-2-basic-geometry"
    
    def test_path_date_validation(self, course):
        """Test end date must be after start date."""
        with pytest.raises(ValidationError, match='after start date'):
            path = CoursePath(
                course=course,
                scope="course",
                label="Invalid Dates",
                start_date=datetime(2024, 9, 10).date(),
                end_date=datetime(2024, 9, 1).date()  # Before start
            )
            path.full_clean()
    
    def test_offering_path_date_within_term(self, course, course_offering):
        """Test offering path dates must be within term."""
        with pytest.raises(ValidationError):
            path = CoursePath(
                course=course,
                scope="offering",
                offering=course_offering,
                label="Invalid Term Dates",
                start_date=datetime(2024, 8, 1).date(),  # Before term
                end_date=datetime(2024, 9, 10).date()
            )
            path.full_clean()
    
    def test_teacher_scope_requires_teacher(self, course):
        """Test teacher-scoped path requires teacher field."""
        with pytest.raises(ValidationError, match='teacher is required'):
            path = CoursePath(
                course=course,
                scope="teacher",
                label="Missing Teacher",
                teacher=None  # Missing!
            )
            path.full_clean()
    
    def test_unique_course_path_per_course(self, course, course_path):
        """Test only one course-scoped path per course."""
        with pytest.raises((IntegrityError, ValidationError)):
            with transaction.atomic():
                CoursePath.objects.create(
                    course=course,
                    scope="course",
                    label="Duplicate Course Path"
                )

    
    def test_generation_status_tracking(self, course_path):
        """Test AI generation status."""
        assert course_path.generation_status == "not_generated"
        
        course_path.generation_status = "partial"
        course_path.save()
        
        assert course_path.generation_status == "partial"


# ============================================================================
# PATH MODULE TESTS
# ============================================================================

@pytest.mark.unit
class TestPathModuleModel:
    """Test PathModule model."""
    
    def test_create_module(self, module):
        """Test creating a module."""
        assert module.title == "Variables and Expressions"
        assert module.slug == "variables-expressions"
        assert module.category == "Algebra"
        assert module.is_published is True
    
    def test_module_slug_auto_generated(self, course_path):
        """Test module slug is auto-generated."""
        module = PathModule.objects.create(
            path=course_path,
            title="Solving Equations",
            category="Algebra",
            order=2
        )
        
        assert module.slug == "solving-equations"
    
    def test_unique_module_slug_per_path(self, module):
        """Test module slug must be unique per path."""
        with pytest.raises(IntegrityError):
            PathModule.objects.create(
                path=module.path,
                title="Different Title",
                slug="variables-expressions",  # Duplicate slug
                category="Algebra"
            )
    
    def test_unique_module_title_per_path(self, module):
        """Test module title must be unique per path."""
        with pytest.raises(IntegrityError):
            PathModule.objects.create(
                path=module.path,
                title="Variables and Expressions",  # Duplicate title
                category="Algebra"
            )
    
    def test_module_ordering(self, course_path):
        """Test modules are ordered."""
        module1 = PathModule.objects.create(
            path=course_path,
            title="Module 1",
            category="Algebra",
            order=1
        )
        module2 = PathModule.objects.create(
            path=course_path,
            title="Module 2",
            category="Algebra",
            order=2
        )
        
        modules = list(course_path.modules.all())
        assert modules[0] == module1
        assert modules[1] == module2


# ============================================================================
# MODULE DETAIL TESTS
# ============================================================================

@pytest.mark.unit
class TestModuleDetailModel:
    """Test ModuleDetail model."""
    
    def test_create_module_detail(self, module_detail):
        """Test creating module detail."""
        assert module_detail.content_type == "text"
        assert "Variables are symbols" in module_detail.text_content
        assert module_detail.is_ai_generated is False
    
    def test_module_detail_one_to_one(self, module, module_detail):
        """Test module can have only one detail."""
        with pytest.raises(IntegrityError):
            ModuleDetail.objects.create(
                module=module,
                content_type="text",
                text_content="Duplicate detail"
            )
    
    def test_module_detail_requires_content(self, module):
        """Test module detail requires at least one content type."""
        with pytest.raises(ValidationError, match='at least one content type'):
            detail = ModuleDetail(
                module=module,
                content_type="text",
                text_content="",  # Empty
                pdf_file=None  # No PDF
            )
            detail.full_clean()
    
    def test_ai_generated_flag(self, module_detail_ai):
        """Test AI-generated content flag."""
        assert module_detail_ai.is_ai_generated is True


# ============================================================================
# MODULE IMAGE TESTS
# ============================================================================

@pytest.mark.unit
class TestModuleImageModel:
    """Test ModuleImage model."""
    
    def test_create_module_image(self, module_image):
        """Test creating module image."""
        assert module_image.title == "Variable Diagram"
        assert module_image.alt_text == "Diagram showing variable x"
        assert module_image.order == 1
    
    def test_multiple_images_per_module(self, module):
        """Test module can have multiple images."""
        img1 = ModuleImage.objects.create(
            module=module,
            title="Image 1",
            image="module_images/img1.png",
            order=1
        )
        img2 = ModuleImage.objects.create(
            module=module,
            title="Image 2",
            image="module_images/img2.png",
            order=2
        )
        
        images = list(module.images.all())
        assert len(images) == 2
        assert images[0] == img1
        assert images[1] == img2


# ============================================================================
# RESOURCE TESTS
# ============================================================================

@pytest.mark.unit
class TestResourceModel:
    """Test Resource model."""
    
    def test_create_pdf_resource(self, resource_pdf):
        """Test creating PDF resource."""
        assert resource_pdf.type == "pdf"
        assert resource_pdf.file == "resources/variables_worksheet.pdf"
        assert resource_pdf.is_required is True
    
    def test_create_url_resource(self, resource_url):
        """Test creating URL resource."""
        assert resource_url.type == "url"
        assert "khanacademy.org" in resource_url.url
        assert resource_url.is_required is False
    
    def test_resource_file_required_for_file_types(self, module):
        """Test file is required for PDF/PPTX/DOCX."""
        with pytest.raises(ValidationError, match='File is required'):
            resource = Resource(
                module=module,
                type="pdf",
                title="Missing File",
                file=None  # Missing!
            )
            resource.full_clean()
    
    def test_resource_url_required_for_url_type(self, module):
        """Test URL is required for URL type."""
        with pytest.raises(ValidationError, match='URL is required'):
            resource = Resource(
                module=module,
                type="url",
                title="Missing URL",
                url=None  # Missing!
            )
            resource.full_clean()
    
    def test_resource_ordering(self, module):
        """Test resources are ordered."""
        r1 = Resource.objects.create(
            module=module,
            type="url",
            title="Resource 1",
            url="https://example.com/1",
            order=1
        )
        r2 = Resource.objects.create(
            module=module,
            type="url",
            title="Resource 2",
            url="https://example.com/2",
            order=2
        )
        
        resources = list(module.resources.all())
        assert resources[0] == r1
        assert resources[1] == r2


# ============================================================================
# MODULE PACKAGE TESTS
# ============================================================================

@pytest.mark.unit
class TestModulePackageModel:
    """Test ModulePackage model."""
    
    def test_create_module_package(self, module_package):
        """Test creating module package."""
        assert module_package.title == "Introduction Package"
        assert module_package.description == "Basic concepts package"
    
    def test_multiple_packages_per_module(self, module):
        """Test module can have multiple packages."""
        pkg1 = ModulePackage.objects.create(
            module=module,
            title="Package 1",
            order=1
        )
        pkg2 = ModulePackage.objects.create(
            module=module,
            title="Package 2",
            order=2
        )
        
        packages = list(module.packages.all())
        assert len(packages) == 2


# ============================================================================
# MODULE TOOL OVERRIDE TESTS
# ============================================================================

@pytest.mark.unit
class TestModuleToolOverrideModel:
    """Test ModuleToolOverride model."""
    
    def test_create_tool_override(self, tool_override):
        """Test creating tool override."""
        assert tool_override.ppt_generator is False
        assert tool_override.flashcard_creator is True
        assert tool_override.quiz_student_visible is False
    
    def test_tool_override_one_to_one(self, module, tool_override):
        """Test module can have only one tool override."""
        with pytest.raises(IntegrityError):
            ModuleToolOverride.objects.create(
                module=module,
                ppt_generator=True
            )
    
    def test_null_means_use_subject_default(self, module):
        """Test None values use subject defaults."""
        override = ModuleToolOverride.objects.create(
            module=module,
            ppt_generator=None,  # Use subject default
            flashcard_creator=False  # Override
        )
        
        assert override.ppt_generator is None
        assert override.flashcard_creator is False