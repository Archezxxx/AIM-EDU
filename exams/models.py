from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class OnlineExam(models.Model):
    """
    Online exam created by teachers.
    """
    
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    subject = models.ForeignKey(
        'schools.Subject',
        on_delete=models.CASCADE,
        related_name='online_exams',
        verbose_name=_('Subject')
    )
    
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='online_exams',
        verbose_name=_('School')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_exams',
        verbose_name=_('Created By')
    )
    
    # Exam settings
    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name=_('Duration (minutes)')
    )
    passing_score = models.PositiveIntegerField(
        default=60,
        verbose_name=_('Passing Score (%)')
    )
    
    # Availability window
    start_time = models.DateTimeField(verbose_name=_('Start Time'))
    end_time = models.DateTimeField(verbose_name=_('End Time'))
    
    # Options
    shuffle_questions = models.BooleanField(
        default=False,
        verbose_name=_('Shuffle Questions')
    )
    shuffle_options = models.BooleanField(
        default=False,
        verbose_name=_('Shuffle Options')
    )
    show_results_immediately = models.BooleanField(
        default=False,
        verbose_name=_('Show Results Immediately')
    )
    
    # Proctoring settings
    max_tab_switches = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Max Tab Switches Before Lock')
    )
    
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Online Exam')
        verbose_name_plural = _('Online Exams')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.subject.name}"
    
    @property
    def is_available(self):
        """Check if exam is currently available."""
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time
    
    @property
    def total_questions(self):
        return self.questions.count()
    
    @property
    def total_points(self):
        return self.questions.aggregate(total=models.Sum('points'))['total'] or 0


class ExamQuestion(models.Model):
    """
    Question for an online exam.
    """
    
    QUESTION_TYPES = [
        ('multiple_choice', _('Multiple Choice')),
        ('fill_blanks', _('Fill in the Blanks')),
    ]
    
    exam = models.ForeignKey(
        OnlineExam,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Exam')
    )
    
    question_text = models.TextField(verbose_name=_('Question'))
    question_image = models.ImageField(
        upload_to='exam_questions/',
        blank=True,
        null=True,
        verbose_name=_('Question Image')
    )
    
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='multiple_choice',
        verbose_name=_('Question Type')
    )
    
    points = models.PositiveIntegerField(default=1, verbose_name=_('Points'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    # For fill_blanks: store multiple correct answers separated by | (pipe)
    # Example: "answer1|Answer2|ANSWER3" - case-insensitive comparison
    correct_answers = models.TextField(
        blank=True,
        verbose_name=_('Correct Answers'),
        help_text=_('For fill-in-the-blanks: separate multiple correct variants with | (pipe)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Exam Question')
        verbose_name_plural = _('Exam Questions')
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class QuestionOption(models.Model):
    """
    Answer option for a question.
    """
    
    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('Question')
    )
    
    text = models.CharField(max_length=500, verbose_name=_('Option Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Correct Answer'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    
    class Meta:
        verbose_name = _('Question Option')
        verbose_name_plural = _('Question Options')
        ordering = ['order', 'id']
    
    def __str__(self):
        return self.text[:50]


class ExamAttempt(models.Model):
    """
    Student's attempt at an exam.
    """
    
    STATUS_CHOICES = [
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('locked', _('Locked')),
        ('timed_out', _('Timed Out')),
    ]
    
    exam = models.ForeignKey(
        OnlineExam,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Exam')
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attempts',
        verbose_name=_('Student')
    )
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Finished At'))
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name=_('Status')
    )
    
    # Proctoring
    tab_switch_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Tab Switch Count')
    )
    is_locked = models.BooleanField(default=False, verbose_name=_('Locked'))
    lock_reason = models.CharField(max_length=200, blank=True, verbose_name=_('Lock Reason'))
    
    # Results
    score = models.PositiveIntegerField(default=0, verbose_name=_('Score'))
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('Percentage')
    )
    
    class Meta:
        verbose_name = _('Exam Attempt')
        verbose_name_plural = _('Exam Attempts')
        ordering = ['-started_at']
        unique_together = ['exam', 'student']  # One attempt per student per exam
    
    def __str__(self):
        return f"{self.student} - {self.exam.title}"
    
    @property
    def time_remaining(self):
        """Calculate remaining time in seconds."""
        if self.status != 'in_progress':
            return 0
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = (self.exam.duration_minutes * 60) - elapsed
        return max(0, int(remaining))
    
    @property
    def is_passed(self):
        return self.percentage >= self.exam.passing_score
    
    def calculate_score(self):
        """Calculate and save the score."""
        correct_answers = self.answers.filter(is_correct=True)
        self.score = sum(a.question.points for a in correct_answers)
        total_points = self.exam.total_points
        if total_points > 0:
            self.percentage = (self.score / total_points) * 100
        else:
            self.percentage = 0
        self.save()


class AttemptAnswer(models.Model):
    """
    Individual answer in an exam attempt.
    """
    
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Attempt')
    )
    
    question = models.ForeignKey(
        ExamQuestion,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
        verbose_name=_('Question')
    )
    
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='selections',
        verbose_name=_('Selected Option')
    )
    
    # For fill_blanks questions
    text_answer = models.TextField(blank=True, verbose_name=_('Text Answer'))
    
    is_correct = models.BooleanField(default=False, verbose_name=_('Correct'))
    answered_at = models.DateTimeField(auto_now=True, verbose_name=_('Answered At'))
    
    class Meta:
        verbose_name = _('Attempt Answer')
        verbose_name_plural = _('Attempt Answers')
        unique_together = ['attempt', 'question']
    
    def save(self, *args, **kwargs):
        # Auto-check if answer is correct
        if self.question.question_type == 'fill_blanks':
            # Check text answer against correct_answers field
            if self.text_answer and self.question.correct_answers:
                correct_variants = [
                    v.strip().lower() 
                    for v in self.question.correct_answers.split('|')
                ]
                self.is_correct = self.text_answer.strip().lower() in correct_variants
            else:
                self.is_correct = False
        elif self.selected_option:
            self.is_correct = self.selected_option.is_correct
        else:
            self.is_correct = False
        super().save(*args, **kwargs)


class ProctorEvent(models.Model):
    """
    Log of proctoring events/violations.
    """
    
    EVENT_TYPES = [
        ('tab_switch', _('Tab Switch')),
        ('window_blur', _('Window Blur')),
        ('copy_attempt', _('Copy Attempt')),
        ('paste_attempt', _('Paste Attempt')),
        ('right_click', _('Right Click')),
        ('exam_locked', _('Exam Locked')),
        ('admin_unlock', _('Admin Unlock')),
        ('exam_started', _('Exam Started')),
        ('exam_submitted', _('Exam Submitted')),
    ]
    
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='proctor_events',
        verbose_name=_('Attempt')
    )
    
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPES,
        verbose_name=_('Event Type')
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_('Timestamp'))
    details = models.JSONField(default=dict, blank=True, verbose_name=_('Details'))
    
    class Meta:
        verbose_name = _('Proctor Event')
        verbose_name_plural = _('Proctor Events')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.attempt.student} - {self.event_type} at {self.timestamp}"
