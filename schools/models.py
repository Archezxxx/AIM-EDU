from django.db import models
from django.utils.translation import gettext_lazy as _


class School(models.Model):
    """
    School model for the AIMS network.
    Uses soft delete (is_active) to preserve historical data.
    """
    
    name = models.CharField(max_length=200, verbose_name=_('School Name'))
    code = models.CharField(max_length=50, unique=True, verbose_name=_('School Code'))
    address = models.TextField(blank=True, verbose_name=_('Address'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    logo = models.ImageField(
        upload_to='school_logos/',
        blank=True,
        null=True,
        verbose_name=_('School Logo')
    )
    
    # Soft delete for data persistence
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('School')
        verbose_name_plural = _('Schools')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject/Course model linked to schools."""
    
    name = models.CharField(max_length=100, verbose_name=_('Subject Name'))
    code = models.CharField(max_length=20, blank=True, verbose_name=_('Subject Code'))
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects',
        verbose_name=_('School')
    )
    
    # Soft delete
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subject')
        verbose_name_plural = _('Subjects')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MasterStudent(models.Model):
    """
    Master student list uploaded by admin.
    Separate list per school for ID matching with ZipGrade.
    """
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='master_students',
        verbose_name=_('School')
    )
    
    # Original ID (preserves leading zeros as string)
    student_id = models.CharField(max_length=20, verbose_name=_('Student ID'))
    # Normalized ID for matching (integer converted to string, no leading zeros)
    student_id_normalized = models.CharField(max_length=20, db_index=True, verbose_name=_('Normalized ID'))
    
    # Student info
    name = models.CharField(max_length=100, verbose_name=_('First Name'))
    surname = models.CharField(max_length=100, verbose_name=_('Last Name'))
    grade = models.CharField(max_length=10, verbose_name=_('Grade'))
    section = models.CharField(max_length=10, verbose_name=_('Section'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Master Student')
        verbose_name_plural = _('Master Students')
        ordering = ['grade', 'section', 'surname', 'name']
        unique_together = ['school', 'student_id']
    
    def save(self, *args, **kwargs):
        # Normalize the student ID for matching
        self.student_id_normalized = self.normalize_id(self.student_id)
        super().save(*args, **kwargs)
    
    @staticmethod
    def normalize_id(raw_id):
        """
        Normalize student ID by removing leading zeros.
        Handles both string and integer inputs.
        Example: '01251001' -> '1251001'
        """
        try:
            return str(int(str(raw_id).strip()))
        except (ValueError, TypeError):
            return str(raw_id).strip()
    
    def __str__(self):
        return f"{self.surname} {self.name} ({self.student_id})"
    
    @property
    def full_name(self):
        return f"{self.surname} {self.name}"
    
    @property
    def class_name(self):
        return f"{self.grade}{self.section}"
