from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from schools.models import School, Subject, MasterStudent


class ExamFolder(models.Model):
    """Folder for organizing ZipGrade exams."""
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='exam_folders',
        verbose_name=_('School')
    )
    name = models.CharField(max_length=200, verbose_name=_('Folder Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subfolders',
        verbose_name=_('Parent Folder')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Exam Folder')
        verbose_name_plural = _('Exam Folders')
        ordering = ['name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} / {self.name}"
        return self.name
    
    @property
    def exam_count(self):
        return self.exams.count()


class ZipGradeExam(models.Model):
    """Represents a ZipGrade exam upload session."""
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='zipgrade_exams',
        verbose_name=_('School')
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_exams',
        verbose_name=_('Uploaded By')
    )
    
    title = models.CharField(max_length=200, verbose_name=_('Exam Title'))
    original_filename = models.CharField(max_length=255, verbose_name=_('Original Filename'))
    exam_date = models.DateField(verbose_name=_('Exam Date'))
    
    # ZipGrade metadata
    total_questions = models.PositiveIntegerField(default=0, verbose_name=_('Total Questions'))
    total_students = models.PositiveIntegerField(default=0, verbose_name=_('Total Students'))
    unknown_students = models.PositiveIntegerField(default=0, verbose_name=_('Unknown Students'))
    
    # Optional folder organization
    folder = models.ForeignKey(
        ExamFolder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='exams',
        verbose_name=_('Folder')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('ZipGrade Exam')
        verbose_name_plural = _('ZipGrade Exams')
        ordering = ['-exam_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.school.name} ({self.exam_date})"
    
    @property
    def average_score(self):
        """Calculate average score across all results."""
        results = self.results.all()
        if not results.exists():
            return 0
        total = sum(r.percentage for r in results)
        return round(total / results.count(), 1)


class SubjectSplit(models.Model):
    """Defines how questions are split by subject in a ZipGrade exam."""
    
    exam = models.ForeignKey(
        ZipGradeExam,
        on_delete=models.CASCADE,
        related_name='subject_splits',
        verbose_name=_('Exam')
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exam_splits',
        verbose_name=_('Subject')
    )
    
    # Question range (1-indexed, inclusive)
    start_question = models.PositiveIntegerField(verbose_name=_('Start Question'))
    end_question = models.PositiveIntegerField(verbose_name=_('End Question'))
    
    # Points per question (default 1)
    points_per_question = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name=_('Points per Question')
    )
    
    class Meta:
        verbose_name = _('Subject Split')
        verbose_name_plural = _('Subject Splits')
        ordering = ['start_question']
        unique_together = ['exam', 'subject']
    
    def __str__(self):
        return f"{self.subject.name}: Q{self.start_question}-Q{self.end_question}"
    
    @property
    def question_count(self):
        return self.end_question - self.start_question + 1
    
    @property
    def max_points(self):
        return self.question_count * float(self.points_per_question)


class ExamResult(models.Model):
    """Individual student result for a ZipGrade exam."""
    
    exam = models.ForeignKey(
        ZipGradeExam,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('Exam')
    )
    
    # Student link (may be None for unknown students)
    student = models.ForeignKey(
        MasterStudent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exam_results',
        verbose_name=_('Student')
    )
    
    # ZipGrade data
    zipgrade_student_id = models.CharField(max_length=50, verbose_name=_('ZipGrade Student ID'))
    zipgrade_first_name = models.CharField(max_length=100, blank=True, verbose_name=_('First Name (ZipGrade)'))
    zipgrade_last_name = models.CharField(max_length=100, blank=True, verbose_name=_('Last Name (ZipGrade)'))
    
    # Scores
    earned_points = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_('Earned Points'))
    max_points = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_('Max Points'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Percentage'))
    
    # Answer data (JSON string of answers)
    answers = models.TextField(blank=True, verbose_name=_('Answers (JSON)'))
    
    # Unknown student flag
    is_unknown = models.BooleanField(default=False, verbose_name=_('Unknown Student'))
    
    # Manual name entry for unknown students
    manual_first_name = models.CharField(max_length=100, blank=True, verbose_name=_('Manual First Name'))
    manual_last_name = models.CharField(max_length=100, blank=True, verbose_name=_('Manual Last Name'))
    manual_class_name = models.CharField(max_length=50, blank=True, verbose_name=_('Manual Class Name'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Exam Result')
        verbose_name_plural = _('Exam Results')
        ordering = ['-percentage']
        unique_together = ['exam', 'zipgrade_student_id']
    
    def __str__(self):
        if self.student:
            return f"{self.student.full_name} - {self.percentage}%"
        return f"Unknown ({self.zipgrade_student_id}) - {self.percentage}%"
    
    @property
    def display_name(self):
        # Priority: linked student > manual name > zipgrade name > unknown
        if self.student:
            return self.student.full_name
        if self.manual_first_name or self.manual_last_name:
            return f"{self.manual_last_name} {self.manual_first_name}".strip()
        if self.zipgrade_first_name or self.zipgrade_last_name:
            return f"{self.zipgrade_last_name} {self.zipgrade_first_name}".strip()
        return f"Unknown ({self.zipgrade_student_id})"


class SubjectResult(models.Model):
    """Subject-specific score for a student (when subject splits are defined)."""
    
    result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name='subject_results',
        verbose_name=_('Result')
    )
    subject_split = models.ForeignKey(
        SubjectSplit,
        on_delete=models.CASCADE,
        related_name='student_results',
        verbose_name=_('Subject Split')
    )
    
    earned_points = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_('Earned Points'))
    max_points = models.DecimalField(max_digits=7, decimal_places=2, verbose_name=_('Max Points'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Percentage'))
    
    # Correct/incorrect per question (JSON)
    question_results = models.TextField(blank=True, verbose_name=_('Question Results (JSON)'))
    
    class Meta:
        verbose_name = _('Subject Result')
        verbose_name_plural = _('Subject Results')
        unique_together = ['result', 'subject_split']
    
    def __str__(self):
        return f"{self.result.display_name} - {self.subject_split.subject.name}: {self.percentage}%"
