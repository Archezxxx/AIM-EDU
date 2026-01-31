from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(forms.Form):
    """User login form with email authentication."""
    
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter your email'),
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter your password'),
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_('Remember me'),
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_('Invalid email or password.'))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_('This account is inactive.'))
        
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache


class StudentRegistrationForm(forms.ModelForm):
    """Student registration form with all required fields."""
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Create a password'),
        })
    )
    password_confirm = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm your password'),
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'mother_phone', 'father_phone']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': _('Your email address'),
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('First name'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Last name'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Your phone number'),
            }),
            'mother_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _("Mother's phone number"),
            }),
            'father_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _("Father's phone number"),
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required for students
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['mother_phone'].required = True
        self.fields['father_phone'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email is already registered.'))
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'student'
        if commit:
            user.save()
        return user


class TeacherForm(forms.ModelForm):
    """Teacher creation/edit form for admins."""
    
    password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Leave empty to keep current'),
        }),
        help_text=_('Leave empty to keep current password (when editing).')
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'primary_school', 'preferred_language', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'primary_school': forms.Select(attrs={'class': 'form-select'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Import here to avoid circular import
        from schools.models import School
        self.fields['primary_school'].queryset = School.objects.filter(is_active=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('This email is already in use.'))
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        user.role = 'teacher'
        if commit:
            user.save()
        return user


class AdminForm(forms.ModelForm):
    """Admin creation/edit form (for super admins only)."""
    
    password = forms.CharField(
        label=_('Password'),
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Leave empty to keep current'),
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'preferred_language', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        user.role = 'super_admin'
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """User profile edit form."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentProfileForm(forms.ModelForm):
    """Student-specific profile form with parent contact fields."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'mother_phone', 'father_phone', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'mother_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'father_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    """Custom password change form with styled fields."""
    
    old_password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter current password'),
        })
    )
    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter new password'),
        })
    )
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm new password'),
        })
    )


class AdminPasswordResetForm(forms.Form):
    """Form for admins to reset user passwords."""
    
    new_password = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Enter new password'),
        })
    )
    confirm_password = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': _('Confirm new password'),
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        
        if password and confirm and password != confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        
        return cleaned_data
