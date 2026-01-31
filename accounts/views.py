from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, activate
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q

from .models import User
from .forms import (
    LoginForm, StudentRegistrationForm, TeacherForm, AdminForm,
    ProfileForm, StudentProfileForm, PasswordChangeForm, AdminPasswordResetForm
)
from .decorators import super_admin_required, teacher_or_admin_required


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Handle language switch
    lang = request.GET.get('lang')
    if lang in ['en', 'ru', 'ky']:
        activate(lang)
        request.session['django_language'] = lang
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Set user's preferred language
            activate(user.preferred_language)
            request.session['django_language'] = user.preferred_language
            
            # Remember me functionality
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
            
            messages.success(request, _('Welcome back, %(name)s!') % {'name': user.first_name})
            
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, _('You have been logged out.'))
    return redirect('accounts:login')


def register_view(request):
    """Student registration view."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Handle language switch
    lang = request.GET.get('lang')
    if lang in ['en', 'ru', 'ky']:
        activate(lang)
        request.session['django_language'] = lang
    
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Registration successful! Welcome to AIMS EXAM.'))
            return redirect('accounts:dashboard')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    """Main dashboard view with role-based content."""
    user = request.user
    context = {'user': user}
    
    if user.is_super_admin:
        # Admin dashboard stats
        context['total_schools'] = 0  # Will be updated when schools model is ready
        context['total_teachers'] = User.objects.filter(role='teacher').count()
        context['total_students'] = User.objects.filter(role='student').count()
        context['total_admins'] = User.objects.filter(role='super_admin').count()
        
        # Import here to avoid issues before migrations
        try:
            from schools.models import School
            context['total_schools'] = School.objects.filter(is_active=True).count()
        except:
            pass
    
    elif user.is_teacher:
        # Teacher dashboard
        context['school'] = user.primary_school
        # Will add more stats later
    
    else:
        # Student dashboard
        context['upcoming_exams'] = []  # Will be populated from exams app
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view."""
    user = request.user
    
    if user.is_student:
        FormClass = StudentProfileForm
    else:
        FormClass = ProfileForm
    
    if request.method == 'POST':
        form = FormClass(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Update session language if changed
            if 'preferred_language' in form.changed_data:
                activate(user.preferred_language)
                request.session['django_language'] = user.preferred_language
            
            messages.success(request, _('Profile updated successfully.'))
            return redirect('accounts:profile')
    else:
        form = FormClass(instance=user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def password_change_view(request):
    """Password change view (requires current password)."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Password changed successfully.'))
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})


# ============ Admin User Management ============

@login_required
@super_admin_required
def users_list_view(request):
    """List all users with filtering."""
    role_filter = request.GET.get('role', '')
    search = request.GET.get('search', '')
    
    users = User.objects.all().order_by('-created_at')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'search': search,
    }
    return render(request, 'accounts/users_list.html', context)


@login_required
@super_admin_required
def teacher_create_view(request):
    """Create new teacher."""
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, _('Teacher "%(name)s" created successfully.') % {'name': teacher.get_full_name()})
            return redirect('accounts:users')
    else:
        form = TeacherForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Add Teacher'),
        'submit_text': _('Create Teacher'),
    })


@login_required
@super_admin_required
def teacher_edit_view(request, pk):
    """Edit existing teacher."""
    teacher = get_object_or_404(User, pk=pk, role='teacher')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, _('Teacher updated successfully.'))
            return redirect('accounts:users')
    else:
        form = TeacherForm(instance=teacher)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Edit Teacher'),
        'submit_text': _('Save Changes'),
        'user_obj': teacher,
    })


@login_required
@super_admin_required
def admin_create_view(request):
    """Create new admin."""
    if request.method == 'POST':
        form = AdminForm(request.POST)
        if form.is_valid():
            admin = form.save()
            messages.success(request, _('Admin "%(name)s" created successfully.') % {'name': admin.get_full_name()})
            return redirect('accounts:users')
    else:
        form = AdminForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Add Admin'),
        'submit_text': _('Create Admin'),
    })


@login_required
@super_admin_required
def admin_edit_view(request, pk):
    """Edit existing admin."""
    admin_user = get_object_or_404(User, pk=pk, role='super_admin')
    
    # Prevent editing yourself (use profile instead)
    if admin_user == request.user:
        messages.warning(request, _('Use the profile page to edit your own account.'))
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        form = AdminForm(request.POST, instance=admin_user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Admin updated successfully.'))
            return redirect('accounts:users')
    else:
        form = AdminForm(instance=admin_user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': _('Edit Admin'),
        'submit_text': _('Save Changes'),
        'user_obj': admin_user,
    })


@login_required
@super_admin_required
def user_delete_view(request, pk):
    """Delete user (soft delete for data preservation)."""
    user = get_object_or_404(User, pk=pk)
    
    # Cannot delete yourself
    if user == request.user:
        messages.error(request, _('You cannot delete your own account.'))
        return redirect('accounts:users')
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, _('User "%(name)s" has been deactivated.') % {'name': user.get_full_name()})
        return redirect('accounts:users')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user})


@login_required
@super_admin_required
def admin_reset_password_view(request, pk):
    """Admin resets a user's password."""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = AdminPasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, _('Password reset for "%(name)s".') % {'name': user.get_full_name()})
            return redirect('accounts:users')
    else:
        form = AdminPasswordResetForm()
    
    return render(request, 'accounts/admin_reset_password.html', {
        'form': form,
        'user_obj': user,
    })
