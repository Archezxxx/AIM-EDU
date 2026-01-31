from django import forms
from django.utils.translation import gettext_lazy as _
from .models import School, Subject, MasterStudent


class SchoolForm(forms.ModelForm):
    """Form for creating/editing schools."""
    
    class Meta:
        model = School
        fields = ['name', 'code', 'address', 'phone', 'email', 'logo', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('School name'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Unique school code (e.g., AMS-R)'),
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': _('School address'),
                'rows': 3,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Phone number'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('Email address'),
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True


class SubjectForm(forms.ModelForm):
    """Form for creating/editing subjects."""
    
    class Meta:
        model = Subject
        fields = ['name', 'code', 'school', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Subject name'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Subject code (optional)'),
            }),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['school'].queryset = School.objects.filter(is_active=True)
        self.fields['school'].required = False


class MasterStudentUploadForm(forms.Form):
    """Form for uploading Master Student List Excel file."""
    
    school = forms.ModelChoiceField(
        queryset=School.objects.filter(is_active=True),
        label=_('School'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(
        label=_('Excel File (.xlsx)'),
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.xlsx,.xls',
        }),
        help_text=_('Upload an Excel file with columns: id, name, surname, class, section')
    )
    replace_existing = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Replace existing students'),
        help_text=_('If checked, all existing students for this school will be deleted before import.')
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.endswith(('.xlsx', '.xls')):
                raise forms.ValidationError(_('Only Excel files (.xlsx, .xls) are allowed.'))
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('File size must be less than 10MB.'))
        return file


class MasterStudentForm(forms.ModelForm):
    """Form for manually adding/editing a student."""
    
    class Meta:
        model = MasterStudent
        fields = ['student_id', 'name', 'surname', 'grade', 'section']
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Student ID'),
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('First name'),
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Last name'),
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Grade (e.g., 9)'),
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Section (e.g., A)'),
            }),
        }
