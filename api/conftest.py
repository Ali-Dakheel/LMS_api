"""
Enhanced conftest.py - Academic model fixtures

Add to your existing conftest.py in apps/academics/tests/

Provides complete academic setup:
- AcademicYear with current year
- Program with auto-generated terms
- Subject, Course, CurriculumMap
- Cohort, ClassSection, CourseOffering
- Student and teacher users with proper program enrollment
- All relationships properly initialized

Key fixes:
- Uses User.objects.create_user() with correct fields (no 'username')
- Creates all required relationships before creating ClassSection
- Properly initializes StudentProgram for university students
- Handles both K-12 and University contexts
"""

import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

# Import academic models
from apps.academics.models import (
    AcademicYear,
    Program,
    Term,
    Cohort,
    ClassSection,
    CourseOffering,
    Enrollment,
    OfferingTeacher,
    StudentProgram,
    StudentSection,
    TeacherProgram,
    TeacherTerm,
    CurriculumMap,
    PrerequisiteChain,
    DeanProgramAssignment,
    StudentEligibility,
    EnrollmentWaitlist,
    ClassSession,
    Attendance,
    TeacherSubject,
    StudentSubject,
)

# Import course models
from apps.courses.models import Subject, Course

User = get_user_model()


# ============================================================================
# ACADEMIC STRUCTURE FIXTURES
# ============================================================================

@pytest.fixture
def academic_year():
    """Create current academic year (2024-2025)."""
    # Clean up any existing current years
    AcademicYear.objects.filter(is_current=True).update(is_current=False)
    
    return AcademicYear.objects.create(
        name="2024-2025",
        start_date=datetime(2024, 9, 1).date(),
        end_date=datetime(2025, 8, 31).date(),
        is_current=True
    )


@pytest.fixture
def program(academic_year):
    """Create 4-year CS program with 2 semesters/year."""
    program = Program.objects.create(
        name="Computer Science",
        code="CS",
        level="UG",
        duration_years=4,
        terms_per_year=2,
        faculty="Engineering",
        is_active=True
    )
    # Signal auto-generates 8 terms
    return program


@pytest.fixture
def program_terms(program):
    """Get all auto-generated program terms."""
    return program.terms.all().order_by('number')


@pytest.fixture
def term_sem1(program):
    """Get Semester 1 of program."""
    return program.terms.get(number=1)


@pytest.fixture
def term_sem2(program):
    """Get Semester 2 of program."""
    return program.terms.get(number=2)


@pytest.fixture
def cohort(program):
    """Create student cohort (CS 2024 entry)."""
    return Cohort.objects.create(
        program=program,
        entry_year=2024,
        name="CS 2024 Cohort",
        is_active=True
    )


@pytest.fixture
def subject():
    """Create test subject."""
    return Subject.objects.create(
        name="Data Structures",
        code="CS101",
        level="UNIV",
        description="Fundamental data structure algorithms"
    )


@pytest.fixture
def subject_advanced(subject):
    """Create advanced subject that depends on basic subject."""
    return Subject.objects.create(
        name="Advanced Algorithms",
        code="CS301",
        level="UNIV",
        description="Advanced algorithmic techniques"
    )


@pytest.fixture
def course(subject):
    """Create course from subject."""
    return Course.objects.create(
        title="Data Structures 101",
        slug="data-structures-101",
        code="CS101",
        subject=subject,
        level="UNIV",
        description="Learn fundamental data structures",
        is_active=True
    )


@pytest.fixture
def course_advanced(subject_advanced):
    """Create advanced course."""
    return Course.objects.create(
        title="Advanced Algorithms",
        slug="advanced-algorithms",
        code="CS301",
        subject=subject_advanced,
        level="UNIV",
        is_active=True
    )


@pytest.fixture
def class_section_university(term_sem1, cohort):
    """Create university class section (CS-2024-A)."""
    return ClassSection.objects.create(
        term=term_sem1,
        cohort=cohort,
        section="A",
        name="CS-2024-A",
        capacity=30,
        is_active=True
    )


@pytest.fixture
def class_section_k12(academic_year):
    """Create K-12 class section (Grade 5-B)."""
    grade_term = Term.objects.create(
        academic_year=academic_year,
        type="GRADE",
        number=5,
        name="Grade 5",
        start_date=datetime(2024, 9, 1).date(),
        end_date=datetime(2025, 8, 31).date(),
        is_current=True
    )
    
    return ClassSection.objects.create(
        term=grade_term,
        section="B",
        name="Grade 5-B",
        capacity=25,
        is_active=True
    )


@pytest.fixture
def course_offering(course, term_sem1, class_section_university):
    """Create course offering (CS101 for CS-2024-A in Sem 1)."""
    return CourseOffering.objects.create(
        course=course,
        term=term_sem1,
        class_section=class_section_university,
        auto_enroll="section",
        capacity=30,
        is_active=True
    )


@pytest.fixture
def course_offering_k12(course, term_sem1, class_section_k12):
    """Create K-12 course offering."""
    return CourseOffering.objects.create(
        course=course,
        term=term_sem1,
        class_section=class_section_k12,
        auto_enroll="none",
        is_active=True
    )


@pytest.fixture
def curriculum_map(program, term_sem1, subject):
    """Map subject to program term (mandatory)."""
    return CurriculumMap.objects.create(
        program=program,
        term=term_sem1,
        subject=subject,
        is_mandatory=True,
        credits=3,
        sequence_order=1
    )


@pytest.fixture
def curriculum_map_elective(program, term_sem1, subject_advanced):
    """Map elective subject to program term."""
    return CurriculumMap.objects.create(
        program=program,
        term=term_sem1,
        subject=subject_advanced,
        is_mandatory=False,
        credits=3,
        sequence_order=2
    )


@pytest.fixture
def prerequisite_chain(subject, subject_advanced):
    """Create prerequisite: Advanced requires Basic."""
    return PrerequisiteChain.objects.create(
        subject=subject_advanced,
        prerequisite_subject=subject,
        min_grade="C",
        is_corequisite=False
    )


# ============================================================================
# USER FIXTURES - CRITICAL: Use correct User model fields
# ============================================================================

@pytest.fixture
def student_user(db, cohort):
    """
    Create student user enrolled in program cohort.
    
    FIXED: Uses email-based User model, NOT username
    """
    student = User.objects.create_user(
        email="student@example.com",
        name="John Student",
        password="SecurePass123!",
        role="student",
        is_active=True
    )
    
    # Enroll in program
    StudentProgram.objects.create(
        student=student,
        program=cohort.program,
        cohort=cohort,
        status="active",
        enrollment_date=datetime(2024, 9, 1).date(),
        expected_graduation_date=datetime(2028, 8, 31).date()
    )
    
    return student


@pytest.fixture
def student_user_2(db, cohort):
    """Create second student for batch tests."""
    student = User.objects.create_user(
        email="student2@example.com",
        name="Jane Student",
        password="SecurePass123!",
        role="student",
        is_active=True
    )
    
    StudentProgram.objects.create(
        student=student,
        program=cohort.program,
        cohort=cohort,
        status="active"
    )
    
    return student


@pytest.fixture
def student_inactive(db, cohort):
    """Create inactive student for testing."""
    student = User.objects.create_user(
        email="inactive@example.com",
        name="Inactive Student",
        password="SecurePass123!",
        role="student",
        is_active=False  # Inactive!
    )
    
    StudentProgram.objects.create(
        student=student,
        program=cohort.program,
        cohort=cohort,
        status="active"
    )
    
    return student


@pytest.fixture
def student_suspended(db, cohort):
    """Create suspended student for testing."""
    student = User.objects.create_user(
        email="suspended@example.com",
        name="Suspended Student",
        password="SecurePass123!",
        role="student",
        is_active=True
    )
    
    StudentProgram.objects.create(
        student=student,
        program=cohort.program,
        cohort=cohort,
        status="suspended"  # Suspended!
    )
    
    return student


@pytest.fixture
def multiple_students(db, cohort):
    """Create 5 students for bulk testing."""
    students = []
    for i in range(5):
        student = User.objects.create_user(
            email=f"student{i}@example.com",
            name=f"Student {i}",
            password="SecurePass123!",
            role="student",
            is_active=True
        )
        
        StudentProgram.objects.create(
            student=student,
            program=cohort.program,
            cohort=cohort,
            status="active"
        )
        
        students.append(student)
    
    return students


@pytest.fixture
def teacher_user(db, program, term_sem1):
    """
    Create teacher user assigned to program and term.
    
    FIXED: Proper email-based User model
    """
    teacher = User.objects.create_user(
        email="teacher@example.com",
        name="Dr. Smith",
        password="SecurePass123!",
        role="teacher",
        is_active=True
    )
    
    # Assign to program
    TeacherProgram.objects.create(
        teacher=teacher,
        program=program,
        is_active=True
    )
    
    # Assign to term
    TeacherTerm.objects.create(
        teacher=teacher,
        term=term_sem1,
        is_active=True
    )
    
    return teacher


@pytest.fixture
def teacher_user_2(db, program, term_sem1):
    """Create second teacher for tests."""
    teacher = User.objects.create_user(
        email="teacher2@example.com",
        name="Prof. Johnson",
        password="SecurePass123!",
        role="teacher",
        is_active=True
    )
    
    TeacherProgram.objects.create(teacher=teacher, program=program, is_active=True)
    TeacherTerm.objects.create(teacher=teacher, term=term_sem1, is_active=True)
    
    return teacher


@pytest.fixture
def dean_user(db, program):
    """Create dean user with program access."""
    dean = User.objects.create_user(
        email="dean@example.com",
        name="Dean Williams",
        password="SecurePass123!",
        role="dean",
        is_active=True
    )
    
    # Assign to program
    DeanProgramAssignment.objects.create(
        dean=dean,
        program=program,
        is_active=True
    )
    
    return dean


@pytest.fixture
def admin_user(db):
    """Create admin/superuser."""
    return User.objects.create_superuser(
        email="admin@example.com",
        name="Admin User",
        password="SecurePass123!"
    )


# ============================================================================
# ENROLLMENT & RELATIONSHIP FIXTURES
# ============================================================================

@pytest.fixture
def enrollment(student_user, course_offering):
    """Create active enrollment."""
    return Enrollment.objects.create(
        student=student_user,
        offering=course_offering,
        status="active"
    )


@pytest.fixture
def enrollment_completed(student_user_2, course_offering):
    """Create completed enrollment."""
    return Enrollment.objects.create(
        student=student_user_2,
        offering=course_offering,
        status="completed",
        completed_at=timezone.now()
    )


@pytest.fixture
def offering_teacher(course_offering, teacher_user):
    """Create primary teacher assignment."""
    return OfferingTeacher.objects.create(
        offering=course_offering,
        teacher=teacher_user,
        is_primary=True
    )


@pytest.fixture
def offering_teacher_secondary(course_offering, teacher_user_2):
    """Create secondary teacher assignment."""
    return OfferingTeacher.objects.create(
        offering=course_offering,
        teacher=teacher_user_2,
        is_primary=False
    )


@pytest.fixture
def student_in_section(student_user, class_section_university):
    """Add student to class section (K-12 style)."""
    return StudentSection.objects.create(
        student=student_user,
        class_section=class_section_university
    )


# ============================================================================
# CLASS SESSION & ATTENDANCE FIXTURES
# ============================================================================

@pytest.fixture
def class_session(course_offering):
    """Create class session."""
    return ClassSession.objects.create(
        offering=course_offering,
        session_date=datetime(2024, 9, 5).date(),
        start_time="09:00:00",
        end_time="10:30:00",
        topic="Introduction to Data Structures"
    )


@pytest.fixture
def class_session_2(course_offering):
    """Create second class session."""
    return ClassSession.objects.create(
        offering=course_offering,
        session_date=datetime(2024, 9, 7).date(),
        start_time="09:00:00",
        end_time="10:30:00",
        topic="Arrays and Lists"
    )


@pytest.fixture
def attendance_present(student_user, class_session):
    """Create present attendance."""
    return Attendance.objects.create(
        student=student_user,
        class_session=class_session,
        status="present"
    )


@pytest.fixture
def attendance_absent(student_user_2, class_session):
    """Create absent attendance."""
    return Attendance.objects.create(
        student=student_user_2,
        class_session=class_session,
        status="absent"
    )


# ============================================================================
# ELIGIBILITY & WAITLIST FIXTURES
# ============================================================================

@pytest.fixture
def student_eligibility_eligible(student_user, course):
    """Create eligible eligibility record."""
    return StudentEligibility.objects.create(
        student=student_user,
        course=course,
        status="eligible",
        reason="Prerequisites met"
    )


@pytest.fixture
def student_eligibility_not_eligible(student_user_2, course_advanced):
    """Create not eligible record."""
    return StudentEligibility.objects.create(
        student=student_user_2,
        course=course_advanced,
        status="not_eligible",
        reason="Missing prerequisite: Data Structures"
    )


@pytest.fixture
def enrollment_waitlist(student_user, course_offering):
    """Add student to enrollment waitlist."""
    return EnrollmentWaitlist.objects.create(
        student=student_user,
        offering=course_offering,
        position=1
    )


# ============================================================================
# COMBINED FIXTURE SUITES (for complex scenarios)
# ============================================================================

@pytest.fixture
def university_setup(
    academic_year,
    program,
    cohort,
    term_sem1,
    subject,
    course,
    class_section_university,
    course_offering,
    student_user,
    teacher_user,
    dean_user
):
    """
    Complete university setup with all relationships.
    
    Returns dict with all fixtures for convenience.
    """
    return {
        'academic_year': academic_year,
        'program': program,
        'cohort': cohort,
        'term': term_sem1,
        'subject': subject,
        'course': course,
        'section': class_section_university,
        'offering': course_offering,
        'student': student_user,
        'teacher': teacher_user,
        'dean': dean_user,
    }


@pytest.fixture
def k12_setup(
    academic_year,
    class_section_k12,
    course,
    student_user,
    teacher_user
):
    """Complete K-12 setup."""
    return {
        'academic_year': academic_year,
        'section': class_section_k12,
        'course': course,
        'student': student_user,
        'teacher': teacher_user,
    }


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

@pytest.fixture(autouse=True)
def reset_sequences(db):
    """Reset database sequences between tests to ensure clean state."""
    yield
    # Cleanup happens automatically with pytest-django