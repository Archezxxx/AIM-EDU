from django import forms
from django.utils.translation import gettext_lazy as _
from .models import OnlineExam, ExamQuestion, QuestionOption


class OnlineExamForm(forms.ModelForm):
    """Form for creating/editing online exams."""
    
    class Meta:
        model = OnlineExam
        fields = [
            'title', 'description', 'subject', 'school',
            'duration_minutes', 'passing_score',
            'start_time', 'end_time',
            'shuffle_questions', 'shuffle_options',
            'show_results_immediately', 'max_tab_switches', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'max_tab_switches': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_('End time must be after start time.'))
        
        return cleaned_data


class ExamQuestionForm(forms.ModelForm):
    """Form for creating/editing exam questions."""
    
    class Meta:
        model = ExamQuestion
        fields = ['question_text', 'question_image', 'question_type', 'points', 'correct_answers', 'order']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'correct_answers': forms.Textarea(attrs={
                'class': 'form-input', 
                'rows': 2,
                'placeholder': _('For fill-in-the-blanks: enter correct answers separated by | (pipe). Example: answer1|answer2|answer3')
            }),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


class QuestionOptionForm(forms.ModelForm):
    """Form for creating/editing question options."""
    
    class Meta:
        model = QuestionOption
        fields = ['text', 'is_correct', 'order']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }


# Formsets for inline editing
QuestionOptionFormSet = forms.inlineformset_factory(
    ExamQuestion,
    QuestionOption,
    form=QuestionOptionForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True
)


class AnswerForm(forms.Form):
    """Form for submitting an answer during exam."""
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    option_id = forms.IntegerField(required=False)
