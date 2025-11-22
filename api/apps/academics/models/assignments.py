"""
Assignment Models - K-12 Focus

Relationship assignments:
- TeacherSubject: Teacher-subject assignments
- TeacherTerm: Teacher-grade assignments
- StudentSection: K-12 section assignments
- StudentSubject: Student-subject assignments
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .structure import Term, ClassSection

User = get_user_model()


# ============================================================================
# TEACHER ASSIGNMENTS
# ============================================================================

class TeacherSubject(models.Model):
    """
    Represents which subjects a teacher teaches in K-12.

    Allows:
    - Teachers assigned to multiple subjects
    - Filtering eligible teachers for courses
    - Tracking teacher qualifications

    Example:
    - Teacher "Ms. Smith" teaches Math
    - Teacher "Mr. Johnson" teaches Science and English
    """

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subject_assignments',
        limit_choices_to={'role': 'teacher'},
        db_index=True,
        help_text="Teacher assigned to this subject"
    )
    subject = models.ForeignKey(
        'courses.Subject',
        on_delete=models.CASCADE,
        related_name='teachers',
        db_index=True,
        help_text="Subject the teacher is qualified to teach"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_subjects'
        verbose_name = 'Teacher Subject Assignment'
        verbose_name_plural = 'Teacher Subject Assignments'
        unique_together = ['teacher', 'subject']
        ordering = ['teacher__name', 'subject__name']
        indexes = [
            models.Index(fields=['teacher']),
            models.Index(fields=['subject']),
        ]

    def __str__(self):
        return f"{self.teacher.name} → {self.subject.name}"

    def clean(self):
        """Validate teacher role."""
        errors = {}

        # Validate teacher role
        if self.teacher_id:
            if hasattr(self, 'teacher'):
                teacher = self.teacher
            else:
                try:
                    teacher = User.objects.get(pk=self.teacher_id)
                except User.DoesNotExist:
                    errors['teacher'] = _('Teacher does not exist')
                    raise ValidationError(errors)

            if teacher.role != 'teacher':
                errors['teacher'] = _('User must have teacher role')

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Ensure validation runs before save."""
        self.full_clean()
        super().save(*args, **kwargs)


class TeacherTerm(models.Model):
    """
    Represents which grade levels a teacher teaches.

    Allows fine-grained control:
    - Teacher A teaches Grade 5
    - Teacher B teaches Grade 10 and Grade 11
    - Useful for substitutes and part-time teachers

    Example:
    - Ms. Smith teaches Grade 5
    - Mr. Johnson teaches Grade 10
    """

    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='term_assignments',
        limit_choices_to={'role': 'teacher'},
        db_index=True,
        help_text="Teacher assigned to this grade"
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='teachers',
        db_index=True,
        help_text="Grade level (1-12)"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Mark assignment as active/inactive"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teacher_terms'
        verbose_name = 'Teacher Grade Assignment'
        verbose_name_plural = 'Teacher Grade Assignments'
        unique_together = ['teacher', 'term']
        ordering = ['term__number', 'teacher__name']
        indexes = [
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['term', 'is_active']),
        ]

    def __str__(self):
        return f"{self.teacher.name} → {self.term.name}"


# ============================================================================
# STUDENT ASSIGNMENTS
# ============================================================================

class StudentSection(models.Model):
    """
    Links students to class sections (K-12 homeroom assignment).

    This represents homeroom assignment (permanent for the grade/term),
    separate from course enrollments (variable).

    Example:
    - Student "John Smith" is in Grade 5-A (homeroom)
    - Student "Mary Johnson" is in Grade 10-B (homeroom)

    Business Rules:
    - K-12 only
    - Represents homeroom/primary section
    - Different from course-specific enrollments
    - Students can only be in one section per grade
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='section_assignments',
        limit_choices_to={'role': 'student'},
        db_index=True,
        help_text="Student assigned to this section"
    )
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.CASCADE,
        related_name='students',
        db_index=True,
        help_text="Class section (homeroom)"
    )

    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_sections'
        verbose_name = 'Student Section Assignment'
        verbose_name_plural = 'Student Section Assignments'
        unique_together = ['student', 'class_section']
        ordering = ['class_section__name', 'student__name']
        indexes = [
            models.Index(fields=['class_section']),
            models.Index(fields=['student']),
        ]

    def __str__(self):
        return f"{self.student.name} → {self.class_section.name}"


class StudentSubject(models.Model):
    """
    Represents which subjects a K-12 student studies.

    K-12 context:
    - Students in a grade study specific subjects
    - Can track electives or specializations
    - Links students to subjects they take

    Example:
    - Student "John Smith" studies Math, Science, English in Grade 5
    - Student "Mary Johnson" studies Math, Physics, Chemistry in Grade 10

    Business Rules:
    - Students can be enrolled in multiple subjects
    - Unique per student, subject, and term (grade)
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subject_enrollments',
        limit_choices_to={'role': 'student'},
        db_index=True,
        help_text="Student enrolled in this subject"
    )
    subject = models.ForeignKey(
        'courses.Subject',
        on_delete=models.CASCADE,
        related_name='students',
        db_index=True,
        help_text="Subject the student studies"
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        db_index=True,
        help_text="Grade level for this subject (optional)"
    )

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Mark assignment as active/inactive"
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_subjects'
        verbose_name = 'Student Subject Assignment'
        verbose_name_plural = 'Student Subject Assignments'
        unique_together = ['student', 'subject', 'term']
        ordering = ['term__number', 'student__name']
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['subject', 'is_active']),
        ]

    def __str__(self):
        term_str = f" ({self.term.name})" if self.term else ""
        return f"{self.student.name} → {self.subject.name}{term_str}"